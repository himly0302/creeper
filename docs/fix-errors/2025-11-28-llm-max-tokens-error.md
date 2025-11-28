# 错误修复：LLM API max_tokens 参数超出范围

**修复时间**：2025-11-28
**错误级别**：High

## 问题详情

### 错误信息
```
ERROR     LLM API 调用失败: Error code: 400 - {'error': {'message': 'Invalid max_tokens value, the valid range of max_tokens is [1, 8192]', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_request_error'}}
INFO      ✓ 已处理: outputs/claude使用文档/个人文章/claude-code-最佳实践-anthropic.md → /home/lyf/workspaces/creeper/parsers/claude使用文档/claude-code-最佳实践-anthropic.md
```

### 错误类型
- **类型**：配置错误 / API 参数错误
- **状态码**：400 (Bad Request)
- **影响范围**：
  - `parser.py` 文件解析功能
  - `aggregator.py` 文件整合功能

### 问题分析

**问题 1: max_tokens 配置值超出 API 限制**
- 配置文件 `.env` 中设置 `AGGREGATOR_MAX_TOKENS=664000`（64 万 tokens）
- DeepSeek API 实际限制为 `[1, 8192]`
- 配置值超出 API 限制 81 倍

**问题 2: 错误处理逻辑缺陷**
- LLM API 调用失败后，`parse_file()` 方法返回错误信息字符串而不是抛出异常
- 错误信息被当作正常内容写入文件
- 日志打印"✓ 已处理"，误导用户认为处理成功
- 生成的文件内容为：
  ```markdown
  # 解析失败

  错误信息: Error code: 400 - {...}

  ## 原始文件
  ```

### 复现步骤
```bash
# 1. 配置错误的 max_tokens 值
echo "AGGREGATOR_MAX_TOKENS=664000" >> .env

# 2. 运行文件解析
python parser.py --input-folder ./outputs/claude使用文档/个人文章 \
  --output-folder ./parsers/claude使用文档 \
  --template parser/doc_parser

# 3. 观察日志：显示 API 调用失败，但仍然打印"✓ 已处理"
# 4. 检查生成的文件：包含错误信息而非解析结果
```

## 解决方案

### 根本原因
1. **配置默认值错误**：`config.py` 中 `AGGREGATOR_MAX_TOKENS` 默认值设为 `64000`，超出 DeepSeek API 的 `8192` 限制
2. **错误处理不当**：异常被捕获后返回错误字符串，而不是抛出异常，导致调用方无法区分成功和失败

### 修复策略
1. 修改默认配置值为 `8000`，符合 API 限制
2. 改进错误处理：LLM API 调用失败时抛出异常
3. 确保失败时不生成文件

### 修改文件

**文件 1: `src/config.py`**
- 修改 `AGGREGATOR_MAX_TOKENS` 默认值从 `64000` 改为 `8000`
- 添加注释说明 API 限制

**文件 2: `.env.example`**
- 修改示例配置值从 `64000` 改为 `8000`
- 添加注释说明 DeepSeek API 限制范围

**文件 3: `src/file_parser.py`**
- 修改 `parse_file()` 方法的异常处理逻辑
- LLM API 调用失败时抛出 `RuntimeError` 而不是返回错误字符串
- `_process_file()` 方法捕获异常时不再写入文件

**文件 4: `src/file_aggregator.py`**
- 修改 `aggregate()` 方法的异常处理逻辑
- LLM API 调用失败时抛出 `RuntimeError`

### 代码变更

#### src/config.py
```python
# 修改前
AGGREGATOR_MAX_TOKENS = int(os.getenv('AGGREGATOR_MAX_TOKENS', 64000))

# 修改后
AGGREGATOR_MAX_TOKENS = int(os.getenv('AGGREGATOR_MAX_TOKENS', 8000))  # DeepSeek 限制: [1, 8192]
```

#### .env.example
```bash
# 修改前
# LLM 返回最大 token 数
AGGREGATOR_MAX_TOKENS=64000

# 修改后
# LLM 返回最大 token 数 (DeepSeek 限制: 1-8192)
AGGREGATOR_MAX_TOKENS=8000
```

