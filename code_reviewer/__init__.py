"""
Agentic Code Reviewer - Built with Claude Agent SDK

An agentic code reviewer inspired by Greptile v3 that uses Claude
to autonomously review code with full codebase context.

Two modes of operation:
1. SDK Mode (Recommended): Use with Claude Code via MCP server
2. Direct Mode: Use the CodeReviewAgent class programmatically
"""

from code_reviewer.agent import CodeReviewAgent
from code_reviewer.models import CodeReviewResult, ReviewFinding

# SDK mode - import the MCP server
try:
    from code_reviewer.agent_sdk import server as mcp_server
    __all__ = ["CodeReviewAgent", "CodeReviewResult", "ReviewFinding", "mcp_server"]
except ImportError:
    # SDK not available, only direct mode
    __all__ = ["CodeReviewAgent", "CodeReviewResult", "ReviewFinding"]

__version__ = "1.0.0"
