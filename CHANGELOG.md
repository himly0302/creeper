# Changelog

All notable changes to Creeper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.0] - 2025-12-08

### Changed
- **重大架构变更**：移除同步爬虫模式，统一使用异步模式
  - 删除 `SyncCrawler` 类和 `--sync` 选项
  - 移除 `src/fetcher.py`，统一使用 `AsyncWebFetcher`
  - 删除同步图片下载器，只保留 `AsyncImageDownloader`
  - 简化项目结构，减少代码维护成本
  - 相关文件：`creeper.py`, `src/cli_parser.py`, `src/base_crawler.py`, `src/image_downloader.py`

### Removed
- **功能**：同步爬虫模式
  - 原因：简化代码结构，专注优化异步模式性能
  - 影响：移除 `--sync` 参数，所有命令默认使用异步模式
  - 相关文件：删除 `src/fetcher.py`, `tests/image_downloader/test_sync_downloader.py`
- **CLI参数**：`--sync` 选项
  - 原因：同步模式已移除，参数不再需要
  - 替代方案：所有操作默认使用异步并发模式

### Fixed
- **事件循环冲突修复**：修复异步环境中模型能力探测因事件循环冲突而失败的问题
  - 新增 `async_get_or_detect()` 异步方法，用于在已有事件循环中调用
  - 同步方法增加事件循环检测保护，避免嵌套调用导致崩溃
  - 相关文件：`src/model_capabilities.py`, `src/translator.py`
- **模型能力探测调用修复**：修复 Translator 模块调用 ModelCapabilityManager.get_or_detect() 参数不匹配的问题
  - 修正错误的 `client` 和 `fallback_max_tokens` 参数为正确的 `api_key` 和 `timeout`
  - 移除错误的 `await` 关键字（该方法是同步的）
  - 相关文件：`src/translator.py`
- **重试机制并发优化**：修复重试等待期间阻塞并发槽的问题
  - 将重试逻辑移至信号量（semaphore）外部执行
  - 重试等待期间释放并发槽，允许其他任务继续执行
  - 避免递归调用导致的信号量嵌套获取问题
  - 提升并发爬取效率，日志输出更清晰有序
  - 相关文件：`src/async_fetcher.py`
- **图片下载器导入**：修复URL列表模式中的图片下载器导入错误
  - 将 ImageDownloader 替换为 AsyncImageDownloader
  - 恢复 --with-images 参数在URL列表模式下的功能
  - 相关文件：`src/url_list_mode.py`
- **维基百科图片下载**：修复维基百科图片因HEAD请求被阻止而下载失败的问题
  - 添加User-Agent头部避免被反爬虫机制识别
  - 实现HEAD请求失败时fallback到GET请求的机制
  - 增强Content-Type验证逻辑，支持多层验证
  - 相关文件：`src/image_downloader.py`
- **内容质量检查增强**：增强反爬虫页面识别机制，处理Bloomberg等网站的验证页面
  - 扩展错误指示词列表，新增9个中英文反爬虫关键词
  - 支持订阅页面、技术错误页面的识别
  - 提高内容质量检查的覆盖面和准确性
  - 相关文件：`src/async_fetcher.py`
- **BBC图片下载优化**：修复BBC图片下载超时问题，提供明确的错误信息
  - 增强异常处理机制，提供详细的错误类型和信息
  - 添加已知问题域名快速失败机制，避免长时间等待
  - 优化超时配置，分离连接超时和读取超时
  - 解决BBC图片服务器aiohttp连接兼容性问题
  - 相关文件：`src/image_downloader.py`
- **历史数据清理**：清理遗留的反爬虫验证页面文件
  - 删除 `outputs/中国/中美关税/bloomberg.md` 错误文件
  - 文件包含反爬虫验证内容而非实际新闻内容
  - 当前代码已有内容质量检查机制防止类似问题
  - 相关文件：删除 `outputs/中国/中美关税/bloomberg.md`
- **文件覆盖**：修复异步保存模式下的文件覆盖问题
  - 改用网页标题作为文件名，而不是H2标题
  - 确保同一H2下的多个URL保存到不同文件
  - 相关文件：`src/storage.py`
- **属性错误**：修复 StorageManager 缺少 stats 属性的问题
  - 在 StorageManager.__init__ 中初始化 stats 属性
  - 修复了所有保存操作失败的问题
  - 相关文件：`src/storage.py`
- **导入错误**：修复删除同步版本后的 WebPage 类导入问题
  - 将 WebPage 类定义移到 async_fetcher.py
  - 更新所有模块的导入路径
  - 统一使用异步保存方法
  - 相关文件：`src/async_fetcher.py`, `src/url_list_mode.py`, `src/storage.py`, `creeper.py`

## [Unreleased]

