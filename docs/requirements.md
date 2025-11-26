# Creeper 网页爬虫工具需求文档

> 📅 **生成时间**: 2025-11-26
> 🎯 **核心目标**: 将 Markdown 文件中的 URL 批量爬取并保存为结构化的本地 Markdown 文档
> ⏱️ **开发时间**: MVP 1-3天,V1.0 1周
> 🔧 **技术栈**: Python 3.8+ / Trafilatura / Playwright / Redis
> 💻 **硬件要求**: 无特殊要求,标准开发环境即可

---

## 1. 工具概述

### 解决的问题

将浏览器收藏夹、阅读清单中的 URL 批量下载为本地 Markdown 文档,方便离线阅读、全文搜索和知识管理。

### 使用场景

- **个人知识库构建**: 定期整理技术博客、文档网站,构建本地知识库
- **离线阅读**: 保存感兴趣的文章,随时随地阅读
- **内容归档**: 防止网页失效,保存重要内容
- **使用频率**: 每周/每月批量处理 50-100 个 URL

### 核心价值

- **节省时间**: 自动化批量爬取,相比手动复制粘贴节省 90% 时间
- **结构化存储**: 按层级目录组织,易于管理和检索
- **智能去重**: 自动跳过已爬取的 URL,避免重复工作
- **内容清洗**: 过滤广告和无关内容,只保留核心内容

### 成功标准

- ✅ 能够解析 Markdown 格式的输入文件,提取所有 URL
- ✅ 成功率 ≥ 85% (技术文档/博客类网站)
- ✅ 自动降级:静态爬取失败时切换到动态渲染
- ✅ 去重机制:已爬取的 URL 自动跳过
- ✅ 输出格式:包含标题、摘要、内容、时间、来源链接的 Markdown 文件

---

## 2. 功能与使用

### 功能列表(按优先级)

#### P0 必须功能

1. **Markdown 文件解析**
   - 输入: 包含 H1/H2 标题和 URL 的 Markdown 文件
   - 输出: 提取标题层级和 URL 列表

2. **网页内容爬取**
   - 静态爬取:使用 Trafilatura 快速提取主体内容
   - 动态渲染:Playwright 自动降级处理 JavaScript 渲染页面
   - 提取:网页标题、描述/摘要、主体内容、爬取网页的时间(如有)

3. **内容清洗**
   - 过滤广告、导航栏、页脚等无关内容
   - 保留文章核心内容、代码块、图片链接

4. **目录结构生成**
   - 按 H1/H2 层级创建文件夹
   - 文件名:网页标题(自动处理非法字符)

5. **去重机制**
   - 使用 Redis 存储已爬取的 URL
   - 爬取前检查,已存在则跳过

6. **错误处理**
   - 超时重试(最多 3 次)
   - 反爬虫检测:随机 User-Agent、请求间隔
   - 失败记录:保存失败的 URL 和错误原因到日志

#### P1 可选功能

1. **Cookie 管理**
   - 支持需要登录的网站
   - Cookie 持久化存储,下次自动使用

2. **并发控制**
   - 5-10 个并发请求(可配置)
   - 请求间隔:1-3 秒随机延迟

3. **进度展示**
   - 实时显示爬取进度
   - 成功/失败/跳过统计

4. **调试模式**
   - `--debug` 参数开启详细日志
   - 打印请求头、响应状态、提取内容预览

#### P2 未来功能

- 代理池支持(IP 轮换)
- 支持更多输入格式(JSON、CSV)
- 图片本地下载
- 支持导出为 PDF

---

### 使用方式

#### 环境准备

**⚠️ 重要: 使用 Python 虚拟环境,避免污染全局环境**

```bash
# 1. 创建虚拟环境(仅需执行一次)
python3 -m venv venv

# 2. 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 4. 安装 Playwright 浏览器
playwright install chromium

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 文件(可选,默认配置已可用)
```

**虚拟环境常用命令:**

```bash
# 退出虚拟环境
deactivate

# 删除虚拟环境(需先退出)
rm -rf venv

# 重新创建虚拟环境
python3 -m venv venv
```

