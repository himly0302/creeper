#!/usr/bin/env python3
"""
测试 Redis 本地持久化 - 数据恢复功能
"""

import sys
import json
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.dedup import DedupManager
from src.config import config

def test_restore_from_file():
    """测试从文件恢复数据到 Redis"""
    print("=" * 60)
    print("测试数据恢复功能")
    print("=" * 60)
    print()

    # 1. 准备测试数据
    print("1. 准备测试数据...")
    dedup1 = DedupManager()

    test_urls = [
        "https://test.com/page1",
        "https://test.com/page2",
        "https://test.com/page3"
    ]

    for url in test_urls:
        dedup1.mark_crawled(url)
    print(f"   ✓ 已标记 {len(test_urls)} 个 URL")
    print()

    # 2. 验证数据已保存到文件
    print("2. 验证数据已保存到文件...")
    cache_file = Path(config.DEDUP_CACHE_FILE)
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        print(f"   ✓ 缓存文件存在")
        print(f"   - 记录数: {len(cache_data.get('data', {}))}")
    else:
        print(f"   ✗ 缓存文件不存在!")
        sys.exit(1)
    print()

    # 3. 清空 Redis (但保留文件)
    print("3. 清空 Redis (保留文件)...")
    import redis
    r = redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        password=config.REDIS_PASSWORD if config.REDIS_PASSWORD else None,
        decode_responses=True
    )
    pattern = f"{config.REDIS_KEY_PREFIX}url:*"
    keys = list(r.scan_iter(match=pattern, count=100))
    if keys:
        r.delete(*keys)
        print(f"   ✓ 已删除 {len(keys)} 个 Redis 键")
    print()

    # 4. 重新初始化 DedupManager (应该从文件恢复)
    print("4. 重新初始化 DedupManager (从文件恢复)...")
    dedup2 = DedupManager()
    print(f"   ✓ 初始化完成")
    print()

    # 5. 验证数据已恢复
    print("5. 验证数据已恢复...")
    for url in test_urls:
        is_crawled = dedup2.is_crawled(url)
        print(f"   - {url}: {'✓ 已恢复' if is_crawled else '✗ 未恢复'}")
    print()

    # 6. 检查统计信息
    print("6. 检查统计信息...")
    stats = dedup2.get_stats()
    print(f"   - Redis 中的记录数: {stats['total_crawled']}")
    print(f"   - Redis 连接: {'✓' if stats['redis_connected'] else '✗'}")
    print()

    # 7. 清理测试数据
    print("7. 清理测试数据...")
    dedup2.clear_all()
    print(f"   ✓ 测试数据已清理")
    print()

    print("=" * 60)
    print("✅ 数据恢复测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_restore_from_file()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
