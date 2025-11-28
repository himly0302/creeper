"""
LLM 模型能力探测与缓存模块

功能:
- 自动探测模型的 max_input_tokens 和 max_output_tokens
- Redis + 本地 JSON 文件混合持久化
- 探测失败时的智能回退
"""

import json
import hashlib
import redis
from pathlib import Path
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
    使用 Redis + 本地 JSON 文件混合持久化策略
    """

    def __init__(self):
        """初始化模型能力管理器"""
        self.key_prefix = f"{config.REDIS_KEY_PREFIX}model:"
        self.cache_file = Path(config.MODEL_CAPABILITY_CACHE_FILE)
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
            logger.warning(f"Redis 连接失败: {e}，将仅使用本地缓存")

        # 确保缓存目录存在
        if config.ENABLE_LOCAL_PERSISTENCE:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"本地持久化已启用: {self.cache_file}")

        # 从本地文件恢复数据（如果 Redis 为空）
        self._restore_from_file_if_needed()

    def _get_cache_key(self, model: str, base_url: str) -> str:
        """
        生成缓存 key

        Args:
            model: 模型名称
            base_url: API Base URL

        Returns:
            Redis key
        """
        # 使用 model + base_url 的组合作为唯一标识
        # 对 base_url 进行哈希以避免 key 过长
        url_hash = hashlib.md5(base_url.encode('utf-8')).hexdigest()[:8]
        return f"{self.key_prefix}{model}:{url_hash}"

    def _load_cache_file(self) -> dict:
        """
        从本地文件加载缓存数据

        Returns:
            缓存数据字典
        """
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载缓存文件失败: {e}")
        return {}

    def _save_to_file(self, cache_data: dict):
        """
        保存缓存数据到本地文件

        Args:
            cache_data: 缓存数据字典
        """
        if not config.ENABLE_LOCAL_PERSISTENCE:
            return

        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"已保存 {len(cache_data)} 条模型能力到缓存文件")
        except Exception as e:
            logger.error(f"保存缓存文件失败: {e}")

    def _restore_from_file_if_needed(self):
        """
        启动时从文件恢复数据到 Redis（如 Redis 为空或连接失败）
        """
        if not config.ENABLE_LOCAL_PERSISTENCE:
            return

        if not self.redis_available:
            logger.info("Redis 不可用，仅使用本地缓存文件")
            return

        try:
            # 检查 Redis 是否已有数据
            try:
                pattern = f"{self.key_prefix}*"
                keys = list(self.redis.scan_iter(match=pattern, count=10))
                if keys:
                    logger.info("Redis 已有模型能力数据，跳过恢复")
                    return
            except redis.RedisError:
                logger.warning("Redis 连接失败，尝试从本地文件恢复")

            # 从文件加载
            if not self.cache_file.exists():
                logger.info("本地模型能力缓存文件不存在，跳过恢复")
                return

            cache_data = self._load_cache_file()
            if not cache_data:
                logger.info("本地模型能力缓存文件为空，跳过恢复")
                return

            # 批量写入 Redis
            restored_count = 0
            for cache_key, info in cache_data.items():
                try:
                    key = f"{self.key_prefix}{cache_key}"
                    self.redis.hset(key, mapping=info)
                    restored_count += 1
                except Exception as e:
                    logger.warning(f"恢复模型能力记录失败: {cache_key}, {e}")
                    continue

            logger.info(f"从本地文件恢复 {restored_count} 条模型能力记录")
        except Exception as e:
            logger.error(f"恢复模型能力数据失败: {e}，继续使用空 Redis")

    def _get_from_cache(self, model: str, base_url: str) -> Optional[Dict]:
        """
        从缓存获取模型能力

        Args:
            model: 模型名称
            base_url: API Base URL

        Returns:
            模型能力字典，如果不存在返回 None
        """
        cache_key = self._get_cache_key(model, base_url)

        # 尝试从 Redis 读取
        if self.redis_available:
            try:
                data = self.redis.hgetall(cache_key)
                if data:
                    logger.debug(f"从 Redis 缓存获取模型能力: {model}")
                    return {
                        'max_input_tokens': int(data.get('max_input_tokens', 0)),
                        'max_output_tokens': int(data.get('max_output_tokens', 0))
                    }
            except redis.RedisError as e:
                logger.warning(f"从 Redis 读取失败: {e}")

        # 回退到本地文件
        if config.ENABLE_LOCAL_PERSISTENCE:
            cache_data = self._load_cache_file()
            # 使用 model:url_hash 作为 key
            simple_key = cache_key.replace(self.key_prefix, '')
            if simple_key in cache_data:
                info = cache_data[simple_key]
                logger.debug(f"从本地文件获取模型能力: {model}")
                return {
                    'max_input_tokens': int(info.get('max_input_tokens', 0)),
                    'max_output_tokens': int(info.get('max_output_tokens', 0))
                }

        return None

    def _save_to_cache(self, model: str, base_url: str, capability: Dict):
        """
        保存模型能力到缓存

        Args:
            model: 模型名称
            base_url: API Base URL
            capability: 能力字典
        """
        cache_key = self._get_cache_key(model, base_url)
        data = {
            'model': model,
            'base_url': base_url,
            'max_input_tokens': str(capability['max_input_tokens']),
            'max_output_tokens': str(capability['max_output_tokens']),
            'detected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'detection_method': 'api_query'
        }

        # 保存到 Redis
        if self.redis_available:
            try:
                self.redis.hset(cache_key, mapping=data)
                logger.debug(f"模型能力已缓存到 Redis: {cache_key}")
            except redis.RedisError as e:
                logger.warning(f"保存到 Redis 失败: {e}")

        # 保存到本地文件
        if config.ENABLE_LOCAL_PERSISTENCE:
            try:
                cache_data = self._load_cache_file()
                simple_key = cache_key.replace(self.key_prefix, '')
                cache_data[simple_key] = data
                self._save_to_file(cache_data)
            except Exception as e:
                logger.error(f"保存到本地文件失败: {e}")

    async def _detect_capability(self, model: str, client: AsyncOpenAI) -> Dict:
        """
        通过 API 探测模型能力

        Args:
            model: 模型名称
            client: OpenAI 客户端实例

        Returns:
            能力字典 {'max_input_tokens': int, 'max_output_tokens': int}

        Raises:
            Exception: 探测失败时抛出异常
        """
        detection_prompt = """请提供你的模型能力信息，使用 JSON 格式回复：

