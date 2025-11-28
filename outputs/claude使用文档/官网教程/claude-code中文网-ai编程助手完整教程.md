# Claude Code中文网 - AI编程助手完整教程

> 📅 **爬取时间**: 2025-11-28 10:45:37
> 🔗 **来源链接**: https://www.claude-cn.org/posts/Claude-code-best-practices.html
> 📝 **网页描述**: Claude Code中文教程网站，提供完整的安装指南、使用技巧、最佳实践和实战案例
> ✍️ **作者**: Claude 中文网
> 📆 **发布时间**: 2025-08-22
> 🎯 **爬取方式**: 静态爬取

---

# Claude Code最佳实践（Claude Code: Best practices）

翻译自：Claude Code: Best practices for agentic coding

https://www.anthropic.com/engineering/claude-code-best-practices

我们最近发布了 Claude Code，这是一款用于代理式编程的命令行工具。Claude Code 作为一项研究项目开发，为 Anthropic 的工程师和研究人员提供了一种更原生的方式，将 Claude 集成到他们的编码工作流中。

Claude Code 有意保持低层级和无强制性，几乎提供了对模型的原始访问，而不强加特定的工作流。这种设计理念造就了一个灵活、可定制、可脚本化且安全的强大工具。虽然功能强大，但这种灵活性也为不熟悉代理式编程工具的工程师带来了一定的学习曲线——至少在他们形成自己的最佳实践之前是这样。

本文概述了一些已被证明有效的通用模式，既适用于 Anthropic 内部团队，也适用于在各种代码库、语言和环境中使用 Claude Code 的外部工程师。这里的建议并非一成不变或普遍适用；请将其视为起点。我们鼓励你大胆尝试，找到最适合自己的方法！

想了解更详细的信息？我们在 claude.ai/code 上有全面的文档，涵盖了本文提到的所有功能，并提供了更多示例、实现细节和高级技巧。

# 1. 自定义你的设置

Claude Code 是一款代理式编程助手，会自动将上下文拉入提示中。这一过程会消耗时间和 token，但你可以通过环境调优来优化它。

## a. 创建 CLAUDE.md 文件

CLAUDE.md 是一个特殊文件，Claude 在开始对话时会自动将其拉入上下文。这使其成为记录以下内容的理想场所：

• 常用 bash 命令

• 核心文件和工具函数

• 代码风格指南

• 测试说明

• 仓库规范（如分支命名、合并 vs. rebase 等）

• 开发环境设置（如 pyenv 使用、可用编译器等）

• 项目中特有的异常行为或警告

• 你希望 Claude 记住的其他信息

CLAUDE.md 文件没有固定格式。我们建议保持简洁且易读。例如：

```
# Bash commands- npm run build: Build the project- npm run typecheck: Run the typechecker# Code style- Use ES modules (import/export) syntax, not CommonJS (require)- Destructure imports when possible (eg. import { foo } from 'bar')# Workflow- Be sure to typecheck when you’re done making a series of code changes- Prefer running single tests, and not the whole test suite, for performance
```

你可以将 CLAUDE.md 文件放在多个位置：

• 仓库根目录，或你运行 claude 的地方（最常见）。命名为 CLAUDE.md 并提交到 git，以便在会话间和团队成员间共享（推荐）；或命名为 CLAUDE.local.md 并加入 .gitignore

• 你运行 claude 目录的任意父级。这对 monorepo 特别有用，比如你在 root/foo 运行 claude，而 root/CLAUDE.md 和 root/foo/CLAUDE.md 都会被自动拉入上下文

• 你运行 claude 目录的任意子级。这种情况下，Claude 会在你处理子目录文件时按需拉入 CLAUDE.md

• 你的 home 文件夹（~/.claude/CLAUDE.md），适用于所有 claude 会话

运行 /init 命令时，Claude 会自动为你生成一个 CLAUDE.md。

## b. 调优你的 CLAUDE.md 文件

你的 CLAUDE.md 文件会成为 Claude 提示的一部分，因此应像常用提示一样不断优化。常见错误是添加了大量内容却没有迭代其有效性。请花时间尝试，找出最能提升模型指令遵循度的内容。

你可以手动添加内容，也可以按 # 键给 Claude 下指令，Claude 会自动将其写入相关的 CLAUDE.md。许多工程师在编码时频繁用 # 记录命令、文件和风格指南，然后将 CLAUDE.md 的更改一并提交，方便团队成员受益。

