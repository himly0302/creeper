# 文件夹内容 LLM 整合 - 需求文档

> 生成时间: 2025-11-27
> 基于项目: Creeper
> 技术栈: Python 3.8+ + AsyncIO + Redis + DeepSeek API

---

## 项目概况

**技术栈**: Python 3.8+ + aiohttp + redis + openai (DeepSeek 兼容) + python-dotenv
**架构模式**: 模块化 + 依赖注入 + 混合持久化 (Redis + 本地 JSON)
**代码风格**: snake_case 函数 / PascalCase 类 / 大写常量 / 优雅降级错误处理

---

## 改动点

### 要实现什么
- **文件夹扫描**: 递归读取指定文件夹所有文件内容，支持文件类型过滤
- **增量更新**: 通过 Redis 追踪已处理文件，仅处理新增文件
- **模板化提示词**: 预设多种整合策略（代码总结、文档合并、数据分析等）
- **LLM 整合**: 将文件内容 + 提示词发送给 LLM，生成整合后的内容
- **迭代合并**: 新文件内容与历史整合结果再次发给 LLM，增量更新输出文件

### 与现有功能的关系
- **依赖现有模块**:
  - `src/dedup.py` (DedupManager) - 用于追踪已处理文件的 Redis 去重逻辑
  - `src/translator.py` (Translator) - 复用 LLM API 调用模板（AsyncOpenAI + DeepSeek）
  - `src/config.py` (Config) - 扩展配置项（并发数、模板路径、LLM 参数）
  - `src/utils.py` - 复用日志、文件名处理、时间戳等工具函数
- **集成位置**: 独立 CLI 命令，不影响现有 `creeper.py` 爬虫功能

### 新增依赖 (无)
无需新增，复用现有依赖：`openai`, `redis`, `python-dotenv`, `aiohttp`

---

## 实现方案

### 需要修改的文件
```
src/config.py                    # 添加新配置项: LLM_AGGREGATOR_* 相关参数
.env.example                     # 添加配置示例
```

### 需要新增的文件
```
src/file_aggregator.py           # 核心: 文件扫描、增量检测、LLM 调用逻辑
src/prompt_templates.py          # 提示词模板管理（预设 + 自定义）
aggregator.py                    # CLI 入口（类似 creeper.py）
tests/file_aggregator/           # 测试文件统一存放
  ├── test_file_scanner.py       # 测试文件扫描逻辑
  ├── test_prompt_templates.py   # 测试模板加载
  └── test_aggregator.py         # 集成测试
data/aggregator_cache.json       # 文件夹映射缓存（自动生成）
prompts/                         # 提示词模板目录
  ├── code_summary.txt           # 代码总结模板
  ├── doc_merge.txt              # 文档合并模板
  └── data_analysis.txt          # 数据分析模板
```

**测试规范**：
- 所有测试相关文件统一保存在 `tests/` 目录中
- 按功能模块组织：`tests/file_aggregator/`

### 实现步骤

**步骤 1: 环境准备**
- [ ] 创建目录: `mkdir -p prompts tests/file_aggregator data`
- [ ] 创建空文件: `touch src/file_aggregator.py src/prompt_templates.py aggregator.py`

**步骤 2: 核心实现**
- [ ] **实现 `src/prompt_templates.py`**:
  - 类 `PromptTemplateManager`: 加载 prompts/ 下的模板文件
  - 方法 `get_template(name)`: 返回模板内容字符串
  - 方法 `list_templates()`: 列出所有可用模板
  - 预设 3 个模板文件 (code_summary, doc_merge, data_analysis)

