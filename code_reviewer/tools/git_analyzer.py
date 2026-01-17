"""
Git history analyzer - analyzes git history to provide context

Inspired by Greptile's ability to check git history to discover when
helper functions were created, trace commits, etc.
"""

from pathlib import Path
from typing import Optional
import git
from code_reviewer.models import GitCommit


class GitAnalyzer:
    """Tool for analyzing git history and providing code context"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        try:
            self.repo = git.Repo(repo_path)
        except git.InvalidGitRepositoryError:
            raise ValueError(f"Not a valid git repository: {repo_path}")

    def get_file_history(
        self, file_path: str, max_commits: int = 10
    ) -> list[GitCommit]:
        """
        Get git history for a specific file

        Args:
            file_path: Path to the file relative to repo root
            max_commits: Maximum number of commits to retrieve

        Returns:
            List of commits that modified the file
        """
        try:
            commits = list(self.repo.iter_commits(paths=file_path, max_count=max_commits))

            return [
                GitCommit(
                    hash=commit.hexsha,
                    author=commit.author.name,
                    date=commit.committed_datetime.isoformat(),
                    message=commit.message.strip(),
                )
                for commit in commits
            ]
        except Exception:
            return []

    def get_commit_diff(self, commit_hash: str, file_path: Optional[str] = None) -> str:
        """
        Get diff for a specific commit

        Args:
            commit_hash: The commit hash
            file_path: Optional file path to get diff for specific file

        Returns:
            Diff as a string
        """
        try:
            commit = self.repo.commit(commit_hash)

            if commit.parents:
                parent = commit.parents[0]
                if file_path:
                    diff = parent.diff(commit, paths=file_path, create_patch=True)
                else:
                    diff = parent.diff(commit, create_patch=True)

                return "\n".join([d.diff.decode("utf-8", errors="ignore") for d in diff])
            else:
                # First commit, show all changes
                return commit.diff(None, create_patch=True)[0].diff.decode(
                    "utf-8", errors="ignore"
                )
        except Exception:
            return ""

    def get_blame(
        self, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None
    ) -> str:
        """
        Get blame information for a file

        Args:
            file_path: Path to the file
            start_line: Optional start line (1-indexed)
            end_line: Optional end line (1-indexed)

        Returns:
            Blame information as a string
        """
        try:
            full_path = self.repo_path / file_path

            if not full_path.exists():
                return ""

            blame = self.repo.git.blame(file_path)

            if start_line is not None and end_line is not None:
                lines = blame.split("\n")
                return "\n".join(lines[start_line - 1 : end_line])

            return blame
        except Exception:
            return ""

    def find_related_commits(
        self, search_term: str, max_commits: int = 20
    ) -> list[GitCommit]:
        """
        Find commits related to a specific term (e.g., function name)

        Args:
            search_term: Term to search for in commit diffs
            max_commits: Maximum number of commits to check

        Returns:
            List of related commits with their diffs
        """
        try:
            commits = list(self.repo.iter_commits(max_count=max_commits))
            related = []

            for commit in commits:
                diff = self.get_commit_diff(commit.hexsha)

                if search_term in diff:
                    related.append(
                        GitCommit(
                            hash=commit.hexsha,
                            author=commit.author.name,
                            date=commit.committed_datetime.isoformat(),
                            message=commit.message.strip(),
                            diff=diff,
                        )
                    )

            return related
        except Exception:
            return []

    def get_current_branch(self) -> str:
        """Get the name of the current branch"""
        try:
            return self.repo.active_branch.name
        except Exception:
            return "unknown"

    def get_changed_files(self, base_branch: str = "main") -> list[str]:
        """
        Get files changed in current branch compared to base

        Args:
            base_branch: The base branch to compare against

        Returns:
            List of changed file paths
        """
        try:
            # Try to get the base branch
            try:
                base = self.repo.commit(base_branch)
            except git.BadName:
                # If base_branch doesn't exist, try 'master'
                try:
                    base = self.repo.commit("master")
                except git.BadName:
                    # If neither exists, compare to HEAD
                    base = self.repo.head.commit

            current = self.repo.head.commit
            diffs = base.diff(current)

            return [diff.a_path or diff.b_path for diff in diffs]
        except Exception:
            return []

    def get_diff(self, base_branch: str = "main", files: Optional[list[str]] = None) -> str:
        """
        Get diff compared to base branch

        Args:
            base_branch: The base branch to compare against
            files: Optional list of specific files to get diff for

        Returns:
            Diff as a string
        """
        try:
            # Try to get the base branch
            try:
                base = self.repo.commit(base_branch)
            except git.BadName:
                try:
                    base = self.repo.commit("master")
                except git.BadName:
                    base = self.repo.head.commit.parents[0] if self.repo.head.commit.parents else None

            if base is None:
                return ""

            current = self.repo.head.commit

            if files:
                diffs = base.diff(current, paths=files, create_patch=True)
            else:
                diffs = base.diff(current, create_patch=True)

            return "\n".join([d.diff.decode("utf-8", errors="ignore") for d in diffs])
        except Exception:
            return ""

    def get_recent_review_comments(self, file_path: str, max_commits: int = 50) -> list[str]:
        """
        Extract review-like comments from commit messages for a file

        This simulates Greptile's ability to learn from other engineers' comments.

        Args:
            file_path: Path to the file
            max_commits: Maximum commits to check

        Returns:
            List of review-related comments
        """
        try:
            commits = list(self.repo.iter_commits(paths=file_path, max_count=max_commits))
            review_comments = []

            # Keywords that indicate review/fix comments
            review_keywords = [
                "fix",
                "bug",
                "issue",
                "review",
                "refactor",
                "improve",
                "optimize",
                "cleanup",
                "address",
            ]

            for commit in commits:
                message = commit.message.strip().lower()

                # Check if commit message contains review keywords
                if any(keyword in message for keyword in review_keywords):
                    review_comments.append(commit.message.strip())

            return review_comments
        except Exception:
            return []

    def was_recently_modified(self, file_path: str, days: int = 7) -> bool:
        """
        Check if a file was recently modified

        Args:
            file_path: Path to the file
            days: Number of days to consider as "recent"

        Returns:
            True if file was modified in the last N days
        """
        try:
            from datetime import datetime, timedelta

            commits = list(self.repo.iter_commits(paths=file_path, max_count=1))

            if not commits:
                return False

            last_commit_date = commits[0].committed_datetime.replace(tzinfo=None)
            cutoff_date = datetime.now() - timedelta(days=days)

            return last_commit_date > cutoff_date
        except Exception:
            return False
