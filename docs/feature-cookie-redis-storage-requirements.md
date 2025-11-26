# Cookie 管理优化 - Redis 存储 + 浏览器交互 - 需求文档

> 生成时间: 2025-11-26
> 基于项目: Creeper 网页爬虫工具
> 技术栈: Python 3.8+ + asyncio + Playwright + Redis

---

## 项目概况

**技术栈**: Python 3.8+ + asyncio/aiohttp + Playwright 1.51+ + Redis 6.4+
**架构模式**: 模块化分层架构 (parser/fetcher/storage/dedup/cookie)
**代码风格**:
- 中文注释和日志
- 使用 dataclass 定义数据结构
- 统一的日志记录器
- 错误处理完善

**现有 Cookie 管理方式**:
- 使用 JSON/Pickle 文件存储 Cookie
- 手动创建 Cookie 文件或从响应中自动提取
- Cookie 按域名分组存储

---

## 改动点

### 要实现什么

**核心功能 1: 浏览器交互式登录**
- 使用 Playwright 打开浏览器窗口(非 headless 模式)
- 加载指定的登录页面
- 等待用户手动完成登录操作
- 用户关闭浏览器后自动提取 Cookie

**核心功能 2: Cookie 存储到 Redis**
- 将提取的 Cookie 保存到 Redis 而非文件
- 按域名分组存储,使用哈希结构
- 支持设置过期时间
- 后续访问时从 Redis 读取 Cookie

**核心功能 3: 新增 CLI 命令**
- 添加 `--login-url` 参数,指定需要登录的 URL
- 检测到该参数时,启动交互式登录流程
- 登录完成后自动保存 Cookie 到 Redis

### 与现有功能的关系

**依赖现有模块**:
- `src/dedup.py` - 复用 Redis 连接和配置
- `src/cookie_manager.py` - 扩展存储方式,添加 Redis 支持
- `src/async_fetcher.py` - 使用 Playwright 打开浏览器
- `src/config.py` - 复用 Redis 配置

**集成位置**:
- `creeper.py:parse_args()` - 添加 `--login-url` 参数
- `creeper_async.py:parse_args()` - 添加 `--login-url` 参数
- `src/cookie_manager.py` - 添加 Redis 存储方法

### 新增依赖

无需新增依赖,使用现有依赖:
- `redis` - 已有,用于 Cookie 存储
- `playwright` - 已有,用于浏览器交互

---

## 实现方案

### 需要修改的文件

```
src/cookie_manager.py       # 添加 Redis 存储支持
src/config.py                # 添加 Cookie 过期时间配置
creeper.py                   # 添加 --login-url 参数
creeper_async.py             # 添加 --login-url 参数和交互式登录流程
```

### 需要新增的文件

```
src/interactive_login.py     # 用途: 交互式登录模块(浏览器控制)
tests/test_login.md          # 用途: 测试用的登录 URL 列表
```

### 实现步骤

#### 步骤 1: 扩展 CookieManager 支持 Redis

**修改 `src/cookie_manager.py`**:

- [ ] 添加 `storage_backend` 参数 ('file' 或 'redis')
- [ ] 添加 `redis_client` 参数,接受 Redis 连接
- [ ] 实现 `_save_to_redis()` 方法:
  ```python
  def _save_to_redis(self, domain: str, cookies: List[dict]) -> bool:
      """将 Cookie 保存到 Redis (Hash 结构)"""
      key = f"{self.key_prefix}cookie:{domain}"
      # 使用 HSET 存储每个 Cookie
      # 设置过期时间
  ```
- [ ] 实现 `_load_from_redis()` 方法:
  ```python
  def _load_from_redis(self, domain: str) -> List[dict]:
      """从 Redis 加载 Cookie"""
      key = f"{self.key_prefix}cookie:{domain}"
      # 使用 HGETALL 读取
  ```
- [ ] 修改 `save()` 和 `load()` 方法,根据 `storage_backend` 选择存储方式
- [ ] 添加 `get_all_domains_from_redis()` 方法,列出所有已存储的域

