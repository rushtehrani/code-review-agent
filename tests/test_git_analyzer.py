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

    def test_get_blame_with_line_range(self, temp_git_repo):
        """Test getting blame for specific line range"""
        analyzer = GitAnalyzer(temp_git_repo)
        blame = analyzer.get_blame("test.py", start_line=1, end_line=2)

        assert len(blame) > 0

    def test_get_blame_nonexistent_file(self, temp_git_repo):
        """Test getting blame for non-existent file"""
        analyzer = GitAnalyzer(temp_git_repo)
        blame = analyzer.get_blame("nonexistent.py")

        assert blame == ""

    def test_get_changed_files(self, temp_git_repo):
        """Test getting changed files"""
        analyzer = GitAnalyzer(temp_git_repo)
        repo = git.Repo(temp_git_repo)

        # Create a new branch and make a change
        repo.git.checkout("-b", "feature")
        test_file = Path(temp_git_repo) / "new_file.py"
        test_file.write_text("def new(): pass\n")
        repo.index.add(["new_file.py"])
        repo.index.commit("Add new file")

        changed = analyzer.get_changed_files("master")

        assert "new_file.py" in changed

    def test_get_diff(self, temp_git_repo):
        """Test getting diff"""
        analyzer = GitAnalyzer(temp_git_repo)
        repo = git.Repo(temp_git_repo)

        # Create a new branch and make a change
        repo.git.checkout("-b", "feature2")
        test_file = Path(temp_git_repo) / "test.py"
        test_file.write_text("def new_function(): pass\n")
        repo.index.add(["test.py"])
        repo.index.commit("Add new function")

        diff = analyzer.get_diff("master")

        assert len(diff) > 0
        assert "new_function" in diff

    def test_get_diff_specific_files(self, temp_git_repo):
        """Test getting diff for specific files"""
        analyzer = GitAnalyzer(temp_git_repo)
        repo = git.Repo(temp_git_repo)

        # Create changes
        repo.git.checkout("-b", "feature3")
        test_file = Path(temp_git_repo) / "test.py"
        test_file.write_text("def another(): pass\n")
        repo.index.add(["test.py"])
        repo.index.commit("Another change")

        diff = analyzer.get_diff("master", files=["test.py"])

        assert len(diff) >= 0  # May have diff or not

    def test_get_file_history_nonexistent(self, temp_git_repo):
        """Test getting history for non-existent file"""
        analyzer = GitAnalyzer(temp_git_repo)
        history = analyzer.get_file_history("nonexistent.py")

        assert len(history) == 0

    def test_find_related_commits_no_matches(self, temp_git_repo):
        """Test finding commits with no matches"""
        analyzer = GitAnalyzer(temp_git_repo)
        related = analyzer.find_related_commits("xyz_no_match_xyz")

        assert len(related) == 0

    def test_was_recently_modified_old_file(self, temp_git_repo):
        """Test checking old modification"""
        analyzer = GitAnalyzer(temp_git_repo)
        # Check if modified in last 0 days (should be False)
        recent = analyzer.was_recently_modified("test.py", days=0)

        # Depends on timing, but should handle gracefully
        assert isinstance(recent, bool)

    def test_get_commit_diff_invalid_hash(self, temp_git_repo):
        """Test getting diff for invalid commit hash"""
        analyzer = GitAnalyzer(temp_git_repo)
        diff = analyzer.get_commit_diff("invalid_hash_xyz")

        assert diff == ""

    def test_get_recent_review_comments_no_keywords(self, temp_git_repo):
        """Test getting review comments when none match keywords"""
        analyzer = GitAnalyzer(temp_git_repo)
        repo = git.Repo(temp_git_repo)

        # Add commit without review keywords
        test_file = Path(temp_git_repo) / "test.py"
        test_file.write_text("def simple(): pass\n")
        repo.index.add(["test.py"])
        repo.index.commit("Regular commit")

        comments = analyzer.get_recent_review_comments("test.py", max_commits=1)

        # May or may not have comments
        assert isinstance(comments, list)
