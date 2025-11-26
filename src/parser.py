"""
Markdown 文件解析模块
从 Markdown 文件中提取标题层级和 URL
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

from .utils import setup_logger, is_valid_url

logger = setup_logger(__name__)


@dataclass
class URLItem:
    """URL 项目数据类"""
    url: str
    h1: str  # 一级标题
    h2: str  # 二级标题
    line_number: int  # 行号(用于调试)

    def __repr__(self):
        return f"URLItem(url={self.url}, h1={self.h1}, h2={self.h2})"


class MarkdownParser:
    """Markdown 文件解析器"""

    def __init__(self, file_path: str):
        """
        初始化解析器

        Args:
            file_path: Markdown 文件路径
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        self.items: List[URLItem] = []
        self.current_h1 = ""
        self.current_h2 = ""

    def parse(self) -> List[URLItem]:
        """
        解析 Markdown 文件

        Returns:
            URL 项目列表
        """
        logger.info(f"开始解析文件: {self.file_path}")

        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # 跳过空行
            if not line:
                continue

            # 解析 H1 标题
            if line.startswith('# ') and not line.startswith('## '):
                self.current_h1 = line[2:].strip()
                self.current_h2 = ""  # 重置 H2
                logger.debug(f"发现 H1: {self.current_h1}")
                continue

            # 解析 H2 标题
            if line.startswith('## ') and not line.startswith('### '):
                self.current_h2 = line[3:].strip()
                logger.debug(f"发现 H2: {self.current_h2}")
                continue

            # 解析 URL
            # 支持以下格式:
            # - http://example.com
            # - https://example.com
            # - [Title](http://example.com)  # Markdown 链接格式
            urls = self._extract_urls(line)
            for url in urls:
                if is_valid_url(url):
                    item = URLItem(
                        url=url,
                        h1=self.current_h1 or "未分类",
                        h2=self.current_h2 or "默认",
                        line_number=line_num
                    )
                    self.items.append(item)
                    logger.debug(f"发现 URL: {url} (行 {line_num})")
                else:
                    logger.warning(f"无效 URL: {url} (行 {line_num})")

        logger.info(f"解析完成,共找到 {len(self.items)} 个 URL")
        return self.items

    def _extract_urls(self, line: str) -> List[str]:
        """
        从行中提取所有 URL

        Args:
            line: 文本行

        Returns:
            URL 列表
        """
        urls = []

        # 匹配 Markdown 链接格式 [Title](URL)
        markdown_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
        markdown_matches = re.findall(markdown_pattern, line)
        for title, url in markdown_matches:
            urls.append(url.strip())

        # 匹配普通 URL
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        plain_matches = re.findall(url_pattern, line)
        for url in plain_matches:
            # 避免重复添加(已被 Markdown 格式匹配的)
            if url not in urls:
                urls.append(url.strip())

        return urls

    def get_structure(self) -> Dict[str, Dict[str, List[str]]]:
        """
        获取文档结构

        Returns:
            嵌套字典 {H1: {H2: [URLs]}}
        """
        structure = {}
        for item in self.items:
            if item.h1 not in structure:
                structure[item.h1] = {}
            if item.h2 not in structure[item.h1]:
                structure[item.h1][item.h2] = []
            structure[item.h1][item.h2].append(item.url)
        return structure

    def display_structure(self):
        """显示文档结构(调试用)"""
        structure = self.get_structure()
        print("\n=== 文档结构 ===")
        for h1, h2_dict in structure.items():
            print(f"\n📁 {h1}")
            for h2, urls in h2_dict.items():
                print(f"  📂 {h2}")
                for url in urls:
                    print(f"    🔗 {url}")
        print("\n================\n")


def parse_markdown_file(file_path: str) -> List[URLItem]:
    """
    便捷函数:解析 Markdown 文件

    Args:
        file_path: Markdown 文件路径

    Returns:
        URL 项目列表
    """
    parser = MarkdownParser(file_path)
    return parser.parse()