#### 步骤 2: 实现交互式登录模块

**新建 `src/interactive_login.py`**:

```python
"""
交互式登录模块
使用 Playwright 打开浏览器,让用户手动登录,提取 Cookie
"""

async def interactive_login(url: str, timeout: int = 300) -> Dict[str, List[dict]]:
    """
    打开浏览器让用户登录,提取 Cookie

    Args:
        url: 登录页面 URL
        timeout: 等待超时时间(秒),默认 5 分钟

    Returns:
        Dict[domain, cookies]: 按域名分组的 Cookie

    流程:
    1. 使用 Playwright 启动浏览器(headless=False)
    2. 创建新页面并导航到 url
    3. 等待用户操作:
       - 监听页面关闭事件
       - 或者等待特定的成功标志(可选)
    4. 提取 context.cookies()
    5. 按域名分组返回
    """
    pass
```

- [ ] 实现主函数 `interactive_login()`
- [ ] 添加日志提示用户操作步骤
- [ ] 处理超时情况(抛出异常或返回空)
- [ ] 添加错误处理(浏览器启动失败等)

#### 步骤 3: 扩展配置文件

**修改 `src/config.py`**:

- [ ] 添加配置项:
  ```python
  # Cookie 配置
  COOKIE_STORAGE = os.getenv('COOKIE_STORAGE', 'redis')  # 'file' 或 'redis'
  COOKIE_EXPIRE_DAYS = int(os.getenv('COOKIE_EXPIRE_DAYS', 7))  # Cookie 过期天数
  COOKIE_REDIS_KEY_PREFIX = os.getenv('COOKIE_REDIS_KEY_PREFIX', 'creeper:cookie:')
  ```

**修改 `.env.example`**:

- [ ] 添加配置示例:
  ```bash
  # Cookie 管理
  COOKIE_STORAGE=redis           # Cookie 存储方式: file 或 redis
  COOKIE_EXPIRE_DAYS=7           # Cookie 在 Redis 中的过期天数
  COOKIE_REDIS_KEY_PREFIX=creeper:cookie:
  ```

#### 步骤 4: 集成到 CLI

**修改 `creeper_async.py`**:

- [ ] 在 `parse_args()` 添加参数:
  ```python
  parser.add_argument(
      '--login-url',
      type=str,
      default=None,
      help='需要登录的 URL,启动交互式登录流程'
  )
  ```

- [ ] 在 `AsyncCreeper.__init__()` 初始化时:
  ```python
  # 如果使用 Redis 存储,传入 redis_client
  if config.COOKIE_STORAGE == 'redis':
      self.cookie_manager = CookieManager(
          storage_backend='redis',
          redis_client=self.dedup.redis
      )
  ```

- [ ] 在 `main()` 函数中添加登录流程:
  ```python
  if args.login_url:
      logger.info(f"启动交互式登录: {args.login_url}")
      logger.info("请在打开的浏览器中完成登录,完成后关闭浏览器窗口")

      # 调用交互式登录
      domain_cookies = await interactive_login(args.login_url)

      # 保存到 cookie_manager
      for domain, cookies in domain_cookies.items():
          creeper.cookie_manager.set_cookies(domain, cookies)
          creeper.cookie_manager.save()  # 保存到 Redis

      logger.info(f"Cookie 已保存,共 {len(domain_cookies)} 个域")
      sys.exit(0)  # 登录完成后退出
  ```

**同样修改 `creeper.py`** (同步版本):
- [ ] 添加相同的 `--login-url` 参数
- [ ] 使用同步版本的 Playwright 实现交互式登录

#### 步骤 5: 测试

**创建测试文件 `tests/test_login.md`**:
```markdown
# 测试登录

## 需要登录的网站
https://example.com/login
```

**测试步骤**:
- [ ] 测试交互式登录流程:
  ```bash
  python creeper_async.py --login-url https://example.com/login
  ```
