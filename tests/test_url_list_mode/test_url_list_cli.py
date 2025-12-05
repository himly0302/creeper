"""
URL列表模式CLI测试
"""

import pytest
import sys
from unittest.mock import Mock, patch
from io import StringIO

# 添加项目根目录到路径
sys.path.insert(0, '/home/lyf/workspaces/creeper')

from src.cli_parser import create_argument_parser


class TestURLListCLI:
    """测试URL列表模式的CLI参数解析"""

    def test_urls_parameter_parsing(self):
        """测试--urls参数解析"""
        parser = create_argument_parser()

        # 测试单个URL
        args = parser.parse_args(['--urls', 'https://example.com'])
        assert args.urls == 'https://example.com'
        assert args.input_file is None

        # 测试多个URL
        args = parser.parse_args(['--urls', 'https://example1.com,https://example2.com'])
        assert args.urls == 'https://example1.com,https://example2.com'

        # 测试URL和输入文件混合（URL优先）
        args = parser.parse_args(['--urls', 'https://example.com', 'input.md'])
        assert args.urls == 'https://example.com'
        assert args.input_file == 'input.md'

    def test_urls_with_other_options(self):
        """测试--urls参数与其他选项的组合"""
        parser = create_argument_parser()

        # 测试与并发数选项组合
        args = parser.parse_args([
            '--urls', 'https://example.com',
            '-c', '10'
        ])
        assert args.urls == 'https://example.com'
        assert args.concurrency == 10

        # 测试与禁用Playwright选项组合
        args = parser.parse_args([
            '--urls', 'https://example.com',
            '--no-playwright'
        ])
        assert args.urls == 'https://example.com'
        assert args.no_playwright is True

        # 测试与调试选项组合
        args = parser.parse_args([
            '--urls', 'https://example.com',
            '--debug'
        ])
        assert args.urls == 'https://example.com'
        assert args.debug is True

    def test_urls_incompatible_with_sync(self):
        """测试--urls参数与同步模式不兼容"""
        parser = create_argument_parser()

        # 这个测试主要验证参数解析，实际的不兼容检查在运行时进行
        args = parser.parse_args([
            '--urls', 'https://example.com',
            '--sync'
        ])
        assert args.urls == 'https://example.com'
        assert args.sync is True