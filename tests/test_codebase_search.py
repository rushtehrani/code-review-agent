"""Tests for codebase search tool"""

import tempfile
import shutil
from pathlib import Path
import pytest
from code_reviewer.tools.codebase_search import CodebaseSearch


class TestCodebaseSearch:
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing"""
        temp_dir = tempfile.mkdtemp()

        # Create some test files
        test_files = {
            "main.py": """
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total

def process_order(order):
    print(f"Processing {order}")
    total = calculate_total(order.items)
    return total
""",
            "utils.py": """
def helper_function(x):
    return x * 2

def calculate_tax(amount):
    # TODO: implement tax calculation
    return amount * 0.1
""",
            "tests/test_main.py": """
import pytest
from main import calculate_total

def test_calculate_total():
    assert calculate_total([]) == 0
""",
        }

        for file_path, content in test_files.items():
            full_path = Path(temp_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)

        yield temp_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_search_pattern(self, temp_repo):
        """Test searching for a pattern"""
        search = CodebaseSearch(temp_repo)
        results = search.search("calculate_total")

        assert len(results) > 0
        assert any("main.py" in r.file for r in results)

    def test_search_with_file_pattern(self, temp_repo):
        """Test searching with file pattern filter"""
        search = CodebaseSearch(temp_repo)
        results = search.search("def", file_pattern="*.py")

        assert len(results) > 0
        assert all(r.file.endswith(".py") for r in results)

    def test_search_case_insensitive(self, temp_repo):
        """Test case-insensitive search"""
        search = CodebaseSearch(temp_repo)
        results = search.search("CALCULATE", case_sensitive=False)

        assert len(results) > 0

    def test_search_case_sensitive(self, temp_repo):
        """Test case-sensitive search"""
        search = CodebaseSearch(temp_repo)
        results = search.search("CALCULATE", case_sensitive=True)

        # Should not find lowercase 'calculate'
        assert len(results) == 0

    def test_find_files(self, temp_repo):
        """Test finding files by pattern"""
        search = CodebaseSearch(temp_repo)
        files = search.find_files("*.py")

        assert len(files) >= 2
        assert any("main.py" in f for f in files)
        assert any("utils.py" in f for f in files)

    def test_read_file(self, temp_repo):
        """Test reading a file"""
        search = CodebaseSearch(temp_repo)
        content = search.read_file("main.py")

        assert "calculate_total" in content
        assert "process_order" in content

    def test_read_file_with_line_range(self, temp_repo):
        """Test reading specific lines of a file"""
        search = CodebaseSearch(temp_repo)
        content = search.read_file("main.py", start_line=2, end_line=4)

        assert "def calculate_total" in content
        # Should have 3 lines (may have trailing newline)
        lines = [l for l in content.split("\n") if l.strip()]
        assert len(lines) == 3

    def test_find_function_calls(self, temp_repo):
        """Test finding function calls"""
        search = CodebaseSearch(temp_repo)
        results = search.find_function_calls("calculate_total")

        assert len(results) > 0
        # Should find both the definition and the call
        matches_found = sum(len(r.matches) for r in results)
        assert matches_found >= 1

    def test_search_no_results(self, temp_repo):
        """Test search with no results"""
        search = CodebaseSearch(temp_repo)
        results = search.search("nonexistent_pattern_xyz")

        assert len(results) == 0

    def test_read_nonexistent_file(self, temp_repo):
        """Test reading a file that doesn't exist"""
        search = CodebaseSearch(temp_repo)
        content = search.read_file("nonexistent.py")

        assert content == ""
