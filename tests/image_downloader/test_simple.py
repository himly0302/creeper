"""
简单的功能测试脚本
用于验证图片下载功能是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import tempfile
import shutil

from src.image_downloader import ImageDownloader


def test_extract_urls():
    """测试 URL 提取"""
    print("\n=== 测试 URL 提取功能 ===")

    downloader = ImageDownloader(base_url="https://example.com/page")

    markdown = """
# Test Document

![Logo](https://example.com/logo.png)
![Banner](https://cdn.example.com/images/banner.jpg)
![Data URI](data:image/png;base64,iVBORw0KG...)
![Relative](/static/img.png)

Regular text.
    """

    urls = downloader.extract_image_urls(markdown)

    print(f"找到 {len(urls)} 个图片 URL:")
    for alt, url in urls:
        print(f"  - [{alt}] {url}")

    assert len(urls) == 3, f"预期 3 个 URL，实际 {len(urls)} 个"
    assert ('Logo', 'https://example.com/logo.png') in urls
    assert ('Banner', 'https://cdn.example.com/images/banner.jpg') in urls
    assert ('Relative', 'https://example.com/static/img.png') in urls

    print("✓ URL 提取测试通过")


def test_filename_generation():
    """测试文件名生成"""
    print("\n=== 测试文件名生成功能 ===")

    downloader = ImageDownloader()

    test_cases = [
        ("https://example.com/images/python-logo.png", "image/png", ".png"),
        ("https://example.com/get_image", "image/jpeg", ".jpg"),
        ("https://cdn.example.com/photo.webp", "image/webp", ".webp"),
    ]

    for url, content_type, expected_ext in test_cases:
        filename = downloader._generate_filename(url, content_type)
        print(f"  {url} -> {filename}")
        assert filename.endswith(expected_ext), f"预期扩展名 {expected_ext}，实际 {filename}"

    print("✓ 文件名生成测试通过")


def test_ssrf_protection():
    """测试 SSRF 防护"""
    print("\n=== 测试 SSRF 防护功能 ===")

    downloader = ImageDownloader()
    temp_dir = Path(tempfile.mkdtemp())

    try:
        dangerous_urls = [
            "http://localhost/image.png",
            "http://127.0.0.1/image.png",
            "http://192.168.1.1/image.png",
            "http://10.0.0.1/image.png",
        ]

        for url in dangerous_urls:
            result = downloader.download_image(url, temp_dir)
            print(f"  {url} -> 被拦截: {result.error}")
            assert result.success is False, f"URL {url} 应该被拦截"
            assert "不允许下载内网资源" in result.error

        print("✓ SSRF 防护测试通过")
    finally:
        shutil.rmtree(temp_dir)


def test_markdown_replacement():
    """测试 Markdown URL 替换"""
    print("\n=== 测试 Markdown URL 替换功能 ===")

    downloader = ImageDownloader()
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # 测试没有图片的情况
        markdown_no_images = "# No Images\n\nJust text."
        result = downloader.process_markdown(markdown_no_images, temp_dir)
        assert result == markdown_no_images, "没有图片时应该返回原始内容"
        print("  ✓ 无图片处理正确")

        # 测试内网 URL（会被拦截，保留原始 URL）
        markdown_localhost = "![Test](http://localhost/image.png)"
        result = downloader.process_markdown(markdown_localhost, temp_dir)
        assert result == markdown_localhost, "内网 URL 应该保留原始内容"
        print("  ✓ 内网 URL 保留原始内容")

        print("✓ Markdown 替换测试通过")
    finally:
        shutil.rmtree(temp_dir)
        downloader.close()


def test_cache_mechanism():
    """测试缓存机制"""
    print("\n=== 测试缓存机制 ===")

    downloader = ImageDownloader()

    from src.image_downloader import ImageInfo

    test_url = "https://example.com/test.png"
    cached_info = ImageInfo(
        original_url=test_url,
        local_path="images/test.png",
        filename="test.png",
        success=True
    )

    # 手动设置缓存
    downloader._download_cache[test_url] = cached_info

    # 第二次调用应该返回缓存
    result = downloader.download_image(test_url, Path("/tmp"))

    assert result.original_url == test_url
    assert result.local_path == "images/test.png"
    assert result.success is True

    print("✓ 缓存机制测试通过")


def run_all_tests():
    """运行所有测试"""
    print("开始运行图片下载器功能测试...")
    print("=" * 50)

    try:
        test_extract_urls()
        test_filename_generation()
        test_ssrf_protection()
        test_markdown_replacement()
        test_cache_mechanism()

        print("\n" + "=" * 50)
        print("✓ 所有测试通过！")
        return True
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
