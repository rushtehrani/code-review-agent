"""Tests for Claude Agent SDK implementation"""

import pytest


class TestAgentSDK:
    def test_sdk_module_imports(self):
        """Test that SDK module can be imported"""
        from code_reviewer import mcp_tools

        assert mcp_tools is not None

    def test_tools_are_defined(self):
        """Test that all tools are defined"""
        from code_reviewer import mcp_tools

        # Check that all tool variables exist (they are SdkMcpTool objects)
        assert hasattr(mcp_tools, 'search_codebase_tool')
        assert hasattr(mcp_tools, 'read_file_tool')
        assert hasattr(mcp_tools, 'get_file_history_tool')
        assert hasattr(mcp_tools, 'find_function_calls_tool')
        assert hasattr(mcp_tools, 'get_blame_tool')
        assert hasattr(mcp_tools, 'apply_rules_tool')
        assert hasattr(mcp_tools, 'get_diff_tool')

    def test_server_is_created(self):
        """Test that MCP server is created"""
        from code_reviewer.mcp_tools import server

        assert server is not None
        # Server is a dict with type, name, and instance
        assert isinstance(server, dict)
        assert 'name' in server
        assert server['name'] == 'code-reviewer'

    def test_tools_have_correct_structure(self):
        """Test that tools have the expected structure"""
        from code_reviewer.mcp_tools import search_codebase_tool
        from claude_agent_sdk import SdkMcpTool

        # Tools are wrapped in SdkMcpTool
        assert isinstance(search_codebase_tool, SdkMcpTool)

    def test_codebase_search_initialization(self):
        """Test that codebase search is initialized"""
        from code_reviewer.mcp_tools import search

        assert search is not None
        assert hasattr(search, 'search')
        assert hasattr(search, 'read_file')

    def test_rule_learner_initialization(self):
        """Test that rule learner is initialized"""
        from code_reviewer.mcp_tools import rule_learner

        assert rule_learner is not None
        assert hasattr(rule_learner, 'apply_rules')
        assert hasattr(rule_learner, 'rules')
        assert len(rule_learner.rules) > 0  # Should have default rules

    def test_git_analyzer_initialization(self):
        """Test that git analyzer handles non-git repos gracefully"""
        from code_reviewer.mcp_tools import git

        # In non-git directory, git should be None
        # In git directory, git should be GitAnalyzer
        assert git is None or hasattr(git, 'get_file_history')

    def test_mcp_server_from_init(self):
        """Test that MCP server can be imported from package"""
        try:
            from code_reviewer import mcp_server
            assert mcp_server is not None
        except ImportError:
            pytest.skip("SDK not fully initialized")

    def test_sdk_tool_count(self):
        """Test that we have 7 tools defined"""
        from code_reviewer import mcp_tools

        tool_names = [
            'search_codebase_tool',
            'read_file_tool',
            'get_file_history_tool',
            'find_function_calls_tool',
            'get_blame_tool',
            'apply_rules_tool',
            'get_diff_tool',
        ]

        for tool_name in tool_names:
            assert hasattr(mcp_tools, tool_name), f"{tool_name} not defined"
