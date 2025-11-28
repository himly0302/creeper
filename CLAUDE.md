# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Creeper 是一个网页爬虫工具，从 Markdown 文件中提取 URL 并保存为结构化的本地 Markdown 文档。支持同步和异步两种爬取模式，基于 Redis 的去重机制，可选的内容翻译功能。V1.6 新增文件夹内容 LLM 整合功能，V1.7 新增图片本地化存储功能，V1.8 新增文件解析功能。

**当前版本**: v1.8.0

## 开发命令

### 环境配置
```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器（仅首次）
playwright install chromium
```

### 运行爬虫
```bash
# 异步模式（默认，推荐）
python creeper.py input.md

# 同步模式
python creeper.py input.md --sync

# 自定义并发数
python creeper.py input.md -c 10

# 调试模式
python creeper.py input.md --debug

# 强制重新爬取（跳过去重）
python creeper.py input.md --force

# 交互式登录（用于需要认证的网站）
python creeper.py --login-url https://example.com/login

# 启用图片下载
DOWNLOAD_IMAGES=true python creeper.py input.md
```

### 运行文件整合 (V1.6 新增)
```bash
# 代码总结
python3 aggregator.py --folder ./src --output ./docs/code_summary.md --template code_summary

# 文档合并
python3 aggregator.py --folder ./docs --output ./merged.md --template doc_merge --extensions .md,.txt

# 列出可用模板
python3 aggregator.py --list-templates

# 强制重新处理所有文件
python3 aggregator.py --folder ./src --output ./docs/code_summary.md --template code_summary --force
```

### 测试
```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_parser.py

# 运行文件整合功能测试
pytest tests/file_aggregator/
```

### 清理
```bash
# 清理所有爬取数据和 Redis 缓存
./clean.sh

# 手动清理
redis-cli -n 1 KEYS "creeper:*" | xargs redis-cli -n 1 DEL
rm -rf output/*
rm -f creeper.log
```

## 架构设计

### 核心组件

**1. 双模式执行**
- `creeper.py`: 统一的 CLI 入口
- `SyncCrawler`: 同步顺序处理
- `AsyncCrawler`: 异步并发处理（默认）
- 两者都继承自 `BaseCrawler` 基类

**2. 数据流水线**
```
Markdown 输入 → Parser → 去重检查 → Fetcher → Storage → Markdown 输出
                   ↓         ↓          ↓
                URLItem  Redis 缓存  WebPage
```

**3. 模块职责**

- `parser.py`: 从 Markdown 提取 H1/H2 层级结构和 URL，输出 `URLItem` 对象
- `dedup.py`: 基于 Redis 的去重，支持本地文件持久化（混合存储）
- `fetcher.py` / `async_fetcher.py`: 网页内容获取，使用 Trafilatura 提取
  - 静态页面: requests + BeautifulSoup
  - 动态页面: Playwright 处理 JS 渲染（自动降级）
- `storage.py`: 生成目录结构并保存 Markdown 文件
- `translator.py`: 可选的英文→中文翻译（DeepSeek API）
- `cookie_manager.py`: Cookie 管理（Redis 或文件存储），用于需要登录的网站
- `interactive_login.py`: 浏览器手动登录，自动提取 Cookie
- `image_downloader.py`: 图片下载器（同步和异步版本）
  - 从 Markdown 提取图片 URL
  - 下载图片到 `images/` 子目录
  - 替换 URL 为相对路径
  - 图片去重和安全验证（SSRF 防护）

### 关键设计模式

**混合存储 (v1.5)**
- 所有操作同时写入 Redis 和本地 JSON 文件（`data/dedup_cache.json`, `data/cookies_cache.json`）
- 启动时如果 Redis 为空，从本地文件恢复数据
- 防止 Redis 重启导致的数据丢失

**渐进式增强**
- Fetcher 先尝试静态请求，失败后降级到 Playwright 动态渲染
- 翻译功能仅对英文内容触发（langdetect 检测）
- Redis 失败不阻塞爬取（优雅降级）

