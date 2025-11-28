# LLM 模型能力自动探测 - 需求文档

> 生成时间：2025-11-28
> 基于项目：Creeper
> 技术栈：Python 3.8+ + AsyncIO + OpenAI SDK

---

## 项目概况

**技术栈**：Python 3.8+ + AsyncIO + OpenAI SDK + Redis + dotenv
**架构模式**：分层模块化设计（爬虫层 + 文件处理层 + 缓存层）
**代码风格**：
- 类型注解完整（`FileItem`, `Optional[str]` 等）
- 异步优先（`async def`）
- 配置驱动（`config.py` 统一管理）
- 日志规范（`logger.info/debug/error`）
- 混合持久化（Redis + JSON 文件）

---

## 改动点

### 要实现什么
- **核心功能 1**：首次调用 LLM API 时，自动探测模型的最大输入 token 和输出 token 限制
- **核心功能 2**：将探测结果缓存到 Redis，避免重复探测
- **核心功能 3**：后续 API 调用自动使用缓存的 token 限制，替代硬编码的 `max_tokens`

### 与现有功能的关系
- **依赖现有模块**：
  - `src/config.py` - 配置管理系统
  - `src/file_parser.py:FileParser` - 文件解析 LLM 调用
  - `src/file_aggregator.py:LLMAggregator` - 文件聚合 LLM 调用
  - `src/translator.py:Translator` - 翻译 LLM 调用
  - Redis 缓存系统（现有去重和解析缓存模式）

- **集成位置**：
  - `src/file_parser.py:337-350` - `FileParser.__init__()` 初始化时探测
  - `src/file_aggregator.py:323-336` - `LLMAggregator.__init__()` 初始化时探测
  - `src/translator.py:35-41` - `Translator.__init__()` 初始化时探测

### 新增依赖
无需新增依赖（使用现有的 `redis`, `openai`, `dotenv`）

---

## 实现方案

### 需要修改的文件
```
src/config.py                  # 新增模型探测配置项
src/file_parser.py             # FileParser 集成探测逻辑
src/file_aggregator.py         # LLMAggregator 集成探测逻辑
src/translator.py              # Translator 集成探测逻辑
.env.example                   # 新增配置示例
```

### 需要新增的文件
```
src/model_capabilities.py     # 模型能力探测和缓存管理器
tests/model_capabilities/      # 测试文件，统一存放在此
  ├── test_capability_cache.py
  └── test_model_detection.py
```

### 实现步骤

**步骤 1：环境准备**
- [x] 无需安装新依赖
- [ ] 创建 `src/model_capabilities.py` 文件
- [ ] 创建测试目录 `tests/model_capabilities/`

**步骤 2：核心实现**
- [ ] 实现 `ModelCapabilityManager` 类：
  - 模型能力缓存（Redis + 本地 JSON 文件混合持久化）
  - 首次探测逻辑（调用 LLM API 询问 token 限制）
  - 缓存读写和恢复机制（遵循现有 Redis 缓存模式）
- [ ] 实现探测提示词：
  - 系统提示词：要求 LLM 返回 JSON 格式的能力信息
  - 响应解析：提取 `max_input_tokens` 和 `max_output_tokens`
- [ ] 添加错误处理：
  - 探测失败时使用默认值（当前配置的 `AGGREGATOR_MAX_TOKENS`）
  - 超时处理（设置 5 秒探测超时）
  - 无效响应处理（JSON 解析失败时回退）

**步骤 3：集成到现有系统**
- [ ] 修改 `src/config.py`：
  - 新增 `MODEL_CAPABILITY_CACHE_FILE = 'data/model_capabilities.json'`
  - 新增 `ENABLE_MODEL_AUTO_DETECTION = true` 开关
  - 新增 `MODEL_DETECTION_TIMEOUT = 10` 超时配置
- [ ] 修改 `src/file_parser.py:FileParser.__init__()`：
  - 初始化时调用 `ModelCapabilityManager.get_or_detect()`
  - 使用探测到的 `max_output_tokens` 替代传入的 `max_tokens`
  - 保留 `max_tokens` 参数作为探测失败的回退值
