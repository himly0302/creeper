"""
配置管理模块
从 .env 文件加载配置
"""

import os
from typing import List
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    """全局配置类"""

    # Redis 配置
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 1))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    REDIS_KEY_PREFIX = os.getenv('REDIS_KEY_PREFIX', 'creeper:')

    # 爬虫配置
    CONCURRENCY = int(os.getenv('CONCURRENCY', 5))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    MIN_DELAY = float(os.getenv('MIN_DELAY', 1))
    MAX_DELAY = float(os.getenv('MAX_DELAY', 3))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    RETRY_BASE_DELAY = float(os.getenv('RETRY_BASE_DELAY', 2))

    # 浏览器配置
    BROWSER_TYPE = os.getenv('BROWSER_TYPE', 'chromium')
    BROWSER_HEADLESS = os.getenv('BROWSER_HEADLESS', 'true').lower() == 'true'
    PAGE_TIMEOUT = int(os.getenv('PAGE_TIMEOUT', 60000))

    # User-Agent 池
    USER_AGENTS = os.getenv(
        'USER_AGENTS',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36,'
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36,'
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    ).split(',')

    # 内容提取配置
    INCLUDE_COMMENTS = os.getenv('INCLUDE_COMMENTS', 'false').lower() == 'true'
    INCLUDE_TABLES = os.getenv('INCLUDE_TABLES', 'true').lower() == 'true'
    INCLUDE_IMAGES = os.getenv('INCLUDE_IMAGES', 'true').lower() == 'true'
    MIN_TEXT_LENGTH = int(os.getenv('MIN_TEXT_LENGTH', 100))

    # 输出配置
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './output')
    MAX_FILENAME_LENGTH = int(os.getenv('MAX_FILENAME_LENGTH', 100))
    SAVE_FAILED_URLS = os.getenv('SAVE_FAILED_URLS', 'true').lower() == 'true'

    # 图片下载配置
    DOWNLOAD_IMAGES = os.getenv('DOWNLOAD_IMAGES', 'false').lower() == 'true'
    MAX_IMAGE_SIZE_MB = int(os.getenv('MAX_IMAGE_SIZE_MB', 10))
    IMAGE_DOWNLOAD_TIMEOUT = int(os.getenv('IMAGE_DOWNLOAD_TIMEOUT', 30))
    SUPPORTED_IMAGE_FORMATS = os.getenv('SUPPORTED_IMAGE_FORMATS', '.jpg,.jpeg,.png,.gif,.webp,.svg')

    # Cookie 配置
    COOKIE_STORAGE = os.getenv('COOKIE_STORAGE', 'redis')  # 'file' 或 'redis'
    COOKIE_EXPIRE_DAYS = int(os.getenv('COOKIE_EXPIRE_DAYS', 7))  # Cookie 过期天数
    COOKIE_REDIS_KEY_PREFIX = os.getenv('COOKIE_REDIS_KEY_PREFIX', 'creeper:cookie:')
    INTERACTIVE_LOGIN_TIMEOUT = int(os.getenv('INTERACTIVE_LOGIN_TIMEOUT', 300))  # 交互式登录超时(秒)

    
    # 翻译配置 (使用 DEEPSEEK API)
    ENABLE_TRANSLATION = os.getenv('ENABLE_TRANSLATION', 'false').lower() == 'true'
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

    # 翻译范围
    TRANSLATE_TITLE = os.getenv('TRANSLATE_TITLE', 'true').lower() == 'true'
    TRANSLATE_DESCRIPTION = os.getenv('TRANSLATE_DESCRIPTION', 'true').lower() == 'true'
    TRANSLATE_CONTENT = os.getenv('TRANSLATE_CONTENT', 'true').lower() == 'true'
    TRANSLATE_METADATA = os.getenv('TRANSLATE_METADATA', 'false').lower() == 'true'

    # LLM 模型能力自动探测配置
    ENABLE_MODEL_AUTO_DETECTION = os.getenv('ENABLE_MODEL_AUTO_DETECTION', 'true').lower() == 'true'
    MODEL_DETECTION_TIMEOUT = int(os.getenv('MODEL_DETECTION_TIMEOUT', 10))
    MODEL_CAPABILITY_CACHE_FILE = os.getenv('MODEL_CAPABILITY_CACHE_FILE', 'data/model_capabilities.json')

    # 调试配置
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'creeper.log')

    @classmethod
    def get_redis_url(cls) -> str:
        """获取 Redis 连接 URL"""
        if cls.REDIS_PASSWORD:
            return f"redis://:{cls.REDIS_PASSWORD}@{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"

    @classmethod
    def display(cls):
        """显示当前配置(调试用)"""
        print("=== 当前配置 ===")
        print(f"Redis: {cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}")
        print(f"并发数: {cls.CONCURRENCY}")
        print(f"请求超时: {cls.REQUEST_TIMEOUT}s")
        print(f"请求间隔: {cls.MIN_DELAY}s - {cls.MAX_DELAY}s")
        print(f"最大重试: {cls.MAX_RETRIES}")
        print(f"输出目录: {cls.OUTPUT_DIR}")
        print(f"调试模式: {cls.DEBUG}")
        print(f"日志级别: {cls.LOG_LEVEL}")
        print("================")


# 创建全局配置实例
config = Config()
