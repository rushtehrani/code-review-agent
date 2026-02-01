"""Integration tests for the code review agent"""

import tempfile
import shutil
import os
from pathlib import Path
import pytest
import git
from code_reviewer.agent import CodeReviewAgent


class TestIntegration:
    @pytest.fixture
    def sample_repo(self):
        """Create a sample repository with issues"""
        temp_dir = tempfile.mkdtemp()
        repo = git.Repo.init(temp_dir)

        # Configure git
        with repo.config_writer() as config:
            config.set_value("user", "name", "Test User")
            config.set_value("user", "email", "test@example.com")

        # Create main branch with initial code
        main_file = Path(temp_dir) / "main.py"
        main_file.write_text("""
def calculate_price(items):
    total = 0
    for item in items:
        total += item.price
    return total

def get_user(user_id):
    # SQL query
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return execute_query(query)
""")

        repo.index.add(["main.py"])
        repo.index.commit("Initial commit")

        # Create a feature branch with changes (including issues)
        feature_branch = repo.create_head("feature/new-code")
        feature_branch.checkout()

        # Add code with issues
        main_file.write_text("""
def calculate_price(items):
    total = 0
    for item in items:
        total += item.price
    return total

def get_user(user_id):
    # SQL query - VULNERABLE TO SQL INJECTION
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return execute_query(query)

def process_payment(amount):
    try:
        charge_card(amount)
    except:  # Bare except - bad practice
        print("Payment failed")  # Using print instead of logging
        pass

    # Hard-coded API key - security issue
    api_key = "sk-1234567890abcdef"
    return api_key

password = "admin123"  # Hard-coded password
""")

        repo.index.add(["main.py"])
        repo.index.commit("Add payment processing")

        # Return to main branch for comparison
        repo.heads.master.checkout()

        yield temp_dir, "feature/new-code"

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_review_with_issues(self, sample_repo):
        """Test reviewing code with security and quality issues"""
        repo_path, feature_branch = sample_repo

        # Switch to feature branch
        repo = git.Repo(repo_path)
        repo.git.checkout(feature_branch)

        # Create agent and review
        agent = CodeReviewAgent(repo_path)
        result = await agent.review_changes(base_branch="master")

        # Should find multiple issues
        assert len(result.findings) > 0

        # Check for specific issue types
        finding_messages = [f.message.lower() for f in result.findings]

        # Should detect security issues
        has_security_issue = any(
            "password" in msg or "api" in msg or "sql" in msg
            for msg in finding_messages
        )
        assert has_security_issue, "Should detect security issues"

        # Should detect code quality issues
        has_quality_issue = any(
            "except" in msg or "print" in msg
            for msg in finding_messages
        )
        assert has_quality_issue, "Should detect code quality issues"

        # Should have investigation steps
        assert len(result.investigation_steps) > 0

        # Should have reviewed files
        assert len(result.files_reviewed) > 0
        assert "main.py" in result.files_reviewed

    @pytest.mark.asyncio
    async def test_review_without_api_key(self, sample_repo):
        """Test that agent handles missing API key gracefully"""
        repo_path, _ = sample_repo

        # Clear API key
        old_key = os.environ.get("ANTHROPIC_API_KEY")
        if old_key:
            del os.environ["ANTHROPIC_API_KEY"]

        try:
            # SDK agent can be created without API key, but review_changes will fail
            agent = CodeReviewAgent(repo_path)
            # The actual API call will fail when invoked
            # This test just verifies the agent can be created
            assert agent is not None
        finally:
            # Restore key
            if old_key:
                os.environ["ANTHROPIC_API_KEY"] = old_key

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_review_clean_code(self, sample_repo):
        """Test reviewing clean code with no changes"""
        repo_path, _ = sample_repo

        # Stay on main branch (no changes)
        agent = CodeReviewAgent(repo_path)
        result = await agent.review_changes(base_branch="master")

        # Should have no changes
        assert "No changes detected" in result.investigation_steps[0]
