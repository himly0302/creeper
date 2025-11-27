# Changelog

All notable changes to Creeper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.6.2] - 2025-11-27

### Fixed
- 🐛 **模块导入**: 修复 `src.file_aggregator` 模块缺失导致的 ModuleNotFoundError
  - 创建缺失的 `src/file_aggregator.py` 文件（包含 FileScanner, AggregatorCache, LLMAggregator）
  - 修复 `aggregator.py` 的命令行参数解析逻辑，使 `--list-templates` 可独立运行
  - 相关文件: `src/file_aggregator.py`, `aggregator.py`

## [1.6.1] - 2025-11-27

### Changed
- ⚙️ **配置分离**: 翻译功能和文件整合功能使用独立的 LLM API 配置
  - 翻译功能: `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`
  - 文件整合: `AGGREGATOR_API_KEY`, `AGGREGATOR_BASE_URL`, `AGGREGATOR_MODEL`
  - 两个功能可以使用不同的 API Key 或服务商
  - 相关文件: `src/config.py`, `.env.example`, `aggregator.py`

## [1.6.0] - 2025-11-27

### Added
- 🧩 **文件夹内容 LLM 整合**: 智能扫描文件夹并使用 LLM 整合内容
  - 递归扫描文件夹并读取文件内容
  - 支持增量更新(基于 Redis 缓存已处理文件)
  - 预设 3 种提示词模板(代码总结、文档合并、数据分析)
  - 自动调用 LLM API 生成整合文档
  - 支持自定义文件类型过滤(--extensions)
  - 混合持久化(Redis + 本地 JSON)
  - 新增配置: `AGGREGATOR_*` 系列配置项
  - 相关文件: `aggregator.py`, `src/file_aggregator.py`, `src/prompt_templates.py`
- 📚 **提示词模板系统**: 可扩展的 LLM 提示词管理
  - 支持 `prompts/` 目录下自定义 `.txt` 模板文件
  - 内置模板缓存机制
  - 通过 `--list-templates` 查看所有可用模板
- 🧪 **单元测试**: 新增文件扫描和模板管理测试
  - `tests/file_aggregator/test_file_scanner.py`
  - `tests/file_aggregator/test_aggregator_cache.py`

### Changed
- 📝 **文档更新**: 更新 README.md 添加文件整合功能使用说明
- ⚙️ **配置扩展**: .env.example 新增 AGGREGATOR_* 配置项
- 📂 **项目结构**: 新增 `prompts/` 和 `docs/features/` 目录

## [1.5.0] - 2025-11-27

### Added
- 💾 **本地持久化**: Redis 数据本地持久化功能 - 混合存储模式
  - 支持 Redis + 本地文件双写,确保数据不丢失
  - 每次操作同时写入 Redis 和 `data/dedup_cache.json`
  - 启动时自动从 JSON 文件恢复去重和 Cookie 数据
  - 支持定期同步 Redis 数据到本地 (可配置间隔)
  - 新增配置: `ENABLE_LOCAL_PERSISTENCE`, `DEDUP_CACHE_FILE`, `SYNC_INTERVAL_SECONDS`
  - 相关文件: `src/dedup.py`, `src/cookie_manager.py`, `src/config.py`
- 🧹 **清理脚本增强**: `clean.sh` 新增清理本地缓存文件功能
  - 自动删除 `data/dedup_cache.json` 和 `data/cookies_cache.json`

## [1.4.3] - 2025-11-26

### Fixed
- ⚡ **翻译性能优化**: 批量翻译减少API调用次数
  - 将多个字段(title/description/content)合并为一次LLM调用
  - 使用 `---FIELD_SEPARATOR---` 分隔符组合字段
  - API调用次数减少 50% (2-3次 → 1次)
  - 降低API成本,提升爬取速度
  - 失败时自动降级为逐个翻译
  - 相关文件: `src/translator.py:106-115`, `src/translator.py:180-234`
- 🐛 **依赖修复**: 安装 brotli 库解决 VS Code 文档爬取失败
  - 修复 "Can not decode content-encoding: brotli" 错误
  - 优化翻译日志,避免重复语言检测

## [1.4.2] - 2025-11-26

### Fixed
- 🐛 **日志可读性**: 异步并发时日志添加 URL 上下文标识
  - 使用 contextvars 实现异步上下文追踪
  - 自定义 logging.Filter 自动提取 URL 信息
  - 日志格式: `INFO [python] 开始爬取...`
  - 大幅提升并发日志的可读性和调试效率
  - 相关文件: `src/utils.py`, `src/async_fetcher.py`

## [1.4.1] - 2025-11-26