- [ ] **实现 `src/file_aggregator.py`**:
  - **数据类 `FileItem`**: 存储文件路径、内容、修改时间、哈希值
  - **类 `FileScanner`**:
    - `scan_directory(path, extensions)`: 递归扫描文件夹
    - `filter_by_type(files, extensions)`: 按扩展名过滤
    - `compute_file_hash(path)`: 计算文件 MD5（用于变更检测）
  - **类 `AggregatorCache` (继承 DedupManager 设计模式)**:
    - Redis key 格式: `creeper:aggregator:<output_file_md5>:files`
    - 存储结构: `{folder_path, output_file, processed_files: {file_path: hash}}`
    - `get_new_files(folder, known_files)`: 返回新增/变更文件列表
    - `update_processed_files(output_file, files)`: 更新已处理文件记录
    - `restore_from_file_if_needed()`: 从 data/aggregator_cache.json 恢复
    - `_save_to_file()`: 同步到本地 JSON（混合持久化）
  - **类 `LLMAggregator` (复用 Translator 的 API 调用模式)**:
    - `__init__(api_key, base_url, model, max_tokens)`: 初始化 AsyncOpenAI 客户端
    - `aggregate(files, prompt_template, existing_content=None)`:
      - 组装消息: `[{system: 提示词}, {user: 文件内容列表}, {assistant: 已有内容}]`
      - 调用 LLM API
      - 返回整合后的文本
    - 错误处理: 记录日志 + 返回错误提示（不崩溃）

- [ ] **实现 `aggregator.py` CLI**:
  - 参数解析:
    - `--folder`: 文件夹路径（必需）
    - `--output`: 输出文件名（必需）
    - `--template`: 模板名称（必需，从 prompts/ 选择）
    - `--extensions`: 文件类型过滤（可选，默认 `.py,.md,.txt`）
    - `--force`: 忽略缓存，重新处理所有文件
    - `--debug`: 调试模式
  - 流程:
    1. 加载配置和 Redis 连接
    2. 扫描文件夹，获取文件列表
    3. 从 Redis 查询已处理文件
    4. 识别新增/变更文件
    5. 如有新文件 → 读取内容 + 加载模板 + 读取已有输出文件
    6. 调用 `LLMAggregator.aggregate()` 生成整合内容
    7. 保存到输出文件
    8. 更新 Redis 和本地 JSON 缓存

- [ ] **添加错误处理**:
  - 文件夹不存在 → 提示并退出
  - Redis 连接失败 → 警告 + 跳过缓存（仍可运行）
  - LLM API 调用失败 → 重试 3 次 + 回退到空响应
  - 输出文件写入失败 → 记录日志并抛出异常

**步骤 3: 集成到现有系统**
- [ ] **修改 `src/config.py`**:
  ```python
  # 新增配置项
  AGGREGATOR_CONCURRENCY = int(os.getenv('AGGREGATOR_CONCURRENCY', 1))
  AGGREGATOR_PROMPTS_DIR = os.getenv('AGGREGATOR_PROMPTS_DIR', 'prompts')
  AGGREGATOR_MAX_TOKENS = int(os.getenv('AGGREGATOR_MAX_TOKENS', 4000))
  AGGREGATOR_MODEL = os.getenv('AGGREGATOR_MODEL', 'deepseek-chat')
  ```
- [ ] **更新 `.env.example`**:
  ```bash
  # 文件夹内容整合功能
  AGGREGATOR_CONCURRENCY=1           # LLM 调用并发数（建议 1 避免限流）
  AGGREGATOR_PROMPTS_DIR=prompts     # 提示词模板目录
  AGGREGATOR_MAX_TOKENS=4000         # LLM 返回最大 token 数
  AGGREGATOR_MODEL=deepseek-chat     # LLM 模型名称
  ```
- [ ] **创建默认提示词模板** (`prompts/code_summary.txt`):
  ```
  你是代码分析专家。请阅读以下文件内容，生成一份简洁的代码总结文档。

  要求：
  1. 按模块分组，说明每个文件的核心功能
  2. 列出关键类/函数及其职责
  3. 总结技术栈和依赖关系
  4. 使用 Markdown 格式输出

  如果提供了已有总结内容，请将新文件的信息整合进去，保持结构一致。
  ```

**步骤 4: 测试**
- [ ] **单元测试** (`tests/file_aggregator/test_file_scanner.py`):
  - 测试文件夹扫描（包含子目录）
  - 测试文件类型过滤
  - 测试文件哈希计算
- [ ] **单元测试** (`tests/file_aggregator/test_prompt_templates.py`):
  - 测试模板加载
  - 测试不存在的模板 → 抛出异常
- [ ] **集成测试** (`tests/file_aggregator/test_aggregator.py`):
  - 模拟文件夹 + Redis + LLM Mock
  - 测试首次整合
  - 测试增量更新（新增文件）
  - 测试 `--force` 强制重新处理