#### 基本命令

```bash
# 注意: 以下命令需要在激活虚拟环境后执行

# 基本使用
python creeper.py input.md

# 指定输出目录
python creeper.py input.md -o ./output

# 开启调试模式
python creeper.py input.md --debug

# 设置并发数
python creeper.py input.md --concurrency 10

# 跳过 Redis 去重检查(强制重新爬取)
python creeper.py input.md --force
```

#### 输入文件格式

`input.md` 示例:

```markdown
# 技术学习资料

## Python 教程
https://realpython.com/python-basics/
https://docs.python.org/3/tutorial/

## Web 开发
https://developer.mozilla.org/zh-CN/docs/Web
https://web.dev/learn/
```

#### 输出目录结构

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

#### 输出文件格式

`Python Basics - Real Python.md` 示例:

```markdown
# Python Basics - Real Python

> 📅 **爬取时间**: 2025-11-26 10:30:45
> 🔗 **来源链接**: https://realpython.com/python-basics/
> 📝 **网页描述**: Learn Python basics with this comprehensive tutorial for beginners...

---

## 简介

Python is a versatile programming language...

## 核心内容

[文章主体内容...]

---

*本文由 Creeper 自动爬取并清洗*
```

---

### 配置文件

`.env` 配置示例:

```bash
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1
REDIS_PASSWORD=

# 爬虫配置
CONCURRENCY=5          # 并发数
REQUEST_TIMEOUT=30     # 请求超时(秒)
MIN_DELAY=1           # 最小请求间隔(秒)
MAX_DELAY=3           # 最大请求间隔(秒)
MAX_RETRIES=3         # 最大重试次数

# User-Agent 池(随机选择)
USER_AGENTS=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36,Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36

# 调试模式
DEBUG=false
```

---

## 3. 技术实现

### 技术栈(基于 Context7 调研)

#### 核心依赖

| 依赖 | 版本 | 用途 | 选择理由 |
|------|------|------|----------|
| **Trafilatura** | 1.12+ | 网页内容提取 | 专为文章提取设计,Benchmark Score 72.8,支持多语言,内置清洗功能 |
| **Playwright** | 1.51+ | 动态网页渲染 | 官方 Python 支持,Benchmark Score 95.2,支持 Chromium/Firefox/WebKit |
| **BeautifulSoup4** | 4.12+ | HTML 解析 | Benchmark Score 97.9,处理 Trafilatura 未覆盖的元数据提取 |
| **Redis-py** | 6.4+ | 去重存储 | 官方客户端,Benchmark Score 89.9,高性能 |
| **Requests** | 2.31+ | HTTP 请求 | Benchmark Score 84.7,简单可靠 |
| **python-dotenv** | 1.0+ | 环境变量管理 | 标准配置方案 |

#### 技术选型说明

**为什么选择 Trafilatura?**
- 专为新闻/博客内容提取设计,比通用爬虫更精准
- 内置广告过滤、样板内容检测
- 支持提取元数据(标题、作者、发布时间)
- 25379 个代码示例,文档完善

**为什么选择 Playwright 而非 Selenium?**
- 更快:无需 WebDriver,直接控制浏览器
- 更稳定:自动等待元素加载
- 更轻量:支持 headless 模式,资源占用小
- Python 官方支持,API 简洁

**反爬虫策略**
1. **请求头伪装**:随机 User-Agent、Referer
2. **请求间隔控制**:1-3 秒随机延迟
3. **失败重试**:指数退避算法 (1s → 2s → 4s)
4. **智能降级**:静态失败 → Playwright 动态渲染

---

### 项目结构

