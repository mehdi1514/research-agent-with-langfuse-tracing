from fastapi import FastAPI
from api.router import router

app = FastAPI(
    title="Multi-Agent Research & Report Writer",
    description="A coordinator-driven multi-agent system using LangGraph with Tavily search, summarization, critic review, and full Langfuse observability.",
    version="0.1.0",
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "Multi-Agent Research & Report Writer API",
        "docs": "/docs",
    }
