"""
翻译模块
使用 DeepSeek API 自动翻译英文内容为中文
"""

import asyncio
from typing import Optional

from openai import AsyncOpenAI
from langdetect import detect, LangDetectException

from src.utils import setup_logger
from src.config import config
from src.model_capabilities import ModelCapabilityManager

logger = setup_logger("translator")


class Translator:
    """DeepSeek 翻译器"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat"
    ):
        """
        初始化翻译器

        Args:
            api_key: DeepSeek API Key
            base_url: API 基础 URL
            model: 模型名称
        """
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

        # 模型能力自动探测
        if config.ENABLE_MODEL_AUTO_DETECTION:
            try:
                capability_mgr = ModelCapabilityManager()
                capability = asyncio.run(capability_mgr.get_or_detect(
                    model=model,
                    base_url=base_url,
                    client=self.client,
                    fallback_max_tokens=8000  # 翻译模块的默认值
                ))
                self.max_tokens = capability['max_output_tokens']
                logger.info(f"翻译器已初始化: 模型={model}, max_tokens={self.max_tokens}")
            except Exception as e:
                logger.warning(f"模型能力探测失败，使用默认值 8000: {e}")
                self.max_tokens = 8000
        else:
            self.max_tokens = 8000
            logger.info(f"翻译器已初始化: 模型={model}, max_tokens=8000")

    def detect_language(self, text: str) -> str:
        """
        检测文本语言

        Args:
            text: 待检测文本

        Returns:
            语言代码: 'en', 'zh', 'other', 'unknown'
        """
        if not text or len(text.strip()) < 10:
            return "unknown"

        try:
            lang = detect(text[:1000])  # 只检测前 1000 字符以提高速度

            # 简化语言分类
            if lang == 'en':
                return 'en'
            elif lang in ['zh-cn', 'zh-tw']:
                return 'zh'
            else:
                return 'other'

        except LangDetectException as e:
            logger.warning(f"语言检测失败: {e}")
            return "unknown"

    async def translate(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "zh",
        skip_detection: bool = False  # 新增参数:跳过语言检测
    ) -> str:
        """
        翻译文本

        Args:
            text: 待翻译文本
            source_lang: 源语言 (默认英文)
            target_lang: 目标语言 (默认中文)
            skip_detection: 是否跳过语言检测(默认False)

        Returns:
            翻译后的文本
        """
        if not text or not text.strip():
            return text

        # 检测语言 (除非明确跳过)
        if not skip_detection:
            detected_lang = self.detect_language(text)
            if detected_lang == target_lang:
                logger.info(f"内容已是目标语言({target_lang}),跳过翻译")
                return text

            if detected_lang == "unknown":
                logger.warning("无法检测语言,跳过翻译")
                return text

        # 构建提示词
        lang_names = {"en": "英文", "zh": "中文"}
        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)

        prompt = f"""请将以下{source_name}文本翻译成{target_name}:

{text}

要求:
1. 保持原文的 Markdown 格式(标题、列表、代码块等)
2. 专业术语保持准确
3. 语句通顺自然
4. 如果文本中包含 ---FIELD_SEPARATOR--- 分隔符,必须在翻译结果中保留该分隔符的完整位置
5. 仅返回翻译结果,不要添加额外说明"""

        # 调用 API
        try:
            logger.info(f"正在翻译: {len(text)} 字符...")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的翻译助手,擅长将英文技术文档翻译成中文。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 降低随机性,提高翻译稳定性
                max_tokens=self.max_tokens   # 使用探测到的 max_tokens
            )

            translated = response.choices[0].message.content.strip()

            logger.info(f"翻译成功: {len(text)} 字符 → {len(translated)} 字符")
            return translated

        except Exception as e:
            logger.error(f"翻译失败: {e}")
            return text  # 失败时返回原文

    async def translate_webpage(self, page) -> 'WebPage':
        """
        翻译网页对象

        Args:
            page: WebPage 对象

        Returns:
            翻译后的 WebPage 对象
        """
        # 1. 检测正文语言
        if not page.content:
            logger.info("网页内容为空,跳过翻译")
            return page

        content_lang = self.detect_language(page.content)

        if content_lang != "en":
            logger.info(f"内容非英文({content_lang}),跳过翻译")
            return page

        logger.info(f"检测到英文内容,开始翻译...")

        # 2. 收集需要翻译的字段
        translation_tasks = []

        if config.TRANSLATE_TITLE and page.title:
            translation_tasks.append(("title", page.title))

        if config.TRANSLATE_DESCRIPTION and page.description:
            translation_tasks.append(("description", page.description))

        if config.TRANSLATE_CONTENT and page.content:
            translation_tasks.append(("content", page.content))

        if config.TRANSLATE_METADATA and page.author:
            translation_tasks.append(("author", page.author))

        # 3. 批量翻译(一次API调用翻译所有字段)
        results = {}

        # 3.1 过滤需要翻译的字段
        fields_to_translate = []
        for field_name, text in translation_tasks:
            field_lang = self.detect_language(text)
            if field_lang == "unknown":
                logger.debug(f"[{field_name}] 无法检测语言,保留原文")
                results[field_name] = text
            elif field_lang != "en":
                logger.debug(f"[{field_name}] 内容非英文({field_lang}),保留原文")
                results[field_name] = text
            else:
                fields_to_translate.append((field_name, text))

        # 3.2 批量翻译所有字段(一次API调用)
        if fields_to_translate:
            try:
                # 构建批量翻译文本
                field_names = [name for name, _ in fields_to_translate]
                texts = [text for _, text in fields_to_translate]

                # 使用特殊分隔符组合多个字段
                combined_text = "\n\n---FIELD_SEPARATOR---\n\n".join(texts)
                total_chars = sum(len(t) for t in texts)

                logger.info(f"批量翻译 {len(fields_to_translate)} 个字段: {total_chars} 字符...")

                # 调用翻译API(一次调用)
                translated_combined = await self.translate(combined_text, skip_detection=True)

                # 分割翻译结果
                translated_parts = translated_combined.split("---FIELD_SEPARATOR---")

                # 映射回对应字段
                for i, field_name in enumerate(field_names):
                    if i < len(translated_parts):
                        results[field_name] = translated_parts[i].strip()
                    else:
                        logger.warning(f"[{field_name}] 翻译结果缺失,保留原文")
                        results[field_name] = texts[i]

                translated_chars = sum(len(results[name]) for name in field_names)
                logger.info(f"批量翻译成功: {total_chars} 字符 → {translated_chars} 字符")

            except Exception as e:
                logger.error(f"批量翻译失败,降级为逐个翻译: {e}")
                # 降级:逐个翻译
                for field_name, text in fields_to_translate:
                    try:
                        results[field_name] = await self.translate(text, skip_detection=True)
                    except Exception as inner_e:
                        logger.error(f"翻译 {field_name} 失败: {inner_e}")
                        results[field_name] = text

        # 4. 更新 WebPage 对象
        if "title" in results:
            # 清理标题中的 Markdown 格式符号,只保留第一行纯文本
            translated_title = results["title"]
            # 移除 Markdown 标题符号 (#)
            translated_title = translated_title.lstrip('#').strip()
            # 只取第一行作为标题
            translated_title = translated_title.split('\n')[0].strip()
            page.title = translated_title

        if "description" in results:
            page.description = results["description"]

        if "content" in results:
            page.content = results["content"]

        if "author" in results:
            page.author = results["author"]

        # 5. 标记已翻译
        page.translated = True
        page.original_language = "en"

        logger.info("网页翻译完成")
        return page