- [ ] **手动测试**:
  ```bash
  # 测试代码总结
  python aggregator.py --folder src --output docs/code_summary.md --template code_summary

  # 测试增量更新（添加新文件后再次运行）
  touch src/new_module.py
  python aggregator.py --folder src --output docs/code_summary.md --template code_summary
  ```
- [ ] **回归测试现有功能** (必须!):
  - 运行 `pytest tests/`
  - 确保 `python creeper.py` 仍正常工作

**步骤 5: 文档更新**
- [ ] **更新 `README.md`**:
  - 在"功能特性"部分添加"文件夹内容 LLM 整合"
  - 添加使用示例（命令行）
  - 添加提示词模板说明
- [ ] **更新 `CHANGELOG.md`**:
  ```markdown
  ## [1.6.0] - 2025-11-27

  ### Added
  - **新功能**: 文件夹内容 LLM 整合
    - 递归扫描文件夹并读取文件内容
    - 支持增量更新（基于 Redis 缓存已处理文件）
    - 预设 3 种提示词模板（代码总结、文档合并、数据分析）
    - 自动调用 LLM 生成整合文档
    - 相关文件: `aggregator.py`, `src/file_aggregator.py`, `src/prompt_templates.py`
  ```
- [ ] **检查并更新 `CLAUDE.md`**:
  - 添加新模块说明: `file_aggregator.py`, `prompt_templates.py`
  - 更新"项目结构约定": 新增 `prompts/` 目录
  - 更新"常见开发任务": 添加"添加新的提示词模板"指南

**步骤 6: 提交代码**
- [ ] 检查 CLAUDE.md 是否需要更新（已在步骤 5 完成）
- [ ] `git add .`
- [ ] `git commit -m "feat: 文件夹内容 LLM 整合"`

---

## 使用方式

### 命令行
```bash
# 基本使用（首次整合）
python aggregator.py \
  --folder ./src \
  --output ./docs/code_summary.md \
  --template code_summary

# 增量更新（添加新文件后再次运行，自动检测新文件）
# 添加新文件
touch src/new_module.py
# 再次运行同样的命令，只处理新文件
python aggregator.py \
  --folder ./src \
  --output ./docs/code_summary.md \
  --template code_summary

# 指定文件类型过滤
python aggregator.py \
  --folder ./docs \
  --output ./docs/merged_docs.md \
  --template doc_merge \
  --extensions .md,.txt

# 强制重新处理所有文件（忽略缓存）
python aggregator.py \
  --folder ./data \
  --output ./analysis/report.md \
  --template data_analysis \
  --force

# 调试模式
python aggregator.py \
  --folder ./src \
  --output ./test.md \
  --template code_summary \
  --debug
```

### 提示词模板格式
在 `prompts/` 目录创建 `.txt` 文件：

```
你是{角色}。请{任务描述}。

要求：
1. {要求 1}
2. {要求 2}

如果提供了已有内容，请将新信息整合进去，保持{一致性要求}。
```

### 配置项
在 `.env` 中添加：
```bash
# LLM 整合功能配置
AGGREGATOR_CONCURRENCY=1           # 并发数（建议 1）
AGGREGATOR_PROMPTS_DIR=prompts     # 模板目录
AGGREGATOR_MAX_TOKENS=4000         # 最大 token 数
AGGREGATOR_MODEL=deepseek-chat     # 模型名称

# 复用现有配置
DEEPSEEK_API_KEY=sk-xxx            # DeepSeek API Key
REDIS_HOST=localhost               # Redis 地址
REDIS_PORT=6379                    # Redis 端口
REDIS_DB=1                         # Redis 数据库编号
ENABLE_LOCAL_PERSISTENCE=true      # 启用本地持久化
```

---

## 完成检查清单

**代码质量**:
- [ ] 遵循项目代码风格（snake_case, @dataclass, 优雅降级）
- [ ] 添加必要注释（复杂逻辑和公共 API）
- [ ] 错误处理完善（文件不存在、Redis 失败、LLM 超时）
- [ ] 无安全漏洞（文件路径遍历、命令注入）

**测试**:
- [ ] 新功能测试通过（单元测试 + 集成测试）
- [ ] 现有功能无影响（`pytest tests/` 全部通过）
- [ ] 边界条件处理（空文件夹、超大文件、网络超时）

