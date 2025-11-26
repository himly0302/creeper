# 合并同步/异步 CLI - 代码重构需求文档

> 生成时间: 2025-11-26
> 基于项目: Creeper 网页爬虫工具
> 技术栈: Python 3.8+ + asyncio + argparse

---

## 项目概况

**技术栈**: Python 3.8+ + asyncio + Playwright + Redis
**架构模式**: 模块化分层架构 (parser/fetcher/storage/dedup/cookie)
**代码风格**:
- 中文注释和日志
- 使用 dataclass 定义数据结构
- 统一的日志记录器
- 完善的错误处理

**现状问题**:
- `creeper.py` (同步版本, 293 行) 和 `creeper_async.py` (异步版本, 381 行) 存在 **47.4% 的代码重复**
- 完全相同的代码: ~220 行 (32.6%)
- 高相似度代码: ~100 行 (14.8%)
- 任何 bug 修复或功能改进需要在两个文件中同步修改,维护成本高

---

## 改动点

### 要实现什么

**核心功能 1: 统一 CLI 入口**
- 将 `creeper.py` 和 `creeper_async.py` 合并为单一入口点 `creeper.py`
- 通过 CLI 参数 `--sync` 选择同步模式,默认使用异步模式
- 保持向后兼容,现有使用方式不变

**核心功能 2: 提取公共逻辑**
- 创建基类 `BaseCrawler` 包含共同初始化、统计、错误处理逻辑
- 创建统一的参数解析函数 `create_argument_parser()`
- 提取公共的工具方法到基类

**核心功能 3: 保持功能完整**
- 同步模式保留原 `creeper.py` 的功能
- 异步模式保留原 `creeper_async.py` 的所有增强功能(Redis Cookie、交互式登录)
- 确保回归测试全部通过

### 与现有功能的关系

**完全兼容现有模块**:
- `src/parser.py` - 无需修改
- `src/dedup.py` - 无需修改
- `src/storage.py` - 无需修改
- `src/cookie_manager.py` - 无需修改
- `src/fetcher.py` - 无需修改
- `src/async_fetcher.py` - 无需修改
- `src/interactive_login.py` - 无需修改

**集成位置**:
- `creeper.py` - 完全重写,合并两个版本
- `creeper_async.py` - 删除(不再需要)

### 新增依赖

无需新增依赖,使用现有依赖。

---

## 实现方案

### 需要修改的文件

```
creeper.py                    # 重构: 合并同步/异步逻辑,成为统一入口
creeper_async.py              # 删除: 功能已合并到 creeper.py
```

### 需要新增的文件

```
src/base_crawler.py           # 用途: 基类,包含公共逻辑
src/cli_parser.py             # 用途: 统一的 CLI 参数解析
```

### 实现步骤

#### 步骤 1: 创建统一参数解析模块

**新建 `src/cli_parser.py`**:

- [ ] 创建 `create_argument_parser()` 函数
- [ ] 合并两个版本的参数定义 (8 个共同参数 + 1 个 `--login-url` + 1 个新增 `--sync`)
- [ ] 添加新参数:
  ```python
  parser.add_argument(
      '--sync',
      action='store_true',
      help='使用同步模式(默认: 异步模式)'
  )
  ```
- [ ] 保留所有现有参数,确保向后兼容
- [ ] 版本号统一为当前最新版本 (1.2.0)

**参数列表** (共 11 个):
1. `input_file` - Markdown 输入文件 (可选,支持 `--login-url` 模式)
2. `-o/--output` - 输出目录
3. `-c/--concurrency` - 并发数 (同步模式忽略)
4. `--force` - 强制重新爬取
5. `--debug` - 调试模式
6. `--no-playwright` - 禁用 Playwright
7. `--cookies-file` - Cookie 文件路径
8. `--save-cookies` - 保存 Cookie
9. `--login-url` - 交互式登录 URL
10. `--sync` - 使用同步模式 **(新增)**
11. `-v/--version` - 版本信息

#### 步骤 2: 创建基类

