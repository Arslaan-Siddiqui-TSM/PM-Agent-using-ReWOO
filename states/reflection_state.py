from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ReflectionIteration(BaseModel):
    """A single reflection cycle containing a draft and optional critique."""

    draft: str = Field(description="Draft produced during this iteration")
    critique: Optional[str] = Field(
        default=None, description="Critique or feedback generated for the draft"
    )
    reasoning: Optional[str] = Field(
        default=None, description="Chain-of-thought style notes or rationale"
    )
    accepted: bool = Field(
        default=False,
        description="Whether this iteration's draft was accepted as final output",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the iteration was recorded",
    )


class ReflectionState(BaseModel):
    """State container for the reflection-style planning agent."""

    task: Optional[str] = Field(
        default=None, description="Original user task or problem statement"
    )
    document_context: Optional[str] = Field(
        default=None, description="Aggregated context derived from documents"
    )
    feasibility_file_path: Optional[str] = Field(
        default=None, description="Path to feasibility assessment notes"
    )
    max_iterations: int = Field(
        default=3,
        description="Maximum number of draft→reflect→revise cycles before stopping",
    )
    iterations: List[ReflectionIteration] = Field(
        default_factory=list,
        description="History of generated drafts and critiques",
    )
    current_draft: Optional[str] = Field(
        default=None, description="Draft under consideration in the current cycle"
    )
    current_critique: Optional[str] = Field(
        default=None, description="Most recent critique generated for the draft"
    )
    revision_instructions: Optional[str] = Field(
        default=None,
        description="Actionable guidance for the next draft when revisions are needed",
    )
    decision_rationale: Optional[str] = Field(
        default=None,
        description="Why the last revise step accepted or rejected the current draft",
    )
    final_plan: Optional[str] = Field(
        default=None, description="Accepted project plan Markdown"
    )

    def __getitem__(self, item: str):
        return getattr(self, item)
