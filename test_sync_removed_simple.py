#!/usr/bin/env python3
"""
简单验证同步版本已移除
不依赖外部模块，只检查文件内容
"""

import os
import sys

def test_files():
    """测试文件是否存在"""
    print("检查文件存在性...")

    # 不应该存在的文件
    should_not_exist = [
        'src/fetcher.py',  # 同步获取器
        'tests/image_downloader/test_sync_downloader.py',  # 同步测试
    ]

    for file_path in should_not_exist:
        if os.path.exists(file_path):
            print(f"❌ 文件应该被删除但仍然存在: {file_path}")
            return False
        else:
            print(f"✓ 文件已正确删除: {file_path}")

    # 应该存在的文件
    should_exist = [
        'src/async_fetcher.py',  # 异步获取器
        'src/image_downloader.py',  # 图片下载器（只有异步）
    ]

    for file_path in should_exist:
        if os.path.exists(file_path):
            print(f"✓ 文件存在: {file_path}")
        else:
            print(f"❌ 文件应该存在但不存在: {file_path}")
            return False

    return True

def test_file_contents():
    """测试文件内容"""
    print("\n检查文件内容...")

    # 检查 creeper.py
    with open('creeper.py', 'r', encoding='utf-8') as f:
        creeper_content = f.read()

    # 不应该包含的内容
    bad_patterns = [
        'SyncCrawler',
        '--sync',
        'if args.sync:',
        '同步模式 (--sync)',
        'from src.fetcher import',
    ]

    for pattern in bad_patterns:
        if pattern in creeper_content:
            print(f"❌ creeper.py 包含不应有的内容: {pattern}")
            return False
        else:
            print(f"✓ creeper.py 不包含: {pattern}")

    # 应该包含的内容
    good_patterns = [
        'AsyncCrawler',
        'asyncio.run',
        '异步模式 (默认)',
    ]

    for pattern in good_patterns:
        if pattern in creeper_content:
            print(f"✓ creeper.py 包含: {pattern}")
        else:
            print(f"❌ creeper.py 应该包含: {pattern}")
            return False

    # 检查 cli_parser.py
    with open('src/cli_parser.py', 'r', encoding='utf-8') as f:
        cli_content = f.read()

    if '--sync' in cli_content:
        print("❌ cli_parser.py 包含 --sync 参数")
        return False
    else:
        print("✓ cli_parser.py 不包含 --sync 参数")

    # 检查 image_downloader.py
    with open('src/image_downloader.py', 'r', encoding='utf-8') as f:
        img_content = f.read()

    if 'class ImageDownloader:' in img_content:
        print("❌ image_downloader.py 包含同步图片下载器类")
        return False
    else:
        print("✓ image_downloader.py 不包含同步图片下载器类")

    return True

def test_help_command():
    """测试帮助命令"""
    print("\n检查帮助命令...")

    import subprocess
    try:
        result = subprocess.run([sys.executable, 'creeper.py', '--help'],
                              capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            if '--sync' in result.stdout:
                print("❌ 帮助信息包含 --sync 参数")
                return False
            else:
                print("✓ 帮助信息不包含 --sync 参数")
        else:
            print(f"⚠️  帮助命令执行失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️  无法执行帮助命令: {e}")
        return False

    return True

def main():
    """主函数"""
    print("=" * 60)
    print("验证同步版本已移除")
    print("=" * 60)

    all_passed = True

    # 运行测试
    all_passed &= test_files()
    all_passed &= test_file_contents()
    all_passed &= test_help_command()

    # 输出结果
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有验证通过！同步版本已成功移除")
    else:
        print("❌ 部分验证失败，需要进一步检查")
    print("=" * 60)

    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)