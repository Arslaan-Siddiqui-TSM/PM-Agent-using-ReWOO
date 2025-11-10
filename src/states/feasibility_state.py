"""
Feasibility State

State management for feasibility assessment graph.
"""

from __future__ import annotations
from typing import Optional, List, Dict
from pydantic import BaseModel


class FeasibilityState(BaseModel):
    """State for feasibility assessment graph execution."""
    
    # Inputs
    session_id: str
    md_file_paths: Optional[List[str]] = None
    development_context: Optional[Dict[str, str]] = None
    
    # Outputs
    thinking_summary: str = ""
    feasibility_report: str = ""
    
    class Config:
        arbitrary_types_allowed = True
