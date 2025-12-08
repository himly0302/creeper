"""
BaseCrawler - 爬虫基类
提供异步版本的公共逻辑
"""

from abc import ABC, abstractmethod
from src.utils import setup_logger

logger = setup_logger("creeper")


class BaseCrawler(ABC):
    """爬虫基类,包含公共逻辑"""

    def __init__(self, args):
        """
        初始化公共属性

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

        # 子类负责初始化的模块
        self.parser = None
        self.dedup = None
        self.fetcher = None
        self.storage = None
        self.cookie_manager = None

    @abstractmethod
    def run(self):
        """运行爬虫 - 子类实现"""
        pass

    @abstractmethod
    def _process_url(self, item):
        """处理单个 URL - 子类实现"""
        pass

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
        if self.storage:
            storage_stats = self.storage.get_stats()
            print(f"\n输出目录: {storage_stats['output_dir']}")
            print(f"生成文件: {storage_stats['total_files']} 个")
