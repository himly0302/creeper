# prompts 提示词模板重构 - 需求文档

> 生成时间：2025-11-28
> 基于项目：Creeper (网页爬虫和文件处理工具)
> 技术栈：Python 3.8+ + OpenAI API + Redis

---

## 项目概况

**技术栈**：Python 3.8+ + AsyncOpenAI + Redis + Playwright
**架构模式**：模块化 / 命令行工具 / 异步处理
**代码风格**：中文注释 / snake_case 命名 / 类型提示

---

## 改动点

### 要实现什么
- 核心功能 1：按照文件解析功能的特点，创建适用于一对一解析的新提示词模板
- 核心功能 2：将新模板存放到独立的文件夹 `prompts/parser/`，与整合类模板（`prompts/aggregator/`）分离
- 核心功能 3：保持向后兼容，不影响现有整合功能的使用

### 与现有功能的关系
- 依赖现有模块：`src/prompt_templates.py` - 提示词模板加载器
- 依赖现有模块：`parser.py` - 文件解析 CLI 入口
- 依赖现有模块：`src/file_parser.py` - FileParser 类
- 集成位置：`src/prompt_templates.py` - 需要支持多目录扫描

### 新增依赖（如有）
无

---

## 实现方案

### 需要修改的文件
```
prompts/                           # 将现有模板移动到子目录
src/prompt_templates.py            # 修改内容：支持扫描 prompts/ 的所有子目录
parser.py                          # 修改内容：更新帮助文档，指明推荐使用 parser/ 目录下的模板
aggregator.py                      # 修改内容：更新帮助文档，指明推荐使用 aggregator/ 目录下的模板
CLAUDE.md                          # 修改内容：更新提示词模板的组织方式说明
```

### 需要新增的文件
```
prompts/parser/                         # 用途：存放文件解析类提示词模板
prompts/parser/code_parser.txt          # 用途：代码文件解析（一对一）
prompts/parser/doc_parser.txt           # 用途：文档文件解析（一对一）
prompts/parser/config_parser.txt        # 用途：配置文件解析（一对一）
prompts/aggregator/                     # 用途：存放文件整合类提示词模板
prompts/aggregator/code_summary.txt     # 用途：从 prompts/ 移动过来
prompts/aggregator/tutorial_merge.txt   # 用途：从 prompts/ 移动过来
prompts/aggregator/*.txt                # 用途：其他 6 个 merge 模板移动过来
tests/file_parser/                      # 测试文件，统一存放在此
```

### 实现步骤

**步骤 1：环境准备**
- [x] 创建新目录结构（`prompts/parser/` 和 `prompts/aggregator/`）
- [x] 移动现有模板到 `prompts/aggregator/`

**步骤 2：核心实现**
- [ ] 创建 3 个新的文件解析提示词模板：
  - `prompts/parser/code_parser.txt`：代码文件解析
  - `prompts/parser/doc_parser.txt`：文档文件解析
  - `prompts/parser/config_parser.txt`：配置文件解析
- [ ] 修改 `src/prompt_templates.py` 支持递归扫描子目录
- [ ] 添加错误处理和输入验证

**步骤 3：集成到现有系统**
- [ ] 修改 `parser.py`：更新 `--list-templates` 输出格式，显示模板所属目录
- [ ] 修改 `aggregator.py`：更新 `--list-templates` 输出格式
- [ ] 更新 `--help` 文档，推荐使用对应目录的模板
- [ ] 确保 `--template` 参数支持子目录路径（如 `parser/code_parser` 或 `code_parser`）

**步骤 4：测试**
- [ ] 测试新模板：使用 `parser.py --template parser/code_parser` 解析代码文件
- [ ] 测试旧模板兼容性：确保 `aggregator.py --template aggregator/code_summary` 仍然可用
- [ ] 测试简化路径：确保 `--template code_parser` 可以自动找到 `parser/code_parser.txt`
- [ ] **回归测试现有功能**（必须！）：运行 `aggregator.py` 确保整合功能未受影响
- [ ] 修复发现的问题

**步骤 5：文档更新**
- [ ] 更新 CHANGELOG.md（按下方"CHANGELOG.md 更新指南"执行）
- [ ] 检查并更新 CLAUDE.md 文件（按下方"CLAUDE.md 文件更新判断"执行）
- [ ] 更新 README.md 中的提示词模板使用示例（按下方"README.md 更新判断标准"执行）

**步骤 6：自我检查**
- [ ] **验证文档完整性**：检查本需求文档各章节是否填写完整，无遗漏或占位符
- [ ] **交叉验证**：确认"实现步骤"与"需要修改/新增的文件"一致
- [ ] **更新建议自查**：确认 CHANGELOG.md、README.md、CLAUDE.md 是否按标准更新（如适用）

**步骤 7：提交代码**
- [ ] 使用 git 提交新增需求的实现

---

## 使用方式

### 命令行（修改后）
```bash
# 文件解析功能（推荐使用 parser/ 目录下的模板）
python parser.py --input-folder ./src --output-folder ./output/parsed --template parser/code_parser
python parser.py --input-folder ./docs --output-folder ./output/summaries --template parser/doc_parser

# 文件整合功能（推荐使用 aggregator/ 目录下的模板）
python3 aggregator.py --folder ./src --output ./docs/code_summary.md --template aggregator/code_summary
python3 aggregator.py --folder ./docs --output ./merged.md --template aggregator/tutorial_merge

# 列出所有模板
python parser.py --list-templates
python aggregator.py --list-templates
```

