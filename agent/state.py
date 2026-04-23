from typing import Any, Dict, List, Optional, TypedDict


class ResearchState(TypedDict):
    """Shared state for the multi-agent research pipeline."""

    topic: str
    search_queries: List[str]
    search_results: List[Dict[str, Any]]
    draft_sections: List[Dict[str, Any]]
    critic_feedback: Optional[str]
    final_report: Optional[str]
    sources: List[Dict[str, Any]]
    status: str
    iteration_count: int
