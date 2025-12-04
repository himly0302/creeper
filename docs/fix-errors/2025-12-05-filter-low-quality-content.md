# 错误修复：过滤低质量和错误页面内容

**修复时间**：2025-12-05
**错误级别**：High

## 问题详情

### 错误描述
`/home/lyf/workspaces/creeper/outputs/中国/中美关税` 文件夹中保存了一些不该保存的文件，包括：
- `您搜索的内容不存在或已不存在.md` - 404 错误页面
- `bloomberg.md` - 反爬虫验证页面

### 错误类型
- 类型：内容过滤错误
- 影响：文件污染，存储浪费，数据质量下降

## 根本原因

### 1. 动态渲染缺少内容验证
- 静态爬取有 `MIN_TEXT_LENGTH` 验证（≥100字符）
- 动态渲染成功后没有内容长度检查
- 没有检查内容质量（错误页面、验证页面等）

### 2. 缺少内容质量检查
爬取器会保存以下类型的不当内容：
- **404 错误页面**：页面不存在、内容不存在
- **反爬虫页面**：机器人验证、JavaScript 要求
- **订阅页面**：请登录、请订阅
- **技术错误页面**：访问被拒绝、禁止访问

## 解决方案

### 修改文件
- `src/async_fetcher.py`：添加动态渲染内容验证
- `src/fetcher.py`：添加同步爬取内容验证

### 代码变更

#### 1. 动态渲染内容验证
```python
# 修改前
page = await self._fetch_dynamic(url)
if page.success:
    logger.info(f"✓ 动态渲染成功: {url}")
    return page

# 修改后
page = await self._fetch_dynamic(url)
if page.success and len(page.content) >= config.MIN_TEXT_LENGTH:
    # 额外检查内容质量
    if self._is_valid_content(page.content):
        logger.info(f"✓ 动态渲染成功: {url}")
        return page
    else:
        logger.warning(f"动态渲染内容质量不佳，跳过保存: {url}")
        page.success = False
        return page
elif page.success:
    logger.warning(f"动态渲染内容不足(<{config.MIN_TEXT_LENGTH}字符),跳过保存: {url}")
    page.success = False
    return page
```

#### 2. 内容质量检查方法
```python
def _is_valid_content(self, content: str) -> bool:
    """
    检查内容是否有效，过滤掉错误页面和低质量内容
    """
    content_lower = content.lower()

    # 检查常见的错误页面指示词
    error_indicators = [
        "页面不存在", "内容不存在", "找不到页面", "404",
        "页面未找到", "您搜索的内容不存在", "已不存在",
        "访问被拒绝", "禁止访问", "请验证您是机器人",
        "请点击下方方框", "证明您不是机器人",
        "请确保您的浏览器支持", "javascript", "cookie 功能",
        "订阅", "立即订阅", "登录", "注册", "请登录", "需要登录"
    ]

    # 如果包含错误指示词，认为内容无效
    for indicator in error_indicators:
        if indicator in content_lower:
            return False

    # 检查内容是否太短
    if len(content.strip()) < 200:
        return False

    # 检查是否包含足够的中文字符或英文内容
    chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
    english_chars = len([c for c in content if 'a' <= c <= 'z' or 'A' <= c <= 'Z'])

    # 如果中文字符少于50个且英文字符少于100个，可能内容质量不高
    if chinese_chars < 50 and english_chars < 100:
        return False

    return True
```

### 3. 错误文件清理
删除已保存的不当内容文件：
- `您搜索的内容不存在或已不存在.md`
- `bloomberg.md`

## 验证结果

### 内容质量检查测试
```
✅ 测试 1: "您搜索的内容不存在或已不存在" → 正确过滤
✅ 测试 2: "请点击下方方框继续操作，以证明您不是机器人" → 正确过滤
✅ 测试 3: 长篇有效内容 → 正确保留
✅ 测试 4: 包含充足中英文的内容 → 正确保留
✅ 测试 5: 订阅页面内容 → 正确过滤
✅ 测试 6: 过短内容 → 正确过滤
```

### 文件清理结果
- ✅ 删除了2个不当内容文件
- ✅ 保留了5个有效内容文件
- ✅ 输出目录现在只包含高质量的内容

## 修复效果

### 质量提升
- **内容准确性**：只保存有意义的网页内容
- **存储效率**：减少无效文件占用磁盘空间
- **数据质量**：提高爬取数据的整体质量

### 用户体验
- **减少噪音**：不再看到错误页面的文件
- **提高效率**：减少后期数据清理工作
- **数据可靠性**：保存的内容更加可信

### 性能优化
- **减少I/O操作**：跳过无效内容的文件写入
- **减少存储开销**：避免保存无用的错误页面
- **提高爬取效率**：减少不必要的处理

## 配置建议

当前验证标准较为严格，可以根据需求调整：

### 内容长度阈值
```python
MIN_TEXT_LENGTH = 100  # 可根据需要调整
```

### 内容质量检查
可以通过修改 `_is_valid_content` 方法调整：
- 添加或删除错误指示词
- 调整中英文字符数量要求
- 修改最低内容长度要求

## 总结

这个修复解决了爬取器保存低质量和错误内容的问题，显著提高了输出数据的质量。通过添加内容质量检查机制，可以有效地过滤掉：
- 404错误页面
- 反爬虫验证页面
- 订阅和登录要求页面
- 其他技术错误页面

修复后，爬取器将只保存高质量的、有意义的网页内容，大大提高了数据的可用性和价值。