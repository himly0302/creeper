# Redis 本地持久化 - 需求文档

> 生成时间: 2025-11-27
> 基于项目: Creeper 网页爬虫工具
> 技术栈: Python 3.8+ + asyncio + Redis

---

## 项目概况

**技术栈**: Python 3.8+ + asyncio/aiohttp + Redis 6.4+ + Trafilatura/Playwright
**架构模式**: 模块化分层架构 (CLI → 爬虫引擎 → 去重/存储 → 输出)
**代码风格**: snake_case 命名 / 中文文档字符串 / 完善的异常处理

**当前 Redis 使用情况**:
- **去重存储**: `creeper:url:{md5}` (Hash 结构, 30天过期)
- **Cookie 存储**: `creeper:cookie:{domain}` (Hash 结构, 7天过期)
- **当前持久化**: 仅依赖 Redis 内存, 重启后数据可能丢失

---

## 改动点

### 要实现什么
- **核心功能 1**: 混合存储 - 每次操作同时写入 Redis 和本地文件
- **核心功能 2**: 启动时自动从本地文件恢复数据到 Redis (如 Redis 为空)
- **核心功能 3**: 支持定期同步 Redis 数据到本地文件

### 与现有功能的关系
- **依赖现有模块**:
  - `dedup.py` - 扩展去重管理器,添加本地存储层
  - `cookie_manager.py` - 已支持文件存储,需统一为混合存储
- **集成位置**:
  - `src/dedup.py:1-213` - 在 DedupManager 添加 JSON 文件存储
  - `src/cookie_manager.py:1-510` - 统一 Redis+文件双写逻辑
  - `src/config.py:1-145` - 添加持久化配置项

### 新增依赖 (如有)
无新增依赖 (使用 Python 标准库 json 模块)

---

## 实现方案

### 需要修改的文件
```
src/dedup.py              # 添加本地文件存储层 (JSON)
src/cookie_manager.py     # 统一双写逻辑,确保 Redis+文件同时更新
src/config.py             # 添加持久化配置项
```

### 需要新增的文件
```
data/dedup_cache.json     # 去重数据本地缓存文件
data/cookies_cache.json   # Cookie 数据本地缓存文件 (备用)
```

### 实现步骤

**步骤 1: 环境准备**
- [x] 创建数据目录: `mkdir -p data`
- [x] 确认 Redis 配置正确 (.env 文件)

**步骤 2: 核心实现**
- [ ] **修改 config.py**: 添加持久化配置
  ```python
  # 持久化配置
  ENABLE_LOCAL_PERSISTENCE = os.getenv('ENABLE_LOCAL_PERSISTENCE', 'true').lower() == 'true'
  DEDUP_CACHE_FILE = os.getenv('DEDUP_CACHE_FILE', 'data/dedup_cache.json')
  COOKIE_CACHE_FILE = os.getenv('COOKIE_CACHE_FILE', 'data/cookies_cache.json')
  SYNC_INTERVAL_SECONDS = int(os.getenv('SYNC_INTERVAL_SECONDS', 300))  # 5分钟
  ```

- [ ] **扩展 DedupManager (dedup.py)**:
  - 添加 `_load_from_file()` 方法: 从 JSON 加载去重记录
  - 添加 `_save_to_file()` 方法: 保存去重记录到 JSON
  - 修改 `mark_crawled()`: 同时写入 Redis 和本地文件
  - 添加 `_sync_file_to_redis()`: 启动时恢复数据
  - 添加错误处理: 文件损坏时跳过,使用 Redis

- [ ] **统一 CookieManager 双写 (cookie_manager.py)**:
  - 修改 `save()` 方法: 同时写入 Redis 和文件
  - 修改 `load()` 方法: 优先 Redis, 降级文件
  - 添加 `_merge_storage()`: 合并 Redis 和文件数据

