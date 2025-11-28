# Claude Code 最佳实践 - 文档分析

## 文档概览
**文件路径**：outputs/claude使用文档/个人文章/claude-code-最佳实践-anthropic.md
**文档类型**：最佳实践指南/教程
**主题**：Claude Code 命令行工具的高效使用方法和最佳实践

## 核心内容

### 概念定义

- **Claude Code**：一款用于代理式编码的命令行工具，提供接近原始模型的访问能力
- **CLAUDE.md**：特殊配置文件，用于提供项目特定的上下文信息
- **MCP (Model Context Protocol)**：模型上下文协议，用于连接外部工具
- **无头模式 (Headless Mode)**：在非交互式环境中运行 Claude Code 的模式

### 功能说明

- **环境定制**：通过 CLAUDE.md 文件定制项目上下文
- **工具扩展**：通过 bash 工具、MCP 服务器和自定义命令扩展功能
- **工作流支持**：支持多种编码工作流模式
- **自动化集成**：支持 CI/CD、git 钩子等自动化场景

## 操作步骤

### 环境配置

#### 步骤 1：创建 CLAUDE.md 文件
在项目根目录、父/子目录或用户主目录创建 CLAUDE.md 文件

**命令/代码**：
```bash
# 在项目根目录创建
touch CLAUDE.md

# 或使用 Claude 自动生成
claude /init
```

**注意事项**：文件可以命名为 CLAUDE.md（推荐签入 git）或 CLAUDE.local.md（推荐 .gitignore）

#### 步骤 2：管理工具权限
通过四种方式管理允许的工具列表：

1. 会话期间选择"始终允许"
2. 使用 `/permissions` 命令
3. 编辑 `.claude/settings.json` 或 `~/.claude.json`
4. 使用 `--allowedTools` CLI 标志

### 工具扩展配置

#### 步骤 1：配置 MCP 服务器
在项目配置或全局配置中添加 MCP 服务器

**命令/代码**：
```bash
# 使用调试模式启动以识别配置问题
claude --mcp-debug
```

#### 步骤 2：创建自定义斜杠命令
在 `.claude/commands` 目录下创建 Markdown 文件

**示例命令文件** `.claude/commands/fix-github-issue.md`：
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

## 工作流模式

### 探索、规划、编码、提交工作流

#### 步骤 1：探索
要求 Claude 阅读相关文件、图像或 URL，暂时不要编写代码

#### 步骤 2：规划
使用思考指令制定计划：
- "think" < "think hard" < "think harder" < "ultrathink"

#### 步骤 3：编码
实现解决方案，验证合理性

#### 步骤 4：提交
提交结果并创建拉取请求

### 测试驱动开发 (TDD) 工作流

#### 步骤 1：编写测试
基于预期的输入/输出对编写测试

#### 步骤 2：验证测试失败
运行测试并确认失败

#### 步骤 3：提交测试
提交测试代码

#### 步骤 4：实现代码
编写通过测试的代码，迭代直到所有测试通过

#### 步骤 5：提交实现
提交最终代码

### 视觉反馈迭代工作流

#### 步骤 1：提供视觉目标
通过截图、拖放或文件路径提供设计图

#### 步骤 2：实现代码
在代码中实现设计

#### 步骤 3：截图结果
获取运行结果截图

#### 步骤 4：迭代改进
重复步骤 2-3 直到与目标一致

## 配置参数

### CLAUDE.md 文件位置
| 位置 | 用途 | 优先级 |
|------|------|---------|
| 项目根目录 | 项目特定配置 | 最高 |
| 父目录 | Monorepo 共享配置 | 中等 |
| 子目录 | 子项目特定配置 | 中等 |
| ~/.claude/CLAUDE.md | 全局用户配置 | 最低 |

### 权限管理命令
| 命令 | 用途 | 示例 |
|------|------|-------|
| `/permissions` | 管理工具白名单 | `/permissions add Edit` |
| `--allowedTools` | CLI 权限设置 | `--allowedTools "Edit,Bash(git commit:*)"` |

## 高级用法

### 无头模式自动化

**命令/代码**：
```bash
# 启用无头模式
claude -p "您的提示" --output-format stream-json

# 示例：issue 自动分类
claude -p "分析新创建的 GitHub issue 并分配适当标签"
```

### 多 Claude 实例协作

**命令/代码**：
```bash
# 终端1：编写代码
claude

# 终端2：审查代码
claude
# 然后使用 /clear 清空上下文进行审查
```

### Git worktree 并行工作

**命令/代码**：
```bash
# 创建 worktree
git worktree add ../project-feature-a feature-a

# 在新 worktree 中启动 Claude
cd ../project-feature-a && claude

# 完成后清理
git worktree remove ../project-feature-a
```

## 最佳实践

### 指令优化
- **具体指令**：提供明确的、具体的指令
- **视觉辅助**：使用截图、图表和设计稿
- **文件引用**：使用 tab 键自动补全引用文件

### 工作流优化
- **及早修正**：使用 Escape 键中断错误操作
- **上下文清理**：任务切换时使用 `/clear` 命令
- **清单管理**：复杂任务使用 Markdown 清单记录进度

### 安全实践
- **权限管理**：谨慎使用工具权限
- **容器隔离**：危险操作在无网络容器中进行
- **备份策略**：重要更改前确保有备份

## 注意事项

### ⚠️ 安全警告
- 避免在生产环境使用 `--dangerously-skip-permissions`
- 在容器中运行高风险操作
- 定期审查工具权限设置

### ⚠️ 性能优化
- 保持 CLAUDE.md 文件简洁有效
- 定期使用 `/clear` 清理上下文
- 避免在长时间会话中积累无关信息

### 兼容性
- 需要安装 gh CLI 以获得最佳 GitHub 集成
- 支持多种开发环境和编程语言
- 版本要求：Claude Code 最新版本

## 相关链接
- **官方文档**：claude.ai/code
- **GitHub CLI**：https://cli.github.com/
- **MCP 协议**：Model Context Protocol 文档