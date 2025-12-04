"""
文件存储模块
生成目录结构并保存 Markdown 文件
"""

import asyncio
from pathlib import Path
from typing import Optional

from .fetcher import WebPage
from .parser import URLItem
from .cleaner import ContentCleaner
from .config import config
from .utils import setup_logger, sanitize_filename, ensure_dir, get_timestamp
from .image_downloader import ImageDownloader, AsyncImageDownloader

logger = setup_logger(__name__)


class StorageManager:
    """文件存储管理器"""

    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化存储管理器

        Args:
            output_dir: 输出目录,如果为 None 则使用配置中的值
        """
        self.output_dir = Path(output_dir or config.OUTPUT_DIR)
        ensure_dir(self.output_dir)
        logger.info(f"文件存储管理器已初始化: {self.output_dir}")

    def save(self, item: URLItem, page: WebPage) -> Optional[Path]:
        """
        保存网页为 Markdown 文件

        Args:
            item: URL 项目(包含 H1/H2 层级信息)
            page: 网页数据

        Returns:
            保存的文件路径,失败返回 None
        """
        try:
            # 构建目录路径: output_dir/H1/H2/
            h1_dir = self.output_dir / sanitize_filename(item.h1)
            h2_dir = h1_dir / sanitize_filename(item.h2)
            ensure_dir(h2_dir)

            # 构建文件名: 标题.md
            filename = sanitize_filename(page.title) + ".md"
            file_path = h2_dir / filename

            # 生成 Markdown 内容
            markdown_content = self._generate_markdown(item, page, h2_dir)

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            logger.info(f"✓ 文件已保存: {file_path.relative_to(self.output_dir)}")
            return file_path

        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            return None

    def _generate_markdown(self, item: URLItem, page: WebPage, h2_dir: Path) -> str:
        """
        生成 Markdown 文件内容

        Args:
            item: URL 项目
            page: 网页数据
            h2_dir: H2 级目录路径（用于保存图片）

        Returns:
            Markdown 格式的文件内容
        """
        # 清洗内容
        content = ContentCleaner.clean(page.content)
        description = ContentCleaner.truncate_description(page.description, 300)

        # 智能图片下载处理（如果启用）
        if config.DOWNLOAD_IMAGES:
            try:
                logger.debug("图片下载功能已启用，开始智能处理图片...")
                downloader = ImageDownloader(base_url=page.url)
                images_dir = h2_dir / "images"

                # 从清洗后的内容中提取图片 URL
                markdown_images = downloader.extract_markdown_images(content)

                if markdown_images:
                    logger.info(f"从清洗后的内容中发现 {len(markdown_images)} 张图片，开始下载...")
                    # 只下载在清洗后内容中存在的图片
                    content = downloader.download_valid_images(content, markdown_images, images_dir)
                else:
                    logger.debug("清洗后的内容中没有发现图片，跳过图片下载")

                downloader.close()
            except Exception as e:
                logger.warning(f"⚠ 智能图片下载处理失败，将使用原始内容: {e}")

    async def _generate_markdown_async(self, item: URLItem, page: WebPage, h2_dir: Path) -> str:
        """
        异步生成 Markdown 文件内容

        Args:
            item: URL 项目
            page: 网页数据
            h2_dir: H2 级目录路径（用于保存图片）

        Returns:
            Markdown 格式的文件内容
        """
        # 清洗内容
        content = ContentCleaner.clean(page.content)
        description = ContentCleaner.truncate_description(page.description, 300)

        # 智能异步图片下载处理（如果启用）
        if config.DOWNLOAD_IMAGES:
            try:
                logger.debug("图片下载功能已启用，开始异步智能处理图片...")
                downloader = AsyncImageDownloader(base_url=page.url)
                images_dir = h2_dir / "images"

                # 从清洗后的内容中提取图片 URL
                markdown_images = downloader.extract_markdown_images(content)

                if markdown_images:
                    logger.info(f"从清洗后的内容中发现 {len(markdown_images)} 张图片，开始异步下载...")
                    # 异步下载在清洗后内容中存在的图片
                    content = await downloader.download_valid_images(content, markdown_images, images_dir)
                else:
                    logger.debug("清洗后的内容中没有发现图片，跳过图片下载")

            except Exception as e:
                logger.warning(f"⚠ 智能异步图片下载处理失败，将使用原始内容: {e}")

        # 构建 Markdown
        lines = []

        # 标题
        lines.append(f"# {page.title}")
        lines.append("")

        # 元信息
        lines.append(f"> 📅 **爬取时间**: {page.crawled_at}")
        lines.append(f"> 🔗 **来源链接**: {page.url}")

        if description:
            lines.append(f"> 📝 **网页描述**: {description}")

        if page.author:
            lines.append(f"> ✍️ **作者**: {page.author}")

        if page.published_date:
            lines.append(f"> 📆 **发布时间**: {page.published_date}")

        lines.append(f"> 🎯 **爬取方式**: {'动态渲染' if page.method == 'dynamic' else '静态爬取'}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 主体内容
        lines.append(content)
        lines.append("")
        lines.append("---")
        lines.append("")

        # 页脚
        lines.append("*本文由 Creeper 自动爬取并清洗*")

        return '\n'.join(lines)

    async def save_async(self, item: URLItem, page: WebPage) -> Optional[Path]:
        """
        异步保存网页内容到 Markdown 文件

        Args:
            item: URL 项目
            page: 网页数据

        Returns:
            保存的文件路径
        """
        try:
            # 创建目录结构
            h1_dir = self.output_dir / sanitize_filename(item.h1)
            h2_dir = h1_dir / sanitize_filename(item.h2)

            ensure_dir(h2_dir)

            # 生成文件名
            filename = f"{sanitize_filename(item.h2)}.md"
            file_path = h2_dir / filename

            # 异步生成 Markdown 内容
            markdown_content = await self._generate_markdown_async(item, page, h2_dir)

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            # 更新统计
            self.stats['total_files'] += 1
            self.stats['total_size'] += file_path.stat().st_size

            logger.info(f"✓ 文件已保存: {file_path.relative_to(self.output_dir)}")
            return file_path

        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            return None

    def save_failed_urls(self, failed_items: list) -> Optional[Path]:
        """
        保存失败的 URL 列表

        Args:
            failed_items: 失败的 (URLItem, error_message) 列表

        Returns:
            保存的文件路径
        """
        if not config.SAVE_FAILED_URLS or not failed_items:
            return None

        try:
            filename = f"failed_urls_{get_timestamp().replace(':', '-').replace(' ', '_')}.txt"
            file_path = self.output_dir / filename

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# 爬取失败的 URL 列表\n")
                f.write(f"# 生成时间: {get_timestamp()}\n")
                f.write(f"# 总计: {len(failed_items)} 个\n\n")

                for item, error in failed_items:
                    f.write(f"URL: {item.url}\n")
                    f.write(f"层级: {item.h1} / {item.h2}\n")
                    f.write(f"错误: {error}\n")
                    f.write("-" * 80 + "\n\n")

            logger.info(f"✓ 失败 URL 列表已保存: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"保存失败 URL 列表失败: {e}")
            return None

    def get_stats(self) -> dict:
        """
        获取存储统计信息

        Returns:
            统计信息字典
        """
        if not self.output_dir.exists():
            return {'total_files': 0, 'total_dirs': 0}

        # 统计文件和目录数量
        md_files = list(self.output_dir.rglob('*.md'))
        dirs = [d for d in self.output_dir.rglob('*') if d.is_dir()]

        return {
            'total_files': len(md_files),
            'total_dirs': len(dirs),
            'output_dir': str(self.output_dir)
        }