### Changed
- **架构**：移除同步爬虫模式，统一使用异步模式
  - 删除 `SyncCrawler` 类和 `--sync` 选项
  - 移除 `src/fetcher.py`，统一使用 `AsyncWebFetcher`
  - 删除同步图片下载器，只保留 `AsyncImageDownloader`
  - 简化项目结构，减少代码维护成本
  - 相关文件：`creeper.py`, `src/cli_parser.py`, `src/base_crawler.py`, `src/image_downloader.py`

### Removed
- **功能**：同步爬虫模式
  - 原因：简化代码结构，专注优化异步模式性能
  - 影响：移除 `--sync` 参数，所有命令默认使用异步模式
  - 相关文件：删除 `src/fetcher.py`, `tests/image_downloader/test_sync_downloader.py`
- **CLI参数**：`--sync` 选项
  - 原因：同步模式已移除，参数不再需要
  - 替代方案：所有操作默认使用异步并发模式

### Added
- **CLI**：新增 `--with-images` 参数，在 `--urls` 模式下提取页面图片链接
  - 必须配合 `--urls` 使用，输出 JSON 中新增 `images` 字段
  - 相关文件：`src/cli_parser.py`, `src/url_list_mode.py`, `creeper.py`

### Fixed
- **内容验证**：修复维基百科等网站爬取失败问题
  - 优化403状态码处理，对维基百科等网站更宽松
  - 调整内容质量检查逻辑，对知名内容网站使用更宽松标准
  - 相关文件：`src/fetcher.py`, `src/async_fetcher.py`

### Changed
- **配置系统**：新增可配置的特殊网站处理机制
  - 用户可配置需要宽松处理的网站列表（PERMISSIVE_DOMAINS）
  - 可配置特定网站允许的HTTP状态码（PERMISSIVE_STATUS_CODES）
  - 可配置内容质量检查规则（PERMISSIVE_CONTENT_RULES）
  - 默认支持维基百科、GitHub、Stack Overflow等知名网站
  - 相关文件：`src/config.py`, `src/fetcher.py`, `src/async_fetcher.py`, `.env.example`
- **CLI**：新增 --urls 参数支持直接输入URL列表
  - 接受逗号分隔的URL，输出JSON格式结构化数据到控制台
  - 每次强制重新查询（类似 --force 行为）
  - 支持异步并发处理，提升效率
  - 相关文件：`src/url_list_mode.py`, `src/cli_parser.py`, `creeper.py`

### Fixed
- **内容验证优化**：修复"does not exist"错误指示词误判问题
  - 移除过于宽泛的"does not exist"指示词，避免误判正常技术文档
  - 保留更精确的错误指示词如"does not exist, or no longer exists"
  - 移除"subscribe"、"subscription"、"login"、"sign in"等常见功能性词汇
  - 相关文件：`src/async_fetcher.py`, `src/fetcher.py`
- **依赖支持**：安装Brotli库支持静态爬取brotli压缩内容
  - 解决静态爬取失败问题："Can not decode content-encoding: brotli (br)"
  - 提升对现代网站压缩格式的兼容性
  - 相关文件：requirements.txt (通过pip install brotli)
- **内容验证**：修复"javascript"错误指示词误判问题
  - 将过于宽泛的"javascript"指示词改为更精确的"请确保您的浏览器支持javascript"
  - 将"enable javascript"改为"please enable javascript"避免误判正常脚本
  - 同步和异步版本均已修复
  - 改进错误信息显示，提供详细的失败原因
  - 相关文件：`src/async_fetcher.py`, `src/fetcher.py`
- **图片下载优化**：智能图片过滤机制，只下载内容清洗后仍然存在的图片
  - 调整执行顺序：先内容清洗，再提取和下载图片
  - 双重验证机制：基于最终内容的图片引用验证
  - 相关文件：`src/storage.py`, `src/image_downloader.py`, `src/async_image_downloader.py`

### Fixed
- **内容验证增强**：增强错误页面过滤，同时检查标题和内容
  - 修复 `_is_valid_content()` 只检查内容不检查标题的问题
  - 添加 `title` 参数，同时验证标题中的错误指示词
  - 解决错误信息仅在标题中出现导致页面被错误保存的问题
  - 相关文件：`src/fetcher.py`, `src/async_fetcher.py`
- **保存功能错误**：修复 Markdown 生成方法缺少 return 语句导致文件保存失败
  - 修复 `_generate_markdown` 和 `_generate_markdown_async` 方法缺少返回语句
  - 恢复完整的 Markdown 构建逻辑和文件保存功能
  - 相关文件：`src/storage.py`
- **配置错误**：修复 CookieManager 初始化参数不匹配问题
- **内容质量控制**：修复静态爬取模式下错误页面被保存的问题
  - 在静态爬取成功分支中添加内容质量验证逻辑
  - 过滤404错误页面、页面不存在提示等低质量内容
  - 增强英文错误内容过滤，添加"does not exist"等关键错误指示词
  - 清理Redis缓存中的历史错误页面数据
  - 完成深度问题跟踪和多次清理工作
  - 相关文件：`src/fetcher.py`, `src/async_fetcher.py`
  - 移除已弃用的 `storage_backend`, `cookies_file`, `format` 参数
  - 统一使用 Redis 存储模式，移除文件存储支持
  - 修复方法调用：使用 `save()` 替代 `set_cookies()`
  - 相关文件：`creeper.py`