在 Anthropic，我们偶尔会用提示优化器处理 CLAUDE.md 文件，并经常调整指令（如用“IMPORTANT”或“YOU MUST”加重语气）以提升遵循度。

![在这里插入图片描述](images/6d41cafc69df.png)

## c. 管理 Claude 的允许工具列表

默认情况下，Claude Code 对任何可能修改系统的操作（如文件写入、许多 bash 命令、MCP 工具等）都会请求权限。我们有意采用这种保守设计以优先保证安全。你可以自定义允许列表，添加你认为安全的工具，或允许易于撤销的潜在不安全工具（如文件编辑、git commit）。

管理允许工具有四种方式：

• 在会话中被提示时选择“Always allow”

• 会话中使用 /permissions 命令 添加或移除允许的工具。例如，添加 Edit 以始终允许文件编辑，Bash(git commit:*) 允许 git 提交，或 mcp__puppeteer__puppeteer_navigate 允许用 Puppeteer MCP 服务器导航

• 手动编辑 .claude/settings.json 或 ~/.claude.json（推荐将前者提交到源码管理，方便团队共享）

• 用 --allowedTools CLI 标志 为会话指定权限

## d. 如果用 GitHub，安装 gh CLI

Claude 能用 gh CLI 与 GitHub 交互，如创建 issue、打开 PR、读取评论等。没有安装 gh 时，Claude 仍可用 GitHub API 或 MCP 服务器（如已安装）。

# 2. 给 Claude 更多工具

Claude 可访问你的 shell 环境，你可以像为自己一样为其构建便捷脚本和函数。它还可通过 MCP 和 REST API 使用更复杂的工具。

## a. 用 bash 工具配合 Claude

Claude Code 继承你的 bash 环境，能访问所有工具。虽然 Claude 了解常见工具如 unix 工具和 gh，但对你的自定义 bash 工具则需你告知：

- 告诉 Claude 工具名并举例用法

- 告诉 Claude 运行 --help 查看工具文档

- 在 CLAUDE.md 记录常用工具

## b. 用 MCP 配合 Claude

Claude Code 既是 MCP 服务器也是客户端。作为客户端，它可通过三种方式连接任意数量的 MCP 服务器：

• 项目配置中（在该目录运行 Claude Code 时可用）

• 全局配置中（所有项目可用）

• 提交到 .mcp.json 文件（任何在你代码库工作的成员都可用）。例如，你可以在 .mcp.json 添加 Puppeteer 和 Sentry 服务器，方便每位工程师开箱即用。

用 MCP 时，建议用 --mcp-debug 标志帮助排查配置问题。

## c. 用自定义斜杠命令

对于重复性工作流（如调试循环、日志分析等），可将提示模板存储在 .claude/commands 文件夹下的 Markdown 文件中。输入 / 时，这些命令会出现在斜杠命令菜单。你可以将这些命令提交到 git，方便团队成员共享。

自定义斜杠命令可用特殊关键字 $ARGUMENTS 传递参数。

例如，以下是一个自动拉取并修复 GitHub issue 的斜杠命令：请分析并修复 GitHub issue: $ARGUMENTS。

```
Please analyze and fix the GitHub issue: $ARGUMENTS.Follow these steps:1. Use `gh issue view` to get the issue details2. Understand the problem described in the issue3. Search the codebase for relevant files4. Implement the necessary changes to fix the issue5. Write and run tests to verify the fix6. Ensure code passes linting and type checking7. Create a descriptive commit message8. Push and create a PRRemember to use the GitHub CLI (`gh`) for all GitHub-related tasks.
```

将上述内容放入 .claude/commands/fix-github-issue.md 后，即可通过 /project:fix-github-issue 命令在 Claude Code 中调用。例如用 /project:fix-github-issue 1234 让 Claude 修复第 1234 号 issue。你也可以将个人命令放到 ~/.claude/commands 文件夹，在所有会话中使用。

# 3. 尝试常见工作流

Claude Code 不强加特定工作流，给你充分的灵活性。社区用户总结出多种高效使用 Claude Code 的模式：

## a. 探索、规划、编码、提交

适用于多种问题的通用工作流：

- 让 Claude 阅读相关文件、图片或 URL，可给出大致指示（如“读处理日志的文件”）或具体文件名（如“读 logging.py”），但明确告知暂时不要写代码。

