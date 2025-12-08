#!/usr/bin/env python3
"""
Creeper v2.0.0 - 网页爬虫工具
将 Markdown 文件中的 URL 批量爬取并保存为结构化的本地 Markdown 文档

支持异步模式 (默认): 高性能并发爬取
"""

import sys
import asyncio
from pathlib import Path
from tqdm import tqdm
from tqdm.asyncio import tqdm as async_tqdm

from src.base_crawler import BaseCrawler
from src.parser import MarkdownParser
from src.dedup import DedupManager
from src.async_fetcher import AsyncWebFetcher
from src.cookie_manager import CookieManager
from src.storage import StorageManager
from src.config import config
from src.utils import setup_logger
from src.cli_parser import create_argument_parser

logger = setup_logger("creeper")




class AsyncCrawler(BaseCrawler):
    """异步爬虫 (并发执行)"""

    def __init__(self, args):
        """初始化异步爬虫"""
        super().__init__(args)

        # 初始化 Cookie 管理器 (仅支持 Redis 模式)
        self.cookie_manager = CookieManager(
            redis_client=None,  # 延迟初始化
            redis_key_prefix=config.COOKIE_REDIS_KEY_PREFIX,
            expire_days=config.COOKIE_EXPIRE_DAYS
        )
        logger.info(f"已启用 Cookie 管理(Redis 模式),过期时间: {config.COOKIE_EXPIRE_DAYS} 天")

        # 初始化各个模块
        self.dedup = DedupManager()

        # 设置 cookie_manager 的 redis_client
        if self.cookie_manager:
            self.cookie_manager.redis_client = self.dedup.redis

        self.fetcher = AsyncWebFetcher(
            use_playwright=not args.no_playwright,
            concurrency=args.concurrency,
            cookie_manager=self.cookie_manager
        )
        self.storage = StorageManager(args.output)

    async def run(self):
        """运行异步爬虫"""
        try:
            logger.info("=" * 60)
            logger.info(f"Creeper v2.0.0 - 异步并发模式")
            logger.info("=" * 60)

            # 1. 解析 Markdown 文件
            logger.info(f"正在解析文件: {self.args.input_file}")
            self.parser = MarkdownParser(self.args.input_file)
            items = self.parser.parse()

            if not items:
                logger.warning("未找到任何 URL,程序退出")
                return

            self.stats['total'] = len(items)
            logger.info(f"共找到 {self.stats['total']} 个 URL")
            logger.info(f"并发数: {self.fetcher.concurrency}")

            # 显示文档结构(如果是调试模式)
            if config.DEBUG:
                self.parser.display_structure()

            # 2. 测试 Redis 连接
            if not self.dedup.test_connection():
                logger.warning("Redis 连接失败,将跳过去重检查")

            # 3. 异步处理每个 URL
            logger.info("开始爬取网页(异步并发)...")
            tasks = []
            for item in items:
                task = self._process_url(item)
                tasks.append(task)

            # 使用 tqdm 显示进度
            for coro in async_tqdm.as_completed(tasks, desc="爬取进度", unit="url", total=len(tasks)):
                await coro

            # 4. 保存失败的 URL
            if self.failed_items:
                self.storage.save_failed_urls(self.failed_items)

            # 5. 显示统计信息
            self._display_stats()

            logger.info("=" * 60)
            logger.info("爬取任务完成!")
            logger.info("=" * 60)

        except KeyboardInterrupt:
            logger.warning("\n用户中断程序")
            self._display_stats()
            sys.exit(1)
        except Exception as e:
            logger.error(f"程序异常: {e}", exc_info=config.DEBUG)
            sys.exit(1)
        finally:
            # 保存 Cookie(如果有)
            if self.cookie_manager and self.args.save_cookies:
                if self.cookie_manager.save():
                    logger.info(f"Cookie 已保存")

            # 清理资源
            self.dedup.close()

    async def _process_url(self, item):
        """
        异步处理单个 URL

        Args:
            item: URLItem 对象
        """
        url = item.url

        try:
            # 去重检查
            if not self.args.force and self.dedup.is_crawled(url):
                logger.info(f"⊘ 跳过(已爬取): {url}")
                self.stats['skipped'] += 1
                return

            # 异步爬取网页
            page = await self.fetcher.fetch(url)

            if not page.success:
                logger.error(f"✗ 爬取失败: {url} - {page.error}")
                self.stats['failed'] += 1
                self.failed_items.append((item, page.error or "未知错误"))
                return

            # 保存文件(异步操作)
            file_path = await self.storage.save_async(item, page)

            if file_path:
                # 标记为已爬取
                self.dedup.mark_crawled(url)
                self.stats['success'] += 1
                logger.info(f"✓ 成功: {url}")
            else:
                self.stats['failed'] += 1
                self.failed_items.append((item, "保存文件失败"))
                logger.error(f"✗ 保存失败: {url}")

        except Exception as e:
            logger.error(f"✗ 处理异常: {url} - {e}")
            self.stats['failed'] += 1
            self.failed_items.append((item, str(e)))


