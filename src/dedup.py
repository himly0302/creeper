"""
Redis 去重模块
使用 Redis 存储已爬取的 URL,实现去重功能
"""

import hashlib
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

    def _get_key(self, url: str) -> str:
        """
        生成 Redis key

        Args:
            url: URL 字符串

        Returns:
            Redis key
        """
        # 使用 MD5 哈希 URL 作为 key,避免 URL 过长
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        return f"{self.key_prefix}url:{url_hash}"

    def is_crawled(self, url: str) -> bool:
        """
        检查 URL 是否已被爬取

        Args:
            url: URL 字符串

        Returns:
            True 表示已爬取,False 表示未爬取
        """
        try:
            key = self._get_key(url)
            exists = self.redis.exists(key)
            if exists:
                logger.debug(f"URL 已存在: {url}")
            return bool(exists)
        except redis.RedisError as e:
            logger.error(f"Redis 查询失败: {e}")
            # Redis 失败时,返回 False 允许爬取(避免因 Redis 问题导致无法工作)
            return False

    def mark_crawled(self, url: str, expire_days: int = 30) -> bool:
        """
        标记 URL 为已爬取

        Args:
            url: URL 字符串
            expire_days: 过期天数(默认 30 天后自动删除)

        Returns:
            成功返回 True,失败返回 False
        """
        try:
            key = self._get_key(url)
            # 存储爬取时间戳
            from .utils import get_timestamp
            timestamp = get_timestamp()

            # 使用 Hash 存储更多信息
            self.redis.hset(key, mapping={
                'url': url,
                'crawled_at': timestamp,
                'status': 'completed'
            })

            # 设置过期时间(天 -> 秒)
            if expire_days > 0:
                self.redis.expire(key, expire_days * 86400)

            logger.debug(f"标记 URL 已爬取: {url}")
            return True
        except redis.RedisError as e:
            logger.error(f"Redis 写入失败: {e}")
            return False

    def get_crawl_info(self, url: str) -> Optional[dict]:
        """
        获取 URL 的爬取信息

        Args:
            url: URL 字符串

        Returns:
            爬取信息字典,如果不存在返回 None
        """
        try:
            key = self._get_key(url)
            info = self.redis.hgetall(key)
            return info if info else None
        except redis.RedisError as e:
            logger.error(f"Redis 查询失败: {e}")
            return None

    def delete(self, url: str) -> bool:
        """
        删除 URL 记录(用于强制重新爬取)

        Args:
            url: URL 字符串

        Returns:
            成功返回 True,失败返回 False
        """
        try:
            key = self._get_key(url)
            self.redis.delete(key)
            logger.debug(f"删除 URL 记录: {url}")
            return True
        except redis.RedisError as e:
            logger.error(f"Redis 删除失败: {e}")
            return False

    def clear_all(self) -> bool:
        """
        清空所有爬取记录(谨慎使用!)

        Returns:
            成功返回 True,失败返回 False
        """
        try:
            # 获取所有匹配的 key
            pattern = f"{self.key_prefix}url:*"
            keys = list(self.redis.scan_iter(match=pattern, count=100))

            if keys:
                self.redis.delete(*keys)
                logger.warning(f"已清空 {len(keys)} 条爬取记录")
            else:
                logger.info("没有需要清空的记录")
            return True
        except redis.RedisError as e:
            logger.error(f"Redis 清空失败: {e}")
            return False

    def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        try:
            pattern = f"{self.key_prefix}url:*"
            keys = list(self.redis.scan_iter(match=pattern, count=100))
            return {
                'total_crawled': len(keys),
                'redis_connected': True
            }
        except redis.RedisError as e:
            logger.error(f"Redis 统计失败: {e}")
            return {
                'total_crawled': 0,
                'redis_connected': False,
                'error': str(e)
            }

    def test_connection(self) -> bool:
        """
        测试 Redis 连接

        Returns:
            连接成功返回 True,失败返回 False
        """
        try:
            self.redis.ping()
            logger.info("Redis 连接测试成功")
            return True
        except redis.RedisError as e:
            logger.error(f"Redis 连接测试失败: {e}")
            return False

    def close(self):
        """关闭 Redis 连接"""
        try:
            self.redis.close()
            logger.info("Redis 连接已关闭")
        except Exception as e:
            logger.error(f"关闭 Redis 连接失败: {e}")
