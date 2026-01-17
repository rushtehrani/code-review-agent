"""
Agentic Code Reviewer - Main agent implementation

Inspired by Greptile v3's agentic approach where the system runs in a loop
with access to tools like codebase search and learned rules.
"""

import os
from typing import Optional
from anthropic import Anthropic
from code_reviewer.models import (
    CodeReviewResult,
    ReviewFinding,
    Severity,
)
from code_reviewer.tools.codebase_search import CodebaseSearch
from code_reviewer.tools.git_analyzer import GitAnalyzer
from code_reviewer.tools.rule_learner import RuleLearner


class CodeReviewAgent:
    """
    Agentic code reviewer powered by Claude

    This agent autonomously reviews code with full codebase context,
    following Greptile's v3 approach of recursive investigation.
    """

    def __init__(
        self,
        repo_path: str,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-5-20251101",
        rules_file: Optional[str] = None,
    ):
        """
        Initialize the code review agent

        Args:
            repo_path: Path to the git repository
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            model: Claude model to use (default: opus-4-5 for best code review)
            rules_file: Optional path to rules file for learning
        """
        self.repo_path = repo_path
        self.model = model

        # Initialize Anthropic client
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        self.client = Anthropic(api_key=api_key)

        # Initialize tools
        self.search = CodebaseSearch(repo_path)
        self.git = GitAnalyzer(repo_path)
        self.rule_learner = RuleLearner(rules_file)

        # Learn from existing commit history
        self._learn_from_repo()

    def _learn_from_repo(self) -> None:
        """Learn patterns from repository history"""
        try:
            # Get recent commits with review-related keywords
            all_commits = []
            for file in self.search.find_files("*.py")[:10]:  # Sample first 10 Python files
                comments = self.git.get_recent_review_comments(file, max_commits=20)
                all_commits.extend(comments)

            if all_commits:
                self.rule_learner.learn_from_commits(all_commits)
        except Exception:
            pass  # Continue even if learning fails

    def review_changes(
        self,
        base_branch: str = "main",
        files: Optional[list[str]] = None,
        max_iterations: int = 10,
    ) -> CodeReviewResult:
        """
        Review code changes in the current branch

        This uses an agentic approach where Claude autonomously decides
        what to investigate next, similar to Greptile v3.

        Args:
            base_branch: Base branch to compare against
            files: Optional list of specific files to review
            max_iterations: Maximum agent iterations (prevents infinite loops)

        Returns:
            CodeReviewResult with findings and investigation steps
        """
        # Get the diff
        diff = self.git.get_diff(base_branch, files)

        if not diff:
            return CodeReviewResult(
                findings=[],
                investigation_steps=["No changes detected"],
                files_reviewed=[],
            )

        # Get changed files
        changed_files = files or self.git.get_changed_files(base_branch)

        # Define tools for the agent
        tools = self._get_tool_definitions()

        # Initial prompt for the agent
        system_prompt = self._get_system_prompt()
        user_message = self._create_review_prompt(diff, changed_files)

        # Run the agentic loop
        findings = []
        investigation_steps = []
        messages = [{"role": "user", "content": user_message}]

        for iteration in range(max_iterations):
            investigation_steps.append(f"Iteration {iteration + 1}: Analyzing code...")

            # Call Claude with tool use
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=tools,
            )

            # Process response
            if response.stop_reason == "end_turn":
                # Agent finished investigation
                investigation_steps.append("Agent completed investigation")
                break

            # Handle tool use
            if response.stop_reason == "tool_use":
                tool_results = []

                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input

                        investigation_steps.append(
                            f"Using tool: {tool_name} with {tool_input}"
                        )

                        # Execute the tool
                        result = self._execute_tool(tool_name, tool_input)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": str(result),
                            }
                        )

                # Add assistant response and tool results to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                # Extract findings from final response
                for content_block in response.content:
                    if hasattr(content_block, "text"):
                        findings.extend(self._parse_findings(content_block.text, changed_files))
                break

        # Apply rule-based checks
        for file_path in changed_files:
            try:
                content = self.search.read_file(file_path)
                if content:
                    violations = self.rule_learner.apply_rules(content, file_path)
                    for violation in violations:
                        findings.append(
                            ReviewFinding(
                                file=violation["file"],
                                line=violation["line"],
                                severity=Severity(violation["severity"]),
                                message=f"[{violation['rule_id']}] {violation['message']}",
                            )
                        )
            except Exception:
                continue

        return CodeReviewResult(
            findings=findings,
            investigation_steps=investigation_steps,
            files_reviewed=changed_files,
        )

    def _get_tool_definitions(self) -> list[dict]:
        """Define tools available to the agent"""
        return [
            {
                "name": "search_codebase",
                "description": "Search for code patterns in the entire codebase. Use this to find similar implementations, related functions, or patterns.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Regex pattern to search for",
                        },
                        "file_pattern": {
                            "type": "string",
                            "description": "File glob pattern (e.g., '*.py')",
                            "default": "*",
                        },
                    },
                    "required": ["pattern"],
                },
            },
            {
                "name": "read_file",
                "description": "Read contents of a specific file to understand implementation details",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file",
                        },
                        "start_line": {
                            "type": "integer",
                            "description": "Optional start line",
                        },
                        "end_line": {
                            "type": "integer",
                            "description": "Optional end line",
                        },
                    },
                    "required": ["file_path"],
                },
            },
            {
                "name": "get_file_history",
                "description": "Get git history for a file to understand when and why changes were made",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file",
                        },
                        "max_commits": {
                            "type": "integer",
                            "description": "Maximum commits to retrieve",
                            "default": 10,
                        },
                    },
                    "required": ["file_path"],
                },
            },
            {
                "name": "find_function_calls",
                "description": "Find all places where a function is called in the codebase",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "function_name": {
                            "type": "string",
                            "description": "Name of the function",
                        },
                        "language": {
                            "type": "string",
                            "description": "Programming language",
                            "default": "python",
                        },
                    },
                    "required": ["function_name"],
                },
            },
            {
                "name": "get_blame",
                "description": "Get git blame to see who last modified specific lines",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file",
                        },
                        "start_line": {
                            "type": "integer",
                            "description": "Start line",
                        },
                        "end_line": {
                            "type": "integer",
                            "description": "End line",
                        },
                    },
                    "required": ["file_path"],
                },
            },
        ]

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent"""
        return """You are an expert code reviewer with deep knowledge of software engineering best practices.

