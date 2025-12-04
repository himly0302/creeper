"""
网页内容爬取模块
支持静态爬取(Trafilatura)和动态渲染(Playwright)自动降级
"""

import time
import random
from typing import Optional, Dict
from dataclasses import dataclass

import requests
import trafilatura
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from .config import config
from .utils import setup_logger, extract_domain, get_timestamp
from .cookie_manager import CookieManager

logger = setup_logger(__name__)


@dataclass
class WebPage:
    """网页数据类"""
    url: str
    title: str
    description: str
    content: str
    author: str = ""
    published_date: str = ""
    crawled_at: str = ""
    method: str = "static"  # static 或 dynamic
    success: bool = True
    error: Optional[str] = None
    translated: bool = False  # 是否已翻译
    original_language: str = "unknown"  # 原始语言

    def __post_init__(self):
        if not self.crawled_at:
            self.crawled_at = get_timestamp()


class WebFetcher:
    """网页爬取器"""

    def __init__(self, use_playwright: bool = True, cookie_manager: Optional[CookieManager] = None):
        """
        初始化爬取器

        Args:
            use_playwright: 是否启用 Playwright 动态渲染
            cookie_manager: Cookie 管理器(可选)
        """
        self.use_playwright = use_playwright
        self.cookie_manager = cookie_manager
        self.session = requests.Session()
        self._setup_session()

        if cookie_manager:
            logger.info(f"网页爬取器已初始化 (Playwright: {use_playwright}, Cookie: 已启用)")
        else:
            logger.info(f"网页爬取器已初始化 (Playwright: {use_playwright})")

    def _setup_session(self):
        """配置 requests session"""
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def _get_random_user_agent(self) -> str:
        """获取随机 User-Agent"""
        return random.choice(config.USER_AGENTS).strip()

    def _random_delay(self):
        """随机延迟(反爬虫策略)"""
        delay = random.uniform(config.MIN_DELAY, config.MAX_DELAY)
        logger.debug(f"延迟 {delay:.2f} 秒...")
        time.sleep(delay)

    def fetch(self, url: str, retry_count: int = 0) -> WebPage:
        """
        爬取网页(自动降级策略)

        Args:
            url: 目标 URL
            retry_count: 当前重试次数

        Returns:
            WebPage 对象
        """
        logger.info(f"开始爬取: {url}")

        # 随机延迟
        if retry_count == 0:
            self._random_delay()

        # 尝试静态爬取
        try:
            page = self._fetch_static(url)
            if page.success and len(page.content) >= config.MIN_TEXT_LENGTH:
                logger.info(f"✓ 静态爬取成功: {url}")
                return page
            else:
                logger.warning(f"静态爬取内容不足(<{config.MIN_TEXT_LENGTH}字符),尝试动态渲染...")
        except Exception as e:
            logger.warning(f"静态爬取失败: {e},尝试动态渲染...")

        # 降级到动态渲染
        if self.use_playwright:
            try:
                page = self._fetch_dynamic(url)
                if page.success and len(page.content) >= config.MIN_TEXT_LENGTH:
                    # 额外检查内容质量
                    if self._is_valid_content(page.content):
                        logger.info(f"✓ 动态渲染成功: {url}")
                        return page
                    else:
                        logger.warning(f"动态渲染内容质量不佳，跳过保存: {url}")
                        page.success = False
                        return page
                elif page.success:
                    logger.warning(f"动态渲染内容不足(<{config.MIN_TEXT_LENGTH}字符),跳过保存: {url}")
                    page.success = False
                    return page
            except Exception as e:
                logger.error(f"动态渲染失败: {e}")

        # 两种方式都失败,返回失败状态
        return WebPage(
            url=url,
            title="",
            description="",
            content="",
            success=False,
            error="所有爬取方式均失败"
        )

    def _fetch_static(self, url: str) -> WebPage:
        """
        静态爬取(使用 Trafilatura)

        Args:
            url: 目标 URL

        Returns:
            WebPage 对象
        """
        # 设置随机 User-Agent
        headers = {'User-Agent': self._get_random_user_agent()}

        # 准备 cookies(如果有)
        cookies = None
        if self.cookie_manager:
            cookies_list = self.cookie_manager.get_cookies_for_url(url)
            if cookies_list:
                cookies = {cookie['name']: cookie['value'] for cookie in cookies_list}
                logger.debug(f"使用 {len(cookies)} 个 Cookie")

        # 下载网页
        response = self.session.get(
            url,
            headers=headers,
            cookies=cookies,
            timeout=config.REQUEST_TIMEOUT,
            allow_redirects=True
        )
        response.raise_for_status()

        # 保存响应的 cookies(如果有 cookie_manager)
        if self.cookie_manager and response.cookies:
            domain = extract_domain(url)
            self.cookie_manager.add_cookies_from_requests(domain, response.cookies)
            logger.debug(f"保存了来自 {domain} 的 Cookie")

        html = response.text

        # 使用 Trafilatura 提取内容
        content = trafilatura.extract(
            html,
            include_comments=config.INCLUDE_COMMENTS,
            include_tables=config.INCLUDE_TABLES,
            include_images=config.INCLUDE_IMAGES,
            output_format='markdown',  # 输出 Markdown 格式
            url=url
        )

        if not content:
            raise ValueError("Trafilatura 提取内容为空")

        # 提取元数据
        metadata = trafilatura.extract_metadata(html)
        title = metadata.title if metadata and metadata.title else self._extract_title_bs4(html)
        description = metadata.description if metadata and metadata.description else ""
        author = metadata.author if metadata and metadata.author else ""
        published_date = metadata.date if metadata and metadata.date else ""

        return WebPage(
            url=url,
            title=title or "无标题",
            description=description,
            content=content,
            author=author,
            published_date=published_date,
            method="static"
        )

    def _fetch_dynamic(self, url: str) -> WebPage:
        """
        动态渲染(使用 Playwright)

        Args:
            url: 目标 URL

        Returns:
            WebPage 对象
        """
        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(headless=config.BROWSER_HEADLESS)

            # 创建页面
            context = browser.new_context(
                user_agent=self._get_random_user_agent(),
                viewport={'width': 1920, 'height': 1080}
            )

            # 添加 cookies(如果有)
            if self.cookie_manager:
                cookies = self.cookie_manager.to_playwright_format()
                if cookies:
                    context.add_cookies(cookies)
                    logger.debug(f"已添加 {len(cookies)} 个 Cookie 到 Playwright")

            page = context.new_page()

            try:
                # 访问页面
                page.goto(url, timeout=config.PAGE_TIMEOUT, wait_until='networkidle')

                # 等待页面加载
                time.sleep(2)

                # 保存 cookies(如果有 cookie_manager)
                if self.cookie_manager:
                    self.cookie_manager.add_cookies_from_playwright(context)
                    logger.debug("已保存 Playwright 的 Cookie")

                # 获取 HTML
                html = page.content()

                # 使用 Trafilatura 提取内容
                content = trafilatura.extract(
                    html,
                    include_comments=config.INCLUDE_COMMENTS,
                    include_tables=config.INCLUDE_TABLES,
                    include_images=config.INCLUDE_IMAGES,
                    output_format='markdown',
                    url=url
                )

                if not content:
                    raise ValueError("Playwright 渲染后 Trafilatura 提取内容为空")

                # 提取元数据
                metadata = trafilatura.extract_metadata(html)
                title = metadata.title if metadata and metadata.title else page.title()
                description = metadata.description if metadata and metadata.description else ""
                author = metadata.author if metadata and metadata.author else ""
                published_date = metadata.date if metadata and metadata.date else ""

                return WebPage(
                    url=url,
                    title=title or "无标题",
                    description=description,
                    content=content,
                    author=author,
                    published_date=published_date,
                    method="dynamic"
                )

            finally:
                context.close()
                browser.close()

    def _extract_title_bs4(self, html: str) -> str:
        """
        使用 BeautifulSoup 提取标题(备用方案)

        Args:
            html: HTML 内容

        Returns:
            标题字符串
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            title = soup.find('title')
            return title.get_text().strip() if title else ""
        except Exception:
            return ""

    def _is_valid_content(self, content: str) -> bool:
        """
        检查内容是否有效，过滤掉错误页面和低质量内容

        Args:
            content: 网页内容

        Returns:
            True 表示内容有效，False 表示内容无效
        """
        content_lower = content.lower()

        # 检查常见的错误页面指示词（中英文）
        error_indicators = [
            # 中文错误指示词
            "页面不存在",
            "内容不存在",
            "找不到页面",
            "页面未找到",
            "您搜索的内容不存在",
            "已不存在",
            "访问被拒绝",
            "禁止访问",
            "请验证您是机器人",
            "请点击下方方框",
            "证明您不是机器人",
            "请确保您的浏览器支持",
            "javascript",
            "cookie 功能",
            "订阅",
            "立即订阅",
            "登录",
            "注册",
            "请登录",
            "需要登录",
            # 英文错误指示词
            "page not found",
            "content not found",
            "not found",
            "404",
            "access denied",
            "forbidden",
            "robot check",
            "verify you are human",
            "prove you are not a robot",
            "enable javascript",
            "enable cookies",
            "subscribe",
            "subscription",
            "login",
            "sign in",
            "please login",
            "authentication required",
            "privacy policy",
            "terms of service",
            "cookie policy"
        ]

        # 如果包含错误指示词，认为内容无效
        for indicator in error_indicators:
            if indicator in content_lower:
                return False

        # 检查内容是否太短或主要是重复文字
        if len(content.strip()) < 200:
            return False

        # 检查是否包含足够的中文字符或英文内容
        chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
        english_chars = len([c for c in content if 'a' <= c <= 'z' or 'A' <= c <= 'Z'])

        # 如果中文字符少于50个且英文字符少于100个，可能内容质量不高
        if chinese_chars < 50 and english_chars < 100:
            return False

        return True

    def close(self):
        """关闭会话"""
        self.session.close()
        logger.info("网页爬取器已关闭")