### Fixed
- 🐛 **文件名格式**: 修复翻译后文件名包含多余 Markdown 格式符号的问题
  - 清理翻译标题中的 `#` 符号和多余换行
  - 只使用第一行作为文件名
  - 文件名长度从 100+ 字符缩短至 20-30 字符
  - 相关文件: `src/translator.py:186-194`

## [1.4.0] - 2025-11-26

### Added
- 🌍 **内容自动翻译**: 支持将英文网页内容自动翻译为中文
  - 集成 DeepSeek API 实现高质量翻译
  - 使用 langdetect 自动检测语言,仅翻译英文内容
  - 支持翻译标题、摘要、正文和元数据
  - 可通过 `.env` 配置灵活控制翻译范围
  - 相关文件: `src/translator.py`
- 📋 新增翻译配置项:
  - `ENABLE_TRANSLATION`: 启用/禁用翻译功能
  - `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`: API 配置
  - `TRANSLATE_TITLE`, `TRANSLATE_DESCRIPTION`, `TRANSLATE_CONTENT`, `TRANSLATE_METADATA`: 选择性翻译

### Changed
- 🔧 `AsyncWebFetcher` 集成翻译器,爬取成功后自动翻译
- 📋 `WebPage` 数据类新增字段: `translated` (是否已翻译), `original_language` (原始语言)
- ⚙️ 翻译失败时保留原文,不影响爬取结果

### Technical
- 使用 OpenAI SDK 兼容 DeepSeek API
- 语言检测使用前 1000 字符,提高检测速度
- 翻译提示词优化,保持 Markdown 格式完整性
- 翻译参数: `temperature=0.3`, `max_tokens=8000`
- 翻译器仅在异步模式中可用(OpenAI SDK 为异步优先)

### Dependencies
- openai>=1.0.0 (兼容 DeepSeek API)
- langdetect>=1.0.9 (语言检测)
- tiktoken>=0.5.0 (Token 计数)

### Usage Example
```bash
# 1. 配置 .env 文件
ENABLE_TRANSLATION=true
DEEPSEEK_API_KEY=your-api-key-here

# 2. 运行爬虫(默认异步模式,自动翻译)
python creeper.py input.md

# 3. 英文内容将自动翻译为中文并保存
```

---

## [1.3.0] - 2025-11-26

### Changed
- 🔧 **代码重构**: 合并同步/异步 CLI 为统一入口
  - `creeper.py` 和 `creeper_async.py` 已合并为单一入口点 `creeper.py`
  - 默认使用异步模式,可通过 `--sync` 参数切换同步模式
  - 提取公共逻辑到基类,消除 220 行重复代码 (47.4%)
  - 统一参数解析和错误处理
  - 完全向后兼容,所有功能保留

### Added
- 📋 新增 CLI 参数: `--sync` 切换同步模式
- 🏗️ 新增基类: `BaseCrawler` 统一爬虫逻辑
- 🔧 新增模块: `src/cli_parser.py` 统一参数解析

### Deprecated
- ⚠️ `creeper_async.py` 已删除,功能已合并到 `creeper.py`
- **迁移**: `python creeper_async.py` → `python creeper.py`
- 异步模式仍是默认模式,无需修改参数

### Technical
- 相关文件: `src/base_crawler.py`, `src/cli_parser.py`, `creeper.py`
- 代码行数减少: ~200 行
- 重复代码消除: 47.4% → 0%
- 维护成本降低: bug 修复从 2 处变为 1 处

### Migration Guide
**命令行迁移** (必需):
```bash
# v1.2.0 及之前
python creeper_async.py input.md

# v1.3.0+ 迁移后
python creeper.py input.md  # 功能完全相同,默认异步模式
```

**新增功能**:
```bash
# 使用同步模式
python creeper.py input.md --sync
```

---

## [1.2.0] - 2025-11-26

### Added
- 🌐 **交互式登录功能**: 使用 Playwright 打开浏览器让用户手动登录
  - 支持 `--login-url` 参数启动交互式登录
  - 登录完成后自动提取并保存 Cookie
  - 相关文件: `src/interactive_login.py`
- 💾 **Cookie Redis 存储**: Cookie 存储到 Redis 替代文件存储
  - 使用 Redis Hash 结构存储,按域名分组
  - 支持设置过期时间(默认 7 天)
  - 跨会话复用 Cookie
  - 相关文件: `src/cookie_manager.py`
- 🔄 **自动 Cookie 管理**: 登录一次,后续爬取自动使用

### Changed
- 🔧 `CookieManager` 支持可选的存储后端 ('file' 或 'redis')
- 📋 新增 CLI 参数: `--login-url <URL>`
- ⚙️ 新增配置项: `COOKIE_STORAGE`, `COOKIE_EXPIRE_DAYS`, `COOKIE_REDIS_KEY_PREFIX`, `INTERACTIVE_LOGIN_TIMEOUT`
- 🔀 `input_file` 参数变为可选(使用 `--login-url` 时不需要)

