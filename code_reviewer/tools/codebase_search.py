"""
Codebase search tool - searches for patterns across the entire codebase

Inspired by Greptile's approach to recursively search the codebase
and follow nested function calls.
"""

import subprocess
import re
from pathlib import Path
from typing import Optional
from code_reviewer.models import CodebaseSearchResult, SearchMatch


class CodebaseSearch:
    """Tool for searching code patterns in a repository"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)

    def search(
        self,
        pattern: str,
        file_pattern: str = "*",
        case_sensitive: bool = False,
        context_lines: int = 3,
    ) -> list[CodebaseSearchResult]:
        """
        Search for a pattern in the codebase using ripgrep or grep

        Args:
            pattern: The regex pattern to search for
            file_pattern: File glob pattern to filter (e.g., "*.py")
            case_sensitive: Whether search should be case sensitive
            context_lines: Number of context lines to include

        Returns:
            List of search results with matches
        """
        try:
            # Try ripgrep first (faster)
            return self._search_with_ripgrep(pattern, file_pattern, case_sensitive, context_lines)
        except (FileNotFoundError, subprocess.CalledProcessError):
            # Fallback to grep
            return self._search_with_grep(pattern, case_sensitive, context_lines)

    def _search_with_ripgrep(
        self, pattern: str, file_pattern: str, case_sensitive: bool, context_lines: int
    ) -> list[CodebaseSearchResult]:
        """Search using ripgrep (rg)"""
        cmd = ["rg", "--json", "--context", str(context_lines)]

        if not case_sensitive:
            cmd.append("-i")

        if file_pattern != "*":
            cmd.extend(["-g", file_pattern])

        cmd.extend([pattern, str(self.repo_path)])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=30
            )

            if result.returncode not in (0, 1):  # 1 means no matches found
                raise subprocess.CalledProcessError(result.returncode, cmd)

            return self._parse_ripgrep_json(result.stdout)
        except subprocess.TimeoutExpired:
            return []

    def _parse_ripgrep_json(self, output: str) -> list[CodebaseSearchResult]:
        """Parse ripgrep JSON output"""
        import json

        results_map: dict[str, CodebaseSearchResult] = {}

        for line in output.strip().split("\n"):
            if not line:
                continue

            try:
                data = json.loads(line)

                if data.get("type") == "match":
                    match_data = data["data"]
                    file_path = match_data["path"]["text"]
                    line_num = match_data["line_number"]
                    content = match_data["lines"]["text"].rstrip()

                    if file_path not in results_map:
                        results_map[file_path] = CodebaseSearchResult(
                            file=file_path, matches=[]
                        )

                    results_map[file_path].matches.append(
                        SearchMatch(line=line_num, content=content)
                    )
            except (json.JSONDecodeError, KeyError):
                continue

        return list(results_map.values())

    def _search_with_grep(
        self, pattern: str, case_sensitive: bool, context_lines: int
    ) -> list[CodebaseSearchResult]:
        """Fallback search using grep"""
        cmd = ["grep", "-r", "-n"]

        if not case_sensitive:
            cmd.append("-i")

        if context_lines > 0:
            cmd.extend(["-C", str(context_lines)])

        cmd.extend([pattern, str(self.repo_path)])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=30
            )

            return self._parse_grep_output(result.stdout)
        except subprocess.TimeoutExpired:
            return []

    def _parse_grep_output(self, output: str) -> list[CodebaseSearchResult]:
        """Parse grep output"""
        results_map: dict[str, CodebaseSearchResult] = {}

        for line in output.strip().split("\n"):
            if not line:
                continue

            # Format: file:line:content
            match = re.match(r"^([^:]+):(\d+):(.+)$", line)
            if match:
                file_path, line_num, content = match.groups()

                if file_path not in results_map:
                    results_map[file_path] = CodebaseSearchResult(
                        file=file_path, matches=[]
                    )

                results_map[file_path].matches.append(
                    SearchMatch(line=int(line_num), content=content.strip())
                )

        return list(results_map.values())

    def find_files(self, pattern: str) -> list[str]:
        """
        Find files matching a glob pattern

        Args:
            pattern: Glob pattern (e.g., "*.py", "**/*.js")

        Returns:
            List of file paths
        """
        try:
            matches = list(self.repo_path.glob(f"**/{pattern}"))
            return [str(m.relative_to(self.repo_path)) for m in matches if m.is_file()]
        except Exception:
            return []

    def read_file(
        self, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None
    ) -> str:
        """
        Read contents of a file

        Args:
            file_path: Path to the file relative to repo root
            start_line: Optional start line (1-indexed)
            end_line: Optional end line (1-indexed)

        Returns:
            File contents or empty string if file doesn't exist
        """
        try:
            full_path = self.repo_path / file_path
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                if start_line is not None and end_line is not None:
                    lines = f.readlines()
                    return "".join(lines[start_line - 1 : end_line])
                return f.read()
        except Exception:
            return ""

    def find_function_calls(self, function_name: str, language: str = "python") -> list[CodebaseSearchResult]:
        """
        Find all calls to a specific function

        Args:
            function_name: Name of the function
            language: Programming language (affects search pattern)

        Returns:
            List of search results
        """
        # Create language-specific patterns
        patterns = {
            "python": rf"{function_name}\s*\(",
            "javascript": rf"{function_name}\s*\(",
            "typescript": rf"{function_name}\s*\(",
            "java": rf"{function_name}\s*\(",
            "go": rf"{function_name}\s*\(",
        }

        pattern = patterns.get(language, rf"{function_name}\s*\(")
        return self.search(pattern, case_sensitive=True)

    def find_similar_patterns(self, code_snippet: str, threshold: int = 80) -> list[CodebaseSearchResult]:
        """
        Find code similar to a given snippet

        This is a simplified version - in production, you'd use more
        sophisticated fuzzy matching or embeddings.

        Args:
            code_snippet: The code to find similar patterns for
            threshold: Similarity threshold (0-100)

        Returns:
            List of search results
        """
        # Extract key identifiers from the snippet
        identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code_snippet)

        if not identifiers:
            return []

        # Search for files containing the same identifiers
        results = []
        for identifier in set(identifiers):
            matches = self.search(identifier, case_sensitive=False)
            results.extend(matches)

        # Remove duplicates
        seen = set()
        unique_results = []
        for result in results:
            if result.file not in seen:
                seen.add(result.file)
                unique_results.append(result)

        return unique_results