**Cookie 管理**
- Redis 模式（默认）: 跨会话持久化，7 天过期
- 文件模式: JSON 存储，向后兼容
- 交互式登录: Playwright 打开浏览器，用户手动登录，Cookie 自动提取

## 配置管理

通过 `.env` 文件配置（从 `.env.example` 复制）:

**关键配置项**
- `CONCURRENCY`: 并发请求数（推荐 5-10）
- `ENABLE_LOCAL_PERSISTENCE`: Redis 备份到本地文件（默认: true）
- `ENABLE_TRANSLATION`: 自动翻译英文内容（默认: false，需要 DeepSeek API key）
- `COOKIE_STORAGE`: `redis`（默认）或 `file`
- `DOWNLOAD_IMAGES`: 启用图片下载（默认: false）（V1.7 新增）
- `MAX_IMAGE_SIZE_MB`: 最大图片大小限制（默认: 10 MB）（V1.7 新增）
- `IMAGE_DOWNLOAD_TIMEOUT`: 图片下载超时时间（默认: 30 秒）（V1.7 新增）
- `AGGREGATOR_*`: 文件整合功能配置（V1.6 新增）

## 项目结构约定

- `src/`: 所有源代码模块
- `tests/`: 所有测试文件（命名规范: `test_*.py`）
- `data/`: 本地持久化缓存文件
- `output/`: 生成的 Markdown 文件（镜像输入的 H1/H2 层级）
- `output/<H1>/<H2>/images/`: 下载的图片文件（如果启用图片下载）（V1.7 新增）
- `docs/`: 需求和设计文档
- `prompts/`: 提示词模板目录（用于文件夹内容整合功能，V1.6 新增）
- `docs/features/`: 功能需求文档（V1.6 新增）

## 重要实现细节

**URL 去重**
- URL 使用 MD5 哈希避免 Redis key 长度限制（`dedup.py:202`）
- 哈希 key 格式: `creeper:url:<md5>`，存储 URL、时间戳和状态元数据

**文件命名**
- 使用 `python-slugify` 生成安全文件名
- 最大长度 100 字符（`config.py:MAX_FILENAME_LENGTH`）

**翻译策略**
- 仅异步模式支持翻译
- 批量处理段落以减少 API 调用（减少 50% 调用，见 commit 3918a50）
- 翻译失败时回退到原始内容

**Redis 连接**
- 5 秒 socket 超时防止挂起
- 默认使用 DB 1（不是 DB 0）
- 连接失败记录日志但不崩溃

## 常见开发任务

**添加新的爬取策略**: 扩展 `WebFetcher` 或 `AsyncWebFetcher`，在 `fetch()` 方法实现降级逻辑

**添加新的存储格式**: 扩展 `StorageManager`，修改 `save()` 方法

**修改去重逻辑**: 编辑 `DedupManager`，确保 Redis 和文件操作都是原子性的

**添加翻译语言对**: 修改 `translator.py`，更新 langdetect 逻辑

**添加新的提示词模板** (V1.6 新增): 在 `prompts/` 创建 `.txt` 文件，通过 `--template` 参数使用
- 模板内容使用中文编写，清晰描述任务和输出要求
- 建议在模板中包含"如果提供了已有内容,请将新信息整合进去"的增量更新逻辑
- 文件名使用 snake_case 命名（如 `code_summary.txt`）

## Git 提交规范

```bash
# 新功能
git commit -m "feat: 添加XXX功能"

# Bug 修复
git commit -m "fix: 修复XXX问题"

# 重构
git commit -m "chore: 重构XXX模块"
```

## 环境依赖

- Python 3.8+
- Redis 服务运行在 localhost:6379（可配置）
- Chromium 浏览器（通过 `playwright install chromium` 安装）

## 已知限制

- 翻译功能仅在异步模式下可用
- 交互式登录需要 Playwright headless 模式
- Redis 数据持久化需要在项目外手动配置
- URL 最大长度受 MD5 哈希碰撞概率限制（实际使用中可忽略）
