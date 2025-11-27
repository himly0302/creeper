"""
测试文件扫描器和模板管理器
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.file_aggregator import FileScanner
from src.prompt_templates import PromptTemplateManager


class TestFileScanner:
    """测试文件扫描器"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path)

    @pytest.fixture
    def sample_files(self, temp_dir):
        """创建示例文件"""
        # 创建 Python 文件
        (temp_dir / "test1.py").write_text("print('hello')")
        (temp_dir / "test2.py").write_text("def foo(): pass")

        # 创建 Markdown 文件
        (temp_dir / "README.md").write_text("# Title\nContent")

        # 创建子目录
        sub_dir = temp_dir / "subdir"
        sub_dir.mkdir()
        (sub_dir / "test3.py").write_text("class Bar: pass")

        # 创建应忽略的文件
        (temp_dir / ".gitignore").write_text("*.pyc")

        return temp_dir

    def test_scan_directory(self, sample_files):
        """测试扫描目录"""
        scanner = FileScanner()
        files = scanner.scan_directory(str(sample_files))

        # 应该找到 4 个文件 (3 个 .py + 1 个 .md)
        assert len(files) >= 4

        # 检查文件路径
        file_paths = {f.path for f in files}
        assert any("test1.py" in p for p in file_paths)
        assert any("README.md" in p for p in file_paths)

    def test_filter_by_extension(self, sample_files):
        """测试按扩展名过滤"""
        scanner = FileScanner()
        files = scanner.scan_directory(str(sample_files), extensions=['.py'])

        # 应该只找到 Python 文件
        assert all(f.extension == '.py' for f in files)
        assert len(files) == 3

    def test_file_hash_computation(self, temp_dir):
        """测试文件哈希计算"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        hash1 = FileScanner.compute_file_hash(test_file)
        hash2 = FileScanner.compute_file_hash(test_file)

        # 相同文件应该产生相同哈希
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 哈希长度

    def test_nonexistent_directory(self):
        """测试不存在的目录"""
        scanner = FileScanner()
        with pytest.raises(FileNotFoundError):
            scanner.scan_directory("/nonexistent/path")


class TestPromptTemplateManager:
    """测试提示词模板管理器"""

    @pytest.fixture
    def temp_templates_dir(self):
        """创建临时模板目录"""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path)

    @pytest.fixture
    def sample_templates(self, temp_templates_dir):
        """创建示例模板"""
        (temp_templates_dir / "template1.txt").write_text("Template 1 content")
        (temp_templates_dir / "template2.txt").write_text("Template 2 content")
        return temp_templates_dir

    def test_list_templates(self, sample_templates):
        """测试列出模板"""
        manager = PromptTemplateManager(str(sample_templates))
        templates = manager.list_templates()

        assert len(templates) == 2
        assert "template1" in templates
        assert "template2" in templates

    def test_get_template(self, sample_templates):
        """测试获取模板"""
        manager = PromptTemplateManager(str(sample_templates))
        content = manager.get_template("template1")

        assert content == "Template 1 content"

    def test_template_not_found(self, sample_templates):
        """测试模板不存在"""
        manager = PromptTemplateManager(str(sample_templates))

        with pytest.raises(FileNotFoundError):
            manager.get_template("nonexistent")

    def test_template_caching(self, sample_templates):
        """测试模板缓存"""
        manager = PromptTemplateManager(str(sample_templates))

        # 第一次获取
        content1 = manager.get_template("template1")

        # 修改文件
        (sample_templates / "template1.txt").write_text("Modified content")

        # 第二次获取(应该返回缓存)
        content2 = manager.get_template("template1")
        assert content2 == content1  # 应该相同

        # 重新加载
        content3 = manager.reload_template("template1")
        assert content3 == "Modified content"
