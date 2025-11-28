#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件解析功能 - 核心模块

功能:
- 文件扫描: 递归扫描文件夹获取文件内容（复用 FileScanner）
- 文件级缓存: 基于 Redis 追踪已处理文件（混合存储）
- LLM 解析: 独立调用 LLM API 处理每个文件
"""

import asyncio
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import redis
from openai import AsyncOpenAI

from src.config import config
from src.file_aggregator import FileItem, FileScanner
from src.utils import setup_logger

logger = setup_logger(__name__)


class ParserCache:
    """文件解析缓存管理器（文件级缓存）"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        初始化缓存管理器

        Args:
            redis_client: Redis 客户端实例，如果为 None 则自动创建
        """
        if redis_client is None:
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
                logger.debug("Redis 连接成功")
            except Exception as e:
                logger.warning(f"Redis 连接失败: {e}")
                self.redis = None
                self.redis_available = False
        else:
            self.redis = redis_client
            self.redis_available = True

        self.key_prefix = f"{config.REDIS_KEY_PREFIX}parser:"
        self.cache_file = Path("data/parser_cache.json")
        logger.info(f"文件解析缓存管理器已初始化")

        # 如果启用本地持久化，尝试从文件恢复数据
        if config.ENABLE_LOCAL_PERSISTENCE:
            logger.info(f"本地持久化已启用: {self.cache_file}")
            self._restore_from_file_if_needed()

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
            logger.error(f"缓存文件格式错误: {e}，使用空数据")
            return {'version': '1.0', 'updated_at': None, 'data': {}}
        except Exception as e:
            logger.error(f"加载缓存文件失败: {e}")
            return {'version': '1.0', 'updated_at': None, 'data': {}}

    def _save_to_file(self):
        """
        保存当前数据到本地文件
        """
        if not self.redis_available:
            return

        try:
            # 确保目录存在
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            # 加载现有数据
            cache_data = self._load_cache_file()

            # 从 Redis 获取所有解析记录
            pattern = f"{self.key_prefix}*"
            keys = list(self.redis.scan_iter(match=pattern, count=100))

            # 更新缓存数据
            for key in keys:
                try:
                    info = self.redis.hgetall(key)
                    if info and 'path' in info:
                        file_hash = hashlib.md5(info['path'].encode('utf-8')).hexdigest()
                        cache_data['data'][file_hash] = info
                except Exception as e:
                    logger.warning(f"读取 Redis key 失败: {key}, {e}")
                    continue

            cache_data['updated_at'] = datetime.now().isoformat()

            # 原子写入（先写临时文件，再重命名）
            temp_file = self.cache_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            temp_file.replace(self.cache_file)

            logger.debug(f"已保存 {len(cache_data['data'])} 条记录到缓存文件")
        except Exception as e:
            logger.error(f"保存缓存文件失败: {e}")

    def _restore_from_file_if_needed(self):
        """
        启动时从文件恢复数据到 Redis（如 Redis 为空或连接失败）
        """
        if not config.ENABLE_LOCAL_PERSISTENCE:
            return

        if not self.redis_available:
            return

        try:
            # 检查 Redis 连接
            try:
                pattern = f"{self.key_prefix}*"
                keys = list(self.redis.scan_iter(match=pattern, count=10))
                if keys:
                    logger.info("Redis 已有数据，跳过恢复")
                    return
            except redis.RedisError:
                logger.warning("Redis 连接失败，尝试从本地文件恢复")

            # 从文件加载
            if not self.cache_file.exists():
                logger.info("本地缓存文件不存在，跳过恢复")
                return

            cache_data = self._load_cache_file()
            data_dict = cache_data.get('data', {})

            if not data_dict:
                logger.info("本地缓存文件为空，跳过恢复")
                return

            # 批量写入 Redis
            restored_count = 0
            for file_hash, info in data_dict.items():
                try:
                    key = self._get_key(info['path'])
                    self.redis.hset(key, mapping=info)
                    restored_count += 1
                except Exception as e:
                    logger.warning(f"恢复记录失败: {info.get('path', 'unknown')}, {e}")
                    continue

            logger.info(f"从本地文件恢复 {restored_count} 条解析记录")
        except Exception as e:
            logger.error(f"恢复数据失败: {e}，继续使用空 Redis")

    def _get_key(self, file_path: str) -> str:
        """
        生成 Redis key

        Args:
            file_path: 文件路径

        Returns:
            Redis key
        """
        # 使用 MD5 哈希文件路径作为 key
        file_hash = hashlib.md5(file_path.encode('utf-8')).hexdigest()
        return f"{self.key_prefix}{file_hash}"

    def is_processed(self, file_item: FileItem, output_folder: str) -> bool:
        """
        检查文件是否已处理且内容未变更

        Args:
            file_item: 文件对象
            output_folder: 输出文件夹路径

        Returns:
            True 表示已处理且内容未变更，False 表示需要处理
        """
        if not self.redis_available:
            return False

        try:
            key = self._get_key(file_item.path)
            info = self.redis.hgetall(key)

            if not info:
                return False

            # 检查文件哈希是否变化
            if info.get('hash') != file_item.hash:
                logger.debug(f"文件已变更: {file_item.path}")
                return False

            # 检查输出文件是否存在
            output_path = info.get('output_path', '')
            if output_path and not os.path.exists(output_path):
                logger.debug(f"输出文件已被删除: {output_path}")
                return False

            logger.debug(f"文件已处理且未变更: {file_item.path}")
            return True

        except redis.RedisError as e:
            logger.error(f"Redis 查询失败: {e}")
            return False

    def mark_processed(self, file_item: FileItem, output_path: str) -> bool:
        """
        标记文件为已处理，同时写入 Redis 和本地文件

        Args:
            file_item: 文件对象
            output_path: 输出文件路径

        Returns:
            成功返回 True，失败返回 False
        """
        redis_success = False
        try:
            key = self._get_key(file_item.path)

            # 使用 Hash 存储更多信息
            self.redis.hset(key, mapping={
                'path': file_item.path,
                'hash': file_item.hash,
                'parsed_at': datetime.now().isoformat(),
                'output_path': output_path,
                'size': str(file_item.size)
            })

            logger.debug(f"标记文件已处理 (Redis): {file_item.path}")
            redis_success = True
        except redis.RedisError as e:
            logger.error(f"Redis 写入失败: {e}")
        except Exception as e:
            logger.error(f"标记文件失败: {e}")

        # 如果启用本地持久化，同时写入文件
        if config.ENABLE_LOCAL_PERSISTENCE and redis_success:
            try:
                self._save_to_file()
            except Exception as e:
                logger.error(f"写入本地文件失败: {e}")

        return redis_success

    def get_unprocessed_files(self, files: List[FileItem], output_folder: str) -> List[FileItem]:
        """
        获取未处理或已变更的文件

        Args:
            files: 文件列表
            output_folder: 输出文件夹路径

        Returns:
            需要处理的文件列表
        """
        if not self.redis_available:
            logger.warning("Redis 不可用，处理所有文件")
            return files

        unprocessed = []
        for file_item in files:
            if not self.is_processed(file_item, output_folder):
                unprocessed.append(file_item)

        logger.info(f"检测到 {len(unprocessed)} 个新增或变更的文件（共 {len(files)} 个文件）")
        return unprocessed

    def clear_all(self) -> bool:
        """
        清空所有解析记录（谨慎使用！）
        同时清空 Redis 和本地文件

        Returns:
            成功返回 True，失败返回 False
        """
        redis_success = False
        try:
            # 获取所有匹配的 key
            pattern = f"{self.key_prefix}*"
            keys = list(self.redis.scan_iter(match=pattern, count=100))

            if keys:
                self.redis.delete(*keys)
                logger.warning(f"已清空 {len(keys)} 条解析记录 (Redis)")
            else:
                logger.info("没有需要清空的记录 (Redis)")
            redis_success = True
        except redis.RedisError as e:
            logger.error(f"Redis 清空失败: {e}")

        # 如果启用本地持久化，同时清空文件
        if config.ENABLE_LOCAL_PERSISTENCE:
            try:
                if self.cache_file.exists():
                    self.cache_file.unlink()
                    logger.warning(f"已删除本地缓存文件: {self.cache_file}")
            except Exception as e:
                logger.error(f"删除本地缓存文件失败: {e}")

        return redis_success


class FileParser:
    """文件解析器（一对一处理）"""

    def __init__(self, api_key: str, base_url: str, model: str, max_tokens: int, temperature: float = 0.1):
        """
        初始化文件解析器

        Args:
            api_key: API Key
            base_url: API Base URL
            model: 模型名称
            max_tokens: 最大 token 数
            temperature: 生成温度（默认 0.1，更严格遵循指令）
        """
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.cache = ParserCache()

    async def parse_file(self, file_item: FileItem, prompt_template: str) -> str:
        """
        调用 LLM 解析单个文件

        Args:
            file_item: 文件对象
            prompt_template: 提示词模板

        Returns:
            解析后的内容
        """
        # 构建消息
        messages = [
            {"role": "system", "content": prompt_template},
            {"role": "user", "content": f"文件路径: {file_item.path}\n文件大小: {file_item.size} bytes\n\n文件内容:\n\n```\n{file_item.content}\n```"}
        ]

        # 调用 LLM API
        try:
            logger.debug(f"调用 LLM API 解析文件: {file_item.path}")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            content = response.choices[0].message.content
            logger.debug(f"LLM 返回内容长度: {len(content)} 字符")
            return content

        except Exception as e:
            logger.error(f"LLM API 调用失败: {e}")
            # 抛出异常而不是返回错误字符串，让调用方决定如何处理
            raise RuntimeError(f"解析文件 {file_item.path} 失败: {e}") from e

    def get_output_path(self, input_folder: str, input_file: str, output_folder: str) -> str:
        """
        保持相对路径结构，扩展名改为 .md

        Args:
            input_folder: 输入文件夹路径
            input_file: 输入文件路径
            output_folder: 输出文件夹路径

        Returns:
            输出文件路径
        """
        # 获取相对路径
        rel_path = os.path.relpath(input_file, input_folder)

        # 拼接输出路径
        output_path = os.path.join(output_folder, rel_path)

        # 替换扩展名为 .md
        output_path = os.path.splitext(output_path)[0] + ".md"

        # 规范化路径（防止路径遍历）
        output_path = os.path.abspath(output_path)
        output_folder = os.path.abspath(output_folder)

        # 检查路径是否在输出文件夹内
        if not output_path.startswith(output_folder):
            logger.error(f"路径遍历检测: {output_path} 不在 {output_folder} 内")
            raise ValueError("非法的输出路径")

        return output_path

    async def _process_file(self, file_item: FileItem, input_folder: str, output_folder: str, template: str):
        """
        处理单个文件（带错误处理）

        Args:
            file_item: 文件对象
            input_folder: 输入文件夹路径
            output_folder: 输出文件夹路径
            template: 提示词模板内容
        """
        try:
            # 解析文件
            result = await self.parse_file(file_item, template)

            # 保存结果
            output_path = self.get_output_path(input_folder, file_item.path, output_folder)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)

            # 更新缓存
            self.cache.mark_processed(file_item, output_path)

            logger.info(f"✓ 已处理: {file_item.path} → {output_path}")

        except Exception as e:
            logger.error(f"✗ 处理失败: {file_item.path} - {str(e)}", exc_info=config.DEBUG)
            # 不再生成失败的文件

    async def parse_directory(self, input_folder: str, output_folder: str, template: str,
                             extensions: List[str], force: bool = False, concurrency: int = 5):
        """
        批量解析文件夹

        Args:
            input_folder: 输入文件夹路径
            output_folder: 输出文件夹路径
            template: 提示词模板内容
            extensions: 文件扩展名列表
            force: 强制重新处理（忽略缓存）
            concurrency: 并发数
        """
        # 扫描文件
        scanner = FileScanner()
        files = scanner.scan_directory(input_folder, extensions)

        if not files:
            logger.warning("未扫描到任何文件")
            return

        # 过滤已处理的文件
        if not force:
            files = self.cache.get_unprocessed_files(files, output_folder)
        else:
            logger.info("强制模式：处理所有文件")

        if not files:
            logger.info("没有需要处理的文件")
            return

        logger.info(f"开始处理 {len(files)} 个文件（并发数: {concurrency}）")

        # 创建输出文件夹
        os.makedirs(output_folder, exist_ok=True)

        # 并发处理文件
        semaphore = asyncio.Semaphore(concurrency)

        async def process_with_semaphore(file_item):
            async with semaphore:
                await self._process_file(file_item, input_folder, output_folder, template)

        tasks = [process_with_semaphore(file_item) for file_item in files]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"文件处理完成")
