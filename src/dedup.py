"""
Redis 去重模块
使用 Redis 存储已爬取的 URL,实现去重功能
支持本地文件持久化,实现混合存储
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
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
        self.cache_file = Path(config.DEDUP_CACHE_FILE)
        logger.info(f"Redis 去重管理器已初始化: {config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}")

        # 如果启用本地持久化,尝试从文件恢复数据
        if config.ENABLE_LOCAL_PERSISTENCE:
            logger.info(f"本地持久化已启用: {self.cache_file}")
            self.restore_from_file_if_needed()

    def _load_cache_file(self) -> dict:
        """
        加载本地缓存文件

        Returns:
            缓存数据字典
        """
        try:
            if not self.cache_file.exists():
                return {'version': '1.0', 'updated_at': None, 'data': {}}

            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"从缓存文件加载 {len(data.get('data', {}))} 条记录")
                return data
        except json.JSONDecodeError as e:
            logger.error(f"缓存文件格式错误: {e},使用空数据")
            return {'version': '1.0', 'updated_at': None, 'data': {}}
        except Exception as e:
            logger.error(f"加载缓存文件失败: {e}")
            return {'version': '1.0', 'updated_at': None, 'data': {}}

    def _save_to_file(self):
        """
        保存当前数据到本地文件
        """
        try:
            # 确保目录存在
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            # 加载现有数据
            cache_data = self._load_cache_file()

            # 从 Redis 获取所有去重记录
            pattern = f"{self.key_prefix}url:*"
            keys = list(self.redis.scan_iter(match=pattern, count=100))

            # 更新缓存数据
            for key in keys:
                try:
                    info = self.redis.hgetall(key)
                    if info and 'url' in info:
                        url_hash = hashlib.md5(info['url'].encode('utf-8')).hexdigest()
                        cache_data['data'][url_hash] = info
                except Exception as e:
                    logger.warning(f"读取 Redis key 失败: {key}, {e}")
                    continue

            cache_data['updated_at'] = datetime.now().isoformat()

            # 原子写入 (先写临时文件,再重命名)
            temp_file = self.cache_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            temp_file.replace(self.cache_file)

            logger.debug(f"已保存 {len(cache_data['data'])} 条记录到缓存文件")
        except Exception as e:
            logger.error(f"保存缓存文件失败: {e}")

    def _mark_file(self, url: str):
        """
        标记 URL 到本地文件

        Args:
            url: URL 字符串
        """
        try:
            # 确保目录存在
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            # 加载现有数据
            cache_data = self._load_cache_file()

            # 添加新记录
            from .utils import get_timestamp
            url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
            cache_data['data'][url_hash] = {
                'url': url,
                'crawled_at': get_timestamp(),
                'status': 'completed'
            }
            cache_data['updated_at'] = datetime.now().isoformat()

            # 原子写入
            temp_file = self.cache_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            temp_file.replace(self.cache_file)

            logger.debug(f"已标记到文件: {url}")
        except Exception as e:
            logger.error(f"标记到文件失败: {e}")

    def restore_from_file_if_needed(self):
        """
        启动时从文件恢复数据到 Redis (如 Redis 为空或连接失败)
        """
        if not config.ENABLE_LOCAL_PERSISTENCE:
            return

        try:
            # 检查 Redis 连接
            try:
                redis_has_data = self.redis.exists(f"{self.key_prefix}url:*")
                if redis_has_data:
                    logger.info("Redis 已有数据,跳过恢复")
                    return
            except redis.RedisError:
                logger.warning("Redis 连接失败,尝试从本地文件恢复")

            # 从文件加载
            if not self.cache_file.exists():
                logger.info("本地缓存文件不存在,跳过恢复")
                return

            cache_data = self._load_cache_file()
            data_dict = cache_data.get('data', {})

            if not data_dict:
                logger.info("本地缓存文件为空,跳过恢复")
                return

            # 批量写入 Redis
            restored_count = 0
            for url_hash, info in data_dict.items():
                try:
                    key = self._get_key(info['url'])
                    self.redis.hset(key, mapping=info)
                    self.redis.expire(key, 30 * 86400)  # 30天
                    restored_count += 1
                except Exception as e:
                    logger.warning(f"恢复记录失败: {info.get('url', 'unknown')}, {e}")
                    continue

            logger.info(f"从本地文件恢复 {restored_count} 条去重记录")
        except Exception as e:
            logger.error(f"恢复数据失败: {e},继续使用空 Redis")

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
        标记 URL 为已爬取,同时写入 Redis 和本地文件

        Args:
            url: URL 字符串
            expire_days: 过期天数(默认 30 天后自动删除)

        Returns:
            成功返回 True,失败返回 False
        """
        redis_success = False
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

            logger.debug(f"标记 URL 已爬取 (Redis): {url}")
            redis_success = True
        except redis.RedisError as e:
            logger.error(f"Redis 写入失败: {e}")

        # 如果启用本地持久化,同时写入文件
        if config.ENABLE_LOCAL_PERSISTENCE:
            try:
                self._mark_file(url)
            except Exception as e:
                logger.error(f"写入本地文件失败: {e}")

        return redis_success

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
        同时清空 Redis 和本地文件

        Returns:
            成功返回 True,失败返回 False
        """
        redis_success = False
        try:
            # 获取所有匹配的 key
            pattern = f"{self.key_prefix}url:*"
            keys = list(self.redis.scan_iter(match=pattern, count=100))

            if keys:
                self.redis.delete(*keys)
                logger.warning(f"已清空 {len(keys)} 条爬取记录 (Redis)")
            else:
                logger.info("没有需要清空的记录 (Redis)")
            redis_success = True
        except redis.RedisError as e:
            logger.error(f"Redis 清空失败: {e}")

        # 如果启用本地持久化,同时清空文件
        if config.ENABLE_LOCAL_PERSISTENCE:
            try:
                if self.cache_file.exists():
                    self.cache_file.unlink()
                    logger.warning(f"已删除本地缓存文件: {self.cache_file}")
            except Exception as e:
                logger.error(f"删除本地缓存文件失败: {e}")

        return redis_success

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
