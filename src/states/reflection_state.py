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

    # ═══════════════════════════════════════════════════════════
    # CORE INPUT FIELDS
    # ═══════════════════════════════════════════════════════════
    task: Optional[str] = Field(
        default=None, description="Original user task or problem statement"
    )
    document_context: Optional[str] = Field(
        default=None, description="Aggregated context derived from documents"
    )
    feasibility_file_path: Optional[str] = Field(
        default=None, description="Path to feasibility assessment notes"
    )
    
    # ═══════════════════════════════════════════════════════════
    # ITERATION CONTROL
    # ═══════════════════════════════════════════════════════════
    max_iterations: int = Field(
        default=3,
        description="Maximum number of draft→reflect→revise cycles before stopping",
    )
    iterations: List[ReflectionIteration] = Field(
        default_factory=list,
        description="History of generated drafts and critiques",
    )
    
    # ═══════════════════════════════════════════════════════════
    # ENHANCED TRACKING (for iteration awareness)
    # ═══════════════════════════════════════════════════════════
    quality_scores: List[float] = Field(
        default_factory=list,
        description="Quality scores (0-10) for each iteration to track improvement trajectory",
    )
    improvement_areas: List[str] = Field(
        default_factory=list,
        description="Focus areas identified for each iteration to avoid redundant critiques",
    )
    iteration_summaries: List[str] = Field(
        default_factory=list,
        description="High-level summaries of what was addressed in each iteration",
    )
    addressed_issues: List[str] = Field(
        default_factory=list,
        description="Issues that have been resolved in previous iterations",
    )
    
    # ═══════════════════════════════════════════════════════════
    # OUTPUT
    # ═══════════════════════════════════════════════════════════
    final_plan: Optional[str] = Field(
        default=None, description="Accepted project plan Markdown"
    )

    def __getitem__(self, item: str):
        """Allow dict-style access for LangGraph compatibility"""
        return getattr(self, item)
    
    # ═══════════════════════════════════════════════════════════
    # CONVENIENCE PROPERTIES (derived from iterations)
    # ═══════════════════════════════════════════════════════════
    @property
    def current_draft(self) -> Optional[str]:
        """Get the most recent draft from iteration history"""
        return self.iterations[-1].draft if self.iterations else None
    
    @property
    def current_critique(self) -> Optional[str]:
        """Get the most recent critique from iteration history"""
        return self.iterations[-1].critique if self.iterations else None
    
    @property
    def iteration_count(self) -> int:
        """Current iteration number (0-indexed)"""
        return len(self.iterations)
