# Architecture Documentation

## Overview

This agentic code reviewer is built using the Claude Agent SDK and follows the architecture patterns described by Greptile in their v3 release.

## Core Principles

### 1. Agentic Approach

Unlike traditional sequential code review tools, this system:
- Runs in an **autonomous loop**
- Makes its own decisions about what to investigate
- Has **high iteration limits** (10+ turns) for deep investigation
- Uses tools to recursively explore the codebase

### 2. Tool-Based Architecture

The agent has access to specialized tools:

```
┌─────────────────────────────────────┐
│      CodeReviewAgent (Main)         │
│                                     │
│  - Agentic loop controller          │
│  - Claude API integration           │
│  - Finding synthesis                │
└──────────────┬──────────────────────┘
               │
               ├──────────────────────────┐
               │                          │
               ▼                          ▼
    ┌──────────────────┐      ┌──────────────────┐
    │  CodebaseSearch  │      │   GitAnalyzer    │
    │                  │      │                  │
    │  - Pattern search│      │  - File history  │
    │  - File reading  │      │  - Blame info    │
    │  - Function calls│      │  - Commit diffs  │
    └──────────────────┘      └──────────────────┘
               │
               ▼
    ┌──────────────────┐
    │   RuleLearner    │
    │                  │
    │  - Pattern rules │
    │  - Learning      │
    │  - Violations    │
    └──────────────────┘
```

## Component Details

### CodeReviewAgent

**Responsibilities:**
- Initialize Claude client and tools
- Orchestrate the review process
- Manage the agentic loop
- Parse and synthesize findings

**Key Methods:**
- `review_changes()`: Main entry point
- `_execute_tool()`: Handle tool execution
- `_parse_findings()`: Extract findings from agent responses

**Agentic Loop:**

```python
for iteration in range(max_iterations):
    # 1. Call Claude with tools
    response = client.messages.create(
        model=model,
        tools=tools,
        messages=messages
    )

    # 2. Handle tool use
    if response.stop_reason == "tool_use":
        for tool in response.tool_uses:
            result = execute_tool(tool)
            messages.append(result)

    # 3. Continue until end_turn
    elif response.stop_reason == "end_turn":
        break
```

### CodebaseSearch

**Responsibilities:**
- Search for patterns using ripgrep/grep
- Find files by glob patterns
- Read file contents
- Locate function calls and similar code

**Key Features:**
- Fast regex search with ripgrep
- Fallback to grep if ripgrep unavailable
- Context lines for better understanding
- Case-sensitive/insensitive modes

### GitAnalyzer

**Responsibilities:**
- Analyze git history for context
- Get file modification history
- Extract commit diffs
- Find related commits
- Learn from past reviews

**Key Features:**
- Uses GitPython for robust git operations
- Extracts review comments from commit messages
- Traces when helper functions were created
- Identifies recent modifications

### RuleLearner

**Responsibilities:**
- Maintain a database of review rules
- Learn patterns from commit history
- Apply rules to code
- Track rule confidence

**Key Features:**
- Default rules for common issues
- Learning from "fix", "bug" commits
- Confidence scoring
- Custom rule support
- Persistent storage

## Data Flow

### 1. Initialization

```
User creates CodeReviewAgent
    ↓
Initialize tools (Search, Git, Rules)
    ↓
Learn from repository history
    ↓
Agent ready for review
```

### 2. Review Process

```
Get diff from git
    ↓
Create initial prompt with diff
    ↓
┌─────────────────────────┐
│   AGENTIC LOOP START    │
└─────────────────────────┘
    ↓
Send to Claude with tools
    ↓
Claude analyzes and uses tools ─────┐
    ↓                               │
Execute tool (search, read, etc.)   │
    ↓                               │
Return results to Claude ───────────┘
    ↓
Claude synthesizes findings
    ↓
Apply rule-based checks
    ↓
Return CodeReviewResult
```

### 3. Tool Execution Flow

```
Agent: "I need to search for similar patterns"
    ↓
Tool Use: search_codebase(pattern="calculate_*")
    ↓
CodebaseSearch.search() executes
    ↓
Returns: List of matches with file:line info
    ↓
Agent: "Now let me read one of those files"
    ↓
Tool Use: read_file(file_path="utils.py")
    ↓
CodebaseSearch.read_file() executes
    ↓
Returns: File contents
    ↓
Agent: "I see a bug in this pattern..."
```

