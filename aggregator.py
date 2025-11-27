#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件夹内容 LLM 整合工具 - CLI 入口

功能:
- 递归扫描文件夹获取文件内容
- 使用 LLM 整合文件内容
- 支持增量更新(基于 Redis 缓存)
- 支持多种提示词模板

使用示例:
    python3 aggregator.py --folder ./src --output ./docs/summary.md --template code_summary
    python3 aggregator.py --folder ./docs --output ./merged.md --template doc_merge --extensions .md,.txt
"""

import argparse
import asyncio
import sys
from pathlib import Path

from src.config import config
from src.file_aggregator import FileScanner, AggregatorCache, LLMAggregator
from src.prompt_templates import PromptTemplateManager
from src.utils import setup_logger

logger = setup_logger(__name__)


async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="文件夹内容 LLM 整合工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 代码总结
  python3 aggregator.py --folder ./src --output ./docs/code_summary.md --template code_summary

  # 文档合并
  python3 aggregator.py --folder ./docs --output ./merged.md --template doc_merge --extensions .md,.txt

  # 数据分析
  python3 aggregator.py --folder ./data --output ./analysis.md --template data_analysis --force

  # 自定义文件类型
  python3 aggregator.py --folder ./config --output ./config_summary.md --template code_summary --extensions .json,.yaml,.toml
        """
    )

    parser.add_argument(
        '--folder',
        required=True,
        help='要扫描的文件夹路径'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='输出文件路径'
    )
    parser.add_argument(
        '--template',
        required=True,
        help='提示词模板名称(不含 .txt 后缀)'
    )
    parser.add_argument(
        '--extensions',
        default='.py,.md,.txt',
        help='文件扩展名过滤,逗号分隔(默认: .py,.md,.txt)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='忽略缓存,重新处理所有文件'
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
            print("\n未找到提示词模板,请在 prompts/ 目录创建 .txt 文件")
        sys.exit(0)

    # 验证文件夹路径
    folder_path = Path(args.folder)
    if not folder_path.exists():
        logger.error(f"文件夹不存在: {args.folder}")
        sys.exit(1)

    if not folder_path.is_dir():
        logger.error(f"不是有效的文件夹: {args.folder}")
        sys.exit(1)

    # 解析扩展名
    extensions = [ext.strip() if ext.startswith('.') else f'.{ext.strip()}'
                  for ext in args.extensions.split(',')]
    logger.info(f"文件类型过滤: {extensions}")

    # 检查 API 配置
    if not config.AGGREGATOR_API_KEY:
        logger.error("未配置 AGGREGATOR_API_KEY,请在 .env 文件中添加")
        sys.exit(1)

    try:
        # 初始化组件
        logger.info("=" * 60)
        logger.info("文件夹内容 LLM 整合工具")
        logger.info("=" * 60)

        template_mgr = PromptTemplateManager()
        file_scanner = FileScanner()
        cache_mgr = AggregatorCache()
        llm_aggregator = LLMAggregator(
            api_key=config.AGGREGATOR_API_KEY,
            base_url=config.AGGREGATOR_BASE_URL,
            model=config.AGGREGATOR_MODEL,
            max_tokens=config.AGGREGATOR_MAX_TOKENS
        )

        # 加载提示词模板
        logger.info(f"加载提示词模板: {args.template}")
        try:
            prompt_template = template_mgr.get_template(args.template)
        except FileNotFoundError as e:
            logger.error(str(e))
            sys.exit(1)

        # 扫描文件夹
        logger.info(f"扫描文件夹: {args.folder}")
        all_files = file_scanner.scan_directory(
            folder_path=str(folder_path),
            extensions=extensions
        )

        if not all_files:
            logger.warning("未找到任何文件")
            sys.exit(0)

        # 检查增量更新
        if args.force:
            logger.info("强制模式: 处理所有文件")
            files_to_process = all_files
        else:
            logger.info("检查增量更新...")
            files_to_process = cache_mgr.get_new_files(
                folder=str(folder_path),
                current_files=all_files,
                output_file=args.output
            )

        if not files_to_process:
            logger.info("没有新增或变更的文件,无需更新")
            sys.exit(0)

        # 读取已有输出文件
        output_path = Path(args.output)
        existing_content = None
        if output_path.exists() and not args.force:
            logger.info(f"读取已有输出文件: {args.output}")
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()

        # 调用 LLM 整合
        logger.info(f"调用 LLM 整合 {len(files_to_process)} 个文件...")
        aggregated_content = await llm_aggregator.aggregate(
            files=files_to_process,
            prompt_template=prompt_template,
            existing_content=existing_content
        )

        # 保存结果
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(aggregated_content)
        logger.info(f"结果已保存到: {args.output}")

        # 更新缓存
        logger.info("更新缓存...")
        cache_mgr.update_processed_files(
            output_file=args.output,
            folder=str(folder_path),
            files=all_files  # 记录所有文件,而不仅仅是新处理的
        )

        logger.info("=" * 60)
        logger.info("✓ 完成!")
        logger.info(f"  处理文件数: {len(files_to_process)}")
        logger.info(f"  输出文件: {args.output}")
        logger.info(f"  输出大小: {len(aggregated_content)} 字符")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.warning("\n用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=args.debug)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
