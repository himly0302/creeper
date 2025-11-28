# Creeper 🕷️

> 智能网页爬虫工具，支持 Markdown URL 批量爬取、LLM 内容整合、自动翻译等功能。

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-1.7.0-green)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## ✨ 核心特性

- 🚀 **异步并发爬取** - 支持多 URL 并发，速度提升 40-50%
- 📷 **图片本地化存储** - 自动下载网页中的图片到本地，生成离线可用的文档
- 🧩 **LLM 文件整合** - 智能扫描文件夹，使用 LLM 生成代码总结/文档合并
- 🌍 **智能翻译** - 自动识别英文内容并翻译为中文（DeepSeek API）
- 💾 **混合持久化** - Redis + 本地文件双写，数据安全可靠
- 🎭 **动态渲染** - 自动降级到 Playwright 处理 JavaScript 页面
- 🔄 **Redis 去重** - 避免重复爬取，支持增量更新
- 🌐 **交互式登录** - 一键打开浏览器手动登录，自动提取 Cookie
- 📁 **结构化存储** - 按 H1/H2 层级目录组织，生成标准 Markdown

## 🚀 快速开始

### 安装

```bash
# 1. 克隆项目
git clone <repository-url>
cd creeper

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt
playwright install chromium

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 配置 Redis、API Key 等（可选）
```

### 基础使用 - 网页爬虫

**1. 准备输入文件** (inputs/input.md):
```markdown
# 技术学习资料

## Python 教程
https://realpython.com/python-basics/
https://docs.python.org/3/tutorial/

## Web 开发
https://developer.mozilla.org/zh-CN/docs/Web
```

**2. 运行爬虫**:
```bash
# 异步模式（推荐）
python creeper.py inputs/input.md

# 同步模式
python creeper.py inputs/input.md --sync

# 自定义并发数
python creeper.py inputs/input.md -c 10

# 启用图片下载（将图片保存到本地）
DOWNLOAD_IMAGES=true python creeper.py inputs/input.md

# 启用翻译（需配置 DEEPSEEK_API_KEY）
python creeper.py inputs/input.md  # 在 .env 中设置 ENABLE_TRANSLATION=true
```

**3. 查看输出**:
生成的 Markdown 文档保存在 `output/` 目录（约定名称为 `outputs/`），按 H1/H2 层级组织。

### 文件整合使用 (V1.6 新功能)

扫描文件夹并使用 LLM 生成代码总结或文档合并：

```bash
# 1. 配置 API Key
# 在 .env 中设置 AGGREGATOR_API_KEY=sk-your-key-here

# 2. 查看可用模板
python3 aggregator.py --list-templates

# 3. 生成代码总结（输出到 aggregators/ 目录）
python3 aggregator.py \
  --folder ./src \
  --output ./aggregators/code_summary.md \
  --template code_summary

# 4. 合并文档
python3 aggregator.py \
  --folder ./docs \
  --output ./aggregators/merged.md \
  --template doc_merge \
  --extensions .md,.txt
```

支持增量更新：再次运行时，只处理新增或变更的文件。

## 📖 使用场景

### 场景 1: 爬取技术文档

```bash
# 1. 在 inputs/ 目录准备 URLs
cat > inputs/tech_docs.md << 'EOF'
# 前端框架文档
## React
https://react.dev/learn
https://react.dev/reference/react

## Vue
https://vuejs.org/guide/introduction.html
EOF

# 2. 运行爬虫
python creeper.py inputs/tech_docs.md -c 5
```

输出结构（默认在 `output/` 目录）：
```
output/
└── 前端框架文档/
    ├── React/
    │   ├── Learn_React.md
    │   └── Reference.md
    └── Vue/
        └── Introduction.md
```

### 场景 2: 需要登录的网站

```bash
# 1. 交互式登录
python creeper.py --login-url https://example.com/login
# → 浏览器自动打开，手动登录后关闭窗口

# 2. 使用保存的 Cookie 爬取
python creeper.py inputs/input.md
# Cookie 自动从 Redis 加载，7 天内有效
```

### 场景 3: 代码库文档生成