- **API 错误**：修复 DedupManager 缺少关键方法问题
  - 添加 `test_connection()` 方法用于 Redis 连接健康检查
  - 添加 `close()` 方法用于资源清理和连接关闭
  - 修复同步爬虫、异步爬虫、交互式登录功能崩溃
  - 相关文件：`src/dedup.py`
- **集成错误**：修复 CookieManager 缺少网页爬取器集成方法问题
  - 添加 `get_cookies_for_url()` 方法支持精确和通配符域名匹配
  - 添加 `to_playwright_format()` 方法转换 cookie 格式
  - 添加 `add_cookies_from_requests()` 和 `add_cookies_from_playwright()` 方法
  - 添加 `set_cookies()` 方法用于覆盖设置 cookies
  - 修复静态爬取和动态渲染功能失效问题
  - 相关文件：`src/cookie_manager.py`
- **解析错误**：修复 Markdown 解析器 URL 重复提取问题
  - 修复正则表达式重复匹配 Markdown 链接导致 URL 数量翻倍
  - 改进 URL 提取逻辑：先处理 Markdown 链接，再处理普通 URL
  - 添加末尾标点符号清理功能，提高 URL 准确性
  - 修复解析结果从错误数量（8个）恢复到正确数量（4个）
  - 相关文件：`src/parser.py`
- **属性错误**：修复 CookieManager Redis 属性名称不一致问题
  - 修复 to_playwright_format() 方法中错误的 self.redis 属性引用
  - 统一使用 self.redis_client 属性名称，保持与初始化和其他方法一致
  - 修复动态渲染时无法正确转换 Cookie 格式的问题
  - 相关文件：`src/cookie_manager.py`
- **内容过滤**：修复爬取器保存低质量和错误页面内容问题
  - 添加动态渲染内容长度验证和质量检查机制
  - 实现智能内容过滤，识别并排除404页面、反爬虫页面、订阅页面等
  - 添加中英文内容数量验证，确保内容质量达标
  - 清理已保存的错误文件，提高输出数据质量
  - 相关文件：`src/async_fetcher.py`, `src/fetcher.py`

### Removed
- **本地持久化功能**：简化为纯 Redis 模式，移除本地文件存储
  - 删除 ENABLE_LOCAL_PERSISTENCE 配置和相关逻辑
  - 简化 DedupManager、CookieManager、ModelCapabilityManager
  - 删除本地缓存文件和相关测试
  - 相关文件：`src/dedup.py`, `src/cookie_manager.py`, `src/model_capabilities.py`, `src/config.py`
- **文件夹内容 LLM 整合功能**：完全删除文件整合器及相关功能
  - 删除 aggregator.py 命令行工具
  - 删除 src/file_aggregator.py 核心模块
  - 删除 8 个整合模板文件
  - 删除相关测试和文档
  - 相关文件：`aggregator.py`, `src/file_aggregator.py`, `prompts/aggregator/`, `tests/file_aggregator/`
- **文件解析功能**：完全删除文件解析器及相关功能
  - 删除 parser.py 命令行工具
  - 删除 src/file_parser.py 核心模块
  - 删除 9 个解析模板文件
  - 删除相关测试和文档
  - 相关文件：`parser.py`, `src/file_parser.py`, `prompts/parser/`, `tests/file_parser/`

### Changed
- 📝 **解析模板全面优化**：增强所有 parser 模板的信息保留能力（基于 Gemini 反馈）

  **doc_parser.txt（文档解析）**：
  - 新增"忠实度最高"、"保留原始结构"、"忠实转录文件内容"约束
  - 新增"工作流模式"专用格式、"表格灵活性要求"
  - 将"最佳实践"和"注意事项"提升为独立二级标题

  **code_parser.txt（代码解析）**：
  - 新增"保留代码结构"、"完整提取代码细节"约束
  - 强调函数签名、算法步骤不能用"..."省略
  - 细化"注意事项"为性能限制、已知问题、最佳实践、兼容性要求

  **config_parser.txt（配置解析）**：
  - 新增"保留原始结构"、"完整转录配置内容"约束
  - 强调配置文件的实际内容必须完整转录（包括注释）

  **practical_parser.txt（实用指南）**：
  - 新增"保留所有数字和标准"约束（不能模糊化为"适量""若干"）
  - 强调时间、配比、温度等具体数值必须完整保留

  **humanities_parser.txt（人文艺术）**：
  - 新增"保留核心观点和论证"约束（不要简化为"作者认为..."）
  - 强调论证逻辑、引用原文、案例细节必须完整转录

  **local_parser.txt（本地资讯）**：
  - 新增"保留5W要素"约束（时间、地点、人物、事件、原因）
  - 强调地址、电话、费用等民生信息必须完整保留

  **history_parser.txt（历史内容）**：
  - 新增"保留时间线"、"保留因果关系"约束
  - 强调历史事件的前因后果、人物关系必须完整保留

  **international_parser.txt（国际资讯）**：
  - 新增"保留多方立场"约束（不能偏向某一方或合并观点）
  - 强调国家/组织名称、地缘关系、全球影响必须完整保留

  **entertainment_parser.txt（娱乐资讯）**：
  - 新增"保留作品信息"、"保留评价数据"约束
  - 强调票房、评分、排名等数据必须完整保留

  **共性改进**：
  - 所有模板新增"信息密度要保持在原文的 80% 以上"量化要求
  - 所有模板新增"这是单篇分析"约束（禁止整合多篇文章）
  - 所有模板新增"忠实度最高"约束（禁止假设、推测或脑补）

  相关文件：`prompts/parser/*.txt`（全部 9 个解析模板）

