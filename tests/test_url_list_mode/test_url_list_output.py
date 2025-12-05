"""
URL列表模式输出格式测试
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock

# 添加项目根目录到路径
import sys
sys.path.insert(0, '/home/lyf/workspaces/creeper')

from src.url_list_mode import URLListMode
from src.fetcher import WebPage


class TestURLListOutput:
    """测试URL列表模式的输出格式"""

    def setup_method(self):
        """设置测试环境"""
        self.mode = URLListMode(concurrency=2, use_playwright=False)

    def test_parse_url_string_single(self):
        """测试解析单个URL字符串"""
        url_string = "https://example.com"
        urls = self.mode.parse_url_string(url_string)
        assert len(urls) == 1
        assert urls[0] == "https://example.com"

    def test_parse_url_string_multiple(self):
        """测试解析多个URL字符串"""
        url_string = "https://example1.com,https://example2.com,https://example3.com"
        urls = self.mode.parse_url_string(url_string)
        assert len(urls) == 3
        assert urls[0] == "https://example1.com"
        assert urls[1] == "https://example2.com"
        assert urls[2] == "https://example3.com"

    def test_parse_url_string_with_spaces(self):
        """测试解析包含空格的URL字符串"""
        url_string = " https://example1.com , https://example2.com "
        urls = self.mode.parse_url_string(url_string)
        assert len(urls) == 2
        assert urls[0] == "https://example1.com"
        assert urls[1] == "https://example2.com"

    def test_validate_urls_valid(self):
        """测试有效URL验证"""
        valid_urls = [
            "https://example.com",
            "http://test.org",
            "https://www.example.net/path"
        ]
        result = self.mode.validate_urls(valid_urls)
        assert len(result) == 3
        assert result == valid_urls

    def test_validate_urls_invalid(self):
        """测试无效URL过滤"""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # 不支持的协议
            "",  # 空字符串
            "https://example.com"  # 只有这个是有效的
        ]
        result = self.mode.validate_urls(invalid_urls)
        assert len(result) == 1
        assert result[0] == "https://example.com"

    def test_webpage_to_dict_success(self):
        """测试将成功WebPage转换为字典"""
        webpage = WebPage(
            url="https://example.com",
            title="Example Title",
            description="Example description",
            content="This is the content of the page.",
            success=True
        )

        result = self.mode.webpage_to_dict(webpage)

        assert result["title"] == "Example Title"
        assert result["summary"] == "Example description"
        assert result["content"] == "This is the content of the page."
        assert result["url"] == "https://example.com"

    def test_webpage_to_dict_failure(self):
        """测试将失败WebPage转换为字典"""
        webpage = WebPage(
            url="https://example.com",
            title="",
            description="",
            content="",
            success=False,
            error="Network error"
        )

        result = self.mode.webpage_to_dict(webpage)

        assert result["title"] == ""
        assert result["summary"] == ""
        assert result["content"] == ""
        assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_process_urls_success(self):
        """测试成功处理URL列表"""
        # 模拟成功的WebPage对象
        mock_webpage1 = WebPage(
            url="https://example1.com",
            title="Title 1",
            description="Description 1",
            content="Content 1",
            success=True
        )
        mock_webpage2 = WebPage(
            url="https://example2.com",
            title="Title 2",
            description="Description 2",
            content="Content 2",
            success=True
        )

        # 模拟fetcher的fetch_batch方法
        with patch.object(self.mode.fetcher, 'fetch_batch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [mock_webpage1, mock_webpage2]

            urls = ["https://example1.com", "https://example2.com"]
            results = await self.mode.process_urls(urls)

            assert len(results) == 2
            assert results[0]["title"] == "Title 1"
            assert results[1]["title"] == "Title 2"

    @pytest.mark.asyncio
    async def test_process_urls_with_failure(self):
        """测试处理包含失败的URL列表"""
        # 模拟一个成功一个失败的WebPage对象
        mock_webpage1 = WebPage(
            url="https://example1.com",
            title="Title 1",
            description="Description 1",
            content="Content 1",
            success=True
        )
        mock_webpage2 = WebPage(
            url="https://example2.com",
            title="",
            description="",
            content="",
            success=False,
            error="404 Not Found"
        )

        # 模拟fetcher的fetch_batch方法
        with patch.object(self.mode.fetcher, 'fetch_batch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [mock_webpage1, mock_webpage2]

            urls = ["https://example1.com", "https://example2.com"]
            results = await self.mode.process_urls(urls)

            assert len(results) == 2
            assert results[0]["title"] == "Title 1"
            assert results[1]["title"] == "获取失败"
            assert "404 Not Found" in results[1]["content"]

    def test_output_json_format(self):
        """测试JSON输出格式"""
        results = [
            {
                "title": "Title 1",
                "summary": "Summary 1",
                "content": "Content 1",
                "url": "https://example1.com"
            },
            {
                "title": "Title 2",
                "summary": "Summary 2",
                "content": "Content 2",
                "url": "https://example2.com"
            }
        ]

        # 测试输出格式是否为有效的JSON
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.mode.output_json(results)
            output = mock_stdout.getvalue()

            # 验证输出是否为有效的JSON
            parsed_output = json.loads(output)
            assert len(parsed_output) == 2
            assert parsed_output[0]["title"] == "Title 1"
            assert parsed_output[1]["title"] == "Title 2"