**新建 `src/base_crawler.py`**:

```python
"""
BaseCrawler - 爬虫基类
提供同步和异步版本的公共逻辑
"""

from abc import ABC, abstractmethod
from src.utils import setup_logger

logger = setup_logger("creeper")


class BaseCrawler(ABC):
    """爬虫基类,包含公共逻辑"""

    def __init__(self, args):
        """初始化公共属性"""
        self.args = args
        self.stats = {
            'total': 0,
            'success': 0,
            'skipped': 0,
            'failed': 0
        }
        self.failed_items = []

        # 子类负责初始化的模块
        self.parser = None
        self.dedup = None
        self.fetcher = None
        self.storage = None
        self.cookie_manager = None

    @abstractmethod
    def run(self):
        """运行爬虫 - 子类实现"""
        pass

    @abstractmethod
    def _process_url(self, item):
        """处理单个 URL - 子类实现"""
        pass

    def _display_stats(self):
        """显示统计信息 - 公共方法"""
        print("\n" + "=" * 60)
        print("📊 爬取统计")
        print("=" * 60)
        print(f"总计:   {self.stats['total']} 个 URL")
        print(f"成功:   {self.stats['success']} 个 ✓")
        print(f"跳过:   {self.stats['skipped']} 个 ⊘")
        print(f"失败:   {self.stats['failed']} 个 ✗")

        if self.stats['total'] > 0:
            success_rate = (self.stats['success'] / self.stats['total']) * 100
            print(f"成功率: {success_rate:.1f}%")

        print("=" * 60)

        # 显示输出目录
        if self.storage:
            storage_stats = self.storage.get_stats()
            print(f"\n输出目录: {storage_stats['output_dir']}")
            print(f"生成文件: {storage_stats['total_files']} 个")
```

- [ ] 实现基类 `BaseCrawler`
- [ ] 提取统计信息初始化到 `__init__()`
- [ ] 提取 `_display_stats()` 方法 (100% 相同)
- [ ] 定义抽象方法 `run()` 和 `_process_url()`
- [ ] 添加公共的错误处理框架

#### 步骤 3: 重构 creeper.py

**重写 `creeper.py`**:

- [ ] 导入 `BaseCrawler` 和 `create_argument_parser()`
- [ ] 定义 `SyncCrawler` 类继承 `BaseCrawler`
- [ ] 定义 `AsyncCrawler` 类继承 `BaseCrawler`
- [ ] 在 `main()` 中根据 `args.sync` 选择执行模式:
  ```python
  def main():
      """主函数"""
      from src.cli_parser import create_argument_parser

      # 解析参数
      parser = create_argument_parser()
      args = parser.parse_args()

      # 设置调试模式
      if args.debug:
          config.DEBUG = True
          config.LOG_LEVEL = 'DEBUG'
          import logging
          logging.getLogger("creeper").setLevel(logging.DEBUG)

      # 处理交互式登录
      if args.login_url:
          # 必须使用异步模式
          if args.sync:
              logger.error("交互式登录不支持同步模式,请移除 --sync 参数")
              sys.exit(1)

          # 执行登录逻辑 (从 creeper_async.py 迁移)
          asyncio.run(do_interactive_login(args))
          return

      # 检查输入文件
      if not args.input_file:
          logger.error("错误: 必须提供输入文件或使用 --login-url 进行登录")
          sys.exit(1)

      if not Path(args.input_file).exists():
          logger.error(f"输入文件不存在: {args.input_file}")
          sys.exit(1)

      # 根据模式选择 Crawler
      if args.sync:
          # 同步模式
          logger.info("使用同步模式")
          if args.concurrency > 1:
              logger.warning("同步模式不支持并发,将忽略 -c/--concurrency 参数")

          creeper = SyncCrawler(args)
          creeper.run()
      else:
          # 异步模式 (默认)
          creeper = AsyncCrawler(args)
          asyncio.run(creeper.run())
  ```

