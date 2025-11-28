# -*- coding: utf-8 -*-
"""提示词模板管理器"""

import os
from pathlib import Path
from typing import Dict, List
from src.utils import setup_logger

logger = setup_logger(__name__)


class PromptTemplateManager:
    """提示词模板管理器"""

    def __init__(self, templates_dir: str = "prompts"):
        self.templates_dir = Path(templates_dir)
        self._templates_cache: Dict[str, str] = {}

        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created templates directory: {self.templates_dir}")

    def get_template(self, name: str) -> str:
        """
        获取提示词模板内容

        Args:
            name: 模板名称，支持以下格式：
                - 简化路径：'code_parser' (自动在子目录中搜索)
                - 完整路径：'parser/code_parser' (精确匹配)

        Returns:
            模板内容
        """
        if name in self._templates_cache:
            return self._templates_cache[name]

        # 尝试直接路径（支持子目录）
        template_path = self.templates_dir / f"{name}.txt"

        if not template_path.exists():
            # 如果直接路径不存在，尝试在子目录中搜索
            found_path = self._find_template_in_subdirs(name)
            if found_path:
                template_path = found_path
            else:
                available = self.list_templates()
                raise FileNotFoundError(
                    f"Template '{name}' not found. Available templates: {', '.join(available)}"
                )

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            self._templates_cache[name] = content
            logger.debug(f"Loaded template: {name} ({len(content)} chars)")

            return content
        except Exception as e:
            logger.error(f"Failed to read template {name}: {e}")
            raise

    def _find_template_in_subdirs(self, name: str) -> Path:
        """
        在子目录中搜索模板文件

        Args:
            name: 模板名称（不含扩展名）

        Returns:
            找到的模板路径，如果未找到返回 None
        """
        # 递归搜索所有子目录
        for file_path in self.templates_dir.rglob(f"{name}.txt"):
            logger.debug(f"Found template in subdirectory: {file_path}")
            return file_path

        return None

    def list_templates(self) -> List[str]:
        """
        列出所有可用的模板

        Returns:
            模板名称列表，格式为 'subdir/template_name' 或 'template_name'
        """
        if not self.templates_dir.exists():
            return []

        templates = []
        # 递归搜索所有 .txt 文件
        for file_path in self.templates_dir.rglob("*.txt"):
            # 获取相对路径（去除扩展名）
            rel_path = file_path.relative_to(self.templates_dir)
            template_name = str(rel_path.with_suffix(''))
            templates.append(template_name)

        return sorted(templates)

    def reload_template(self, name: str) -> str:
        if name in self._templates_cache:
            del self._templates_cache[name]

        return self.get_template(name)

    def clear_cache(self):
        self._templates_cache.clear()
        logger.debug("Template cache cleared")
