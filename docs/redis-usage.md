# Creeper Redis 使用文档

**版本**: v1.6.2
**最后更新**: 2025-11-27

---

## 概述

Creeper 使用 Redis 作为核心缓存存储，支持三大功能模块：
1. **URL 去重**（`dedup.py`）- 避免重复爬取相同 URL
2. **Cookie 管理**（`cookie_manager.py`）- 跨会话持久化登录状态
3. **文件聚合缓存**（`file_aggregator.py`）- 增量更新文件整合结果

所有模块均支持**混合持久化**（Redis + 本地 JSON），确保数据不因 Redis 重启而丢失。

---

## 一、Redis 连接配置

### 1.1 环境变量配置

在 `.env` 文件中配置 Redis 连接参数：

```bash
# Redis 连接配置
REDIS_HOST=localhost          # Redis 服务器地址
REDIS_PORT=6379               # Redis 端口
REDIS_DB=1                    # 数据库编号（默认 DB 1，不是 DB 0）
REDIS_PASSWORD=               # Redis 密码（可选，留空表示无密码）
REDIS_KEY_PREFIX=creeper:     # 全局 Key 前缀

# Cookie Redis 配置
COOKIE_REDIS_KEY_PREFIX=creeper:cookie:    # Cookie Key 前缀

# 混合持久化
ENABLE_LOCAL_PERSISTENCE=true  # 启用本地 JSON 备份
```

### 1.2 连接参数

**默认配置**（`src/config.py`）:
- **Host**: `localhost`
- **Port**: `6379`
- **DB**: `1`（注意不是 DB 0）
- **超时**: 5 秒（socket_connect_timeout / socket_timeout）
- **编码**: `decode_responses=True`（自动解码为字符串）

---

## 二、数据结构设计

### 2.1 URL 去重（dedup.py）

**功能**: 记录已爬取的 URL，避免重复爬取

#### Key 格式
```
creeper:url:<md5_hash>
```

- **Key 类型**: Hash
- **Key 说明**: `<md5_hash>` 是 URL 的 MD5 哈希值（避免 URL 过长）
- **过期时间**: 30 天（可配置）

#### Hash 字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `url` | String | 原始 URL | `https://example.com/page` |
| `crawled_at` | String | 爬取时间戳 | `2025-11-27 12:00:00` |
| `status` | String | 爬取状态 | `completed` |

#### 示例数据

```redis
# Key
creeper:url:5d41402abc4b2a76b9719d911017c592

# Hash 内容
url: https://example.com/article/123
crawled_at: 2025-11-27 14:30:15
status: completed
```

#### 核心操作

**检查 URL 是否已爬取**:
```python
from src.dedup import DedupManager

dedup = DedupManager()
if dedup.is_crawled("https://example.com/page"):
    print("已爬取")
```

**标记 URL 为已爬取**:
```python
dedup.mark_crawled("https://example.com/page", expire_days=30)
```

**清理所有去重记录**:
```bash
redis-cli -n 1 KEYS "creeper:url:*" | xargs redis-cli -n 1 DEL
```

---

### 2.2 Cookie 管理（cookie_manager.py）

**功能**: 存储网站登录 Cookie，支持跨会话持久化

#### Key 格式
```
creeper:cookie:<domain>
```

- **Key 类型**: String（JSON 序列化）
- **Key 说明**: `<domain>` 是网站域名（如 `example.com`）
- **过期时间**: 7 天（默认，可配置）

#### 数据结构（JSON）

```json
[
  {
    "name": "session_id",
    "value": "abc123...",
    "domain": ".example.com",
    "path": "/",
    "secure": true,
    "httpOnly": true,
    "sameSite": "Lax",
    "expires": 1735286400
  }
]
```

#### 示例数据

```redis
# Key
creeper:cookie:example.com

# Value（JSON 数组）
[{"name":"sessionid","value":"xyz789","domain":".example.com","path":"/","secure":true}]
```

#### 核心操作

