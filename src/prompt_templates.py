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
        if name in self._templates_cache:
            return self._templates_cache[name]

        template_path = self.templates_dir / f"{name}.txt"

        if not template_path.exists():
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

    def list_templates(self) -> List[str]:
        if not self.templates_dir.exists():
            return []

        templates = []
        for file_path in self.templates_dir.glob("*.txt"):
            templates.append(file_path.stem)

        return sorted(templates)

    def reload_template(self, name: str) -> str:
        if name in self._templates_cache:
            del self._templates_cache[name]

        return self.get_template(name)

    def clear_cache(self):
        self._templates_cache.clear()
        logger.debug("Template cache cleared")
