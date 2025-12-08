"""
异步网页爬取模块 (V1.0)
支持并发处理,提升爬取效率
"""

import asyncio
import time
import random
from typing import Optional, List
from dataclasses import dataclass

import aiohttp
import trafilatura
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from .config import config
from .utils import setup_logger, extract_domain, get_timestamp, current_url
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


class AsyncWebFetcher:
    """异步网页爬取器"""

    def __init__(self, use_playwright: bool = True, concurrency: int = None, cookie_manager: Optional[CookieManager] = None):
        """
        初始化异步爬取器

        Args:
            use_playwright: 是否启用 Playwright 动态渲染
            concurrency: 并发数,默认使用配置中的值
            cookie_manager: Cookie 管理器(可选)
        """
        self.use_playwright = use_playwright
        self.concurrency = concurrency or config.CONCURRENCY
        self.cookie_manager = cookie_manager
        self.semaphore = asyncio.Semaphore(self.concurrency)

        # 初始化翻译器
        self.translator = None
        if config.ENABLE_TRANSLATION and config.DEEPSEEK_API_KEY:
            from .translator import Translator

            self.translator = Translator(
                api_key=config.DEEPSEEK_API_KEY,
                base_url=config.DEEPSEEK_BASE_URL,
                model=config.DEEPSEEK_MODEL
            )
            logger.info("翻译功能已启用 (DeepSeek)")


        if cookie_manager:
            logger.info(f"异步网页爬取器已初始化 (并发数: {self.concurrency}, Playwright: {use_playwright}, Cookie: 已启用)")
        else:
            logger.info(f"异步网页爬取器已初始化 (并发数: {self.concurrency}, Playwright: {use_playwright})")

    def _get_random_user_agent(self) -> str:
        """获取随机 User-Agent"""
        return random.choice(config.USER_AGENTS).strip()

    async def _random_delay(self):
        """随机延迟(反爬虫策略)"""
        delay = random.uniform(config.MIN_DELAY, config.MAX_DELAY)
        logger.debug(f"延迟 {delay:.2f} 秒...")
        await asyncio.sleep(delay)

    async def fetch(self, url: str, retry_count: int = 0) -> WebPage:
        """
        异步爬取网页(自动降级策略)

        Args:
            url: 目标 URL
            retry_count: 当前重试次数

        Returns:
            WebPage 对象
        """
        async with self.semaphore:  # 控制并发数
            # 设置当前URL到context (用于日志追踪)
            current_url.set(url)

            logger.info(f"开始爬取: {url}")

            # 随机延迟
            if retry_count == 0:
                await self._random_delay()

            # 尝试静态爬取
            try:
                page = await self._fetch_static(url)
                if page.success and len(page.content) >= config.MIN_TEXT_LENGTH:
                    # 检查内容质量，过滤错误页面（同时检查标题和内容）
                    if self._is_valid_content(page.content, page.title, url):
                        logger.info(f"✓ 静态爬取成功: {url}")
                        # 调用翻译
                        if self.translator:
                            try:
                                page = await self.translator.translate_webpage(page)
                            except Exception as e:
                                logger.error(f"翻译失败(保留原文): {e}")
                        return page
                    else:
                        logger.warning(f"静态爬取内容质量不佳，跳过保存: {url}")
                        page.success = False
                        page.error = "内容质量检查未通过，可能包含错误页面指示词或内容过短"
                        return page
                else:
                    logger.warning(f"静态爬取内容不足(<{config.MIN_TEXT_LENGTH}字符),尝试动态渲染...")
            except Exception as e:
                logger.warning(f"静态爬取失败: {e},尝试动态渲染...")

            # 降级到动态渲染
            if self.use_playwright:
                try:
                    page = await self._fetch_dynamic(url)
                    if page.success and len(page.content) >= config.MIN_TEXT_LENGTH:
                        # 额外检查内容质量（同时检查标题和内容）
                        if self._is_valid_content(page.content, page.title, url):
                            logger.info(f"✓ 动态渲染成功: {url}")
                            # 调用翻译
                            if self.translator:
                                try:
                                    page = await self.translator.translate_webpage(page)
                                except Exception as e:
                                    logger.error(f"翻译失败(保留原文): {e}")
                            return page
                        else:
                            logger.warning(f"动态渲染内容质量不佳，跳过保存: {url}")
                            page.success = False
                            page.error = "内容质量检查未通过，可能包含错误页面指示词或内容过短"
                            return page
                    elif page.success:
                        logger.warning(f"动态渲染内容不足(<{config.MIN_TEXT_LENGTH}字符),跳过保存: {url}")
                        page.success = False
                        page.error = f"动态渲染内容过短({len(page.content)}字符 < {config.MIN_TEXT_LENGTH}字符)"
                        return page
                except Exception as e:
                    logger.error(f"动态渲染失败: {e}")

            # 两种方式都失败,进行重试
            if retry_count < config.MAX_RETRIES:
                retry_delay = config.RETRY_BASE_DELAY * (2 ** retry_count)  # 指数退避
                logger.warning(f"爬取失败,{retry_delay}秒后重试 (第{retry_count+1}/{config.MAX_RETRIES}次)")
                await asyncio.sleep(retry_delay)
                return await self.fetch(url, retry_count + 1)

            # 所有重试都失败
            return WebPage(
                url=url,
                title="",
                description="",
                content="",
                success=False,
                error=f"所有爬取方式均失败(已重试{config.MAX_RETRIES}次)"
            )

    async def _fetch_static(self, url: str) -> WebPage:
        """
        异步静态爬取(使用 aiohttp + Trafilatura)

        Args:
            url: 目标 URL

        Returns:
            WebPage 对象
        """
        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

        # 准备 cookies(如果有)
        cookies = None
        if self.cookie_manager:
            cookies_list = self.cookie_manager.get_cookies_for_url(url)
            if cookies_list:
                cookies = {cookie['name']: cookie['value'] for cookie in cookies_list}
                logger.debug(f"使用 {len(cookies)} 个 Cookie")

        timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)

        async with aiohttp.ClientSession(timeout=timeout, cookies=cookies) as session:
            async with session.get(url, headers=headers, allow_redirects=True) as response:
                # 检查状态码，但对特殊网站使用配置的宽容规则
                if response.status >= 400:
                    permitted_codes = config.get_permitted_status_codes(url)
                    if response.status in permitted_codes:
                        logger.warning(f"网站 {url} 返回 {response.status}，但该状态码在宽容列表中，继续处理")
                    else:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"HTTP {response.status}"
                        )
                html = await response.text()

                # 保存响应的 cookies(如果有 cookie_manager)
                if self.cookie_manager and response.cookies:
                    domain = extract_domain(url)
                    # 将 aiohttp cookies 转换为标准格式
                    cookies_to_save = []
                    for key, cookie in response.cookies.items():
                        cookies_to_save.append({
                            'name': key,
                            'value': cookie.value,
                            'domain': domain,
                            'path': '/',
                        })
                    if cookies_to_save:
                        self.cookie_manager.set_cookies(domain, cookies_to_save)
                        logger.debug(f"保存了来自 {domain} 的 Cookie")

        # 使用 Trafilatura 提取内容(CPU密集型,在线程池中运行)
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(
            None,
            lambda: trafilatura.extract(
                html,
                include_comments=config.INCLUDE_COMMENTS,
                include_tables=config.INCLUDE_TABLES,
                include_images=config.INCLUDE_IMAGES,
                output_format='markdown',
                url=url
            )
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

    async def _fetch_dynamic(self, url: str) -> WebPage:
        """
        异步动态渲染(使用 Playwright)

        Args:
            url: 目标 URL

        Returns:
            WebPage 对象
        """
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(headless=config.BROWSER_HEADLESS)

            # 创建页面
            context = await browser.new_context(
                user_agent=self._get_random_user_agent(),
                viewport={'width': 1920, 'height': 1080}
            )

            # 添加 cookies(如果有)
            if self.cookie_manager:
                cookies = self.cookie_manager.to_playwright_format()
                if cookies:
                    await context.add_cookies(cookies)
                    logger.debug(f"已添加 {len(cookies)} 个 Cookie 到 Playwright")

            page = await context.new_page()

            try:
                # 访问页面
                await page.goto(url, timeout=config.PAGE_TIMEOUT, wait_until='networkidle')

                # 等待页面加载
                await asyncio.sleep(2)

                # 保存 cookies(如果有 cookie_manager)
                if self.cookie_manager:
                    cookies = await context.cookies()
                    # 按域分组
                    domain_cookies = {}
                    for cookie in cookies:
                        domain = cookie.get('domain', '')
                        if domain not in domain_cookies:
                            domain_cookies[domain] = []
                        domain_cookies[domain].append(cookie)

                    # 存储到 cookie manager
                    for domain, cookies in domain_cookies.items():
                        self.cookie_manager.set_cookies(domain, cookies)
                    logger.debug("已保存 Playwright 的 Cookie")

                # 获取 HTML
                html = await page.content()

                # 使用 Trafilatura 提取内容
                loop = asyncio.get_event_loop()
                content = await loop.run_in_executor(
                    None,
                    lambda: trafilatura.extract(
                        html,
                        include_comments=config.INCLUDE_COMMENTS,
                        include_tables=config.INCLUDE_TABLES,
                        include_images=config.INCLUDE_IMAGES,
                        output_format='markdown',
                        url=url
                    )
                )

                if not content:
                    raise ValueError("Playwright 渲染后 Trafilatura 提取内容为空")

                # 提取元数据
                metadata = trafilatura.extract_metadata(html)
                page_title = await page.title()
                title = metadata.title if metadata and metadata.title else page_title
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
                await context.close()
                await browser.close()

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

    def _is_valid_content(self, content: str, title: str = "", url: str = "") -> bool:
        """
        检查内容是否有效，过滤掉错误页面和低质量内容

        Args:
            content: 网页内容
            title: 网页标题（可选）
            url: 网页URL（可选，用于特殊网站处理）

        Returns:
            True 表示内容有效，False 表示内容无效
        """
        content_lower = content.lower()
        title_lower = title.lower() if title else ""

        # 获取该URL的内容验证规则
        validation_rules = config.get_content_validation_rules(url)

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
            "请确保您的浏览器支持javascript",
            "cookie 功能",
            # 英文错误指示词
            "page not found",
            "content not found",
            "not found",
            "does not exist, or no longer exists",
            "no longer exists",
            "the content you are searching",
            "404",
            "access denied",
            "robot check",
            "verify you are human",
            "prove you are not a robot",
            "please enable javascript",
            "enable cookies"
        ]

        # 如果包含错误指示词，认为内容无效
        # 对于配置的网站，跳过指定的错误指示词
        for indicator in error_indicators:
            if indicator in content_lower:
                # 检查是否在跳过列表中
                if indicator in validation_rules['skip_indicators']:
                    continue
                logger.debug(f"内容包含错误指示词: '{indicator}'")
                return False
            if indicator in title_lower:
                # 检查是否在跳过列表中
                if indicator in validation_rules['skip_indicators']:
                    continue
                logger.debug(f"标题包含错误指示词: '{indicator}'")
                return False

        # 检查内容是否太短
        content_length = len(content.strip())
        min_length = validation_rules['min_length']

        if content_length < min_length:
            logger.debug(f"内容过短: {content_length} 字符 < {min_length} 字符")
            return False

        # 检查是否包含足够的中文字符或英文内容
        chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
        english_chars = len([c for c in content if 'a' <= c <= 'z' or 'A' <= c <= 'Z'])

        # 使用配置的字符数要求
        min_chinese = validation_rules['min_chinese']
        min_english = validation_rules['min_english']

        if chinese_chars < min_chinese and english_chars < min_english:
            logger.debug(f"字符数不足: 中文 {chinese_chars} 字符 < {min_chinese}, 英文 {english_chars} 字符 < {min_english}")
            return False

        return True

    async def fetch_batch(self, urls: List[str]) -> List[WebPage]:
        """
        批量异步爬取

        Args:
            urls: URL 列表

        Returns:
            WebPage 对象列表
        """
        tasks = [self.fetch(url) for url in urls]
        return await asyncio.gather(*tasks)