## [1.10.1] - 2025-11-28

### Fixed
- **LLM 模型能力探测**：修复在运行中的事件循环中调用 `asyncio.run()` 导致的错误
  - 将探测逻辑从 `__init__` 移至首次调用时（懒加载模式）
  - 使用 `@property` 装饰器提供 `max_tokens` 兼容性
  - 相关文件：`src/file_parser.py`, `src/file_aggregator.py`, `src/translator.py`

## [1.10.0] - 2025-11-28

### Added
- **LLM 模型能力自动探测**：首次调用 LLM 时自动询问模型的 token 限制，避免手动配置错误
  - 自动探测 `max_input_tokens` 和 `max_output_tokens`
  - Redis + 本地文件混合持久化缓存（避免重复探测）
  - 支持探测失败时的智能回退（使用配置的 `AGGREGATOR_MAX_TOKENS`）
  - 新增配置项：`ENABLE_MODEL_AUTO_DETECTION`（默认启用）、`MODEL_DETECTION_TIMEOUT`（默认 10 秒）
  - 相关文件：`src/model_capabilities.py`, `src/file_parser.py`, `src/file_aggregator.py`, `src/translator.py`
  - 缓存文件：`data/model_capabilities.json`

## [1.9.3] - 2025-11-28

### Fixed
- **LLM API 参数配置**：修复 `AGGREGATOR_MAX_TOKENS` 默认值超出 DeepSeek API 限制的问题
  - 默认值从 `64000` 调整为 `8000`（DeepSeek API 限制：[1, 8192]）
  - 相关文件：`src/config.py`, `.env.example`
- **错误处理逻辑**：修复 LLM API 调用失败后仍生成错误文件的问题
  - `parse_file()` 和 `aggregate()` 方法失败时抛出异常，而非返回错误字符串
  - 失败时不再生成包含错误信息的文件
  - 日志输出更准确（成功显示"✓ 已处理"，失败显示"✗ 处理失败"）
  - 相关文件：`src/file_parser.py`, `src/file_aggregator.py`

## [1.9.2] - 2025-11-28

### Added
- 📁 **项目目录约定**: 明确定义核心输出目录的用途和组织方式
  - `inputs/`: 爬虫输入文档地址文件夹（可按题材分类）
  - `outputs/`: 爬虫输出文档地址文件夹（注意：当前实际目录名为 `output/`）
  - `parsers/`: 解析文档存放文件夹（parser.py 一对一输出）
  - `aggregators/`: 融合文档存放文件夹（aggregator.py 多对一输出）
  - 更新 CLAUDE.md 和 README.md 添加目录约定说明
  - 更新 .gitignore 添加目录说明注释

### Changed
- 📝 **文档完善**: 在使用场景中补充目录约定的实际应用示例
  - 场景 1 使用 `inputs/` 存放输入文件
  - 场景 3 使用 `aggregators/` 存放整合文档
  - 场景 4 使用 `parsers/` 存放解析文档
- 🔧 **命令行示例更新**: 所有文档中的命令行示例更新为使用约定目录结构
  - 爬虫命令: `python creeper.py inputs/input.md`
  - 整合命令: `--output ./aggregators/code_summary.md`
  - 解析命令: `--input-folder ./outputs/编程 --output-folder ./parsers/编程分析`
  - 清理命令: `rm -rf output/* outputs/* parsers/* aggregators/* data/*.json`

## [1.9.1] - 2025-11-28

### Added
- 🆕 **题材类文件解析模板**: 新增 6 个专门用于文件解析的题材类提示词模板
  - `prompts/parser/humanities_parser.txt`：人文艺术内容分析（文化评论、哲学思考、社会观察）
  - `prompts/parser/practical_parser.txt`：实用指南提取（生活技巧、工作方法、学习技能）
  - `prompts/parser/local_parser.txt`：本地资讯分析（城市资讯、社区动态、民生服务）
  - `prompts/parser/history_parser.txt`：历史内容分析（历史事件、人物传记、历史研究）
  - `prompts/parser/international_parser.txt`：国际资讯分析（全球事件、外交关系、跨国议题）
  - `prompts/parser/entertainment_parser.txt`：娱乐资讯分析（影视音乐、游戏综艺、明星动态）
