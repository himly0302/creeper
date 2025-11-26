#!/usr/bin/env python3
"""
翻译功能测试脚本
用于验证英文网页自动翻译为中文的功能
"""

import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 临时启用翻译功能
os.environ['ENABLE_TRANSLATION'] = 'true'

from src.async_fetcher import AsyncWebFetcher
from src.cookie_manager import CookieManager
from src.config import config

async def test_translation():
    """测试翻译功能"""

    print("=" * 60)
    print("翻译功能测试")
    print("=" * 60)
    print()

    # 显示当前配置
    print("📋 当前配置:")
    print(f"  ├─ 翻译功能: {'✓ 已启用' if config.ENABLE_TRANSLATION else '✗ 未启用'}")
    print(f"  ├─ API 地址: {config.DEEPSEEK_BASE_URL}")
    print(f"  ├─ 模型: {config.DEEPSEEK_MODEL}")
    print(f"  ├─ API Key: {config.DEEPSEEK_API_KEY[:20]}..." if config.DEEPSEEK_API_KEY else "  ├─ API Key: 未配置")
    print(f"  ├─ 翻译标题: {'✓' if config.TRANSLATE_TITLE else '✗'}")
    print(f"  ├─ 翻译摘要: {'✓' if config.TRANSLATE_DESCRIPTION else '✗'}")
    print(f"  ├─ 翻译正文: {'✓' if config.TRANSLATE_CONTENT else '✗'}")
    print(f"  └─ 翻译元数据: {'✓' if config.TRANSLATE_METADATA else '✗'}")
    print()

    # 测试 URL (英文技术文章)
    test_url = "https://paulgraham.com/startupideas.html"

    print(f"🌐 测试 URL: {test_url}")
    print(f"📝 说明: Paul Graham 的英文技术博客文章")
    print()

    # 初始化爬取器
    print("🚀 初始化爬取器...")
    cookie_manager = CookieManager()
    fetcher = AsyncWebFetcher(
        use_playwright=True,
        concurrency=1,
        cookie_manager=cookie_manager
    )
    print()

    # 爬取网页
    print("📥 开始爬取...")
    print("-" * 60)
    page = await fetcher.fetch(test_url)
    print("-" * 60)
    print()

    # 显示结果
    if page.success:
        print("✅ 爬取成功!")
        print()
        print("📊 网页信息:")
        print(f"  ├─ 标题: {page.title[:80]}{'...' if len(page.title) > 80 else ''}")
        print(f"  ├─ 摘要: {page.description[:80] if page.description else '(无)'}{'...' if page.description and len(page.description) > 80 else ''}")
        print(f"  ├─ 正文长度: {len(page.content)} 字符")
        print(f"  ├─ 爬取方式: {page.method}")
        print(f"  ├─ 原始语言: {page.original_language}")
        print(f"  └─ 是否已翻译: {'✓ 是' if page.translated else '✗ 否'}")
        print()

        if page.translated:
            print("🎉 翻译成功!")
            print()
            print("📄 翻译后的标题:")
            print(f"  {page.title}")
            print()
            print("📄 翻译后的正文(前 500 字符):")
            print("-" * 60)
            print(page.content[:500])
            if len(page.content) > 500:
                print("...")
            print("-" * 60)
            print()
            print("✅ 测试通过!")
        else:
            print("⚠️  内容未被翻译")
            print("可能原因:")
            print("  - 内容非英文")
            print("  - 翻译功能未启用")
            print("  - API 调用失败")
    else:
        print(f"❌ 爬取失败: {page.error}")
        print()
        print("可能原因:")
        print("  - 网络连接问题")
        print("  - URL 无效或无法访问")
        print("  - 反爬虫限制")

    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_translation())
