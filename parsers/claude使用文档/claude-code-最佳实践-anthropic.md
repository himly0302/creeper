# Claude Code 最佳实践 - 文档分析

## 文档概览
**文件路径**：outputs/claude使用文档/个人文章/claude-code-最佳实践-anthropic.md
**文档类型**：最佳实践指南/教程
**主题**：Claude Code 命令行工具的高效使用方法和最佳实践

## 核心内容

### 概念定义

- **Claude Code**：用于代理式编码的命令行工具，提供接近原始模型的访问能力
- **CLAUDE.md**：特殊配置文件，用于提供项目特定的上下文信息
- **MCP (Model Context Protocol)**：模型上下文协议，用于连接外部工具
- **无头模式 (Headless Mode)**：在非交互式环境中运行 Claude Code 的模式

### 功能说明

- **环境定制**：通过 CLAUDE.md 文件定制项目上下文
- **工具扩展**：集成 bash 工具、MCP 服务器和自定义命令
- **工作流支持**：支持多种编码工作流模式
- **自动化能力**：支持 CI/CD 集成和自动化任务

## 操作步骤

### 环境定制与配置

#### 步骤 1：创建 CLAUDE.md 文件
在以下位置创建 CLAUDE.md 文件：
- 项目根目录（最常见）
- 父/子目录（适用于 monorepo）
- 用户主目录 (`~/.claude/CLAUDE.md`)

**示例内容**：
```
# Bash 命令
- npm run build：构建项目
- npm run typecheck：运行类型检查器
# 代码风格
- 使用 ES 模块 (import/export) 语法，而不是 CommonJS (require)
- 尽可能解构导入 (例如 import { foo } from 'bar')
# 工作流
- 在完成一系列代码更改后，请务必进行类型检查
- 出于性能考虑，首选运行单个测试，而不是整个测试套件
```

#### 步骤 2：管理工具权限
**方法**：
- 会话中选择 "Always allow"
- 使用 `/permissions` 命令
- 编辑 `.claude/settings.json` 或 `~/.claude.json`
- 使用 `--allowedTools` CLI 标志

#### 步骤 3：安装 GitHub CLI
```bash
# 安装 gh CLI 工具
gh --version
```

### 扩展 Claude 的工具集

#### 步骤 1：集成 bash 工具
- 告知 Claude 工具名称和使用示例
- 运行 `--help` 查看工具文档
- 在 CLAUDE.md 中记录常用工具

#### 步骤 2：配置 MCP 服务器
**配置位置**：
- 项目配置 (`.mcp.json`)
- 全局配置
- 签入的配置文件

**调试命令**：
```bash
claude --mcp-debug
```

#### 步骤 3：创建自定义斜杠命令
在 `.claude/commands` 目录下创建 Markdown 文件

**示例命令** (`fix-github-issue.md`)：
```
请分析并修复 GitHub issue：$ARGUMENTS。
请遵循以下步骤：
1. 使用 `gh issue view` 获取 issue 详细信息
2. 理解 issue 中描述的问题
3. 在代码库中搜索相关文件
4. 实现必要的更改以修复 issue
5. 编写并运行测试以验证修复
6. 确保代码通过 linting 和类型检查
7. 创建描述性的提交消息
8. 推送并创建 PR
请记住使用 GitHub CLI (`gh`) 处理所有与 GitHub 相关的任务。
```

**调用方式**：
```bash
/project:fix-github-issue 1234
```

### 有效的工作流程模式

#### 探索、规划、编码、提交工作流

**步骤 1：探索**
要求 Claude 阅读相关文件、图像或 URL，但暂时不要编写代码

**步骤 2：规划**
使用思考指令触发扩展思考模式：
- "think" < "think hard" < "think harder" < "ultrathink"

**步骤 3：编码**
要求 Claude 实现解决方案并验证合理性

**步骤 4：提交**
提交结果并创建拉取请求

#### 测试驱动开发 (TDD) 工作流

**步骤 1：编写测试**
```bash
# 要求 Claude 基于预期的输入/输出对编写测试
```

**步骤 2：验证测试失败**
明确告诉 Claude 不要编写实现代码

**步骤 3：提交测试**
```bash
# 提交测试文件
```

**步骤 4：编写实现代码**
要求 Claude 编写通过测试的代码，不要修改测试

**步骤 5：提交代码**
```bash
# 提交实现代码
```

#### 基于视觉反馈迭代工作流

**步骤 1：提供截图方法**
使用 Puppeteer MCP 服务器或手动截图

**步骤 2：提供视觉模型**
通过复制/粘贴、拖放或文件路径提供图像

**步骤 3：实现和迭代**
要求 Claude 实现设计，截图结果，并迭代直到匹配

**步骤 4：提交**
```bash
# 提交最终代码
```

### 优化日常工作流

#### 提供明确指令
**差指令**："为 foo.py 添加测试"
**好指令**："为 foo.py 编写一个新的测试用例，覆盖用户未登录的边缘情况。避免使用模拟（mock）"

