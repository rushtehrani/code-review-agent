"""
Agentic Code Reviewer - Built with Claude Agent SDK

An agentic code reviewer that uses the Claude Agent SDK to provide
tools for autonomous code review.
"""

import os
from pathlib import Path
from typing import Any
from claude_agent_sdk import tool, create_sdk_mcp_server
from code_reviewer.tools.codebase_search import CodebaseSearch
from code_reviewer.tools.git_analyzer import GitAnalyzer
from code_reviewer.tools.rule_learner import RuleLearner


# Initialize tools with current directory
REPO_PATH = os.getcwd()
search = CodebaseSearch(REPO_PATH)
try:
    git = GitAnalyzer(REPO_PATH)
except ValueError:
    git = None  # Not a git repository
rule_learner = RuleLearner()


@tool(
    name="search_codebase",
    description="Search for code patterns across the entire codebase. Use this to find similar implementations, related functions, or patterns. Supports regex patterns.",
    input_schema={
        "pattern": str,
        "file_pattern": str,
        "case_sensitive": bool,
    }
)
async def search_codebase_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Search the codebase for patterns"""
    pattern = args["pattern"]
    file_pattern = args.get("file_pattern", "*")
    case_sensitive = args.get("case_sensitive", False)

    results = search.search(pattern, file_pattern, case_sensitive)

    if not results:
        return {
            "content": [{
                "type": "text",
                "text": f"No matches found for pattern: {pattern}"
            }]
        }

    # Format results
    output = [f"Found {len(results)} file(s) matching pattern '{pattern}':\n"]

    for result in results[:5]:  # Limit to 5 files
        output.append(f"\n📄 {result.file}")
        for match in result.matches[:3]:  # Limit to 3 matches per file
            output.append(f"  Line {match.line}: {match.content.strip()}")

    if len(results) > 5:
        output.append(f"\n... and {len(results) - 5} more files")

    return {
        "content": [{
            "type": "text",
            "text": "\n".join(output)
        }]
    }


@tool(
    name="read_file",
    description="Read the contents of a specific file to understand implementation details. Can optionally read specific line ranges.",
    input_schema={
        "file_path": str,
        "start_line": int,
        "end_line": int,
    }
)
async def read_file_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Read a file from the codebase"""
    file_path = args["file_path"]
    start_line = args.get("start_line")
    end_line = args.get("end_line")

    content = search.read_file(file_path, start_line, end_line)

    if not content:
        return {
            "content": [{
                "type": "text",
                "text": f"File not found or empty: {file_path}"
            }]
        }

    # Limit content size
    if len(content) > 4000:
        content = content[:4000] + "\n... (truncated)"

    line_range = ""
    if start_line and end_line:
        line_range = f" (lines {start_line}-{end_line})"

    return {
        "content": [{
            "type": "text",
            "text": f"📄 {file_path}{line_range}:\n\n{content}"
        }]
    }


@tool(
    name="get_file_history",
    description="Get git history for a file to understand when and why changes were made. Helps provide context about the evolution of code.",
    input_schema={
        "file_path": str,
        "max_commits": int,
    }
)
async def get_file_history_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Get git history for a file"""
    if git is None:
        return {
            "content": [{
                "type": "text",
                "text": "Not a git repository"
            }]
        }

    file_path = args["file_path"]
    max_commits = args.get("max_commits", 10)

    commits = git.get_file_history(file_path, max_commits)

    if not commits:
        return {
            "content": [{
                "type": "text",
                "text": f"No history found for {file_path}"
            }]
        }

    output = [f"📚 Git history for {file_path}:\n"]
    for commit in commits[:5]:  # Limit to 5 commits
        output.append(f"\n{commit.hash[:8]} - {commit.author} - {commit.date}")
        output.append(f"  {commit.message.split(chr(10))[0][:80]}")  # First line only

    return {
        "content": [{
            "type": "text",
            "text": "\n".join(output)
        }]
    }


@tool(
    name="find_function_calls",
    description="Find all places where a specific function is called in the codebase. Useful for understanding impact and dependencies.",
    input_schema={
        "function_name": str,
        "language": str,
    }
)
async def find_function_calls_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Find all calls to a specific function"""
    function_name = args["function_name"]
    language = args.get("language", "python")

    results = search.find_function_calls(function_name, language)

    if not results:
        return {
            "content": [{
                "type": "text",
                "text": f"No calls found for function: {function_name}"
            }]
        }

    output = [f"🔍 Found {sum(len(r.matches) for r in results)} call(s) to '{function_name}':\n"]

    for result in results[:5]:
        output.append(f"\n📄 {result.file}")
        for match in result.matches[:2]:
            output.append(f"  Line {match.line}: {match.content.strip()}")

    return {
        "content": [{
            "type": "text",
            "text": "\n".join(output)
        }]
    }