- [ ] 验证浏览器是否正确打开
- [ ] 手动登录后关闭浏览器
- [ ] 检查 Redis 中是否保存了 Cookie:
  ```bash
  redis-cli KEYS "creeper:cookie:*"
  redis-cli HGETALL "creeper:cookie:example.com"
  ```
- [ ] 测试使用已保存的 Cookie 爬取:
  ```bash
  python creeper_async.py tests/test_input.md
  ```
- [ ] 验证从 Redis 加载 Cookie 成功
- [ ] **回归测试**: 测试不使用 Cookie 的正常爬取
- [ ] **回归测试**: 测试原有的文件存储方式(设置 `COOKIE_STORAGE=file`)

#### 步骤 6: 文档更新

- [ ] 更新 `README.md`:
  - 在特性列表添加 "交互式登录支持"
  - 添加使用示例:
    ```bash
    # 交互式登录并保存 Cookie
    python creeper_async.py --login-url https://example.com/login

    # 后续爬取自动使用 Cookie
    python creeper_async.py input.md
    ```
  - 在 FAQ 添加 Q8: 如何使用交互式登录?

- [ ] 更新 `CHANGELOG.md`:
  ```markdown
  ## [1.2.0] - 2025-11-26

  ### Added
  - 🌐 **交互式登录**: 使用浏览器手动登录,自动提取 Cookie
  - 💾 **Cookie Redis 存储**: Cookie 存储到 Redis,支持跨会话复用
  - 🔑 **自动 Cookie 管理**: 登录一次,后续爬取自动使用

  ### Changed
  - 🔧 `CookieManager` 支持 Redis 存储后端
  - 📋 新增 CLI 参数: `--login-url`
  - ⚙️ 新增配置项: `COOKIE_STORAGE`, `COOKIE_EXPIRE_DAYS`

  ### Technical
  - 新增 `src/interactive_login.py` 交互式登录模块
  - Cookie 使用 Redis Hash 结构存储,按域名分组
  - 支持设置 Cookie 过期时间(默认 7 天)
  ```

- [ ] 更新 `.env.example` 添加新配置

---

## 使用方式

### 交互式登录

```bash
# 启动交互式登录
python creeper_async.py --login-url https://example.com/login

# 操作步骤:
# 1. 程序会打开浏览器并加载登录页面
# 2. 在浏览器中手动完成登录
# 3. 登录成功后,关闭浏览器窗口
# 4. Cookie 自动保存到 Redis
```

### 使用已保存的 Cookie 爬取

```bash
# Cookie 已在 Redis 中,直接爬取
python creeper_async.py input.md

# 程序会自动从 Redis 加载 Cookie
```

### 查看 Redis 中的 Cookie

```bash
# 查看所有 Cookie 域
redis-cli KEYS "creeper:cookie:*"

# 查看特定域的 Cookie
redis-cli HGETALL "creeper:cookie:example.com"

# 清除所有 Cookie
redis-cli DEL $(redis-cli KEYS "creeper:cookie:*")
```

### 配置项

**`.env` 文件**:
```bash
# Cookie 存储方式
COOKIE_STORAGE=redis           # 'file' 或 'redis'

# Cookie 过期时间
COOKIE_EXPIRE_DAYS=7           # Redis 中的过期天数

# Redis Key 前缀
COOKIE_REDIS_KEY_PREFIX=creeper:cookie:
```

---

## 完成检查清单

**代码质量**:
- [ ] 遵循项目代码风格(中文注释,统一日志)
- [ ] 添加必要注释和文档字符串
- [ ] 错误处理完善(浏览器启动失败、Redis 连接失败)
- [ ] 无安全漏洞(Cookie 敏感信息处理)

**测试**:
- [ ] 交互式登录测试通过
- [ ] Cookie 保存到 Redis 成功
- [ ] 从 Redis 加载 Cookie 成功
- [ ] 使用 Cookie 爬取测试通过
- [ ] 现有功能无影响(回归测试)
- [ ] 边界条件处理(超时、用户取消等)

