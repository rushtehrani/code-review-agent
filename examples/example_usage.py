"""
Example usage of the Agentic Code Reviewer

This demonstrates how to use the code review agent to review
pull requests or local changes.
"""

import os
from code_reviewer import CodeReviewAgent

def main():
    # Set your API key (or use environment variable ANTHROPIC_API_KEY)
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Get your API key from: https://console.anthropic.com/")
        return

    # Initialize the agent with your repository path
    repo_path = "."  # Current directory
    agent = CodeReviewAgent(
        repo_path=repo_path,
        api_key=api_key,
        model="claude-opus-4-5-20251101",  # Use Opus 4.5 for best results
    )

    print("🤖 Starting agentic code review...")
    print("=" * 60)

    # Review changes compared to main branch
    result = agent.review_changes(
        base_branch="main",
        max_iterations=10,  # Allow agent to investigate thoroughly
    )

    print(f"\n📊 Review Summary")
    print(f"Files reviewed: {len(result.files_reviewed)}")
    print(f"Findings: {len(result.findings)}")
    print(f"Investigation steps: {len(result.investigation_steps)}")

    if result.findings:
        print("\n🔍 Findings:")
        print("=" * 60)

        # Group by severity
        errors = [f for f in result.findings if f.severity.value == "error"]
        warnings = [f for f in result.findings if f.severity.value == "warning"]
        info = [f for f in result.findings if f.severity.value == "info"]

        if errors:
            print(f"\n❌ ERRORS ({len(errors)}):")
            for finding in errors:
                print(f"\n  {finding.file}:{finding.line}")
                print(f"  {finding.message}")
                if finding.suggestion:
                    print(f"  💡 Suggestion: {finding.suggestion}")

        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for finding in warnings:
                print(f"\n  {finding.file}:{finding.line}")
                print(f"  {finding.message}")
                if finding.suggestion:
                    print(f"  💡 Suggestion: {finding.suggestion}")

        if info:
            print(f"\nℹ️  INFO ({len(info)}):")
            for finding in info:
                print(f"\n  {finding.file}:{finding.line}")
                print(f"  {finding.message}")
                if finding.suggestion:
                    print(f"  💡 Suggestion: {finding.suggestion}")
    else:
        print("\n✅ No issues found!")

    print("\n🔎 Investigation Process:")
    print("=" * 60)
    for step in result.investigation_steps:
        print(f"  • {step}")

    print("\n" + "=" * 60)
    print("Review complete!")


if __name__ == "__main__":
    main()
