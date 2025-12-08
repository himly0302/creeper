# 错误修复：翻译模块 max_tokens 类型错误

**修复时间**：2025-12-08
**错误级别**：High

## 问题详情

### 错误信息
```
ERROR    [anthropic] 翻译失败: Error code: 400 - {'error': {'code': 'invalid_value', 'message': "'max_tokens' must be Integer", 'param': None, 'type': 'invalid_request_error'}}
ERROR    [claude] 翻译失败: Error code: 400 - {'error': {'code': 'invalid_value', 'message': "'max_tokens' must be Integer", 'param': None, 'type': 'invalid_request_error'}}
```

### 错误类型
- 类型：API/数据类型错误
- 状态码：400

## 解决方案

### 根本原因
`ModelCapabilityManager` 在缓存模型能力信息时，将 `max_input_tokens` 和 `max_output_tokens` 转换为字符串存储：
```python
"max_input_tokens": str(max_input_tokens),
"max_output_tokens": str(max_output_tokens)
```

当从缓存读取时，这些值仍然是字符串类型，导致翻译 API 调用时传递了字符串类型的 `max_tokens` 参数，而 API 要求整数类型。

### 修改文件
- `src/model_capabilities.py`：修复 `get_cached_capability` 方法中的类型转换

### 代码变更
```python
# 修改前
"max_input_tokens": capability_data.get("max_input_tokens"),
"max_output_tokens": capability_data.get("max_output_tokens"),

# 修改后
"max_input_tokens": int(capability_data.get("max_input_tokens", 0)),
"max_output_tokens": int(capability_data.get("max_output_tokens", 0)),
```

### 修复效果
1. 确保从缓存读取的 token 值始终是整数类型
2. 提供默认值 0 处理缺失的缓存数据
3. 避免 API 调用时的类型错误

## 验证结果
- [x] 代码语法检查通过
- [x] 缓存数据类型转换测试通过
- [x] max_tokens 类型确认为整数