{
  "max_input_tokens": <最大输入 token 数>,
  "max_output_tokens": <最大输出 token 数>
}

仅返回 JSON，不要包含其他文本。"""

        try:
            logger.info(f"正在探测模型能力: {model}")
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个模型能力查询助手，请准确返回模型的 token 限制信息。"},
                    {"role": "user", "content": detection_prompt}
                ],
                max_tokens=500,  # 探测只需要很少的 tokens
                temperature=0.0  # 使用最严格的温度以获得准确信息
            )

            content = response.choices[0].message.content.strip()
            logger.debug(f"模型返回内容: {content}")

            # 解析 JSON 响应
            # 尝试提取 JSON 块（处理可能包含 markdown 格式的响应）
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            capability_data = json.loads(content)

            max_input = int(capability_data.get('max_input_tokens', 0))
            max_output = int(capability_data.get('max_output_tokens', 0))

            if max_input <= 0 or max_output <= 0:
                raise ValueError(f"探测到的 token 限制无效: input={max_input}, output={max_output}")

            logger.info(f"模型能力探测成功: max_input_tokens={max_input}, max_output_tokens={max_output}")
            return {
                'max_input_tokens': max_input,
                'max_output_tokens': max_output
            }

        except json.JSONDecodeError as e:
            raise RuntimeError(f"解析模型响应失败: {e}, 响应内容: {content}")
        except Exception as e:
            raise RuntimeError(f"探测模型能力失败: {e}")

    async def get_or_detect(self, model: str, base_url: str, client: AsyncOpenAI,
                           fallback_max_tokens: int) -> Dict:
        """
        获取或探测模型能力

        Args:
            model: 模型名称
            base_url: API Base URL
            client: OpenAI 客户端实例
            fallback_max_tokens: 探测失败时的回退值

        Returns:
            能力字典 {'max_input_tokens': int, 'max_output_tokens': int}
        """
        # 1. 检查缓存
        cached = self._get_from_cache(model, base_url)
        if cached:
            logger.info(f"使用缓存的模型能力: {model} (max_output_tokens={cached['max_output_tokens']})")
            return cached

        # 2. 尝试探测
        try:
            capability = await self._detect_capability(model, client)
            # 3. 缓存结果
            self._save_to_cache(model, base_url, capability)
            return capability
        except Exception as e:
            logger.warning(f"模型能力探测失败，使用回退值 {fallback_max_tokens}: {e}")
            # 使用回退值（假设输入是输出的 2 倍）
            return {
                'max_input_tokens': fallback_max_tokens * 2,
                'max_output_tokens': fallback_max_tokens
            }