- 📊 **模板总数**: 现在共有 17 个提示词模板（8个整合类 + 9个解析类）

### Technical Details
- 所有题材类解析模板都遵循"一对一"原则（单篇文章分析）
- 禁止整合逻辑，不包含"合并已有内容"等语句
- 保持题材特色，提取各题材的核心关注点

## [1.9.0] - 2025-11-28

### Changed
- 📂 **提示词模板组织**: 重构 prompts 目录结构，区分解析和整合类模板
  - 新增 `prompts/parser/` 目录：存放文件解析类提示词（一对一输出）
  - 新增 `prompts/aggregator/` 目录：存放文件整合类提示词（多对一输出）
  - 移动现有 8 个整合模板到 `prompts/aggregator/`
  - 相关文件：`src/prompt_templates.py`, `parser.py`, `aggregator.py`

### Added
- 🆕 **文件解析模板**: 新增 3 个专用文件解析提示词模板
  - `prompts/parser/code_parser.txt`：代码文件解析（深度分析单个文件）
  - `prompts/parser/doc_parser.txt`：文档文件解析（结构化提取文档要点）
  - `prompts/parser/config_parser.txt`：配置文件解析（解析配置项和示例）
- 🔍 **模板查找增强**: `PromptTemplateManager` 支持递归扫描子目录
  - 支持简化路径：`--template code_parser`（自动在子目录中搜索）
  - 支持完整路径：`--template parser/code_parser`（精确匹配）
  - `--list-templates` 现在显示带子目录的完整路径（如 `parser/code_parser`）
  - 完全向后兼容，旧模板路径仍然可用

### Technical Details
- `PromptTemplateManager.list_templates()` 使用 `rglob()` 递归搜索所有 `.txt` 文件
- `PromptTemplateManager.get_template()` 优先尝试直接路径，失败后在子目录中搜索
- 模板路径格式：`subdir/template_name` 或 `template_name`（不含 `.txt` 扩展名）

## [1.8.0] - 2025-11-28

### Added
- 📄 **文件解析功能**: 支持文件夹批量解析，每个文件独立调用 LLM 处理并生成对应的输出文件
  - 通过 Redis 实现增量更新，仅处理新增或变更的文件（文件级缓存）
  - 支持自定义输出文件夹、提示词模板、文件扩展名过滤
  - 保持输入文件夹的相对路径结构，输出扩展名统一为 `.md`
  - 支持并发处理，默认并发数 5（可通过 `--concurrency` 调整）
  - 混合存储模式：Redis + 本地 JSON（`data/parser_cache.json`），防止缓存丢失
  - 相关文件：`src/file_parser.py`, `parser.py`, `prompts/file_parser.txt`
  - 新增命令：`python parser.py --input-folder <path> --output-folder <path> --template <name>`
  - 测试：`python parser.py --list-templates` 列出可用模板

### Technical Details
- 复用 `FileScanner` 进行文件扫描和哈希计算（MD5）
- 采用混合存储模式（Redis + 本地 JSON），启动时自动恢复缓存
- 支持异步并发处理，使用 `asyncio.Semaphore` 控制并发数
- 路径遍历防护：使用 `os.path.abspath()` 规范化路径，检查输出路径是否在允许范围内
- 缓存键格式：`creeper:parser:<md5(file_path)>`，存储文件哈希、解析时间、输出路径等元数据

## [1.7.0] - 2025-11-27

### Added
- 📷 **图片本地化存储**: 自动下载 Markdown 中的图片到本地，替换为相对路径
  - 支持同步和异步下载模式（兼容现有同步/异步爬虫）
  - 图片保存到 `output/<H1>/<H2>/images/` 目录
  - 支持图片格式：JPG, PNG, GIF, WebP, SVG
  - 图片去重机制（相同 URL 只下载一次）
  - 下载失败时保留原始 URL（不影响文档生成）
  - SSRF 防护：拒绝下载内网资源（localhost, 127.0.0.1, 192.168.*, 10.*, 172.*）
  - 文件大小限制：默认最大 10 MB（可配置）
  - 相关文件：`src/image_downloader.py`, `src/storage.py`, `src/config.py`
  - 新增配置：`DOWNLOAD_IMAGES`, `MAX_IMAGE_SIZE_MB`, `IMAGE_DOWNLOAD_TIMEOUT`
  - 测试文件：`tests/image_downloader/test_sync_downloader.py`, `tests/image_downloader/test_async_downloader.py`

## [1.6.4] - 2025-11-27