```bash
# 1. 扫描 src 目录，生成代码总结（存储到 aggregators/ 目录）
python3 aggregator.py \
  --folder ./src \
  --output ./aggregators/architecture.md \
  --template code_summary

# 2. 增量更新：添加新文件后再次运行
touch src/new_module.py
python3 aggregator.py \
  --folder ./src \
  --output ./aggregators/architecture.md \
  --template code_summary
# → 只处理 new_module.py，并更新文档
```

### 场景 4: 批量解析文件 (V1.8 新增)

```bash
# 1. 解析文档文件夹（存储到 parsers/ 目录）
python parser.py \
  --input-folder ./inputs/编程/ \
  --output-folder ./parsers/编程分析/ \
  --template parser/practical_parser

# 2. 解析代码文件
python parser.py \
  --input-folder ./src \
  --output-folder ./parsers/代码分析/ \
  --template parser/code_parser \
  --extensions .py
```

## 📁 项目目录约定

### 核心输出目录

- **`inputs/`**: 爬虫输入文档地址文件夹
  - 存放包含 URL 列表的 Markdown 文件
  - 可按题材分类组织（如 `inputs/国际/`, `inputs/编程/`）

- **`outputs/`**: 爬虫输出文档地址文件夹
  - 存放 `creeper.py` 爬取后生成的 Markdown 文件
  - 按 H1/H2 层级自动组织
  - 图片存储在子目录 `images/`

- **`parsers/`**: 解析文档存放文件夹
  - 存放 `parser.py` 生成的文档
  - 每个文件独立解析，一对一输出

- **`aggregators/`**: 融合文档存放文件夹
  - 存放 `aggregator.py` 生成的文档
  - 多个文件整合为单个输出

## ⚙️ 配置指南

编辑 `.env` 文件自定义配置（从 `.env.example` 复制）：

### Redis 配置
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1
REDIS_PASSWORD=          # 可选
```

### 翻译功能配置
```bash
ENABLE_TRANSLATION=false
DEEPSEEK_API_KEY=sk-your-translation-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 翻译范围
TRANSLATE_TITLE=true
TRANSLATE_CONTENT=true
```

### 图片下载配置
```bash
DOWNLOAD_IMAGES=false           # 启用/禁用图片下载（默认 false）
MAX_IMAGE_SIZE_MB=10            # 最大图片大小限制（MB，默认 10）
IMAGE_DOWNLOAD_TIMEOUT=30       # 图片下载超时时间（秒，默认 30）
```

**说明**：启用后，爬取的网页中的图片会被下载到 `output/<H1>/<H2>/images/` 目录，Markdown 中的图片链接会替换为本地相对路径。

### 文件整合配置 (独立 API)
```bash
AGGREGATOR_API_KEY=sk-your-aggregator-key-here
AGGREGATOR_BASE_URL=https://api.deepseek.com
AGGREGATOR_MODEL=deepseek-chat
AGGREGATOR_MAX_TOKENS=8000  # DeepSeek 限制: [1, 8192]
```

**注意**: 翻译和文件整合使用独立的 API 配置，可以使用不同的 Key 或服务商。

### LLM 模型能力自动探测 (V1.10 新增)
```bash
ENABLE_MODEL_AUTO_DETECTION=true  # 启用自动探测（默认: true）
MODEL_DETECTION_TIMEOUT=10        # 探测超时时间（秒，默认: 10）
```

**说明**：启用后，首次调用 LLM 时会自动询问模型的 `max_input_tokens` 和 `max_output_tokens`，结果缓存到 Redis 和本地文件。探测失败时使用配置的 `AGGREGATOR_MAX_TOKENS` 作为回退值。

### Cookie 管理配置
```bash
COOKIE_STORAGE=redis     # 或 file（传统模式）
COOKIE_EXPIRE_DAYS=7     # Redis 模式过期天数
```

### 本地持久化配置
```bash
ENABLE_LOCAL_PERSISTENCE=true
DEDUP_CACHE_FILE=data/dedup_cache.json
SYNC_INTERVAL_SECONDS=300  # 定期同步间隔，0 = 禁用
```

## 🔧 命令行参数

### 爬虫工具 (creeper.py)
```bash
python creeper.py [输入文件] [选项]

