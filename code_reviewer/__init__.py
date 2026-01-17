"""
Agentic Code Reviewer - Built with Claude Agent SDK

An agentic code reviewer inspired by Greptile v3 that uses Claude
to autonomously review code with full codebase context.
"""

from code_reviewer.agent import CodeReviewAgent
from code_reviewer.models import CodeReviewResult, ReviewFinding

__version__ = "1.0.0"
__all__ = ["CodeReviewAgent", "CodeReviewResult", "ReviewFinding"]
