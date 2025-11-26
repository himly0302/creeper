"""
交互式登录模块
使用 Playwright 打开浏览器,让用户手动登录,自动提取 Cookie
"""

import asyncio
from typing import Dict, List
from urllib.parse import urlparse

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from src.utils import setup_logger

logger = setup_logger("creeper.login")


async def interactive_login(url: str, timeout: int = 300) -> Dict[str, List[dict]]:
    """
    打开浏览器让用户手动登录,提取 Cookie

    Args:
        url: 登录页面 URL
        timeout: 等待超时时间(秒),默认 5 分钟

    Returns:
        Dict[domain, cookies]: 按域名分组的 Cookie

    流程:
    1. 使用 Playwright 启动浏览器(headless=False)
    2. 创建新页面并导航到 url
    3. 等待用户操作:
       - 监听页面关闭事件
       - 超时后自动关闭
    4. 提取 context.cookies()
    5. 按域名分组返回
    """
    logger.info(f"启动交互式登录: {url}")
    logger.info("=" * 60)
    logger.info("📋 操作步骤:")
    logger.info("  1. 浏览器窗口将自动打开")
    logger.info("  2. 请在浏览器中完成登录操作")
    logger.info("  3. 登录成功后,关闭浏览器窗口即可")
    logger.info(f"  4. 超时时间: {timeout} 秒")
    logger.info("=" * 60)

    domain_cookies = {}

    try:
        async with async_playwright() as p:
            # 启动浏览器(非 headless 模式)
            logger.info("正在启动浏览器...")
            browser = await p.chromium.launch(
                headless=False,
                args=['--start-maximized']  # 最大化窗口
            )

            # 创建上下文和页面
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()

            logger.info(f"正在加载登录页面: {url}")
            await page.goto(url, wait_until='domcontentloaded')

            logger.info("✅ 浏览器已打开,请在浏览器中完成登录")
            logger.info("💡 提示: 登录完成后,直接关闭浏览器窗口即可")

            # 等待页面关闭或超时
            try:
                # 监听页面关闭事件
                page_closed = asyncio.Event()

                async def on_close():
                    page_closed.set()

                page.on('close', lambda: asyncio.create_task(on_close()))

                # 等待页面关闭或超时
                try:
                    await asyncio.wait_for(page_closed.wait(), timeout=timeout)
                    logger.info("检测到浏览器窗口关闭")
                except asyncio.TimeoutError:
                    logger.warning(f"等待超时({timeout}秒),自动关闭浏览器")

            except Exception as e:
                logger.error(f"等待用户操作时出错: {e}")

            # 提取 Cookie
            logger.info("正在提取 Cookie...")
            cookies = await context.cookies()

            if not cookies:
                logger.warning("未找到任何 Cookie")
                await browser.close()
                return {}

            # 按域名分组
            for cookie in cookies:
                domain = cookie.get('domain', '')
                if domain:
                    # 去掉域名开头的点
                    domain = domain.lstrip('.')
                    if domain not in domain_cookies:
                        domain_cookies[domain] = []
                    domain_cookies[domain].append(cookie)

            logger.info(f"✅ 成功提取 Cookie,共 {len(domain_cookies)} 个域:")
            for domain, cookies in domain_cookies.items():
                logger.info(f"   - {domain}: {len(cookies)} 个 Cookie")

            # 关闭浏览器
            await browser.close()
            logger.info("浏览器已关闭")

    except PlaywrightTimeout as e:
        logger.error(f"Playwright 超时: {e}")
        raise
    except Exception as e:
        logger.error(f"交互式登录失败: {e}", exc_info=True)
        raise

    return domain_cookies


async def interactive_login_sync(url: str, timeout: int = 300) -> Dict[str, List[dict]]:
    """
    同步版本的交互式登录(适用于同步上下文)

    Args:
        url: 登录页面 URL
        timeout: 等待超时时间(秒),默认 5 分钟

    Returns:
        Dict[domain, cookies]: 按域名分组的 Cookie
    """
    return await interactive_login(url, timeout)
