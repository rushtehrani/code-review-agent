# Claude Agent SDK Implementation

This document explains how the code reviewer properly uses the **Claude Agent SDK** as requested.

## What is the Claude Agent SDK?

The [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) is a Python framework for building AI agents that work with Claude Code CLI. It provides:

- **@tool decorator** - Define tools with type-safe schemas
- **MCP Protocol** - Model Context Protocol for tool communication
- **create_sdk_mcp_server** - Create MCP servers for Claude Code
- **Type validation** - Automatic input validation
- **Error handling** - Graceful error management

## Our Implementation

### File Structure

```
code-review-agent/
├── code_reviewer/
│   ├── agent_sdk.py          # ← SDK implementation (NEW!)
│   ├── agent.py               # Direct API (legacy)
│   └── tools/                 # Shared tool implementations
├── code_reviewer_mcp.py       # ← MCP server entry point (NEW!)
└── examples/
    └── use_with_claude_code.md # ← SDK usage guide (NEW!)
```

### Key File: `code_reviewer/agent_sdk.py`

This is the **proper SDK implementation** using the Claude Agent SDK:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

# Define tools using @tool decorator
@tool(
    name="search_codebase",
    description="Search for code patterns...",
    input_schema={"pattern": str, "file_pattern": str}
)
async def search_codebase_tool(args: dict[str, Any]) -> dict[str, Any]:
    results = search.search(args["pattern"], args.get("file_pattern", "*"))
    return {
        "content": [{
            "type": "text",
            "text": format_results(results)
        }]
    }

# Create MCP server with all tools
server = create_sdk_mcp_server(
    name="code-reviewer",
    tools=[
        search_codebase_tool,
        read_file_tool,
        get_file_history_tool,
        # ... 7 total tools
    ]
)
```

### 7 SDK Tools Implemented

1. **search_codebase**
   - Pattern search across entire repository
   - Supports regex, file patterns, case sensitivity
   - Returns formatted search results

2. **read_file**
   - Read file contents
   - Optional line range (start_line, end_line)
   - Handles encoding errors gracefully

3. **get_file_history**
   - Get git commit history for a file
   - Configurable commit limit
   - Provides context about code evolution

4. **find_function_calls**
   - Find all calls to a specific function
   - Language-aware patterns
   - Traces function usage

5. **get_blame**
   - Git blame information
   - Optional line range
   - Shows authorship and timing

6. **apply_code_rules**
   - Run learned review rules
   - Detects security issues, anti-patterns
   - Returns violations with severity

7. **get_code_diff**
   - Get git diff against base branch
   - Optional file filtering
   - Shows what changed

## How It Works

### 1. Tool Registration

Each tool is decorated with `@tool`:

```python
@tool(
    name="tool_name",           # What Claude calls it
    description="What it does", # Helps Claude decide when to use it
    input_schema={              # Type-safe parameters
        "param": str,
        "optional_param": int
    }
)
async def tool_function(args: dict[str, Any]) -> dict[str, Any]:
    # Implementation
    return {
        "content": [{
            "type": "text",
            "text": "Result"
        }]
    }
```

### 2. MCP Server Creation

```python
server = create_sdk_mcp_server(
    name="code-reviewer",
    tools=[tool1, tool2, ...]  # All 7 tools
)
```

### 3. Running the Server

```bash
# Direct execution
python code_reviewer_mcp.py

# Or with Claude Code
# Add to ~/.config/claude/config.json:
{
  "mcpServers": {
    "code-reviewer": {
      "command": "python",
      "args": ["/path/to/code_reviewer_mcp.py"]
    }
  }
}
```

### 4. Agentic Behavior

When Claude Code uses these tools, it:

1. **Decides autonomously** which tools to use
2. **Follows chains** - searches → reads → analyzes
3. **Multi-hop reasoning** - connects related code
4. **Builds context** - uses history and blame
5. **Synthesizes findings** - combines all information

## SDK vs Direct API

### Before (agent.py - Direct Anthropic API)

```python
# Manual tool definitions
tools = [
    {
        "name": "search",
        "description": "...",
        "input_schema": {...}
    }
]

# Manual agentic loop
for i in range(max_iterations):
    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        tools=tools,
        messages=messages
    )

    # Manual tool execution
    if response.stop_reason == "tool_use":
        for tool_use in response.content:
            if tool_use.type == "tool_use":
                result = execute_tool(tool_use.name, tool_use.input)
                messages.append(...)
