"""
Agentic Code Reviewer - Built with Claude Agent SDK

An agentic code reviewer inspired by Greptile v3 that uses Claude
to autonomously review code with full codebase context.

Three modes of operation:
1. SDK Agent (Recommended): Full SDK integration with query() and tools
2. MCP Server: Use with Claude Code via MCP protocol
3. Direct Mode: Use the CodeReviewAgent class programmatically (legacy)
"""

from code_reviewer.agent import CodeReviewAgent
from code_reviewer.models import CodeReviewResult, ReviewFinding

# SDK mode - import SDK agent and MCP server
try:
    from code_reviewer.sdk_agent import SDKCodeReviewer, review_code
    from code_reviewer.agent_sdk import server as mcp_server

    __all__ = [
        "SDKCodeReviewer",  # Full SDK agent
        "review_code",  # Convenience function
        "mcp_server",  # MCP server for Claude Code
        "CodeReviewAgent",  # Legacy direct API
        "CodeReviewResult",
        "ReviewFinding",
    ]
except ImportError:
    # SDK not available, only direct mode
    __all__ = ["CodeReviewAgent", "CodeReviewResult", "ReviewFinding"]

__version__ = "2.0.0"  # Major version bump for SDK rewrite