### Added
- 📝 **文件整合**: 新增技术教程文档专用整合提示词
  - 新增 `prompts/tutorial_merge.txt` 模板，专门用于技术教程、官网文档整合
  - 5 级优先级体系：操作步骤 > 配置说明 > 故障排查 > 高级用法 > 概念背景
  - 15+ 次强调"禁止精简内容"，要求保留 60-80% 源文档长度
  - 明确要求 100% 保留所有命令、代码示例、操作步骤
  - 8 项质量检查清单（含输出长度检查）
  - 相关文件：`prompts/tutorial_merge.txt`

### Changed
- 🧹 **清理脚本**: 增强 clean.sh 清理功能
  - 新增 `aggregators/` 目录的清理（删除所有聚合生成的文件）
  - 新增 `data/aggregator_cache.json` 的清理（聚合器缓存文件）
  - 更新清理步骤编号和提示信息
  - 相关文件：`clean.sh`

## [1.6.3] - 2025-11-27

### Fixed
- 🎯 **文件整合**: 优化聚合提示词质量，修复输出格式和内容质量问题
  - 代码总结提示词增强：深度分析架构设计、依赖关系、关键实现细节
  - 文档合并提示词增强：保留核心信息、智能去重、结构化输出
  - 修复 LLM 输出被 markdown 代码块包裹的问题（禁止 ` ```markdown ` 包裹）
  - 修复 LLM 臆造不存在文件路径的问题（强制使用实际文件路径）
  - 新增函数签名提取、输入输出说明、异常处理分析
  - 新增架构概览、技术栈详情、使用示例等结构化内容
  - 相关文件：`prompts/code_summary.txt`, `prompts/doc_merge.txt`

## [1.6.2] - 2025-11-27

### Fixed
- 🐛 **模块导入**: 修复 `src.file_aggregator` 模块缺失导致的 ModuleNotFoundError
  - 创建缺失的 `src/file_aggregator.py` 文件（包含 FileScanner, AggregatorCache, LLMAggregator）
  - 修复 `aggregator.py` 的命令行参数解析逻辑，使 `--list-templates` 可独立运行
  - 相关文件: `src/file_aggregator.py`, `aggregator.py`

## [1.6.1] - 2025-11-27

### Changed
- ⚙️ **配置分离**: 翻译功能和文件整合功能使用独立的 LLM API 配置
  - 翻译功能: `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`
  - 文件整合: `AGGREGATOR_API_KEY`, `AGGREGATOR_BASE_URL`, `AGGREGATOR_MODEL`
  - 两个功能可以使用不同的 API Key 或服务商
  - 相关文件: `src/config.py`, `.env.example`, `aggregator.py`

## [1.6.0] - 2025-11-27

### Added
- 🧩 **文件夹内容 LLM 整合**: 智能扫描文件夹并使用 LLM 整合内容
  - 递归扫描文件夹并读取文件内容
  - 支持增量更新(基于 Redis 缓存已处理文件)
  - 预设 3 种提示词模板(代码总结、文档合并、数据分析)
  - 自动调用 LLM API 生成整合文档
  - 支持自定义文件类型过滤(--extensions)
  - 混合持久化(Redis + 本地 JSON)
  - 新增配置: `AGGREGATOR_*` 系列配置项
  - 相关文件: `aggregator.py`, `src/file_aggregator.py`, `src/prompt_templates.py`
- 📚 **提示词模板系统**: 可扩展的 LLM 提示词管理
  - 支持 `prompts/` 目录下自定义 `.txt` 模板文件
  - 内置模板缓存机制
  - 通过 `--list-templates` 查看所有可用模板
- 🧪 **单元测试**: 新增文件扫描和模板管理测试
  - `tests/file_aggregator/test_file_scanner.py`
  - `tests/file_aggregator/test_aggregator_cache.py`

### Changed
- 📝 **文档更新**: 更新 README.md 添加文件整合功能使用说明
- ⚙️ **配置扩展**: .env.example 新增 AGGREGATOR_* 配置项
- 📂 **项目结构**: 新增 `prompts/` 和 `docs/features/` 目录

## [1.5.0] - 2025-11-27

### Added
- 💾 **本地持久化**: Redis 数据本地持久化功能 - 混合存储模式
  - 支持 Redis + 本地文件双写,确保数据不丢失
  - 每次操作同时写入 Redis 和 `data/dedup_cache.json`
  - 启动时自动从 JSON 文件恢复去重和 Cookie 数据
  - 支持定期同步 Redis 数据到本地 (可配置间隔)
  - 新增配置: `ENABLE_LOCAL_PERSISTENCE`, `DEDUP_CACHE_FILE`, `SYNC_INTERVAL_SECONDS`
  - 相关文件: `src/dedup.py`, `src/cookie_manager.py`, `src/config.py`
- 🧹 **清理脚本增强**: `clean.sh` 新增清理本地缓存文件功能
  - 自动删除 `data/dedup_cache.json` 和 `data/cookies_cache.json`

## [1.4.3] - 2025-11-26

### Fixed
- ⚡ **翻译性能优化**: 批量翻译减少API调用次数
  - 将多个字段(title/description/content)合并为一次LLM调用
  - 使用 `---FIELD_SEPARATOR---` 分隔符组合字段
  - API调用次数减少 50% (2-3次 → 1次)
  - 降低API成本,提升爬取速度
  - 失败时自动降级为逐个翻译
  - 相关文件: `src/translator.py:106-115`, `src/translator.py:180-234`
- 🐛 **依赖修复**: 安装 brotli 库解决 VS Code 文档爬取失败
  - 修复 "Can not decode content-encoding: brotli" 错误
  - 优化翻译日志,避免重复语言检测

## [1.4.2] - 2025-11-26

### Fixed
- 🐛 **日志可读性**: 异步并发时日志添加 URL 上下文标识
  - 使用 contextvars 实现异步上下文追踪
  - 自定义 logging.Filter 自动提取 URL 信息
  - 日志格式: `INFO [python] 开始爬取...`
  - 大幅提升并发日志的可读性和调试效率
  - 相关文件: `src/utils.py`, `src/async_fetcher.py`

## [1.4.1] - 2025-11-26

### Fixed
- 🐛 **文件名格式**: 修复翻译后文件名包含多余 Markdown 格式符号的问题
  - 清理翻译标题中的 `#` 符号和多余换行
  - 只使用第一行作为文件名
  - 文件名长度从 100+ 字符缩短至 20-30 字符
  - 相关文件: `src/translator.py:186-194`

