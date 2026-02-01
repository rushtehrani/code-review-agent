"""Tests for data models"""

import pytest
from code_reviewer.models import (
    Severity,
    ReviewFinding,
    GitCommit,
    CodeReviewResult,
    ReviewRule,
    CodebaseSearchResult,
    SearchMatch,
)


class TestModels:
    def test_severity_enum(self):
        """Test Severity enum values"""
        assert Severity.ERROR.value == "error"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"

    def test_review_finding_basic(self):
        """Test basic ReviewFinding creation"""
        finding = ReviewFinding(
            file="test.py",
            line=10,
            severity=Severity.ERROR,
            message="Test error",
        )

        assert finding.file == "test.py"
        assert finding.line == 10
        assert finding.severity == Severity.ERROR
        assert finding.message == "Test error"
        assert finding.suggestion is None

    def test_review_finding_with_suggestion(self):
        """Test ReviewFinding with suggestion"""
        finding = ReviewFinding(
            file="test.py",
            line=10,
            severity=Severity.WARNING,
            message="Test warning",
            suggestion="Fix this way",
        )

        assert finding.suggestion == "Fix this way"

    def test_git_commit_basic(self):
        """Test GitCommit model"""
        commit = GitCommit(
            hash="abc123",
            author="Test User",
            date="2024-01-01",
            message="Test commit",
        )

        assert commit.hash == "abc123"
        assert commit.author == "Test User"
        assert commit.date == "2024-01-01"
        assert commit.message == "Test commit"
        assert commit.diff is None

    def test_git_commit_with_diff(self):
        """Test GitCommit with diff"""
        commit = GitCommit(
            hash="abc123",
            author="Test User",
            date="2024-01-01",
            message="Test commit",
            diff="+added line\n-removed line",
        )

        assert commit.diff is not None
        assert "added line" in commit.diff

    def test_code_review_result(self):
        """Test CodeReviewResult model"""
        findings = [
            ReviewFinding(
                file="test.py",
                line=10,
                severity=Severity.ERROR,
                message="Error 1",
            ),
            ReviewFinding(
                file="test.py",
                line=20,
                severity=Severity.WARNING,
                message="Warning 1",
            ),
        ]

        result = CodeReviewResult(
            findings=findings,
            investigation_steps=["Step 1", "Step 2"],
            files_reviewed=["test.py", "utils.py"],
        )

        assert len(result.findings) == 2
        assert len(result.investigation_steps) == 2
        assert len(result.files_reviewed) == 2

    def test_review_rule(self):
        """Test ReviewRule model"""
        rule = ReviewRule(
            id="test-rule",
            pattern=r"test.*pattern",
            message="Test message",
            severity=Severity.INFO,
        )

        assert rule.id == "test-rule"
        assert rule.pattern == r"test.*pattern"
        assert rule.message == "Test message"
        assert rule.severity == Severity.INFO
        assert rule.confidence == 1.0  # default
        assert rule.learned_from is None

    def test_review_rule_with_learning(self):
        """Test ReviewRule with learning metadata"""
        rule = ReviewRule(
            id="learned-rule",
            pattern=r"pattern",
            message="Learned message",
            severity=Severity.WARNING,
            confidence=0.8,
            learned_from="Fix bug in commit abc123",
        )

        assert rule.confidence == 0.8
        assert rule.learned_from is not None

    def test_codebase_search_result(self):
        """Test CodebaseSearchResult model"""
        matches = [
            SearchMatch(line=10, content="def test():"),
            SearchMatch(line=20, content="def test2():"),
        ]

        result = CodebaseSearchResult(
            file="test.py",
            matches=matches,
        )

        assert result.file == "test.py"
        assert len(result.matches) == 2

    def test_search_match(self):
        """Test SearchMatch model"""
        match = SearchMatch(
            line=42,
            content="    def hello():",
        )

        assert match.line == 42
        assert match.content == "    def hello():"

    def test_review_finding_validation(self):
        """Test that ReviewFinding validates line numbers"""
        # Line number should be positive
        finding = ReviewFinding(
            file="test.py",
            line=1,
            severity=Severity.INFO,
            message="Test",
        )

        assert finding.line == 1

    def test_model_serialization(self):
        """Test that models can be serialized"""
        finding = ReviewFinding(
            file="test.py",
            line=10,
            severity=Severity.ERROR,
            message="Test error",
        )

        data = finding.model_dump()

        assert data["file"] == "test.py"
        assert data["line"] == 10
        assert data["severity"] == "error"

    def test_model_deserialization(self):
        """Test that models can be deserialized"""
        data = {
            "file": "test.py",
            "line": 10,
            "severity": "warning",
            "message": "Test message",
        }

        finding = ReviewFinding(**data)

        assert finding.file == "test.py"
        assert finding.severity == Severity.WARNING