- [ ] **添加数据完整性检查**:
  - JSON 文件包含版本号和校验和
  - 加载失败时回退到空数据 + 日志告警

**步骤 3: 集成到现有系统**
- [ ] **修改 creeper.py**: 启动时触发数据恢复
  ```python
  # 初始化时
  dedup = DedupManager()
  dedup.restore_from_file_if_needed()
  ```

- [ ] **添加定期同步** (可选):
  - 在异步爬虫中添加后台任务,每 N 分钟同步一次
  - 使用 `asyncio.create_task()` 非阻塞执行

- [ ] **更新 clean.sh**: 添加清理本地缓存选项
  ```bash
  rm -f data/dedup_cache.json
  rm -f data/cookies_cache.json
  ```

**步骤 4: 测试**
- [ ] **单元测试**:
  - 测试 `mark_crawled()` 是否同时写入 Redis + 文件
  - 测试停止 Redis 后,数据能从文件恢复
  - 测试文件损坏时程序不崩溃

- [ ] **回归测试现有功能** (必须!):
  - 正常爬取流程不受影响
  - Redis 仍为主存储,文件为备份
  - Cookie 管理功能正常

- [ ] **压力测试**:
  - 大量 URL 去重时文件 I/O 性能
  - 并发写入时文件锁问题

**步骤 5: 文档更新**
- [ ] 更新 README.md:
  - 添加持久化配置说明
  - 说明 Redis + 文件双写机制

- [ ] 更新 CHANGELOG.md (见下方)

- [ ] 更新 .env.example (如有):
  ```bash
  ENABLE_LOCAL_PERSISTENCE=true
  DEDUP_CACHE_FILE=data/dedup_cache.json
  SYNC_INTERVAL_SECONDS=300
  ```

**步骤 6: 提交代码**
- [ ] 使用 git 提交: `git commit -m "feat: Redis 本地持久化"`

---

## 使用方式

### 配置项 (环境变量)
```bash
# .env 文件
ENABLE_LOCAL_PERSISTENCE=true           # 启用本地持久化 (默认 true)
DEDUP_CACHE_FILE=data/dedup_cache.json  # 去重数据缓存路径
COOKIE_CACHE_FILE=data/cookies_cache.json # Cookie 缓存路径 (可选)
SYNC_INTERVAL_SECONDS=300               # 定期同步间隔 (秒, 0=禁用)
```

### 使用方式
```bash
# 正常使用,自动双写
python creeper.py input.md

# 停止 Redis 后,数据从文件自动恢复
docker stop redis
python creeper.py input.md  # 自动从 data/dedup_cache.json 恢复

# 清理本地缓存
rm data/dedup_cache.json
```

### 数据文件格式
```json
{
  "version": "1.0",
  "updated_at": "2025-11-27T10:30:00",
  "data": {
    "url_md5_1": {
      "url": "https://example.com",
      "crawled_at": "2025-11-27 10:00:00",
      "status": "success"
    }
  }
}
```

---

## 完成检查清单

**代码质量**:
- [ ] 遵循项目代码风格 (snake_case, 中文注释)
- [ ] 添加必要的文档字符串
- [ ] 异常处理完善 (文件 I/O 失败不影响主流程)
- [ ] 无安全漏洞 (文件路径验证, 避免路径遍历)

**测试**:
- [ ] 新功能测试通过 (双写、恢复、降级)
- [ ] 现有功能无影响 (爬虫、去重、翻译正常)
- [ ] 边界条件处理 (文件损坏、权限不足、磁盘满)

**文档**:
- [ ] README 已更新 (持久化说明)
- [ ] CHANGELOG 已更新 (见下方指南)
- [ ] 配置文档已更新 (.env.example)

---

## CHANGELOG.md 更新指南

**版本号规则**: 向后兼容的新功能 → MINOR 版本 (1.5.0)

**更新位置**: 文件顶部添加新版本