## [1.4.0] - 2025-11-26

### Added
- 🌍 **内容自动翻译**: 支持将英文网页内容自动翻译为中文
  - 集成 DeepSeek API 实现高质量翻译
  - 使用 langdetect 自动检测语言,仅翻译英文内容
  - 支持翻译标题、摘要、正文和元数据
  - 可通过 `.env` 配置灵活控制翻译范围
  - 相关文件: `src/translator.py`
- 📋 新增翻译配置项:
  - `ENABLE_TRANSLATION`: 启用/禁用翻译功能
  - `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`: API 配置
  - `TRANSLATE_TITLE`, `TRANSLATE_DESCRIPTION`, `TRANSLATE_CONTENT`, `TRANSLATE_METADATA`: 选择性翻译

### Changed
- 🔧 `AsyncWebFetcher` 集成翻译器,爬取成功后自动翻译
- 📋 `WebPage` 数据类新增字段: `translated` (是否已翻译), `original_language` (原始语言)
- ⚙️ 翻译失败时保留原文,不影响爬取结果

### Technical
- 使用 OpenAI SDK 兼容 DeepSeek API
- 语言检测使用前 1000 字符,提高检测速度
- 翻译提示词优化,保持 Markdown 格式完整性
- 翻译参数: `temperature=0.3`, `max_tokens=64000`
- 翻译器仅在异步模式中可用(OpenAI SDK 为异步优先)

### Dependencies
- openai>=1.0.0 (兼容 DeepSeek API)
- langdetect>=1.0.9 (语言检测)
- tiktoken>=0.5.0 (Token 计数)

### Usage Example
```bash
# 1. 配置 .env 文件
ENABLE_TRANSLATION=true
DEEPSEEK_API_KEY=your-api-key-here

# 2. 运行爬虫(默认异步模式,自动翻译)
python creeper.py input.md

# 3. 英文内容将自动翻译为中文并保存
```

---

## [1.3.0] - 2025-11-26

### Changed
- 🔧 **代码重构**: 合并同步/异步 CLI 为统一入口
  - `creeper.py` 和 `creeper_async.py` 已合并为单一入口点 `creeper.py`
  - 默认使用异步模式,可通过 `--sync` 参数切换同步模式
  - 提取公共逻辑到基类,消除 220 行重复代码 (47.4%)
  - 统一参数解析和错误处理
  - 完全向后兼容,所有功能保留

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

### Migration Guide
**命令行迁移** (必需):
```bash
# v1.2.0 及之前
python creeper_async.py input.md

# v1.3.0+ 迁移后
python creeper.py input.md  # 功能完全相同,默认异步模式
```

**新增功能**:
```bash
# 使用同步模式
python creeper.py input.md --sync
```

---

## [1.2.0] - 2025-11-26

### Added
- 🌐 **交互式登录功能**: 使用 Playwright 打开浏览器让用户手动登录
  - 支持 `--login-url` 参数启动交互式登录
  - 登录完成后自动提取并保存 Cookie
  - 相关文件: `src/interactive_login.py`
- 💾 **Cookie Redis 存储**: Cookie 存储到 Redis 替代文件存储
  - 使用 Redis Hash 结构存储,按域名分组
  - 支持设置过期时间(默认 7 天)
  - 跨会话复用 Cookie
  - 相关文件: `src/cookie_manager.py`
- 🔄 **自动 Cookie 管理**: 登录一次,后续爬取自动使用

