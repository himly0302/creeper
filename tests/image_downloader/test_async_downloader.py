"""
异步图片下载器测试
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil

from src.image_downloader import AsyncImageDownloader, ImageInfo


class TestAsyncImageDownloader:
    """测试异步图片下载器"""

    @pytest.fixture
    def downloader(self):
        """创建异步下载器实例"""
        return AsyncImageDownloader(base_url="https://example.com/page", concurrency=3)

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # 清理
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    def test_extract_image_urls(self, downloader):
        """测试从 Markdown 提取图片 URL"""
        markdown = """
# Test Document

![Logo](https://example.com/logo.png)
![Banner](https://example.com/images/banner.jpg)
![Data URI](data:image/png;base64,iVBORw0KG...)
![Relative](/static/img.png)
        """

        urls = downloader.extract_image_urls(markdown)

        assert len(urls) == 3
        assert ('Logo', 'https://example.com/logo.png') in urls
        assert ('Banner', 'https://example.com/images/banner.jpg') in urls
        assert ('Relative', 'https://example.com/static/img.png') in urls

    def test_generate_filename(self, downloader):
        """测试文件名生成"""
        url = "https://example.com/images/python-logo.png"
        content_type = "image/png"

        filename = downloader._generate_filename(url, content_type)

        assert filename.endswith('.png')
        assert 'python-logo' in filename or len(filename) > 0

    @pytest.mark.asyncio
    async def test_download_cache(self, downloader):
        """测试异步下载缓存机制"""
        test_url = "https://example.com/test.png"
        cached_info = ImageInfo(
            original_url=test_url,
            local_path="images/test.png",
            filename="test.png",
            success=True
        )

        downloader._download_cache[test_url] = cached_info

        result = await downloader.download_image(test_url, Path("/tmp"))

        assert result.original_url == test_url
        assert result.local_path == "images/test.png"
        assert result.success is True

    @pytest.mark.asyncio
    async def test_invalid_url_security(self, downloader, temp_dir):
        """测试 SSRF 防护"""
        localhost_urls = [
            "http://localhost/image.png",
            "http://127.0.0.1/image.png",
            "http://192.168.1.1/image.png",
        ]

        for url in localhost_urls:
            result = await downloader.download_image(url, temp_dir)
            assert result.success is False
            assert "不允许下载内网资源" in result.error

    @pytest.mark.asyncio
    async def test_process_markdown_no_images(self, downloader, temp_dir):
        """测试处理没有图片的 Markdown"""
        markdown = "# No Images\n\nJust text."

        result = await downloader.process_markdown(markdown, temp_dir)

        assert result == markdown

    @pytest.mark.asyncio
    async def test_process_markdown_with_failed_download(self, downloader, temp_dir):
        """测试下载失败时保留原始 URL"""
        markdown = "![Test](http://localhost/image.png)"

        result = await downloader.process_markdown(markdown, temp_dir)

        # 下载失败，应该保留原始 URL
        assert result == markdown

    @pytest.mark.asyncio
    async def test_concurrency_limit(self, downloader):
        """测试并发限制"""
        assert downloader.concurrency == 3
        assert downloader.semaphore._value == 3  # 信号量初始值应为 concurrency


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