**保存 Cookie**:
```python
from src.cookie_manager import CookieManager

cookie_mgr = CookieManager(
    storage_backend='redis',  # 或 'file' 或 'hybrid'
    redis_client=redis_client
)
cookie_mgr.set_cookies("example.com", cookies)
cookie_mgr.save()  # 保存到 Redis（hybrid 模式同时保存到文件）
```

**加载 Cookie**:
```python
cookies = cookie_mgr.get_cookies("example.com")
```

**列出所有域**:
```python
domains = cookie_mgr.list_domains()  # ['example.com', 'another.com']
```

**清理过期 Cookie**:
```bash
# 手动删除特定域
redis-cli -n 1 DEL "creeper:cookie:example.com"

# 删除所有 Cookie
redis-cli -n 1 KEYS "creeper:cookie:*" | xargs redis-cli -n 1 DEL
```

---

### 2.3 文件聚合缓存（file_aggregator.py）

**功能**: 记录已处理的文件列表，支持增量更新

#### Key 格式
```
creeper:aggregator:<output_md5>:files
```

- **Key 类型**: String（JSON 序列化）
- **Key 说明**: `<output_md5>` 是输出文件路径的 MD5 哈希
- **过期时间**: 无（永久保存）

#### 数据结构（JSON）

```json
{
  "folder": "/path/to/source",
  "output_file": "/path/to/output.md",
  "processed_files": {
    "/path/to/file1.py": "abc123...",  // 文件路径: MD5 哈希
    "/path/to/file2.md": "def456..."
  }
}
```

#### 示例数据

```redis
# Key
creeper:aggregator:8b1a9953c4611296a827abf8c47804d7:files

# Value（JSON 对象）
{
  "folder": "/home/user/project/src",
  "output_file": "/home/user/docs/summary.md",
  "processed_files": {
    "/home/user/project/src/main.py": "5d41402abc4b2a76b9719d911017c592",
    "/home/user/project/src/utils.py": "7d793037a0760186574b0282f2f435e7"
  }
}
```

#### 核心操作

**检测新增文件**:
```python
from src.file_aggregator import AggregatorCache

cache = AggregatorCache()
new_files = cache.get_new_files(
    folder="/path/to/source",
    current_files=scanned_files,
    output_file="/path/to/output.md"
)
```

**更新缓存**:
```python
cache.update_processed_files(
    output_file="/path/to/output.md",
    folder="/path/to/source",
    files=all_files
)
```

**清理缓存**:
```bash
# 删除特定输出文件的缓存
redis-cli -n 1 DEL "creeper:aggregator:<md5>:files"

# 删除所有聚合缓存
redis-cli -n 1 KEYS "creeper:aggregator:*" | xargs redis-cli -n 1 DEL
```

---

## 三、混合持久化机制

### 3.1 设计原理

**问题**: Redis 重启会导致数据丢失
**解决方案**: 双写机制（Redis + 本地 JSON）

**工作流程**:
1. **写入数据**: 同时写入 Redis 和本地 JSON 文件
2. **读取数据**: 优先从 Redis 读取
3. **启动恢复**: 如果 Redis 为空，从本地 JSON 文件恢复

### 3.2 本地持久化文件

| 模块 | 本地文件路径 | 说明 |
|------|-------------|------|
| URL 去重 | `data/dedup_cache.json` | 存储所有已爬取 URL |
| Cookie 管理 | `data/cookies_cache.json` | 存储所有域的 Cookie |
| 文件聚合 | `data/aggregator_cache.json` | 存储所有输出文件的处理记录 |

### 3.3 恢复机制

**启动时自动恢复**（仅当 Redis 为空时）:

```python
# dedup.py
dedup_manager = DedupManager()
dedup_manager.restore_from_file_if_needed()  # 自动从文件恢复

# cookie_manager.py
cookie_mgr = CookieManager(storage_backend='hybrid')  # 自动加载

# file_aggregator.py
cache = AggregatorCache()  # 自动恢复
```

**手动恢复**:
```bash
# 1. 清空 Redis
redis-cli -n 1 FLUSHDB

# 2. 重启爬虫（自动从 data/*.json 恢复）
python creeper.py input.md
```

### 3.4 配置控制