**模板**:
```markdown
## [1.5.0] - 2025-11-27

### Added
- **持久化**: Redis 本地持久化功能 - 混合存储模式
  - 支持 Redis + 本地文件双写,确保数据不丢失
  - 启动时自动从 JSON 文件恢复去重和 Cookie 数据
  - 支持定期同步 Redis 数据到本地 (可配置间隔)
  - 相关文件: `src/dedup.py`, `src/cookie_manager.py`, `src/config.py`
  - 新增配置: `ENABLE_LOCAL_PERSISTENCE`, `DEDUP_CACHE_FILE`, `SYNC_INTERVAL_SECONDS`
```

---

## 提交代码

在需求实现完成后,使用 git 提交:

```bash
# 添加所有修改的文件
git add .

# 提交,commit 信息使用需求文档的标题
git commit -m "feat: Redis 本地持久化"
```

---

## 注意事项

**技术风险**:
- **文件 I/O 性能**: 大量 URL 时频繁写文件可能影响性能 → 批量写入或定期同步
- **并发写入冲突**: 异步并发时可能同时写文件 → 使用文件锁 (fcntl) 或 asyncio.Lock
- **磁盘空间**: 长期运行可能积累大量数据 → 定期清理过期数据 (30天)

**兼容性**:
- ✅ 向后兼容 (默认启用,可通过环境变量禁用)
- ✅ 不破坏现有 API (DedupManager/CookieManager 接口不变)
- ❌ 不需要迁移脚本 (新功能,无历史数据迁移)

**性能优化建议**:
- 使用内存缓冲区,每 N 次操作批量写入文件
- 定期同步模式: 仅定时全量同步,不每次写入
- 异步文件 I/O: 使用 aiofiles 库 (如需要)

---

## 实现细节参考

### DedupManager 双写示例
```python
def mark_crawled(self, url: str, expire_days: int = 30) -> bool:
    """标记 URL 已爬取,同时写入 Redis 和本地文件"""
    try:
        # 1. 写入 Redis (主存储)
        redis_success = self._mark_redis(url, expire_days)

        # 2. 写入本地文件 (备份)
        if config.ENABLE_LOCAL_PERSISTENCE:
            self._mark_file(url)

        return redis_success
    except Exception as e:
        logger.error(f"标记爬取失败: {url}, 错误: {e}")
        return False

def _mark_file(self, url: str):
    """写入本地文件"""
    cache_file = Path(config.DEDUP_CACHE_FILE)
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    # 加载现有数据
    data = self._load_cache_file()

    # 更新数据
    url_md5 = hashlib.md5(url.encode()).hexdigest()
    data['data'][url_md5] = {
        'url': url,
        'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'success'
    }
    data['updated_at'] = datetime.now().isoformat()

    # 原子写入 (先写临时文件,再重命名)
    temp_file = cache_file.with_suffix('.tmp')
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    temp_file.replace(cache_file)
```

### 数据恢复逻辑
```python
def restore_from_file_if_needed(self):
    """启动时从文件恢复数据到 Redis (如 Redis 为空)"""
    if not config.ENABLE_LOCAL_PERSISTENCE:
        return

    try:
        # 检查 Redis 是否为空
        if self.redis.dbsize() > 0:
            logger.info("Redis 已有数据,跳过恢复")
            return

        # 从文件加载
        cache_file = Path(config.DEDUP_CACHE_FILE)
        if not cache_file.exists():
            logger.info("本地缓存文件不存在,跳过恢复")
            return

        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 批量写入 Redis
        restored_count = 0
        for url_md5, info in data.get('data', {}).items():
            key = self._get_key(info['url'])
            self.redis.hset(key, mapping=info)
            self.redis.expire(key, 30 * 86400)  # 30天
            restored_count += 1

        logger.info(f"从本地文件恢复 {restored_count} 条去重记录")
    except Exception as e:
        logger.error(f"恢复数据失败: {e},继续使用空 Redis")
```

---
