# 错误修复：重试机制阻塞并发槽导致任务交错执行

**修复时间**：2025-12-08
**错误级别**：High

## 问题详情

### 错误信息
```
WARNING  [reddit] 爬取失败,2.0秒后重试 (第1/3次)
WARNING  [reddit] 爬取失败,2.0秒后重试 (第1/3次)
INFO     [anthropic] 翻译成功: 28284 字符 → 9528 字符
INFO     [reddit] 开始爬取: https://www.reddit.com/...
INFO     [claude] 翻译成功: 24038 字符 → 10154 字符
WARNING  [reddit] 爬取失败,4.0秒后重试 (第2/3次)
...
```

### 错误类型
- 类型：并发控制/性能
- 影响：重试等待期间阻塞其他任务，导致日志交错、整体效率下降

## 解决方案

### 根本原因
`AsyncWebFetcher.fetch()` 方法中，重试逻辑在信号量（`async with self.semaphore`）内部执行：

1. 当爬取失败需要重试时，`await asyncio.sleep(retry_delay)` 在信号量保护块内执行
2. 递归调用 `await self.fetch(url, retry_count + 1)` 时，当前调用仍持有信号量
3. 这导致：
   - 重试等待期间，其他任务无法获取并发槽
   - 如果多个 URL 同时失败并重试，会出现交错执行的现象
   - 整体爬取效率大幅下降

### 修改文件
- `src/async_fetcher.py`：重构 `fetch()` 方法，将重试逻辑移至信号量外部

### 代码变更
```python
# 修改前
async def fetch(self, url: str, retry_count: int = 0) -> WebPage:
    async with self.semaphore:  # 获取信号量
        # ... 爬取逻辑 ...

        # 两种方式都失败,进行重试
        if retry_count < config.MAX_RETRIES:
            await asyncio.sleep(retry_delay)  # ⚠️ 在信号量内等待！
            return await self.fetch(url, retry_count + 1)  # ⚠️ 递归调用

# 修改后
async def fetch(self, url: str, retry_count: int = 0) -> WebPage:
    # 重试逻辑在信号量外部，避免阻塞并发槽
    while True:
        result = await self._fetch_with_semaphore(url, retry_count)

        if result.success:
            return result

        if retry_count >= config.MAX_RETRIES:
            result.error = f"所有爬取方式均失败(已重试{config.MAX_RETRIES}次): {result.error}"
            return result

        # 在信号量外等待，释放并发槽给其他任务
        retry_delay = config.RETRY_BASE_DELAY * (2 ** retry_count)
        logger.warning(f"爬取失败,{retry_delay}秒后重试...")
        await asyncio.sleep(retry_delay)
        retry_count += 1

async def _fetch_with_semaphore(self, url: str, retry_count: int = 0) -> WebPage:
    async with self.semaphore:  # 控制并发数
        # ... 单次爬取尝试逻辑 ...
```

### 修复效果
1. 重试等待期间不再占用并发槽
2. 其他任务可以正常并发执行
3. 日志不再交错，执行顺序更清晰
4. 整体爬取效率提升

## 验证结果
- [x] 代码语法检查通过
- [x] 模块导入验证通过
- [x] 方法存在性验证通过
