# Creeper 🕷️

> 一个简单实用的网页爬虫工具,将 Markdown 文件中的 URL 批量爬取并保存为结构化的本地 Markdown 文档。

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-1.6.0-green)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## ✨ 特性

- 🚀 **异步并发**: 支持多URL并发爬取,速度提升40-50%
- 🧩 **文件整合**: LLM 智能整合文件夹内容,支持增量更新
- 🌍 **智能翻译**: 自动识别英文内容并翻译为中文(DeepSeek API)
- 💾 **本地持久化**: Redis + 文件混合存储,数据安全可靠
- 🧠 **智能提取**: 使用 Trafilatura 精准提取文章核心内容,过滤广告
- 🎭 **动态渲染**: 自动降级到 Playwright 处理 JavaScript 渲染页面
- 🔄 **自动去重**: Redis 存储已爬取 URL,避免重复工作
- 🌐 **交互式登录**: 一键打开浏览器手动登录,自动提取 Cookie 到 Redis
- 🍪 **智能 Cookie**: Redis 跨会话存储,登录一次后续自动使用
- 📁 **结构化存储**: 按层级目录组织,生成标准 Markdown 文档
- 🛡️ **反爬虫策略**: 随机 User-Agent、请求间隔、指数退避重试
- 🎨 **友好界面**: 彩色日志、实时进度条、详细统计

## 📋 功能

**V1.6 新增** 🧩
- ✅ 文件夹内容 LLM 整合
- ✅ 递归扫描文件夹并读取文件内容
- ✅ 支持增量更新(基于 Redis 缓存已处理文件)
- ✅ 预设 3 种提示词模板(代码总结、文档合并、数据分析)
- ✅ 自动调用 LLM 生成整合文档

**V1.5 新增** 💾
- ✅ Redis 本地持久化(混合存储模式)
- ✅ 启动时自动数据恢复
- ✅ 支持定期同步 Redis 到本地文件
- ✅ 数据安全,防止 Redis 重启丢失

**V1.4 新增** 🌍
- ✅ 内容自动翻译(英文→中文)
- ✅ 集成 DeepSeek API
- ✅ 智能语言检测,仅翻译英文内容
- ✅ 可配置翻译范围(标题/摘要/正文/元数据)

**V1.3 新增** 🔧
- ✅ 统一 CLI 入口(合并同步/异步模式)
- ✅ 通过 `--sync` 参数切换模式
- ✅ 代码重构(消除 47.4% 重复代码)

**V1.2 新增** 🌐
- ✅ 交互式登录(Playwright 浏览器手动登录)
- ✅ Cookie Redis 存储(跨会话复用)
- ✅ 自动 Cookie 管理(登录一次,后续自动使用)

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
| OpenAI | 1.0+ | DeepSeek API 兼容 |
| langdetect | 1.0+ | 语言检测 |

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

**基本使用(异步模式,默认推荐)** ⚡

```bash
# 基本使用(默认并发数5)
python creeper.py input.md

# 自定义并发数(推荐 5-10)
python creeper.py input.md -c 10

# 指定输出目录
python creeper.py input.md -o ./my-output

# 开启调试模式
python creeper.py input.md --debug

# 强制重新爬取(跳过去重检查)
python creeper.py input.md --force

# 禁用 Playwright(仅静态爬取)
python creeper.py input.md --no-playwright

# 交互式登录(首次登录网站)
python creeper.py --login-url https://example.com/login

# 使用已保存的 Cookie 爬取(自动从 Redis 加载)
python creeper.py input.md
```

**使用同步模式**

```bash
# 使用同步模式(顺序爬取)
python creeper.py input.md --sync

# 同步模式会自动忽略并发参数
python creeper.py input.md --sync -c 10  # -c 10 被忽略
```

**性能对比**:
- 异步模式(推荐): 3个URL约16秒 ⚡
- 同步模式: 3个URL约28秒
- 性能提升: ~43%

**迁移说明 (v1.3.0+)**:
- ✅ `creeper_async.py` 已合并到 `creeper.py`
- 旧命令: `python creeper_async.py input.md`
- 新命令: `python creeper.py input.md` (功能完全相同)
- 异步模式仍是默认模式,无需修改参数

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

