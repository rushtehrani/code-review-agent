"""
Data models for the code review agent
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity levels for review findings"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ReviewFinding(BaseModel):
    """A single finding from code review"""

    file: str = Field(description="File path where the issue was found")
    line: int = Field(description="Line number of the issue")
    severity: Severity = Field(description="Severity of the finding")
    message: str = Field(description="Description of the issue")
    suggestion: Optional[str] = Field(default=None, description="Suggested fix")
    related_code: list[str] = Field(
        default_factory=list, description="Related code snippets from codebase"
    )


class CodeReviewResult(BaseModel):
    """Result of a code review"""

    findings: list[ReviewFinding] = Field(
        default_factory=list, description="List of findings from the review"
    )
    investigation_steps: list[str] = Field(
        default_factory=list, description="Steps taken during investigation"
    )
    files_reviewed: list[str] = Field(
        default_factory=list, description="Files that were reviewed"
    )
    cache_hit_rate: Optional[float] = Field(
        default=None, description="Cache hit rate for this review"
    )


class SearchMatch(BaseModel):
    """A match from codebase search"""

    line: int
    content: str
    context: list[str] = Field(default_factory=list)


class CodebaseSearchResult(BaseModel):
    """Result from searching the codebase"""

    file: str
    matches: list[SearchMatch] = Field(default_factory=list)


class GitCommit(BaseModel):
    """A git commit"""

    hash: str
    author: str
    date: str
    message: str
    diff: Optional[str] = None


class ReviewRule(BaseModel):
    """A learned review rule"""

    id: str
    pattern: str
    message: str
    severity: Severity
    learned_from: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
