#!/usr/bin/env python3
"""
Creeper v1.3.0 - 网页爬虫工具
将 Markdown 文件中的 URL 批量爬取并保存为结构化的本地 Markdown 文档

支持同步和异步两种模式:
- 异步模式 (默认): 高性能并发爬取
- 同步模式 (--sync): 顺序爬取
"""

import sys
import asyncio
from pathlib import Path
from tqdm import tqdm
from tqdm.asyncio import tqdm as async_tqdm

from src.base_crawler import BaseCrawler
from src.parser import MarkdownParser
from src.dedup import DedupManager
from src.fetcher import WebFetcher
from src.async_fetcher import AsyncWebFetcher
from src.cookie_manager import CookieManager
from src.storage import StorageManager
from src.config import config
from src.utils import setup_logger
from src.cli_parser import create_argument_parser

logger = setup_logger("creeper")


class SyncCrawler(BaseCrawler):
    """同步爬虫 (顺序执行)"""

    def __init__(self, args):
        """初始化同步爬虫"""
        super().__init__(args)

        # 初始化 Cookie 管理器 (仅文件模式)
        if args.cookies_file:
            self.cookie_manager = CookieManager(
                cookies_file=args.cookies_file,
                format='json'
            )
            logger.info(f"已启用 Cookie 管理,文件: {args.cookies_file}")

        # 初始化各个模块
        self.dedup = DedupManager()
        self.fetcher = WebFetcher(
            use_playwright=not args.no_playwright,
            cookie_manager=self.cookie_manager
        )
        self.storage = StorageManager(args.output)

    def run(self):
        """运行同步爬虫"""
        try:
            logger.info("=" * 60)
            logger.info(f"Creeper v1.3.0 - 同步模式")
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

            # 显示文档结构(如果是调试模式)
            if config.DEBUG:
                self.parser.display_structure()

            # 2. 测试 Redis 连接
            if not self.dedup.test_connection():
                logger.warning("Redis 连接失败,将跳过去重检查")

            # 3. 处理每个 URL
            logger.info("开始爬取网页(同步模式)...")
            with tqdm(total=len(items), desc="爬取进度", unit="url") as pbar:
                for item in items:
                    self._process_url(item, pbar)

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
            self.fetcher.close()
            self.dedup.close()

    def _process_url(self, item, pbar):
        """
        处理单个 URL (同步)

        Args:
            item: URLItem 对象
            pbar: 进度条对象
        """
        url = item.url
        pbar.set_description(f"处理: {url[:50]}...")

        try:
            # 去重检查
            if not self.args.force and self.dedup.is_crawled(url):
                logger.info(f"⊘ 跳过(已爬取): {url}")
                self.stats['skipped'] += 1
                pbar.update(1)
                return

            # 爬取网页
            page = self.fetcher.fetch(url)

            if not page.success:
                logger.error(f"✗ 爬取失败: {url} - {page.error}")
                self.stats['failed'] += 1
                self.failed_items.append((item, page.error or "未知错误"))
                pbar.update(1)
                return

            # 保存文件
            file_path = self.storage.save(item, page)

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
        finally:
            pbar.update(1)


class AsyncCrawler(BaseCrawler):
    """异步爬虫 (并发执行)"""

    def __init__(self, args):
        """初始化异步爬虫"""
        super().__init__(args)

        # 初始化 Cookie 管理器
        if args.cookies_file:
            # 使用文件存储模式(向后兼容)
            self.cookie_manager = CookieManager(
                cookies_file=args.cookies_file,
                format='json',
                storage_backend='file'
            )
            logger.info(f"已启用 Cookie 管理(文件模式),文件: {args.cookies_file}")
        elif config.COOKIE_STORAGE == 'redis':
            # 使用 Redis 存储模式
            self.cookie_manager = CookieManager(
                storage_backend='redis',
                redis_client=None,  # 延迟初始化
                redis_key_prefix=config.COOKIE_REDIS_KEY_PREFIX,
                expire_days=config.COOKIE_EXPIRE_DAYS
            )
            logger.info(f"已启用 Cookie 管理(Redis 模式),过期时间: {config.COOKIE_EXPIRE_DAYS} 天")

        # 初始化各个模块
        self.dedup = DedupManager()

        # 如果 cookie_manager 使用 Redis 模式,传入 redis_client
        if self.cookie_manager and self.cookie_manager.storage_backend == 'redis':
            self.cookie_manager.redis_client = self.dedup.redis
            # 重新加载 Cookie
            self.cookie_manager._load_all_from_redis()

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
            logger.info(f"Creeper v1.3.0 - 异步并发模式")
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

            # 保存文件(同步操作,但很快)
            file_path = self.storage.save(item, page)

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
            storage_backend='redis',
            redis_client=dedup.redis,
            redis_key_prefix=config.COOKIE_REDIS_KEY_PREFIX,
            expire_days=config.COOKIE_EXPIRE_DAYS
        )

        # 保存 Cookie
        for domain, cookies in domain_cookies.items():
            cookie_manager.set_cookies(domain, cookies)

        success = cookie_manager.save()

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

    # 处理交互式登录
    if args.login_url:
        # 必须使用异步模式
        if args.sync:
            logger.error("交互式登录不支持同步模式,请移除 --sync 参数")
            sys.exit(1)

        # 执行登录逻辑
        success = asyncio.run(do_interactive_login(args))
        sys.exit(0 if success else 1)

    # 检查输入文件
    if not args.input_file:
        logger.error("错误: 必须提供输入文件或使用 --login-url 进行登录")
        sys.exit(1)

    if not Path(args.input_file).exists():
        logger.error(f"输入文件不存在: {args.input_file}")
        sys.exit(1)

    # 根据模式选择 Crawler
    if args.sync:
        # 同步模式
        logger.info("使用同步模式")
        if args.concurrency > 1:
            logger.warning("同步模式不支持并发,将忽略 -c/--concurrency 参数")

        creeper = SyncCrawler(args)
        creeper.run()
    else:
        # 异步模式 (默认)
        creeper = AsyncCrawler(args)
        asyncio.run(creeper.run())


if __name__ == '__main__':
    main()
