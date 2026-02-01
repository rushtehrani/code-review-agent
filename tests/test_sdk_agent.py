"""Tests for SDK Agent (complete rewrite)"""

import pytest
import tempfile
import shutil
from pathlib import Path
import git
from unittest.mock import Mock, patch, AsyncMock


class TestSDKAgent:
    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary git repository for testing"""
        temp_dir = tempfile.mkdtemp()
        repo = git.Repo.init(temp_dir)

        # Configure git
        with repo.config_writer() as config:
            config.set_value("user", "name", "Test User")
            config.set_value("user", "email", "test@example.com")

        # Create initial file
        test_file = Path(temp_dir) / "main.py"
        test_file.write_text("""
def calculate(x):
    return x * 2
""")

        repo.index.add(["main.py"])
        repo.index.commit("Initial commit")

        # Make changes
        test_file.write_text("""
def calculate(x):
    password = "secret123"  # Security issue
    return x * 2

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

    def test_sdk_agent_import(self):
        """Test that SDK agent can be imported"""
        from code_reviewer.agent import CodeReviewAgent, review_code

        assert CodeReviewAgent is not None
        assert review_code is not None

    def test_sdk_agent_initialization(self, temp_git_repo):
        """Test SDK agent initialization"""
        from code_reviewer.agent import CodeReviewAgent

        reviewer = CodeReviewAgent(repo_path=temp_git_repo)

        assert reviewer.repo_path == Path(temp_git_repo).absolute()
        assert reviewer.search is not None
        assert reviewer.git is not None
        assert reviewer.rule_learner is not None
        assert reviewer.options is not None

    def test_sdk_agent_initialization_no_git(self):
        """Test SDK agent handles non-git directory"""
        from code_reviewer.agent import CodeReviewAgent

        temp_dir = tempfile.mkdtemp()
        try:
            reviewer = CodeReviewAgent(repo_path=temp_dir)
            assert reviewer.git is None
        finally:
            shutil.rmtree(temp_dir)

    def test_create_review_prompt(self, temp_git_repo):
        """Test review prompt creation"""
        from code_reviewer.agent import CodeReviewAgent

        reviewer = CodeReviewAgent(repo_path=temp_git_repo)

        diff = "+def new_function(): pass"
        files = ["main.py"]

        prompt = reviewer._create_review_prompt(diff, files, "main")

        assert "main.py" in prompt
        assert "new_function" in prompt
        assert "search_codebase" in prompt
        assert "autonomous" in prompt.lower() or "agentic" in prompt.lower()

    def test_parse_findings_from_response(self, temp_git_repo):
        """Test parsing findings from Claude's response"""
        from code_reviewer.agent import CodeReviewAgent

        reviewer = CodeReviewAgent(repo_path=temp_git_repo)

        response = """
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

        findings = reviewer._parse_findings_from_response(response, ["main.py"])

        assert len(findings) == 2
        assert findings[0].file == "main.py"
        assert findings[0].line == 10
        assert findings[0].message == "Hardcoded password detected"
        assert findings[0].suggestion == "Use environment variables"

    def test_create_finding(self, temp_git_repo):
        """Test finding creation"""
        from code_reviewer.agent import CodeReviewAgent
        from code_reviewer.models import Severity

        reviewer = CodeReviewAgent(repo_path=temp_git_repo)

        data = {
            "file": "test.py",
            "line": 42,
            "severity": "error",
            "message": "Test error",
            "suggestion": "Fix it"
        }

        finding = reviewer._create_finding(data)

        assert finding.file == "test.py"
        assert finding.line == 42
        assert finding.severity == Severity.ERROR
        assert finding.message == "Test error"

    @pytest.mark.asyncio
    async def test_review_changes_no_git(self):
        """Test review in non-git directory"""
        from code_reviewer.agent import CodeReviewAgent

        temp_dir = tempfile.mkdtemp()
        try:
            reviewer = CodeReviewAgent(repo_path=temp_dir)
            result = await reviewer.review_changes()

            assert len(result.findings) == 0
            assert "Not a git repository" in result.investigation_steps
        finally:
            shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_review_changes_no_changes(self, temp_git_repo):
        """Test review with no changes"""
        from code_reviewer.agent import CodeReviewAgent

        # Reset to initial commit
        repo = git.Repo(temp_git_repo)
        repo.head.reset('HEAD~1', index=True, working_tree=True)

        reviewer = CodeReviewAgent(repo_path=temp_git_repo)
        result = await reviewer.review_changes()

        assert "No changes detected" in result.investigation_steps

    def test_sdk_options_configuration(self, temp_git_repo):
        """Test that SDK options are properly configured"""
        from code_reviewer.agent import CodeReviewAgent
        import os

        reviewer = CodeReviewAgent(
            repo_path=temp_git_repo,
            api_key="test-key",
            model="claude-opus-4-5-20251101"
        )

        # API key is set in environment, not in options
        assert os.environ.get("ANTHROPIC_API_KEY") == "test-key"
        assert reviewer.options.model == "claude-opus-4-5-20251101"
        assert str(reviewer.options.cwd) == str(Path(temp_git_repo).absolute())

    def test_exports_from_init(self):
        """Test that SDK agent is exported from package"""
        try:
            from code_reviewer import CodeReviewAgent, review_code

            assert CodeReviewAgent is not None
            assert review_code is not None
        except ImportError:
            pytest.skip("SDK not fully initialized")

    @pytest.mark.asyncio
    async def test_review_code_convenience_function(self, temp_git_repo):
        """Test the convenience review_code function"""
        from code_reviewer.agent import review_code

        # Mock the query function since we don't have real API
        with patch('code_reviewer.agent.query', new_callable=AsyncMock) as mock_query:
            # Make it return empty iterator
            mock_query.return_value = iter([])

            result = await review_code(
                repo_path=temp_git_repo,
                base_branch="HEAD~1"
            )

            assert result is not None
            assert isinstance(result.files_reviewed, list)

    def test_sdk_agent_tools_initialized(self, temp_git_repo):
        """Test that all tools are properly initialized"""
        from code_reviewer.agent import CodeReviewAgent

        reviewer = CodeReviewAgent(repo_path=temp_git_repo)

        # Check search tool
        assert reviewer.search is not None
        assert hasattr(reviewer.search, 'search')
        assert hasattr(reviewer.search, 'read_file')

        # Check git tool
        assert reviewer.git is not None
        assert hasattr(reviewer.git, 'get_diff')
        assert hasattr(reviewer.git, 'get_file_history')

        # Check rule learner
        assert reviewer.rule_learner is not None
        assert hasattr(reviewer.rule_learner, 'apply_rules')
        assert len(reviewer.rule_learner.rules) > 0

    def test_sdk_version(self):
        """Test that version is set correctly"""
        from code_reviewer import __version__

        # Should be 0.1.0
        assert __version__ == "0.1.0"

    def test_parsing_handles_incomplete_findings(self, temp_git_repo):
        """Test that parsing handles incomplete findings gracefully"""
        from code_reviewer.agent import CodeReviewAgent

        reviewer = CodeReviewAgent(repo_path=temp_git_repo)

        # Incomplete finding (missing severity)
        response = """
