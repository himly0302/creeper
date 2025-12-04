# 删除文件夹内容 LLM 整合功能 - 需求文档

> 生成时间：2025-12-05
> 基于项目：Creeper
> 技术栈：Python 3.8+ + asyncio + Redis + LLM API

---

## 项目概况

**技术栈**：Python 3.8+ + asyncio + Redis + OpenAI SDK + Playwright
**架构模式**：模块化分层架构
**代码风格**：snake_case 命名 / 中文注释 / 类型提示

---

## 改动点

### 要实现什么
- 核心功能 1：完全删除文件夹内容 LLM 整合功能（aggregator.py 和相关模块）
- 核心功能 2：清理所有相关文件、配置、文档和测试
- 核心功能 3：移除相关缓存数据和配置项
- 核心功能 4：删除整合类提示词模板

### 与现有功能的关系
- 依赖现有模块：file_aggregator.py（FileScanner 类可能被其他模块使用）- 需要评估是否保留
- 集成位置：作为独立工具存在，删除不影响爬虫功能

### 新增依赖（如有）
- 无（删除操作）

---

## 实现方案

### 需要删除的文件
```
aggregator.py  # CLI 入口点
src/file_aggregator.py  # 核心整合逻辑（需要评估 FileScanner 依赖）
src/model_capabilities.py  # LLM 模型能力探测（可能被其他模块使用）
tests/file_aggregator/  # 测试目录（包含所有子文件）
data/aggregator_cache.json  # 本地缓存文件（如有）
docs/features/文件夹内容LLM整合.md  # 原需求文档
docs/features/文件夹内容LLM整合-自查报告.md  # 自查报告
prompts/aggregator/  # 整合模板目录（包含所有 .txt 文件）
```

### 需要修改的文件
```
src/config.py  # 删除 AGGREGATOR_* 相关配置项
src/prompt_templates.py  # 检查是否需要删除整合模板相关代码
CLAUDE.md  # 删除整合相关说明和命令
README.md  # 删除文件整合功能介绍
CHANGELOG.md  # 添加删除记录
.env.example  # 删除整合相关配置项注释
requirements.txt  # 如有 aggregator 独占依赖则删除
```

### 实施步骤

**步骤 1：环境准备**
- [ ] 确认没有正在运行的整合任务
- [ ] 备份重要的整合结果文件（如有）

**步骤 2：依赖关系分析**
- [ ] 检查 FileScanner 类是否被其他模块使用
- [ ] 检查 ModelCapabilityManager 是否被其他模块使用
- [ ] 确定需要保留的组件

**步骤 3：核心删除**
- [ ] 删除 aggregator.py CLI 入口文件
- [ ] 删除 src/file_aggregator.py 核心模块（或保留部分组件）
- [ ] 删除 tests/file_aggregator/ 测试目录
- [ ] 删除 prompts/aggregator/ 模板目录
- [ ] 删除相关功能文档

**步骤 4：清理相关代码**
- [ ] 清理 src/config.py 中的 AGGREGATOR_* 配置项
- [ ] 清理 .env.example 中的相关配置注释
- [ ] 检查并清理 src/prompt_templates.py 中的整合模板相关逻辑

**步骤 5：更新文档**
- [ ] 更新 CLAUDE.md：删除整合相关命令、配置、使用说明
- [ ] 更新 README.md：删除文件整合功能介绍
- [ ] 更新 CHANGELOG.md：记录删除操作

**步骤 6：清理缓存**
- [ ] 清理 Redis 中的 aggregator 相关缓存
- [ ] 删除本地缓存文件 data/aggregator_cache.json

**步骤 7：测试**
- [ ] 测试爬虫功能正常工作
- [ ] 确认 aggregator.py 命令不再可用

**步骤 8：文档更新**（必须执行）

使用 **Edit 工具**按以下标准判断并更新：

| 文档 | 需要更新 | 不需要更新 |
|------|----------|-----------|
| **CHANGELOG.md** | 每次功能完成后必须更新 | - |
| **README.md** | 删除文件整合功能介绍 | - |
| **CLAUDE.md** | 删除整合相关命令、配置、使用说明 | - |

**CHANGELOG.md 更新**（在 `## [Unreleased]` 下添加）：
```markdown
### Removed
- **文件夹内容 LLM 整合功能**：完全删除文件整合器及相关功能
  - 删除 aggregator.py 命令行工具
  - 删除 src/file_aggregator.py 核心模块
  - 删除 8 个整合模板文件
  - 删除相关测试和文档
  - 相关文件：`aggregator.py`, `src/file_aggregator.py`, `prompts/aggregator/`, `tests/file_aggregator/`
```

**版本号规则**：删除功能 → MINOR 版本（如果 API 兼容）或 PATCH（小改进）

**步骤 9：提交代码**（必须执行）

使用 **Bash 工具**执行：
```bash
git add .
git commit -m "feat: 删除文件夹内容LLM整合功能

- 删除 aggregator.py 和相关模块
- 清理整合模板和测试文件
- 更新文档说明

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**步骤 10：自我检查**
- [ ] 文件整合功能是否完全删除
- [ ] 爬虫功能是否正常（未被破坏）
- [ ] CHANGELOG.md 是否已更新
- [ ] README.md 是否已更新
- [ ] CLAUDE.md 是否已更新
- [ "实现步骤"与"需要修改/新增的文件"是否一致
- [ ] 所有相关文件是否已提交

---

## 使用方式

### 删除后的变化
- 不再支持 `python3 aggregator.py` 命令
- `prompts/aggregator/` 目录下的 8 个整合模板将被删除
- 文件夹级别的批量整合能力将消失
- 保留爬虫（creeper.py）功能

### 功能替代方案
如需要文件处理功能，可以使用：
1. **外部工具**：如 Pandoc、其他 Python 脚本等
2. **手动整合**：直接复制粘贴文件内容
3. **其他 LLM 工具**：如 ChatGPT、Claude 等进行手动整合

---

## 注意事项

**技术风险**：
- 确保 FileScanner 类不被其他模块需要（评估后再删除）
- 检查 ModelCapabilityManager 是否被翻译等其他功能使用
- 评估是否需要保留部分通用组件

**兼容性**：
- 这是一个破坏性变更，需要更新版本号
- 用户需要迁移到其他文件处理方案

**数据清理**：
- 务必清理 Redis 和本地的 aggregator 相关缓存
- 通知用户备份重要的整合结果文件

**组件保留策略**：
- 如果 FileScanner 被其他模块使用，可考虑将其提取为独立模块
- 如果 ModelCapabilityManager 被翻译功能使用，需要保留该模块
- 评估提示词模板管理器是否仍有存在价值