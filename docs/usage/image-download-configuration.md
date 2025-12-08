# 图片下载配置指南

本文档介绍如何配置和使用图片下载器的域名策略功能。

## 概述

图片下载器现在支持域名策略配置，可以：
- 自动检测和处理不同域名的连接问题
- 支持用户配置强制使用特定下载方式（requests库）

## 下载策略类型

### 1. 配置域名（requests模式）
强制使用requests库下载，适用于已知aiohttp有问题的域名。

### 2. 默认域名（aiohttp模式）
其他所有域名使用aiohttp下载。

## 配置方法

### 环境变量配置

通过设置 `FORCE_REQUESTS_DOMAINS` 环境变量来配置强制使用requests的域名：

```bash
# .env 文件中配置
FORCE_REQUESTS_DOMAINS=bbci.co.uk,bbc.com,example-problematic.com

# 或者在命令行中设置
export FORCE_REQUESTS_DOMAINS="bbci.co.uk,bbc.com"
python creeper.py inputs/input.md
```

### 配置多个域名

```bash
# 用逗号分隔多个域名
FORCE_REQUESTS_DOMAINS=bbci.co.uk,bbc.com,example.com,test-site.org
```

### 配置子域名

支持子域名匹配：

```bash
# 这个配置会影响所有bbc.co.uk和bbc.com的子域名
FORCE_REQUESTS_DOMAINS=bbci.co.uk,bbc.com
```

## 默认问题域名

系统默认包含以下已知有连接问题的域名：

- `bbci.co.uk` 和 `bbc.com`：BBC图片服务器

## 使用示例

### 示例1：BBC图片下载

```python
from src.image_downloader import AsyncImageDownloader

downloader = AsyncImageDownloader()
# BBC图片会自动使用requests下载
result = await downloader.download_image(
    'https://ichef.bbci.co.uk/ace/ws/640/cpsprodpb/image.jpg.webp',
    Path('./images')
)
```

### 示例2：配置特定域名

```bash
# 配置example.com强制使用requests
export FORCE_REQUESTS_DOMAINS="example.com"
python creeper.py inputs/input.md
```

### 示例3：查看当前配置

```python
downloader = AsyncImageDownloader()

# 查看配置的域名列表
print(f"配置的域名: {downloader._force_requests_domains}")

# 测试特定域名是否使用requests
domain = "bbci.co.uk"
uses_requests = downloader._should_use_requests(domain)
print(f"域名 {domain} 是否使用requests: {uses_requests}")
```

## 性能考虑

### 线程池配置
- 使用2个线程池来处理requests请求
- 避免阻塞主异步循环

### 缓存机制
- 下载成功的图片会被缓存
- 避免重复下载相同图片

### 错误处理
- 详细的错误信息包含具体的异常类型
- 配置域名失败时会尝试aiohttp备用方案

## 故障排除

### 常见问题

**Q: 为什么有些域名仍然下载失败？**
A: 可能是网络连接问题或服务器端限制。

**Q: 如何添加新的问题域名？**
A: 在环境变量中添加域名即可。

**Q: 配置的域名不生效？**
A: 检查环境变量是否正确设置，可以使用 `echo $FORCE_REQUESTS_DOMAINS` 验证。

### 调试模式

启用调试日志查看详细下载过程：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

调试日志会显示：
- 域名匹配结果
- 下载方法选择
- 错误详情

## 最佳实践

1. **合理配置**：只对已知有问题的域名强制使用requests
2. **性能监控**：监控下载成功率和响应时间
3. **灵活调整**：根据实际情况调整配置策略

通过这套简单的配置系统，图片下载器能够有效处理不同域名的连接问题，提供最佳的下载成功率。