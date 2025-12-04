# 错误修复：CookieManager 初始化参数不匹配

**修复时间**：2025-12-05
**错误级别**：Critical

## 问题详情

### 错误信息
```
Traceback (most recent call last):
  File "/home/lyf/workspaces/creeper/creeper.py", line 422, in <module>
    main()
  File "/home/lyf/workspaces/creeper/creeper.py", line 417, in main
    creeper = AsyncCrawler(args)
              ^^^^^^^^^^^^^^^^^^
  File "/home/lyf/workspaces/creeper/creeper.py", line 183, in __init__
    self.cookie_manager = CookieManager(
                          ^^^^^^^^^^^^^^
TypeError: CookieManager.__init__() got an unexpected keyword argument 'storage_backend'
```

### 错误类型
- 类型：API/配置错误
- 状态码：TypeError (Python 运行时错误)

## 解决方案

### 根本原因
CookieManager 类已经重构为仅支持 Redis 存储，但 creeper.py 中的调用代码仍使用旧的 API 接口，传递了不存在的参数：
- `storage_backend` (已移除)
- `cookies_file` (已移除)
- `format` (已移除)

### 修改文件
- `creeper.py`：修复所有 CookieManager 调用的参数

### 代码变更
```python
// 修改前 - SyncCrawler.__init__
if args.cookies_file:
    self.cookie_manager = CookieManager(
        cookies_file=args.cookies_file,
        format='json',
        storage_backend='file'
    )

// 修改后 - SyncCrawler.__init__
self.cookie_manager = CookieManager(
    redis_client=None,  # 延迟初始化
    redis_key_prefix=config.COOKIE_REDIS_KEY_PREFIX,
    expire_days=config.COOKIE_EXPIRE_DAYS
)
```

```python
// 修改前 - AsyncCrawler.__init__
if args.cookies_file:
    # 使用文件存储模式(向后兼容)
    self.cookie_manager = CookieManager(
        cookies_file=args.cookies_file,
        format='json',
        storage_backend='file'
    )
elif config.COOKIE_STORAGE == 'redis':
    # 使用 Redis 存储模式
    self.cookie_manager = CookieManager(
        storage_backend='redis',
        redis_client=None,  # 延迟初始化
        redis_key_prefix=config.COOKIE_REDIS_KEY_PREFIX,
        expire_days=config.COOKIE_EXPIRE_DAYS
    )

// 修改后 - AsyncCrawler.__init__
# 初始化 Cookie 管理器 (仅支持 Redis 模式)
self.cookie_manager = CookieManager(
    redis_client=None,  # 延迟初始化
    redis_key_prefix=config.COOKIE_REDIS_KEY_PREFIX,
    expire_days=config.COOKIE_EXPIRE_DAYS
)
```

```python
// 修改前 - 交互式登录函数
cookie_manager = CookieManager(
    storage_backend='redis',
    redis_client=dedup.redis,
    redis_key_prefix=config.COOKIE_REDIS_KEY_PREFIX,
    expire_days=config.COOKIE_EXPIRE_DAYS
)

// 修改后 - 交互式登录函数
cookie_manager = CookieManager(
    redis_client=dedup.redis,
    redis_key_prefix=config.COOKIE_REDIS_KEY_PREFIX,
    expire_days=config.COOKIE_EXPIRE_DAYS
)
```

```python
// 修复方法调用
// 修改前
cookie_manager.set_cookies(domain, cookies)
success = cookie_manager.save()

// 修改后
success = True
for domain, cookies in domain_cookies.items():
    if not cookie_manager.save(cookies, domain):
        success = False
```

```python
// 修复属性引用
// 修改前
if self.cookie_manager and self.cookie_manager.storage_backend == 'redis':
    self.cookie_manager.redis_client = self.dedup.redis
    # 重新加载 Cookie
    self.cookie_manager._load_all_from_redis()

// 修改后
# 设置 cookie_manager 的 redis_client
if self.cookie_manager:
    self.cookie_manager.redis_client = self.dedup.redis
```

## 验证结果
- [x] 代码检查通过 (python3 -m py_compile creeper.py)
- [x] 参数验证通过 (移除了所有旧参数)
- [x] 方法调用修复 (save 替代 set_cookies)
- [x] 属性引用修复 (移除 storage_backend 检查)

## 影响评估
- **受影响功能**：Cookie 管理、交互式登录
- **修复范围**：同步爬虫、异步爬虫、登录功能
- **向后兼容性**：已移除文件存储模式的支持