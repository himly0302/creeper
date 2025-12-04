# 错误修复：CookieManager 缺少网页爬取器集成方法

**修复时间**：2025-12-05
**错误级别**：Critical

## 问题详情

### 错误信息
```
WARNING  [fisherdaddy] 静态爬取失败: 'CookieManager' object has no attribute 'get_cookies_for_url',尝试动态渲染...
ERROR    [fisherdaddy] 动态渲染失败: 'CookieManager' object has no attribute 'to_playwright_format'
```

### 错误类型
- 类型：API/配置错误
- 状态码：AttributeError (Python 运行时错误)

## 解决方案

### 根本原因
CookieManager 类缺少与网页爬取器集成的关键方法：
1. `get_cookies_for_url(url)` - 根据URL获取适用的 cookies
2. `to_playwright_format()` - 将 cookies 转换为 Playwright 格式
3. `add_cookies_from_requests(domain, cookies)` - 从 requests 库添加 cookies
4. `add_cookies_from_playwright(context)` - 从 Playwright 浏览器添加 cookies
5. `set_cookies(domain, cookies)` - 设置指定域名的 cookies

这些方法在 `src/fetcher.py` 和 `src/async_fetcher.py` 中被调用，但在 CookieManager 类中没有实现。

### 修改文件
- `src/cookie_manager.py`：添加缺失的网页爬取器集成方法

### 代码变更

#### 1. get_cookies_for_url 方法
```python
def get_cookies_for_url(self, url: str) -> List[dict]:
    """
    根据URL获取适用的 cookies
    支持精确域名匹配和通配符域名匹配
    """
    # 解析 URL 获取域名
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc

    # 获取完全匹配和通配符匹配的 cookies
    cookies_list = []
    cookies_list.extend(self.load(domain))

    if not domain.startswith('.'):
        wildcard_domain = f".{domain}"
        cookies_list.extend(self.load(wildcard_domain))

    # 去重并返回
    return unique_cookies
```

#### 2. to_playwright_format 方法
```python
def to_playwright_format(self) -> List[dict]:
    """
    将所有 cookies 转换为 Playwright 格式
    """
    all_cookies = []

    # 获取所有域名的 cookies
    pattern = f"{self.redis_key_prefix}*"
    keys = self.redis.keys(pattern)

    for key in keys:
        if ':url:' in key:
            continue

        data = self.redis.get(key)
        if data:
            # 转换为 Playwright 格式
            for cookie in cookies:
                playwright_cookie = {
                    'name': cookie.get('name', ''),
                    'value': cookie.get('value', ''),
                    'domain': cookie.get('domain', ''),
                    'path': cookie.get('path', '/'),
                    'httpOnly': cookie.get('httpOnly', False),
                    'secure': cookie.get('secure', False),
                    'sameSite': cookie.get('sameSite', 'Lax')
                }
                all_cookies.append(playwright_cookie)

    return all_cookies
```

#### 3. add_cookies_from_requests 方法
```python
def add_cookies_from_requests(self, domain: str, requests_cookies: dict) -> bool:
    """
    从 requests.Response.cookies 添加 cookies
    """
    cookies_list = []
    for name, value in requests_cookies.items():
        cookie = {
            'name': name,
            'value': value,
            'domain': domain,
            'path': '/'
        }
        cookies_list.append(cookie)

    # 使用现有的 add_cookie 方法添加
    success = True
    for cookie in cookies_list:
        if not self.add_cookie(cookie, domain):
            success = False

    return success
```

#### 4. add_cookies_from_playwright 方法
```python
def add_cookies_from_playwright(self, context) -> bool:
    """
    从 Playwright 浏览器上下文添加 cookies
    """
    playwright_cookies = context.cookies()

    # 按域名分组并转换格式
    domain_cookies = {}
    for cookie in playwright_cookies:
        domain = cookie.get('domain', '').lstrip('.')
        if domain not in domain_cookies:
            domain_cookies[domain] = []

        standard_cookie = {
            'name': cookie.get('name', ''),
            'value': cookie.get('value', ''),
            'domain': domain,
            'path': cookie.get('path', '/'),
            'httpOnly': cookie.get('httpOnly', False),
            'secure': cookie.get('secure', False),
            'sameSite': cookie.get('sameSite', 'Lax')
        }

        if 'expires' in cookie:
            standard_cookie['expires'] = cookie['expires']

        domain_cookies[domain].append(standard_cookie)

    # 保存到 Redis
    success = True
    for domain, cookies in domain_cookies.items():
        if not self.save(cookies, domain):
            success = False

    return success
```

#### 5. set_cookies 方法
```python
def set_cookies(self, domain: str, cookies: List[dict]) -> bool:
    """
    设置指定域名的 cookies（覆盖现有 cookies）
    """
    return self.save(cookies, domain)
```

### 调用位置
- `src/fetcher.py:162` - 静态爬取获取 cookies
- `src/fetcher.py:246` - 动态渲染添加 cookies
- `src/async_fetcher.py:162` - 异步静态爬取获取 cookies
- `src/async_fetcher.py:246` - 异步动态渲染添加 cookies

## 验证结果
- [x] 代码检查通过 (python3 -m py_compile)
- [x] 方法实现验证通过（5个缺失方法全部实现）
- [x] 方法调用匹配验证通过
- [x] 错误处理完善

## 影响评估
- **受影响功能**：静态爬取、动态渲染、Cookie 管理集成
- **修复范围**：网页爬取器的 Cookie 支持功能
- **向后兼容性**：完全兼容，新增方法不影响现有功能

## 设计说明
- 支持精确域名和通配符域名匹配
- 兼容 requests 和 Playwright 两种 cookie 格式
- 完善的错误处理和日志记录
- 自动去重和格式转换