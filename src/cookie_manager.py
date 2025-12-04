"""
Cookie 管理模块
负责 Cookie 的存储、加载和管理
仅支持 Redis 存储
"""

import json
import pickle
from typing import Optional, Dict, List
from datetime import datetime
import redis

from src.utils import setup_logger
from src.config import config

logger = setup_logger("creeper.cookie")


class CookieManager:
    """Cookie 管理器"""

    def __init__(
        self,
        redis_client: redis.Redis,
        redis_key_prefix: str = 'creeper:cookie:',
        expire_days: int = 7
    ):
        """
        初始化 Cookie 管理器

        Args:
            redis_client: Redis 客户端实例
            redis_key_prefix: Redis Key 前缀
            expire_days: Cookie 过期天数
        """
        self.redis_client = redis_client
        self.redis_key_prefix = redis_key_prefix
        self.expire_days = expire_days
        self.cookies: Dict[str, List[dict]] = {}  # domain -> cookies

        logger.info(f"Redis Cookie 管理器已初始化，过期时间: {expire_days} 天")

    def save(self, cookies: List[dict], domain: str = None) -> bool:
        """
        保存 Cookie 到 Redis

        Args:
            cookies: Cookie 列表
            domain: 域名（可选）

        Returns:
            True 表示成功, False 表示失败
        """
        try:
            # 如果指定了域名，按域名存储
            if domain:
                self.cookies[domain] = cookies
                key = f"{self.redis_key_prefix}{domain}"
            else:
                # 否则存储所有 cookies
                self.cookies['all'] = cookies
                key = f"{self.redis_key_prefix}all"

            # 序列化 cookies
            data = {
                'cookies': cookies,
                'domain': domain,
                'created_at': datetime.now().isoformat(),
                'format': 'json'
            }

            # 保存到 Redis
            serialized_data = json.dumps(data, ensure_ascii=False)
            self.redis_client.setex(
                key,
                self.expire_days * 24 * 3600,  # 转换为秒
                serialized_data
            )

            # 根据配置决定日志级别
            if config.VERBOSE_COOKIE_LOGGING:
                logger.info(f"Cookie 已保存到 Redis: {domain or 'all'} ({len(cookies)} 个)")
            else:
                logger.debug(f"Cookie 已保存到 Redis: {domain or 'all'} ({len(cookies)} 个)")
            return True

        except Exception as e:
            logger.error(f"保存 Cookie 失败: {e}")
            return False

    def load(self, domain: str = None) -> List[dict]:
        """
        从 Redis 加载 Cookie

        Args:
            domain: 域名（可选）

        Returns:
            Cookie 列表
        """
        try:
            # 如果指定了域名，加载指定域名的 cookies
            if domain:
                key = f"{self.redis_key_prefix}{domain}"
            else:
                # 否则加载所有 cookies
                key = f"{self.redis_key_prefix}all"

            data = self.redis_client.get(key)
            if not data:
                logger.debug(f"Redis 中没有 Cookie 数据: {domain or 'all'}")
                return []

            # 反序列化
            cookie_data = json.loads(data)
            cookies = cookie_data.get('cookies', [])

            # 更新内存缓存
            if domain:
                self.cookies[domain] = cookies
            else:
                self.cookies['all'] = cookies

            logger.debug(f"从 Redis 加载 Cookie: {domain or 'all'} ({len(cookies)} 个)")
            return cookies

        except Exception as e:
            logger.error(f"加载 Cookie 失败: {e}")
            return []

    def add_cookie(self, cookie: dict, domain: str) -> bool:
        """
        添加单个 Cookie

        Args:
            cookie: Cookie 字典
            domain: 域名

        Returns:
            True 表示成功, False 表示失败
        """
        try:
            # 加载现有的 cookies
            existing_cookies = self.load(domain)

            # 检查是否已存在相同 name 的 cookie
            for i, existing_cookie in enumerate(existing_cookies):
                if existing_cookie.get('name') == cookie.get('name'):
                    # 更新现有 cookie
                    existing_cookies[i] = cookie
                    break
            else:
                # 添加新 cookie
                existing_cookies.append(cookie)

            # 保存更新后的 cookies
            return self.save(existing_cookies, domain)

        except Exception as e:
            logger.error(f"添加 Cookie 失败: {e}")
            return False

    def get_cookies(self, domain: str) -> List[dict]:
        """
        获取指定域名的 Cookie

        Args:
            domain: 域名

        Returns:
            Cookie 列表
        """
        return self.load(domain)

    def get_all_cookies(self) -> Dict[str, List[dict]]:
        """
        获取所有 Cookie

        Returns:
            域名到 Cookie 列表的映射
        """
        # 这里可以实现获取所有域名的 cookies
        # 当前简化实现，只返回内存中的缓存
        return self.cookies.copy()

    def clear_cookies(self, domain: str = None) -> bool:
        """
        清除 Cookie

        Args:
            domain: 域名（可选，如果不指定则清除所有）

        Returns:
            True 表示成功, False 表示失败
        """
        try:
            if domain:
                # 清除指定域名的 cookies
                key = f"{self.redis_key_prefix}{domain}"
                self.redis_client.delete(key)
                if domain in self.cookies:
                    del self.cookies[domain]
                logger.info(f"已清除域名 {domain} 的 Cookie")
            else:
                # 清除所有 cookies
                pattern = f"{self.redis_key_prefix}*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                self.cookies.clear()
                logger.info(f"已清除所有 Cookie ({len(keys)} 个)")

            return True

        except Exception as e:
            logger.error(f"清除 Cookie 失败: {e}")
            return False

    def get_stats(self) -> dict:
        """
        获取 Cookie 管理器统计信息

        Returns:
            统计信息字典
        """
        try:
            pattern = f"{self.redis_key_prefix}*"
            keys = self.redis_client.keys(pattern)

            total_cookies = 0
            for key in keys:
                data = self.redis_client.get(key)
                if data:
                    cookie_data = json.loads(data)
                    total_cookies += len(cookie_data.get('cookies', []))

            return {
                'total_domains': len(keys),
                'total_cookies': total_cookies,
                'expire_days': self.expire_days,
                'storage_backend': 'redis'
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'total_domains': 0,
                'total_cookies': 0,
                'error': str(e)
            }

    def export_cookies(self, format: str = 'json') -> str:
        """
        导出所有 Cookie 为字符串

        Args:
            format: 导出格式 ('json' 或 'netscape')

        Returns:
            Cookie 字符串
        """
        all_cookies = {}

        # 获取所有域名的 cookies
        try:
            pattern = f"{self.redis_key_prefix}*"
            keys = self.redis_client.keys(pattern)

            for key in keys:
                data = self.redis_client.get(key)
                if data:
                    cookie_data = json.loads(data)
                    domain = cookie_data.get('domain', 'unknown')
                    cookies = cookie_data.get('cookies', [])
                    all_cookies[domain] = cookies

        except Exception as e:
            logger.error(f"导出 Cookie 失败: {e}")
            return ""

        if format == 'json':
            return json.dumps(all_cookies, ensure_ascii=False, indent=2)
        elif format == 'netscape':
            # Netscape 格式
            lines = [
                "# Netscape HTTP Cookie File",
                "# This is a generated file! Do not edit.",
                ""
            ]

            for domain, cookies in all_cookies.items():
                for cookie in cookies:
                    line = f"{domain or ''}\t{'TRUE' if cookie.get('secure') else 'FALSE'}\t{cookie.get('path', '/')}\t{'FALSE' if cookie.get('httpOnly') else 'TRUE'}\t{cookie.get('expires', '')}\t{cookie.get('name', '')}\t{cookie.get('value', '')}"
                    lines.append(line)

            return '\n'.join(lines)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def get_cookies_for_url(self, url: str) -> List[dict]:
        """
        根据URL获取适用的 cookies

        Args:
            url: 目标 URL

        Returns:
            适用于该 URL 的 cookies 列表
        """
        try:
            # 解析 URL 获取域名
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            if not domain:
                return []

            # 移除端口号（如果存在）
            if ':' in domain:
                domain = domain.split(':')[0]

            cookies_list = []

            # 首先尝试获取完全匹配的域名
            exact_cookies = self.load(domain)
            cookies_list.extend(exact_cookies)

            # 尝试匹配通配符域名（例如，对于 example.com，也查找 .example.com）
            if not domain.startswith('.'):
                wildcard_domain = f".{domain}"
                wildcard_cookies = self.load(wildcard_domain)
                cookies_list.extend(wildcard_cookies)

            # 去重（相同 name 的 cookie，后面的覆盖前面的）
            seen_names = set()
            unique_cookies = []
            for cookie in cookies_list:
                name = cookie.get('name')
                if name and name not in seen_names:
                    seen_names.add(name)
                    unique_cookies.append(cookie)
                elif name:  # 重复的 cookie，覆盖
                    # 找到并替换已存在的 cookie
                    for i, existing_cookie in enumerate(unique_cookies):
                        if existing_cookie.get('name') == name:
                            unique_cookies[i] = cookie
                            break

            logger.debug(f"为 URL {url} 找到 {len(unique_cookies)} 个 cookies")
            return unique_cookies

        except Exception as e:
            logger.error(f"获取 URL cookies 失败: {e}")
            return []

    def to_playwright_format(self) -> List[dict]:
        """
        将所有 cookies 转换为 Playwright 格式

        Returns:
            Playwright 格式的 cookies 列表
        """
        try:
            all_cookies = []

            # 获取所有域名的 cookies
            pattern = f"{self.redis_key_prefix}*"
            keys = self.redis_client.keys(pattern)

            for key in keys:
                # 跳过 URL 相关的 key（格式为 creeper:cookie:domain）
                if ':url:' in key:
                    continue

                data = self.redis_client.get(key)
                if data:
                    cookie_data = json.loads(data)
                    cookies = cookie_data.get('cookies', [])

                    # 转换为 Playwright 格式
                    for cookie in cookies:
                        playwright_cookie = {
                            'name': cookie.get('name', ''),
                            'value': cookie.get('value', ''),
                            'domain': cookie.get('domain', cookie_data.get('domain', '')),
                            'path': cookie.get('path', '/'),
                            'httpOnly': cookie.get('httpOnly', False),
                            'secure': cookie.get('secure', False),
                            'sameSite': cookie.get('sameSite', 'Lax') if cookie.get('sameSite') else 'Lax'
                        }

                        # 添加 expires（如果存在）
                        if 'expires' in cookie:
                            playwright_cookie['expires'] = cookie['expires']

                        all_cookies.append(playwright_cookie)

            logger.debug(f"转换为 Playwright 格式: {len(all_cookies)} 个 cookies")
            return all_cookies

        except Exception as e:
            logger.error(f"转换为 Playwright 格式失败: {e}")
            return []

    def add_cookies_from_requests(self, domain: str, requests_cookies: dict) -> bool:
        """
        从 requests.Response.cookies 添加 cookies

        Args:
            domain: 域名
            requests_cookies: requests 库的 cookies 对象

        Returns:
            True 表示成功, False 表示失败
        """
        try:
            # 转换 requests cookies 为标准格式
            cookies_list = []
            for name, value in requests_cookies.items():
                cookie = {
                    'name': name,
                    'value': value,
                    'domain': domain,
                    'path': '/'
                }
                cookies_list.append(cookie)

            # 使用现有的 add_cookie 方法添加每个 cookie
            success = True
            for cookie in cookies_list:
                if not self.add_cookie(cookie, domain):
                    success = False

            if success:
                logger.debug(f"从 requests 添加了 {len(cookies_list)} 个 cookies 到 {domain}")

            return success

        except Exception as e:
            logger.error(f"从 requests 添加 cookies 失败: {e}")
            return False

    def add_cookies_from_playwright(self, context, target_domain: str = None, save_third_party: bool = True) -> bool:
        """
        从 Playwright 浏览器上下文添加 cookies

        Args:
            context: Playwright 浏览器上下文
            target_domain: 目标域名（可选，如果提供则只保存该域名相关的 Cookie）
            save_third_party: 是否保存第三方 Cookie（默认：True）

        Returns:
            True 表示成功, False 表示失败
        """
        try:
            # 获取 Playwright cookies
            playwright_cookies = context.cookies()
            if not playwright_cookies:
                return True

            # 按域名分组
            domain_cookies = {}
            for cookie in playwright_cookies:
                domain = cookie.get('domain', '')
                if not domain:
                    continue

                # 移除前导点（如果存在）
                if domain.startswith('.'):
                    domain = domain[1:]

                # 过滤逻辑
                if target_domain:
                    # 如果指定了目标域名，只保存目标域名相关的 Cookie
                    if not self._is_domain_related(domain, target_domain):
                        continue
                elif not save_third_party:
                    # 如果不保存第三方 Cookie，则跳过（需要上下文信息判断）
                    # 这里简化处理：只保存与目标域名匹配的 Cookie
                    if target_domain and not domain.endswith(target_domain):
                        continue

                if domain not in domain_cookies:
                    domain_cookies[domain] = []

                # 转换为标准格式
                standard_cookie = {
                    'name': cookie.get('name', ''),
                    'value': cookie.get('value', ''),
                    'domain': domain,
                    'path': cookie.get('path', '/'),
                    'httpOnly': cookie.get('httpOnly', False),
                    'secure': cookie.get('secure', False),
                    'sameSite': cookie.get('sameSite', 'Lax') if cookie.get('sameSite') else 'Lax'
                }

                # 添加 expires（如果存在）
                if 'expires' in cookie and cookie['expires']:
                    standard_cookie['expires'] = cookie['expires']

                domain_cookies[domain].append(standard_cookie)

            # 保存每个域名的 cookies
            success = True
            for domain, cookies in domain_cookies.items():
                if not self.save(cookies, domain):
                    success = False

            if success:
                total_cookies = sum(len(cookies) for cookies in domain_cookies.values())
                logger.debug(f"从 Playwright 添加了 {total_cookies} 个 cookies 到 {len(domain_cookies)} 个域")

            return success

        except Exception as e:
            logger.error(f"从 Playwright 添加 cookies 失败: {e}")
            return False

    def set_cookies(self, domain: str, cookies: List[dict]) -> bool:
        """
        设置指定域名的 cookies（覆盖现有 cookies）

        Args:
            domain: 域名
            cookies: cookies 列表

        Returns:
            True 表示成功, False 表示失败
        """
        try:
            # 使用 save 方法保存 cookies（会覆盖现有的）
            success = self.save(cookies, domain)
            if success:
                logger.debug(f"设置了 {len(cookies)} 个 cookies 到 {domain}")
            return success

        except Exception as e:
            logger.error(f"设置 cookies 失败: {e}")
            return False

    def _is_domain_related(self, cookie_domain: str, target_domain: str) -> bool:
        """
        判断 Cookie 域名是否与目标域名相关

        Args:
            cookie_domain: Cookie 的域名
            target_domain: 目标域名

        Returns:
            True 表示相关，False 表示不相关
        """
        # 直接匹配
        if cookie_domain == target_domain:
            return True

        # 子域名匹配
        if cookie_domain.endswith('.' + target_domain):
            return True

        # 父域名匹配（如 gov.cn 相关的 gov.cn 域名）
        if target_domain.endswith(cookie_domain):
            return True

        # 重要的公共服务域名
        public_domains = [
            'gov.cn', 'edu.cn', 'org.cn', 'com.cn',
            'wikimedia.org', 'wikipedia.org'
        ]

        for public_domain in public_domains:
            if (cookie_domain.endswith(public_domain) and
                target_domain.endswith(public_domain)):
                return True

        return False