- [ ] 修改 `src/file_aggregator.py:LLMAggregator.__init__()`：
  - 同 FileParser 的集成方式
- [ ] 修改 `src/translator.py:Translator.__init__()`：
  - 初始化时探测能力
  - 将硬编码的 `max_tokens=8000` 改为使用探测值
- [ ] 更新 `.env.example`：
  - 添加 `ENABLE_MODEL_AUTO_DETECTION=true` 配置项
  - 添加配置说明注释

**步骤 4：测试**
- [ ] 单元测试：
  - `tests/model_capabilities/test_capability_cache.py`：测试缓存读写和恢复
  - `tests/model_capabilities/test_model_detection.py`：测试探测逻辑和错误处理
- [ ] 集成测试：
  - 测试 FileParser 正常探测和使用缓存
  - 测试探测失败时的回退机制
- [ ] 回归测试：
  - 运行 `python parser.py` 确保现有功能正常
  - 运行 `python aggregator.py` 确认整合功能正常
  - 检查 Redis 中的缓存数据格式

**步骤 5：文档更新**
- [ ] 更新 CHANGELOG.md（按下方"CHANGELOG.md 更新指南"执行）
- [ ] 更新 CLAUDE.md 文件（新增 LLM 模型探测最佳实践）
- [ ] 更新 README.md（在"开发命令"章节补充新配置项说明）

**步骤 6：自我检查**
- [ ] **验证文档完整性**：检查本需求文档各章节是否填写完整，无遗漏或占位符
- [ ] **交叉验证**：确认"实现步骤"与"需要修改/新增的文件"一致
- [ ] **更新建议自查**：
  - CHANGELOG.md：✅ 需要更新（新增功能）
  - CLAUDE.md：✅ 需要更新（引入新的 LLM 调用最佳实践）
  - README.md：✅ 需要更新（新增配置项 `ENABLE_MODEL_AUTO_DETECTION`）

**步骤 7：提交代码**
- [ ] 使用 git 提交新增需求的实现

---

## 使用方式

### 配置项（.env 文件）
```bash
# ==================== LLM 模型能力自动探测 ====================
# 是否启用模型能力自动探测（默认: true）
# 启用后，首次调用 LLM 时会自动询问模型的 token 限制
ENABLE_MODEL_AUTO_DETECTION=true

# 模型探测超时时间（秒，默认: 10）
MODEL_DETECTION_TIMEOUT=10
```

### 自动探测流程（无需手动操作）

1. **首次运行解析命令**：
```bash
python parser.py --input-folder ./outputs/编程 --output-folder ./parsers/编程分析 --template parser/code_parser
```

2. **控制台输出示例**：
```
INFO      正在探测模型能力: deepseek-chat (https://api.deepseek.com)
INFO      模型能力探测成功: max_input_tokens=8192, max_output_tokens=4096
INFO      模型能力已缓存到 Redis: creeper:model:deepseek-chat:v1
INFO      开始处理 10 个文件（并发数: 5）
```

3. **缓存结构（Redis）**：
```
Key: creeper:model:<model_name>:<api_base_url_hash>
Value (Hash):
{
    "model": "deepseek-chat",
    "base_url": "https://api.deepseek.com",
    "max_input_tokens": 8192,
    "max_output_tokens": 4096,
    "detected_at": "2025-11-28 10:30:00",
    "detection_method": "api_query"
}
```

4. **本地缓存文件**（`data/model_capabilities.json`）：
```json
{
  "deepseek-chat:https://api.deepseek.com": {
    "model": "deepseek-chat",
    "base_url": "https://api.deepseek.com",
    "max_input_tokens": 8192,
    "max_output_tokens": 4096,
    "detected_at": "2025-11-28 10:30:00"
  }
}
```