# 本地持久化配置
ENABLE_LOCAL_PERSISTENCE=true       # 启用本地持久化(默认: true)
DEDUP_CACHE_FILE=data/dedup_cache.json    # 去重数据缓存路径
COOKIE_CACHE_FILE=data/cookies_cache.json # Cookie 缓存路径
SYNC_INTERVAL_SECONDS=300           # 定期同步间隔(秒, 0=禁用)

# 翻译配置 (可选)
ENABLE_TRANSLATION=false   # 启用翻译功能
DEEPSEEK_API_KEY=          # DeepSeek API Key (https://platform.deepseek.com/)
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 翻译范围 (选择性翻译)
TRANSLATE_TITLE=true       # 翻译标题
TRANSLATE_DESCRIPTION=true # 翻译摘要
TRANSLATE_CONTENT=true     # 翻译正文
TRANSLATE_METADATA=false   # 翻译元数据(作者等)

# 调试模式
DEBUG=false
LOG_LEVEL=INFO
```

### 本地持久化功能

从 **V1.5** 开始,Creeper 支持 Redis 数据的本地持久化,确保数据不会因 Redis 重启而丢失:

- **混合存储**: 每次操作同时写入 Redis 和本地文件
- **自动恢复**: 启动时自动从本地文件恢复数据到 Redis
- **数据安全**: Redis 故障时仍可从本地文件读取历史数据

**工作原理**:
1. 每次标记 URL 已爬取时,同时写入 Redis 和 `data/dedup_cache.json`
2. 启动时检查 Redis,如果为空则从本地文件恢复数据
3. 定期同步模式(可选): 按配置的间隔将 Redis 数据同步到文件

**配置项**:
- `ENABLE_LOCAL_PERSISTENCE`: 是否启用本地持久化(默认 `true`)
- `DEDUP_CACHE_FILE`: 去重数据缓存文件路径
- `COOKIE_CACHE_FILE`: Cookie 缓存文件路径(可选)
- `SYNC_INTERVAL_SECONDS`: 定期同步间隔(秒, 设为 `0` 禁用定期同步)

### 翻译功能使用说明

翻译功能可将英文网页内容自动翻译为中文(使用 DeepSeek API):

1. **获取 API Key**: 访问 [DeepSeek 平台](https://platform.deepseek.com/) 注册并获取 API Key
2. **配置 `.env`**: 设置 `ENABLE_TRANSLATION=true` 和 `DEEPSEEK_API_KEY`
3. **运行爬虫**: 使用异步模式 `python creeper.py input.md`
4. **自动翻译**:
   - 自动检测英文内容
   - 翻译完成后保存中文版本
   - 非英文内容保持原样
   - 翻译失败时保留原文

**注意**:
- 翻译功能仅在异步模式下可用(`python creeper.py`)
- 同步模式(`--sync`)不支持翻译
- 翻译大量内容可能需要较长时间,请耐心等待

## 🔧 命令行参数

```bash
python creeper_async.py [输入文件] [选项]

必需参数:
  input_file              Markdown 输入文件路径(使用 --login-url 时可选)

可选参数:
  -o, --output DIR        输出目录(默认: ./output)
  -c, --concurrency NUM   并发数(默认: 5)
  --force                 强制重新爬取(跳过去重)
  --debug                 开启调试模式
  --no-playwright         禁用 Playwright(仅静态爬取)
  --login-url URL         交互式登录 URL,打开浏览器让用户手动登录
  --cookies-file PATH     Cookie 存储文件路径(文件模式,向后兼容)
  --save-cookies          爬取结束后保存 Cookie(仅文件模式)
  -v, --version           显示版本信息
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

### 示例 3: 交互式登录并爬取需要登录的网站 (V1.2 新特性)

**推荐方式 - 使用 Redis 存储(自动管理)**:

