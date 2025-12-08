# 错误修复：ModelCapabilityManager.get_or_detect() 参数不匹配

**修复时间**：2025-12-08
**错误级别**：Medium

## 问题详情

### 错误信息
```
WARNING  [anthropic] 模型能力探测失败，使用默认值 8000: ModelCapabilityManager.get_or_detect() got an unexpected keyword argument 'client'
```

### 错误类型
- 类型：API/配置
- 影响：翻译模块无法正确探测模型能力，始终使用默认值 8000

## 解决方案

### 根本原因
`translator.py` 调用 `ModelCapabilityManager.get_or_detect()` 时传递了错误的参数：
- 传递了 `client` 和 `fallback_max_tokens` 参数
- 但方法签名实际是 `(model, base_url, api_key, timeout)`
- 另外使用了 `await`，但该方法是同步方法（内部使用 `loop.run_until_complete`）

### 修改文件
- `src/translator.py`：修正调用参数

### 代码变更
```python
# 修改前
capability = await capability_mgr.get_or_detect(
    model=self.model,
    base_url=self.base_url,
    client=self.client,
    fallback_max_tokens=8000  # 翻译模块的默认值
)

# 修改后
capability = capability_mgr.get_or_detect(
    model=self.model,
    base_url=self.base_url,
    api_key=self.client.api_key,
    timeout=config.MODEL_DETECTION_TIMEOUT
)
```

### 修复效果
1. 正确传递 `api_key` 参数
2. 使用配置的 `MODEL_DETECTION_TIMEOUT` 超时值
3. 移除错误的 `await`（方法是同步的）

## 验证结果
- [x] 代码语法检查通过
- [x] 模块导入验证通过
- [x] Translator 初始化测试通过