```bash
# .env 文件
ENABLE_LOCAL_PERSISTENCE=true  # 启用混合持久化（推荐）
```

---

## 四、Redis 运维指南

### 4.1 查看数据统计

**查看所有 Key 数量**:
```bash
redis-cli -n 1 INFO keyspace
```

**查看各模块数据量**:
```bash
# URL 去重
redis-cli -n 1 KEYS "creeper:url:*" | wc -l

# Cookie 管理
redis-cli -n 1 KEYS "creeper:cookie:*" | wc -l

# 文件聚合缓存
redis-cli -n 1 KEYS "creeper:aggregator:*" | wc -l
```

### 4.2 数据清理

**清理特定模块数据**:
```bash
# 清理 URL 去重（慎用！）
redis-cli -n 1 --scan --pattern "creeper:url:*" | xargs -L 1000 redis-cli -n 1 DEL

# 清理 Cookie
redis-cli -n 1 --scan --pattern "creeper:cookie:*" | xargs -L 1000 redis-cli -n 1 DEL

# 清理文件聚合缓存
redis-cli -n 1 --scan --pattern "creeper:aggregator:*" | xargs -L 1000 redis-cli -n 1 DEL
```

**完全清空数据库**（危险操作！）:
```bash
redis-cli -n 1 FLUSHDB
```

**推荐使用项目提供的清理脚本**:
```bash
./clean.sh  # 清理所有数据和日志
```

### 4.3 数据备份

**手动备份**:
```bash
# 1. 触发 Redis 保存
redis-cli -n 1 SAVE

# 2. 复制 dump.rdb 文件
cp /var/lib/redis/dump.rdb /path/to/backup/dump_$(date +%Y%m%d).rdb
```

**依赖本地持久化备份**（推荐）:
```bash
# data/ 目录下的 JSON 文件即为备份
cp -r data/ backup/data_$(date +%Y%m%d)/
```

### 4.4 性能优化

**建议配置**（`redis.conf`）:
```conf
# 最大内存（根据实际情况调整）
maxmemory 256mb

# 淘汰策略（优先删除即将过期的 key）
maxmemory-policy volatile-ttl

# 持久化策略（推荐 RDB + AOF）
save 900 1
save 300 10
save 60 10000
appendonly yes
```

---

## 五、常见问题

### Q1: Redis 连接失败怎么办？

**错误信息**:
```
Redis 连接失败: Error 111 connecting to localhost:6379. Connection refused.
```

**解决方案**:
1. **检查 Redis 是否运行**:
   ```bash
   redis-cli ping  # 应返回 PONG
   ```

2. **启动 Redis**:
   ```bash
   # Linux/macOS
   sudo systemctl start redis
   # 或
   redis-server

   # Windows
   redis-server.exe
   ```

3. **检查配置**:
   - 确认 `.env` 中的 `REDIS_HOST` 和 `REDIS_PORT` 正确
   - 确认防火墙未阻止 6379 端口

**优雅降级**: 即使 Redis 连接失败，Creeper 仍可正常工作（但会失去去重功能）

---

### Q2: 如何查看某个 URL 是否已爬取？

```bash
# 1. 计算 URL 的 MD5
echo -n "https://example.com/page" | md5sum
# 输出: 5d41402abc4b2a76b9719d911017c592

# 2. 查询 Redis
redis-cli -n 1 HGETALL "creeper:url:5d41402abc4b2a76b9719d911017c592"
```

或使用 Python:
```python
from src.dedup import DedupManager

dedup = DedupManager()
if dedup.is_crawled("https://example.com/page"):
    print("已爬取")
else:
    print("未爬取")
```

---

### Q3: 如何强制重新爬取所有 URL？

**方法 1**: 使用 `--force` 参数（推荐）
```bash
python creeper.py input.md --force
```

**方法 2**: 清空 Redis 缓存
```bash
redis-cli -n 1 KEYS "creeper:url:*" | xargs redis-cli -n 1 DEL
```

**方法 3**: 使用清理脚本
```bash
./clean.sh  # 清理所有数据
```

---

### Q4: Cookie 过期后如何重新登录？