a. 这一步建议充分利用子代理，尤其在处理复杂问题时。让 Claude 用子代理核查细节或调查问题，能在不影响效率的前提下保留更多上下文。

- 让 Claude 制定解决特定问题的计划。建议用“think”一词触发扩展思考模式，Claude 会获得更多计算时间以更全面地评估方案。具体短语会分配不同的思考预算：“think” < “think hard” < “think harder” < “ultrathink”，级别越高，思考预算越多。

a. 如果这一步结果合理，可以让 Claude 创建文档或 GitHub issue 记录计划，便于后续回滚。

- 让 Claude 实现解决方案代码。此时也可让它在实现过程中显式验证方案的合理性。

- 让 Claude 提交结果并创建 PR。如有需要，也可让 Claude 更新 README 或 changelog，说明所做更改。

第 1-2 步至关重要——否则 Claude 往往会直接跳到编码。对于需要深入思考的问题，先让 Claude 研究和规划，能显著提升效果。

## b. 写测试、提交；编码、迭代、提交

适合用单元、集成或端到端测试易于验证的更改。测试驱动开发（TDD）在代理式编程中更强大：

- 让 Claude 根据预期输入/输出对写测试。明确说明你在做 TDD，这样 Claude 就不会为尚未实现的功能写 mock 实现。

- 让 Claude 运行测试并确认失败。此时明确告知不要写实现代码很有帮助。

- 对测试满意后让 Claude 提交测试。

- 让 Claude 编写通过测试的代码，并告知不要修改测试。让 Claude 持续迭代直到所有测试通过。通常需要几轮 Claude 编写代码、运行测试、调整代码、再测试。

a. 此时可让独立子代理验证实现是否过拟合测试。

- 对更改满意后让 Claude 提交代码。

Claude 在有明确目标（如可视化 mock、测试用例等）时表现最佳。提供预期输出后，Claude 能不断修改、评估并逐步完善，直到成功。

## c. 编码、截图结果、迭代

类似测试工作流，你可以为 Claude 提供可视化目标：

- 为 Claude 提供截图工具（如 Puppeteer MCP 服务器、iOS 模拟器 MCP 服务器，或手动复制/粘贴截图到 Claude）。

- 通过粘贴、拖拽或文件路径提供视觉 mock。

- 让 Claude 实现设计、截图结果并迭代，直到结果与 mock 匹配。

- 满意后让 Claude 提交。

像人类一样，Claude 的输出通过多次迭代会显著提升。第一版可能不错，2-3 轮后通常会更好。给 Claude 提供可见输出工具，效果最佳。

![在这里插入图片描述](images/07b10c27354e.png)

## d. 安全 YOLO 模式

你可以用 claude --dangerously-skip-permissions 跳过所有权限检查，让 Claude 一次性完成任务。适合修复 lint 错误或生成样板代码等工作流。

让 Claude 任意运行命令有风险，可能导致数据丢失、系统损坏，甚至数据泄露（如提示注入攻击）。为降低风险，建议在无网络访问的容器中用 --dangerously-skip-permissions。可参考 Docker Dev Containers 实现。

## e. 代码库问答

新成员入职时，可用 Claude Code 学习和探索代码库。你可以像和项目工程师结对编程时一样向 Claude 提问。Claude 会自动搜索代码库，回答如：

• 日志是如何工作的？

• 如何新增 API 端点？

• foo.rs 第 134 行的 async move { ... } 有什么作用？

• CustomerOnboardingFlowImpl 处理了哪些边界情况？

• 为什么第 333 行调用 foo() 而不是 bar()？

• baz.py 第 334 行在 Java 中的等价实现是什么？

在 Anthropic，这已成为核心入职流程，显著提升了上手速度，减轻了其他工程师负担。无需特殊提示！直接提问，Claude 会自动探索代码找答案。

![在这里插入图片描述](images/003bf18074f7.png)

## f. 用 Claude 操作 git

Claude 能高效处理许多 git 操作。许多 Anthropic 工程师 90% 以上的 git 操作都交给 Claude：

• 搜索 git 历史，回答“v1.2.3 包含了哪些更改？”、“谁负责这个功能？”、“这个 API 为什么这样设计？”等问题。建议明确让 Claude 查 git 历史。

• 编写提交信息。Claude 会自动查看你的更改和最近历史，生成包含所有相关上下文的提交信息。

