"""Tests for git analyzer tool"""

import tempfile
import shutil
from pathlib import Path
import pytest
import git
from code_reviewer.tools.git_analyzer import GitAnalyzer


class TestGitAnalyzer:
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
        test_file = Path(temp_dir) / "test.py"
        test_file.write_text("def hello():\n    print('Hello')\n")

        repo.index.add(["test.py"])
        repo.index.commit("Initial commit")

        # Create a second commit
        test_file.write_text("def hello():\n    print('Hello World')\n")
        repo.index.add(["test.py"])
        repo.index.commit("Fix: Update hello message")

        # Create a third commit
        test_file.write_text(
            "def hello():\n    print('Hello World')\n\ndef goodbye():\n    print('Goodbye')\n"
        )
        repo.index.add(["test.py"])
        repo.index.commit("Add goodbye function")

        yield temp_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_get_file_history(self, temp_git_repo):
        """Test getting file history"""
        analyzer = GitAnalyzer(temp_git_repo)
        history = analyzer.get_file_history("test.py", max_commits=5)

        assert len(history) == 3
        assert history[0].author == "Test User"
        assert "goodbye" in history[0].message.lower()

    def test_get_current_branch(self, temp_git_repo):
        """Test getting current branch"""
        analyzer = GitAnalyzer(temp_git_repo)
        branch = analyzer.get_current_branch()

        # Default branch is usually 'master' or 'main'
        assert branch in ["master", "main"]

    def test_get_commit_diff(self, temp_git_repo):
        """Test getting commit diff"""
        analyzer = GitAnalyzer(temp_git_repo)
        history = analyzer.get_file_history("test.py")

        if history:
            diff = analyzer.get_commit_diff(history[0].hash, "test.py")
            assert len(diff) > 0

    def test_find_related_commits(self, temp_git_repo):
        """Test finding commits related to a term"""
        analyzer = GitAnalyzer(temp_git_repo)
        related = analyzer.find_related_commits("hello", max_commits=10)

        assert len(related) > 0
        assert any("hello" in commit.diff.lower() for commit in related if commit.diff)

    def test_get_recent_review_comments(self, temp_git_repo):
        """Test extracting review comments from commits"""
        analyzer = GitAnalyzer(temp_git_repo)
        comments = analyzer.get_recent_review_comments("test.py")

        # Should find the "Fix:" commit
        assert len(comments) > 0
        assert any("fix" in comment.lower() for comment in comments)

    def test_was_recently_modified(self, temp_git_repo):
        """Test checking if file was recently modified"""
        analyzer = GitAnalyzer(temp_git_repo)
        # File was just modified, so should be recent
        recent = analyzer.was_recently_modified("test.py", days=1)

        assert recent is True

    def test_invalid_repo(self):
        """Test with invalid repository"""
        temp_dir = tempfile.mkdtemp()

        try:
            with pytest.raises(ValueError):
                GitAnalyzer(temp_dir)
        finally:
            shutil.rmtree(temp_dir)

    def test_get_blame(self, temp_git_repo):
        """Test getting blame information"""
        analyzer = GitAnalyzer(temp_git_repo)
        blame = analyzer.get_blame("test.py")

        assert len(blame) > 0
        assert "Test User" in blame