Your task is to review code changes autonomously by:
1. Analyzing the diff to understand what changed
2. Using tools to explore the codebase and find related code
3. Following function calls and dependencies to understand impact
4. Checking git history to understand context
5. Identifying bugs, anti-patterns, security issues, and opportunities for improvement

Take an investigative approach:
- When you see a new function, search for similar implementations
- When you see a calculation, check if it's used consistently elsewhere
- When you see a change to a helper function, find all its callers
- Use git history to understand why code was written a certain way

Focus on:
- Security vulnerabilities (SQL injection, XSS, hardcoded secrets, etc.)
- Logic errors and edge cases
- Performance issues
- Code quality and maintainability
- Consistency with existing codebase patterns

Be thorough but concise. Use tools recursively to build complete understanding."""

    def _create_review_prompt(self, diff: str, changed_files: list[str]) -> str:
        """Create the initial review prompt"""
        return f"""Review the following code changes:

Changed files: {', '.join(changed_files)}

Diff:
```
{diff[:8000]}  # Limit initial diff size
```

Please thoroughly review these changes. Use the available tools to:
1. Understand the full context of changes
2. Find related code in the codebase
3. Check git history for context
4. Identify any issues or improvements

Provide your findings in this format for each issue:
FILE: <file_path>
LINE: <line_number>
SEVERITY: <ERROR|WARNING|INFO>
MESSAGE: <description>
SUGGESTION: <optional suggestion>
---
"""

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool and return the result"""
        try:
            if tool_name == "search_codebase":
                results = self.search.search(
                    tool_input["pattern"],
                    tool_input.get("file_pattern", "*"),
                )
                if not results:
                    return "No matches found"

                output = []
                for result in results[:5]:  # Limit to 5 results
                    output.append(f"\nFile: {result.file}")
                    for match in result.matches[:3]:  # Limit matches per file
                        output.append(f"  Line {match.line}: {match.content}")

                return "\n".join(output)

            elif tool_name == "read_file":
                content = self.search.read_file(
                    tool_input["file_path"],
                    tool_input.get("start_line"),
                    tool_input.get("end_line"),
                )
                return content[:4000]  # Limit content size

            elif tool_name == "get_file_history":
                commits = self.git.get_file_history(
                    tool_input["file_path"],
                    tool_input.get("max_commits", 10),
                )
                if not commits:
                    return "No history found"

                output = []
                for commit in commits[:5]:
                    output.append(
                        f"{commit.hash[:8]} - {commit.author} - {commit.date}\n  {commit.message}"
                    )

                return "\n".join(output)

            elif tool_name == "find_function_calls":
                results = self.search.find_function_calls(
                    tool_input["function_name"],
                    tool_input.get("language", "python"),
                )
                if not results:
                    return "No calls found"

                output = []
                for result in results[:5]:
                    output.append(f"\nFile: {result.file}")
                    for match in result.matches[:2]:
                        output.append(f"  Line {match.line}: {match.content}")

                return "\n".join(output)

            elif tool_name == "get_blame":
                blame = self.git.get_blame(
                    tool_input["file_path"],
                    tool_input.get("start_line"),
                    tool_input.get("end_line"),
                )
                return blame[:2000]  # Limit blame output

            else:
                return f"Unknown tool: {tool_name}"

        except Exception as e:
            return f"Error executing tool: {str(e)}"

    def _parse_findings(self, text: str, changed_files: list[str]) -> list[ReviewFinding]:
        """Parse findings from agent's response"""
        findings = []
        current_finding = {}

        for line in text.split("\n"):
            line = line.strip()

            if line.startswith("FILE:"):
                if current_finding:
                    findings.append(self._create_finding(current_finding))
                current_finding = {"file": line.replace("FILE:", "").strip()}

            elif line.startswith("LINE:"):
                try:
                    current_finding["line"] = int(line.replace("LINE:", "").strip())
                except ValueError:
                    current_finding["line"] = 1

            elif line.startswith("SEVERITY:"):
                severity_str = line.replace("SEVERITY:", "").strip().lower()
                current_finding["severity"] = severity_str

            elif line.startswith("MESSAGE:"):
                current_finding["message"] = line.replace("MESSAGE:", "").strip()

            elif line.startswith("SUGGESTION:"):
                current_finding["suggestion"] = line.replace("SUGGESTION:", "").strip()

            elif line == "---":
                if current_finding:
                    findings.append(self._create_finding(current_finding))
                    current_finding = {}

        # Add last finding if exists
        if current_finding:
            findings.append(self._create_finding(current_finding))

        return findings

    def _create_finding(self, data: dict) -> ReviewFinding:
        """Create a ReviewFinding from parsed data"""
        severity_map = {
            "error": Severity.ERROR,
            "warning": Severity.WARNING,
            "info": Severity.INFO,
        }

        return ReviewFinding(
            file=data.get("file", "unknown"),
            line=data.get("line", 1),
            severity=severity_map.get(data.get("severity", "info"), Severity.INFO),
            message=data.get("message", "No message"),
            suggestion=data.get("suggestion"),
        )