**SyncCrawler 实现** (基于原 `creeper.py`):
- [ ] 继承 `BaseCrawler`
- [ ] 实现 `__init__()` - 初始化同步模块
- [ ] 实现 `run()` - 同步版本的运行逻辑
- [ ] 实现 `_process_url()` - 同步处理 URL
- [ ] 使用 `src.fetcher.WebFetcher`
- [ ] Cookie 管理仅支持文件模式

**AsyncCrawler 实现** (基于原 `creeper_async.py`):
- [ ] 继承 `BaseCrawler`
- [ ] 实现 `__init__()` - 初始化异步模块 (支持 Redis Cookie)
- [ ] 实现 `async def run()` - 异步版本的运行逻辑
- [ ] 实现 `async def _process_url()` - 异步处理 URL
- [ ] 使用 `src.async_fetcher.AsyncWebFetcher`
- [ ] 支持 Redis Cookie 存储

#### 步骤 4: 删除旧文件

**删除 `creeper_async.py`**:

- [ ] 备份原文件 (以防需要回滚):
  ```bash
  cp creeper_async.py creeper_async.py.bak
  ```
- [ ] 删除 `creeper_async.py`:
  ```bash
  rm creeper_async.py
  ```
- [ ] 在 git 中标记删除:
  ```bash
  git rm creeper_async.py
  ```
- [ ] 在文档中说明迁移路径:
  - 旧命令: `python creeper_async.py input.md`
  - 新命令: `python creeper.py input.md` (功能完全相同)

#### 步骤 5: 测试

- [ ] **单元测试**:
  - 测试 `create_argument_parser()` 参数解析
  - 测试 `BaseCrawler` 公共方法

- [ ] **集成测试 - 同步模式**:
  ```bash
  python creeper.py tests/test_input.md --sync
  ```

- [ ] **集成测试 - 异步模式** (默认):
  ```bash
  python creeper.py tests/test_input.md
  python creeper.py tests/test_input.md -c 10
  ```

- [ ] **交互式登录测试**:
  ```bash
  python creeper.py --login-url https://example.com/login
  ```

- [ ] **参数测试**:
  - 测试所有 11 个参数
  - 测试参数组合 (`--sync` + `--login-url` 应报错)
  - 测试默认值

- [ ] **功能回归测试**:
  - Cookie 文件存储 (`--cookies-file`)
  - Cookie Redis 存储 (异步模式)
  - 去重检查 (`--force`)
  - Playwright 切换 (`--no-playwright`)
  - 调试模式 (`--debug`)

#### 步骤 6: 文档更新

- [ ] 更新 `README.md`:
  ```markdown
  ## 使用方式

  ### 基本使用

  ```bash
  # 异步模式 (推荐,默认)
  python creeper.py input.md

  # 异步模式 + 设置并发数
  python creeper.py input.md -c 10

  # 同步模式
  python creeper.py input.md --sync

  # 交互式登录
  python creeper.py --login-url https://example.com/login
  ```

  ### 迁移说明 (v1.3.0+)

  - ✅ `creeper_async.py` 已合并到 `creeper.py`
  - 旧命令: `python creeper_async.py input.md`
  - 新命令: `python creeper.py input.md` (功能完全相同)
  ```

- [ ] 更新 `CHANGELOG.md`:
  ```markdown
  ## [1.3.0] - 2025-11-26

  ### Changed
  - 🔧 **代码重构**: 合并 `creeper.py` 和 `creeper_async.py` 为统一入口
    - 默认使用异步模式,提供 `--sync` 参数切换同步模式
    - 提取公共逻辑到 `BaseCrawler` 基类
    - 统一 CLI 参数解析到 `src/cli_parser.py`
    - 消除 ~220 行重复代码 (47.4% 代码重复率降为 0%)
  - 📋 新增 CLI 参数: `--sync` (切换同步模式)

  ### Technical
  - 新增 `src/base_crawler.py` - 爬虫基类
  - 新增 `src/cli_parser.py` - 统一参数解析
  - `SyncCrawler` 和 `AsyncCrawler` 继承 `BaseCrawler`
  - 完全向后兼容,现有使用方式不变

  ### Deprecated
  - ⚠️ `creeper_async.py` 已删除,功能已合并到 `creeper.py`
  - **迁移**: `python creeper_async.py` → `python creeper.py`
  - 异步模式仍是默认模式,无需修改参数
  ```

