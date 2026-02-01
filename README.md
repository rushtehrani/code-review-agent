# Agentic Code Reviewer

**Version 0.1.0** - Built with [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)

An agentic code reviewer inspired by [Greptile v3](https://claude.com/customers/greptile) that uses Claude to autonomously review code with full codebase context.

## Features

✅ **Fully Agentic** - Claude autonomously decides which tools to use
✅ **Recursive Investigation** - Follows function calls and dependencies
✅ **Complete Context** - Uses git history, blame, and codebase search
✅ **Pattern Learning** - Learns from your repository's commit history
✅ **MCP Protocol** - Works with Claude Code CLI
✅ **7 Powerful Tools** - Search, read, history, calls, blame, rules, diff

## Installation

```bash
git clone https://github.com/rushtehrani/code-review-agent
cd code-review-agent
pip install -r requirements.txt
export ANTHROPIC_API_KEY='your-key'
```

## Quick Start

### SDK Agent Mode

```python
import asyncio
from code_reviewer import review_code

async def main():
    # Autonomous review using Claude Agent SDK
    result = await review_code(repo_path=".", base_branch="main")

    # Display findings
    for finding in result.findings:
        print(f"[{finding.severity.value.upper()}] {finding.file}:{finding.line}")
        print(f"  {finding.message}")

asyncio.run(main())
```

### MCP Server Mode

```bash
# Run as MCP server
python code_reviewer_mcp.py

# Configure Claude Code (~/.config/claude/config.json):
{
  "mcpServers": {
    "code-reviewer": {
      "command": "python",
      "args": ["/path/to/code_reviewer_mcp.py"]
    }
  }
}

# Then in Claude Code:
# "Please review my recent changes"
```

## How It Works

### Agentic Architecture

The code reviewer uses the Claude Agent SDK's `query()` function to enable fully autonomous code review:

1. **You provide the diff** - Changed files and git diff
2. **Claude investigates autonomously** - Decides which tools to use
3. **Recursive exploration** - Follows chains up to 10+ tool uses
4. **Complete context** - Searches codebase, reads files, checks history
5. **Comprehensive report** - Synthesizes findings with severity levels

### Example Investigation

```
User: Review changes in auth.py

Claude autonomously:
├─ get_code_diff → Sees new authentication function
├─ search_codebase("auth") → Finds 3 similar functions
├─ read_file("auth_helpers.py") → Reads existing implementation
├─ get_file_history("auth_helpers.py") → Sees security patch history
├─ find_function_calls("validate_token") → Finds 12 call sites
├─ get_blame("auth_helpers.py", 45, 60) → Checks authorship
├─ search_codebase("password.*=") → Searches for hardcoded secrets
├─ read_file("api/endpoints.py") → Reads dependent code
└─ apply_code_rules("auth.py") → Runs learned rules

Result: Comprehensive review with full context
```

## 7 MCP Tools

The agent has access to 7 specialized tools:

1. **search_codebase** - Search for patterns across entire repository
2. **read_file** - Read files with optional line ranges
3. **get_file_history** - Get git commit history for context
4. **find_function_calls** - Find all places a function is called
5. **get_blame** - Git blame to see who modified lines
6. **apply_code_rules** - Run learned security and quality rules
7. **get_code_diff** - Get git diff against base branch

## API Reference

### CodeReviewAgent

```python
from code_reviewer import CodeReviewAgent

reviewer = CodeReviewAgent(
    repo_path: str = ".",
    api_key: Optional[str] = None,  # Uses ANTHROPIC_API_KEY env var
    model: str = "claude-opus-4-5-20251101"
)

# Autonomous review
result = await reviewer.review_changes(
    base_branch: str = "main",
    files: Optional[list[str]] = None,
    stream: bool = True
)

# Interactive session
async for message in reviewer.interactive_review():
    print(message)
```

### Convenience Function

```python
from code_reviewer import review_code

result = await review_code(
    repo_path=".",
    base_branch="main",
    files=None,  # Review all changed files
    api_key=None,  # Uses env var
    model="claude-opus-4-5-20251101"
)
```

### Models

```python
@dataclass
class CodeReviewResult:
    findings: list[ReviewFinding]
    investigation_steps: list[str]
    files_reviewed: list[str]
    cache_hit_rate: Optional[float]

@dataclass
class ReviewFinding:
    file: str
    line: int
    severity: Severity  # ERROR, WARNING, INFO
    message: str
    suggestion: Optional[str]
    related_code: list[str]
```

## Usage Examples

### Basic Review

```python
import asyncio
from code_reviewer import review_code

async def main():
    result = await review_code(repo_path=".")

    # Group by severity
    errors = [f for f in result.findings if f.severity.value == "error"]
    warnings = [f for f in result.findings if f.severity.value == "warning"]

    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")

asyncio.run(main())
```

### Review Specific Files

```python
from code_reviewer import CodeReviewAgent

async def review_specific():
    reviewer = CodeReviewAgent(repo_path=".")

    result = await reviewer.review_changes(
        base_branch="main",
        files=["src/auth.py", "src/api.py"]
    )

    for finding in result.findings:
        print(f"{finding.file}:{finding.line} - {finding.message}")

asyncio.run(review_specific())
```

### Interactive Session

```python
from code_reviewer import CodeReviewAgent

async def interactive():
    reviewer = CodeReviewAgent(repo_path=".")

    async for message in reviewer.interactive_review():
        if hasattr(message, 'content'):
            print(message.content)

asyncio.run(interactive())
```

## Comparison to Greptile v3

This implementation follows Greptile's v3 agentic architecture:

| Feature | This Implementation | Greptile v3 |
|---------|-------------------|-------------|
| Framework | Claude Agent SDK | Custom |
| Agentic Loop | SDK query() | Custom loop |
| Autonomous | ✅ Claude decides | ✅ Claude decides |
| Codebase Search | ✅ search_codebase | ✅ Similar |
| Git History | ✅ get_file_history | ✅ Similar |
| Recursive | ✅ 10+ iterations | ✅ High limits |
| Learning | ✅ From commits | ✅ From reviews |
| Model | ✅ Opus 4.5 | ✅ Opus 4.5 |
| MCP Protocol | ✅ Full support | ✅ Full support |

## Testing

```bash
# Run all tests
pytest tests/

# With coverage
pytest tests/ --cov=code_reviewer --cov-report=term
```

**Test Results:**
- 105 tests passing ✅
- 67% code coverage
- 16 SDK agent tests
- 9 MCP tool tests
- 80 tool and model tests

## Architecture

### Files

```
code-review-agent/
├── code_reviewer/
│   ├── __init__.py         # Package exports
│   ├── agent.py            # Main SDK agent (100 lines, 77% coverage)
│   ├── mcp_tools.py        # MCP tools (7 tools)
│   ├── models.py           # Data models (100% coverage)
│   └── tools/              # Tool implementations
│       ├── codebase_search.py  # Pattern search (70% coverage)
│       ├── git_analyzer.py     # Git operations (78% coverage)
│       └── rule_learner.py     # Pattern learning (94% coverage)
├── tests/                  # 105 comprehensive tests
├── examples/               # Usage examples
└── code_reviewer_mcp.py    # MCP server entry point
```

### SDK Integration

Uses Claude Agent SDK components:
- **query()** - For autonomous reviews
- **ClaudeSDKClient** - For interactive sessions
- **ClaudeAgentOptions** - For configuration
- **@tool** - For MCP tool definitions
- **create_sdk_mcp_server** - For MCP server

## Documentation

- **README.md** (this file) - Getting started
- **examples/** - Code examples

## Requirements

- Python 3.11+
- claude-agent-sdk >= 0.1.27
- GitPython >= 3.1.0
- pydantic >= 2.0.0
- anthropic >= 0.40.0 (indirect dependency)

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY='your-key-here'
```

### "Not a git repository"
Ensure you're running from within a git repository:
```bash
cd your-git-repo
python your_script.py
```

### "Module not found: claude_agent_sdk"
```bash
pip install claude-agent-sdk>=0.1.27
```

## Contributing

Contributions welcome! Please:
1. Maintain SDK architecture patterns
2. Add tests for new features
3. Keep coverage above 65%
4. Follow agentic design principles

## License

MIT

## Credits

Built with:
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)
- [Anthropic Claude Opus 4.5](https://www.anthropic.com/claude)
- [GitPython](https://gitpython.readthedocs.io/)
- [Pydantic](https://docs.pydantic.dev/)

Inspired by:
- [Greptile v3](https://www.greptile.com/blog/greptile-v3-agentic-code-review)
- [Greptile at Anthropic](https://claude.com/customers/greptile)

## References

- [Claude Agent SDK Documentation](https://github.com/anthropics/claude-agent-sdk-python)
- [Greptile v3 Blog Post](https://www.greptile.com/blog/greptile-v3-agentic-code-review)
- [Claude Code CLI](https://claude.com/code)
- [MCP Protocol](https://modelcontextprotocol.io/)

---

**Version 0.1.0** - Built with Claude Agent SDK
