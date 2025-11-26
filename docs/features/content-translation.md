# 内容智能翻译 - 需求文档

> 生成时间: 2025-11-26
> 基于项目: Creeper 网页爬虫工具
> 技术栈: Python 3.8+ + DeepSeek API + asyncio

---

## 项目概况

**技术栈**: Python 3.8+ + asyncio + Playwright + Redis + DeepSeek API
**架构模式**: 模块化分层架构 (parser/fetcher/storage/dedup/cookie/translator)
**代码风格**:
- 中文注释和日志
- 使用 dataclass 定义数据结构
- 统一的日志记录器
- 完善的错误处理

**现有内容处理流程**:
```
爬取网页 → Trafilatura提取 → ContentCleaner清洗 → StorageManager保存
```

**问题**:
- 英文网页的标题、摘要、正文保存为英文
- 不利于中文用户阅读和检索
- 缺少内容智能处理能力

---

## 改动点

### 要实现什么

**核心功能 1: 语言自动检测**
- 检测网页内容的主要语言(英文/中文/其他)
- 使用轻量级语言检测库 `langdetect`
- 仅对英文内容触发翻译

**核心功能 2: DeepSeek API 集成**
- 集成 DeepSeek-V3.1 模型进行翻译
- 支持批量翻译(标题、摘要、正文)
- 异步 API 调用,不阻塞爬取流程
- 完善的错误处理和重试机制

**核心功能 3: 智能翻译策略**
- 仅翻译英文内容,保留中文内容
- 支持配置启用/禁用翻译功能
- 翻译失败时保留原文,不中断流程
- 翻译结果缓存(避免重复翻译)

**核心功能 4: 翻译范围配置**
- 标题 (title): 翻译网页标题
- 摘要 (description): 翻译页面描述
- 正文 (content): 翻译完整 Markdown 内容
- 元数据 (author): 翻译作者名等元信息

### 与现有功能的关系

**依赖现有模块**:
- `src/fetcher.py` / `src/async_fetcher.py` - 在爬取后调用翻译
- `src/storage.py` - 保存翻译后的内容
- `src/config.py` - 添加翻译相关配置
- `WebPage` dataclass - 扩展字段存储翻译结果

**集成位置**:
- `src/async_fetcher.py:fetch()` - 爬取后调用翻译 (第 163 行之后)
- `src/fetcher.py:fetch()` - 同步版本集成 (第 129 行之后)
- `src/storage.py:_generate_markdown()` - 保存翻译后内容 (第 89-120 行)

### 新增依赖

- `openai` - OpenAI 兼容的 API 客户端 (DeepSeek 使用 OpenAI SDK)
- `langdetect` - 语言检测库
- `tiktoken` (可选) - Token 计数,控制成本

---

## 实现方案

### 需要修改的文件

```
src/config.py              # 添加 DeepSeek API 配置
src/fetcher.py             # 同步模式集成翻译
src/async_fetcher.py       # 异步模式集成翻译
.env.example               # 添加配置示例
requirements.txt           # 添加新依赖
```

### 需要新增的文件

```
src/translator.py          # 用途: 翻译模块(语言检测+DeepSeek API)
tests/test_translator.py   # 用途: 翻译功能测试
```

---

## 实现方案

### 步骤 1: 安装依赖

**添加到 `requirements.txt`**:
```
openai>=1.0.0              # DeepSeek 使用 OpenAI SDK
langdetect>=1.0.9          # 语言检测
tiktoken>=0.5.0            # Token 计数(可选)
```

**安装命令**:
```bash
pip install openai langdetect tiktoken
```

### 步骤 2: 创建翻译模块

**新建 `src/translator.py`**:

- [ ] 实现 `Translator` 类
- [ ] 实现 `detect_language()` - 检测内容语言
- [ ] 实现 `translate()` - 调用 DeepSeek API 翻译
- [ ] 实现 `translate_batch()` - 批量翻译多个字段
- [ ] 添加翻译缓存机制(使用 Redis)
- [ ] 添加错误处理和重试逻辑

