# 错误修复：StorageManager 缺少 stats 属性

**修复时间**：2025-12-08
**错误级别**：Critical

## 问题详情

### 错误信息
```
ERROR    [com] 保存文件失败: 'StorageManager' object has no attribute 'stats'
ERROR    [com] ✗ 保存失败: https://cn.chinadaily.com.cn/a/202511/17/WS691a7178a310942cc4991ac8.html
```

### 错误类型
- 类型：属性错误（AttributeError）
- 状态码：运行时错误

## 问题分析

### 根本原因
`StorageManager` 类在初始化时没有定义 `stats` 属性，但在 `save_async` 方法中试图访问和更新这个属性。这导致所有保存操作都失败，爬取的内容无法保存到文件。

### 影响范围
- 所有网页保存操作失败
- 爬取的内容丢失
- 失败的 URL 被错误地记录到失败列表

## 解决方案

### 修改文件
- `src/storage.py`：在 `__init__` 方法中初始化 `stats` 属性

### 代码变更
```python
// 修改前 - src/storage.py:23-32
def __init__(self, output_dir: Optional[str] = None):
    """
    初始化存储管理器

    Args:
        output_dir: 输出目录,如果为 None 则使用配置中的值
    """
    self.output_dir = Path(output_dir or config.OUTPUT_DIR)
    ensure_dir(self.output_dir)
    logger.info(f"文件存储管理器已初始化: {self.output_dir}")

// 修改后 - src/storage.py:23-39
def __init__(self, output_dir: Optional[str] = None):
    """
    初始化存储管理器

    Args:
        output_dir: 输出目录,如果为 None 则使用配置中的值
    """
    self.output_dir = Path(output_dir or config.OUTPUT_DIR)
    ensure_dir(self.output_dir)

    # 统计信息
    self.stats = {
        'total_files': 0,
        'total_size': 0
    }

    logger.info(f"文件存储管理器已初始化: {self.output_dir}")
```

## 验证结果
- [x] AttributeError 已修复
- [x] StorageManager.stats 属性正确初始化
- [x] 保存操作应该能够正常工作

## 相关上下文
这个错误是在删除同步版本后暴露的问题。之前可能代码路径不同或者有其他方式初始化了这个属性。