**文档**:
- [ ] README 已更新(特性、使用示例、FAQ)
- [ ] CHANGELOG 已更新
- [ ] .env.example 已更新
- [ ] 配置文档已更新

---

## CHANGELOG.md 更新指南

**版本号**: `1.2.0` (新增功能,向后兼容)

**更新位置**: `CHANGELOG.md` 文件顶部

**内容**:
```markdown
## [1.2.0] - 2025-11-26

### Added
- 🌐 **交互式登录功能**: 使用 Playwright 打开浏览器让用户手动登录
  - 支持 `--login-url` 参数启动交互式登录
  - 登录完成后自动提取并保存 Cookie
  - 相关文件: `src/interactive_login.py`
- 💾 **Cookie Redis 存储**: Cookie 存储到 Redis 替代文件存储
  - 使用 Redis Hash 结构存储,按域名分组
  - 支持设置过期时间(默认 7 天)
  - 跨会话复用 Cookie
  - 相关文件: `src/cookie_manager.py`

### Changed
- 🔧 `CookieManager` 支持可选的存储后端 ('file' 或 'redis')
- 📋 新增 CLI 参数: `--login-url <URL>`
- ⚙️ 新增配置项: `COOKIE_STORAGE`, `COOKIE_EXPIRE_DAYS`, `COOKIE_REDIS_KEY_PREFIX`

### Technical
- Cookie 在 Redis 中使用 `creeper:cookie:{domain}` 作为 Key
- 使用 HSET/HGETALL 操作 Cookie 数据
- Playwright 以非 headless 模式打开,等待用户操作
- 支持超时控制(默认 5 分钟)
```

---

## 注意事项

**技术风险**:
- Playwright 浏览器启动可能较慢,需要合理设置超时时间
- Redis 存储的 Cookie 敏感信息,需要确保 Redis 访问安全
- 用户可能在登录过程中取消,需要优雅处理

**兼容性**:
- ✅ 向后兼容: 原有的文件存储方式仍然可用(设置 `COOKIE_STORAGE=file`)
- ✅ 不破坏现有 API: 原有的 `--cookies-file` 参数仍然有效
- ✅ 默认行为不变: 未设置 `--login-url` 时,行为与之前一致

**性能影响**:
- 交互式登录是一次性操作,不影响正常爬取性能
- Redis 读取比文件读取更快,可能有轻微性能提升
- Cookie 过期后需要重新登录

**用户体验**:
- 首次使用需要手动登录,后续自动使用 Cookie
- 登录流程直观,用户在真实浏览器中操作
- Cookie 过期提示需要明确,避免用户困惑

---

## 实现优先级

**P0 (必须实现)**:
1. ✅ 扩展 `CookieManager` 支持 Redis 存储
2. ✅ 实现 `interactive_login()` 函数
3. ✅ 添加 `--login-url` CLI 参数
4. ✅ 集成到主流程

**P1 (重要功能)**:
1. ✅ 添加配置项(`COOKIE_STORAGE`, `COOKIE_EXPIRE_DAYS`)
2. ✅ 完善错误处理和超时控制
3. ✅ 更新文档

**P2 (可选优化)**:
1. 添加 Cookie 管理命令(列出、删除特定域的 Cookie)
2. 支持多账号登录(同一域名不同账号)
3. Cookie 过期自动提醒

---

**开发建议**:
1. 先实现 Redis 存储,测试通过后再实现交互式登录
2. 交互式登录可以先用简单的测试页面验证流程
3. 确保 Redis 存储与文件存储可以共存和切换
4. 充分测试超时、取消等边界情况
5. 更新 `clean.sh` 脚本,添加清理 Redis Cookie 的功能

---

**安全建议**:
- Cookie 是敏感信息,确保 Redis 有密码保护
- 文档中提醒用户不要在公共 Redis 服务器上存储 Cookie
- 考虑添加 Cookie 加密存储功能(V1.3)
