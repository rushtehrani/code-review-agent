#!/usr/bin/env python3
"""
Code Reviewer MCP Server

Run this as an MCP server to provide code review tools to Claude Code.

Usage:
    python code_reviewer_mcp.py
"""

from code_reviewer.mcp_tools import server

if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run())