• 处理复杂 git 操作，如回滚文件、解决 rebase 冲突、比较和移植补丁。

## g. 用 Claude 操作 GitHub

Claude Code 可管理许多 GitHub 交互：

• 创建 PR：Claude 理解“pr”简写，会根据 diff 和上下文生成合适的提交信息。

• 一键解决简单代码审查评论：只需让它修复 PR 上的评论（可选补充说明），完成后推送回 PR 分支。

• 修复构建失败或 linter 警告

• 分类和整理 open issues，让 Claude 循环处理所有 open GitHub issues

这样无需记住 gh 命令行语法，自动化日常任务。

## h. 用 Claude 处理 Jupyter notebook

Anthropic 的研究员和数据科学家用 Claude Code 读写 Jupyter notebook。Claude 能解读输出（包括图片），快速探索和交互数据。没有强制提示或工作流，推荐在 VS Code 并排打开 Claude Code 和 .ipynb 文件。

你还可以让 Claude 优化 notebook 或数据可视化的美观度。明确要求“美观”能提醒 Claude 优化人类观感。

# 4. 优化你的工作流

以下建议适用于所有工作流：

## a. 指令要具体

Claude Code 在收到更具体指令时成功率显著提升，尤其是首次尝试。明确指令能减少后续修正。

例如：

![在这里插入图片描述](images/c5efe6ef90d3.png)

参考首页现有 widget 的实现，了解模式，尤其是代码与接口如何分离。HotDogWidget.php 是很好的例子。然后，按此模式实现一个新日历 widget，支持选择月份和前后翻页选择年份。只用代码库已有的库，从零实现。Claude 能推断意图，但不能读心。具体说明能更好地对齐预期。

![在这里插入图片描述](images/f5555e5328b2.png)

## b. 给 Claude 图片

Claude 通过多种方式善于处理图片和图表：

• 粘贴截图（macOS 下 cmd+ctrl+shift+4 截图到剪贴板，ctrl+v 粘贴。注意不是常规的 cmd+v，且远程时无效）

• 拖拽图片到输入框

• 提供图片文件路径

这对 UI 开发时用设计稿做参考、分析和调试可视化图表特别有用。即使不加图片，也可以明确告知 Claude 结果需美观。

![在这里插入图片描述](images/3230e85e9a0a.png)

## c. 明确提及要处理的文件

用 tab 补全快速引用仓库中任意文件或文件夹，帮助 Claude 找到或更新正确资源。

![在这里插入图片描述](images/583dee8db160.png)

## d. 给 Claude URL

在提示中粘贴具体 URL，Claude 会自动拉取和阅读。为避免同一域名反复请求权限（如 docs.foo.com），用 /permissions 添加域名到允许列表。

## e. 及时纠正

虽然自动接受模式（shift+tab 切换）让 Claude 自动工作，但主动协作和引导 Claude 通常效果更好。开头详细说明任务最佳，但你随时可以纠正 Claude 的做法。

以下四种工具有助于纠正：

• 让 Claude 先制定计划，明确告知未确认前不要编码。

• 按 Escape 中断 Claude 任意阶段（思考、调用工具、编辑文件），保留上下文，便于重定向或补充指令。

• 双击 Escape 回到历史记录，编辑前一个提示，探索不同方向。可反复编辑直到满意为止。

• 让 Claude 撤销更改，常与第 2 点结合，尝试不同方案。

虽然 Claude Code 偶尔能一次性完美解决问题，但用这些纠正工具通常能更快获得更好结果。

## f. 用 /clear 保持上下文聚焦

长会话中，Claude 的上下文窗口可能被无关对话、文件内容和命令填满，影响性能甚至分散注意力。每完成一个任务，建议用 /clear 重置上下文窗口。

## g. 用清单和草稿本处理复杂工作流

对于多步骤或需穷举解决方案的大型任务（如代码迁移、修复大量 lint 错误、运行复杂构建脚本），建议让 Claude 用 Markdown 文件（甚至 GitHub issue）做清单和草稿本：

例如，修复大量 lint 问题时：

- 让 Claude 运行 lint 命令，将所有错误（含文件名和行号）写入 Markdown 清单

- 让 Claude 逐条处理，每修复并验证一个就勾选，再处理下一个

## h. 向 Claude 传递数据

有多种方式向 Claude 提供数据：

