"""
URL列表模式模块 (V1.0)
支持直接输入URL列表并输出JSON格式数据
"""

import json
import asyncio
import sys
from typing import List, Dict, Any
from urllib.parse import urlparse

from .async_fetcher import AsyncWebFetcher, WebPage
from .utils import setup_logger
from .config import config

logger = setup_logger(__name__)


class URLListMode:
    """URL列表模式处理器"""

    def __init__(self, concurrency: int = None, use_playwright: bool = True, with_images: bool = False):
        """
        初始化URL列表模式

        Args:
            concurrency: 并发数，默认使用配置中的值
            use_playwright: 是否启用Playwright动态渲染
            with_images: 是否提取页面中的图片链接
        """
        self.concurrency = concurrency or config.CONCURRENCY
        self.use_playwright = use_playwright
        self.with_images = with_images
        self.fetcher = AsyncWebFetcher(
            use_playwright=use_playwright,
            concurrency=self.concurrency
        )
        mode_desc = " (含图片提取)" if with_images else ""
        logger.info(f"URL列表模式已初始化 (并发数: {self.concurrency}{mode_desc})")

    def validate_urls(self, urls: List[str]) -> List[str]:
        """
        验证并过滤有效的URL

        Args:
            urls: URL列表

        Returns:
            有效的URL列表
        """
        valid_urls = []
        for url in urls:
            url = url.strip()
            if not url:
                continue

            # 检查URL格式
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                logger.warning(f"无效的URL格式: {url}")
                continue

            # 只支持http和https
            if parsed.scheme not in ['http', 'https']:
                logger.warning(f"不支持的协议: {url}")
                continue

            valid_urls.append(url)

        return valid_urls

    def parse_url_string(self, url_string: str) -> List[str]:
        """
        解析URL字符串，支持逗号分隔

        Args:
            url_string: 逗号分隔的URL字符串

        Returns:
            URL列表
        """
        # 按逗号分割URL
        urls = [url.strip() for url in url_string.split(',')]

        # 验证URL
        valid_urls = self.validate_urls(urls)

        if not valid_urls:
            logger.error("没有找到有效的URL")
            sys.exit(1)

        logger.info(f"解析得到 {len(valid_urls)} 个有效URL")
        return valid_urls

    def webpage_to_dict(self, webpage: WebPage) -> Dict[str, Any]:
        """
        将WebPage对象转换为指定的JSON格式

        Args:
            webpage: WebPage对象

        Returns:
            符合输出格式的字典
        """
        result = {
            "title": webpage.title,
            "summary": webpage.description,
            "content": webpage.content,
            "url": webpage.url
        }

        # 如果启用图片提取，添加 images 字段
        if self.with_images and webpage.success:
            # 复用 ImageDownloader 的图片提取逻辑
            from .image_downloader import ImageDownloader
            downloader = ImageDownloader(base_url=webpage.url)
            image_urls = downloader.extract_image_urls(webpage.content)
            # 提取完整URL列表（去掉alt_text和原始URL）
            result["images"] = [img_url for _, _, img_url in image_urls]

        return result

    async def process_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        处理URL列表并返回JSON格式数据

        Args:
            urls: URL列表

        Returns:
            JSON格式的数据列表
        """
        logger.info(f"开始处理 {len(urls)} 个URL")

        # 批量爬取
        webpages = await self.fetcher.fetch_batch(urls)

        # 转换为输出格式
        results = []
        successful_count = 0
        failed_count = 0

        for webpage in webpages:
            if webpage.success:
                result = self.webpage_to_dict(webpage)
                results.append(result)
                successful_count += 1
                logger.info(f"✓ 成功处理: {webpage.url}")
            else:
                # 即使失败也输出基本信息
                result = {
                    "title": "获取失败",
                    "summary": "",
                    "content": f"获取失败: {webpage.error or '未知错误'}",
                    "url": webpage.url
                }
                results.append(result)
                failed_count += 1
                logger.error(f"✗ 处理失败: {webpage.url} - {webpage.error}")

        logger.info(f"处理完成: 成功 {successful_count} 个，失败 {failed_count} 个")
        return results

    async def run(self, url_string: str) -> None:
        """
        运行URL列表模式

        Args:
            url_string: 逗号分隔的URL字符串
        """
        try:
            # 解析URL
            urls = self.parse_url_string(url_string)

            # 处理URL
            results = await self.process_urls(urls)

            # 输出JSON格式
            self.output_json(results)

        except KeyboardInterrupt:
            logger.info("用户中断操作")
            sys.exit(1)
        except Exception as e:
            logger.error(f"处理过程中发生错误: {e}")
            sys.exit(1)

    def output_json(self, results: List[Dict[str, Any]]) -> None:
        """
        输出JSON格式结果到控制台

        Args:
            results: 结果列表
        """
        try:
            # 输出JSON到控制台
            json_output = json.dumps(results, ensure_ascii=False, indent=2)
            print(json_output)

            # 同时输出统计信息到stderr（不影响JSON输出）
            successful = sum(1 for r in results if not r["content"].startswith("获取失败"))
            failed = len(results) - successful
            print(f"\n处理统计: 成功 {successful} 个，失败 {failed} 个", file=sys.stderr)

        except Exception as e:
            logger.error(f"输出JSON时发生错误: {e}")
            sys.exit(1)


async def run_url_list_mode(url_string: str, concurrency: int = None, use_playwright: bool = True, with_images: bool = False):
    """
    运行URL列表模式的便捷函数

    Args:
        url_string: 逗号分隔的URL字符串
        concurrency: 并发数
        use_playwright: 是否启用Playwright
        with_images: 是否提取页面中的图片链接
    """
    mode = URLListMode(concurrency=concurrency, use_playwright=use_playwright, with_images=with_images)
    await mode.run(url_string)