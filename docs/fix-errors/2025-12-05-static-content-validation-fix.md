# 错误修复：静态爬取模式下错误页面被保存

**修复时间**：2025-12-05
**错误级别**：Medium

## 问题详情

### 错误信息
在爬虫输出目录中发现了404错误页面文件被保存，如：
- `outputs/中国/中美关税/您查找的内容不存在-或已不再存在.md`

### 错误类型
- 类型：内容质量控制
- 状态码：N/A（逻辑错误）

### 问题现象
爬虫在静态爬取模式下成功保存了404错误页面、页面不存在提示等低质量内容，这些内容应该被过滤掉。

## 解决方案

### 根本原因
在 `src/fetcher.py` 和 `src/async_fetcher.py` 的静态爬取成功分支中，只检查了内容长度是否达到 `MIN_TEXT_LENGTH` 要求，但没有调用 `_is_valid_content()` 方法进行内容质量验证。只有在动态渲染模式下才进行了内容验证。

### 修改文件
- `src/fetcher.py`：第104-113行，为静态爬取添加内容质量验证
- `src/async_fetcher.py`：第94-108行，为静态爬取添加内容质量验证

### 代码变更
**src/fetcher.py**：
```python
// 修改前
try:
    page = self._fetch_static(url)
    if page.success and len(page.content) >= config.MIN_TEXT_LENGTH:
        logger.info(f"✓ 静态爬取成功: {url}")
        return page

// 修改后
try:
    page = self._fetch_static(url)
    if page.success and len(page.content) >= config.MIN_TEXT_LENGTH:
        # 检查内容质量，过滤错误页面
        if self._is_valid_content(page.content):
            logger.info(f"✓ 静态爬取成功: {url}")
            return page
        else:
            logger.warning(f"静态爬取内容质量不佳，跳过保存: {url}")
            page.success = False
            return page
```

**src/async_fetcher.py**：类似修改，在静态爬取成功分支中添加相同的内容验证逻辑。

## 验证结果
- [x] 代码检查通过
- [x] 内容验证测试通过
  - 错误页面内容被正确过滤（False）
  - 正常内容通过验证（True）
  - 边界情况（404、订阅要求、短内容）都被正确过滤
- [x] 已清理之前错误保存的文件

## 影响评估
- **正面影响**：提高爬取内容质量，减少垃圾文件
- **潜在影响**：某些包含错误关键词的正常内容可能会被误过滤，但现有验证逻辑已经考虑了这种情况

## 预防措施
1. 确保所有爬取路径都经过相同的内容验证
2. 定期检查输出目录，及时发现异常文件
3. 考虑将内容验证逻辑提取为公共方法，避免重复代码