### Changed
- 🔧 `CookieManager` 支持可选的存储后端 ('file' 或 'redis')
- 📋 新增 CLI 参数: `--login-url <URL>`
- ⚙️ 新增配置项: `COOKIE_STORAGE`, `COOKIE_EXPIRE_DAYS`, `COOKIE_REDIS_KEY_PREFIX`, `INTERACTIVE_LOGIN_TIMEOUT`
- 🔀 `input_file` 参数变为可选(使用 `--login-url` 时不需要)

### Technical
- Cookie 在 Redis 中使用 `creeper:cookie:{domain}` 作为 Key
- 使用 HSET/HGETALL 操作 Cookie 数据
- Playwright 以非 headless 模式打开,等待用户操作
- 支持超时控制(默认 5 分钟)
- Cookie 自动从 Redis 加载,无需手动指定文件

### Migration Guide
**向后兼容**: 原有的 `--cookies-file` 参数仍然有效,文件存储模式不受影响。

如需切换到 Redis 存储模式:
1. 在 `.env` 中设置 `COOKIE_STORAGE=redis`
2. 使用 `--login-url` 进行首次登录
3. 后续爬取自动使用 Redis 中的 Cookie

---

## [1.1.0] - 2025-11-26

### Added
- 🍪 **Cookie 管理功能**: 支持 Cookie 的存储、加载和复用
- 🔐 **登录态保持**: 可爬取需要登录的网站内容
- 💾 **Cookie 持久化**: 支持 JSON 格式存储 Cookie
- 🔄 **自动 Cookie 提取**: 从请求响应中自动提取并保存 Cookie
- 📝 **Cookie 统计**: 提供 Cookie 管理的详细统计信息

### Changed
- 🔧 `WebFetcher` 和 `AsyncWebFetcher` 现在支持 `cookie_manager` 参数
- 📋 新增 CLI 参数: `--cookies-file` 和 `--save-cookies`

### Technical
- 新增 `src/cookie_manager.py` Cookie 管理模块
- 支持与 requests 和 Playwright 的 Cookie 互转
- Cookie 按域名分组存储
- 支持 Cookie 的精确匹配和父域匹配

---

## [1.0.0] - 2025-11-26

### Added
- 🚀 **异步并发处理**: 使用 asyncio + aiohttp 实现高性能并发爬取
- 🔄 **智能重试机制**: 指数退避算法,失败后自动重试(最多3次)
- ⚡ **性能提升**: 相比 MVP 版本速度提升约 40-50%
- 📊 **详细统计信息**: 成功率、耗时统计等
- 🎯 **可配置并发数**: 通过 `-c` 参数灵活控制并发数量

### Changed
- 💡 优化日志输出格式
- ⚡ 使用异步 Playwright 提升动态渲染性能
- 🔧 改进错误处理和异常捕获

### Fixed
- 🐛 修复部分网站 Brotli 压缩解码问题(自动降级到 Playwright)
- 🐛 优化内存使用,避免大量并发时的资源占用

### Technical
- 新增 `creeper_async.py` 异步并发版本
- 新增 `src/async_fetcher.py` 异步爬取模块
- 保留 `creeper.py` 同步版本作为备份
- 使用信号量(Semaphore)控制并发数

### Performance
- 测试数据(3个URL, 并发数3):
  - MVP 同步版本: ~28秒
  - V1.0 异步版本: ~16秒
  - 性能提升: ~43%

---

## [0.1.0] - 2025-11-26

### Added
- ✨ Markdown 文件解析功能,支持 H1/H2 层级结构
- ✨ 网页内容爬取功能(Trafilatura 静态爬取)
- ✨ Playwright 动态渲染自动降级
- ✨ Redis 去重机制,避免重复爬取
- ✨ 按层级目录自动生成文件结构
- ✨ 内容清洗,移除不可见字符和多余空白
- ✨ 反爬虫策略:随机 User-Agent、请求间隔
- ✨ 彩色日志输出和进度条展示
- ✨ 命令行参数支持(--force, --debug, --no-playwright)
- ✨ 失败 URL 自动保存到日志文件
- ✨ Python 虚拟环境支持,避免污染全局环境
- ✨ 一键初始化脚本(setup.sh / setup.bat)
- ✨ 清理脚本(clean.sh)便于测试
- 📝 完整的 README 和需求文档
- 📝 配置文件模板(.env.example)

### Technical
- 使用 Trafilatura 1.12+ 进行专业内容提取
- 使用 Playwright 1.51+ 处理动态页面
- 使用 Redis 6.4+ 实现高效去重
- 使用 colorlog 实现彩色日志
- 使用 tqdm 显示进度条
- 模块化设计:parser, fetcher, dedup, cleaner, storage

### Known Limitations (MVP)
- 仅支持单线程顺序执行
- 暂不支持 Cookie 管理
- 暂不支持图片本地下载
- 暂不支持代理池

---

## 版本说明

- **1.0.0**: 稳定版本,支持异步并发,生产环境可用
- **0.1.0**: MVP 版本,核心功能已实现,适合轻量使用

## 贡献者

- [@Claude] - 初始版本开发 & V1.0 异步并发实现
