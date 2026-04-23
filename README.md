# Multi-Agent Research & Report Writer

A coordinator-driven multi-agent system built with **LangGraph** that researches any topic via web search, synthesizes findings into structured sections, runs a quality-check critic loop, and assembles a polished Markdown report — with full **Langfuse** observability for cost, latency, and prompt versioning per agent.

---

## Architecture

```
User Topic
    │
    ▼
┌─────────────┐
│ Coordinator │ ──► Generates 2–4 targeted search queries
└──────┬──────┘
       │
       ▼
┌──────────────┐
│ Web Searcher │ ──► Calls Tavily API for real-time results
└──────┬───────┘
       │
       ▼
┌────────────┐
│ Summarizer │ ──► Synthesizes raw results into structured sections
└──────┬─────┘
       │
       ▼
┌─────────┐
│  Critic │ ──► Evaluates quality; routes to Reviser or Assembler
└────┬────┘
     │ REVISE (max 2 iterations)
     ▼
┌─────────┐
│ Reviser │ ──► Refines sections based on critic feedback
└────┬────┘
     │
     └──────────────► Critic (loop guard at 2 iterations)
     │ PASS
     ▼
┌───────────┐
│ Assembler │ ──► Compiles final Markdown report with sources
└─────┬─────┘
      │
      ▼
   Final Report
```

### Agents & Responsibilities

| Agent | Role |
|-------|------|
| **Coordinator** | Breaks the topic into targeted search queries |
| **Web Searcher** | Executes Tavily searches and collects sources |
| **Summarizer** | Synthesizes search results into structured draft sections |
| **Critic** | Reviews drafts for completeness, accuracy, and tone |
| **Reviser** | Revises sections based on critic feedback |
| **Assembler** | Compiles everything into a polished Markdown report |

---

## Tech Stack

- **Python 3.13+** with `uv`
- **LangChain** + **LangGraph** — agent orchestration with `MemorySaver` checkpointing
- **Google Gemini** — LLM via `langchain-google-genai`
- **Tavily** — real-time web search (`langchain-tavily`)
- **Langfuse** — distributed tracing, cost & latency per agent, prompt versioning
- **FastAPI** + **Uvicorn** — HTTP API wrapper

---

## Quickstart

### 1. Prerequisites

- [uv](https://docs.astral.sh/uv/) installed
- API keys for:
  - [Google AI Studio](https://aistudio.google.com/app/apikey) (`GOOGLE_API_KEY`)
  - [Tavily](https://tavily.com) (`TAVILY_API_KEY`)
  - [Langfuse](https://langfuse.com) (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`)

### 2. Configure Environment

Create or update `.env` in the project root:

```bash
GOOGLE_API_KEY=your-google-api-key
TAVILY_API_KEY=your-tavily-api-key
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
LANGFUSE_BASE_URL=https://cloud.langfuse.com  # or your self-hosted URL
```

### 3. Create Virtual Environment & Install Dependencies

```bash
uv venv              # create .venv
uv sync              # install dependencies into .venv
```

All subsequent commands (`uv run python`, `uv run pytest`, `uv run uvicorn`) automatically use the `.venv`.

### 4. Run Tests

```bash
uv run pytest tests/ -v
```

All nodes are tested in isolation before graph integration.

### 5. Start the API Server

```bash
uv run uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API documentation.

---

## API Usage

### Start Research

```bash
curl -X POST http://localhost:8000/api/v1/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "LLM pricing trends in 2025"}'
```

**Response:**

```json
{
  "run_id": "uuid-here",
  "status": "complete",
  "final_report": "# Research Report: ...",
  "sources": [
    {"title": "Source Name", "url": "https://example.com"}
  ],
  "langfuse_trace_id": "uuid-here",
  "latency_seconds": 120.5
}
```

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

---

## Observability with Langfuse

Every agent node is traced as a nested span under a single Langfuse trace:

- **Cost per run** — token usage and estimated cost
- **Latency per agent** — how long each node takes
- **Prompt versioning** — prompts managed in Langfuse Prompt Management with `production` labels; local fallbacks in `agent/prompts.py`

You can view your graph's traces in Langfuse dashboard.

---

## Project Structure

```
agent/
  state.py              # Shared TypedDict state definition
  nodes.py              # Agent node implementations (pure functions)
  prompts.py            # Local fallback prompts (PROMPTS dict)
  prompt_client.py      # Langfuse prompt fetcher with graceful fallback
  research_graph.py     # LangGraph wiring + MemorySaver checkpointing
  email_agent.py        # Existing reference agent
  graph.py              # Existing reference graph
tools/
  search.py             # Tavily search wrapper
api/
  models.py             # Pydantic request/response schemas
  router.py             # FastAPI routes
tests/
  test_nodes.py         # Isolated unit tests for every node
  test_graph.py         # Integration tests for full graph flow
  test_api.py           # FastAPI endpoint tests
  test_prompt_client.py # Prompt client fetch + fallback tests
  test_setup_prompts.py # Setup script tests
main.py                 # FastAPI app entrypoint
pyproject.toml          # uv project config
```

---

## Key Design Decisions

- **Pure node functions** — Each agent is a pure function `fn(state) -> partial_state`, making isolation testing trivial.
- **MemorySaver checkpointing** — LangGraph's in-memory checkpointer ensures the critic→reviser loop only re-executes changed nodes.
- **Graceful degradation** — Tavily failures return empty results rather than crashing the pipeline.
- **Loop guards** — The critic can trigger at most 2 revise iterations to prevent runaway loops and control cost.
- **Gemini content parsing** — The `_extract_text` helper safely handles both string and list-of-dicts LLM responses.
- **Langfuse Prompt Management** — Prompts are fetched at runtime from Langfuse by name/label. If Langfuse is unreachable, the app falls back to local prompts without crashing.

---

## Prompt Versioning with Langfuse

All agent prompts are managed in **Langfuse Prompt Management**, not hard-coded as Python constants.

### How it works

1. Prompts are defined as local fallbacks in `agent/prompts.py`.
2. They are pushed to Langfuse via `scripts/setup_prompts.py`.
3. At runtime, each node fetches the current `production`-labeled prompt from Langfuse via `agent/prompt_client.get_prompt()`.
4. If Langfuse is unreachable, the node gracefully falls back to the local prompt.
5. Every trace in Langfuse shows which prompt version was used.

### Push prompts to Langfuse

```bash
uv run python scripts/setup_prompts.py
```

### Update a prompt

1. Edit the prompt text in `scripts/setup_prompts.py` (or directly in the Langfuse UI).
2. Re-run `uv run python scripts/setup_prompts.py` to create a new version.
3. In the Langfuse UI, assign the `production` label to the new version to deploy it.
4. No code redeploy needed — the next API call fetches the new version automatically.

### Rollback

In the Langfuse UI, move the `production` label to any previous version. The app will serve that version on the next request.