async def do_interactive_login(args):
    """
    执行交互式登录

    Args:
        args: 命令行参数
    """
    from src.interactive_login import interactive_login

    try:
        # 执行交互式登录
        domain_cookies = await interactive_login(
            args.login_url,
            timeout=config.INTERACTIVE_LOGIN_TIMEOUT
        )

        if not domain_cookies:
            logger.error("未提取到任何 Cookie")
            return False

        # 创建 cookie_manager
        dedup = DedupManager()

        cookie_manager = CookieManager(
            redis_client=dedup.redis,
            redis_key_prefix=config.COOKIE_REDIS_KEY_PREFIX,
            expire_days=config.COOKIE_EXPIRE_DAYS
        )

        # 保存 Cookie
        success = True
        for domain, cookies in domain_cookies.items():
            if not cookie_manager.save(cookies, domain):
                success = False

        if success:
            logger.info("=" * 60)
            logger.info("✅ Cookie 已成功保存到 Redis")
            logger.info(f"   共保存 {len(domain_cookies)} 个域的 Cookie")
            logger.info(f"   过期时间: {config.COOKIE_EXPIRE_DAYS} 天")
            logger.info("   后续爬取将自动使用这些 Cookie")
            logger.info("=" * 60)
        else:
            logger.error("Cookie 保存失败")
            return False

        dedup.close()
        return True

    except Exception as e:
        logger.error(f"交互式登录失败: {e}", exc_info=True)
        return False


def main():
    """主函数"""
    # 解析参数
    parser = create_argument_parser()
    args = parser.parse_args()

    # 设置调试模式
    if args.debug:
        config.DEBUG = True
        config.LOG_LEVEL = 'DEBUG'
        # 重新设置 logger
        import logging
        logging.getLogger("creeper").setLevel(logging.DEBUG)

    # 验证 --with-images 参数组合
    if args.with_images and not args.urls:
        logger.error("错误: --with-images 参数必须配合 --urls 使用")
        sys.exit(1)

    # 处理交互式登录
    if args.login_url:
        # 执行登录逻辑
        success = asyncio.run(do_interactive_login(args))
        sys.exit(0 if success else 1)

    # 处理URL列表模式
    if args.urls:

        # 检查 --with-images 参数组合
        if args.with_images:
            logger.info("已启用图片链接提取功能")
        else:
            # 验证参数组合：--with-images 必须配合 --urls
            if hasattr(args, 'with_images') and args.with_images and not args.urls:
                logger.error("--with-images 参数必须配合 --urls 使用")
                sys.exit(1)

        # 导入URL列表模式模块
        from src.url_list_mode import run_url_list_mode

        # 运行URL列表模式
        asyncio.run(run_url_list_mode(
            url_string=args.urls,
            concurrency=args.concurrency,
            use_playwright=not args.no_playwright,
            with_images=args.with_images
        ))
        return

    # 检查输入文件
    if not args.input_file:
        logger.error("错误: 必须提供输入文件，或使用 --urls 或 --login-url 参数")
        sys.exit(1)

    if not Path(args.input_file).exists():
        logger.error(f"输入文件不存在: {args.input_file}")
        sys.exit(1)

    # 异步模式 (默认)
    creeper = AsyncCrawler(args)
    asyncio.run(creeper.run())


if __name__ == '__main__':
    main()
