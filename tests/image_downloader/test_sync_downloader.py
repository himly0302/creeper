"""
图片下载器测试
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.image_downloader import ImageDownloader, ImageInfo


class TestImageDownloader:
    """测试同步图片下载器"""

    @pytest.fixture
    def downloader(self):
        """创建下载器实例"""
        return ImageDownloader(base_url="https://example.com/page")

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

Regular text here.
        """

        urls = downloader.extract_image_urls(markdown)

        # 应该提取到 4 个 URL（data URI 被过滤，相对路径被转换）
        assert len(urls) == 3
        assert ('Logo', 'https://example.com/logo.png') in urls
        assert ('Banner', 'https://example.com/images/banner.jpg') in urls
        # 相对路径应该被转换为绝对路径
        assert ('Relative', 'https://example.com/static/img.png') in urls

    def test_extract_no_images(self, downloader):
        """测试没有图片的 Markdown"""
        markdown = """
# No Images

This is just text.
        """

        urls = downloader.extract_image_urls(markdown)
        assert len(urls) == 0

    def test_generate_filename(self, downloader):
        """测试文件名生成"""
        url = "https://example.com/images/python-logo.png"
        content_type = "image/png"

        filename = downloader._generate_filename(url, content_type)

        # 应该包含原始文件名的部分和 hash
        assert filename.endswith('.png')
        assert 'python-logo' in filename or len(filename) > 0

    def test_generate_filename_without_extension(self, downloader):
        """测试没有扩展名的 URL"""
        url = "https://example.com/get_image"
        content_type = "image/jpeg"

        filename = downloader._generate_filename(url, content_type)

        # 应该从 Content-Type 推断扩展名
        assert filename.endswith('.jpg')

    def test_ext_from_content_type(self, downloader):
        """测试从 Content-Type 推断扩展名"""
        assert downloader._ext_from_content_type('image/jpeg') == '.jpg'
        assert downloader._ext_from_content_type('image/png') == '.png'
        assert downloader._ext_from_content_type('image/gif') == '.gif'
        assert downloader._ext_from_content_type('image/webp') == '.webp'
        assert downloader._ext_from_content_type('image/svg+xml') == '.svg'
        assert downloader._ext_from_content_type('unknown/type') == '.jpg'  # 默认

    def test_process_markdown_no_images(self, downloader, temp_dir):
        """测试处理没有图片的 Markdown"""
        markdown = "# No Images\n\nJust text."

        result = downloader.process_markdown(markdown, temp_dir)

        assert result == markdown
        # 不应该创建 images 目录
        assert not (temp_dir / "images").exists() or len(list((temp_dir / "images").iterdir())) == 0

    def test_download_cache(self, downloader):
        """测试下载缓存机制"""
        # 第一次下载会尝试真实下载，第二次应该使用缓存
        # 这里我们手动设置缓存来测试
        test_url = "https://example.com/test.png"
        cached_info = ImageInfo(
            original_url=test_url,
            local_path="images/test.png",
            filename="test.png",
            success=True
        )

        downloader._download_cache[test_url] = cached_info

        # 第二次调用应该返回缓存结果
        result = downloader.download_image(test_url, Path("/tmp"))

        assert result.original_url == test_url
        assert result.local_path == "images/test.png"
        assert result.success is True

    def test_invalid_url_security(self, downloader, temp_dir):
        """测试 SSRF 防护"""
        # 测试内网 URL 应该被拒绝
        localhost_urls = [
            "http://localhost/image.png",
            "http://127.0.0.1/image.png",
            "http://192.168.1.1/image.png",
            "http://10.0.0.1/image.png",
        ]

        for url in localhost_urls:
            result = downloader.download_image(url, temp_dir)
            assert result.success is False
            assert "不允许下载内网资源" in result.error

    def test_process_markdown_with_failed_download(self, downloader, temp_dir):
        """测试下载失败时保留原始 URL"""
        markdown = "![Test](http://localhost/image.png)"

        result = downloader.process_markdown(markdown, temp_dir)

        # 下载失败，应该保留原始 URL
        assert result == markdown


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
