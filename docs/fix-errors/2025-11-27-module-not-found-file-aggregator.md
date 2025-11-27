# 错误修复：file_aggregator 模块缺失

**修复时间**：2025-11-27
**错误级别**：Critical

## 问题详情

### 错误信息
```
Traceback (most recent call last):
  File "/home/lyf/workspaces/creeper/aggregator.py", line 23, in <module>
    from src.file_aggregator import FileScanner, AggregatorCache, LLMAggregator
ModuleNotFoundError: No module named 'src.file_aggregator'
```

### 错误类型
- 类型：模块导入错误
- 状态码：N/A（运行时错误）
- 影响范围：文件夹内容 LLM 整合功能（aggregator.py）完全不可用

### 复现步骤
```bash
source venv/bin/activate
python3 aggregator.py --list-templates
```

### 根本原因
在实现 v1.6.0 文件夹内容 LLM 整合功能时，由于 Write 工具在处理包含大量中文注释的 Python 文件时遇到编码问题，导致 `src/file_aggregator.py` 文件未能成功创建。该文件包含三个核心类：
- `FileScanner`：文件扫描器
- `AggregatorCache`：Redis 缓存管理器
- `LLMAggregator`：LLM 整合器

## 解决方案

### 修复策略
1. 使用 Bash heredoc 方式创建 `src/file_aggregator.py` 文件，避免编码问题
2. 修复 `aggregator.py` 中的参数解析逻辑，使 `--list-templates` 不依赖其他必需参数

### 修改文件
- `src/file_aggregator.py`：新建文件（核心模块）
- `aggregator.py`：修复命令行参数解析逻辑

### 代码变更

**1. 创建 src/file_aggregator.py**

新建文件，包含以下核心类：

```python
class FileScanner:
    """文件扫描器 - 递归扫描文件夹，过滤文件类型，计算文件哈希"""
    def scan_directory(self, folder_path: str, extensions: List[str]) -> List[FileItem]
    def compute_file_hash(file_path: str) -> str

class AggregatorCache:
    """文件聚合缓存管理器 - 基于 Redis 的增量更新缓存"""
    def get_new_files(self, folder: str, current_files: List[FileItem], output_file: str) -> List[FileItem]
    def update_processed_files(self, output_file: str, folder: str, files: List[FileItem])

class LLMAggregator:
    """LLM 文件整合器 - 调用 DeepSeek API 整合文件内容"""
    async def aggregate(self, files: List[FileItem], prompt_template: str, existing_content: Optional[str]) -> str
```

**2. 修复 aggregator.py 参数解析**

```python
# 修改前（问题代码）
parser.add_argument('--folder', required=True, help='要扫描的文件夹路径')
parser.add_argument('--output', required=True, help='输出文件路径')
parser.add_argument('--template', required=True, help='提示词模板名称')

# 修改后（移除 required=True，改为手动验证）
parser.add_argument('--folder', help='要扫描的文件夹路径')
parser.add_argument('--output', help='输出文件路径')
parser.add_argument('--template', help='提示词模板名称')

# 添加参数验证逻辑
if args.list_templates:
    # 列出模板后直接退出，无需验证其他参数
    template_mgr = PromptTemplateManager()
    templates = template_mgr.list_templates()
    # ... 显示模板列表
    sys.exit(0)

# 验证必需参数（仅在非 --list-templates 模式下）
if not args.folder or not args.output or not args.template:
    parser.error("--folder, --output 和 --template 是必需参数")
```

## 验证结果

```bash
$ python3 aggregator.py --list-templates
可用的提示词模板:
  - code_summary
  - data_analysis
  - doc_merge
```

- [x] 模块导入成功
- [x] --list-templates 命令正常工作
- [x] 无新增错误

## 技术要点

**编码问题处理**：
- 使用 Bash heredoc (`cat > file << 'ENDOFFILE'`) 创建包含 UTF-8 中文的 Python 文件
- 避免 Write 工具在处理大文件时的编码问题

**文件结构**：
- 忽略目录：`.git`, `__pycache__`, `node_modules`, `.venv`, `venv`, `data`
- 忽略文件：`.env`, `.env.local`, `.DS_Store`
- 最大文件大小：1MB（可配置）

**缓存机制**：
- Redis key 格式：`creeper:aggregator:<output_file_md5>:files`
- 混合持久化：Redis + 本地 JSON (`data/aggregator_cache.json`)
- 优雅降级：Redis 不可用时仍可正常运行

## 后续建议

1. **测试完整功能**：运行完整的文件聚合流程，确保所有功能正常
2. **添加单元测试**：为 `FileScanner`, `AggregatorCache`, `LLMAggregator` 添加测试
3. **文档完善**：确保 README.md 和 CLAUDE.md 包含正确的使用说明
