"""
Redis 去重模块
使用 Redis 存储已爬取的 URL,实现去重功能
"""

import hashlib
from datetime import datetime
from typing import Optional
import redis

from .config import config
from .utils import setup_logger

logger = setup_logger(__name__)


class DedupManager:
    """去重管理器"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        初始化去重管理器

        Args:
            redis_client: Redis 客户端实例,如果为 None 则自动创建
        """
        if redis_client is None:
            self.redis = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                password=config.REDIS_PASSWORD if config.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        else:
            self.redis = redis_client

        self.key_prefix = config.REDIS_KEY_PREFIX
        logger.info(f"Redis 去重管理器已初始化: {config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}")

    def _get_url_hash(self, url: str) -> str:
        """
        获取 URL 的 MD5 哈希值

        Args:
            url: 原始 URL

        Returns:
            MD5 哈希值
        """
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def is_crawled(self, url: str) -> bool:
        """
        检查 URL 是否已被爬取

        Args:
            url: 要检查的 URL

        Returns:
            True 表示已爬取, False 表示未爬取
        """
        url_hash = self._get_url_hash(url)
        redis_key = f"{self.key_prefix}url:{url_hash}"

        try:
            result = self.redis.exists(redis_key)
            return bool(result)
        except Exception as e:
            logger.error(f"检查去重失败: {e}")
            # Redis 出错时,认为未爬取,避免重复爬取
            return False

    def mark_crawled(self, url: str, expire_days: int = 30) -> bool:
        """
        标记 URL 为已爬取

        Args:
            url: 要标记的 URL
            expire_days: 过期天数

        Returns:
            True 表示成功, False 表示失败
        """
        url_hash = self._get_url_hash(url)
        redis_key = f"{self.key_prefix}url:{url_hash}"

        # 构建存储的数据
        data = {
            "url": url,
            "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "completed"
        }

        try:
            # 使用管道提高性能
            pipe = self.redis.pipeline()
            pipe.hset(redis_key, mapping=data)
            pipe.expire(redis_key, expire_days * 24 * 3600)  # 转换为秒
            pipe.execute()

            logger.debug(f"URL 已标记为已爬取: {url}")
            return True

        except Exception as e:
            logger.error(f"标记去重失败: {e}")
            return False

    def get_crawled_info(self, url: str) -> Optional[dict]:
        """
        获取 URL 的爬取信息

        Args:
            url: URL

        Returns:
            爬取信息字典,如果不存在则返回 None
        """
        url_hash = self._get_url_hash(url)
        redis_key = f"{self.key_prefix}url:{url_hash}"

        try:
            data = self.redis.hgetall(redis_key)
            if data:
                return {
                    "url": data.get("url", ""),
                    "crawled_at": data.get("crawled_at", ""),
                    "status": data.get("status", "")
                }
            return None

        except Exception as e:
            logger.error(f"获取去重信息失败: {e}")
            return None

    def get_stats(self) -> dict:
        """
        获取去重统计信息

        Returns:
            统计信息字典
        """
        try:
            pattern = f"{self.key_prefix}url:*"
            keys = self.redis.keys(pattern)

            return {
                "total_urls": len(keys),
                "redis_keys_pattern": pattern
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "total_urls": 0,
                "error": str(e)
            }

    def test_connection(self) -> bool:
        """
        测试 Redis 连接

        Returns:
            True 表示连接正常, False 表示连接失败
        """
        try:
            # 使用 ping 命令测试连接
            result = self.redis.ping()
            return bool(result)
        except Exception as e:
            logger.error(f"Redis 连接测试失败: {e}")
            return False

    def close(self):
        """
        关闭 Redis 连接
        """
        try:
            if hasattr(self.redis, 'close'):
                self.redis.close()
            elif hasattr(self.redis, 'connection_pool'):
                # 关闭连接池
                self.redis.connection_pool.disconnect()
            logger.debug("Redis 连接已关闭")
        except Exception as e:
            logger.error(f"关闭 Redis 连接失败: {e}")

    def clear_all(self) -> bool:
        """
        清空所有去重数据

        Returns:
            True 表示成功, False 表示失败
        """
        try:
            pattern = f"{self.key_prefix}url:*"
            keys = self.redis.keys(pattern)

            if keys:
                self.redis.delete(*keys)
                logger.info(f"已清空 {len(keys)} 条去重记录")
            else:
                logger.info("没有需要清空的去重记录")

            return True

        except Exception as e:
            logger.error(f"清空去重数据失败: {e}")
            return False