**文档**:
- [ ] README 已更新（功能说明 + 使用示例）
- [ ] CHANGELOG 已更新（见下方指南）
- [ ] CLAUDE.md 已检查并更新（新模块 + 开发任务）
- [ ] 提示词模板文档已创建（prompts/*.txt）

---

## CHANGELOG.md 更新指南

**版本号规则**:
- 新增功能 (向后兼容) → MINOR (1.6.0)
- 破坏性变更 → MAJOR (2.0.0)
- 小改进/修复 → PATCH (1.5.1)

**更新位置**: 文件顶部添加新版本

**模板**:
```markdown
## [1.6.0] - 2025-11-27

### Added
- **新功能**: 文件夹内容 LLM 整合
  - 递归扫描文件夹并读取文件内容
  - 支持增量更新（基于 Redis 缓存已处理文件）
  - 预设 3 种提示词模板（代码总结、文档合并、数据分析）
  - 自动调用 LLM 生成整合文档
  - 相关文件: `aggregator.py`, `src/file_aggregator.py`, `src/prompt_templates.py`
  - 新增配置项: `AGGREGATOR_*` 系列环境变量
```

**CLAUDE.md 更新判断**:

**需要更新** (本次适用):
- ✅ 新增独立功能模块 (`file_aggregator.py`, `prompt_templates.py`)
- ✅ 新增目录约定 (`prompts/` 存放提示词模板)
- ✅ 扩展配置管理策略 (新增 `AGGREGATOR_*` 配置项)

**更新内容**:
```markdown
## 项目结构约定

- `src/`: 所有源代码模块
- `tests/`: 所有测试文件（命名规范: `test_*.py`）
- `data/`: 本地持久化缓存文件
- `output/`: 生成的 Markdown 文件（镜像输入的 H1/H2 层级）
- `docs/`: 需求和设计文档
- **`prompts/`**: 提示词模板目录（用于文件夹内容整合功能）

## 常见开发任务

...

**添加新的提示词模板**: 在 `prompts/` 创建 `.txt` 文件，通过 `--template` 参数使用
```

---

## 提交代码

在需求实现完成后，按以下顺序操作：

```bash
# 1. 检查是否需要更新 CLAUDE.md 文件（已在步骤 5 完成）

# 2. 添加所有修改的文件
git add .

# 3. 提交，commit 信息使用需求文档的标题
git commit -m "feat: 文件夹内容 LLM 整合"
```

注意：
- **先更新 CLAUDE.md 文件，再提交代码**
- commit 信息只包含需求文档的标题
- 使用 `feat:` 前缀表示这是新增功能
- 如更新了 CLAUDE.md，已在步骤 5 体现

---

## 注意事项

**技术风险**:
- LLM API 调用成本 → 使用 `max_tokens` 限制，建议从小文件夹测试
- Redis 数据膨胀 → 定期清理旧缓存（提供 `--clean-cache` 命令）
- 大文件夹性能 → 添加进度条（tqdm），限制单次最大文件数
- 文件内容过大 → 截断超长文件（如 > 100KB），记录警告日志

**兼容性**:
- 向后兼容 → 不影响现有 `creeper.py` 功能
- 需要迁移脚本 → 无
- 破坏现有 API → 无

**安全考虑**:
- 文件路径遍历 → 使用 `os.path.realpath()` 验证路径在目标文件夹内
- 敏感文件过滤 → 默认忽略 `.env`, `.git`, `__pycache__` 等
- API Key 泄露 → 确保 `.env` 在 `.gitignore` 中

---

## 实现优先级建议

**阶段 1: MVP (最小可行产品)**
- [ ] 文件扫描 + 模板加载 + LLM 调用
- [ ] 首次整合功能（无增量更新）
- [ ] 1 个提示词模板（code_summary）

**阶段 2: 增量更新**
- [ ] Redis 缓存已处理文件
- [ ] 增量检测 + 合并逻辑
- [ ] 本地 JSON 持久化

**阶段 3: 完善功能**
- [ ] 多种提示词模板（3 个）
- [ ] 文件类型过滤
- [ ] 完整测试覆盖

**阶段 4: 优化体验**
- [ ] 进度条显示
- [ ] 缓存清理命令
- [ ] 详细错误提示
