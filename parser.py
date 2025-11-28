#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件解析工具 - CLI 入口

功能:
- 递归扫描文件夹获取文件内容
- 独立调用 LLM 处理每个文件（一对一）
- 支持增量更新（基于 Redis 文件级缓存）
- 支持多种提示词模板
- 保持输入文件夹的相对路径结构

使用示例:
    python parser.py --input-folder ./src --output-folder ./output/parsed --template code_analysis
    python parser.py --input-folder ./docs --output-folder ./output/summaries --template doc_summary --extensions .md,.txt
"""

import argparse
import asyncio
import sys
from pathlib import Path

from src.config import config
from src.file_parser import FileParser
from src.prompt_templates import PromptTemplateManager
from src.utils import setup_logger

logger = setup_logger(__name__)


async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="文件解析工具 - 批量处理文件夹中的文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 代码分析（解析所有 Python 文件）
  python parser.py --input-folder ./src --output-folder ./output/parsed --template code_analysis

  # 文档总结（解析所有 Markdown 文件）
  python parser.py --input-folder ./docs --output-folder ./output/summaries --template doc_summary --extensions .md

  # 强制重新处理所有文件
  python parser.py --input-folder ./src --output-folder ./output/parsed --template code_analysis --force

  # 自定义并发数
  python parser.py --input-folder ./src --output-folder ./output/parsed --template code_analysis --concurrency 10

  # 调试模式
  python parser.py --input-folder ./src --output-folder ./output/parsed --template code_analysis --debug
        """
    )

    parser.add_argument(
        '--input-folder',
        help='输入文件夹路径'
    )
    parser.add_argument(
        '--output-folder',
        help='输出文件夹路径'
    )
    parser.add_argument(
        '--template',
        help='提示词模板名称（不含 .txt 后缀）'
    )
    parser.add_argument(
        '--extensions',
        default='.py,.md,.txt',
        help='文件扩展名过滤，逗号分隔（默认: .py,.md,.txt）'
    )
    parser.add_argument(
        '--concurrency',
        type=int,
        default=config.CONCURRENCY,
        help=f'并发处理文件数（默认: {config.CONCURRENCY}）'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='忽略缓存，重新处理所有文件'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='调试模式'
    )
    parser.add_argument(
        '--list-templates',
        action='store_true',
        help='列出所有可用的提示词模板'
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("调试模式已启用")

    # 列出模板
    if args.list_templates:
        template_mgr = PromptTemplateManager()
        templates = template_mgr.list_templates()
        if templates:
            print("\n可用的提示词模板:")
            for template in templates:
                print(f"  - {template}")
        else:
            print("\n未找到提示词模板，请在 prompts/ 目录创建 .txt 文件")
        sys.exit(0)

    # 验证必需参数
    if not args.input_folder or not args.output_folder or not args.template:
        parser.error("--input-folder, --output-folder 和 --template 是必需参数")

    # 验证输入文件夹路径
    input_folder = Path(args.input_folder)
    if not input_folder.exists():
        logger.error(f"输入文件夹不存在: {args.input_folder}")
        sys.exit(1)

    if not input_folder.is_dir():
        logger.error(f"不是有效的文件夹: {args.input_folder}")
        sys.exit(1)

    # 解析扩展名
    extensions = [ext.strip() if ext.startswith('.') else f'.{ext.strip()}'
                  for ext in args.extensions.split(',')]
    logger.info(f"文件类型过滤: {extensions}")

    # 检查 API 配置
    if not config.AGGREGATOR_API_KEY:
        logger.error("未配置 AGGREGATOR_API_KEY，请在 .env 文件中添加")
        sys.exit(1)

    # 验证并发数
    if args.concurrency < 1:
        logger.error("并发数必须大于 0")
        sys.exit(1)

    try:
        # 初始化组件
        logger.info("=" * 60)
        logger.info("文件解析工具")
        logger.info("=" * 60)

        template_mgr = PromptTemplateManager()
        file_parser = FileParser(
            api_key=config.AGGREGATOR_API_KEY,
            base_url=config.AGGREGATOR_BASE_URL,
            model=config.AGGREGATOR_MODEL,
            max_tokens=config.AGGREGATOR_MAX_TOKENS,
            temperature=config.AGGREGATOR_TEMPERATURE
        )

        # 加载提示词模板
        logger.info(f"加载提示词模板: {args.template}")
        try:
            prompt_template = template_mgr.get_template(args.template)
        except FileNotFoundError as e:
            logger.error(str(e))
            logger.info("\n提示: 使用 --list-templates 查看可用模板")
            sys.exit(1)

        # 解析文件夹
        logger.info(f"输入文件夹: {args.input_folder}")
        logger.info(f"输出文件夹: {args.output_folder}")
        logger.info(f"并发数: {args.concurrency}")

        await file_parser.parse_directory(
            input_folder=str(input_folder),
            output_folder=args.output_folder,
            template=prompt_template,
            extensions=extensions,
            force=args.force,
            concurrency=args.concurrency
        )

        logger.info("=" * 60)
        logger.info("✓ 完成!")
        logger.info(f"  输入文件夹: {args.input_folder}")
        logger.info(f"  输出文件夹: {args.output_folder}")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.warning("\n用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=args.debug)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
