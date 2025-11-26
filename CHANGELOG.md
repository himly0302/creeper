# Changelog

All notable changes to Creeper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

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
- 📝 完整的 README 和需求文档
- 📝 配置文件模板(.env.example)

### Technical
- 使用 Trafilatura 1.12+ 进行专业内容提取
- 使用 Playwright 1.51+ 处理动态页面
- 使用 Redis 6.4+ 实现高效去重
- 使用 colorlog 实现彩色日志
- 使用 tqdm 显示进度条
- 模块化设计:parser, fetcher, dedup, cleaner, storage

### Known Limitations
- MVP 版本暂不支持并发处理(单线程顺序执行)
- 暂不支持 Cookie 管理
- 暂不支持图片本地下载
- 暂不支持代理池

---

## 版本说明

- **0.1.0**: MVP 版本,核心功能已实现,可用于个人日常使用
- 后续版本将添加并发处理、Cookie 管理等高级功能

## 贡献者

- [@Claude] - 初始版本开发
