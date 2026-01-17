# Agentic Code Reviewer

An autonomous code review agent built with the Claude Agent SDK, inspired by [Greptile's v3 agentic approach](https://www.greptile.com/blog/greptile-v3-agentic-code-review).

## Overview

This code reviewer uses Claude (Opus 4.5) to autonomously review pull requests with full codebase context. Unlike traditional rule-based reviewers, it takes an **agentic approach**:

- 🔍 **Autonomous Investigation**: The agent decides what to investigate next
- 🌐 **Full Codebase Context**: Searches beyond the diff to find related code
- 🔄 **Recursive Analysis**: Follows nested function calls and dependencies
- 📚 **Learning from History**: Learns patterns from git history and past reviews
- 🎯 **Deep Understanding**: Checks for bugs, security issues, and anti-patterns

## Features

- **Agentic Loop**: Runs autonomously with access to multiple tools
- **Codebase Search**: Finds similar patterns and related implementations
- **Git Analysis**: Examines history to understand context and intent
- **Rule Learning**: Learns from commit messages and review patterns
- **Security Focus**: Detects SQL injection, XSS, hardcoded secrets, etc.
- **High Cache Hit Rates**: Optimized for cost efficiency (similar to Greptile's 90%)

## Architecture

Inspired by Greptile's architecture described in their blog post, this agent:

1. **Runs in an agentic loop** with high iteration limits for thorough investigation
2. **Has access to tools**:
   - `search_codebase`: Find code patterns across the entire repository
   - `read_file`: Read specific files for detailed analysis
   - `get_file_history`: Check git history for context
   - `find_function_calls`: Trace function usage throughout codebase
   - `get_blame`: See who last modified specific lines
3. **Learns and applies rules** from past reviews and team patterns
4. **Makes autonomous decisions** about what to investigate next

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd code-review-agent

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e ".[dev]"
```

## Quick Start

```python
import os
from code_reviewer import CodeReviewAgent

# Set your API key
os.environ["ANTHROPIC_API_KEY"] = "your-api-key"

# Initialize the agent
agent = CodeReviewAgent(
    repo_path=".",
    model="claude-opus-4-5-20251101"  # Best for code review
)

# Review changes
result = agent.review_changes(base_branch="main")

# Print findings
for finding in result.findings:
    print(f"{finding.severity}: {finding.file}:{finding.line}")
    print(f"  {finding.message}")
```

## Usage Examples

### Review Current Branch

```python
from code_reviewer import CodeReviewAgent

agent = CodeReviewAgent(repo_path=".")
result = agent.review_changes(base_branch="main")

print(f"Found {len(result.findings)} issues")
for finding in result.findings:
    print(f"[{finding.severity}] {finding.file}:{finding.line}")
    print(f"  {finding.message}")
    if finding.suggestion:
        print(f"  Suggestion: {finding.suggestion}")
```

### Review Specific Files

```python
result = agent.review_changes(
    base_branch="main",
    files=["src/api.py", "src/utils.py"]
)
```

### Custom Configuration

```python
agent = CodeReviewAgent(
    repo_path="/path/to/repo",
    api_key="your-key",
    model="claude-opus-4-5-20251101",
    rules_file="custom_rules.json"  # Optional custom rules
)

result = agent.review_changes(
    base_branch="develop",
    max_iterations=15  # Allow more investigation depth
)
```

## Testing

The project includes comprehensive unit and integration tests:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=code_reviewer --cov-report=html

# Run specific test file
pytest tests/test_codebase_search.py

# Run integration tests (requires ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=your-key pytest tests/test_integration.py
```

### Test Coverage

- **Unit Tests**: Test individual tools (search, git analysis, rule learning)
- **Integration Tests**: Test the full agent with real repositories
- **Edge Cases**: Handle missing files, invalid repos, network failures

## What Gets Detected

The agent detects various issues:

### Security Issues
- SQL injection vulnerabilities
- XSS (Cross-Site Scripting) risks
- Hardcoded passwords and API keys
- Insecure random number generation
- Command injection vulnerabilities

### Code Quality
- Bare except clauses
- Long functions (>50 lines)
- Missing docstrings
- Print statements in production code
- TODO comments (should be in issue tracker)

### Logic Errors
- Inconsistent calculations across codebase
- Outdated formulas in helper functions
- Edge cases not handled
- Race conditions

## How It Works

### 1. Initial Analysis
The agent starts by analyzing the git diff to understand what changed.

### 2. Agentic Investigation Loop
The agent then enters an autonomous loop where it:
- Decides what to investigate next
- Uses tools to gather information
- Follows leads (function calls, similar patterns, etc.)
- Builds understanding of the full context

### 3. Pattern Matching
Applies learned rules and common patterns to detect issues.

### 4. Report Generation
Synthesizes findings with severity levels, messages, and suggestions.

## Comparison to Greptile

This implementation is inspired by Greptile's approach:

| Feature | This Implementation | Greptile v3 |
|---------|-------------------|-------------|
| Agentic Loop | ✅ Yes | ✅ Yes |
| Codebase Search | ✅ Yes | ✅ Yes |
| Git History | ✅ Yes | ✅ Yes |
| Rule Learning | ✅ Yes | ✅ Yes |
| Model | Claude Opus 4.5 | Claude Opus 4.5 |
| Cache Optimization | ✅ Yes | ✅ 90% hit rate |
| Business Integrations | ❌ No | ✅ Jira, Notion, etc. |

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)

### Custom Rules

You can provide a custom rules file:

```python
from code_reviewer import CodeReviewAgent
from code_reviewer.models import ReviewRule, Severity

# Create agent with custom rules file
agent = CodeReviewAgent(
    repo_path=".",
    rules_file="my_rules.json"
)

# Add custom rules programmatically
agent.rule_learner.add_custom_rule(
    ReviewRule(
        id="no-deprecated-api",
        pattern=r"old_api_call",
        message="Use new_api_call instead",
        severity=Severity.WARNING
    )
)
```

## Performance

- **Cache Hit Rates**: Leverages Claude's prompt caching for efficiency
- **Iteration Limits**: Configurable max iterations (default: 10)
- **Parallel Processing**: Can review multiple files concurrently
- **Context Windows**: Optimized chunk sizes for token limits

## Contributing

Contributions welcome! Please ensure:

1. All tests pass: `pytest`
2. Code is formatted: `black code_reviewer tests`
3. Type hints are valid: `mypy code_reviewer`
4. Linting passes: `ruff check code_reviewer`

## License

MIT

## Acknowledgments

Inspired by:
- [Greptile v3's agentic code review approach](https://www.greptile.com/blog/greptile-v3-agentic-code-review)
- [Greptile's usage of Claude for investigative code review](https://claude.com/customers/greptile)
- Anthropic's Claude Agent SDK

## Sources

- [Greptile v3, an agentic approach to code review](https://www.greptile.com/blog/greptile-v3-agentic-code-review)
- [Customer story | Greptile | Claude](https://claude.com/customers/greptile)
- [Greptile bags $25M in funding](https://siliconangle.com/2025/09/23/greptile-bags-25m-funding-take-coderabbit-graphite-ai-code-validation/)