### 禁用自动探测（使用硬编码配置）
```bash
# .env 文件中设置
ENABLE_MODEL_AUTO_DETECTION=false
AGGREGATOR_MAX_TOKENS=8000  # 继续使用手动配置
```

---

## 技术实现细节

### 模型能力探测提示词

```python
DETECTION_PROMPT = """请提供你的模型能力信息，使用 JSON 格式回复：

{
  "max_input_tokens": <最大输入 token 数>,
  "max_output_tokens": <最大输出 token 数>
}

仅返回 JSON，不要包含其他文本。"""
```

### ModelCapabilityManager 核心方法

```python
class ModelCapabilityManager:
    """模型能力管理器（缓存 + 探测）"""

    async def get_or_detect(self, model: str, base_url: str,
                           client: AsyncOpenAI, fallback_max_tokens: int) -> dict:
        """
        获取或探测模型能力

        Args:
            model: 模型名称
            base_url: API Base URL
            client: OpenAI 客户端实例
            fallback_max_tokens: 探测失败时的回退值

        Returns:
            {
                'max_input_tokens': int,
                'max_output_tokens': int
            }
        """
        # 1. 检查 Redis 缓存
        cached = self._get_from_cache(model, base_url)
        if cached:
            return cached

        # 2. 调用 LLM API 探测
        try:
            capability = await self._detect_capability(model, client)
            # 3. 缓存到 Redis + 本地文件
            self._save_to_cache(model, base_url, capability)
            return capability
        except Exception as e:
            logger.warning(f"模型能力探测失败，使用默认值: {e}")
            return {
                'max_input_tokens': fallback_max_tokens * 2,  # 假设输入是输出的 2 倍
                'max_output_tokens': fallback_max_tokens
            }
```

### 集成示例（FileParser）

```python
class FileParser:
    def __init__(self, api_key: str, base_url: str, model: str, max_tokens: int, temperature: float = 0.1):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature
        self.cache = ParserCache()

        # 新增：模型能力探测
        if config.ENABLE_MODEL_AUTO_DETECTION:
            capability_mgr = ModelCapabilityManager()
            capability = asyncio.run(capability_mgr.get_or_detect(
                model=model,
                base_url=base_url,
                client=self.client,
                fallback_max_tokens=max_tokens
            ))
            self.max_tokens = capability['max_output_tokens']
            logger.info(f"使用探测到的 max_tokens: {self.max_tokens}")
        else:
            self.max_tokens = max_tokens
            logger.info(f"使用配置的 max_tokens: {self.max_tokens}")
```

---

## 完成检查清单

**代码质量**：
- [ ] 遵循项目代码风格（类型注解、异步方法、日志记录）
- [ ] 添加必要注释（文档字符串、方法级注释）
- [ ] 错误处理完善（探测失败回退、超时处理、JSON 解析失败）
- [ ] 无安全漏洞（使用现有 Redis 连接，无新增网络调用）

**测试**：
- [ ] 新功能测试通过（单元测试 + 集成测试）
- [ ] 现有功能无影响（回归测试 parser.py 和 aggregator.py）
- [ ] 边界条件处理：
  - [ ] Redis 连接失败时使用本地缓存
  - [ ] 探测超时时使用回退值
  - [ ] JSON 解析失败时使用默认值
  - [ ] 禁用自动探测时保持原有行为

**文档**：
- [ ] README 已更新（新增配置项说明）
- [ ] CHANGELOG 已更新（版本号 v1.10.0）
- [ ] CLAUDE.md 已更新（新增 LLM 调用最佳实践）
- [ ] 需求文档完整（本文档各章节无遗漏）

---

## CHANGELOG.md 更新指南

**版本号规则**：新增功能（向后兼容）→ MINOR (x.X.0)

