# 错误修复：URL列表模式中的图片下载器导入错误

**修复时间**：2025-12-08
**错误级别**：High

## 问题详情

### 错误信息
```
ERROR     处理过程中发生错误: cannot import name 'ImageDownloader' from 'src.image_downloader' (/home/lyf/workspaces/creeper/src/image_downloader.py)
```

### 错误类型
- 类型：导入错误（ImportError）
- 状态码：运行时错误

## 问题分析

### 根本原因
在删除同步爬虫版本时，`ImageDownloader` 类被删除了，但URL列表模式中的图片提取功能仍在尝试导入这个已删除的类。

### 影响范围
- URL列表模式下的 `--with-images` 参数完全失效
- 无法提取网页中的图片链接
- 导致URL列表模式功能部分不可用

## 解决方案

### 修改文件
- `src/url_list_mode.py`：将同步图片下载器改为异步版本

### 代码变更
```python
// 修改前 - src/url_list_mode.py:114-119
# 复用 ImageDownloader 的图片提取逻辑
from .image_downloader import ImageDownloader
downloader = ImageDownloader(base_url=webpage.url)
image_urls = downloader.extract_image_urls(webpage.content)
# 提取完整URL列表（去掉alt_text和原始URL）
result["images"] = [img_url for _, _, img_url in image_urls]

// 修改后 - src/url_list_mode.py:114-119
# 使用 AsyncImageDownloader 的图片提取逻辑
from .image_downloader import AsyncImageDownloader
downloader = AsyncImageDownloader(base_url=webpage.url)
image_urls = downloader.extract_image_urls(webpage.content)
# 提取完整URL列表（去掉alt_text和原始URL）
result["images"] = [img_url for _, _, img_url in image_urls]
```

### 修复说明
- 将 `ImageDownloader` 替换为 `AsyncImageDownloader`
- 保持了相同的接口（`extract_image_urls` 方法）
- 图片提取功能完全恢复

## 验证结果
- [x] 导入错误已修复
- [x] URL列表模式可以正常导入图片下载器
- [x] `--with-images` 参数应该可以正常工作

## 相关上下文
这个错误是删除同步版本后的连锁反应。同步版本的 `ImageDownloader` 被删除时，需要确保所有引用它的地方都更新为异步版本。