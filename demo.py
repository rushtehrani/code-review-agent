#!/usr/bin/env python3
"""
Demo script to show the agentic code reviewer in action

This demonstrates the code reviewer without requiring an actual API key
by showing how it would work with the tools.
"""

import sys
from code_reviewer.tools.codebase_search import CodebaseSearch
from code_reviewer.tools.git_analyzer import GitAnalyzer
from code_reviewer.tools.rule_learner import RuleLearner


def demo_codebase_search():
    """Demonstrate codebase search capabilities"""
    print("=" * 70)
    print("🔍 DEMO: Codebase Search Tool")
    print("=" * 70)

    search = CodebaseSearch(".")

    # Search for class definitions
    print("\nSearching for class definitions...")
    results = search.search(r"class \w+", file_pattern="*.py")
    print(f"Found {len(results)} files with class definitions")

    for result in results[:3]:
        print(f"\n  📄 {result.file}")
        for match in result.matches[:2]:
            print(f"    Line {match.line}: {match.content.strip()}")

    # Find Python files
    print("\n\nFinding Python files...")
    files = search.find_files("*.py")
    print(f"Found {len(files)} Python files")
    for f in files[:5]:
        print(f"  • {f}")


def demo_git_analyzer():
    """Demonstrate git analysis capabilities"""
    print("\n" + "=" * 70)
    print("📚 DEMO: Git History Analyzer")
    print("=" * 70)

    try:
        git = GitAnalyzer(".")

        # Get current branch
        branch = git.get_current_branch()
        print(f"\nCurrent branch: {branch}")

        # Get recent commits
        print("\nRecent commits:")
        history = git.get_file_history("code_reviewer/agent.py", max_commits=3)
        for commit in history:
            print(f"  • {commit.hash[:8]} - {commit.author}")
            print(f"    {commit.message[:60]}")

    except Exception as e:
        print(f"\nNote: Git operations require a git repository: {e}")


def demo_rule_learner():
    """Demonstrate rule learning and application"""
    print("\n" + "=" * 70)
    print("🎓 DEMO: Rule Learner")
    print("=" * 70)

    learner = RuleLearner()

    print(f"\nLoaded {len(learner.rules)} default rules")
    print("\nSample rules:")
    for rule in learner.rules[:5]:
        print(f"  • [{rule.id}] {rule.message[:50]}...")

    # Test code with issues
    test_code = """
def risky_function(user_input):
    # Security issues below
    password = "admin123"
    query = f"SELECT * FROM users WHERE id = {user_input}"

    try:
        execute(query)
    except:
        print("Error occurred")
    """

    print("\n\nApplying rules to test code:")
    violations = learner.apply_rules(test_code, "test.py")

    print(f"Found {len(violations)} violations:")
    for v in violations:
        severity_emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}
        emoji = severity_emoji.get(v["severity"], "•")
        print(f"  {emoji} Line {v['line']}: {v['message'][:60]}")


def demo_learning():
    """Demonstrate learning from commit messages"""
    print("\n" + "=" * 70)
    print("🧠 DEMO: Learning from Commits")
    print("=" * 70)

    learner = RuleLearner()
    initial_count = len(learner.rules)

    # Simulate learning from commit messages
    commit_messages = [
        "Fix SQL injection vulnerability in user authentication",
        "Patch XSS issue in comment rendering",
        "Fix race condition in payment processing",
    ]

    print("\nLearning from commit messages:")
    for msg in commit_messages:
        print(f"  • {msg}")

    learner.learn_from_commits(commit_messages)

    new_count = len(learner.rules)
    print(f"\n✅ Learned {new_count - initial_count} new patterns")
    print("\nNew rules:")
    for rule in learner.rules[initial_count:]:
        print(f"  • [{rule.id}] Confidence: {rule.confidence:.1f}")


def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("   AGENTIC CODE REVIEWER - DEMONSTRATION")
    print("   Built with Claude Agent SDK (Python)")
    print("=" * 70)
    print("\nThis demo shows the tools available to the AI agent.")
    print("The agent autonomously decides which tools to use during review.\n")

    try:
        demo_codebase_search()
        demo_git_analyzer()
        demo_rule_learner()
        demo_learning()

        print("\n" + "=" * 70)
        print("✅ Demo Complete!")
        print("=" * 70)
        print("\nTo run a full code review with Claude:")
        print("  1. Set ANTHROPIC_API_KEY environment variable")
        print("  2. Run: python examples/example_usage.py")
        print("\nTo run tests:")
        print("  pytest tests/")
        print("\n" + "=" * 70 + "\n")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