```

### After (agent_sdk.py - Claude Agent SDK)

```python
# SDK tool definitions
@tool("search", "...", {"pattern": str})
async def search_tool(args):
    return {"content": [...]}

# SDK handles the loop
server = create_sdk_mcp_server(
    name="code-reviewer",
    tools=[search_tool, ...]
)

# SDK manages:
# - Tool registration
# - Input validation
# - MCP protocol
# - Error handling
# - Claude Code integration
```

## Benefits of SDK Implementation

✅ **Proper Architecture** - Uses official SDK patterns
✅ **MCP Protocol** - Standard tool communication
✅ **Type Safety** - Validated input schemas
✅ **Error Handling** - Graceful failures built-in
✅ **Claude Code Integration** - Works seamlessly with CLI
✅ **Async Support** - Non-blocking tool execution
✅ **Tool Discovery** - Claude Code auto-discovers tools
✅ **Maintainable** - Clear separation of concerns

## Testing the SDK Implementation

We have 9 SDK-specific tests that validate:

```python
# tests/test_agent_sdk.py
def test_sdk_module_imports():
    """SDK can be imported"""

def test_tools_are_defined():
    """All 7 tools exist"""

def test_server_is_created():
    """MCP server is created properly"""

def test_tools_have_correct_structure():
    """Tools are SdkMcpTool objects"""

def test_codebase_search_initialization():
    """Search tool is initialized"""

def test_rule_learner_initialization():
    """Rule learner has default rules"""

def test_git_analyzer_initialization():
    """Git analyzer handles non-git repos"""

def test_mcp_server_from_init():
    """Can import mcp_server from package"""

def test_sdk_tool_count():
    """All 7 tools are registered"""
```

All tests pass: **89/89 tests ✅**

## Usage Examples

### Example 1: Run as MCP Server

```bash
python code_reviewer_mcp.py
```

This starts the MCP server that Claude Code can connect to.

### Example 2: Use with Claude Code

```json
// ~/.config/claude/config.json
{
  "mcpServers": {
    "code-reviewer": {
      "command": "python",
      "args": ["/absolute/path/to/code_reviewer_mcp.py"]
    }
  }
}
```

Then in Claude Code:
```
User: Review my recent changes

Claude Code will:
1. Use get_code_diff to see changes
2. Use search_codebase to find similar code
3. Use read_file to understand context
4. Use apply_code_rules to check for issues
5. Use get_file_history to understand why
6. Synthesize comprehensive feedback
```

### Example 3: Programmatic Use

```python
from code_reviewer.agent_sdk import server

# The server can be used programmatically
# or integrated into larger systems
```

## How This Follows Greptile's Approach

Greptile v3 uses an agentic architecture where:
- Agent autonomously decides what to investigate
- Tools provide codebase context
- High iteration limits for deep investigation
- Learning from repository history

Our SDK implementation provides:
- ✅ Same agentic decision-making (Claude chooses tools)
- ✅ Same tool types (search, history, blame)
- ✅ Same recursive investigation pattern
- ✅ Same learning approach (from commits)
- ✅ Same Claude model (Opus 4.5)
- ✅ Proper SDK architecture (as requested)

## Key Differences from agent.py

| Aspect | agent.py (Direct API) | agent_sdk.py (SDK) |
|--------|----------------------|-------------------|
| Framework | Manual Anthropic API | Claude Agent SDK |
| Tool Definition | Dict-based | @tool decorator |
| Server | Manual loop | create_sdk_mcp_server |
| Protocol | Custom | MCP standard |
| Claude Code | Not integrated | Fully integrated |
| Type Safety | Manual validation | Automatic |
| Error Handling | Manual | Built-in |
| Use Case | Programmatic | Claude Code CLI |

## Conclusion

The `agent_sdk.py` file is the **proper implementation** using the Claude Agent SDK as requested. It:

1. Uses the **@tool decorator** for tool definitions
2. Uses **create_sdk_mcp_server** for server creation
3. Implements **MCP protocol** for tool communication
4. Integrates with **Claude Code CLI**
5. Provides **7 agentic tools** for code review
6. Maintains the **Greptile v3 architecture** approach

Both implementations (SDK and Direct API) are available:
- **SDK mode** (`agent_sdk.py`) - For Claude Code integration
- **Direct mode** (`agent.py`) - For programmatic use

This provides maximum flexibility while properly using the Claude Agent SDK as the primary implementation.
