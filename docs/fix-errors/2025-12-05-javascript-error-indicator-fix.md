# 错误修复：内容验证逻辑中的"javascript"误判问题

**修复时间**：2025-12-05
**错误级别**：Medium

## 问题详情

### 错误信息
```
WARNING  [claude] 静态爬取内容质量不佳，跳过保存: https://code.claude.com/docs/zh-CN/quickstart
ERROR     ✗ 处理失败: https://code.claude.com/docs/zh-CN/quickstart - None
```

### 错误类型
- 类型：内容质量检查
- 影响：所有包含"javascript"的现代网页都被误判为低质量内容

## 解决方案

### 根本原因
错误指示词列表中的"javascript"过于宽泛，任何现代网页的HTML中都包含`<script>`标签或"javascript"字符串，导致内容验证逻辑误判。

### 修改文件
- `src/async_fetcher.py`：修复异步版本的内容验证逻辑
- `src/fetcher.py`：修复同步版本的内容验证逻辑

### 代码变更
```python
// 修改前
error_indicators = [
    # ...
    "请确保您的浏览器支持",
    "javascript",  # 过于宽泛
    "cookie 功能",
    # ...
    "enable javascript",  # 过于宽泛
    "enable cookies",
]

// 修改后
error_indicators = [
    # ...
    "请确保您的浏览器支持",
    "请确保您的浏览器支持javascript",  # 更精确的匹配
    "cookie 功能",
    # ...
    "please enable javascript",  # 更精确的匹配
    "enable cookies",
]
```

### 额外改进
同时修复了错误信息显示问题：
```python
// 修改前：错误信息为空
page.success = False
return page

// 修改后：提供详细的错误信息
page.success = False
page.error = "内容质量检查未通过，可能包含错误页面指示词或内容过短"
return page
```

## 验证结果
- [x] 代码逻辑检查通过
- [x] 错误指示词更加精确
- [x] 错误信息更加详细
- [x] 同步和异步版本都已修复

## 测试建议
修复后，之前被误判的URL（如 https://code.claude.com/docs/zh-CN/quickstart）应该能够正常爬取。