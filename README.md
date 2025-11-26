# Creeper 🕷️

> 一个简单实用的网页爬虫工具,将 Markdown 文件中的 URL 批量爬取并保存为结构化的本地 Markdown 文档。

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## ✨ 特性

- 🚀 **批量处理**: 从 Markdown 文件自动提取 URL 并批量爬取
- 🧠 **智能提取**: 使用 Trafilatura 精准提取文章核心内容,过滤广告
- 🎭 **动态渲染**: 自动降级到 Playwright 处理 JavaScript 渲染页面
- 🔄 **自动去重**: Redis 存储已爬取 URL,避免重复工作
- 📁 **结构化存储**: 按层级目录组织,生成标准 Markdown 文档
- 🛡️ **反爬虫策略**: 随机 User-Agent、请求间隔、重试机制
- 🎨 **友好界面**: 彩色日志、实时进度条、详细统计

## 📋 功能

- ✅ Markdown 文件解析(H1/H2 层级结构)
- ✅ 网页内容爬取(静态 + 动态)
- ✅ 内容清洗(过滤广告、保留核心)
- ✅ Redis 去重机制
- ✅ 目录结构自动生成
- ✅ 并发处理(可配置)
- ✅ 错误处理与重试
- ✅ 调试模式

## 🛠️ 技术栈

| 依赖 | 版本 | 用途 |
|------|------|------|
| Trafilatura | 1.12+ | 专业文章内容提取 |
| Playwright | 1.51+ | 动态网页渲染 |
| BeautifulSoup4 | 4.12+ | HTML 解析 |
| Redis | 6.4+ | 去重存储 |
| Requests | 2.31+ | HTTP 请求 |

## 📦 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd creeper
```

### 2. 创建 Python 虚拟环境

**使用虚拟环境可以避免污染全局 Python 环境**

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

激活后,终端提示符会显示 `(venv)` 前缀。

### 3. 安装依赖

```bash
# 升级 pip(推荐)
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器(仅需安装一次)
playwright install chromium
```

### 4. 配置环境变量

**前提**: Redis 已在全局安装并运行(本项目直接连接使用)

```bash
# 复制配置文件模板
cp .env.example .env

# 编辑配置文件(可选,默认配置已可用)
nano .env
```

## 🚀 快速开始

### 1. 准备输入文件

创建 `input.md` 文件:

```markdown
# 技术学习资料

## Python 教程
https://realpython.com/python-basics/
https://docs.python.org/3/tutorial/

## Web 开发
https://developer.mozilla.org/zh-CN/docs/Web
https://web.dev/learn/
```

### 2. 运行爬虫

```bash
# 基本使用
python creeper.py input.md

# 指定输出目录
python creeper.py input.md -o ./my-output

# 开启调试模式
python creeper.py input.md --debug

# 设置并发数
python creeper.py input.md --concurrency 10

# 强制重新爬取(跳过去重检查)
python creeper.py input.md --force
```

### 3. 查看输出

```
output/
├── 技术学习资料/
│   ├── Python 教程/
│   │   ├── Python Basics - Real Python.md
│   │   └── The Python Tutorial.md
│   └── Web 开发/
│       ├── MDN Web Docs.md
│       └── Learn Web Development.md
└── creeper.log
```

## 📖 输出文件格式

生成的 Markdown 文件包含完整信息:

```markdown
# Python Basics - Real Python

> 📅 **爬取时间**: 2025-11-26 10:30:45
> 🔗 **来源链接**: https://realpython.com/python-basics/
> 📝 **网页描述**: Learn Python basics with this comprehensive tutorial...

---

## 简介

Python is a versatile programming language...

## 核心内容

[文章主体内容...]

---

*本文由 Creeper 自动爬取并清洗*
```

## ⚙️ 配置说明

编辑 `.env` 文件自定义配置:

```bash
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# 爬虫配置
CONCURRENCY=5              # 并发数
REQUEST_TIMEOUT=30         # 请求超时(秒)
MIN_DELAY=1               # 最小请求间隔
MAX_DELAY=3               # 最大请求间隔
MAX_RETRIES=3             # 最大重试次数

# 调试模式
DEBUG=false
LOG_LEVEL=INFO
```

## 🔧 命令行参数

```bash
python creeper.py [输入文件] [选项]

必需参数:
  input_file              Markdown 输入文件路径

可选参数:
  -o, --output DIR        输出目录(默认: ./output)
  -c, --concurrency NUM   并发数(默认: 5)
  --force                 强制重新爬取(跳过去重)
  --debug                 开启调试模式
  --no-playwright         禁用 Playwright(仅静态爬取)
  -h, --help              显示帮助信息
```

## 📊 使用示例

### 示例 1: 爬取技术文档

```bash
# 输入文件: docs.md
# Python 3.13 文档
https://docs.python.org/3.13/whatsnew/3.13.html

# Rust 书籍
https://doc.rust-lang.org/book/

# 运行
python creeper.py docs.md -o ./tech-docs
```

### 示例 2: 批量爬取博客文章

```bash
# 输入文件: blogs.md
# 机器学习
https://machinelearningmastery.com/start-here/

# Web 开发
https://css-tricks.com/

# 运行(开启调试)
python creeper.py blogs.md --debug
```

## 🐛 常见问题

### Q1: Redis 连接失败

**错误**: `redis.exceptions.ConnectionError: Error connecting to Redis`

**解决**:
```bash
# 检查 Redis 是否运行
redis-cli ping  # 应返回 PONG

# 检查 .env 配置中的 Redis 连接信息是否正确
# REDIS_HOST, REDIS_PORT, REDIS_PASSWORD 等
```

### Q2: Playwright 浏览器未安装

**错误**: `playwright._impl._api_types.Error: Executable doesn't exist`

**解决**:
```bash
# 安装浏览器
playwright install chromium
```

### Q3: 部分网站爬取失败

**原因**: 反爬虫机制、网络问题、页面结构特殊

**解决**:
- 检查 `creeper.log` 查看详细错误
- 增加请求间隔: `MAX_DELAY=5`
- 使用 `--debug` 查看详细信息
- 手动访问失败的 URL 确认是否需要登录

### Q4: 如何退出虚拟环境?

```bash
# 退出虚拟环境
deactivate
```

### Q5: 如何删除虚拟环境?

```bash
# 退出虚拟环境
deactivate

# 删除虚拟环境目录
rm -rf venv
```

## 📝 开发计划

查看 [docs/requirements.md](docs/requirements.md) 了解完整需求和开发计划。

- ✅ **MVP (当前)**: 核心爬取功能
- 🔄 **V1.0 (计划)**: Cookie 管理、性能优化
- 📅 **V1.1 (未来)**: 代理池、图片下载、PDF 导出

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## ⚠️ 免责声明

- 本工具仅用于**个人学习和知识管理**,请勿用于商业目的
- 请**尊重网站 robots.txt**,不爬取明确禁止的内容
- 请**控制爬取频率**,避免对目标网站造成负担
- 使用本工具时请遵守相关法律法规

## 📄 许可证

MIT License

## 🔗 相关链接

- [需求文档](docs/requirements.md)
- [更新日志](CHANGELOG.md)
- [Trafilatura 文档](https://trafilatura.readthedocs.io/)
- [Playwright 文档](https://playwright.dev/python/)

---

**Happy Crawling!** 🕷️✨
