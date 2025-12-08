"""
图片下载器模块

支持异步模式，从 Markdown 中提取图片 URL，
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
import asyncio
from concurrent.futures import ThreadPoolExecutor

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

        # 超时时间（分离连接超时和总超时）
        self.timeout = aiohttp.ClientTimeout(
            total=config.IMAGE_DOWNLOAD_TIMEOUT,
            connect=10,  # 连接超时10秒
            sock_read=15  # 读取超时15秒
        )

        # 下载缓存
        self._download_cache: Dict[str, ImageInfo] = {}

        # 线程池用于requests备用下载
        self._thread_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="image_download")

        # 配置的域名列表（强制使用requests）
        self._force_requests_domains = self._load_domain_list()

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

                # 获取域名
                domain = parsed.hostname.lower() if parsed.hostname else ""

                # 检查是否应该使用requests
                if self._should_use_requests(domain):
                    logger.debug(f"域名 {domain} 配置使用requests下载: {url}")
                    result = await self._download_with_requests_async(url, save_dir)
                    return result

                # 否则使用aiohttp

                # 添加 User-Agent 和其他头部避免被阻止
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }

                # 使用aiohttp下载
                connector = aiohttp.TCPConnector()
                async with aiohttp.ClientSession(timeout=self.timeout, headers=headers, connector=connector) as session:
                    # 尝试 HEAD 请求检查文件信息
                    try:
                        async with session.head(url, allow_redirects=True) as head_response:
                            content_type = head_response.headers.get('Content-Type', '').lower()
                            content_length = head_response.headers.get('Content-Length')

                            # 如果 HEAD 请求返回非图片类型或403，尝试 GET 请求验证
                            if (not content_type.startswith('image/') or
                                head_response.status == 403 or
                                head_response.status == 404):

                                logger.debug(f"HEAD 请求失败或返回非图片类型，尝试 GET 请求验证: {url}")
                                raise Exception("HEAD请求验证失败")
                            else:
                                # HEAD请求成功，检查文件大小
                                if content_length and int(content_length) > self.max_size_bytes:
                                    size_mb = int(content_length) / 1024 / 1024
                                    logger.warning(f"⚠ 图片超过大小限制 ({size_mb:.1f}MB > {self.max_size_mb}MB): {url}")
                                    return ImageInfo(url, "", "", False, f"文件过大: {size_mb:.1f}MB")

                    except Exception as head_error:
                        logger.debug(f"HEAD 请求失败，直接使用 GET 请求: {head_error}")

                    # 使用 GET 请求下载图片
                    logger.debug(f"使用 GET 请求下载图片: {url}")
                    async with session.get(url, allow_redirects=True) as response:
                        response.raise_for_status()

                        # 验证响应的 Content-Type
                        content_type = response.headers.get('Content-Type', '').lower()
                        if content_type and not content_type.startswith('image/'):
                            logger.warning(f"⚠ URL 不是图片类型 ({content_type}): {url}")
                            return ImageInfo(url, "", "", False, f"非图片类型: {content_type}")

                        # 检查文件大小
                        content_length = response.headers.get('Content-Length')
                        if content_length and int(content_length) > self.max_size_bytes:
                            size_mb = int(content_length) / 1024 / 1024
                            logger.warning(f"⚠ 图片超过大小限制 ({size_mb:.1f}MB > {self.max_size_mb}MB): {url}")
                            return ImageInfo(url, "", "", False, f"文件过大: {size_mb:.1f}MB")

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
                aiohttp_error_msg = f"aiohttp下载失败: {type(e).__name__}: {e}"
                logger.warning(f"⚠ {aiohttp_error_msg}: {url}")

                # 对于配置的域名，尝试requests备用
                logger.debug(f"尝试requests备用下载: {url}")
                try:
                    result = await self._download_with_requests_async(url, save_dir)
                    return result

                except Exception as requests_e:
                    logger.warning(f"⚠ requests备用下载也失败: {url} - {type(requests_e).__name__}: {requests_e}")
                    # 返回组合错误信息
                    combined_error = f"{aiohttp_error_msg}; requests备用也失败: {type(requests_e).__name__}: {requests_e}"
                    return ImageInfo(url, "", "", False, combined_error)

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

    async def _download_with_requests_async(self, url: str, save_dir: Path) -> ImageInfo:
        """
        异步包装requests下载方法

        Args:
            url: 图片 URL
            save_dir: 保存目录

        Returns:
            ImageInfo 对象
        """
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                self._thread_pool,
                self._download_with_requests,
                url,
                save_dir
            )

            # 缓存结果
            if result.success:
                self._download_cache[url] = result

            return result

        except Exception as e:
            error_msg = f"requests异步下载失败: {type(e).__name__}: {e}"
            logger.warning(f"⚠ {error_msg}: {url}")
            return ImageInfo(url, "", "", False, error_msg)

    def _load_domain_list(self) -> List[str]:
        """
        加载需要强制使用requests的域名列表

        Returns:
            List[str]: 域名列表
        """
        domains = []

        # 从环境变量加载
        env_domains = os.getenv('FORCE_REQUESTS_DOMAINS', '').split(',')
        domains.extend([d.strip() for d in env_domains if d.strip()])

        # 默认包含的问题域名
        default_domains = ['bbci.co.uk', 'bbc.com']
        for domain in default_domains:
            if domain not in domains:
                domains.append(domain)
                logger.debug(f"默认添加问题域名: {domain}")

        logger.info(f"配置使用requests的域名: {domains}")
        return domains

    def _should_use_requests(self, domain: str) -> bool:
        """
        检查域名是否应该使用requests

        Args:
            domain: 域名

        Returns:
            bool: 是否使用requests
        """
        domain = domain.lower()

        # 检查是否在强制列表中
        for configured_domain in self._force_requests_domains:
            if domain == configured_domain or domain.endswith('.' + configured_domain):
                logger.debug(f"域名 {domain} 匹配配置，使用requests: {configured_domain}")
                return True

        return False

    def _download_with_requests(self, url: str, save_dir: Path) -> ImageInfo:
        """
        使用requests库下载图片（用于BBC等aiohttp有问题的域名）

        Args:
            url: 图片 URL
            save_dir: 保存目录

        Returns:
            ImageInfo 对象
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            # 使用requests下载
            response = requests.get(url, headers=headers, timeout=15, stream=True)
            response.raise_for_status()

            # 检查Content-Type
            content_type = response.headers.get('Content-Type', '').lower()
            if not content_type.startswith('image/'):
                error_msg = f"requests下载检测到非图片类型: {content_type}"
                logger.warning(f"⚠ {error_msg}: {url}")
                return ImageInfo(url, "", "", False, error_msg)

            # 检查文件大小
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > self.max_size_bytes:
                size_mb = int(content_length) / 1024 / 1024
                error_msg = f"图片超过大小限制 ({size_mb:.1f}MB > {self.max_size_mb}MB)"
                logger.warning(f"⚠ {error_msg}: {url}")
                return ImageInfo(url, "", "", False, error_msg)

            # 下载内容
            content = response.content
            if len(content) > self.max_size_bytes:
                size_mb = len(content) / 1024 / 1024
                error_msg = f"图片超过大小限制 ({size_mb:.1f}MB > {self.max_size_mb}MB)"
                logger.warning(f"⚠ {error_msg}: {url}")
                return ImageInfo(url, "", "", False, error_msg)

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

            # 写入文件
            with open(file_path, 'wb') as f:
                f.write(content)

            logger.info(f"✓ 图片已下载 (requests): {filename}")

            # 相对路径
            local_path = f"images/{filename}"

            # 创建结果对象
            result = ImageInfo(url, local_path, filename, True)

            return result

        except Exception as e:
            error_msg = f"requests下载失败: {type(e).__name__}: {e}"
            logger.warning(f"⚠ {error_msg}: {url}")
            return ImageInfo(url, "", "", False, error_msg)

    def extract_markdown_images(self, content: str) -> List[str]:
        """
        从 Markdown 内容中提取图片 URL（用于智能过滤）

        Args:
            content: Markdown 文本内容

        Returns:
            图片 URL 列表（原始 URL，用于去重和验证）
        """
        image_urls = []
        matches = self.IMAGE_PATTERN.findall(content)

        for _, url in matches:
            url = url.strip()
            if not url or url.startswith('data:'):
                continue

            # 处理相对路径（需要 base_url）
            if self.base_url and not url.startswith(('http://', 'https://')):
                url = urljoin(self.base_url, url)

            # 只保留 http/https URL
            if url.startswith(('http://', 'https://')):
                image_urls.append(url)

        return list(set(image_urls))  # 去重

    async def download_valid_images(self, content: str, image_urls: List[str], save_dir: Path) -> str:
        """
        异步下载指定的有效图片，并替换 Markdown 中的 URL

        Args:
            content: Markdown 内容
            image_urls: 需要下载的图片 URL 列表（已去重）
            save_dir: 图片保存目录（绝对路径）

        Returns:
            处理后的 Markdown 内容
        """
        if not image_urls:
            logger.debug("没有需要下载的图片")
            return content

        logger.info(f"开始异步下载 {len(image_urls)} 张有效图片...")

        # 异步下载指定的图片
        tasks = [self.download_image(url, save_dir) for url in image_urls]
        download_results = await asyncio.gather(*tasks)

        # 替换 Markdown 中的图片 URL
        processed_content = content
        success_count = 0

        for original_url, image_info in zip(image_urls, download_results):
            if image_info.success:
                # 在内容中查找并替换所有匹配的 URL
                for alt_text, markdown_url, resolved_url in self.extract_image_urls(processed_content):
                    if resolved_url == original_url:
                        # 使用原始 Markdown 中的 URL 进行替换
                        old_pattern = f"![{alt_text}]({markdown_url})"
                        new_pattern = f"![{alt_text}]({image_info.local_path})"
                        processed_content = processed_content.replace(old_pattern, new_pattern)
                        success_count += 1
                        break  # 避免重复替换同一个 URL

        # 统计
        logger.info(f"✓ 有效图片异步下载完成: {success_count}/{len(image_urls)} 成功")

        return processed_content

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