```
creeper/
├── README.md              # 快速开始、使用说明
├── CHANGELOG.md           # 版本更新记录
├── requirements.txt       # Python 依赖
├── .env.example           # 配置文件模板
├── .env                   # 实际配置(不提交 git)
├── .gitignore
├── creeper.py             # 主入口 + CLI 参数解析
├── src/
│   ├── __init__.py
│   ├── parser.py          # Markdown 文件解析
│   ├── fetcher.py         # 网页内容爬取(静态+动态)
│   ├── cleaner.py         # 内容清洗
│   ├── storage.py         # 文件保存 + 目录结构生成
│   ├── dedup.py           # Redis 去重逻辑
│   ├── config.py          # 配置加载
│   └── utils.py           # 工具函数(文件名处理、日志等)
├── tests/                 # 单元测试(V1.0)
│   ├── test_parser.py
│   ├── test_fetcher.py
│   └── test_cleaner.py
└── docs/
    ├── 简略需求点.md      # 原始需求
    └── requirements.md    # 本文档
```

---

### CHANGELOG.md 模板

```markdown
# Changelog

All notable changes to Creeper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.0.0] - YYYY-MM-DD
### Added
- P0 核心功能完整实现
- Cookie 管理支持
- 完善的错误处理和日志
- 详细的使用文档

### Changed
- 优化内容清洗算法
- 改进反爬虫策略

### Fixed
- 修复特殊字符文件名问题
- 修复 Playwright 超时处理

## [0.1.0] - YYYY-MM-DD
### Added
- 项目初始化
- Markdown 文件解析
- 基础爬取功能(Trafilatura)
- Redis 去重机制
- 简单目录结构生成
```

---

### 维护指南

**版本号规则**
- **0.1.0**: MVP 版本(核心功能可用)
- **1.0.0**: V1.0 稳定版(功能完善,生产可用)
- **1.1.0**: 新增 P1 功能
- **1.0.1**: Bug 修复

**更新 CHANGELOG 时机**
- MVP 完成后:记录 `[0.1.0]` 版本
- V1.0 完成后:记录 `[1.0.0]` 版本
- 每次发布新版本:更新对应版本号和日期

**分类说明**
- `Added`: 新增功能
- `Changed`: 功能优化/重构
- `Fixed`: Bug 修复
- `Deprecated`: 即将废弃的功能
- `Removed`: 已移除的功能

---

## 4. 开发计划

### MVP (1-3 天) - 能用

**目标**: 完成核心爬取流程,能够成功处理大部分技术文档/博客网站

#### 任务清单

- [ ] **项目初始化** (30 分钟)
  - 创建项目结构
  - 配置 `.env.example` 和 `.gitignore`
  - 编写基础 `README.md`
  - 创建 `CHANGELOG.md` v0.1.0

- [ ] **Markdown 解析** (1 小时)
  - 实现 `parser.py`:提取 H1/H2 和 URL
  - 处理多种 Markdown 格式变体

- [ ] **核心爬取功能** (4-6 小时)
  - 实现 `fetcher.py`:Trafilatura 静态爬取
  - 提取标题、描述、主体内容
  - 基础错误处理(超时、404)

- [ ] **Redis 去重** (1-2 小时)
  - 实现 `dedup.py`:连接 Redis,存储/查询 URL
  - 添加去重检查逻辑

- [ ] **文件保存** (2-3 小时)
  - 实现 `storage.py`:创建目录结构
  - 生成 Markdown 文件
  - 处理文件名非法字符

- [ ] **CLI 入口** (1 小时)
  - 实现 `creeper.py`:参数解析
  - 基础日志输出

- [ ] **简单测试** (1 小时)
  - 手动测试 5-10 个不同网站
  - 修复明显 Bug

**里程碑**: ✅ 第 1-3 天:MVP 完成,更新 CHANGELOG v0.1.0

---

### V1.0 (1 周) - 好用

**目标**: 功能完善,错误处理健壮,生产环境可用

#### 任务清单

- [ ] **Playwright 动态渲染** (1-2 天)
  - 集成 Playwright
  - 实现自动降级逻辑
  - 处理 headless 模式和超时

- [ ] **内容清洗优化** (1 天)
  - 实现 `cleaner.py`:高级清洗规则
  - 处理特殊网站(Medium、Dev.to 等)

- [ ] **反爬虫策略** (半天)
  - 随机 User-Agent 池
  - 请求间隔控制
  - 重试机制(指数退避)

- [ ] **配置文件支持** (半天)
  - 实现 `config.py`:加载 `.env`
  - 支持命令行参数覆盖

