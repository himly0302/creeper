# 错误修复：增强标题验证过滤错误页面

**修复时间**：2025-12-05
**错误级别**：Medium
**修复类型**：内容质量验证增强

## 问题详情

### 错误信息
在 `outputs/中国/中美关税` 文件夹中发现错误页面文件：
- `您搜索的内容不存在或已不存在.md`（创建时间：02:19:42）

### 错误类型
- 类型：内容过滤逻辑缺陷
- 影响：错误页面被保存为有效文件

## 根本原因

### 问题分析
1. **错误信息在标题中**：网页标题为 "您搜索的内容不存在或已不存在。"
2. **内容验证盲区**：`_is_valid_content()` 方法只检查 `content`（正文内容），没有检查 `title`（标题）
3. **正文内容绕过验证**：该错误页面的正文是 cookie 隐私提示文字，不包含错误关键词

### 技术细节
```python
# 修复前：只检查内容
def _is_valid_content(self, content: str) -> bool:
    content_lower = content.lower()
    for indicator in error_indicators:
        if indicator in content_lower:  # 只检查内容
            return False

# 问题：标题 "您搜索的内容不存在或已不存在" 未被检查
# 正文：cookie 隐私提示文字，通过了验证
```

## 解决方案

### 修改文件
- `src/fetcher.py`：增强 `_is_valid_content()` 方法，添加标题检查
- `src/async_fetcher.py`：同步增强 `_is_valid_content()` 方法

### 代码变更
```python
# 修改后：同时检查标题和内容
def _is_valid_content(self, content: str, title: str = "") -> bool:
    content_lower = content.lower()
    title_lower = title.lower() if title else ""

    for indicator in error_indicators:
        if indicator in content_lower:
            logger.debug(f"内容包含错误指示词: {indicator}")
            return False
        if indicator in title_lower:
            logger.debug(f"标题包含错误指示词: {indicator}")
            return False
```

### 调用处更新
```python
# 修改前
if self._is_valid_content(page.content):

# 修改后
if self._is_valid_content(page.content, page.title):
```

## 验证结果

### 测试场景
```
✅ 正常内容应该通过: True
✅ 标题包含错误应该被过滤: False（正确过滤）
✅ 内容包含错误应该被过滤: False（正确过滤）
✅ 英文标题错误应该被过滤: False（正确过滤）
✅ 英文内容错误应该被过滤: False（正确过滤）
```

### 清理工作
1. **删除错误文件**：已删除 `您搜索的内容不存在或已不存在.md`
2. **清理 Redis 缓存**：已删除键 `creeper:url:4b31ec5f12677741699aaa04e72d5c7f`
3. **验证结果**：目录中仅保留 3 个有效文件

## 经验教训

1. **标题的重要性**：404 错误信息可能只出现在标题中，而正文可能是其他内容
2. **验证覆盖面**：需要同时检查标题和内容才能完整过滤错误页面
3. **调试日志**：添加 debug 日志有助于追踪哪个指示词触发了过滤

## 改进建议

1. **统一验证接口**：考虑创建 `WebPage` 级别的验证方法，统一验证标题、内容、描述
2. **验证前置**：在 `_fetch_dynamic` 和 `_fetch_static` 返回前就进行验证，而不是在调用后
3. **配置化关键词**：将错误指示词列表移到配置文件，便于维护和扩展