```bash
# 步骤 1: 首次使用,进行交互式登录
python creeper_async.py --login-url https://example.com/login

# 操作说明:
# 1. 程序会自动打开浏览器窗口
# 2. 在浏览器中手动完成登录操作
# 3. 登录成功后,关闭浏览器窗口
# 4. Cookie 会自动保存到 Redis(默认过期时间: 7天)

# 步骤 2: 后续爬取,自动使用已保存的 Cookie
python creeper_async.py private.md -c 5

# 说明:
# - 程序会自动从 Redis 加载 Cookie
# - 无需再次登录
# - Cookie 会在 Redis 中保持 7 天(可在 .env 中配置)
# - 支持跨会话复用
```

**传统方式 - 使用文件存储(向后兼容)**:

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

### Q7: 如何使用交互式登录功能? (V1.2 新特性)

**场景**: 需要爬取需要登录的网站,使用 Redis 自动管理 Cookie

**步骤**:

1. **配置 Redis Cookie 存储**(推荐):
   - 编辑 `.env` 文件,确保 `COOKIE_STORAGE=redis`(默认已启用)
   - 配置 Cookie 过期时间: `COOKIE_EXPIRE_DAYS=7`(默认7天)

2. **首次交互式登录**:
   ```bash
   python creeper_async.py --login-url https://example.com/login
   ```
   - 程序会自动打开浏览器(最大化窗口)
   - 在浏览器中手动完成登录操作
   - 登录成功后,直接关闭浏览器窗口
   - Cookie 会自动提取并保存到 Redis

3. **后续爬取自动使用 Cookie**:
   ```bash
   python creeper_async.py input.md
   ```
   - 程序会自动从 Redis 加载之前保存的 Cookie
   - 无需再次登录,直接开始爬取

4. **查看 Redis 中保存的 Cookie**:
   ```bash
   # 查看所有 Cookie Key
   redis-cli -n 1 KEYS "creeper:cookie:*"

   # 查看特定域名的 Cookie
   redis-cli -n 1 HGETALL "creeper:cookie:example.com"

   # 删除特定域名的 Cookie
   redis-cli -n 1 DEL "creeper:cookie:example.com"
   ```

**优势**:
- ✅ 无需手动从浏览器导出 Cookie
- ✅ 自动跨会话复用,不用每次登录
- ✅ 支持多域名 Cookie 自动分组
- ✅ 自动过期管理(默认7天)
- ✅ 交互式登录超时保护(默认5分钟)

**注意事项**:
- 交互式登录需要 Playwright 浏览器支持
- 确保 Redis 服务正常运行
- Cookie 包含敏感信息,请妥善保管 Redis 数据
- 如需重新登录,可删除 Redis 中对应域名的 Cookie

### Q8: 如何使用 Cookie 文件模式(传统方式)?

**场景**: 不想使用 Redis,使用文件存储 Cookie(向后兼容)

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

**注意事项**:
- Cookie 文件包含敏感信息,请勿分享或上传到公开仓库
- 定期更新 Cookie 以保持登录态
- 建议将 cookies.json 添加到 .gitignore

### Q9: 如何使用文件夹内容 LLM 整合功能? (V1.6 新特性)

**场景**: 扫描文件夹中的文件,使用 LLM 智能整合内容,生成代码总结或文档合并

**步骤**:

1. **配置 LLM API Key**:
   - 编辑 `.env` 文件,添加 `AGGREGATOR_API_KEY=sk-your-key-here`
   - 也可配置 `AGGREGATOR_BASE_URL` 和 `AGGREGATOR_MODEL`
   - 注意: 文件整合功能使用独立的 API 配置,与翻译功能分离

2. **查看可用模板**:
   ```bash
   python3 aggregator.py --list-templates
   ```
   输出示例:
   ```
   可用的提示词模板:
     - code_summary       # 代码总结
     - data_analysis      # 数据分析
     - doc_merge          # 文档合并
   ```

3. **基本使用 - 代码总结**:
   ```bash
   python3 aggregator.py \
     --folder ./src \
     --output ./docs/code_summary.md \
     --template code_summary
   ```

4. **文档合并**:
   ```bash
   python3 aggregator.py \
     --folder ./docs \
     --output ./merged.md \
     --template doc_merge \
     --extensions .md,.txt
   ```

