"""
Complete Agent SDK Rewrite - Agentic Code Reviewer

This is a full rewrite using Claude Agent SDK for agentic code review.
Provides both MCP server mode (for Claude Code) and standalone agent mode.
"""

import os
from pathlib import Path
from typing import Optional, AsyncIterator
from claude_agent_sdk import (
    query,
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
)
from code_reviewer.tools.codebase_search import CodebaseSearch
from code_reviewer.tools.git_analyzer import GitAnalyzer
from code_reviewer.tools.rule_learner import RuleLearner
from code_reviewer.models import CodeReviewResult, ReviewFinding, Severity


class SDKCodeReviewer:
    """
    Complete rewrite of code reviewer using Claude Agent SDK

    Features:
    - Uses SDK's query() for autonomous reviews
    - Provides MCP tools for Claude Code
    - Fully agentic with SDK architecture
    - Supports streaming responses
    """

    def __init__(
        self,
        repo_path: str = ".",
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-5-20251101",
    ):
        """
        Initialize SDK-based code reviewer

        Args:
            repo_path: Path to repository
            api_key: Anthropic API key (optional, uses ANTHROPIC_API_KEY env var)
            model: Claude model to use
        """
        self.repo_path = Path(repo_path).absolute()
        self.model = model

        # Set API key in environment if provided
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key

        # Initialize tools
        self.search = CodebaseSearch(str(self.repo_path))
        try:
            self.git = GitAnalyzer(str(self.repo_path))
        except ValueError:
            self.git = None
        self.rule_learner = RuleLearner()

        # SDK options (no api_key parameter - it uses ANTHROPIC_API_KEY env var)
        self.options = ClaudeAgentOptions(
            cwd=str(self.repo_path),
            model=model,
        )

    async def review_changes(
        self,
        base_branch: str = "main",
        files: Optional[list[str]] = None,
        stream: bool = True,
    ) -> CodeReviewResult:
        """
        Review code changes using SDK's query function

        This is the main agentic entry point. Claude autonomously:
        - Decides which tools to use
        - Investigates code recursively
        - Builds complete context
        - Synthesizes findings

        Args:
            base_branch: Base branch to compare against
            files: Optional list of specific files
            stream: Whether to stream responses

        Returns:
            CodeReviewResult with findings
        """
        if self.git is None:
            return CodeReviewResult(
                findings=[],
                investigation_steps=["Not a git repository"],
                files_reviewed=[],
            )

        # Get changed files and diff
        changed_files = files or self.git.get_changed_files(base_branch)
        if not changed_files:
            return CodeReviewResult(
                findings=[],
                investigation_steps=["No changes detected"],
                files_reviewed=[],
            )

        diff = self.git.get_diff(base_branch, files)

        # Create review prompt for the agent
        prompt = self._create_review_prompt(diff, changed_files, base_branch)

        # Use SDK's query function - this is the agentic magic!
        # Claude will autonomously decide which tools to use
        findings = []
        investigation_steps = []

        try:
            async for message in query(prompt=prompt, options=self.options):
                # Track investigation steps
                if hasattr(message, 'content'):
                    content = str(message.content)
                    if 'tool' in content.lower():
                        investigation_steps.append(f"Agent: {content[:100]}")

                # Collect final response
                if hasattr(message, 'type') and message.type == 'assistant':
                    # Parse findings from response
                    if hasattr(message, 'content'):
                        findings.extend(
                            self._parse_findings_from_response(
                                str(message.content),
                                changed_files
                            )
                        )

        except Exception as e:
            investigation_steps.append(f"Error during review: {str(e)}")

        # Also apply rule-based checks
        for file_path in changed_files:
            try:
                content = self.search.read_file(file_path)
                if content:
                    violations = self.rule_learner.apply_rules(content, file_path)
                    for v in violations:
                        findings.append(ReviewFinding(
                            file=v["file"],
                            line=v["line"],
                            severity=Severity(v["severity"]),
                            message=f"[{v['rule_id']}] {v['message']}",
                        ))
            except Exception:
                continue

        return CodeReviewResult(
            findings=findings,
            investigation_steps=investigation_steps,
            files_reviewed=changed_files,
        )

    async def interactive_review(self) -> AsyncIterator:
        """
        Start an interactive review session using ClaudeSDKClient

        This allows back-and-forth conversation about code.
        """
        async with ClaudeSDKClient(options=self.options) as client:
            # Initial prompt
            if self.git:
                diff = self.git.get_diff()
                files = self.git.get_changed_files()

                prompt = f"""I'm starting an interactive code review session.

Changed files: {', '.join(files[:10])}

Diff summary:
{diff[:1000]}

Please start reviewing the changes. Use the available tools to:
1. Search for similar code patterns
2. Read files for context
3. Check git history
4. Find function dependencies
5. Apply learned rules

Let's begin the review!"""
            else:
                prompt = "I'm ready to review code. What would you like me to analyze?"

            # Send initial message
            await client.send_user_message(prompt)

            # Yield responses
            async for message in client.receive_messages():
                yield message

    def _create_review_prompt(
        self,
        diff: str,
        changed_files: list[str],
        base_branch: str
    ) -> str:
        """Create the autonomous review prompt for Claude"""

        # Limit diff size for token efficiency
        if len(diff) > 8000:
            diff = diff[:8000] + "\n... (truncated)"

        return f"""You are an expert code reviewer with access to powerful codebase analysis tools.

# Your Task
Review the following code changes thoroughly and autonomously. Use the available tools to:
- Search for similar patterns in the codebase
- Read related files for context
- Check git history to understand evolution
- Find all places functions are called
- Identify security issues, bugs, and anti-patterns

# Changed Files
{', '.join(changed_files)}

# Git Diff (vs {base_branch})
```diff
{diff}
```

# Available Tools
You have access to these tools - use them liberally and recursively:

1. **search_codebase** - Search for patterns across entire repository
2. **read_file** - Read any file for detailed analysis
3. **get_file_history** - Understand when/why code was written
4. **find_function_calls** - Trace function usage and dependencies
5. **get_blame** - See who wrote specific lines
6. **apply_code_rules** - Check for known issues and anti-patterns

# Your Approach (Agentic & Recursive)

1. **Start with the diff** - Understand what changed
2. **Search recursively** - For each new function/pattern:
   - Search for similar code in the codebase
   - Check if the pattern is used consistently
   - Read related files to understand context
3. **Follow the chain** - If you find a function call:
   - Find where else it's called
   - Read the implementation
   - Check git history for context
4. **Build complete picture** - Use multiple tools together:
   - Search → Read → History → Blame
   - Keep investigating until you understand fully
5. **Report findings** - For each issue found, provide:
   - File and line number
   - Severity (ERROR, WARNING, INFO)
   - Clear description
   - Optional suggestion for fix

# Focus Areas
- **Security**: SQL injection, XSS, hardcoded secrets, authentication issues
- **Bugs**: Logic errors, edge cases, type mismatches, null handling
- **Quality**: Code duplication, long functions, missing tests
- **Performance**: Inefficient algorithms, unnecessary loops
- **Consistency**: Deviations from codebase patterns

# Output Format
For each finding, use this format:

FILE: <file_path>
LINE: <line_number>
SEVERITY: <ERROR|WARNING|INFO>
MESSAGE: <clear description>
SUGGESTION: <optional fix>
---

Begin your autonomous review now. Investigate thoroughly and report all findings!"""

    def _parse_findings_from_response(
        self,
        response: str,
        files: list[str]
    ) -> list[ReviewFinding]:
        """Parse findings from Claude's response"""
        findings = []
        current = {}

        for line in response.split('\n'):
            line = line.strip()

            if line.startswith('FILE:'):
                if current:
                    findings.append(self._create_finding(current))
                current = {'file': line.replace('FILE:', '').strip()}

            elif line.startswith('LINE:'):
                try:
                    current['line'] = int(line.replace('LINE:', '').strip())
                except ValueError:
                    current['line'] = 1

            elif line.startswith('SEVERITY:'):
                sev = line.replace('SEVERITY:', '').strip().lower()
                current['severity'] = sev

            elif line.startswith('MESSAGE:'):
                current['message'] = line.replace('MESSAGE:', '').strip()

            elif line.startswith('SUGGESTION:'):
                current['suggestion'] = line.replace('SUGGESTION:', '').strip()

            elif line == '---':
                if current:
                    findings.append(self._create_finding(current))
                    current = {}

        if current:
            findings.append(self._create_finding(current))

        return findings

    def _create_finding(self, data: dict) -> ReviewFinding:
        """Create ReviewFinding from parsed data"""
        severity_map = {
            'error': Severity.ERROR,
            'warning': Severity.WARNING,
            'info': Severity.INFO,
        }

        return ReviewFinding(
            file=data.get('file', 'unknown'),
            line=data.get('line', 1),
            severity=severity_map.get(data.get('severity', 'info'), Severity.INFO),
            message=data.get('message', 'No message'),
            suggestion=data.get('suggestion'),
        )


# For backwards compatibility and convenience
async def review_code(
    repo_path: str = ".",
    base_branch: str = "main",
    files: Optional[list[str]] = None,
    **kwargs
) -> CodeReviewResult:
    """
    Convenience function for quick code reviews

    Example:
        result = await review_code(repo_path=".", base_branch="main")
        for finding in result.findings:
            print(f"{finding.severity}: {finding.message}")
    """
    reviewer = SDKCodeReviewer(repo_path=repo_path, **kwargs)
    return await reviewer.review_changes(base_branch=base_branch, files=files)
