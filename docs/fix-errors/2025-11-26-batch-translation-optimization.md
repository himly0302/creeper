# 性能优化：批量翻译减少API调用

**修复时间**：2025-11-26
**错误级别**：Medium (性能优化)

## 问题详情

### 问题描述
一个网页内容的翻译调用了多次LLM API,造成不必要的开销:
```
2025-11-26 23:13:35 - translator - INFO - [visualstudio]检测到英文内容,开始翻译...
2025-11-26 23:13:35 - translator - INFO - [visualstudio]正在翻译: 232 字符...
2025-11-26 23:13:37 - translator - INFO - [visualstudio]翻译成功: 232 字符 → 120 字符
2025-11-26 23:13:37 - translator - INFO - [visualstudio]正在翻译: 1535 字符...
2025-11-26 23:13:44 - translator - INFO - [visualstudio]翻译成功: 1535 字符 → 781 字符
2025-11-26 23:13:44 - translator - INFO - [visualstudio]网页翻译完成
```

### 问题类型
- 类型：性能优化
- 影响范围：翻译功能,API成本
- 资源浪费：每个网页多次API调用(title, description, content分别调用)

### 根本原因
原实现逻辑在 `translate_webpage()` 方法中对每个字段(title, description, content)单独调用 `translate()`,导致一个网页需要2-3次LLM API调用。

## 解决方案

### 优化策略
采用**批量翻译**策略:
1. 使用特殊分隔符(`---FIELD_SEPARATOR---`)将多个字段组合为单个文本
2. 一次API调用翻译所有字段
3. 分割翻译结果并映射回对应字段
4. 失败时自动降级为逐个翻译

### 修改文件
- `src/translator.py:106-115`: 更新翻译提示词,添加分隔符保留规则
- `src/translator.py:180-234`: 重构批量翻译逻辑

### 代码变更

**修改前（逐个翻译）**:
```python
# 3. 并发翻译
results = {}
for field_name, text in translation_tasks:
    try:
        field_lang = self.detect_language(text)
        if field_lang == "unknown":
            results[field_name] = text
            continue
        elif field_lang != "en":
            results[field_name] = text
            continue

        # 每个字段单独调用API
        results[field_name] = await self.translate(text, skip_detection=True)
    except Exception as e:
        logger.error(f"翻译 {field_name} 失败: {e}")
        results[field_name] = text
```

**修改后（批量翻译）**:
```python
# 3. 批量翻译(一次API调用翻译所有字段)
results = {}

# 3.1 过滤需要翻译的字段
fields_to_translate = []
for field_name, text in translation_tasks:
    field_lang = self.detect_language(text)
    if field_lang == "unknown":
        results[field_name] = text
    elif field_lang != "en":
        results[field_name] = text
    else:
        fields_to_translate.append((field_name, text))

# 3.2 批量翻译所有字段(一次API调用)
if fields_to_translate:
    try:
        # 使用分隔符组合
        combined_text = "\n\n---FIELD_SEPARATOR---\n\n".join(texts)

        # 一次API调用
        translated_combined = await self.translate(combined_text, skip_detection=True)

        # 分割并映射结果
        translated_parts = translated_combined.split("---FIELD_SEPARATOR---")
        for i, field_name in enumerate(field_names):
            results[field_name] = translated_parts[i].strip()

    except Exception as e:
        # 降级:逐个翻译
        for field_name, text in fields_to_translate:
            results[field_name] = await self.translate(text, skip_detection=True)
```

## 验证结果

### 性能对比
**优化前**:
```
INFO - [visualstudio]正在翻译: 232 字符...   (第1次API调用)
INFO - [visualstudio]翻译成功: 232 字符 → 120 字符
INFO - [visualstudio]正在翻译: 1535 字符...  (第2次API调用)
INFO - [visualstudio]翻译成功: 1535 字符 → 781 字符
```

**优化后**:
```
INFO - [visualstudio]批量翻译 2 个字段: 1767 字符...
INFO - [visualstudio]正在翻译: 1792 字符...  (仅1次API调用)
INFO - [visualstudio]翻译成功: 1792 字符 → 923 字符
INFO - [visualstudio]批量翻译成功: 1767 字符 → 898 字符
```

### 优化效果
- ✅ API调用次数减少 **50%** (2次 → 1次)
- ✅ 翻译质量保持不变
- ✅ 降低API成本
- ✅ 减少网络开销
- ✅ 提升整体爬取速度

### 测试检查
- [x] 单个网页翻译正常
- [x] 分隔符正确保留
- [x] 多字段映射准确
- [x] 降级机制有效
- [x] 日志清晰易读
