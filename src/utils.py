"""
工具函数模块
提供文件名处理、日志配置等通用功能
"""

import re
import logging
import colorlog
from pathlib import Path
from datetime import datetime
from slugify import slugify
from typing import Optional

from .config import config


def setup_logger(name: str = "creeper", log_file: Optional[str] = None) -> logging.Logger:
    """
    配置彩色日志

    Args:
        name: 日志器名称
        log_file: 日志文件路径,如果为 None 则使用配置中的值

    Returns:
        配置好的 Logger 对象
    """
    logger = logging.getLogger(name)

    # 如果已经配置过,直接返回
    if logger.handlers:
        return logger

    # 设置日志级别
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # 控制台处理器(彩色输出)
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(log_level)

    # 彩色日志格式
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件处理器(普通格式)
    log_file_path = log_file or config.LOG_FILE
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别

    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


def sanitize_filename(filename: str, max_length: Optional[int] = None) -> str:
    """
    清理文件名,移除非法字符

    Args:
        filename: 原始文件名
        max_length: 最大长度,默认使用配置中的值

    Returns:
        清理后的安全文件名
    """
    if not filename:
        return "untitled"

    # 移除或替换非法字符
    # Windows 非法字符: < > : " / \ | ? *
    # 使用 slugify 处理,保留中文
    safe_name = slugify(filename, allow_unicode=True)

    # 如果 slugify 后为空(比如纯符号),使用时间戳
    if not safe_name:
        safe_name = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # 限制长度
    max_len = max_length or config.MAX_FILENAME_LENGTH
    if len(safe_name) > max_len:
        safe_name = safe_name[:max_len]

    return safe_name


def ensure_dir(path: str) -> Path:
    """
    确保目录存在,不存在则创建

    Args:
        path: 目录路径

    Returns:
        Path 对象
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def extract_domain(url: str) -> str:
    """
    从 URL 提取域名

    Args:
        url: 完整 URL

    Returns:
        域名字符串
    """
    pattern = r'https?://(?:www\.)?([^/]+)'
    match = re.search(pattern, url)
    return match.group(1) if match else "unknown"


def format_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        可读的大小字符串 (如 1.5 MB)
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断字符串

    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀

    Returns:
        截断后的字符串
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def get_timestamp() -> str:
    """
    获取当前时间戳字符串

    Returns:
        格式化的时间字符串
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def is_valid_url(url: str) -> bool:
    """
    检查 URL 是否有效

    Args:
        url: URL 字符串

    Returns:
        是否有效
    """
    pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
    return bool(re.match(pattern, url))
