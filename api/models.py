from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    topic: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Research topic to investigate",
    )
    max_iterations: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Maximum critic-revise iterations",
    )


class ResearchResponse(BaseModel):
    run_id: str
    status: str
    final_report: Optional[str]
    sources: List[Dict[str, str]]
    langfuse_trace_id: Optional[str]
    latency_seconds: float
