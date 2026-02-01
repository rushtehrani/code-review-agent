"""Tests for the code review agent with mocking"""

import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import pytest
import git
from code_reviewer.agent import CodeReviewAgent
from code_reviewer.models import ReviewFinding, Severity


class TestCodeReviewAgent:
    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary git repository for testing"""
        temp_dir = tempfile.mkdtemp()
        repo = git.Repo.init(temp_dir)

        # Configure git
        with repo.config_writer() as config:
            config.set_value("user", "name", "Test User")
            config.set_value("user", "email", "test@example.com")

        # Create initial commit
        test_file = Path(temp_dir) / "main.py"
        test_file.write_text("""
def calculate(x):
    return x * 2
""")

        repo.index.add(["main.py"])
        repo.index.commit("Initial commit")

        # Create a second commit with a bug
        test_file.write_text("""
def calculate(x):
    password = "secret123"  # Security issue
    return x * 2

def process():
    try:
        risky()
    except:  # Bare except
        print("Error")
""")
        repo.index.add(["main.py"])
        repo.index.commit("Add password and bare except")

        yield temp_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_agent_initialization(self, temp_git_repo):
        """Test agent initialization"""
        agent = CodeReviewAgent(
            repo_path=temp_git_repo,
            api_key="test-key",
        )

        assert agent.repo_path == temp_git_repo
        assert agent.search is not None
        assert agent.git is not None
        assert agent.rule_learner is not None

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_agent_get_tool_definitions(self, temp_git_repo):
        """Test that agent defines tools correctly"""
        agent = CodeReviewAgent(
            repo_path=temp_git_repo,
            api_key="test-key",
        )

        tools = agent._get_tool_definitions()

        assert len(tools) == 5
        assert any(t["name"] == "search_codebase" for t in tools)
        assert any(t["name"] == "read_file" for t in tools)
        assert any(t["name"] == "get_file_history" for t in tools)
        assert any(t["name"] == "find_function_calls" for t in tools)
        assert any(t["name"] == "get_blame" for t in tools)

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_agent_execute_tool_search(self, temp_git_repo):
        """Test executing search_codebase tool"""
        agent = CodeReviewAgent(
            repo_path=temp_git_repo,
            api_key="test-key",
        )

        result = agent._execute_tool(
            "search_codebase",
            {"pattern": "def calculate"}
        )

        assert isinstance(result, str)
        assert len(result) > 0

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_agent_execute_tool_read_file(self, temp_git_repo):
        """Test executing read_file tool"""
        agent = CodeReviewAgent(
            repo_path=temp_git_repo,
            api_key="test-key",
        )

        result = agent._execute_tool(
            "read_file",
            {"file_path": "main.py"}
        )

        assert isinstance(result, str)
        assert "def calculate" in result

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_agent_execute_tool_file_history(self, temp_git_repo):
        """Test executing get_file_history tool"""
        agent = CodeReviewAgent(
            repo_path=temp_git_repo,
            api_key="test-key",
        )

        result = agent._execute_tool(
            "get_file_history",
            {"file_path": "main.py", "max_commits": 5}
        )

        assert isinstance(result, str)

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_agent_execute_tool_find_calls(self, temp_git_repo):
        """Test executing find_function_calls tool"""
        agent = CodeReviewAgent(
            repo_path=temp_git_repo,
            api_key="test-key",
        )

        result = agent._execute_tool(
            "find_function_calls",
            {"function_name": "calculate", "language": "python"}
        )

        assert isinstance(result, str)

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_agent_execute_tool_blame(self, temp_git_repo):
        """Test executing get_blame tool"""
        agent = CodeReviewAgent(
            repo_path=temp_git_repo,
            api_key="test-key",
        )

        result = agent._execute_tool(
            "get_blame",
            {"file_path": "main.py"}
        )

        assert isinstance(result, str)

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_agent_execute_unknown_tool(self, temp_git_repo):
        """Test executing unknown tool"""
        agent = CodeReviewAgent(
            repo_path=temp_git_repo,
            api_key="test-key",
        )

        result = agent._execute_tool(
            "unknown_tool",
            {}
        )

        assert "Unknown tool" in result

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_agent_parse_findings(self, temp_git_repo):
        """Test parsing findings from agent response"""
        agent = CodeReviewAgent(
            repo_path=temp_git_repo,
            api_key="test-key",
        )

        text = """
FILE: main.py
LINE: 10
SEVERITY: ERROR
MESSAGE: Hardcoded password detected
SUGGESTION: Use environment variables
---
FILE: utils.py
LINE: 20
SEVERITY: WARNING
MESSAGE: Function too long
---
"""

        findings = agent._parse_findings(text, ["main.py", "utils.py"])

        assert len(findings) == 2
        assert findings[0].file == "main.py"
        assert findings[0].line == 10
        assert findings[0].severity == Severity.ERROR
        assert "password" in findings[0].message.lower()

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_agent_create_finding(self, temp_git_repo):
        """Test creating a finding from parsed data"""
        agent = CodeReviewAgent(
            repo_path=temp_git_repo,
            api_key="test-key",
        )

        data = {
            "file": "test.py",
            "line": 42,
            "severity": "error",
            "message": "Test error",
            "suggestion": "Fix it",
        }

        finding = agent._create_finding(data)

        assert finding.file == "test.py"
        assert finding.line == 42
        assert finding.severity == Severity.ERROR
        assert finding.message == "Test error"
        assert finding.suggestion == "Fix it"

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_agent_create_finding_defaults(self, temp_git_repo):
        """Test creating finding with default values"""
        agent = CodeReviewAgent(
            repo_path=temp_git_repo,
            api_key="test-key",
        )

        data = {}

        finding = agent._create_finding(data)

        assert finding.file == "unknown"
        assert finding.line == 1
        assert finding.severity == Severity.INFO

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_agent_get_system_prompt(self, temp_git_repo):
        """Test system prompt generation"""
        agent = CodeReviewAgent(
            repo_path=temp_git_repo,
            api_key="test-key",
        )

        prompt = agent._get_system_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "code reviewer" in prompt.lower()

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_agent_create_review_prompt(self, temp_git_repo):
        """Test review prompt creation"""
        agent = CodeReviewAgent(
            repo_path=temp_git_repo,
            api_key="test-key",
        )

        diff = "+def new_function():\n+    pass"
        files = ["main.py"]

        prompt = agent._create_review_prompt(diff, files)

        assert isinstance(prompt, str)
        assert "main.py" in prompt
        assert "new_function" in prompt

    def test_agent_requires_api_key(self, temp_git_repo):
        """Test that agent requires API key"""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            CodeReviewAgent(repo_path=temp_git_repo)

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_agent_tool_error_handling(self, temp_git_repo):
        """Test that tool execution handles errors gracefully"""
        agent = CodeReviewAgent(
            repo_path=temp_git_repo,
            api_key="test-key",
        )

        # Try to read a file that doesn't exist
        result = agent._execute_tool(
            "read_file",
            {"file_path": "nonexistent_file.py"}
        )

        # Should return empty or error message, not crash
        assert isinstance(result, str)