**核心方法签名**:
```python
class Translator:
    """DeepSeek 翻译器"""

    def __init__(self, api_key: str, base_url: str, model: str = "deepseek-chat"):
        """初始化翻译器"""
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def detect_language(self, text: str) -> str:
        """检测文本语言 (en/zh/other)"""
        pass

    async def translate(self, text: str, source_lang: str = "en", target_lang: str = "zh") -> str:
        """异步翻译单个文本"""
        pass

    async def translate_webpage(self, page: WebPage) -> WebPage:
        """翻译网页对象(标题、摘要、正文、元数据)"""
        pass
```

**实现要点**:

1. **语言检测** (使用 `langdetect`):
```python
from langdetect import detect, LangDetectException

def detect_language(self, text: str) -> str:
    """检测文本语言"""
    if not text or len(text.strip()) < 10:
        return "unknown"

    try:
        lang = detect(text)
        # 简化为 en/zh/other
        if lang in ['en', 'zh-cn', 'zh-tw']:
            return 'zh' if lang.startswith('zh') else 'en'
        return 'other'
    except LangDetectException:
        return "unknown"
```

2. **DeepSeek API 调用**:
```python
async def translate(self, text: str, source_lang: str = "en", target_lang: str = "zh") -> str:
    """异步翻译"""
    if not text or not text.strip():
        return text

    # 检查语言,中文内容不翻译
    detected_lang = self.detect_language(text)
    if detected_lang == target_lang:
        logger.info("内容已是目标语言,跳过翻译")
        return text

    # 构建提示词
    prompt = f"""请将以下{source_lang}文本翻译成{target_lang}:

{text}

要求:
1. 保持原文的 Markdown 格式
2. 专业术语保持准确
3. 语句通顺自然
4. 仅返回翻译结果,不要添加额外说明"""

    try:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的翻译助手,擅长将英文技术文档翻译成中文。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # 降低随机性,提高翻译稳定性
            max_tokens=8000   # 控制输出长度
        )

        translated = response.choices[0].message.content.strip()
        logger.info(f"翻译成功: {len(text)} 字符 → {len(translated)} 字符")
        return translated

    except Exception as e:
        logger.error(f"翻译失败: {e}")
        return text  # 失败时返回原文
```

3. **批量翻译网页对象**:
```python
async def translate_webpage(self, page: WebPage) -> WebPage:
    """翻译网页对象"""
    # 1. 检测正文语言
    content_lang = self.detect_language(page.content)

    if content_lang != "en":
        logger.info(f"内容非英文({content_lang}),跳过翻译")
        return page

    logger.info(f"检测到英文内容,开始翻译...")

    # 2. 并发翻译多个字段
    tasks = []

    if config.TRANSLATE_TITLE and page.title:
        tasks.append(("title", self.translate(page.title)))

    if config.TRANSLATE_DESCRIPTION and page.description:
        tasks.append(("description", self.translate(page.description)))

    if config.TRANSLATE_CONTENT and page.content:
        tasks.append(("content", self.translate(page.content)))

    if config.TRANSLATE_METADATA and page.author:
        tasks.append(("author", self.translate(page.author)))

    # 3. 等待所有翻译完成
    results = {}
    for field_name, task in tasks:
        try:
            results[field_name] = await task
        except Exception as e:
            logger.error(f"翻译 {field_name} 失败: {e}")
            results[field_name] = getattr(page, field_name)  # 保留原文

    # 4. 更新 WebPage 对象
    page.title = results.get("title", page.title)
    page.description = results.get("description", page.description)
    page.content = results.get("content", page.content)
    page.author = results.get("author", page.author)

    return page
```

4. **Redis 缓存翻译结果** (可选优化):
```python
def _get_cache_key(self, text: str) -> str:
    """生成缓存 key"""
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    return f"creeper:translation:{text_hash}"

async def translate_with_cache(self, text: str) -> str:
    """带缓存的翻译"""
    cache_key = self._get_cache_key(text)

    # 尝试从 Redis 读取
    cached = self.redis.get(cache_key)
    if cached:
        logger.info("使用缓存的翻译结果")
        return cached.decode('utf-8')

    # 调用 API 翻译
    translated = await self.translate(text)

    # 保存到 Redis (7 天过期)
    self.redis.setex(cache_key, 7 * 86400, translated)

    return translated
```

### 步骤 3: 扩展配置

**修改 `src/config.py`**:

