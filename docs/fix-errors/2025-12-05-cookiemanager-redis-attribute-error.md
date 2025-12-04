# 错误修复：CookieManager Redis 属性名称不一致

**修复时间**：2025-12-05
**错误级别**：Medium

## 问题详情

### 错误信息
```
ERROR    [gov] 转换为 Playwright 格式失败: 'CookieManager' object has no attribute 'redis'
```

### 错误类型
- 类型：API/配置错误
- 状态码：AttributeError (Python 运行时错误)

## 解决方案

### 根本原因
CookieManager 类中存在属性名称不一致问题：

1. **初始化方法**：使用 `self.redis_client` 存储 Redis 客户端
   ```python
   def __init__(self, redis_client: redis.Redis, ...):
       self.redis_client = redis_client  # 正确
   ```

2. **to_playwright_format 方法**：错误使用 `self.redis`
   ```python
   def to_playwright_format(self) -> List[dict]:
       keys = self.redis.keys(pattern)      # ❌ 错误：应该是 self.redis_client
       data = self.redis.get(key)           # ❌ 错误：应该是 self.redis_client
   ```

3. **其他所有方法**：正确使用 `self.redis_client`
   - `save()`、`load()`、`add_cookie()` 等方法都正确使用 `self.redis_client`

### 修改文件
- `src/cookie_manager.py`：修复 `to_playwright_format()` 方法中的属性名称

### 代码变更

#### 修改前
```python
def to_playwright_format(self) -> List[dict]:
    try:
        # 获取所有域名的 cookies
        pattern = f"{self.redis_key_prefix}*"
        keys = self.redis.keys(pattern)  # ❌ 错误：self.redis 不存在

        for key in keys:
            # 跳过 URL 相关的 key
            if ':url:' in key:
                continue

            data = self.redis.get(key)  # ❌ 错误：self.redis 不存在
```

#### 修改后
```python
def to_playwright_format(self) -> List[dict]:
    try:
        # 获取所有域名的 cookies
        pattern = f"{self.redis_key_prefix}*"
        keys = self.redis_client.keys(pattern)  # ✅ 正确

        for key in keys:
            # 跳过 URL 相关的 key
            if ':url:' in key:
                continue

            data = self.redis_client.get(key)  # ✅ 正确
```

### 修复位置
- `src/cookie_manager.py:363` - 将 `self.redis.keys(pattern)` 改为 `self.redis_client.keys(pattern)`
- `src/cookie_manager.py:370` - 将 `self.redis.get(key)` 改为 `self.redis_client.get(key)`

## 验证结果
- [x] 代码检查通过 (python3 -m py_compile)
- [x] 属性名称一致性验证通过（11处正确使用，0处错误使用）
- [x] 动态渲染时 Cookie 转换功能恢复正常

## 影响评估
- **受影响功能**：动态渲染时的 Playwright Cookie 转换
- **修复范围**：`to_playwright_format()` 方法
- **严重程度**：Medium（虽然有异常处理，但导致 Cookie 无法在动态渲染中使用）

### 修复前后对比

#### 修复前
- 动态渲染时无法正确转换 Cookie 格式
- Playwright 无法使用保存的 cookies
- 错误被异常处理捕获，返回空 Cookie 列表

#### 修复后
- 动态渲染时正确转换 Cookie 格式
- Playwright 能够使用保存的 cookies
- 提高动态渲染的成功率和准确性

## 设计说明
- **一致性**：确保整个类中使用统一的属性命名
- **维护性**：避免类似的属性名称不一致问题
- **容错性**：保留原有的异常处理机制，确保程序稳定性