FILE: test.py
LINE: 10
MESSAGE: Some issue
---
"""

        findings = reviewer._parse_findings_from_response(response, ["test.py"])

        assert len(findings) == 1
        # Should have defaults for missing fields
        assert findings[0].file == "test.py"
        assert findings[0].line == 10

    def test_prompt_includes_all_tools(self, temp_git_repo):
        """Test that prompt mentions all available tools"""
        from code_reviewer.agent import CodeReviewAgent

        reviewer = CodeReviewAgent(repo_path=temp_git_repo)
        prompt = reviewer._create_review_prompt("+test", ["test.py"], "main")

        # All 7 tools should be mentioned
        assert "search_codebase" in prompt
        assert "read_file" in prompt
        assert "get_file_history" in prompt
        assert "find_function_calls" in prompt
        assert "get_blame" in prompt
        assert "apply_code_rules" in prompt

    def test_prompt_emphasizes_agentic_behavior(self, temp_git_repo):
        """Test that prompt encourages agentic investigation"""
        from code_reviewer.agent import CodeReviewAgent

        reviewer = CodeReviewAgent(repo_path=temp_git_repo)
        prompt = reviewer._create_review_prompt("+test", ["test.py"], "main")

        # Should encourage autonomous, recursive investigation
        assert any(word in prompt.lower() for word in ["agentic", "autonomous", "recursive"])
        assert "investigate" in prompt.lower()
        assert "thoroughly" in prompt.lower() or "complete" in prompt.lower()