- [ ] 添加翻译配置项:
```python
# 翻译配置
ENABLE_TRANSLATION = os.getenv('ENABLE_TRANSLATION', 'false').lower() == 'true'
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

# 翻译范围
TRANSLATE_TITLE = os.getenv('TRANSLATE_TITLE', 'true').lower() == 'true'
TRANSLATE_DESCRIPTION = os.getenv('TRANSLATE_DESCRIPTION', 'true').lower() == 'true'
TRANSLATE_CONTENT = os.getenv('TRANSLATE_CONTENT', 'true').lower() == 'true'
TRANSLATE_METADATA = os.getenv('TRANSLATE_METADATA', 'false').lower() == 'true'

# 翻译缓存
TRANSLATION_CACHE_ENABLED = os.getenv('TRANSLATION_CACHE_ENABLED', 'true').lower() == 'true'
TRANSLATION_CACHE_EXPIRE_DAYS = int(os.getenv('TRANSLATION_CACHE_EXPIRE_DAYS', 7))
```

**修改 `.env.example`**:

- [ ] 添加配置示例:
```bash
# ==================== 翻译配置 ====================
# 是否启用翻译功能
ENABLE_TRANSLATION=false

# DeepSeek API 配置
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 翻译范围(选择性翻译)
TRANSLATE_TITLE=true              # 翻译标题
TRANSLATE_DESCRIPTION=true        # 翻译摘要
TRANSLATE_CONTENT=true            # 翻译正文
TRANSLATE_METADATA=false          # 翻译元数据(作者等)

# 翻译缓存(避免重复翻译,节省费用)
TRANSLATION_CACHE_ENABLED=true
TRANSLATION_CACHE_EXPIRE_DAYS=7
```

### 步骤 4: 集成到爬虫

**修改 `src/async_fetcher.py`**:

- [ ] 在 `__init__()` 初始化翻译器:
```python
def __init__(self, use_playwright=True, concurrency=5, cookie_manager=None):
    # ... 现有代码

    # 初始化翻译器
    self.translator = None
    if config.ENABLE_TRANSLATION and config.DEEPSEEK_API_KEY:
        from src.translator import Translator
        self.translator = Translator(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
            model=config.DEEPSEEK_MODEL
        )
        logger.info("翻译功能已启用 (DeepSeek-V3.1)")
```

- [ ] 在 `fetch()` 方法中调用翻译:
```python
async def fetch(self, url: str, retry_count: int = 0) -> WebPage:
    """异步爬取网页"""
    async with self.semaphore:
        # ... 现有爬取逻辑

        # 爬取成功后,调用翻译
        if page.success and self.translator:
            try:
                page = await self.translator.translate_webpage(page)
            except Exception as e:
                logger.error(f"翻译失败(保留原文): {e}")
                # 不影响爬取流程,继续

        return page
```

**同样修改 `src/fetcher.py`** (同步版本):

- [ ] 使用同步 API 调用:
```python
# 同步版本需要使用 OpenAI 的同步接口
response = self.client.chat.completions.create(...)  # 同步调用
```

### 步骤 5: 更新 WebPage 数据结构(可选)

**修改 `src/fetcher.py` 中的 `WebPage` dataclass**:

- [ ] 添加翻译标记字段:
```python
@dataclass
class WebPage:
    # ... 现有字段
    translated: bool = False           # 是否已翻译
    original_language: str = "unknown" # 原始语言
```

### 步骤 6: 测试

- [ ] **单元测试 - 语言检测**:
```python
def test_detect_language():
    translator = Translator(api_key="test", base_url="test")

    assert translator.detect_language("Hello World") == "en"
    assert translator.detect_language("你好世界") == "zh"
```

- [ ] **单元测试 - API 调用**:
```python
async def test_translate():
    translator = Translator(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )

    result = await translator.translate("Hello World", "en", "zh")
    assert "你好" in result or "世界" in result
```

- [ ] **集成测试 - 完整流程**:
```bash
# 1. 设置环境变量
export ENABLE_TRANSLATION=true
export DEEPSEEK_API_KEY=sk-xxx

# 2. 爬取英文网页
python creeper.py tests/test_input.md

# 3. 检查输出文件是否为中文
cat output/xxx.md  # 应该看到中文标题和内容
```