选项:
  -c, --concurrency N    并发数（默认: 5）
  --sync                 使用同步模式
  --force                忽略去重，强制重新爬取
  --debug                调试模式
  --login-url URL        交互式登录
```

### 文件整合工具 (aggregator.py)
```bash
python3 aggregator.py --folder PATH --output FILE --template NAME [选项]

选项:
  --folder PATH          要扫描的文件夹
  --output FILE          输出文件路径
  --template NAME        模板名称（code_summary/doc_merge/data_analysis）
  --extensions EXTS      文件类型过滤（默认: .py,.md,.txt）
  --force                忽略缓存，重新处理所有文件
  --list-templates       列出所有可用模板
```

## 🐛 故障排查

### Q1: Redis 连接失败

**错误**: `ConnectionError: Error connecting to Redis`

**解决**:
```bash
# 检查 Redis 是否运行
redis-cli ping
# 应返回: PONG

# 如未安装 Redis
# macOS: brew install redis && brew services start redis
# Ubuntu: sudo apt install redis-server && sudo systemctl start redis

# 检查 .env 配置
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Q2: Playwright 浏览器未安装

**错误**: `playwright._impl._api_types.Error: Executable doesn't exist`

**解决**:
```bash
playwright install chromium
```

### Q3: API Key 未配置

**错误**: `未配置 AGGREGATOR_API_KEY`

**解决**:
```bash
# 编辑 .env 文件
AGGREGATOR_API_KEY=sk-your-key-here

# 或使用环境变量
export AGGREGATOR_API_KEY=sk-your-key-here
```

### Q4: 文件整合找不到模板

**错误**: `Template 'xxx' not found`

**解决**:
```bash
# 列出可用模板
python3 aggregator.py --list-templates

# 确保 prompts/ 目录下有对应的 .txt 文件
ls prompts/
# 应显示: code_summary.txt  doc_merge.txt  data_analysis.txt
```

### Q5: 清空测试数据

```bash
# 使用清理脚本
./clean.sh

# 或手动清理
redis-cli -n 1 KEYS "creeper:*" | xargs redis-cli -n 1 DEL
rm -rf output/* outputs/* parsers/* aggregators/* data/*.json
rm -f creeper.log
```

## 📚 进阶文档

- 📋 [CHANGELOG.md](CHANGELOG.md) - 版本历史和更新日志
- 🧑‍💻 [CLAUDE.md](CLAUDE.md) - 开发者指南和架构文档
- 📖 [需求文档](docs/features/) - 详细功能需求说明

## 🛠️ 技术栈

| 依赖 | 版本 | 用途 |
|------|------|------|
| Trafilatura | 1.12+ | 文章内容提取 |
| Playwright | 1.51+ | 动态网页渲染 |
| BeautifulSoup4 | 4.12+ | HTML 解析 |
| Redis | 6.4+ | 去重和缓存 |
| OpenAI | 1.0+ | LLM API 调用 |
| langdetect | 1.0+ | 语言检测 |

完整依赖列表见 [requirements.txt](requirements.txt)

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交代码：`git commit -m "feat: add your feature"`
4. 推送分支：`git push origin feature/your-feature`
5. 提交 Pull Request

**提交规范**:
- `feat:` 新功能
- `fix:` 修复 Bug
- `docs:` 文档更新
- `refactor:` 代码重构

详细开发指南见 [CLAUDE.md](CLAUDE.md)

## ⚠️ 免责声明

本工具仅供学习和研究使用。使用时请遵守目标网站的 robots.txt 和服务条款，尊重网站的访问频率限制。对于因使用本工具而产生的任何法律问题，作者概不负责。

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

## 🔗 相关链接

- [GitHub Issues](https://github.com/your-repo/issues) - 问题反馈
- [DeepSeek API](https://platform.deepseek.com/) - 获取 API Key
- [Playwright 文档](https://playwright.dev/python/) - 浏览器自动化

---

**Star ⭐ 本项目** 如果觉得有帮助！
