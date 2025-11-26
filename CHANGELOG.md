# Changelog

All notable changes to Creeper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

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
