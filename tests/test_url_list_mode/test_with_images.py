"""
测试 --with-images 功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from src.url_list_mode import URLListMode
from src.fetcher import WebPage


class TestWithImages:
    """测试图片链接提取功能"""

    def test_url_list_mode_init_with_images(self):
        """测试URLListMode初始化with_images参数"""
        # 测试启用图片提取
        mode_with_images = URLListMode(concurrency=5, use_playwright=False, with_images=True)
        assert mode_with_images.concurrency == 5
        assert mode_with_images.use_playwright is False
        assert mode_with_images.with_images is True

        # 测试默认参数
        mode_default = URLListMode()
        assert mode_default.with_images is False

    @pytest.mark.asyncio
    async def test_webpage_to_dict_with_images(self):
        """测试webpage_to_dict方法with_images功能"""
        # 创建包含图片的WebPage对象
        webpage = WebPage(
            url="https://example.com",
            title="测试页面",
            description="测试描述",
            content="这是一个测试页面\n\n![测试图片](https://example.com/img1.png)\n\n![另一张图](https://example.com/img2.jpg)",
            success=True
        )

        # 测试不启用图片提取
        mode_without_images = URLListMode(with_images=False)
        result_without = mode_without_images.webpage_to_dict(webpage)

        expected_without = {
            "title": "测试页面",
            "summary": "测试描述",
            "content": "这是一个测试页面\n\n![测试图片](https://example.com/img1.png)\n\n![另一张图](https://example.com/img2.jpg)",
            "url": "https://example.com"
        }
        assert result_without == expected_without
        assert "images" not in result_without

        # 测试启用图片提取
        mode_with_images = URLListMode(with_images=True)
        result_with = mode_with_images.webpage_to_dict(webpage)

        expected_with = {
            "title": "测试页面",
            "summary": "测试描述",
            "content": "这是一个测试页面\n\n![测试图片](https://example.com/img1.png)\n\n![另一张图](https://example.com/img2.jpg)",
            "url": "https://example.com",
            "images": ["https://example.com/img1.png", "https://example.com/img2.jpg"]
        }
        assert result_with == expected_with
        assert "images" in result_with
        assert len(result_with["images"]) == 2

    @pytest.mark.asyncio
    async def test_webpage_to_dict_with_failed_page(self):
        """测试失败页面时的图片提取"""
        # 创建失败的WebPage对象
        webpage = WebPage(
            url="https://example.com",
            title="获取失败",
            description="",
            content="获取失败",
            success=False
        )

        # 测试失败页面不应提取图片
        mode_with_images = URLListMode(with_images=True)
        result = mode_with_images.webpage_to_dict(webpage)

        assert "images" not in result

    @pytest.mark.asyncio
    async def test_webpage_to_dict_with_no_images(self):
        """测试没有图片的页面"""
        # 创建不包含图片的WebPage对象
        webpage = WebPage(
            url="https://example.com",
            title="无图片页面",
            description="无图片描述",
            content="这是一个没有图片的页面\n\n只有文字内容",
            success=True
        )

        # 测试无图片页面
        mode_with_images = URLListMode(with_images=True)
        result = mode_with_images.webpage_to_dict(webpage)

        assert "images" in result
        assert result["images"] == []  # 应该是空数组

    def test_webpage_to_dict_with_relative_images(self):
        """测试相对路径图片URL的处理"""
        # 创建包含相对路径图片的WebPage对象
        webpage = WebPage(
            url="https://example.com/path/page.html",
            title="相对路径图片测试",
            description="测试描述",
            content="包含相对路径图片\n\n![相对图片](../images/relative.png)\n\n![根路径图片](/images/root.png)",
            success=True
        )

        # 测试相对路径URL解析
        mode_with_images = URLListMode(with_images=True)
        result = mode_with_images.webpage_to_dict(webpage)

        assert "images" in result
        # 应该将相对路径转换为绝对路径
        expected_images = [
            "https://example.com/images/relative.png",  # ../images/relative.png
            "https://example.com/images/root.png"        # /images/root.png
        ]
        assert result["images"] == expected_images

    @pytest.mark.asyncio
    async def test_run_url_list_mode_function(self):
        """测试run_url_list_mode便捷函数"""
        # Mock fetcher.fetch_batch
        mock_webpages = [
            WebPage(
                url="https://example.com",
                title="测试页面",
                description="测试描述",
                content="![图片](https://example.com/img.png)",
                success=True
            )
        ]

        with patch('src.url_list_mode.AsyncWebFetcher') as MockFetcher:
            mock_fetcher_instance = AsyncMock()
            mock_fetcher_instance.fetch_batch.return_value = mock_webpages
            MockFetcher.return_value = mock_fetcher_instance

            from src.url_list_mode import run_url_list_mode

            # 测试不启用图片提取
            with patch('sys.stdout'):  # 抑制输出
                await run_url_list_mode("https://example.com", with_images=False)

            # 验证fetcher被正确初始化
            MockFetcher.assert_called_with(
                use_playwright=True,
                concurrency=None
            )

            # 测试启用图片提取
            with patch('sys.stdout'):  # 抑制输出
                await run_url_list_mode("https://example.com", with_images=True)

    def test_webpage_to_dict_with_invalid_images(self):
        """测试包含无效图片URL的情况"""
        # 创建包含各种图片URL的WebPage对象
        webpage = WebPage(
            url="https://example.com",
            title="无效图片测试",
            description="测试描述",
            content="""
![有效图片](https://example.com/valid.png)
![data URI图片](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==)
![空图片]()
![相对图片](../images/relative.png)
""",
            success=True
        )

        # 测试过滤无效图片URL
        mode_with_images = URLListMode(with_images=True)
        result = mode_with_images.webpage_to_dict(webpage)

        assert "images" in result
        # 应该只包含有效的http/https URL
        expected_images = [
            "https://example.com/valid.png",
            "https://example.com/images/relative.png"  # 相对路径被转换为绝对路径
        ]
        assert result["images"] == expected_images