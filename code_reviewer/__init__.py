"""
Agentic Code Reviewer - Built with Claude Agent SDK

An agentic code reviewer inspired by Greptile v3 that uses Claude
to autonomously review code with full codebase context.

Two modes of operation:
1. SDK Agent: Full SDK integration with query() and ClaudeSDKClient
2. MCP Server: Use with Claude Code via MCP protocol
"""

from code_reviewer.agent import CodeReviewAgent, review_code
from code_reviewer.mcp_tools import server as mcp_server
from code_reviewer.models import CodeReviewResult, ReviewFinding

__all__ = [
    "CodeReviewAgent",  # Main SDK agent
    "review_code",  # Convenience function
    "mcp_server",  # MCP server for Claude Code
    "CodeReviewResult",  # Result model
    "ReviewFinding",  # Finding model
]

__version__ = "0.1.0"
