"""
内容清洗模块
对提取的内容进行进一步清洗和处理
"""

import re
from typing import Optional

from .utils import setup_logger

logger = setup_logger(__name__)


class ContentCleaner:
    """内容清洗器"""

    @staticmethod
    def clean(content: str) -> str:
        """
        清洗内容

        Args:
            content: 原始内容

        Returns:
            清洗后的内容
        """
        if not content:
            return ""

        # MVP 版本:Trafilatura 已经做了大部分清洗工作
        # 这里只做基本的格式规范化

        # 1. 统一换行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # 2. 移除多余的空行(连续 3 个以上换行 -> 2 个换行)
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 3. 移除行首行尾空白
        lines = [line.strip() for line in content.split('\n')]
        content = '\n'.join(lines)

        # 4. 移除零宽字符和其他不可见字符
        content = ContentCleaner._remove_invisible_chars(content)

        return content.strip()

    @staticmethod
    def _remove_invisible_chars(text: str) -> str:
        """
        移除不可见字符

        Args:
            text: 原始文本

        Returns:
            清洗后的文本
        """
        # 零宽字符列表
        invisible_chars = [
            '\u200b',  # 零宽空格
            '\u200c',  # 零宽非连接符
            '\u200d',  # 零宽连接符
            '\ufeff',  # 零宽非断空格 (BOM)
            '\u00ad',  # 软连字符
        ]

        for char in invisible_chars:
            text = text.replace(char, '')

        return text

    @staticmethod
    def truncate_description(description: str, max_length: int = 200) -> str:
        """
        截断描述文本

        Args:
            description: 原始描述
            max_length: 最大长度

        Returns:
            截断后的描述
        """
        if not description:
            return ""

        if len(description) <= max_length:
            return description

        # 尝试在句号处截断
        truncated = description[:max_length]
        last_period = truncated.rfind('。')
        if last_period > max_length * 0.7:  # 如果句号位置不太靠前
            return truncated[:last_period + 1]

        # 否则直接截断并添加省略号
        return truncated[:max_length - 3] + '...'

    @staticmethod
    def extract_summary(content: str, max_length: int = 300) -> str:
        """
        从内容中提取摘要

        Args:
            content: 完整内容
            max_length: 最大长度

        Returns:
            摘要文本
        """
        if not content:
            return ""

        # 移除 Markdown 标记
        text = re.sub(r'#+\s+', '', content)  # 移除标题标记
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # 移除链接,保留文本
        text = re.sub(r'[*_`]', '', text)  # 移除加粗、斜体、代码标记

        # 取前几句话作为摘要
        sentences = text.split('。')
        summary = ""
        for sentence in sentences:
            if len(summary) + len(sentence) <= max_length:
                summary += sentence + '。'
            else:
                break

        return summary.strip() or text[:max_length] + '...'
