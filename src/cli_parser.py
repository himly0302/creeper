"""
CLI 参数解析模块
统一管理同步和异步版本的命令行参数
"""

import argparse
from src.config import config


def create_argument_parser():
    """
    创建统一的参数解析器

    Returns:
        argparse.ArgumentParser: 配置好的参数解析器
    """
    parser = argparse.ArgumentParser(
        description='Creeper - 网页爬虫工具 (支持同步/异步模式)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s input.md                    # 异步模式(默认,推荐)
  %(prog)s input.md -c 10              # 设置并发数为 10
  %(prog)s input.md --sync             # 使用同步模式
  %(prog)s input.md -o ./output        # 指定输出目录
  %(prog)s input.md --debug            # 开启调试模式
  %(prog)s input.md --force            # 强制重新爬取
  %(prog)s input.md --no-playwright    # 禁用 Playwright
  %(prog)s --login-url URL             # 交互式登录
  %(prog)s --urls "URL1,URL2"          # URL列表模式，输出JSON

更多信息: https://github.com/your-repo/creeper
        """
    )

    # 输入文件 (可选,支持 --login-url 和 --urls 模式)
    parser.add_argument(
        'input_file',
        type=str,
        nargs='?',
        default=None,
        help='Markdown 输入文件路径'
    )

    # URL列表模式
    parser.add_argument(
        '--urls',
        type=str,
        default=None,
        help='直接输入URL列表，用逗号分隔。输出JSON格式数据到控制台'
    )

    # 提取图片链接
    parser.add_argument(
        '--with-images',
        action='store_true',
        help='提取页面中的图片链接(仅在 --urls 模式下生效)'
    )

    # 输出目录
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=config.OUTPUT_DIR,
        help=f'输出目录 (默认: {config.OUTPUT_DIR})'
    )

    # 并发数
    parser.add_argument(
        '-c', '--concurrency',
        type=int,
        default=config.CONCURRENCY,
        help=f'并发数 (默认: {config.CONCURRENCY}, 同步模式下忽略)'
    )

    # 强制重新爬取
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新爬取(跳过去重检查)'
    )

    # 调试模式
    parser.add_argument(
        '--debug',
        action='store_true',
        help='开启调试模式'
    )

    # 禁用 Playwright
    parser.add_argument(
        '--no-playwright',
        action='store_true',
        help='禁用 Playwright(仅使用静态爬取)'
    )

    # Cookie 文件路径
    parser.add_argument(
        '--cookies-file',
        type=str,
        default=None,
        help='Cookie 存储文件路径(启用 Cookie 管理)'
    )

    # 保存 Cookie
    parser.add_argument(
        '--save-cookies',
        action='store_true',
        help='爬取结束后保存 Cookie'
    )

    # 交互式登录 URL
    parser.add_argument(
        '--login-url',
        type=str,
        default=None,
        help='需要登录的 URL,启动交互式登录流程(仅异步模式)'
    )

    # 同步模式 (新增)
    parser.add_argument(
        '--sync',
        action='store_true',
        help='使用同步模式(默认: 异步模式)'
    )

    # 版本信息
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='Creeper 1.3.0'
    )

    return parser
