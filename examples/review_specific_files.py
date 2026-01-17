"""
Example: Review specific files

This shows how to review only specific files instead of all changes.
"""

import os
from code_reviewer import CodeReviewAgent


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return

    # Initialize agent
    agent = CodeReviewAgent(
        repo_path=".",
        api_key=api_key,
    )

    # Review only specific files
    files_to_review = [
        "code_reviewer/agent.py",
        "code_reviewer/tools/codebase_search.py",
    ]

    print(f"Reviewing files: {', '.join(files_to_review)}")

    result = agent.review_changes(
        base_branch="main",
        files=files_to_review,
    )

    # Print summary
    print(f"\nFound {len(result.findings)} issues:")
    for finding in result.findings:
        print(f"  [{finding.severity.value.upper()}] {finding.file}:{finding.line}")
        print(f"  {finding.message}\n")


if __name__ == "__main__":
    main()