5. **增量更新** (自动检测新增文件):
   ```bash
   # 添加新文件后
   touch src/new_module.py

   # 再次运行相同命令,只处理新文件
   python3 aggregator.py \
     --folder ./src \
     --output ./docs/code_summary.md \
     --template code_summary
   ```

6. **强制重新处理所有文件**:
   ```bash
   python3 aggregator.py \
     --folder ./src \
     --output ./docs/code_summary.md \
     --template code_summary \
     --force
   ```

**高级用法**:

- **自定义文件类型过滤**:
  ```bash
  python3 aggregator.py \
    --folder ./config \
    --output ./config_summary.md \
    --template code_summary \
    --extensions .json,.yaml,.toml
  ```

- **创建自定义模板**:
  1. 在 `prompts/` 目录创建 `.txt` 文件
  2. 编写提示词内容(支持中文)
  3. 通过 `--template` 参数使用

**特性**:
- ✅ 自动增量更新(基于 Redis 缓存)
- ✅ 支持递归扫描子目录
- ✅ 智能过滤特定文件类型
- ✅ 混合持久化(Redis + 本地文件)
- ✅ 自动忽略 `.git`, `__pycache__` 等目录

**注意事项**:
- 大文件夹建议从小范围测试
- LLM 调用可能产生 API 费用
- 超大文件(>1MB)会被自动跳过

## 📂 项目结构

```
creeper/
├── README.md              # 项目说明文档
├── CHANGELOG.md           # 版本更新记录
├── requirements.txt       # Python 依赖列表
├── .env.example           # 环境变量配置模板
├── creeper.py             # 统一 CLI 入口(网页爬虫)
├── aggregator.py          # 文件整合 CLI 入口(V1.6 新增)
├── src/                   # 源代码目录
│   ├── parser.py          # Markdown 文件解析
│   ├── fetcher.py         # 网页内容爬取
│   ├── cleaner.py         # 内容清洗
│   ├── storage.py         # 文件保存与目录结构生成
│   ├── dedup.py           # Redis 去重逻辑
│   ├── file_aggregator.py # 文件扫描与 LLM 整合(V1.6 新增)
│   ├── prompt_templates.py # 提示词模板管理(V1.6 新增)
│   └── utils.py           # 工具函数
├── tests/                 # 测试文件目录（所有测试统一存放于此）
│   ├── test_parser.py
│   ├── test_fetcher.py
│   ├── test_utils.py
│   └── file_aggregator/   # 文件整合功能测试(V1.6 新增)
│       ├── test_file_scanner.py
│       └── test_aggregator_cache.py
├── data/                  # 数据缓存目录
│   ├── dedup_cache.json   # 去重数据缓存
│   ├── cookies_cache.json # Cookie 缓存
│   └── aggregator_cache.json # 文件整合缓存(V1.6 新增)
├── prompts/               # 提示词模板目录(V1.6 新增)
│   ├── code_summary.txt   # 代码总结模板
│   ├── doc_merge.txt      # 文档合并模板
│   └── data_analysis.txt  # 数据分析模板
└── docs/
    ├── requirements.md    # 详细需求文档
    └── features/          # 功能需求文档(V1.6 新增)
        └── 文件夹内容LLM整合.md
```

## 🧪 测试与开发规范

**测试规范**
- 所有测试文件统一保存在 `tests/` 目录中
- 测试文件命名格式：`test_*.py` 或 `*_test.py`

**运行测试**
```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/macOS

# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_parser.py
```

**提交代码规范**
```bash
# 新增功能
git commit -m "feat: 添加XXX功能"

# 错误修复
git commit -m "fix: 修复XXX问题"
```

## 📝 开发计划

查看 [docs/requirements.md](docs/requirements.md) 了解完整需求和开发计划。

- ✅ **MVP**: 核心爬取功能
- ✅ **V1.0**: 异步并发、性能优化
- ✅ **V1.1**: Cookie 管理
- ✅ **V1.2**: 交互式登录、Redis Cookie 存储
- 📅 **V1.3 (未来)**: 代理池、图片下载、PDF 导出

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
