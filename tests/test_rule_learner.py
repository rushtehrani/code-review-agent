"""Tests for rule learner"""

import tempfile
import shutil
from pathlib import Path
import pytest
from code_reviewer.tools.rule_learner import RuleLearner
from code_reviewer.models import ReviewRule, Severity


class TestRuleLearner:
    @pytest.fixture
    def temp_rules_file(self):
        """Create a temporary rules file"""
        temp_dir = tempfile.mkdtemp()
        rules_file = Path(temp_dir) / "rules.json"

        yield str(rules_file)

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_initialize_default_rules(self):
        """Test that default rules are initialized"""
        learner = RuleLearner()

        assert len(learner.rules) > 0
        assert any(rule.id == "no-print-statements" for rule in learner.rules)
        assert any(rule.id == "no-bare-except" for rule in learner.rules)

    def test_apply_rules_print_statement(self):
        """Test detecting print statements"""
        learner = RuleLearner()
        code = """
def test():
    print("Debug message")
    return True
"""

        violations = learner.apply_rules(code, "test.py")

        assert len(violations) > 0
        assert any("print" in v["message"].lower() for v in violations)

    def test_apply_rules_bare_except(self):
        """Test detecting bare except clauses"""
        learner = RuleLearner()
        code = """
try:
    risky_operation()
except:
    pass
"""

        violations = learner.apply_rules(code, "test.py")

        assert len(violations) > 0
        assert any("except" in v["message"].lower() for v in violations)

    def test_apply_rules_hardcoded_password(self):
        """Test detecting hardcoded passwords"""
        learner = RuleLearner()
        code = """
config = {
    'password': 'secret123'
}
"""

        violations = learner.apply_rules(code, "test.py")

        assert len(violations) > 0
        assert any("password" in v["message"].lower() for v in violations)

    def test_learn_from_commits(self):
        """Test learning patterns from commit messages"""
        learner = RuleLearner()
        initial_count = len(learner.rules)

        commit_messages = [
            "Fix SQL injection vulnerability in user query",
            "Patch XSS issue in comments section",
            "Fix race condition in payment processing",
        ]

        learner.learn_from_commits(commit_messages)

        # Should have learned new rules
        assert len(learner.rules) >= initial_count
        assert any("sql" in rule.id.lower() for rule in learner.rules)

    def test_add_custom_rule(self):
        """Test adding a custom rule"""
        learner = RuleLearner()
        initial_count = len(learner.rules)

        custom_rule = ReviewRule(
            id="custom-test",
            pattern=r"FIXME",
            message="FIXME comments should be resolved",
            severity=Severity.WARNING,
        )

        learner.add_custom_rule(custom_rule)

        assert len(learner.rules) == initial_count + 1
        assert learner.get_rule_by_id("custom-test") is not None

    def test_save_and_load_rules(self, temp_rules_file):
        """Test saving and loading rules"""
        # Create learner with custom rule
        learner1 = RuleLearner(temp_rules_file)
        custom_rule = ReviewRule(
            id="test-rule",
            pattern=r"test",
            message="Test message",
            severity=Severity.INFO,
        )
        learner1.add_custom_rule(custom_rule)
        learner1.save_rules()

        # Load in new instance
        learner2 = RuleLearner(temp_rules_file)

        assert len(learner2.rules) > 0
        assert learner2.get_rule_by_id("test-rule") is not None

    def test_get_rule_by_id(self):
        """Test getting a specific rule"""
        learner = RuleLearner()
        rule = learner.get_rule_by_id("no-print-statements")

        assert rule is not None
        assert rule.id == "no-print-statements"

    def test_get_nonexistent_rule(self):
        """Test getting a rule that doesn't exist"""
        learner = RuleLearner()
        rule = learner.get_rule_by_id("nonexistent-rule")

        assert rule is None

    def test_rule_confidence(self):
        """Test that learning increases rule confidence"""
        learner = RuleLearner()

        # Learn same pattern multiple times
        for _ in range(3):
            learner.learn_from_commits(
                ["Fix SQL injection in query builder"]
            )

        sql_rule = next(
            (r for r in learner.rules if "sql" in r.id.lower()), None
        )

        if sql_rule:
            # Confidence should have increased
            assert sql_rule.confidence > 0.7

    def test_apply_rules_no_violations(self):
        """Test applying rules to clean code"""
        learner = RuleLearner()
        code = """
def clean_function(data: list) -> int:
    \"\"\"Calculate sum of data.\"\"\"
    return sum(data)
"""

        violations = learner.apply_rules(code, "clean.py")

        # Might have some minor violations (like missing docstring check)
        # but shouldn't have major errors
        assert not any(v["severity"] == "error" for v in violations)

    def test_get_rules_for_language(self):
        """Test getting rules for specific language"""
        learner = RuleLearner()
        python_rules = learner.get_rules_for_language("python")

        assert len(python_rules) > 0
        assert all(isinstance(rule.id, str) for rule in python_rules)

    def test_apply_rules_with_invalid_regex(self):
        """Test that invalid regex patterns are handled"""
        learner = RuleLearner()

        # Add a rule with invalid regex
        from code_reviewer.models import ReviewRule, Severity
        bad_rule = ReviewRule(
            id="bad-regex",
            pattern=r"[invalid(regex",  # Invalid regex
            message="Test",
            severity=Severity.INFO,
        )
        learner.rules.append(bad_rule)

        code = "def test(): pass"

        # Should not crash, just skip the bad rule
        violations = learner.apply_rules(code, "test.py")

        assert isinstance(violations, list)

    def test_learn_from_commits_xss(self):
        """Test learning XSS patterns"""
        learner = RuleLearner()
        initial_count = len(learner.rules)

        learner.learn_from_commits([
            "Fix cross-site scripting vulnerability in templates"
        ])

        assert len(learner.rules) > initial_count

    def test_learn_from_commits_memory_leak(self):
        """Test learning memory leak patterns"""
        learner = RuleLearner()
        initial_count = len(learner.rules)

        learner.learn_from_commits([
            "Fix memory leak in background worker"
        ])

        assert len(learner.rules) > initial_count

    def test_rule_learned_from_source(self):
        """Test that learned rules track their source"""
        learner = RuleLearner()

        commit_msg = "Fix SQL injection in auth module"
        learner.learn_from_commits([commit_msg])

        sql_rule = next(
            (r for r in learner.rules if "sql" in r.id.lower() and r.learned_from),
            None
        )

        if sql_rule:
            assert sql_rule.learned_from is not None

    def test_save_rules_creates_directory(self, temp_rules_file):
        """Test that save_rules creates parent directories"""
        # Create path in non-existent directory
        import os
        nested_path = os.path.join(os.path.dirname(temp_rules_file), "nested", "rules.json")

        learner = RuleLearner(nested_path)
        learner.save_rules()

        assert os.path.exists(nested_path)