@tool(
    name="get_blame",
    description="Get git blame information to see who last modified specific lines of code. Helps understand authorship and context.",
    input_schema={
        "file_path": str,
        "start_line": int,
        "end_line": int,
    }
)
async def get_blame_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Get git blame for a file"""
    if git is None:
        return {
            "content": [{
                "type": "text",
                "text": "Not a git repository"
            }]
        }

    file_path = args["file_path"]
    start_line = args.get("start_line")
    end_line = args.get("end_line")

    blame = git.get_blame(file_path, start_line, end_line)

    if not blame:
        return {
            "content": [{
                "type": "text",
                "text": f"No blame info available for {file_path}"
            }]
        }

    # Limit blame output
    if len(blame) > 2000:
        blame = blame[:2000] + "\n... (truncated)"

    return {
        "content": [{
            "type": "text",
            "text": f"👤 Git blame for {file_path}:\n\n{blame}"
        }]
    }


@tool(
    name="apply_code_rules",
    description="Apply learned code review rules to detect common issues like security vulnerabilities, code quality problems, and anti-patterns.",
    input_schema={
        "file_path": str,
    }
)
async def apply_rules_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Apply code review rules to a file"""
    file_path = args["file_path"]

    content = search.read_file(file_path)
    if not content:
        return {
            "content": [{
                "type": "text",
                "text": f"Cannot read file: {file_path}"
            }]
        }

    violations = rule_learner.apply_rules(content, file_path)

    if not violations:
        return {
            "content": [{
                "type": "text",
                "text": f"✅ No rule violations found in {file_path}"
            }]
        }

    output = [f"⚠️  Found {len(violations)} issue(s) in {file_path}:\n"]

    severity_icons = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}

    for v in violations[:10]:  # Limit to 10 violations
        icon = severity_icons.get(v["severity"], "•")
        output.append(f"\n{icon} Line {v['line']} [{v['severity'].upper()}]")
        output.append(f"  {v['message']}")

    if len(violations) > 10:
        output.append(f"\n... and {len(violations) - 10} more issues")

    return {
        "content": [{
            "type": "text",
            "text": "\n".join(output)
        }]
    }


@tool(
    name="get_code_diff",
    description="Get git diff to see what changes were made. Compare current branch against a base branch.",
    input_schema={
        "base_branch": str,
        "files": list[str],
    }
)
async def get_diff_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Get git diff"""
    if git is None:
        return {
            "content": [{
                "type": "text",
                "text": "Not a git repository"
            }]
        }

    base_branch = args.get("base_branch", "main")
    files = args.get("files")

    diff = git.get_diff(base_branch, files)

    if not diff:
        return {
            "content": [{
                "type": "text",
                "text": f"No diff found against {base_branch}"
            }]
        }

    # Limit diff size
    if len(diff) > 6000:
        diff = diff[:6000] + "\n... (truncated)"

    return {
        "content": [{
            "type": "text",
            "text": f"📊 Diff against {base_branch}:\n\n```diff\n{diff}\n```"
        }]
    }


# Create the MCP server with all tools
server = create_sdk_mcp_server(
    name="code-reviewer",
    tools=[
        search_codebase_tool,
        read_file_tool,
        get_file_history_tool,
        find_function_calls_tool,
        get_blame_tool,
        apply_rules_tool,
        get_diff_tool,
    ]
)


if __name__ == "__main__":
    # Run the server
    import asyncio
    asyncio.run(server.run())