- [ ] 更新 `.env.example` - 无需修改

- [ ] 更新 `docs/` 中的相关文档:
  - 更新所有 `creeper_async.py` 调用示例为 `creeper.py`
  - 添加 `--sync` 参数说明

---

## 使用方式

### 异步模式 (默认,推荐)

```bash
# 基本使用
python creeper.py input.md

# 设置并发数
python creeper.py input.md -c 10

# 强制重新爬取
python creeper.py input.md --force

# 交互式登录
python creeper.py --login-url https://example.com/login
```

### 同步模式

```bash
# 使用同步模式
python creeper.py input.md --sync

# 同步模式会忽略 -c 参数
python creeper.py input.md --sync -c 10  # -c 10 被忽略
```

### 向后兼容

```bash
# v1.2.0 及之前版本
python creeper_async.py input.md

# v1.3.0+ 迁移后
python creeper.py input.md  # 功能完全相同,默认异步模式
```

**迁移说明**:
- `creeper_async.py` 已删除
- 直接替换为 `python creeper.py` 即可
- 所有参数保持不变
- 异步模式仍是默认模式

### 参数对比

| 参数 | 同步模式 | 异步模式 |
|------|---------|---------|
| `input_file` | ✅ 必需 | ✅ 必需 (除非使用 `--login-url`) |
| `-c/--concurrency` | ⚠️ 忽略 | ✅ 支持 |
| `--login-url` | ❌ 不支持 | ✅ 支持 |
| Cookie Redis 存储 | ❌ 仅文件 | ✅ 支持 |

---

## 完成检查清单

**代码质量**:
- [ ] 遵循项目代码风格 (中文注释)
- [ ] 添加必要的文档字符串
- [ ] 错误处理完善
- [ ] 无安全漏洞
- [ ] 通过代码审查

**重构目标**:
- [ ] 消除重复代码 (目标: 47.4% → 0%)
- [ ] 保持功能完整性 (100% 特性保留)
- [ ] 向后兼容 (现有脚本无需修改)
- [ ] 代码行数减少 (~200 行)

**测试**:
- [ ] 同步模式测试通过
- [ ] 异步模式测试通过
- [ ] 交互式登录测试通过
- [ ] 所有参数测试通过
- [ ] 回归测试通过 (现有功能无影响)
- [ ] 迁移测试:确认旧用户可以无缝切换到新命令

**文档**:
- [ ] README 已更新
- [ ] CHANGELOG 已更新
- [ ] 示例代码已更新
- [ ] 迁移指南已提供 (如需要)

---

## CHANGELOG.md 更新指南

**版本号**: `1.3.0` (代码重构,新增 `--sync` 参数,向后兼容)

**更新位置**: `CHANGELOG.md` 文件顶部

**内容**:
```markdown
## [1.3.0] - 2025-11-26

### Changed
- 🔧 **代码重构**: 合并同步/异步 CLI 为统一入口
  - `creeper.py` 和 `creeper_async.py` 合并
  - 默认异步模式,可通过 `--sync` 切换同步模式
  - 提取公共逻辑到基类,消除 220 行重复代码 (47.4%)
  - 统一参数解析和错误处理
  - 完全向后兼容

### Added
- 📋 新增 CLI 参数: `--sync` 切换同步模式
- 🏗️ 新增基类: `BaseCrawler` 统一爬虫逻辑
- 🔧 新增模块: `src/cli_parser.py` 统一参数解析

### Deprecated
- ⚠️ `creeper_async.py` 已删除,功能已合并到 `creeper.py`
- **迁移**: `python creeper_async.py` → `python creeper.py`
- 异步模式仍是默认模式,无需修改参数

### Technical
- 相关文件: `src/base_crawler.py`, `src/cli_parser.py`, `creeper.py`
- 代码行数减少: ~200 行
- 重复代码消除: 47.4% → 0%
- 维护成本降低: bug 修复从 2 处变为 1 处
```