- [ ] **回归测试**:
```bash
# 禁用翻译,确保不影响原有功能
export ENABLE_TRANSLATION=false
python creeper.py tests/test_input.md
```

### 步骤 7: 文档更新

- [ ] 更新 `README.md`:
```markdown
## ✨ 特性

- 🌐 **智能翻译**: DeepSeek API 自动将英文内容翻译为中文
  - 自动检测语言,仅翻译英文内容
  - 支持标题、摘要、正文全方位翻译
  - 翻译结果缓存,节省 API 费用
  - 可配置启用/禁用

## 🚀 快速开始

### 4. 配置翻译功能(可选)

如果需要自动翻译英文网页:

```bash
# 编辑 .env 文件
ENABLE_TRANSLATION=true
DEEPSEEK_API_KEY=sk-your-api-key-here

# 获取 DeepSeek API Key:
# 访问 https://platform.deepseek.com/
```

### 使用示例

```bash
# 爬取英文网页,自动翻译为中文
python creeper.py input.md  # 翻译功能在 .env 中启用后自动生效
```
```

- [ ] 更新 `CHANGELOG.md`:
```markdown
## [1.4.0] - 2025-11-26

### Added
- 🌐 **智能翻译功能**: 集成 DeepSeek-V3.1 API
  - 自动检测英文内容并翻译为中文
  - 支持标题、摘要、正文、元数据翻译
  - 翻译结果 Redis 缓存(7天)
  - 相关文件: `src/translator.py`
  - 新增依赖: `openai>=1.0.0`, `langdetect>=1.0.9`

### Changed
- 🔧 扩展 `WebPage` 数据结构,添加翻译标记字段
- ⚙️ 新增配置项: `ENABLE_TRANSLATION`, `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`
- 📋 新增翻译范围配置: `TRANSLATE_TITLE`, `TRANSLATE_CONTENT` 等

### Technical
- 使用 OpenAI SDK 兼容 DeepSeek API
- 语言检测使用 `langdetect` 库
- 异步 API 调用,不阻塞爬取流程
- 翻译失败时保留原文,不中断流程
```

---

## 使用方式

### 配置翻译功能

**编辑 `.env` 文件**:
```bash
# 启用翻译
ENABLE_TRANSLATION=true

# DeepSeek API 配置
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 翻译范围
TRANSLATE_TITLE=true
TRANSLATE_DESCRIPTION=true
TRANSLATE_CONTENT=true
TRANSLATE_METADATA=false
```

### 获取 DeepSeek API Key

1. 访问 https://platform.deepseek.com/
2. 注册账号并登录
3. 进入 API Keys 页面
4. 创建新 API Key
5. 复制 API Key 到 `.env` 文件

### 运行爬虫

```bash
# 启用翻译后,正常运行即可
python creeper.py input.md

# 英文内容会自动翻译为中文
```

### 查看翻译结果

生成的 Markdown 文件会包含翻译后的中文内容:

```markdown
# Python 基础教程 (原标题: Python Basics Tutorial)

> 📅 **爬取时间**: 2025-11-26 22:30:00
> 🔗 **来源链接**: https://example.com/python-basics
> 📝 **网页描述**: 这是一个全面的 Python 基础教程...
> 🌐 **原始语言**: English
> 🔄 **已翻译**: 是

---

# 正文内容(已翻译为中文)

Python 是一门强大的编程语言...
```

---

## 完成检查清单

**代码质量**:
- [ ] 遵循项目代码风格(中文注释)
- [ ] 添加必要的文档字符串
- [ ] 错误处理完善(API 失败、网络超时)
- [ ] API Key 安全存储(不提交到 Git)

**功能实现**:
- [ ] 语言检测准确
- [ ] DeepSeek API 调用成功
- [ ] 翻译质量满足要求
- [ ] 翻译缓存工作正常
- [ ] 配置开关生效

**测试**:
- [ ] 英文网页翻译成功
- [ ] 中文网页跳过翻译
- [ ] 翻译失败时保留原文
- [ ] 缓存功能正常
- [ ] 回归测试通过(禁用翻译时原功能正常)

**文档**:
- [ ] README 已更新(特性、使用说明)
- [ ] CHANGELOG 已更新
- [ ] .env.example 已更新
- [ ] 添加 API Key 获取指南

---

## CHANGELOG.md 更新指南

