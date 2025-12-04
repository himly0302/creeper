"""
智能图片下载功能测试

测试从清洗后的内容中提取和下载图片的功能
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.image_downloader import ImageDownloader, AsyncImageDownloader, ImageInfo
from src.cleaner import ContentCleaner


class TestSmartImageDownload:
    """智能图片下载测试"""

    def setup_method(self):
        """测试前设置"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.base_url = "https://example.com"

    def teardown_method(self):
        """测试后清理"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_extract_markdown_images_clean_content(self):
        """测试从清洗后的内容中提取图片 URL"""
        downloader = ImageDownloader(base_url=self.base_url)

        # 模拟清洗后的内容（包含有效图片引用）
        clean_content = """
        # 测试文章

        这是一篇测试文章，包含一些图片：

        ![示例图片1](https://example.com/image1.jpg)
        ![相对路径图片](./images/local.png)
        ![数据URI图片](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==)

        文章内容继续...
        """

        # 提取图片 URL
        image_urls = downloader.extract_markdown_images(clean_content)

        # 验证结果
        assert len(image_urls) == 2
        assert "https://example.com/image1.jpg" in image_urls
        assert "https://example.com/images/local.png" in image_urls
        # data URI 应该被过滤掉

    def test_extract_markdown_images_no_images(self):
        """测试没有图片的内容"""
        downloader = ImageDownloader(base_url=self.base_url)

        # 没有图片的内容
        clean_content = """
        # 无图片文章

        这是一篇没有任何图片的文章。
        只有纯文本内容。
        """

        # 提取图片 URL
        image_urls = downloader.extract_markdown_images(clean_content)

        # 验证结果
        assert len(image_urls) == 0

    def test_download_valid_images_success(self):
        """测试下载有效图片成功"""
        downloader = ImageDownloader(base_url=self.base_url)

        # 模拟内容
        content = """
        # 测试内容

        ![测试图片](https://example.com/test.jpg)
        """

        # 模拟图片 URL 列表
        image_urls = ["https://example.com/test.jpg"]

        # Mock download_image 方法
        mock_image_info = ImageInfo(
            original_url="https://example.com/test.jpg",
            local_path="images/test-hash.jpg",
            filename="test-hash.jpg",
            success=True
        )

        with patch.object(downloader, 'download_image', return_value=mock_image_info):
            result_content = downloader.download_valid_images(content, image_urls, self.temp_dir)

        # 验证结果
        assert "images/test-hash.jpg" in result_content
        assert "https://example.com/test.jpg" not in result_content

    def test_download_valid_images_failure(self):
        """测试下载图片失败时的处理"""
        downloader = ImageDownloader(base_url=self.base_url)

        # 模拟内容
        content = """
        # 测试内容

        ![测试图片](https://example.com/test.jpg)
        """

        # 模拟图片 URL 列表
        image_urls = ["https://example.com/test.jpg"]

        # Mock download_image 方法返回失败
        mock_image_info = ImageInfo(
            original_url="https://example.com/test.jpg",
            local_path="",
            filename="",
            success=False,
            error="下载失败"
        )

        with patch.object(downloader, 'download_image', return_value=mock_image_info):
            result_content = downloader.download_valid_images(content, image_urls, self.temp_dir)

        # 验证结果：下载失败时保留原始 URL
        assert "https://example.com/test.jpg" in result_content

    def test_smart_download_workflow(self):
        """测试完整的智能下载工作流程"""
        # 模拟原始内容（包含图片，但有些可能在清洗后被移除）
        original_content = """
        # 原始内容

        这是一篇包含大量图片的文章：

        ![有效图片1](https://example.com/valid1.jpg)
        ![广告图片](https://ads.example.com/ad.gif)
        ![有效图片2](https://example.com/valid2.png)
        <img src="https://example.com/html-tag.jpg" alt="HTML标签图片">
        """

        # 模拟内容清洗过程（移除广告和HTML标签）
        cleaned_content = ContentCleaner.clean(original_content)

        # 创建下载器
        downloader = ImageDownloader(base_url=self.base_url)

        # 从清洗后的内容中提取图片
        markdown_images = downloader.extract_markdown_images(cleaned_content)

        # Mock 图片下载
        def mock_download_image(url, save_dir):
            if "valid" in url:
                filename = f"downloaded-{url.split('/')[-1]}"
                return ImageInfo(
                    original_url=url,
                    local_path=f"images/{filename}",
                    filename=filename,
                    success=True
                )
            else:
                return ImageInfo(
                    original_url=url,
                    local_path="",
                    filename="",
                    success=False,
                    error="无效图片"
                )

        with patch.object(downloader, 'download_image', side_effect=mock_download_image):
            # 只下载清洗后内容中存在的图片
            final_content = downloader.download_valid_images(
                cleaned_content, markdown_images, self.temp_dir
            )

        # 验证结果
        assert len(markdown_images) >= 1  # 至少有一个有效图片
        assert "images/downloaded-" in final_content  # 包含下载后的图片路径


class TestAsyncSmartImageDownload:
    """异步智能图片下载测试"""

    def setup_method(self):
        """测试前设置"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.base_url = "https://example.com"

    def teardown_method(self):
        """测试后清理"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_async_extract_markdown_images(self):
        """测试异步版本从清洗后的内容中提取图片 URL"""
        downloader = AsyncImageDownloader(base_url=self.base_url)

        # 模拟清洗后的内容
        clean_content = """
        # 异步测试文章

        ![异步图片1](https://example.com/async1.jpg)
        ![异步图片2](./images/async2.png)
        """

        # 提取图片 URL
        image_urls = downloader.extract_markdown_images(clean_content)

        # 验证结果
        assert len(image_urls) == 2
        assert "https://example.com/async1.jpg" in image_urls
        assert "https://example.com/images/async2.png" in image_urls

    @pytest.mark.asyncio
    async def test_async_download_valid_images(self):
        """测试异步下载有效图片"""
        downloader = AsyncImageDownloader(base_url=self.base_url)

        # 模拟内容
        content = """
        # 异步测试内容

        ![异步测试图片](https://example.com/async-test.jpg)
        """

        # 模拟图片 URL 列表
        image_urls = ["https://example.com/async-test.jpg"]

        # Mock download_image 方法
        mock_image_info = ImageInfo(
            original_url="https://example.com/async-test.jpg",
            local_path="images/async-test-hash.jpg",
            filename="async-test-hash.jpg",
            success=True
        )

        with patch.object(downloader, 'download_image', return_value=mock_image_info):
            result_content = await downloader.download_valid_images(content, image_urls, self.temp_dir)

        # 验证结果
        assert "images/async-test-hash.jpg" in result_content
        assert "https://example.com/async-test.jpg" not in result_content

    @pytest.mark.asyncio
    async def test_async_concurrent_download(self):
        """测试异步并发下载"""
        downloader = AsyncImageDownloader(base_url=self.base_url, concurrency=3)

        # 模拟包含多个图片的内容
        content = """
        # 并发测试内容

        ![图片1](https://example.com/img1.jpg)
        ![图片2](https://example.com/img2.jpg)
        ![图片3](https://example.com/img3.jpg)
        """

        # 提取图片 URL
        image_urls = downloader.extract_markdown_images(content)

        # Mock 异步下载
        async def mock_download_image(url, save_dir):
            # 模拟下载延迟
            import asyncio
            await asyncio.sleep(0.1)

            return ImageInfo(
                original_url=url,
                local_path=f"images/{url.split('/')[-1]}",
                filename=url.split('/')[-1],
                success=True
            )

        with patch.object(downloader, 'download_image', side_effect=mock_download_image):
            # 测试并发下载
            result_content = await downloader.download_valid_images(content, image_urls, self.temp_dir)

        # 验证所有图片都被下载和替换
        for img_name in ["img1.jpg", "img2.jpg", "img3.jpg"]:
            assert f"images/{img_name}" in result_content


class TestContentFiltering:
    """测试内容过滤效果"""

    def test_content_cleaning_removes_images(self):
        """测试内容清洗可能移除某些图片"""
        # 模拟包含广告图片的原始内容
        original_content = """
        # 原始文章

        文章内容：

        ![正文图片](https://example.com/content.jpg)

        <div class="advertisement">
            ![广告图片](https://ads.example.com/banner.gif)
        </div>

        更多正文内容...
        """

        # 模拟内容清洗（可能移除广告相关内容）
        # 注意：这里只是示例，实际的 ContentCleaner 可能不会移除图片
        # 我们测试的是基于清洗后内容的图片提取

        # 模拟清洗后的内容（广告被移除）
        cleaned_content = """
        # 原始文章

        文章内容：

        ![正文图片](https://example.com/content.jpg)

        更多正文内容...
        """

        # 创建下载器
        downloader = ImageDownloader(base_url="https://example.com")

        # 从清洗后的内容中提取图片
        markdown_images = downloader.extract_markdown_images(cleaned_content)

        # 验证：只提取了正文图片，广告图片被过滤掉
        assert len(markdown_images) == 1
        assert "https://example.com/content.jpg" in markdown_images
        assert "https://ads.example.com/banner.gif" not in markdown_images

    def test_deduplicate_image_urls(self):
        """测试图片 URL 去重"""
        downloader = ImageDownloader(base_url=self.base_url)

        # 包含重复图片引用的内容
        content_with_duplicates = """
        # 重复图片测试

        ![重复图片](https://example.com/duplicate.jpg)
        一些文本...
        ![重复图片](https://example.com/duplicate.jpg)
        更多文本...
        ![重复图片](https://example.com/duplicate.jpg)
        """

        # 提取图片 URL
        image_urls = downloader.extract_markdown_images(content_with_duplicates)

        # 验证去重效果
        assert len(image_urls) == 1
        assert "https://example.com/duplicate.jpg" in image_urls