- [ ] **错误处理改进** (半天)
  - 友好的错误提示
  - 详细的失败日志
  - 生成失败 URL 列表

- [ ] **并发处理** (1 天)
  - 使用 `asyncio` + `aiohttp` 提升性能
  - 并发控制和任务队列

- [ ] **进度展示** (半天)
  - 实时进度条(`tqdm`)
  - 统计信息(成功/失败/跳过)

- [ ] **完善文档** (1 天)
  - 完善 `README.md`:安装、使用、FAQ
  - 更新 `CHANGELOG.md` v1.0.0
  - 添加示例输入/输出文件

- [ ] **代码优化** (1 天)
  - 代码审查和重构
  - 添加必要注释
  - 性能优化

**里程碑**: ✅ 第 7 天:V1.0 完成,更新 CHANGELOG v1.0.0

---

### 后续优化 (按需)

#### P1 功能
- [ ] Cookie 管理(支持需要登录的网站)
- [ ] 图片本地下载
- [ ] 支持更多输入格式(JSON、CSV)

#### P2 功能
- [ ] 代理池支持
- [ ] Web UI 界面
- [ ] 导出为 PDF
- [ ] Docker 容器化部署

#### 质量提升
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试(多种网站类型)
- [ ] 性能测试和优化
- [ ] CI/CD 自动化

---

### 时间评估

| 阶段 | 时间 | 成果 | 关键指标 |
|------|------|------|----------|
| **MVP** | 1-3 天 | 能用的基础版本 | 成功率 ≥ 70%,支持静态网站 |
| **V1.0** | 1 周 | 功能完善的稳定版本 | 成功率 ≥ 85%,支持动态网站 |
| **后续** | 按需 | 持续改进 | 根据实际使用反馈优化 |

---

## 5. 风险与注意事项

### 技术风险

1. **反爬虫机制**
   - 风险:某些网站可能检测并封禁爬虫
   - 对策:请求间隔、User-Agent 轮换、Playwright 模拟真实浏览器

2. **网页结构多样性**
   - 风险:不同网站结构差异大,提取准确率可能不理想
   - 对策:使用 Trafilatura(专为文章提取优化),BeautifulSoup 作为补充

3. **动态内容加载**
   - 风险:JavaScript 渲染的内容静态爬取无法获取
   - 对策:自动降级到 Playwright

### 法律与道德

- ⚠️ **仅用于个人学习和知识管理**,不得用于商业目的
- ⚠️ **尊重网站 robots.txt**,不爬取明确禁止的内容
- ⚠️ **控制爬取频率**,避免对目标网站造成负担

---

## 6. 常见问题 (FAQ)

### Q1: 为什么选择 Redis 而不是本地文件?
A: Redis 提供更快的查询速度(O(1)),适合大量 URL 去重。如果不想依赖 Redis,V1.1 可以考虑添加 SQLite 作为备选。

### Q2: 能否支持其他输入格式?
A: MVP 仅支持 Markdown,V1.1 可以考虑支持 JSON、CSV 等格式。

### Q3: 爬取失败怎么办?
A: 失败的 URL 会记录到 `creeper.log`,可以使用 `--force` 参数重新爬取。

### Q4: 能否下载图片?
A: MVP 仅保存图片链接,V1.1 可以添加图片下载功能。

---

## 7. 总结

Creeper 是一个**实用至上、快速开发、易于维护**的个人工具,专注于解决批量爬取和本地归档的核心需求。

**核心优势**:
- ✅ 自动化批量处理,节省 90% 时间
- ✅ 智能去重,避免重复工作
- ✅ 内容清洗,只保留核心内容
- ✅ 结构化存储,方便管理和检索

**开发计划**:
- 📅 **1-3 天**: MVP 完成,更新 CHANGELOG v0.1.0
- 📅 **1 周**: V1.0 完成,更新 CHANGELOG v1.0.0
- 📅 **按需**: 持续优化和功能扩展

**立即开始**: 按照开发计划,从 MVP 开始迭代! 🚀
