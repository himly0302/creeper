#!/usr/bin/env python3
"""
测试异步模式正常工作
验证删除同步版本后，异步模式依然正常运行
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from creeper import AsyncCrawler
from src.parser import MarkdownParser
from src.dedup import DedupManager
from src.async_fetcher import AsyncWebFetcher
from src.cookie_manager import CookieManager
from src.storage import StorageManager


class TestAsyncOnlyMode:
    """测试异步模式正常工作"""

    def test_async_crawler_initialization(self):
        """测试异步爬虫初始化"""
        # 创建模拟参数
        args = Mock()
        args.input_file = "test_input.md"
        args.output = "test_output"
        args.no_playwright = True
        args.concurrency = 5
        args.debug = False
        args.save_cookies = False

        # 初始化异步爬虫
        crawler = AsyncCrawler(args)

        # 验证关键组件存在
        assert crawler.dedup is not None, "去重管理器应该存在"
        assert crawler.cookie_manager is not None, "Cookie 管理器应该存在"
        assert crawler.fetcher is not None, "异步获取器应该存在"
        assert isinstance(crawler.fetcher, AsyncWebFetcher), "应该是异步获取器"
        assert crawler.storage is not None, "存储管理器应该存在"

        print("✓ 异步爬虫初始化测试通过")

    def test_no_sync_imports(self):
        """验证没有导入同步相关模块"""
        # 尝试导入同步模块应该失败
        try:
            from src.fetcher import WebFetcher
            assert False, "不应该能导入 WebFetcher"
        except ImportError:
            print("✓ 同步获取器已成功移除")

        # 验证图片下载器中只有异步类
        from src.image_downloader import AsyncImageDownloader

        try:
            from src.image_downloader import ImageDownloader
            assert False, "不应该能导入同步图片下载器"
        except (ImportError, AttributeError):
            print("✓ 同步图片下载器已成功移除")

    async def test_async_components_exist(self):
        """测试异步组件存在且可用"""
        # 验证异步获取器
        fetcher = AsyncWebFetcher(use_playwright=False, concurrency=5)
        assert hasattr(fetcher, 'fetch'), "异步获取器应该有 fetch 方法"
        assert asyncio.iscoroutinefunction(fetcher.fetch), "fetch 应该是异步方法"

        # 验证异步图片下载器
        from src.image_downloader import AsyncImageDownloader
        downloader = AsyncImageDownloader()
        assert hasattr(downloader, 'download_image'), "异步下载器应该有 download_image 方法"
        assert asyncio.iscoroutinefunction(downloader.download_image), "download_image 应该是异步方法"

        print("✓ 异步组件测试通过")

    def test_cli_parser_no_sync(self):
        """测试命令行解析器没有 --sync 选项"""
        from src.cli_parser import create_argument_parser

        parser = create_argument_parser()

        # 尝试解析 --sync 应该报错
        try:
            args = parser.parse_args(['--sync'])
            assert False, "不应该能解析 --sync 参数"
        except SystemExit:
            print("✓ --sync 参数已成功移除")

    def test_base_crawler_updated(self):
        """测试基类已更新注释"""
        from src.base_crawler import BaseCrawler

        # 验证基类仍然存在
        assert BaseCrawler is not None, "基类应该仍然存在"

        # 验证基类文档字符串已更新
        doc = BaseCrawler.__doc__
        assert doc is not None, "基类应该有文档字符串"
        assert "同步" not in doc, "文档中不应包含'同步'"
        assert "异步" in doc, "文档中应包含'异步'"

        print("✓ 基类更新测试通过")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试删除同步版本后的功能")
    print("=" * 60)

    test_obj = TestAsyncOnlyMode()

    # 运行同步测试
    test_obj.test_async_crawler_initialization()
    test_obj.test_no_sync_imports()
    test_obj.test_cli_parser_no_sync()
    test_obj.test_base_crawler_updated()

    # 运行异步测试
    async def run_async_tests():
        await test_obj.test_async_components_exist()

    asyncio.run(run_async_tests())

    print("=" * 60)
    print("✅ 所有测试通过！同步版本已成功删除")
    print("=" * 60)


if __name__ == '__main__':
    run_tests()