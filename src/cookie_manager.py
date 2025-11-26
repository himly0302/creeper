"""
Cookie 管理模块
负责 Cookie 的存储、加载和管理
"""

import json
import pickle
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from src.utils import setup_logger

logger = setup_logger("creeper.cookie")


class CookieManager:
    """Cookie 管理器"""

    def __init__(self, cookies_file: Optional[str] = None, format: str = 'json'):
        """
        初始化 Cookie 管理器

        Args:
            cookies_file: Cookie 存储文件路径
            format: 存储格式 ('json' 或 'pickle')
        """
        self.cookies_file = Path(cookies_file) if cookies_file else None
        self.format = format
        self.cookies: Dict[str, List[dict]] = {}  # domain -> cookies

        # 如果指定了文件且文件存在,自动加载
        if self.cookies_file and self.cookies_file.exists():
            self.load()
            logger.info(f"已加载 Cookie 文件: {self.cookies_file}")

    def save(self, cookies_file: Optional[str] = None) -> bool:
        """
        保存 Cookies 到文件

        Args:
            cookies_file: Cookie 存储文件路径(可选,默认使用初始化时的路径)

        Returns:
            bool: 是否保存成功
        """
        file_path = Path(cookies_file) if cookies_file else self.cookies_file

        if not file_path:
            logger.warning("未指定 Cookie 文件路径,跳过保存")
            return False

        try:
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 添加元数据
            data = {
                'cookies': self.cookies,
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'format': self.format,
                    'version': '1.0'
                }
            }

            if self.format == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif self.format == 'pickle':
                with open(file_path, 'wb') as f:
                    pickle.dump(data, f)
            else:
                logger.error(f"不支持的存储格式: {self.format}")
                return False

            self.cookies_file = file_path
            logger.info(f"Cookie 已保存到: {file_path}")
            logger.debug(f"保存了 {len(self.cookies)} 个域的 Cookie")
            return True

        except Exception as e:
            logger.error(f"保存 Cookie 失败: {e}")
            return False

    def load(self, cookies_file: Optional[str] = None) -> bool:
        """
        从文件加载 Cookies

        Args:
            cookies_file: Cookie 存储文件路径(可选,默认使用初始化时的路径)

        Returns:
            bool: 是否加载成功
        """
        file_path = Path(cookies_file) if cookies_file else self.cookies_file

        if not file_path or not file_path.exists():
            logger.warning(f"Cookie 文件不存在: {file_path}")
            return False

        try:
            # 自动检测格式
            if self.format == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif self.format == 'pickle':
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
            else:
                logger.error(f"不支持的存储格式: {self.format}")
                return False

            # 提取 cookies
            if isinstance(data, dict) and 'cookies' in data:
                self.cookies = data['cookies']
                metadata = data.get('metadata', {})
                logger.debug(f"Cookie 文件元数据: {metadata}")
            else:
                # 兼容旧格式
                self.cookies = data

            self.cookies_file = file_path
            logger.info(f"Cookie 已加载: {len(self.cookies)} 个域")
            return True

        except Exception as e:
            logger.error(f"加载 Cookie 失败: {e}")
            return False

    def set_cookies(self, domain: str, cookies: List[dict]):
        """
        设置指定域的 Cookies

        Args:
            domain: 域名(如 'example.com')
            cookies: Cookie 列表(字典格式)
        """
        self.cookies[domain] = cookies
        logger.debug(f"已设置 {domain} 的 {len(cookies)} 个 Cookie")

    def get_cookies(self, domain: str) -> List[dict]:
        """
        获取指定域的 Cookies

        Args:
            domain: 域名

        Returns:
            List[dict]: Cookie 列表
        """
        return self.cookies.get(domain, [])

    def get_cookies_for_url(self, url: str) -> List[dict]:
        """
        根据 URL 获取匹配的 Cookies

        Args:
            url: 目标 URL

        Returns:
            List[dict]: 匹配的 Cookie 列表
        """
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.netloc

        # 尝试精确匹配
        if domain in self.cookies:
            return self.cookies[domain]

        # 尝试匹配父域
        parts = domain.split('.')
        for i in range(len(parts)):
            parent_domain = '.'.join(parts[i:])
            if parent_domain in self.cookies:
                logger.debug(f"使用父域 {parent_domain} 的 Cookie")
                return self.cookies[parent_domain]

        logger.debug(f"未找到 {domain} 的 Cookie")
        return []

    def add_cookies_from_requests(self, domain: str, requests_cookies):
        """
        从 requests.cookies.RequestsCookieJar 添加 Cookies

        Args:
            domain: 域名
            requests_cookies: requests.cookies.RequestsCookieJar 对象
        """
        cookies = []
        for cookie in requests_cookies:
            cookies.append({
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path,
                'expires': cookie.expires,
                'secure': cookie.secure,
                'httpOnly': getattr(cookie, 'httponly', False),
            })

        self.set_cookies(domain, cookies)
        logger.debug(f"从 requests 添加了 {len(cookies)} 个 Cookie")

    def add_cookies_from_playwright(self, context):
        """
        从 Playwright context 提取并添加 Cookies

        Args:
            context: Playwright BrowserContext 对象
        """
        cookies = context.cookies()

        # 按域分组
        domain_cookies = {}
        for cookie in cookies:
            domain = cookie.get('domain', '')
            if domain not in domain_cookies:
                domain_cookies[domain] = []
            domain_cookies[domain].append(cookie)

        # 存储到 cookie manager
        for domain, cookies in domain_cookies.items():
            self.set_cookies(domain, cookies)
            logger.debug(f"从 Playwright 添加了 {domain} 的 {len(cookies)} 个 Cookie")

    def to_requests_format(self, domain: str) -> dict:
        """
        转换为 requests 库的 Cookie 格式

        Args:
            domain: 域名

        Returns:
            dict: {cookie_name: cookie_value} 格式
        """
        cookies = self.get_cookies(domain)
        return {cookie['name']: cookie['value'] for cookie in cookies}

    def to_playwright_format(self, domain: Optional[str] = None) -> List[dict]:
        """
        转换为 Playwright 库的 Cookie 格式

        Args:
            domain: 域名(可选,如果不指定则返回所有 Cookie)

        Returns:
            List[dict]: Playwright Cookie 格式
        """
        if domain:
            return self.get_cookies(domain)
        else:
            # 返回所有 Cookie
            all_cookies = []
            for cookies in self.cookies.values():
                all_cookies.extend(cookies)
            return all_cookies

    def clear(self, domain: Optional[str] = None):
        """
        清除 Cookies

        Args:
            domain: 域名(可选,如果不指定则清除所有 Cookie)
        """
        if domain:
            if domain in self.cookies:
                del self.cookies[domain]
                logger.info(f"已清除 {domain} 的 Cookie")
        else:
            self.cookies.clear()
            logger.info("已清除所有 Cookie")

    def has_cookies(self, domain: Optional[str] = None) -> bool:
        """
        检查是否有 Cookies

        Args:
            domain: 域名(可选)

        Returns:
            bool: 是否有 Cookie
        """
        if domain:
            return domain in self.cookies and len(self.cookies[domain]) > 0
        else:
            return len(self.cookies) > 0

    def get_stats(self) -> dict:
        """
        获取 Cookie 统计信息

        Returns:
            dict: 统计信息
        """
        total_cookies = sum(len(cookies) for cookies in self.cookies.values())
        return {
            'total_domains': len(self.cookies),
            'total_cookies': total_cookies,
            'domains': list(self.cookies.keys()),
            'cookies_file': str(self.cookies_file) if self.cookies_file else None,
        }
