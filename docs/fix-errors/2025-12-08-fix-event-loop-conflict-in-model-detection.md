# 错误修复：事件循环冲突导致模型能力探测失败

**修复时间**：2025-12-08
**错误级别**：Medium

## 问题详情

### 错误信息
```
WARNING  [anthropic] 模型能力探测失败，使用默认值 8000: This event loop is already running
RuntimeWarning: coroutine 'ModelCapabilityManager.detect_capability' was never awaited
```

### 错误类型
- 类型：异步/并发
- 影响：翻译模块无法正确探测模型能力，始终使用默认值

## 解决方案

### 根本原因
1. `ModelCapabilityManager.get_or_detect()` 是同步方法，内部使用 `loop.run_until_complete()` 运行异步函数
2. 但 `translator.py` 中的 `_ensure_capability_detected()` 是异步方法，在已运行的事件循环中被调用
3. 在已运行的事件循环中调用 `loop.run_until_complete()` 会报错 "This event loop is already running"

### 修改文件
- `src/model_capabilities.py`：添加异步方法 `async_get_or_detect()`
- `src/translator.py`：使用异步方法进行探测

### 代码变更
```python
# model_capabilities.py - 新增异步方法
async def async_get_or_detect(self, model: str, base_url: str, api_key: str, timeout: int = 10) -> Dict:
    """异步获取模型能力（用于在已有事件循环中调用）"""
    cached = self.get_cached_capability(model, base_url)
    if cached:
        return cached
    return await self.detect_capability(model, base_url, api_key, timeout)

# model_capabilities.py - 同步方法增加保护
def get_or_detect(self, ...):
    # ...
    if loop.is_running():
        logger.warning("事件循环已运行，无法同步探测，使用默认值")
        return self._get_default_capability(model, base_url)

# translator.py - 使用异步方法
capability = await capability_mgr.async_get_or_detect(
    model=self.model,
    base_url=self.base_url,
    api_key=self.client.api_key,
    timeout=config.MODEL_DETECTION_TIMEOUT
)
```

### 修复效果
1. 异步爬虫中可以正确探测模型能力
2. 避免事件循环冲突错误
3. 同步调用场景仍然支持（使用 `get_or_detect()`）

## 验证结果
- [x] 代码语法检查通过
- [x] 模块导入验证通过
- [x] 异步模型能力探测测试通过
