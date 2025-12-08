#!/usr/bin/env python3
"""
验证同步逻辑已完全移除
确保没有任何同步版本的残留代码
"""

import sys
import os
import inspect
import re

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


class TestSyncRemoved:
    """验证同步逻辑已完全移除"""

    def test_no_sync_crawler_in_main(self):
        """验证主文件中没有 SyncCrawler 类"""
        from creeper import AsyncCrawler

        # 获取 creeper 模块的所有成员
        import creeper
        members = inspect.getmembers(creeper)

        # 验证没有 SyncCrawler 类
        for name, obj in members:
            if name == 'SyncCrawler':
                assert False, f"不应该存在 SyncCrawler 类: {obj}"

        # 验证只有 AsyncCrawler
        assert AsyncCrawler is not None, "AsyncCrawler 应该存在"

        print("✓ 主文件中没有 SyncCrawler 类")

    def test_main_function_structure(self):
        """验证主函数结构已更新"""
        with open('creeper.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查没有同步相关的判断
        assert 'if args.sync:' not in content, "不应该有同步模式判断"
        assert 'SyncCrawler(' not in content, "不应该有 SyncCrawler 实例化"
        assert 'logger.info("使用同步模式")' not in content, "不应该有同步模式日志"

        # 检查只有异步模式
        assert 'AsyncCrawler(args)' in content, "应该有 AsyncCrawler 实例化"
        assert 'asyncio.run(creeper.run())' in content, "应该有异步运行代码"

        print("✓ 主函数结构已更新")

    def test_file_header_updated(self):
        """验证文件头部注释已更新"""
        with open('creeper.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查文档字符串
        assert '支持同步和异步两种模式:' not in content, "不应该提到同步模式"
        assert '- 同步模式 (--sync): 顺序爬取' not in content, "不应该有同步模式说明"

        # 应该只有异步模式
        assert '支持异步模式 (默认): 高性能并发爬取' in content, "应该提到异步模式"

        print("✓ 文件头部注释已更新")

    def test_imports_cleaned(self):
        """验证导入语句已清理"""
        with open('creeper.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查没有同步获取器导入
        assert 'from src.fetcher import' not in content, "不应该导入同步获取器"
        assert 'import WebFetcher' not in content, "不应该导入 WebFetcher"

        # 应该有异步获取器导入
        assert 'from src.async_fetcher import AsyncWebFetcher' in content, "应该导入异步获取器"

        print("✓ 导入语句已清理")

    def test_no_sync_image_downloader(self):
        """验证同步图片下载器已移除"""
        from src.image_downloader import AsyncImageDownloader

        # 检查异步下载器存在
        assert AsyncImageDownloader is not None, "异步图片下载器应该存在"

        # 尝试导入同步下载器应该失败
        try:
            from src.image_downloader import ImageDownloader
            assert False, "不应该能导入同步图片下载器"
        except (ImportError, AttributeError):
            pass

        print("✓ 同步图片下载器已移除")

    def test_image_downloader_header_updated(self):
        """验证图片下载器头部注释已更新"""
        with open('src/image_downloader.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查文档字符串
        assert '支持同步和异步两种模式' not in content, "不应该提到同步模式"
        assert '支持异步模式' in content, "应该提到异步模式"

        print("✓ 图片下载器头部注释已更新")

    def test_cli_parser_cleaned(self):
        """验证命令行解析器已清理"""
        with open('src/cli_parser.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查文档字符串
        assert '统一管理同步和异步版本的命令行参数' not in content, "不应该提到同步版本"
        assert '管理异步版本的命令行参数' in content, "应该提到异步版本"

        # 检查没有 --sync 参数
        assert '--sync' not in content, "不应该有 --sync 参数"
        assert "'--sync'" not in content, "不应该有 --sync 参数定义"

        # 检查示例中没有同步模式
        assert 'input.md --sync' not in content, "示例中不应该有同步模式"
        assert '(同步模式下忽略)' not in content, "帮助信息中不应该有同步模式说明"

        print("✓ 命令行解析器已清理")

    def test_no_sync_test_files(self):
        """验证同步测试文件已删除"""
        sync_test_file = 'tests/image_downloader/test_sync_downloader.py'
        assert not os.path.exists(sync_test_file), f"同步测试文件应该已删除: {sync_test_file}"

        print("✓ 同步测试文件已删除")

    def test_base_crawler_docstring(self):
        """验证基类文档字符串已更新"""
        with open('src/base_crawler.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查文档字符串
        assert '提供同步和异步版本的公共逻辑' not in content, "不应该提到同步版本"
        assert '提供异步版本的公共逻辑' in content, "应该提到异步版本"

        print("✓ 基类文档字符串已更新")

    def test_no_fetcher_file(self):
        """验证同步获取器文件已删除"""
        fetcher_file = 'src/fetcher.py'
        assert not os.path.exists(fetcher_file), f"同步获取器文件应该已删除: {fetcher_file}"

        # 异步获取器文件应该存在
        async_fetcher_file = 'src/async_fetcher.py'
        assert os.path.exists(async_fetcher_file), f"异步获取器文件应该存在: {async_fetcher_file}"

        print("✓ 同步获取器文件已删除")


def run_all_tests():
    """运行所有验证测试"""
    print("=" * 60)
    print("验证同步逻辑已完全移除")
    print("=" * 60)

    test_obj = TestSyncRemoved()

    # 获取所有测试方法
    test_methods = [method for method in dir(test_obj) if method.startswith('test_')]

    failed_tests = []

    for test_method in test_methods:
        try:
            getattr(test_obj, test_method)()
        except AssertionError as e:
            failed_tests.append(f"❌ {test_method}: {str(e)}")
        except Exception as e:
            failed_tests.append(f"❌ {test_method}: 意外错误 - {str(e)}")

    # 输出结果
    print("=" * 60)
    if failed_tests:
        print("⚠️  部分测试失败:")
        for failed in failed_tests:
            print(f"  {failed}")
        print(f"\n失败: {len(failed_tests)}/{len(test_methods)}")
    else:
        print(f"✅ 所有测试通过！({len(test_methods)}/{len(test_methods)})")
        print("同步版本已完全移除")
    print("=" * 60)

    return len(failed_tests) == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)