**自动检测过期**:
```python
cookie_mgr = CookieManager(storage_backend='redis')
if cookie_mgr.has_expired("example.com"):
    print("Cookie 已过期，需要重新登录")
```

**交互式登录**:
```bash
python creeper.py --login-url https://example.com/login
```

登录后 Cookie 自动保存到 Redis（7 天过期）

---

### Q5: 如何迁移数据到新 Redis 实例？

**方法 1**: 使用混合持久化（推荐）
```bash
# 1. 确保启用本地持久化
ENABLE_LOCAL_PERSISTENCE=true

# 2. 停止爬虫，数据已自动保存到 data/*.json

# 3. 修改 .env 中的 Redis 配置
REDIS_HOST=new-redis-host
REDIS_PORT=6379

# 4. 启动爬虫，数据自动从本地恢复
python creeper.py input.md
```

**方法 2**: Redis 数据迁移
```bash
# 使用 redis-cli --rdb 导出导入
redis-cli -n 1 --rdb dump.rdb
redis-cli -h new-host -n 1 --pipe < dump.rdb
```

---

### Q6: 文件聚合缓存失效怎么办？

**强制重新处理**:
```bash
python3 aggregator.py --folder ./src --output ./docs/summary.md --template code_summary --force
```

**清理特定缓存**:
```bash
# 手动删除缓存 key
redis-cli -n 1 DEL "creeper:aggregator:<output_file_md5>:files"
```

---

## 六、最佳实践

### 6.1 开发环境

- ✅ 使用 **DB 1**（避免与其他项目冲突）
- ✅ 启用 **混合持久化**（`ENABLE_LOCAL_PERSISTENCE=true`）
- ✅ 定期清理测试数据（`./clean.sh`）

### 6.2 生产环境

- ✅ 配置 **Redis 密码**（`REDIS_PASSWORD`）
- ✅ 启用 **RDB + AOF 持久化**
- ✅ 设置 **maxmemory** 和 **淘汰策略**
- ✅ 定期备份 `data/*.json` 文件
- ✅ 监控 Redis 内存和连接数

### 6.3 性能优化

- ✅ 使用 **Pipeline** 批量操作（已实现）
- ✅ 设置合理的 **过期时间**（URL 去重 30 天）
- ✅ 避免存储超大 Value（文件内容截断为 1MB）
- ✅ 使用 **SCAN** 代替 **KEYS**（避免阻塞）

---

## 七、架构图

```
┌─────────────────────────────────────────────────┐
│                  Creeper 应用                    │
├─────────────────┬─────────────┬─────────────────┤
│   dedup.py      │ cookie_mgr  │ file_aggregator │
│  (URL 去重)     │ (Cookie)    │   (文件缓存)     │
└────────┬────────┴──────┬──────┴─────────┬───────┘
         │               │                 │
         │  写入/查询    │  写入/查询      │  写入/查询
         ▼               ▼                 ▼
┌──────────────────────────────────────────────────┐
│              Redis (DB 1)                         │
│  ┌──────────────┬──────────────┬────────────┐   │
│  │ creeper:url: │creeper:cookie│creeper:     │   │
│  │ <md5>        │:<domain>     │aggregator:* │   │
│  └──────────────┴──────────────┴────────────┘   │
└──────────────────┬───────────────────────────────┘
                   │ 双写机制
                   ▼
┌──────────────────────────────────────────────────┐
│          本地持久化文件 (data/)                   │
│  ┌──────────────┬──────────────┬────────────┐   │
│  │dedup_cache   │cookies_cache │aggregator_ │   │
│  │.json         │.json         │cache.json  │   │
│  └──────────────┴──────────────┴────────────┘   │
└──────────────────────────────────────────────────┘
```

---

## 八、参考资源

- **Redis 官方文档**: https://redis.io/documentation
- **Redis Python 客户端**: https://github.com/redis/redis-py
- **Creeper 配置文档**: `src/config.py`
- **清理脚本**: `clean.sh`

---

**文档版本**: v1.0
**维护者**: Claude Code
**最后更新**: 2025-11-27