**版本号**: `1.4.0` (新增功能,向后兼容)

**更新位置**: `CHANGELOG.md` 文件顶部

**内容**:
```markdown
## [1.4.0] - 2025-11-26

### Added
- 🌐 **智能翻译功能**: 集成 DeepSeek-V3.1 API 自动翻译英文内容
  - 自动检测语言,仅翻译英文网页
  - 支持标题、摘要、正文、元数据翻译
  - 翻译结果 Redis 缓存(默认 7 天)
  - 可配置启用/禁用和翻译范围
  - 相关文件: `src/translator.py`
  - 新增依赖: `openai>=1.0.0`, `langdetect>=1.0.9`, `tiktoken>=0.5.0`

### Changed
- 🔧 扩展 `WebPage` 数据结构,添加翻译相关字段
- ⚙️ 新增配置项:
  - `ENABLE_TRANSLATION` - 启用翻译功能
  - `DEEPSEEK_API_KEY` - DeepSeek API 密钥
  - `DEEPSEEK_BASE_URL` - API 基础 URL
  - `DEEPSEEK_MODEL` - 模型名称(默认 deepseek-chat)
  - `TRANSLATE_TITLE/DESCRIPTION/CONTENT/METADATA` - 翻译范围
  - `TRANSLATION_CACHE_ENABLED` - 启用缓存
- 📋 爬取流程增强: 爬取 → 翻译 → 保存

### Technical
- 使用 OpenAI SDK 兼容 DeepSeek API
- 语言检测使用 `langdetect` 库(99%+ 准确率)
- 异步 API 调用,不阻塞爬取流程
- 翻译失败时保留原文,不中断流程
- Redis 缓存翻译结果,避免重复翻译
- 支持批量翻译优化性能
```

---

## 注意事项

**技术风险**:
- DeepSeek API 调用可能失败(网络、配额等) → 添加重试和降级
- 长文本翻译可能超时 → 分段翻译
- API 费用控制 → 使用缓存,避免重复翻译

**兼容性**:
- ✅ 向后兼容: 禁用翻译时行为不变
- ✅ 不破坏现有 API: 新增功能完全可选
- ✅ 默认行为: 翻译功能默认禁用,需手动开启

**性能影响**:
- API 调用增加爬取时间(每个网页约 2-5 秒)
- 使用缓存可大幅减少重复翻译
- 异步调用不阻塞其他 URL 爬取

**成本控制**:
- DeepSeek-V3.1 定价: ¥1/百万 tokens (输入), ¥2/百万 tokens (输出)
- 典型网页(5000字): 约 ¥0.001-0.002
- 启用缓存可节省 90%+ 费用

**安全建议**:
- API Key 存储在 `.env` 文件,不提交到 Git
- 在 `.gitignore` 中添加 `.env` 规则
- 使用环境变量管理敏感信息

---

## 实现优先级

**P0 (必须实现)**:
1. 创建 `src/translator.py` - 翻译核心模块
2. 实现语言检测和 DeepSeek API 调用
3. 集成到 `AsyncCrawler` 和 `SyncCrawler`
4. 添加配置项和环境变量

**P1 (重要功能)**:
1. 翻译缓存(Redis)
2. 错误处理和重试机制
3. 更新文档和示例
4. 测试覆盖

**P2 (可选优化)**:
1. 分段翻译长文本
2. 翻译进度显示
3. 翻译质量评估
4. 成本统计和监控

---

**开发建议**:
1. 先实现基础翻译功能,测试通过后再添加缓存
2. 使用小文本测试 API 调用,确保正确后再处理长文本
3. 充分测试错误处理(API 失败、网络超时等)
4. 注意 API Key 安全,不要提交到代码仓库
5. 建议先在本地测试,确认功能正常后再推送

---

**成本估算**:
- 测试阶段: 约 10-20 个网页,费用 < ¥0.1
- 日常使用: 100 个网页/天,费用约 ¥0.1-0.2/天
- 启用缓存后: 费用可降低 90%+

---

**DeepSeek-V3.1 优势**:
- 国内可直接访问,无需科学上网
- 价格极低(¥1/百万 tokens)
- 中文翻译质量优秀
- 上下文窗口大(64K tokens)
- API 兼容 OpenAI,易于集成
