# 图片下载域名配置示例

本文档提供了图片下载域名配置的实际使用示例。

## 快速开始

### 1. 默认配置（BBC图片自动使用requests）

无需任何配置，系统会自动处理BBC域名：

```bash
# 使用默认配置，BBC图片自动使用requests下载
python creeper.py inputs/input.md
```

### 2. 添加新的问题域名

在 `.env` 文件中配置：

```bash
# 编辑 .env 文件
FORCE_REQUESTS_DOMAINS=bbci.co.uk,bbc.com,problematic-site.com

# 或者通过命令行
export FORCE_REQUESTS_DOMAINS="bbci.co.uk,bbc.com,problematic-site.com"
python creeper.py inputs/input.md
```

### 3. 多个域名配置示例

```bash
# .env 文件配置
FORCE_REQUESTS_DOMAINS=bbci.co.uk,bbc.com,example.com,test.org,problematic-site.net
```

## 实际使用场景

### 场景1：BBC新闻图片下载

**输入文件** `inputs/bbc-news.md`:
```markdown
# BBC新闻示例

![BBC图片](https://ichef.bbci.co.uk/ace/ws/640/cpsprodpb/12345/image.jpg.webp)

![其他图片](https://example.com/normal-image.png)
```

**运行命令**:
```bash
# 使用默认配置即可
python creeper.py inputs/bbc-news.md
```

**结果**:
- BBC图片使用 requests 库下载 ✅
- 其他图片使用 aiohttp 库下载 ✅

### 场景2：添加新的问题域名

**发现问题**：`example-problematic.com` 的图片无法用aiohttp下载

**解决方案**:
```bash
# 方法1：修改 .env 文件
echo "FORCE_REQUESTS_DOMAINS=bbci.co.uk,bbc.com,example-problematic.com" >> .env

# 方法2：命令行设置
export FORCE_REQUESTS_DOMAINS="bbci.co.uk,bbc.com,example-problematic.com"

# 运行爬虫
python creeper.py inputs/input.md
```

### 场景3：临时配置测试

```bash
# 临时设置，只对当前命令有效
FORCE_REQUESTS_DOMAINS="test-site.com,another-site.org" python creeper.py inputs/input.md

# 或者
export FORCE_REQUESTS_DOMAINS="test-site.com"
python creeper.py inputs/input.md
unset FORCE_REQUESTS_DOMAINS  # 清除环境变量
```

## 验证配置

### 检查当前配置

```python
# 创建验证脚本 check_domains.py
from src.image_downloader import AsyncImageDownloader

downloader = AsyncImageDownloader()

print("当前配置的域名:", downloader._force_requests_domains)

# 测试特定域名
test_domains = ['bbci.co.uk', 'sub.bbci.co.uk', 'example.com', 'google.com']
for domain in test_domains:
    uses_requests = downloader._should_use_requests(domain)
    method = "requests" if uses_requests else "aiohttp"
    print(f"  {domain} -> {method}")
```

### 运行验证

```bash
source venv/bin/activate
python check_domains.py
```

**输出示例**:
```
当前配置的域名: ['bbci.co.uk', 'bbc.com', 'example-problematic.com']
  bbci.co.uk -> requests
  sub.bbci.co.uk -> requests
  example.com -> aiohttp
  google.com -> aiohttp
```

## 子域名匹配

配置支持自动子域名匹配：

```bash
# 配置主域名
FORCE_REQUESTS_DOMAINS=example.com

# 自动匹配的子域名
# - sub.example.com ✅
# - news.bbc.co.uk ✅ (当配置了 bbci.co.uk)
# - api.bbc.co.uk ✅
```

## 常见问题域名

根据实际使用经验，以下域名可能需要配置：

```bash
# 示例配置，根据实际情况调整
FORCE_REQUESTS_DOMAINS=bbci.co.uk,bbc.com,example-problematic.com,another-problematic.org
```

## 故障排除

### 1. 检查环境变量

```bash
echo $FORCE_REQUESTS_DOMAINS
```

### 2. 检查 .env 文件

```bash
grep FORCE_REQUESTS_DOMAINS .env
```

### 3. 调试模式

```bash
python creeper.py inputs/input.md --debug
```

调试日志会显示：
- 域名匹配结果
- 下载方法选择
- 详细错误信息

## 最佳实践

1. **按需配置**：只对确实有问题的域名添加配置
2. **定期检查**：观察日志，发现新的问题域名
3. **测试验证**：配置后先用小批量测试
4. **文档记录**：记录配置的问题域名和原因

通过这些简单的配置，可以有效解决各种域名的图片下载兼容性问题。