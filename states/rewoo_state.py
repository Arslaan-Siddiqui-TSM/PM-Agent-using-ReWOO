from typing import List, Optional
from pydantic import BaseModel, Field


class ReWOO(BaseModel):
    plan_string: Optional[str] = Field(None, description="The plan to achieve the task")
    steps: List = Field(description="The steps to follow in the plan", default_factory=list)
    results: dict = Field(description="The results of each step", default_factory=dict)
    result: Optional[str] = Field(None, description="The final result of the task")
    document_context: Optional[str] = Field(None, description="Intelligent document analysis context")

    def __getitem__(self, item):
        return getattr(self, item)