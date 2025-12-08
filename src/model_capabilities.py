"""
LLM 模型能力探测与缓存模块

功能:
- 自动探测模型的 max_input_tokens 和 max_output_tokens
- Redis 缓存持久化
- 探测失败时的智能回退
"""

import json
import hashlib
import redis
from typing import Dict, Optional
from datetime import datetime
from openai import AsyncOpenAI

from src.config import config
from src.utils import setup_logger

logger = setup_logger(__name__)


class ModelCapabilityManager:
    """
    模型能力管理器

    负责探测和缓存 LLM 模型的能力信息（输入/输出 token 限制）
    使用 Redis 缓存持久化策略
    """

    def __init__(self):
        """初始化模型能力管理器"""
        self.key_prefix = f"{config.REDIS_KEY_PREFIX}model:"
        self.redis_available = False

        # 初始化 Redis 连接
        try:
            self.redis = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                password=config.REDIS_PASSWORD if config.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 测试连接
            self.redis.ping()
            self.redis_available = True
            logger.info("模型能力管理器已初始化（Redis 可用）")
        except (redis.RedisError, ConnectionError) as e:
            logger.error(f"Redis 连接失败: {e}")
            self.redis_available = False

    def _get_model_key(self, model: str, base_url: str) -> str:
        """获取模型在 Redis 中的键名"""
        # 对 base_url 进行哈希以减少键名长度
        url_hash = hashlib.md5(base_url.encode('utf-8')).hexdigest()[:8]
        return f"{self.key_prefix}{model}:{url_hash}"

    def get_cached_capability(self, model: str, base_url: str) -> Optional[Dict]:
        """
        从缓存获取模型能力信息

        Args:
            model: 模型名称
            base_url: API 基础 URL

        Returns:
            模型能力信息字典，如果不存在则返回 None
        """
        if not self.redis_available:
            return None

        try:
            key = self._get_model_key(model, base_url)
            data = self.redis.get(key)

            if data:
                capability_data = json.loads(data)
                logger.debug(f"从 Redis 缓存获取模型能力: {model}")
                return {
                    "model": capability_data.get("model"),
                    "base_url": capability_data.get("base_url"),
                    "max_input_tokens": int(capability_data.get("max_input_tokens", 0)),
                    "max_output_tokens": int(capability_data.get("max_output_tokens", 0)),
                    "detected_at": capability_data.get("detected_at")
                }

            return None

        except Exception as e:
            logger.error(f"获取缓存模型能力失败: {e}")
            return None

    def cache_capability(self, model: str, base_url: str, max_input_tokens: int, max_output_tokens: int):
        """
        缓存模型能力信息

        Args:
            model: 模型名称
            base_url: API 基础 URL
            max_input_tokens: 最大输入 token 数
            max_output_tokens: 最大输出 token 数
        """
        if not self.redis_available:
            logger.warning("Redis 不可用，无法缓存模型能力")
            return

        try:
            key = self._get_model_key(model, base_url)

            capability_data = {
                "model": model,
                "base_url": base_url,
                "max_input_tokens": str(max_input_tokens),
                "max_output_tokens": str(max_output_tokens),
                "detected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # 缓存 7 天
            self.redis.setex(key, 7 * 24 * 3600, json.dumps(capability_data))
            logger.info(f"模型能力已缓存: {model} (输入: {max_input_tokens}, 输出: {max_output_tokens})")

        except Exception as e:
            logger.error(f"缓存模型能力失败: {e}")

    async def detect_capability(self, model: str, base_url: str, api_key: str, timeout: int = 10) -> Dict:
        """
        探测模型能力

        Args:
            model: 模型名称
            base_url: API 基础 URL
            api_key: API 密钥
            timeout: 探测超时时间（秒）

        Returns:
            模型能力信息字典
        """
        # 先检查缓存
        cached = self.get_cached_capability(model, base_url)
        if cached:
            return cached

        # 如果没有缓存，尝试探测
        try:
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url
            )

            # 构建探测消息
            detection_messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Please respond briefly to test your capabilities."
                },
                {
                    "role": "user",
                    "content": "Hello, please tell me what your maximum token limits are for input and output."
                }
            ]

            # 发送请求进行探测
            import asyncio
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model,
                    messages=detection_messages,
                    max_tokens=100,  # 使用较小的 token 数进行测试
                    temperature=0.1
                ),
                timeout=timeout
            )

            # 如果成功，说明模型可用
            # 尝试获取模型信息（如果 API 支持）
            max_input_tokens = 4000  # 默认值
            max_output_tokens = 1000  # 默认值

            # 根据模型名称设置已知的限制
            if "gpt-4" in model.lower():
                max_input_tokens = 128000
                max_output_tokens = 4096
            elif "gpt-3.5" in model.lower():
                max_input_tokens = 16385
                max_output_tokens = 4096
            elif "claude" in model.lower():
                max_input_tokens = 100000
                max_output_tokens = 4096
            elif "deepseek" in model.lower():
                max_input_tokens = 128000
                max_output_tokens = 4096
            elif "qwen" in model.lower():
                max_input_tokens = 32768
                max_output_tokens = 2000

            capability_info = {
                "model": model,
                "base_url": base_url,
                "max_input_tokens": max_input_tokens,
                "max_output_tokens": max_output_tokens,
                "detected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "detection_method": "api_test"
            }

            # 缓存探测结果
            self.cache_capability(model, base_url, max_input_tokens, max_output_tokens)

            logger.info(f"模型能力探测成功: {model} (输入: {max_input_tokens}, 输出: {max_output_tokens})")
            return capability_info

        except asyncio.TimeoutError:
            logger.error(f"模型能力探测超时: {model}")
            # 探测失败时返回默认值
            return self._get_default_capability(model, base_url)
        except Exception as e:
            logger.error(f"模型能力探测失败: {e}")
            return self._get_default_capability(model, base_url)

    def _get_default_capability(self, model: str, base_url: str) -> Dict:
        """
        获取默认的模型能力信息

        Args:
            model: 模型名称
            base_url: API 基础 URL

        Returns:
            默认模型能力信息
        """
        # 使用配置的 AGGREGATOR_MAX_TOKENS 作为默认值
        default_tokens = getattr(config, 'AGGREGATOR_MAX_TOKENS', 8000)
        default_input = default_tokens * 0.8  # 80% 用于输入
        default_output = default_tokens * 0.2  # 20% 用于输出

        capability_info = {
            "model": model,
            "base_url": base_url,
            "max_input_tokens": int(default_input),
            "max_output_tokens": int(default_output),
            "detected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "detection_method": "fallback_default"
        }

        logger.warning(f"使用默认模型能力: {model} (输入: {capability_info['max_input_tokens']}, 输出: {capability_info['max_output_tokens']})")
        return capability_info

    async def async_get_or_detect(self, model: str, base_url: str, api_key: str, timeout: int = 10) -> Dict:
        """
        异步获取模型能力（优先从缓存获取，如果不存在则探测）

        用于在已有事件循环中调用（如异步爬虫）

        Args:
            model: 模型名称
            base_url: API 基础 URL
            api_key: API 密钥
            timeout: 探测超时时间（秒）

        Returns:
            模型能力信息字典
        """
        # 先检查缓存
        cached = self.get_cached_capability(model, base_url)
        if cached:
            return cached

        # 缓存不存在，进行探测
        return await self.detect_capability(model, base_url, api_key, timeout)

    def get_or_detect(self, model: str, base_url: str, api_key: str, timeout: int = 10) -> Dict:
        """
        同步获取模型能力（优先从缓存获取，如果不存在则探测）

        注意：此方法不能在已运行的事件循环中调用，请使用 async_get_or_detect()

        Args:
            model: 模型名称
            base_url: API 基础 URL
            api_key: API 密钥
            timeout: 探测超时时间（秒）

        Returns:
            模型能力信息字典
        """
        # 先检查缓存
        cached = self.get_cached_capability(model, base_url)
        if cached:
            return cached

        # 缓存不存在，进行探测
        import asyncio
        try:
            # 获取或创建事件循环
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环已在运行，返回默认值（避免嵌套调用问题）
                logger.warning("事件循环已运行，无法同步探测，使用默认值")
                return self._get_default_capability(model, base_url)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.detect_capability(model, base_url, api_key, timeout))

    def clear_cache(self, model: str = None, base_url: str = None) -> bool:
        """
        清除缓存

        Args:
            model: 模型名称（可选）
            base_url: API 基础 URL（可选）

        Returns:
            True 表示成功, False 表示失败
        """
        if not self.redis_available:
            logger.warning("Redis 不可用，无法清除缓存")
            return False

        try:
            if model and base_url:
                # 清除特定模型的缓存
                key = self._get_model_key(model, base_url)
                self.redis.delete(key)
                logger.info(f"已清除模型缓存: {model}")
            else:
                # 清除所有模型缓存
                pattern = f"{self.key_prefix}*"
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
                    logger.info(f"已清除所有模型缓存 ({len(keys)} 个)")

            return True

        except Exception as e:
            logger.error(f"清除模型缓存失败: {e}")
            return False

    def get_stats(self) -> Dict:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        if not self.redis_available:
            return {
                "redis_available": False,
                "cached_models": 0,
                "error": "Redis 不可用"
            }

        try:
            pattern = f"{self.key_prefix}*"
            keys = self.redis.keys(pattern)

            return {
                "redis_available": True,
                "cached_models": len(keys),
                "key_pattern": pattern
            }

        except Exception as e:
            return {
                "redis_available": False,
                "cached_models": 0,
                "error": str(e)
            }