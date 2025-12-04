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

            logger.info(f"Cookie 已保存到 Redis: {domain or 'all'} ({len(cookies)} 个)")
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