#!/usr/bin/env python3
"""
测试 Redis 本地持久化功能
"""

import sys
import json
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.dedup import DedupManager
from src.config import config

def test_dedup_persistence():
    """测试去重管理器的持久化功能"""
    print("=" * 60)
    print("测试 DedupManager 本地持久化功能")
    print("=" * 60)
    print()

    # 1. 测试初始化
    print("1. 初始化 DedupManager...")
    dedup = DedupManager()
    print(f"   ✓ 初始化成功")
    print(f"   - 缓存文件路径: {dedup.cache_file}")
    print()

    # 2. 测试标记 URL (双写)
    print("2. 测试标记 URL (Redis + 文件双写)...")
    test_urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3"
    ]

    for url in test_urls:
        success = dedup.mark_crawled(url)
        print(f"   - {url}: {'✓' if success else '✗'}")
    print()

    # 3. 检查文件是否创建
    print("3. 检查本地缓存文件...")
    if dedup.cache_file.exists():
        with open(dedup.cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        print(f"   ✓ 缓存文件已创建")
        print(f"   - 版本: {cache_data.get('version')}")
        print(f"   - 更新时间: {cache_data.get('updated_at')}")
        print(f"   - 记录数: {len(cache_data.get('data', {}))}")
    else:
        print(f"   ✗ 缓存文件不存在!")
    print()

    # 4. 测试 is_crawled
    print("4. 测试去重检查...")
    for url in test_urls:
        is_crawled = dedup.is_crawled(url)
        print(f"   - {url}: {'已爬取' if is_crawled else '未爬取'}")
    print()

    # 5. 测试统计信息
    print("5. 获取统计信息...")
    stats = dedup.get_stats()
    print(f"   - 总爬取数: {stats['total_crawled']}")
    print(f"   - Redis 连接: {'✓' if stats['redis_connected'] else '✗'}")
    print()

    # 6. 清空测试
    print("6. 测试清空功能...")
    dedup.clear_all()
    print(f"   ✓ 已清空 Redis 和本地文件")

    # 检查文件是否删除
    if not dedup.cache_file.exists():
        print(f"   ✓ 本地缓存文件已删除")
    else:
        print(f"   ✗ 本地缓存文件仍然存在")
    print()

    print("=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_dedup_persistence()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