#### 使用图像和文件
**方法**：
- 粘贴截图 (macOS: cmd+ctrl+shift+4)
- 拖放图像到提示输入
- 提供图像文件路径
- 使用 tab 键自动补全文件引用

#### 纠正和中断
**工具**：
- 按 Escape 键中断当前操作
- 双击 Escape 键跳回历史记录
- 要求 Claude 制定计划
- 要求 Claude 撤销更改

#### 清理上下文
```bash
/clear
```

## 配置参数

### CLAUDE.md 文件位置
| 位置 | 用途 | 推荐 |
|------|------|------|
| 项目根目录 | 项目特定配置 | ✓ 推荐签入 git |
| 父目录 | Monorepo 共享配置 | ✓ |
| 子目录 | 子项目特定配置 | ✓ |
| `~/.claude/CLAUDE.md` | 全局配置 | ✓ 个人使用 |

### 权限管理配置
| 方法 | 作用范围 | 持久性 |
|------|----------|--------|
| "Always allow" | 当前会话 | 临时 |
| `/permissions` 命令 | 当前会话 | 临时 |
| `.claude/settings.json` | 项目范围 | 持久 |
| `~/.claude.json` | 全局范围 | 持久 |
| `--allowedTools` 标志 | 单次运行 | 临时 |

## 代码示例

### 无头模式使用
```bash
# 自动化任务示例
claude -p "将 foo.py 从 React 迁移到 Vue。完成后，如果成功，您必须返回字符串 OK，如果任务失败，则返回 FAIL。" --allowedTools Edit Bash(git commit:*)

# 流水线集成
claude -p "<您的提示>" --json | your_command
```

### Git worktree 使用
```bash
# 创建 worktree
git worktree add ../project-feature-a feature-a

# 在 worktree 中启动 Claude
cd ../project-feature-a && claude

# 清理 worktree
git worktree remove ../project-feature-a
```

## 高级用法

### 多 Claude 协作
**模式**：
- 一个 Claude 编写代码，另一个审查或测试
- 使用 `/clear` 或在另一个终端启动第二个 Claude
- 让实例通过工作草稿板相互通信

### 无头模式自动化
**扇出模式**：
```bash
# 处理大型迁移
claude -p "将文件从框架 A 迁移到框架 B" --allowedTools Edit Bash(git commit:*)
```

**流水线模式**：
```bash
# 集成到处理流水线
claude -p "<提示>" --json | next_command
```

## 常见问题

### Q1：如何提高 Claude 的首次成功率？
**症状**：Claude 经常需要多次迭代才能完成任务
**原因**：指令不够具体
**解决方案**：
```bash
# 提供具体指令而非模糊要求
# 差："为 foo.py 添加测试"
# 好："为 foo.py 编写一个新的测试用例，覆盖用户未登录的边缘情况。避免使用模拟"
```

### Q2：如何处理上下文窗口过满？
**症状**：Claude 性能下降，注意力分散
**原因**：上下文窗口填满无关信息
**解决方案**：
```bash
/clear
```

### Q3：如何安全地使用跳过权限模式？
**症状**：需要快速修复 lint 错误但担心安全风险
**原因**：`--dangerously-skip-permissions` 可能造成数据丢失
**解决方案**：
```bash
# 在无互联网访问的容器中使用
docker run --rm -it your-container claude --dangerously-skip-permissions
```

## 最佳实践

### 环境配置
- 迭代优化 CLAUDE.md 文件，保持简洁有效
- 使用 `#` 键快速添加指令到 CLAUDE.md
- 在团队项目中签入 CLAUDE.md 和设置文件

### 工作流优化
- 对于复杂问题，先让 Claude 研究和制定计划
- 使用测试驱动开发提供明确的目标
- 为视觉任务提供图像参考
- 在任务切换时使用 `/clear` 命令

### 协作模式
- 使用多个 Claude 实例进行代码编写和审查
- 利用 git worktree 实现并行开发
- 为重复工作流创建自定义斜杠命令

## 注意事项

### 安全限制
- ⚠️ `--dangerously-skip-permissions` 可能造成数据丢失或系统损坏
- ⚠️ 在容器中使用跳过权限模式以降低风险
- ⚠️ 谨慎管理工具白名单，平衡安全与效率

### 性能优化
- ⚠️ 长时间会话会降低 Claude 性能，定期使用 `/clear`
- ⚠️ 上下文窗口有限，避免加载过多无关文件
- ⚠️ 具体指令显著提高首次成功率

### 兼容性
- GitHub CLI (`gh`) 可显著提升 GitHub 相关任务效率
- MCP 服务器需要正确配置和调试
- 无头模式适用于 CI/CD 和非交互式环境

## 相关链接
- **官方文档**：claude.ai/code
- **GitHub CLI**：https://cli.github.com/
- **MCP 协议**：Model Context Protocol 文档