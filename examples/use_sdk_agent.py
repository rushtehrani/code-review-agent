#!/usr/bin/env python3
"""
Example: Using the SDK-based Code Reviewer

This shows how to use the completely rewritten SDK agent.
"""

import asyncio
import os
from code_reviewer import SDKCodeReviewer, review_code


async def example_basic_review():
    """Example 1: Basic code review using SDK"""
    print("=" * 70)
    print("Example 1: Basic SDK Code Review")
    print("=" * 70)

    # Quick review using convenience function
    result = await review_code(
        repo_path=".",
        base_branch="main",
    )

    print(f"\n✅ Review complete!")
    print(f"Found {len(result.findings)} issues")
    print(f"Reviewed {len(result.files_reviewed)} files")
    print(f"Investigation steps: {len(result.investigation_steps)}")

    # Show findings
    if result.findings:
        print("\n🔍 Findings:")
        for finding in result.findings[:5]:  # Show first 5
            print(f"\n[{finding.severity.value.upper()}] {finding.file}:{finding.line}")
            print(f"  {finding.message}")
            if finding.suggestion:
                print(f"  💡 Suggestion: {finding.suggestion}")


async def example_detailed_review():
    """Example 2: Detailed review with SDK agent"""
    print("\n" + "=" * 70)
    print("Example 2: Detailed SDK Agent")
    print("=" * 70)

    # Create SDK reviewer
    reviewer = SDKCodeReviewer(
        repo_path=".",
        model="claude-opus-4-5-20251101"
    )

    print("\nStarting agentic review...")
    print("Claude will autonomously:")
    print("  - Search for similar code")
    print("  - Read related files")
    print("  - Check git history")
    print("  - Follow function calls")
    print("  - Apply learned rules")

    # Review changes
    result = await reviewer.review_changes(
        base_branch="main",
        stream=True
    )

    print(f"\n✅ Autonomous review complete!")

    # Group findings by severity
    errors = [f for f in result.findings if f.severity.value == "error"]
    warnings = [f for f in result.findings if f.severity.value == "warning"]
    info = [f for f in result.findings if f.severity.value == "info"]

    print(f"\n📊 Summary:")
    print(f"  ❌ Errors: {len(errors)}")
    print(f"  ⚠️  Warnings: {len(warnings)}")
    print(f"  ℹ️  Info: {len(info)}")

    # Show investigation
    if result.investigation_steps:
        print(f"\n🔬 Agent Investigation:")
        for step in result.investigation_steps[:5]:
            print(f"  • {step}")


async def example_specific_files():
    """Example 3: Review specific files"""
    print("\n" + "=" * 70)
    print("Example 3: Review Specific Files")
    print("=" * 70)

    result = await review_code(
        repo_path=".",
        base_branch="main",
        files=["code_reviewer/sdk_agent.py", "code_reviewer/agent_sdk.py"]
    )

    print(f"\nReviewed: {', '.join(result.files_reviewed)}")
    print(f"Found: {len(result.findings)} issues")


async def example_interactive_session():
    """Example 4: Interactive review session"""
    print("\n" + "=" * 70)
    print("Example 4: Interactive SDK Session")
    print("=" * 70)

    reviewer = SDKCodeReviewer(repo_path=".")

    print("\nStarting interactive session...")
    print("(This would allow back-and-forth conversation)")

    # Note: Interactive session requires async iteration
    # Skipping for this example as it needs user input
    print("\nInteractive mode available via reviewer.interactive_review()")


async def main():
    """Run all examples"""

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY not set")
        print("Set it to run full SDK reviews with Claude")
        print("\nRunning limited examples...")
        print("\nTo use full SDK features:")
        print("  export ANTHROPIC_API_KEY='your-key'")
        print("  python examples/use_sdk_agent.py")
        return

    try:
        # Run examples
        await example_basic_review()
        await example_detailed_review()
        await example_specific_files()
        await example_interactive_session()

        print("\n" + "=" * 70)
        print("✅ All examples complete!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. ANTHROPIC_API_KEY set")
        print("  2. claude-agent-sdk installed")
        print("  3. A git repository with changes")


if __name__ == "__main__":
    asyncio.run(main())
