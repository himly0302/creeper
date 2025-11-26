# Creeper 🕷️

> 一个简单实用的网页爬虫工具,将 Markdown 文件中的 URL 批量爬取并保存为结构化的本地 Markdown 文档。

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-1.1.0-green)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## ✨ 特性

- 🚀 **异步并发**: 支持多URL并发爬取,速度提升40-50%
- 🧠 **智能提取**: 使用 Trafilatura 精准提取文章核心内容,过滤广告
- 🎭 **动态渲染**: 自动降级到 Playwright 处理 JavaScript 渲染页面
- 🔄 **自动去重**: Redis 存储已爬取 URL,避免重复工作
- 🍪 **Cookie 管理**: 支持 Cookie 存储和复用,可爬取需要登录的网站
- 📁 **结构化存储**: 按层级目录组织,生成标准 Markdown 文档
- 🛡️ **反爬虫策略**: 随机 User-Agent、请求间隔、指数退避重试
- 🎨 **友好界面**: 彩色日志、实时进度条、详细统计

## 📋 功能

**V1.1 新增** 🍪
- ✅ Cookie 管理与持久化
- ✅ 支持需要登录的网站爬取
- ✅ 自动提取和保存 Cookie

**V1.0 新增** ⚡
- ✅ 异步并发处理(asyncio + aiohttp)
- ✅ 可配置并发数量
- ✅ 智能重试机制(指数退避)
- ✅ 性能提升 40-50%

**核心功能**
- ✅ Markdown 文件解析(H1/H2 层级结构)
- ✅ 网页内容爬取(静态 + 动态)
- ✅ 内容清洗(过滤广告、保留核心)
- ✅ Redis 去重机制
- ✅ 目录结构自动生成
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

**方式1: 使用 V1.0 异步版本(推荐)** ⚡

```bash
# 基本使用(默认并发数5)
python creeper_async.py input.md

# 自定义并发数(推荐 5-10)
python creeper_async.py input.md -c 10

# 指定输出目录
python creeper_async.py input.md -o ./my-output

# 开启调试模式
python creeper_async.py input.md --debug

# 强制重新爬取(跳过去重检查)
python creeper_async.py input.md --force

# 禁用 Playwright(仅静态爬取)
python creeper_async.py input.md --no-playwright
```

**方式2: 使用 MVP 同步版本(兼容)**

```bash
# 基本使用
python creeper.py input.md

# 其他参数与异步版本相同
python creeper.py input.md -o ./output --debug
```

**性能对比**:
- 异步版本(V1.0): 3个URL约16秒 ⚡
- 同步版本(MVP): 3个URL约28秒
- 性能提升: ~43%

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
  --cookies-file PATH     Cookie 存储文件路径(启用 Cookie 管理)
  --save-cookies          爬取结束后保存 Cookie
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

### 示例 3: 使用 Cookie 爬取需要登录的网站

```bash
# 第一次爬取,使用已有的 Cookie 文件
python creeper_async.py private.md --cookies-file ./cookies.json

# 爬取并保存 Cookie(用于下次复用)
python creeper_async.py private.md --cookies-file ./cookies.json --save-cookies

# 说明:
# 1. 首次使用需要手动创建 cookies.json 文件(可以从浏览器导出)
# 2. 程序会自动使用该 Cookie 访问网站
# 3. 使用 --save-cookies 会在爬取结束后保存新的 Cookie
# 4. Cookie 文件格式为 JSON,按域名分组存储
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

### Q6: 如何清空测试数据重新测试?

**使用清理脚本** (推荐):
```bash
# 运行清理脚本,会清空:
# - Redis 中的爬取记录
# - output/ 目录下的所有文件
# - creeper.log 日志文件
./clean.sh
```

**手动清理**:
```bash
# 清空 Redis
redis-cli -n 1 KEYS "creeper:*" | xargs redis-cli -n 1 DEL

# 删除输出文件
rm -rf output/*

# 删除日志
rm -f creeper.log
```

### Q7: 如何使用 Cookie 功能?

**场景**: 需要爬取需要登录的网站

**步骤**:

1. **手动获取 Cookie**(首次使用):
   - 在浏览器中登录目标网站
   - 打开开发者工具(F12) → Application → Cookies
   - 复制需要的 Cookie 信息

2. **创建 Cookie 文件** (cookies.json):
   ```json
   {
     "cookies": {
       "example.com": [
         {
           "name": "session_id",
           "value": "your_session_id_here",
           "domain": "example.com",
           "path": "/"
         }
       ]
     },
     "metadata": {
       "created_at": "2025-11-26T10:00:00",
       "format": "json",
       "version": "1.0"
     }
   }
   ```

3. **使用 Cookie 爬取**:
   ```bash
   python creeper_async.py input.md --cookies-file ./cookies.json --save-cookies
   ```

4. **自动保存更新的 Cookie**:
   - 使用 `--save-cookies` 参数会自动保存爬取过程中更新的 Cookie
   - 下次爬取时可以继续使用

**注意事项**:
- Cookie 文件包含敏感信息,请勿分享或上传到公开仓库
- 定期更新 Cookie 以保持登录态
- 建议将 cookies.json 添加到 .gitignore

## 📝 开发计划

查看 [docs/requirements.md](docs/requirements.md) 了解完整需求和开发计划。

- ✅ **MVP**: 核心爬取功能
- ✅ **V1.0**: 异步并发、性能优化
- ✅ **V1.1**: Cookie 管理
- 📅 **V1.2 (未来)**: 代理池、图片下载、PDF 导出

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
