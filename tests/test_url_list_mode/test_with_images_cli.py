"""
测试 --with-images CLI参数验证
"""

import pytest
import sys
from unittest.mock import patch
from io import StringIO

from src.cli_parser import create_argument_parser


class TestWithImagesCLI:
    """测试 --with-images CLI参数"""

    def test_parser_with_with_images(self):
        """测试解析器正确解析--with-images参数"""
        parser = create_argument_parser()

        # 测试 --with-images 参数
        args = parser.parse_args(['--urls', 'https://example.com', '--with-images'])
        assert args.urls == 'https://example.com'
        assert args.with_images is True

        # 测试不包含 --with-images
        args = parser.parse_args(['--urls', 'https://example.com'])
        assert args.urls == 'https://example.com'
        assert args.with_images is False

    def test_help_message(self):
        """测试帮助信息包含--with-images"""
        parser = create_argument_parser()
        help_text = parser.format_help()

        assert '--with-images' in help_text
        assert '提取页面中的图片链接' in help_text
        assert '仅在 --urls 模式下生效' in help_text

    @patch('sys.stderr', new_callable=StringIO)
    @patch('sys.exit')
    def test_with_images_without_urls_error(self, mock_exit, mock_stderr):
        """测试--with-images必须配合--urls使用"""
        from creeper import main

        # 模拟命令行参数
        test_args = ['creeper.py', '--with-images']

        with patch('sys.argv', test_args):
            main()

        # 验证错误消息被输出
        mock_exit.assert_called_once_with(1)
        error_output = mock_stderr.getvalue()
        assert '--with-images 参数必须配合 --urls 使用' in error_output

    @patch('sys.stderr', new_callable=StringIO)
    @patch('sys.exit')
    def test_with_images_with_urls_success(self, mock_exit, mock_stderr):
        """测试--with-images配合--urls使用成功"""
        with patch('src.url_list_mode.run_url_list_mode') as mock_run:
            test_args = ['creeper.py', '--urls', 'https://example.com', '--with-images']

            with patch('sys.argv', test_args):
                main()

            # 验证run_url_list_mode被正确调用
            mock_run.assert_called_once()
            args = mock_run.call_args[1]  # 获取关键字参数
            assert args['with_images'] is True

    def test_with_images_parameter_combination(self):
        """测试各种参数组合"""
        parser = create_argument_parser()

        # 测试 --with-images 和其他参数组合
        args = parser.parse_args([
            '--urls', 'https://example.com,https://test.com',
            '--with-images',
            '--concurrency', '10',
            '--no-playwright'
        ])

        assert args.urls == 'https://example.com,https://test.com'
        assert args.with_images is True
        assert args.concurrency == 10
        assert args.no_playwright is True

    @patch('sys.stdout', new_callable=StringIO)
    def test_url_list_mode_with_images_logging(self, mock_stdout):
        """测试启用图片提取时的日志输出"""
        from src.url_list_mode import URLListMode
        from src.utils import setup_logger

        # 创建logger并捕获输出
        import logging
        logger = setup_logger("test")

        with patch('logging.Logger.info') as mock_info:
            mode = URLListMode(with_images=True)
            # 验证初始化日志包含图片提取信息
            mock_info.assert_called()
            log_calls = [call.args[0] for call in mock_info.call_args_list]
            any_log_with_images = any('含图片提取' in log for log in log_calls)
            assert any_log_with_images