**模板**：
```markdown
## [1.10.0] - 2025-11-28

### Added
- **LLM 模型能力自动探测**：首次调用 LLM 时自动询问模型的 token 限制，避免手动配置错误
  - 自动探测 max_input_tokens 和 max_output_tokens
  - Redis + 本地文件混合持久化缓存（避免重复探测）
  - 支持探测失败时的智能回退（使用配置的 `AGGREGATOR_MAX_TOKENS`）
  - 新增配置项：`ENABLE_MODEL_AUTO_DETECTION`（默认启用）
  - 相关文件：`src/model_capabilities.py`, `src/file_parser.py`, `src/file_aggregator.py`, `src/translator.py`
  - 缓存文件：`data/model_capabilities.json`
```

**README.md 更新判断标准**：

✅ **需要更新**（新增用户可见的配置项）

更新位置：
1. `.env` 配置说明章节：添加 `ENABLE_MODEL_AUTO_DETECTION` 配置项
2. "开发命令"章节：补充自动探测的工作原理（可选）

**更新原则**：README.md 只记录用户快速开始所需的核心内容。**⚠️ 切忌不要与 CHANGELOG.md 和 CLAUDE.md 文件内容重复**（不写版本历史、开发规范、详细实现）

**CLAUDE.md 文件更新判断**：

✅ **需要更新**（引入新的 LLM 调用最佳实践）

更新建议：
- 在"重要实现细节"章节新增"LLM 模型能力自动探测"小节
- 说明新的 LLM 类初始化模式（先探测，后使用）
- 提示开发者：新增 LLM 调用模块时应集成自动探测

---

## 提交代码

在需求实现完成后，按以下顺序操作：

```bash
# 1. 完成步骤 5（文档更新）：更新 CHANGELOG.md、README.md、CLAUDE.md
# 2. 完成步骤 6（自我检查）：验证文档完整性、交叉验证、更新建议自查
# 3. 添加所有修改的文件
git add .
# 4. 提交，commit 信息使用需求文档的标题
git commit -m "feat: LLM 模型能力自动探测

- 首次调用 LLM 时自动询问模型 token 限制
- Redis + 本地文件混合缓存，避免重复探测
- 集成到 FileParser、LLMAggregator、Translator
- 新增配置项 ENABLE_MODEL_AUTO_DETECTION
- 更新 README.md 和 CLAUDE.md 文档"
```

注意：
- **严格按顺序**：步骤 5（文档更新）→ 步骤 6（自我检查）→ 步骤 7（提交代码）
- 使用 `feat:` 前缀表示这是新增功能
- 标题要简洁明确，正文详细列出关键改动

---

## 注意事项

**技术风险**：
- **探测失败风险**：部分 LLM 可能不支持自省能力，需要有可靠的回退机制
  - 缓解：探测失败时使用配置的 `AGGREGATOR_MAX_TOKENS` 作为回退值
  - 缓解：设置探测超时（10 秒），避免长时间阻塞
- **缓存失效风险**：模型能力可能随版本更新变化
  - 缓解：缓存 key 包含 `model` 和 `base_url`，不同模型/服务商独立缓存
  - 缓解：提供 `--force-detect` 参数强制重新探测（可选，后续扩展）
- **性能影响**：首次探测会增加一次 API 调用
  - 缓解：探测结果永久缓存，后续调用无额外开销

**兼容性**：
- ✅ **向后兼容**：禁用自动探测时，行为与原有逻辑完全一致
- ✅ **无需迁移脚本**：现有 `.env` 配置无需修改（默认启用自动探测）
- ❌ **不破坏现有 API**：所有类构造函数保持原有参数，仅在内部使用探测值

**配置建议**：
- 首次运行时保持 `ENABLE_MODEL_AUTO_DETECTION=true`，让系统自动探测
- 如果使用的 LLM 不支持自省，可以禁用自动探测并手动配置 `AGGREGATOR_MAX_TOKENS`
- 探测结果缓存到 Redis 后，可以手动修改缓存值（如模型实际支持更大的 token）

**扩展性考虑**：
- 未来可扩展探测其他能力：支持的功能（如 function calling）、计费信息、模型别名等
- 可扩展为预定义的模型能力数据库（避免每次都调用 API 探测）