## Key Design Decisions

### Why Agentic vs Sequential?

**Traditional Approach:**
```
1. Parse diff
2. Run static analysis
3. Check rules
4. Return findings
```

**Agentic Approach:**
```
1. Parse diff
2. Agent decides: "I should check if this function is used elsewhere"
3. Agent uses search tool
4. Agent decides: "Let me check git history for this file"
5. Agent uses git tool
6. Agent decides: "I found an inconsistency"
7. Agent continues investigating...
```

Benefits:
- More thorough investigation
- Context-aware analysis
- Discovers issues that rules can't catch
- Adapts to different code patterns

### Why Multiple Tools?

Each tool serves a specific purpose:
- **Search**: Fast pattern matching across codebase
- **Git**: Historical context and intent
- **Rules**: Quick detection of known patterns

Combined, they give the agent complete context.

### Why Learn from History?

Git commit messages contain valuable information:
- "Fix SQL injection in login" → Learn SQL injection patterns
- "Remove hardcoded credentials" → Learn credential patterns
- "Address race condition in cache" → Learn concurrency issues

This allows the agent to learn team-specific patterns.

## Model Selection

Uses **Claude Opus 4.5** (same as Greptile):
- Best coding model for bug detection
- Strong reasoning for autonomous investigation
- Large context window for codebase analysis
- Excellent tool use capabilities

## Caching Strategy

Leverages Claude's prompt caching:
- System prompt is cached
- Tool definitions are cached
- Repository context can be cached
- Achieves high cache hit rates (target: 90% like Greptile)

## Performance Optimizations

1. **Limit result sizes**: Tools return limited results to avoid token bloat
2. **Smart chunking**: Large files are read in chunks
3. **Early termination**: Agent can stop when confident
4. **Parallel potential**: Could run multiple agents for large PRs

## Extensibility

### Adding New Tools

```python
# Define tool
tools = [
    {
        "name": "check_dependencies",
        "description": "Check package dependencies",
        "input_schema": {...}
    }
]

# Implement execution
def _execute_tool(self, name, input):
    if name == "check_dependencies":
        return self._check_deps(input)
```

### Adding New Rules

```python
rule_learner.add_custom_rule(
    ReviewRule(
        id="custom",
        pattern=r"pattern",
        message="message",
        severity=Severity.WARNING
    )
)
```

### Custom Learning

```python
# Learn from custom sources
rule_learner.learn_from_commits(commit_messages)
rule_learner.learn_from_reviews(pr_comments)
```

## Testing Strategy

### Unit Tests
- Test each tool independently
- Mock external dependencies (git, file system)
- Test edge cases and error handling

### Integration Tests
- Test full agent with real repositories
- Test agentic loop behavior
- Verify findings are correct

### Performance Tests
- Measure cache hit rates
- Measure tokens used per review
- Measure review time

## Future Enhancements

Potential improvements:
1. **Business integrations**: Jira, Linear, Notion (like Greptile)
2. **Multi-file reasoning**: Better understanding of cross-file impacts
3. **Fix suggestions**: Auto-generate code fixes
4. **Team learning**: Learn from team's review comments
5. **Language-specific rules**: Better rules per language
6. **Parallel agents**: Run multiple agents for large changes

## Comparison to Greptile

| Aspect | This Implementation | Greptile v3 |
|--------|-------------------|-------------|
| Architecture | Agentic loop | Agentic loop |
| Model | Claude Opus 4.5 | Claude Opus 4.5 |
| Tools | 5 core tools | Similar + business integrations |
| Learning | Git history | Git + PR comments |
| Scale | Single repo | Enterprise scale |
| Caching | Yes (via SDK) | 90% hit rate |
| Cost | Open source | Commercial |

## References

- [Greptile v3 Blog Post](https://www.greptile.com/blog/greptile-v3-agentic-code-review)
- [Greptile on Claude.com](https://claude.com/customers/greptile)
- Anthropic Claude Agent SDK Documentation