• 直接复制粘贴到提示（最常用）

• 管道传入 Claude Code（如 cat foo.txt | claude），适合日志、CSV、大数据

• 让 Claude 通过 bash 命令、MCP 工具或自定义斜杠命令拉取数据

• 让 Claude 读取文件或拉取 URL（图片同理）

大多数会话会结合多种方式。例如，你可以先管道传入日志文件，再让 Claude 用工具拉取更多上下文调试日志。

- 用无头模式自动化基础设施

Claude Code 提供无头模式，适用于 CI、pre-commit 钩子、构建脚本和自动化等非交互场景。用 -p 标志加提示启用无头模式，--output-format stream-json 可流式输出 JSON。

注意，无头模式不会在会话间持久化。每次都需手动触发。

## a. 用 Claude 处理 issue 分拣

无头模式可驱动由 GitHub 事件触发的自动化，如新 issue 创建时。比如，Claude Code 的公开仓库用 Claude 检查新 issue 并分配合适标签。

## b. 用 Claude 做 linter

Claude Code 可做主观代码审查，发现传统 linter 检查不到的问题，如拼写错误、过时注释、误导性函数或变量名等。

# 6. 多 Claude 协作提升效率

除了单独使用，最强大的用法之一是并行运行多个 Claude 实例：

## a. 一个 Claude 写代码，另一个 Claude 审查

简单高效的方法是让一个 Claude 写代码，另一个审查或测试。类似多工程师协作，分开上下文有时更好：

- 用 Claude 写代码

- 用 /clear 或在另一个终端启动第二个 Claude

- 让第二个 Claude 审查第一个 Claude 的工作

- 再启动一个 Claude（或再次 /clear），读取代码和审查反馈

- 让这个 Claude 根据反馈修改代码

你也可以让一个 Claude 写测试，另一个写通过测试的代码。甚至可以让 Claude 实例间通过草稿本交流，指定谁写谁读。

这种分工往往比单 Claude 处理所有任务效果更好。

## b. 多仓库检出

许多 Anthropic 工程师会：

- 创建 3-4 个 git 检出，放在不同文件夹

- 分别在不同终端标签页打开每个文件夹

- 在每个文件夹启动 Claude，分配不同任务

- 轮流检查进度，批准/拒绝权限请求

## c. 用 git worktree

适合多个独立任务，是多检出的轻量替代方案。git worktree 允许你将同一仓库的多个分支检出到不同目录。每个 worktree 有独立工作目录和文件，历史和 reflog 共享。

用 git worktree 可让你同时在项目不同部分运行多个 Claude，每个专注于独立任务。例如，一个 Claude 重构认证系统，另一个构建数据可视化组件。任务互不干扰，各自高效推进，无需等待或处理冲突：

- 创建 worktree：git worktree add ../project-feature-a feature-a

- 在每个 worktree 启动 Claude：cd ../project-feature-a && claude

- 按需创建更多 worktree（在新终端标签页重复 1-2 步）

一些建议：

• 命名规范统一

• 每个 worktree 保持一个终端标签页

• Mac 用户用 iTerm2 设置 Claude 需要关注时的通知

• 不同 worktree 用不同 IDE 窗口

• 完成后清理：git worktree remove ../project-feature-a

## d. 用无头模式配合自定义脚本

claude -p（无头模式）可将 Claude Code 程序化集成到更大工作流，同时利用其内置工具和系统提示。主要有两种模式：

- 批量处理，适合大规模迁移或分析（如分析数百日志或数千 CSV）：

a. 让 Claude 写脚本生成任务列表。例如，生成 2000 个需从框架 A 迁移到 B 的文件列表。

b. 循环处理任务，程序化调用 Claude，传入任务和可用工具。例如：claude -p “migrate foo.py from React to Vue. When you are done, you MUST return the string OK if you succeeded, or FAIL if the task failed.” --allowedTools Edit Bash(git commit:*)

c. 多次运行脚本，迭代优化提示，直到满意。

- 流水线，将 Claude 集成到现有数据/处理流水线：

a. 调用 claude -p “<你的提示>” --json | your_command，your_command 是流水线下一步

b. 就这样！可选的 JSON 输出便于自动处理。

两种用法都建议用 --verbose 标志调试 Claude 调用。生产环境建议关闭 verbose，输出更简洁。

---

*本文由 Creeper 自动爬取并清洗*