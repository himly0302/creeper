# 快速开始 - Claude Code Docs

> 📅 **爬取时间**: 2025-11-28 14:12:31
> 🔗 **来源链接**: https://code.claude.com/docs/zh-CN/quickstart
> 📝 **网页描述**: 欢迎使用 Claude Code！
> 📆 **发布时间**: 2025-11-06
> 🎯 **爬取方式**: 静态爬取

---

## 开始前

确保您有：- 打开的终端或命令提示符
- 一个要处理的代码项目
- 一个 Claude.ai（推荐）或 Claude Console 账户

## 步骤 1：安装 Claude Code

To install Claude Code, use one of the following methods:- Native Install (Recommended)
- NPM

**Homebrew (macOS, Linux):**

**macOS, Linux, WSL:**

**Windows PowerShell:**

**Windows CMD:**

## 步骤 2：登录您的账户

Claude Code 需要账户才能使用。当您使用`claude`

命令启动交互式会话时，您需要登录：
- Claude.ai（订阅计划 - 推荐）
- Claude Console（带预付额度的 API 访问）

当您首次使用 Claude Console 账户对 Claude Code 进行身份验证时，会自动为您创建一个名为”Claude Code”的工作区。此工作区为您的组织中所有 Claude Code 使用情况提供集中的成本跟踪和管理。

您可以在同一电子邮件地址下拥有两种账户类型。如果您需要再次登录或切换账户，请在 Claude Code 中使用

`/login`

命令。## 步骤 3：启动您的第一个会话

在任何项目目录中打开您的终端并启动 Claude Code：`/help`

查看可用命令，或输入 `/resume`

继续之前的对话。
## 步骤 4：提出您的第一个问题

让我们从了解您的代码库开始。尝试以下命令之一：Claude Code 根据需要读取您的文件 - 您无需手动添加上下文。Claude 还可以访问其自己的文档，并可以回答有关其功能和特性的问题。

## 步骤 5：进行您的第一次代码更改

现在让我们让 Claude Code 进行一些实际的编码。尝试一个简单的任务：- 找到适当的文件
- 向您显示建议的更改
- 请求您的批准
- 进行编辑

Claude Code 在修改文件前总是请求许可。您可以批准单个更改或为会话启用”全部接受”模式。

## 步骤 6：在 Claude Code 中使用 Git

Claude Code 使 Git 操作变得对话式：## 步骤 7：修复错误或添加功能

Claude 擅长调试和功能实现。 用自然语言描述您想要的内容：- 定位相关代码
- 理解上下文
- 实现解决方案
- 如果可用，运行测试

## 步骤 8：尝试其他常见工作流

有许多方式可以与 Claude 合作：**重构代码**

**编写测试**

**更新文档**

**代码审查**

## 基本命令

以下是日常使用中最重要的命令：| 命令 | 功能 | 示例 |
|---|---|---|
`claude` | 启动交互模式 | `claude` |
`claude "task"` | 运行一次性任务 | `claude "fix the build error"` |
`claude -p "query"` | 运行一次性查询，然后退出 | `claude -p "explain this function"` |
`claude -c` | 继续最近的对话 | `claude -c` |
`claude -r` | 恢复之前的对话 | `claude -r` |
`claude commit` | 创建 Git 提交 | `claude commit` |
`/clear` | 清除对话历史 | `> /clear` |
`/help` | 显示可用命令 | `> /help` |
`exit` 或 Ctrl+C | 退出 Claude Code | `> exit` |

## 初学者的专业提示

对您的请求要具体

对您的请求要具体

而不是：“fix the bug”尝试：“fix the login bug where users see a blank screen after entering wrong credentials”

使用分步说明

使用分步说明

将复杂任务分解为步骤：

让 Claude 先探索

让 Claude 先探索

在进行更改之前，让 Claude 理解您的代码：

使用快捷方式节省时间

使用快捷方式节省时间

- 按
`?`

查看所有可用的键盘快捷方式 - 使用 Tab 进行命令补全
- 按 ↑ 查看命令历史
- 输入
`/`

查看所有斜杠命令

## 接下来是什么？

现在您已经学习了基础知识，探索更多高级功能：## 获取帮助

**在 Claude Code 中**：输入`/help`

或询问”how do I…”**文档**：您在这里！浏览其他指南**社区**：加入我们的 Discord 获取提示和支持

---

*本文由 Creeper 自动爬取并清洗*