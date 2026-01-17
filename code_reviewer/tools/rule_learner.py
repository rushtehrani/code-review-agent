"""
Rule learner - learns review patterns from past reviews

Inspired by Greptile's ability to learn team best practices and
coding standards by reading other engineers' comments.
"""

import json
import re
from pathlib import Path
from typing import Optional
from code_reviewer.models import ReviewRule, Severity


class RuleLearner:
    """Tool for learning and applying code review rules"""

    def __init__(self, rules_file: Optional[str] = None):
        self.rules_file = Path(rules_file) if rules_file else None
        self.rules: list[ReviewRule] = []

        if self.rules_file and self.rules_file.exists():
            self.load_rules()
        else:
            self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        """Initialize with common code review rules"""
        self.rules = [
            ReviewRule(
                id="no-print-statements",
                pattern=r"\bprint\s*\(",
                message="Avoid using print statements in production code. Use proper logging instead.",
                severity=Severity.WARNING,
            ),
            ReviewRule(
                id="no-todo-comments",
                pattern=r"#\s*TODO",
                message="TODO comments should be tracked in issue tracker instead of code.",
                severity=Severity.INFO,
            ),
            ReviewRule(
                id="no-bare-except",
                pattern=r"except\s*:",
                message="Avoid bare except clauses. Catch specific exceptions instead.",
                severity=Severity.ERROR,
            ),
            ReviewRule(
                id="no-eval",
                pattern=r"\beval\s*\(",
                message="Using eval() is dangerous and should be avoided.",
                severity=Severity.ERROR,
            ),
            ReviewRule(
                id="password-in-code",
                pattern=r"['\"]?password['\"]?\s*[=:]\s*['\"]",
                message="Hard-coded passwords detected. Use environment variables or secret management.",
                severity=Severity.ERROR,
            ),
            ReviewRule(
                id="api-key-in-code",
                pattern=r"api[_-]?key\s*=\s*['\"]",
                message="Hard-coded API keys detected. Use environment variables.",
                severity=Severity.ERROR,
            ),
            ReviewRule(
                id="sql-injection-risk",
                pattern=r"execute\s*\(\s*['\"].*%s",
                message="Potential SQL injection vulnerability. Use parameterized queries.",
                severity=Severity.ERROR,
            ),
            ReviewRule(
                id="long-function",
                pattern=r"def\s+\w+.*:\s*\n(?:\s+.*\n){50,}",
                message="Function is too long (>50 lines). Consider breaking it into smaller functions.",
                severity=Severity.WARNING,
            ),
            ReviewRule(
                id="missing-docstring",
                pattern=r"def\s+\w+.*:\s*\n\s+(?!\"\"\")",
                message="Public functions should have docstrings.",
                severity=Severity.INFO,
            ),
            ReviewRule(
                id="unused-import",
                pattern=r"^import\s+\w+$",
                message="Verify all imports are used.",
                severity=Severity.INFO,
            ),
        ]

    def learn_from_commits(self, commit_messages: list[str]) -> None:
        """
        Learn patterns from commit messages

        Args:
            commit_messages: List of commit messages to learn from
        """
        # Extract patterns from "fix", "bug", "issue" type commits
        for message in commit_messages:
            message_lower = message.lower()

            # Look for common patterns
            if "sql injection" in message_lower:
                self._add_or_update_rule(
                    "learned-sql-injection",
                    r"\.execute\s*\(",
                    "Potential SQL injection. Use parameterized queries.",
                    Severity.ERROR,
                    message,
                )
            elif "xss" in message_lower or "cross-site scripting" in message_lower:
                self._add_or_update_rule(
                    "learned-xss",
                    r"\.innerHTML\s*=",
                    "Potential XSS vulnerability. Use textContent or sanitize input.",
                    Severity.ERROR,
                    message,
                )
            elif "race condition" in message_lower:
                self._add_or_update_rule(
                    "learned-race-condition",
                    r"threading",
                    "Potential race condition. Ensure proper synchronization.",
                    Severity.WARNING,
                    message,
                )
            elif "memory leak" in message_lower:
                self._add_or_update_rule(
                    "learned-memory-leak",
                    r"while\s+True:",
                    "Infinite loop detected. Ensure proper cleanup and exit conditions.",
                    Severity.WARNING,
                    message,
                )

    def _add_or_update_rule(
        self,
        rule_id: str,
        pattern: str,
        message: str,
        severity: Severity,
        learned_from: str,
    ) -> None:
        """Add a new rule or update confidence of existing rule"""
        for rule in self.rules:
            if rule.id == rule_id:
                # Increase confidence if we see the pattern again
                rule.confidence = min(1.0, rule.confidence + 0.1)
                return

        # Add new rule
        self.rules.append(
            ReviewRule(
                id=rule_id,
                pattern=pattern,
                message=message,
                severity=severity,
                learned_from=learned_from,
                confidence=0.7,  # Start with moderate confidence
            )
        )

    def apply_rules(self, file_content: str, file_path: str) -> list[dict]:
        """
        Apply all rules to file content

        Args:
            file_content: Content of the file to check
            file_path: Path to the file (for context)

        Returns:
            List of rule violations found
        """
        violations = []

        for rule in self.rules:
            try:
                matches = re.finditer(rule.pattern, file_content, re.MULTILINE)

                for match in matches:
                    # Find line number
                    line_num = file_content[: match.start()].count("\n") + 1

                    violations.append(
                        {
                            "file": file_path,
                            "line": line_num,
                            "rule_id": rule.id,
                            "severity": rule.severity.value,
                            "message": rule.message,
                            "confidence": rule.confidence,
                        }
                    )
            except re.error:
                # Skip invalid regex patterns
                continue

        return violations

    def get_rule_by_id(self, rule_id: str) -> Optional[ReviewRule]:
        """Get a specific rule by ID"""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None

    def add_custom_rule(self, rule: ReviewRule) -> None:
        """Add a custom rule"""
        self.rules.append(rule)

    def save_rules(self) -> None:
        """Save rules to file"""
        if not self.rules_file:
            return

        rules_data = [rule.model_dump() for rule in self.rules]

        self.rules_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.rules_file, "w") as f:
            json.dump(rules_data, f, indent=2)

    def load_rules(self) -> None:
        """Load rules from file"""
        if not self.rules_file or not self.rules_file.exists():
            return

        try:
            with open(self.rules_file, "r") as f:
                rules_data = json.load(f)

            self.rules = [ReviewRule(**rule) for rule in rules_data]
        except Exception:
            self._initialize_default_rules()

    def get_rules_for_language(self, language: str) -> list[ReviewRule]:
        """
        Get rules specific to a programming language

        Args:
            language: Programming language (e.g., 'python', 'javascript')

        Returns:
            List of applicable rules
        """
        # For now, return all rules
        # In production, you'd filter by language-specific rules
        return self.rules
