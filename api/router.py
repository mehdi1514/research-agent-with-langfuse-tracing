import time
import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from langfuse.langchain import CallbackHandler

from agent.research_graph import compiled_research_graph
from agent.state import ResearchState
from api.models import ResearchRequest, ResearchResponse

router = APIRouter()

# Initialize Langfuse CallbackHandler for tracing
langfuse_handler = CallbackHandler()


def _build_initial_state(request: ResearchRequest) -> ResearchState:
    return {
        "topic": request.topic,
        "search_queries": [],
        "search_results": [],
        "draft_sections": [],
        "critic_feedback": None,
        "final_report": None,
        "sources": [],
        "status": "initialized",
        "iteration_count": 0,
    }


@router.post("/research", response_model=ResearchResponse)
async def create_research(request: ResearchRequest):
    run_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    initial_state = _build_initial_state(request)
    config = {
        "configurable": {"thread_id": run_id},
        "metadata": {"run_id": run_id, "topic": request.topic},
        "callbacks": [langfuse_handler],
    }

    try:
        final_state = compiled_research_graph.invoke(initial_state, config=config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    latency = time.perf_counter() - start_time

    return ResearchResponse(
        run_id=run_id,
        status=final_state.get("status", "unknown"),
        final_report=final_state.get("final_report"),
        sources=final_state.get("sources", []),
        langfuse_trace_id=run_id,
        latency_seconds=round(latency, 3),
    )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}
