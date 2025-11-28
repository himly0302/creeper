#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件夹内容 LLM 整合 - 核心模块

功能:
- 文件扫描: 递归扫描文件夹获取文件内容
- 增量缓存: 基于 Redis 追踪已处理文件
- LLM 整合: 调用 LLM API 生成整合内容
"""

import asyncio
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from openai import AsyncOpenAI

from src.config import config
from src.model_capabilities import ModelCapabilityManager
from src.utils import setup_logger

logger = setup_logger(__name__)


@dataclass
class FileItem:
    """文件数据结构"""
    path: str
    content: str
    hash: str
    size: int


class FileScanner:
    """文件扫描器"""
    
    def __init__(self, max_file_size: int = None):
        """
        初始化文件扫描器
        
        Args:
            max_file_size: 最大文件大小(字节),超过则截断
        """
        self.max_file_size = max_file_size or config.AGGREGATOR_MAX_FILE_SIZE
        
    def scan_directory(self, folder_path: str, extensions: List[str]) -> List[FileItem]:
        """
        递归扫描文件夹
        
        Args:
            folder_path: 文件夹路径
            extensions: 文件扩展名列表(如 ['.py', '.md'])
            
        Returns:
            FileItem 列表
        """
        folder = Path(folder_path)
        if not folder.exists():
            logger.error(f"文件夹不存在: {folder_path}")
            return []
            
        files = []
        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'data'}
        ignore_files = {'.env', '.env.local', '.DS_Store'}
        
        for root, dirs, filenames in os.walk(folder_path):
            # 过滤忽略的目录
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for filename in filenames:
                # 过滤忽略的文件
                if filename in ignore_files:
                    continue
                    
                # 过滤扩展名
                if not any(filename.endswith(ext) for ext in extensions):
                    continue
                    
                file_path = os.path.join(root, filename)
                try:
                    file_item = self._read_file(file_path)
                    if file_item:
                        files.append(file_item)
                except Exception as e:
                    logger.warning(f"读取文件失败 {file_path}: {e}")
                    
        logger.info(f"扫描到 {len(files)} 个文件")
        return files
        
    def _read_file(self, file_path: str) -> Optional[FileItem]:
        """
        读取单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            FileItem 或 None
        """
        try:
            file_size = os.path.getsize(file_path)
            
            # 跳过空文件
            if file_size == 0:
                logger.debug(f"跳过空文件: {file_path}")
                return None
                
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if file_size > self.max_file_size:
                    logger.warning(f"文件过大({file_size} bytes),截断: {file_path}")
                    content = f.read(self.max_file_size)
                    content += f"\n\n[文件过大,已截断...]"
                else:
                    content = f.read()
                    
            # 计算文件哈希
            file_hash = self.compute_file_hash(file_path)
            
            return FileItem(
                path=file_path,
                content=content,
                hash=file_hash,
                size=file_size
            )
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return None
            
    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """
        计算文件 MD5 哈希
        
        Args:
            file_path: 文件路径
            
        Returns:
            MD5 哈希值
        """
        md5 = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败 {file_path}: {e}")
            return ""


class AggregatorCache:
    """文件聚合缓存管理器"""
    
    def __init__(self):
        """初始化缓存管理器"""
        try:
            import redis
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
            
        # 本地持久化文件
        self.cache_file = Path("data/aggregator_cache.json")
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 从文件恢复缓存
        self._restore_from_file_if_needed()
        
    def _restore_from_file_if_needed(self):
        """从本地文件恢复缓存到 Redis"""
        if not self.redis_available:
            return
            
        if not self.cache_file.exists():
            return
            
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            # 检查 Redis 是否为空
            keys = self.redis.keys("creeper:aggregator:*")
            if not keys:
                logger.info("从本地文件恢复缓存到 Redis...")
                for key, value in cache_data.items():
                    self.redis.set(key, json.dumps(value))
                logger.info(f"恢复了 {len(cache_data)} 条缓存记录")
        except Exception as e:
            logger.warning(f"从文件恢复缓存失败: {e}")
            
    def _save_to_file(self):
        """保存 Redis 缓存到本地文件"""
        if not self.redis_available:
            return
            
        try:
            cache_data = {}
            keys = self.redis.keys("creeper:aggregator:*")
            for key in keys:
                value = self.redis.get(key)
                if value:
                    cache_data[key.decode() if isinstance(key, bytes) else key] = json.loads(value)
                    
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"缓存已保存到文件: {len(cache_data)} 条记录")
        except Exception as e:
            logger.warning(f"保存缓存到文件失败: {e}")
            
    def _get_cache_key(self, output_file: str) -> str:
        """
        生成缓存 key
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            Redis key
        """
        file_hash = hashlib.md5(output_file.encode()).hexdigest()
        return f"creeper:aggregator:{file_hash}:files"
        
    def get_new_files(self, folder: str, current_files: List[FileItem], 
                      output_file: str) -> List[FileItem]:
        """
        获取新增或变更的文件
        
        Args:
            folder: 文件夹路径
            current_files: 当前扫描到的文件列表
            output_file: 输出文件路径
            
        Returns:
            需要处理的文件列表
        """
        if not self.redis_available:
            logger.warning("Redis 不可用,处理所有文件")
            return current_files
            
        cache_key = self._get_cache_key(output_file)
        
        try:
            # 获取已处理文件的哈希记录
            cached_data = self.redis.get(cache_key)
            if not cached_data:
                logger.info("首次处理,缓存为空")
                return current_files
                
            cache = json.loads(cached_data)
            processed_files = cache.get('processed_files', {})
            
            # 检测新增或变更的文件
            new_files = []
            for file_item in current_files:
                cached_hash = processed_files.get(file_item.path)
                if cached_hash != file_item.hash:
                    new_files.append(file_item)
                    
            logger.info(f"检测到 {len(new_files)} 个新增或变更的文件")
            return new_files
            
        except Exception as e:
            logger.warning(f"读取缓存失败: {e},处理所有文件")
            return current_files
            
    def update_processed_files(self, output_file: str, folder: str, 
                               files: List[FileItem]):
        """
        更新已处理文件记录
        
        Args:
            output_file: 输出文件路径
            folder: 文件夹路径
            files: 已处理的文件列表
        """
        if not self.redis_available:
            logger.warning("Redis 不可用,跳过缓存更新")
            return
            
        cache_key = self._get_cache_key(output_file)
        
        try:
            # 构建缓存数据
            processed_files = {file_item.path: file_item.hash for file_item in files}
            cache_data = {
                'folder': folder,
                'output_file': output_file,
                'processed_files': processed_files
            }
            
            # 保存到 Redis
            self.redis.set(cache_key, json.dumps(cache_data))
            logger.debug(f"缓存已更新: {len(processed_files)} 个文件")
            
            # 同步到本地文件
            self._save_to_file()
            
        except Exception as e:
            logger.warning(f"更新缓存失败: {e}")


class LLMAggregator:
    """LLM 文件整合器"""

    def __init__(self, api_key: str, base_url: str, model: str, max_tokens: int, temperature: float = 0.1):
        """
        初始化 LLM 整合器

        Args:
            api_key: API Key
            base_url: API Base URL
            model: 模型名称
            max_tokens: 最大 token 数（探测失败时的回退值）
            temperature: 生成温度 (默认 0.1,更严格遵循指令)
        """
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.fallback_max_tokens = max_tokens

        # 延迟探测：首次调用 aggregate 时进行
        self._max_tokens = None
        self._capability_detected = False

    @property
    def max_tokens(self) -> int:
        """获取 max_tokens（兼容旧代码）"""
        if self._max_tokens is None:
            return self.fallback_max_tokens
        return self._max_tokens

    async def _ensure_capability_detected(self):
        """确保模型能力已探测（懒加载）"""
        if self._capability_detected:
            return

        self._capability_detected = True

        if config.ENABLE_MODEL_AUTO_DETECTION:
            try:
                capability_mgr = ModelCapabilityManager()
                capability = await capability_mgr.get_or_detect(
                    model=self.model,
                    base_url=self.base_url,
                    client=self.client,
                    fallback_max_tokens=self.fallback_max_tokens
                )
                self._max_tokens = capability['max_output_tokens']
                logger.info(f"使用探测到的 max_tokens: {self._max_tokens}")
            except Exception as e:
                logger.warning(f"模型能力探测失败，使用配置值: {e}")
                self._max_tokens = self.fallback_max_tokens
        else:
            self._max_tokens = self.fallback_max_tokens
            logger.info(f"使用配置的 max_tokens: {self._max_tokens}")

    async def aggregate(self, files: List[FileItem], prompt_template: str,
                       existing_content: Optional[str] = None) -> str:
        """
        调用 LLM 整合文件内容

        Args:
            files: 文件列表
            prompt_template: 提示词模板
            existing_content: 已有输出内容(用于增量更新)

        Returns:
            整合后的内容
        """
        # 确保模型能力已探测
        await self._ensure_capability_detected()
        if not files:
            logger.warning("文件列表为空")
            return ""
            
        # 组装文件内容
        files_content = self._format_files(files)
        
        # 构建消息
        messages = [
            {"role": "system", "content": prompt_template},
            {"role": "user", "content": f"文件内容:\n\n{files_content}"}
        ]
        
        # 如果有已有内容,添加到消息中
        if existing_content:
            messages.append({
                "role": "assistant",
                "content": f"已有内容:\n\n{existing_content}"
            })
            messages.append({
                "role": "user",
                "content": "请将上述新文件的信息整合到已有内容中,保持结构一致。"
            })
            
        # 调用 LLM API
        try:
            logger.info(f"调用 LLM API (模型: {self.model})...")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            content = response.choices[0].message.content
            logger.info(f"LLM 返回内容长度: {len(content)} 字符")
            return content
            
        except Exception as e:
            logger.error(f"LLM API 调用失败: {e}")
            # 抛出异常而不是返回错误字符串
            raise RuntimeError(f"整合失败: {e}") from e
            
    def _format_files(self, files: List[FileItem]) -> str:
        """
        格式化文件内容为文本
        
        Args:
            files: 文件列表
            
        Returns:
            格式化后的文本
        """
        result = []
        for file_item in files:
            result.append(f"### 文件: {file_item.path}")
            result.append(f"大小: {file_item.size} bytes")
            result.append(f"\n```\n{file_item.content}\n```\n")
            
        return "\n".join(result)
