"""
图片下载器模块

支持同步和异步两种模式，从 Markdown 中提取图片 URL，
下载到本地，并替换为相对路径。
"""

import os
import re
import hashlib
import asyncio
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass

import requests
import aiohttp

from src.config import config
from src.utils import setup_logger

logger = setup_logger(__name__)


@dataclass
class ImageInfo:
    """图片信息"""
    original_url: str      # 原始 URL
    local_path: str        # 本地相对路径（如 "images/python-logo.png"）
    filename: str          # 文件名
    success: bool          # 是否下载成功
    error: Optional[str] = None  # 错误信息


class ImageDownloader:
    """同步图片下载器"""

    # Markdown 图片 URL 正则表达式
    IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

    def __init__(self, base_url: Optional[str] = None):
        """
        初始化图片下载器

        Args:
            base_url: 网页的基础 URL，用于解析相对路径图片
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # 支持的图片格式（从配置读取）
        formats_str = os.getenv('SUPPORTED_IMAGE_FORMATS', '.jpg,.jpeg,.png,.gif,.webp,.svg')
        self.supported_formats = [fmt.strip() for fmt in formats_str.split(',')]

        # 最大图片大小（MB）
        self.max_size_mb = config.MAX_IMAGE_SIZE_MB
        self.max_size_bytes = self.max_size_mb * 1024 * 1024

        # 超时时间
        self.timeout = config.IMAGE_DOWNLOAD_TIMEOUT

        # 下载缓存（避免重复下载相同 URL）
        self._download_cache: Dict[str, ImageInfo] = {}

    def extract_image_urls(self, markdown_content: str) -> List[Tuple[str, str, str]]:
        """
        从 Markdown 中提取图片 URL

        Args:
            markdown_content: Markdown 文本内容

        Returns:
            [(alt_text, original_markdown_url, resolved_url), ...] 列表
            - original_markdown_url: Markdown 中的原始 URL（用于替换）
            - resolved_url: 解析后的完整 URL（用于下载）
        """
        matches = self.IMAGE_PATTERN.findall(markdown_content)

        # 过滤和规范化 URL
        image_urls = []
        for alt_text, url in matches:
            # 移除空白字符
            url = url.strip()
            alt_text = alt_text.strip()

            # 跳过 data URI 和空 URL
            if not url or url.startswith('data:'):
                continue

            # 保存原始 URL（用于替换）
            original_markdown_url = url

            # 处理相对路径（需要 base_url）
            if self.base_url and not url.startswith(('http://', 'https://')):
                url = urljoin(self.base_url, url)

            # 只保留 http/https URL
            if url.startswith(('http://', 'https://')):
                image_urls.append((alt_text, original_markdown_url, url))

        return image_urls

    def download_image(self, url: str, save_dir: Path) -> ImageInfo:
        """
        下载单张图片

        Args:
            url: 图片 URL
            save_dir: 保存目录（绝对路径）

        Returns:
            ImageInfo 对象
        """
        # 检查缓存
        if url in self._download_cache:
            logger.debug(f"图片已存在缓存，跳过下载: {url}")
            return self._download_cache[url]

        try:
            # 验证 URL 安全性（防止 SSRF）
            parsed = urlparse(url)
            if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0'] or \
               parsed.hostname.startswith('192.168.') or \
               parsed.hostname.startswith('10.') or \
               parsed.hostname.startswith('172.'):
                raise ValueError(f"不允许下载内网资源: {url}")

            # 发送 HEAD 请求检查文件信息
            head_response = self.session.head(url, timeout=10, allow_redirects=True)

            # 检查 Content-Type
            content_type = head_response.headers.get('Content-Type', '').lower()
            if not content_type.startswith('image/'):
                logger.warning(f"⚠ URL 不是图片类型 ({content_type}): {url}")
                return ImageInfo(url, "", "", False, f"非图片类型: {content_type}")

            # 检查文件大小
            content_length = head_response.headers.get('Content-Length')
            if content_length and int(content_length) > self.max_size_bytes:
                size_mb = int(content_length) / 1024 / 1024
                logger.warning(f"⚠ 图片超过大小限制 ({size_mb:.1f}MB > {self.max_size_mb}MB): {url}")
                return ImageInfo(url, "", "", False, f"文件过大: {size_mb:.1f}MB")

            # 下载图片
            logger.debug(f"开始下载图片: {url}")
            response = self.session.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()

            # 生成文件名（基于 URL 的 hash + 扩展名）
            filename = self._generate_filename(url, content_type)

            # 确保保存目录存在
            save_dir.mkdir(parents=True, exist_ok=True)

            # 保存文件
            file_path = save_dir / filename

            # 处理文件名冲突（添加序号）
            counter = 1
            original_filename = filename
            while file_path.exists():
                name, ext = os.path.splitext(original_filename)
                filename = f"{name}-{counter}{ext}"
                file_path = save_dir / filename
                counter += 1

            # 流式写入（节省内存）
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"✓ 图片已下载: {filename}")

            # 相对路径（相对于 Markdown 文件）
            local_path = f"images/{filename}"

            # 创建结果对象
            result = ImageInfo(url, local_path, filename, True)

            # 缓存结果
            self._download_cache[url] = result

            return result

        except Exception as e:
            logger.warning(f"⚠ 图片下载失败，保留原始URL: {url} - {e}")
            return ImageInfo(url, "", "", False, str(e))

    def _generate_filename(self, url: str, content_type: str) -> str:
        """
        生成安全的文件名

        Args:
            url: 图片 URL
            content_type: Content-Type 头

        Returns:
            文件名（如 "abc123.png"）
        """
        # 从 URL 中提取原始文件名
        parsed = urlparse(url)
        path = parsed.path
        original_name = os.path.basename(path)

        # 提取扩展名
        _, ext = os.path.splitext(original_name)

        # 如果没有扩展名，从 Content-Type 推断
        if not ext or ext not in self.supported_formats:
            ext = self._ext_from_content_type(content_type)

        # 生成 hash（使用 URL 的 MD5，前 12 位）
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]

        # 如果原始名称有意义（非随机字符串），保留一部分
        name_part = ""
        if original_name and len(original_name) > 0:
            # 移除扩展名和特殊字符
            clean_name = re.sub(r'[^a-zA-Z0-9\-_\u4e00-\u9fa5]', '-',
                               os.path.splitext(original_name)[0])
            # 限制长度
            if clean_name and len(clean_name) <= 30:
                name_part = clean_name[:30] + "-"

        # 组合文件名
        filename = f"{name_part}{url_hash}{ext}"

        return filename

    def _ext_from_content_type(self, content_type: str) -> str:
        """
        从 Content-Type 推断文件扩展名

        Args:
            content_type: Content-Type 头

        Returns:
            扩展名（如 ".png"）
        """
        content_type = content_type.lower()

        mapping = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/svg+xml': '.svg',
        }

        return mapping.get(content_type, '.jpg')

    def process_markdown(self, markdown_content: str, save_dir: Path) -> str:
        """
        处理 Markdown 内容：下载图片并替换 URL

        Args:
            markdown_content: 原始 Markdown 内容
            save_dir: 图片保存目录（绝对路径）

        Returns:
            处理后的 Markdown 内容（图片 URL 已替换为本地路径）
        """
        # 提取所有图片 URL
        image_urls = self.extract_image_urls(markdown_content)

        if not image_urls:
            logger.debug("Markdown 中未发现图片")
            return markdown_content

        logger.info(f"发现 {len(image_urls)} 张图片，开始下载...")

        # 下载所有图片
        results = []
        for alt_text, original_markdown_url, resolved_url in image_urls:
            result = self.download_image(resolved_url, save_dir)
            results.append((alt_text, original_markdown_url, result))

        # 替换 Markdown 中的图片 URL
        processed_content = markdown_content

        for alt_text, original_markdown_url, result in results:
            if result.success:
                # 使用原始 Markdown 中的 URL 进行替换
                old_pattern = f"![{alt_text}]({original_markdown_url})"
                new_pattern = f"![{alt_text}]({result.local_path})"
                processed_content = processed_content.replace(old_pattern, new_pattern)
            # 下载失败时保留原始 URL（不做替换）

        # 统计
        success_count = sum(1 for _, _, r in results if r.success)
        logger.info(f"✓ 图片下载完成: {success_count}/{len(results)} 成功")

        return processed_content

    def close(self):
        """关闭会话"""
        self.session.close()


class AsyncImageDownloader:
    """异步图片下载器"""

    IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

    def __init__(self, base_url: Optional[str] = None, concurrency: int = 5):
        """
        初始化异步图片下载器

        Args:
            base_url: 网页的基础 URL，用于解析相对路径图片
            concurrency: 并发下载数
        """
        self.base_url = base_url
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)

        # 支持的图片格式
        formats_str = os.getenv('SUPPORTED_IMAGE_FORMATS', '.jpg,.jpeg,.png,.gif,.webp,.svg')
        self.supported_formats = [fmt.strip() for fmt in formats_str.split(',')]

        # 最大图片大小（MB）
        self.max_size_mb = config.MAX_IMAGE_SIZE_MB
        self.max_size_bytes = self.max_size_mb * 1024 * 1024

        # 超时时间
        self.timeout = aiohttp.ClientTimeout(total=config.IMAGE_DOWNLOAD_TIMEOUT)

        # 下载缓存
        self._download_cache: Dict[str, ImageInfo] = {}

    def extract_image_urls(self, markdown_content: str) -> List[Tuple[str, str, str]]:
        """
        从 Markdown 中提取图片 URL

        Args:
            markdown_content: Markdown 文本内容

        Returns:
            [(alt_text, original_markdown_url, resolved_url), ...] 列表
            - original_markdown_url: Markdown 中的原始 URL（用于替换）
            - resolved_url: 解析后的完整 URL（用于下载）
        """
        matches = self.IMAGE_PATTERN.findall(markdown_content)

        image_urls = []
        for alt_text, url in matches:
            url = url.strip()
            alt_text = alt_text.strip()

            if not url or url.startswith('data:'):
                continue

            # 保存原始 URL（用于替换）
            original_markdown_url = url

            if self.base_url and not url.startswith(('http://', 'https://')):
                url = urljoin(self.base_url, url)

            if url.startswith(('http://', 'https://')):
                image_urls.append((alt_text, original_markdown_url, url))

        return image_urls

    async def download_image(self, url: str, save_dir: Path) -> ImageInfo:
        """
        异步下载单张图片

        Args:
            url: 图片 URL
            save_dir: 保存目录（绝对路径）

        Returns:
            ImageInfo 对象
        """
        # 检查缓存
        if url in self._download_cache:
            logger.debug(f"图片已存在缓存，跳过下载: {url}")
            return self._download_cache[url]

        async with self.semaphore:  # 限制并发
            try:
                # 验证 URL 安全性
                parsed = urlparse(url)
                if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0'] or \
                   parsed.hostname.startswith('192.168.') or \
                   parsed.hostname.startswith('10.') or \
                   parsed.hostname.startswith('172.'):
                    raise ValueError(f"不允许下载内网资源: {url}")

                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    # HEAD 请求检查文件信息
                    async with session.head(url, allow_redirects=True) as head_response:
                        # 检查 Content-Type
                        content_type = head_response.headers.get('Content-Type', '').lower()
                        if not content_type.startswith('image/'):
                            logger.warning(f"⚠ URL 不是图片类型 ({content_type}): {url}")
                            return ImageInfo(url, "", "", False, f"非图片类型: {content_type}")

                        # 检查文件大小
                        content_length = head_response.headers.get('Content-Length')
                        if content_length and int(content_length) > self.max_size_bytes:
                            size_mb = int(content_length) / 1024 / 1024
                            logger.warning(f"⚠ 图片超过大小限制 ({size_mb:.1f}MB > {self.max_size_mb}MB): {url}")
                            return ImageInfo(url, "", "", False, f"文件过大: {size_mb:.1f}MB")

                    # 下载图片
                    logger.debug(f"开始下载图片: {url}")
                    async with session.get(url) as response:
                        response.raise_for_status()

                        # 生成文件名
                        filename = self._generate_filename(url, content_type)

                        # 确保保存目录存在
                        save_dir.mkdir(parents=True, exist_ok=True)

                        # 保存文件
                        file_path = save_dir / filename

                        # 处理文件名冲突
                        counter = 1
                        original_filename = filename
                        while file_path.exists():
                            name, ext = os.path.splitext(original_filename)
                            filename = f"{name}-{counter}{ext}"
                            file_path = save_dir / filename
                            counter += 1

                        # 流式写入
                        with open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)

                        logger.info(f"✓ 图片已下载: {filename}")

                        # 相对路径
                        local_path = f"images/{filename}"

                        # 创建结果对象
                        result = ImageInfo(url, local_path, filename, True)

                        # 缓存结果
                        self._download_cache[url] = result

                        return result

            except Exception as e:
                logger.warning(f"⚠ 图片下载失败，保留原始URL: {url} - {e}")
                return ImageInfo(url, "", "", False, str(e))

    def _generate_filename(self, url: str, content_type: str) -> str:
        """生成安全的文件名（与同步版本相同）"""
        parsed = urlparse(url)
        path = parsed.path
        original_name = os.path.basename(path)

        _, ext = os.path.splitext(original_name)

        if not ext or ext not in self.supported_formats:
            ext = self._ext_from_content_type(content_type)

        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]

        name_part = ""
        if original_name and len(original_name) > 0:
            clean_name = re.sub(r'[^a-zA-Z0-9\-_\u4e00-\u9fa5]', '-',
                               os.path.splitext(original_name)[0])
            if clean_name and len(clean_name) <= 30:
                name_part = clean_name[:30] + "-"

        filename = f"{name_part}{url_hash}{ext}"

        return filename

    def _ext_from_content_type(self, content_type: str) -> str:
        """从 Content-Type 推断文件扩展名（与同步版本相同）"""
        content_type = content_type.lower()

        mapping = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/svg+xml': '.svg',
        }

        return mapping.get(content_type, '.jpg')

    async def process_markdown(self, markdown_content: str, save_dir: Path) -> str:
        """
        异步处理 Markdown 内容：下载图片并替换 URL

        Args:
            markdown_content: 原始 Markdown 内容
            save_dir: 图片保存目录（绝对路径）

        Returns:
            处理后的 Markdown 内容
        """
        # 提取所有图片 URL
        image_urls = self.extract_image_urls(markdown_content)

        if not image_urls:
            logger.debug("Markdown 中未发现图片")
            return markdown_content

        logger.info(f"发现 {len(image_urls)} 张图片，开始异步下载...")

        # 异步下载所有图片（使用解析后的 URL）
        tasks = [self.download_image(resolved_url, save_dir)
                for _, _, resolved_url in image_urls]
        results_list = await asyncio.gather(*tasks)

        # 组合结果（使用原始 Markdown URL）
        results = [(alt_text, original_markdown_url, result)
                   for (alt_text, original_markdown_url, _), result in zip(image_urls, results_list)]

        # 替换 Markdown 中的图片 URL
        processed_content = markdown_content

        for alt_text, original_markdown_url, result in results:
            if result.success:
                # 使用原始 Markdown 中的 URL 进行替换
                old_pattern = f"![{alt_text}]({original_markdown_url})"
                new_pattern = f"![{alt_text}]({result.local_path})"
                processed_content = processed_content.replace(old_pattern, new_pattern)

        # 统计
        success_count = sum(1 for _, _, r in results if r.success)
        logger.info(f"✓ 图片下载完成: {success_count}/{len(results)} 成功")

        return processed_content
