# URL列表直接输出功能 - 需求文档

> 生成时间：2025-12-05
> 基于项目：Creeper (v1.9.2)
> 技术栈：Python 3.8+ + asyncio + Trafilatura + Redis

---

## 项目概况

**技术栈**：Python 3.8+ + asyncio + Trafilatura + Redis + Playwright
**架构模式**：模块化设计，继承自BaseCrawler的双模式执行（同步/异步）
**代码风格**：类型提示 + 数据类 + 彩色日志 + 依赖注入

---

## 改动点

### 要实现什么
- 核心功能 1：新增 `--urls` 参数，接受逗号分隔的URL列表
- 核心功能 2：直接输出JSON格式的结构化数据到控制台
- 核心功能 3：每次强制重新查询（类似 --force 行为）

### 与现有功能的关系
- 依赖现有模块：AsyncWebFetcher - 负责网页内容抓取
- 依赖现有模块：URLItem - 可复用URL数据结构
- 集成位置：creeper.py:main() - 添加新的命令行参数处理逻辑

### 新增依赖（如有）
- 无新增依赖（使用现有的 json 标准库）

---

## 实现方案

### 需要修改的文件
```
src/cli_parser.py  # 修改内容：添加 --urls 参数
creeper.py         # 修改内容：处理URL列表输入模式，输出JSON格式
```

### 需要新增的文件
```
src/url_list_mode.py  # 用途：URL列表模式的核心逻辑实现
tests/test_url_list_mode/  # ⚠️ 测试文件必须保存在 tests/ 目录下
├── test_url_list_cli.py   # 测试命令行参数解析
└── test_url_list_output.py # 测试JSON输出格式
```

### 实施步骤

**步骤 1：环境准备**
- [ ] 创建新的模块文件 `src/url_list_mode.py`
- [ ] 创建测试目录结构

**步骤 2：核心实现**
- [ ] 实现URL列表解析功能：将逗号分隔的URL字符串转为列表
- [ ] 实现并发抓取功能：复用AsyncWebFetcher获取页面内容
- [ ] 实现数据格式化：将WebPage对象转为指定的JSON格式
- [ ] 添加错误处理和输入验证

**步骤 3：集成到现有系统**
- [ ] 修改 `src/cli_parser.py`：添加 `--urls` 参数定义
- [ ] 修改 `creeper.py`：添加URL列表模式的处理逻辑

**步骤 4：测试**
- [ ] 测试新功能（测试文件保存到 `tests/` 目录）
- [ ] **回归测试现有功能**（必须！）

**步骤 5：文档更新**（必须执行）

使用 **Edit 工具**按以下标准判断并更新：

| 文档 | 需要更新 | 不需要更新 |
|------|----------|-----------|
| **CHANGELOG.md** | 每次功能完成后必须更新 | - |
| **README.md** | 新增用户可见命令/参数、核心功能、修改安装配置流程 | 仅内部优化/重构、辅助功能 |
| **CLAUDE.md** | 引入新语言/框架、新增代码风格约定、修改错误处理策略 | 仅新增普通功能 |

**CHANGELOG.md 更新**（在 `## [Unreleased]` 下添加）：
```markdown
### Added
- **CLI**：新增 --urls 参数支持直接输入URL列表
  - 接受逗号分隔的URL，输出JSON格式结构化数据
  - 相关文件：`src/url_list_mode.py`, `src/cli_parser.py`
```

**版本号规则**：新增功能（兼容）→ MINOR、破坏性变更 → MAJOR、小改进/修复 → PATCH

**步骤 6：提交代码**（必须执行）

使用 **Bash 工具**执行：
```bash
git add .
git commit -m "feat: add URL list output mode

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**步骤 7：自我检查**
- [ ] 新功能是否按需求正常工作
- [ ] 现有功能是否正常（未被破坏）
- [ ] CHANGELOG.md 是否已更新
- [ ] README.md 是否按标准判断并更新
- [ ] CLAUDE.md 是否按标准判断并更新
- [ ] "实现步骤"与"需要修改/新增的文件"是否一致
- [ ] 所有相关文件是否已提交

---

## 使用方式

### 命令行（如适用）
```bash
# 单个URL
python creeper.py --urls "https://example.com"

# 多个URL（逗号分隔）
python creeper.py --urls "https://example1.com,https://example2.com"

# 结合其他选项
python creeper.py --urls "https://example.com" -c 10 --debug
```

### 输出格式
```json
[
    {
        "title": "页面标题1",
        "summary": "页面描述或摘要",
        "content": "提取的正文内容",
        "url": "https://example1.com"
    },
    {
        "title": "页面标题2",
        "summary": "页面描述或摘要",
        "content": "提取的正文内容",
        "url": "https://example2.com"
    }
]
```

### 配置项（如需要）
```json
{"url_list_mode": true}  // 启用URL列表模式（内部标识）
```

---

## 注意事项

**技术风险**：无新增依赖，与现有系统兼容性良好
**兼容性**：向后兼容，不影响现有的Markdown文件输入模式
**性能考虑**：URL列表模式默认强制重新抓取，不使用Redis去重