---

## 注意事项

**技术风险**:
- 重构可能引入新 bug → 充分的回归测试
- 基类设计不当可能影响可维护性 → 保持简单,仅提取真正公共的逻辑
- 异步/同步模式切换可能有边界情况 → 明确参数互斥关系

**兼容性**:
- ✅ 功能向后兼容: 所有参数和功能完整保留
- ⚠️ 命令行迁移: `python creeper_async.py` → `python creeper.py`
- ✅ 默认行为不变: 异步模式仍是默认和推荐模式

**性能影响**:
- ✅ 无性能影响: 重构仅影响代码组织,不改变执行逻辑
- ✅ 异步模式仍然是默认和推荐模式

**用户体验**:
- ✅ 更简洁的命令: 统一使用 `python creeper.py`
- ✅ 更清晰的模式选择: `--sync` 显式声明
- ⚠️ 需要更新旧脚本: 替换 `creeper_async.py` 为 `creeper.py`
- ✅ 文档更易理解: 单一入口点

**维护成本**:
- ✅ 大幅降低: bug 修复和功能改进只需修改一处
- ✅ 代码更简洁: ~200 行代码减少
- ✅ 更易扩展: 基类提供统一接口

---

## 实现优先级

**P0 (必须实现)**:
1. 创建 `src/cli_parser.py` - 统一参数解析
2. 创建 `src/base_crawler.py` - 提取公共逻辑
3. 重构 `creeper.py` - 合并同步/异步入口
4. 回归测试 - 确保功能完整

**P1 (重要功能)**:
1. 向后兼容处理 - 保留或删除 `creeper_async.py`
2. 文档更新 - README、CHANGELOG
3. 示例更新 - 统一使用新命令

**P2 (可选优化)**:
1. 添加单元测试覆盖基类
2. 性能对比测试 (重构前后)
3. 迁移脚本 (自动更新现有项目的调用)

---

## 重构收益

**代码质量提升**:
- 消除 220 行重复代码 (47.4% → 0%)
- 总代码行数减少: ~674 行 → ~470 行 (30% 减少)
- 单一职责原则: CLI 解析、公共逻辑、执行逻辑分离

**维护成本降低**:
- Bug 修复效率提升 50%: 从 2 处修改变为 1 处
- 新功能开发更快: 公共逻辑复用
- 代码审查更容易: 逻辑更清晰

**用户体验改善**:
- 统一入口点: `python creeper.py`
- 显式模式选择: `--sync` 参数
- 更好的文档和示例

---

**开发建议**:
1. 先实现 `cli_parser.py`,确保参数解析正确
2. 再实现 `base_crawler.py`,提取公共逻辑
3. 最后重构 `creeper.py`,集成两个版本
4. 充分测试每个步骤,确保功能正确
5. 保留原文件备份,以便回滚

---

**测试策略**:
1. **单元测试**: 测试新模块 (`cli_parser`, `base_crawler`)
2. **集成测试**: 测试完整流程 (同步/异步)
3. **回归测试**: 使用现有测试用例确保功能不变
4. **兼容性测试**: 测试向后兼容性
5. **性能测试**: 确保重构不影响性能

---

**回滚计划**:
如果重构出现严重问题:
1. 恢复备份文件 `creeper.py.bak` 和 `creeper_async.py.bak`
2. 删除新增的 `src/base_crawler.py` 和 `src/cli_parser.py`
3. 使用 git 恢复到重构前的提交
4. 通知用户回滚原因和计划

---

**版本发布计划**:
1. **Alpha**: 内部测试版本 (开发环境)
2. **Beta**: 公开测试版本 (征集反馈)
3. **RC**: 候选发布版本 (完整测试)
4. **Release**: 正式发布版本 (v1.3.0)
