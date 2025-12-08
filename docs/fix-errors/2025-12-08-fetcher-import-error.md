# 错误修复：删除同步版本后的导入错误

**修复时间**：2025-12-08
**错误级别**：Critical

## 问题详情

### 错误信息
```
Traceback (most recent call last):
  File "/home/lyf/workspaces/creeper/creeper.py", line 18, in <module>
    from src.async_fetcher import AsyncWebFetcher
  File "/home/lyf/workspaces/creeper/src/async_fetcher.py", line 19, in <module>
    from .fetcher import WebPage  # 复用 WebPage 数据类
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ModuleNotFoundError: No module named 'src.fetcher'
```

### 错误类型
- 类型：配置/代码结构问题
- 状态码：导入失败

## 解决方案

### 根本原因
在删除同步爬虫模式时，删除了 `src/fetcher.py` 文件，但多个模块仍然从中导入 `WebPage` 类：
- `async_fetcher.py` 导入 `WebPage` 数据类
- `url_list_mode.py` 导入 `WebPage` 数据类
- `storage.py` 导入 `WebPage` 数据类和同步图片下载器

### 修改文件
- `src/async_fetcher.py`：将 `WebPage` 类定义移入该模块
- `src/url_list_mode.py`：修改导入，从 `async_fetcher` 导入 `WebPage`
- `src/storage.py`：修改导入，删除同步图片下载器依赖
- `creeper.py`：使用异步保存方法 `save_async` 替代同步方法

### 代码变更

```python
// 修改前 - src/async_fetcher.py
from .fetcher import WebPage  # 复用 WebPage 数据类

// 修改后 - src/async_fetcher.py
@dataclass
class WebPage:
    """网页数据类"""
    url: str
    title: str
    description: str
    content: str
    # ... 完整的类定义

// 修改前 - src/url_list_mode.py
from .fetcher import WebPage

// 修改后 - src/url_list_mode.py
from .async_fetcher import AsyncWebFetcher, WebPage

// 修改前 - src/storage.py
from .fetcher import WebPage
from .image_downloader import ImageDownloader, AsyncImageDownloader

// 修改后 - src/storage.py
from .async_fetcher import WebPage
from .image_downloader import AsyncImageDownloader

// 修改前 - creeper.py
file_path = self.storage.save(item, page)

// 修改后 - creeper.py
file_path = await self.storage.save_async(item, page)
```

## 验证结果
- [x] 导入错误已修复
- [x] 所有模块使用异步版本
- [x] 移除了同步版本的依赖

## 影响范围
- 整个爬虫功能恢复正常
- 统一使用异步模式，性能更好
- 代码结构更清晰，维护成本降低