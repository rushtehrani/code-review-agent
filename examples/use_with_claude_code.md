# Using the Code Reviewer with Claude Code

This code reviewer is built using the **Claude Agent SDK** and provides tools that can be used with Claude Code.

## Architecture

The code reviewer provides 7 MCP (Model Context Protocol) tools:

1. **search_codebase** - Search for patterns across the entire codebase
2. **read_file** - Read file contents with optional line ranges
3. **get_file_history** - Get git history for context
4. **find_function_calls** - Find all calls to a function
5. **get_blame** - See who modified specific lines
6. **apply_code_rules** - Run rule-based checks
7. **get_code_diff** - Get git diff against base branch

## Setup as MCP Server

### Option 1: Run as Standalone MCP Server

```bash
# Run the MCP server
python code_reviewer_mcp.py
```

This starts an MCP server that Claude Code can connect to.

### Option 2: Configure in Claude Code Settings

Add to your Claude Code configuration file (`~/.config/claude/config.json` or project-specific):

```json
{
  "mcpServers": {
    "code-reviewer": {
      "command": "python",
      "args": ["/path/to/code-review-agent/code_reviewer_mcp.py"]
    }
  }
}
```

## Usage with Claude Code

Once configured, you can ask Claude Code to review your code:

```
Please review my recent changes using the code reviewer tools.
```

Claude will autonomously:
1. Use `get_code_diff` to see what changed
2. Use `search_codebase` to find similar code
3. Use `read_file` to read related files
4. Use `get_file_history` to understand context
5. Use `apply_code_rules` to check for issues
6. Provide comprehensive feedback

## Example Session

```
User: Review the changes in main.py

Claude Code will:
1. Call get_code_diff(base_branch="main", files=["main.py"])
2. Call apply_code_rules(file_path="main.py")
3. Call search_codebase(pattern="similar_function")
4. Call get_file_history(file_path="main.py", max_commits=10)
5. Synthesize findings and report issues
```

## Agentic Behavior

Because this uses the Claude Agent SDK, Claude can:
- **Autonomously decide** which tools to use
- **Follow nested calls** by searching for related functions
- **Build context** by reading git history
- **Multi-hop reasoning** across multiple files
- **Learn patterns** from your codebase

## Benefits of SDK Architecture

✅ **Proper tool definitions** - Using SDK's @tool decorator
✅ **MCP protocol** - Standard protocol for tool communication
✅ **Async execution** - Non-blocking tool calls
✅ **Type safety** - Validated input schemas
✅ **Error handling** - Graceful failures
✅ **Claude Code integration** - Works seamlessly with Claude Code CLI

## Programmatic Usage

You can also import and use the tools directly:

```python
from code_reviewer.mcp_tools import (
    search_codebase_tool,
    read_file_tool,
    get_file_history_tool,
    apply_rules_tool,
)

# Use tools directly (async)
import asyncio

async def review_file():
    # Apply rules
    result = await apply_rules_tool({"file_path": "main.py"})
    print(result["content"][0]["text"])

    # Search for patterns
    result = await search_codebase_tool({
        "pattern": "def.*calculate",
        "file_pattern": "*.py",
        "case_sensitive": False
    })
    print(result["content"][0]["text"])

asyncio.run(review_file())
```

## Comparison: SDK vs Direct API

### Before (Direct API):
```python
# Manual tool definitions
tools = [{"name": "search", "description": "..."}]

# Manual agentic loop
for i in range(max_iterations):
    response = client.messages.create(tools=tools, ...)
    # Handle tool use manually
```

### After (Claude Agent SDK):
```python
# Use SDK decorators
@tool("search_codebase", "Search code", {"pattern": str})
async def search_codebase_tool(args):
    return {"content": [...]}

# SDK handles the loop
server = create_sdk_mcp_server(name="code-reviewer", tools=[...])
```

The SDK provides:
- ✅ Built-in agentic loop
- ✅ MCP protocol support
- ✅ Tool registration
- ✅ Type validation
- ✅ Error handling
- ✅ Claude Code integration

## Advanced Configuration

### Custom Repository Path

By default, uses current working directory. To customize:

```python
# Edit code_reviewer/mcp_tools.py
REPO_PATH = "/path/to/your/repo"
```

### Custom Rules

```python
from code_reviewer.tools.rule_learner import RuleLearner
from code_reviewer.models import ReviewRule, Severity

rule_learner = RuleLearner()
rule_learner.add_custom_rule(ReviewRule(
    id="custom-rule",
    pattern=r"bad_pattern",
    message="Don't use this pattern",
    severity=Severity.WARNING
))
```

### Learning from History

The rule learner automatically learns from your git history on initialization:

```python
# Learns from commit messages like:
# "Fix SQL injection in login"
# "Patch XSS vulnerability"
# "Remove hardcoded secrets"
```

## Troubleshooting

### Server Won't Start

```bash
# Check dependencies
pip install -r requirements.txt

# Test import
python -c "from code_reviewer.mcp_tools import server"
```

### Tools Not Available

Make sure the MCP server is running and Claude Code configuration points to the correct path.

### No Git History

If not in a git repository, git-related tools will return appropriate messages. The server will still work for non-git operations.

## References

- [Claude Agent SDK Documentation](https://github.com/anthropics/claude-agent-sdk-python)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Claude Code Documentation](https://claude.com/code)