### Technical
- Cookie 在 Redis 中使用 `creeper:cookie:{domain}` 作为 Key
- 使用 HSET/HGETALL 操作 Cookie 数据
- Playwright 以非 headless 模式打开,等待用户操作
- 支持超时控制(默认 5 分钟)
- Cookie 自动从 Redis 加载,无需手动指定文件

### Migration Guide
**向后兼容**: 原有的 `--cookies-file` 参数仍然有效,文件存储模式不受影响。

如需切换到 Redis 存储模式:
1. 在 `.env` 中设置 `COOKIE_STORAGE=redis`
2. 使用 `--login-url` 进行首次登录
3. 后续爬取自动使用 Redis 中的 Cookie

---

## [1.1.0] - 2025-11-26

### Added
- 🍪 **Cookie 管理功能**: 支持 Cookie 的存储、加载和复用
- 🔐 **登录态保持**: 可爬取需要登录的网站内容
- 💾 **Cookie 持久化**: 支持 JSON 格式存储 Cookie
- 🔄 **自动 Cookie 提取**: 从请求响应中自动提取并保存 Cookie
- 📝 **Cookie 统计**: 提供 Cookie 管理的详细统计信息

### Changed
- 🔧 `WebFetcher` 和 `AsyncWebFetcher` 现在支持 `cookie_manager` 参数
- 📋 新增 CLI 参数: `--cookies-file` 和 `--save-cookies`

### Technical
- 新增 `src/cookie_manager.py` Cookie 管理模块
- 支持与 requests 和 Playwright 的 Cookie 互转
- Cookie 按域名分组存储
- 支持 Cookie 的精确匹配和父域匹配

---

## [1.0.0] - 2025-11-26

### Added
- 🚀 **异步并发处理**: 使用 asyncio + aiohttp 实现高性能并发爬取
- 🔄 **智能重试机制**: 指数退避算法,失败后自动重试(最多3次)
- ⚡ **性能提升**: 相比 MVP 版本速度提升约 40-50%
- 📊 **详细统计信息**: 成功率、耗时统计等
- 🎯 **可配置并发数**: 通过 `-c` 参数灵活控制并发数量

### Changed
- 💡 优化日志输出格式
- ⚡ 使用异步 Playwright 提升动态渲染性能
- 🔧 改进错误处理和异常捕获

### Fixed
- 🐛 修复部分网站 Brotli 压缩解码问题(自动降级到 Playwright)
- 🐛 优化内存使用,避免大量并发时的资源占用

### Technical
- 新增 `creeper_async.py` 异步并发版本
- 新增 `src/async_fetcher.py` 异步爬取模块
- 保留 `creeper.py` 同步版本作为备份
- 使用信号量(Semaphore)控制并发数

### Performance
- 测试数据(3个URL, 并发数3):
  - MVP 同步版本: ~28秒
  - V1.0 异步版本: ~16秒
  - 性能提升: ~43%

---

## [0.1.0] - 2025-11-26

### Added
- ✨ Markdown 文件解析功能,支持 H1/H2 层级结构
- ✨ 网页内容爬取功能(Trafilatura 静态爬取)
- ✨ Playwright 动态渲染自动降级
- ✨ Redis 去重机制,避免重复爬取
- ✨ 按层级目录自动生成文件结构
- ✨ 内容清洗,移除不可见字符和多余空白
- ✨ 反爬虫策略:随机 User-Agent、请求间隔
- ✨ 彩色日志输出和进度条展示
- ✨ 命令行参数支持(--force, --debug, --no-playwright)
- ✨ 失败 URL 自动保存到日志文件
- ✨ Python 虚拟环境支持,避免污染全局环境
- ✨ 一键初始化脚本(setup.sh / setup.bat)
- ✨ 清理脚本(clean.sh)便于测试
- 📝 完整的 README 和需求文档
- 📝 配置文件模板(.env.example)

### Technical
- 使用 Trafilatura 1.12+ 进行专业内容提取
- 使用 Playwright 1.51+ 处理动态页面
- 使用 Redis 6.4+ 实现高效去重
- 使用 colorlog 实现彩色日志
- 使用 tqdm 显示进度条
- 模块化设计:parser, fetcher, dedup, cleaner, storage

### Known Limitations (MVP)
- 仅支持单线程顺序执行
- 暂不支持 Cookie 管理
- 暂不支持图片本地下载
- 暂不支持代理池

---

## 版本说明

- **1.0.0**: 稳定版本,支持异步并发,生产环境可用
- **0.1.0**: MVP 版本,核心功能已实现,适合轻量使用

## 贡献者

- [@Claude] - 初始版本开发 & V1.0 异步并发实现
