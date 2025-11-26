#!/usr/bin/env python3
"""
Creeper - 网页爬虫工具
将 Markdown 文件中的 URL 批量爬取并保存为结构化的本地 Markdown 文档
"""

import sys
import argparse
from pathlib import Path
from tqdm import tqdm

from src.parser import MarkdownParser
from src.dedup import DedupManager
from src.fetcher import WebFetcher
from src.storage import StorageManager
from src.config import config
from src.utils import setup_logger

logger = setup_logger("creeper")


class Creeper:
    """Creeper 主类"""

    def __init__(self, args):
        """
        初始化 Creeper

        Args:
            args: 命令行参数
        """
        self.args = args
        self.stats = {
            'total': 0,
            'success': 0,
            'skipped': 0,
            'failed': 0
        }
        self.failed_items = []

        # 初始化各个模块
        self.parser = None
        self.dedup = DedupManager()
        self.fetcher = WebFetcher(use_playwright=not args.no_playwright)
        self.storage = StorageManager(args.output)

    def run(self):
        """运行爬虫"""
        try:
            logger.info("=" * 60)
            logger.info(f"Creeper v0.1.0 - 开始运行")
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
            logger.info("开始爬取网页...")
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
            # 清理资源
            self.fetcher.close()
            self.dedup.close()

    def _process_url(self, item, pbar):
        """
        处理单个 URL

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

    def _display_stats(self):
        """显示统计信息"""
        print("\n" + "=" * 60)
        print("📊 爬取统计")
        print("=" * 60)
        print(f"总计:   {self.stats['total']} 个 URL")
        print(f"成功:   {self.stats['success']} 个 ✓")
        print(f"跳过:   {self.stats['skipped']} 个 ⊘")
        print(f"失败:   {self.stats['failed']} 个 ✗")

        if self.stats['total'] > 0:
            success_rate = (self.stats['success'] / self.stats['total']) * 100
            print(f"成功率: {success_rate:.1f}%")

        print("=" * 60)

        # 显示输出目录
        storage_stats = self.storage.get_stats()
        print(f"\n输出目录: {storage_stats['output_dir']}")
        print(f"生成文件: {storage_stats['total_files']} 个")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Creeper - 网页爬虫工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s input.md                    # 基本使用
  %(prog)s input.md -o ./output        # 指定输出目录
  %(prog)s input.md --debug            # 开启调试模式
  %(prog)s input.md --force            # 强制重新爬取
  %(prog)s input.md --no-playwright    # 禁用 Playwright

更多信息: https://github.com/your-repo/creeper
        """
    )

    parser.add_argument(
        'input_file',
        type=str,
        help='Markdown 输入文件路径'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default=config.OUTPUT_DIR,
        help=f'输出目录 (默认: {config.OUTPUT_DIR})'
    )

    parser.add_argument(
        '-c', '--concurrency',
        type=int,
        default=config.CONCURRENCY,
        help=f'并发数 (默认: {config.CONCURRENCY}, MVP 版本暂不支持)'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新爬取(跳过去重检查)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='开启调试模式'
    )

    parser.add_argument(
        '--no-playwright',
        action='store_true',
        help='禁用 Playwright(仅使用静态爬取)'
    )

    parser.add_argument(
        '-v', '--version',
        action='version',
        version='Creeper 0.1.0 (MVP)'
    )

    return parser.parse_args()


def main():
    """主函数"""
    # 解析参数
    args = parse_args()

    # 设置调试模式
    if args.debug:
        config.DEBUG = True
        config.LOG_LEVEL = 'DEBUG'
        # 重新设置 logger
        import logging
        logging.getLogger("creeper").setLevel(logging.DEBUG)

    # 检查输入文件
    if not Path(args.input_file).exists():
        logger.error(f"输入文件不存在: {args.input_file}")
        sys.exit(1)

    # 运行爬虫
    creeper = Creeper(args)
    creeper.run()


if __name__ == '__main__':
    main()