#### src/file_parser.py
```python
# 修改前 (parse_file 方法)
except Exception as e:
    logger.error(f"LLM API 调用失败: {e}")
    return f"# 解析失败\n\n错误信息: {e}\n\n## 原始文件\n\n文件路径: {file_item.path}\n\n```\n{file_item.content}\n```"

# 修改后
except Exception as e:
    logger.error(f"LLM API 调用失败: {e}")
    # 抛出异常而不是返回错误字符串，让调用方决定如何处理
    raise RuntimeError(f"解析文件 {file_item.path} 失败: {e}") from e
```

```python
# 修改前 (_process_file 方法)
except Exception as e:
    logger.error(f"✗ 处理失败: {file_item.path} - {str(e)}", exc_info=config.DEBUG)

# 修改后
except Exception as e:
    logger.error(f"✗ 处理失败: {file_item.path} - {str(e)}", exc_info=config.DEBUG)
    # 不再生成失败的文件
```

#### src/file_aggregator.py
```python
# 修改前
except Exception as e:
    logger.error(f"LLM API 调用失败: {e}")
    return f"# 整合失败\n\n错误信息: {e}\n\n## 文件列表\n\n{files_content}"

# 修改后
except Exception as e:
    logger.error(f"LLM API 调用失败: {e}")
    # 抛出异常而不是返回错误字符串
    raise RuntimeError(f"整合失败: {e}") from e
```

## 验证结果

### 配置验证
```bash
$ grep AGGREGATOR_MAX_TOKENS .env
AGGREGATOR_MAX_TOKENS=8000
```

### 功能验证
```bash
$ python parser.py --input-folder ./outputs/claude使用文档/个人文章 \
  --output-folder ./parsers/claude使用文档 \
  --template parser/doc_parser --force

INFO      ✓ 已处理: outputs/claude使用文档/个人文章/claude-code-最佳实践-anthropic.md → /home/lyf/workspaces/creeper/parsers/claude使用文档/claude-code-最佳实践-anthropic.md
```

### 文件内容验证
```bash
$ head -30 parsers/claude使用文档/claude-code-最佳实践-anthropic.md
# Claude Code 最佳实践 - 文档分析

## 文档概览
**文件路径**：outputs/claude使用文档/个人文章/claude-code-最佳实践-anthropic.md
**文档类型**：最佳实践指南/教程
**主题**：Claude Code 命令行工具的高效使用方法和最佳实践
...
```

✅ 文件内容正常，包含解析后的结构化内容，而非错误信息

### 测试检查清单
- [x] 配置值已修改为合法范围
- [x] LLM API 调用成功
- [x] 生成文件内容正确
- [x] 错误处理逻辑正确（失败时不生成文件）
- [x] 日志输出正确（成功显示"✓ 已处理"，失败显示"✗ 处理失败"）

## 影响评估

### 用户侧影响
- **已有配置**：用户需要手动修改 `.env` 文件中的 `AGGREGATOR_MAX_TOKENS` 值
- **新用户**：从 `.env.example` 复制配置时将获得正确的默认值
- **错误文件**：已生成的错误文件需要手动删除并重新解析

### 修复建议
用户需要执行以下操作：
```bash
# 1. 修改配置文件
sed -i 's/AGGREGATOR_MAX_TOKENS=.*/AGGREGATOR_MAX_TOKENS=8000/' .env

# 2. 删除错误生成的文件
rm -f parsers/*/解析失败*.md

# 3. 重新运行解析
python parser.py --input-folder <input> --output-folder <output> --template <template> --force
```

## 后续优化建议

1. **配置验证**：在启动时验证配置值是否在合法范围内
2. **API 兼容性检测**：根据不同 LLM 服务商动态调整 `max_tokens` 上限
3. **更友好的错误提示**：在日志中提示用户检查配置文件
4. **单元测试**：添加配置验证和错误处理的单元测试