### 配置项（如需要）
无新增配置项

---

## 完成检查清单

**代码质量**：
- [ ] 遵循项目代码风格
- [ ] 添加必要注释
- [ ] 错误处理完善
- [ ] 无安全漏洞

**测试**：
- [ ] 新功能测试通过
- [ ] 现有功能无影响
- [ ] 边界条件处理

**文档**：
- [ ] README 已判断并按需更新
- [ ] CHANGELOG 已更新
- [ ] CLAUDE.md 已检查并更新
- [ ] API/配置文档已更新

---

## CHANGELOG.md 更新指南

**版本号规则**：新增功能（向后兼容）→ MINOR (x.X.0)、破坏性变更 → MAJOR (X.0.0)、小改进/修复 → PATCH (x.x.X)

**模板**：
```markdown
## [1.9.0] - 2025-11-28

### Changed
- **提示词模板组织**：重构 prompts 目录结构，区分解析和整合类模板
  - 新增 `prompts/parser/` 目录：存放文件解析类提示词（一对一输出）
  - 新增 `prompts/aggregator/` 目录：存放文件整合类提示词（多对一输出）
  - 移动现有 8 个整合模板到 `prompts/aggregator/`
  - 相关文件：`src/prompt_templates.py`, `parser.py`, `aggregator.py`

### Added
- **文件解析模板**：新增 3 个文件解析提示词模板
  - `prompts/parser/code_parser.txt`：代码文件解析
  - `prompts/parser/doc_parser.txt`：文档文件解析
  - `prompts/parser/config_parser.txt`：配置文件解析
```

**README.md 更新判断标准**：

**何时需要更新**：
- ✅ 新增了用户可见的命令、参数或选项
- ✅ 新增了核心功能（影响用户使用方式）
- ✅ 修改了安装或配置流程
- ✅ 新增了重要的依赖或环境要求
- ❌ 仅内部优化、重构或 Bug 修复
- ❌ 新增辅助功能（不影响主要使用流程）
- ❌ 仅修改已有功能的实现细节

**本次需求是否需要更新 README.md**：
- ✅ **需要更新**：提示词模板的组织方式发生变化，影响用户使用（需要更新示例命令中的模板路径）

**更新原则**：README.md 只记录用户快速开始所需的核心内容。**⚠️ 切忌不要与 CHANGELOG.md 和 CLAUDE.md 文件内容重复**（不写版本历史、开发规范、详细实现）

**CLAUDE.md 文件更新判断**：

**何时更新**：
- ✅ 引入新的编程语言或框架
- ✅ 新增代码风格约定
- ✅ 修改错误处理或日志策略
- ✅ 引入新的性能标准或资源限制
- ✅ 更新依赖管理策略
- ❌ 仅新增普通功能，无规范变化

**本次需求是否需要更新 CLAUDE.md**：
- ✅ **需要更新**：提示词模板的组织和使用规范发生变化（需要更新"添加新的提示词模板"部分）

---

## 提交代码

在需求实现完成后，按以下顺序操作：

```bash
# 1. 完成步骤 5（文档更新）：更新 CHANGELOG.md、判断并更新 README.md 和 CLAUDE.md
# 2. 完成步骤 6（自我检查）：验证文档完整性、交叉验证、更新建议自查
# 3. 添加所有修改的文件
git add .
# 4. 提交，commit 信息使用需求文档的标题
git commit -m "feat: prompts 提示词模板重构"
```

注意：
- **严格按顺序**：步骤 5（文档更新）→ 步骤 6（自我检查）→ 步骤 7（提交代码）
- 使用 `feat:` 前缀表示这是新增功能
- 标题要简洁明确，例如："新增数据导出功能"、"添加命令行参数解析"
- 如更新了 README.md 或 CLAUDE.md，在 commit message 中可补充说明

---

## 注意事项

**技术风险**：
- 目录结构变化可能影响用户现有脚本（使用 `--template` 参数的脚本）
- 缓解方案：保持向后兼容，支持简化路径（自动在子目录中搜索）

**兼容性**：
- ✅ 向后兼容：旧的模板路径仍然可用（`aggregator/code_summary` 等）
- ✅ 不需要迁移脚本
- ✅ 不破坏现有 API

**实现细节**：
- `src/prompt_templates.py` 的 `list_templates()` 需要递归扫描子目录
- `get_template()` 方法需要支持：
  1. 完整路径：`parser/code_parser`
  2. 简化路径：`code_parser`（自动在所有子目录中搜索）
  3. 同名冲突处理：优先使用第一个找到的，或提示用户使用完整路径

**新模板设计原则**：
- **一对一解析**：提示词应针对单个文件，输出独立的分析结果
- **禁止增量更新逻辑**：不应包含"如果提供了已有内容，请整合"等语句
- **禁止汇总多个文件**：不应包含"整合所有文件"等语句
- **输出格式要求**：直接输出 Markdown，禁止使用代码块包裹
- **参考现有模板**：可以参考 `code_summary.txt` 的分析深度，但去除整合逻辑
