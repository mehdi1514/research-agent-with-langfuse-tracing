from typing import Any, Dict, List

from langchain.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv

from agent.prompt_client import get_prompt
from agent.state import ResearchState
from tools.search import execute_search

load_dotenv()

# Initialize LLM (matches existing project pattern)
model = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", temperature=0)


def _extract_text(response) -> str:
    """Safely extract text from an LLM response.

    Handles both string content and list-of-dicts content (Gemini format).
    """
    content = response.content if hasattr(response, "content") else str(response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                texts.append(item["text"])
            elif isinstance(item, str):
                texts.append(item)
        return "\n".join(texts)
    return str(content)


def coordinator(state: ResearchState) -> Dict[str, Any]:
    """Generate targeted search queries for the research topic."""
    topic = state["topic"]
    system_prompt = get_prompt("coordinator-system")
    user_prompt = get_prompt("coordinator-user")

    messages = [
        SystemMessage(content=system_prompt.prompt),
        HumanMessage(content=user_prompt.compile(topic=topic)),
    ]
    response = model.invoke(messages)
    text = _extract_text(response)

    queries: List[str] = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Remove leading numbers/bullets like "1. " or "- "
        if ". " in line[:4]:
            line = line.split(". ", 1)[1]
        elif line.startswith("-"):
            line = line.lstrip("- ").strip()
        if line:
            queries.append(line)

    return {
        "search_queries": queries,
        "status": "searching",
    }


def web_searcher(state: ResearchState) -> Dict[str, Any]:
    """Execute web searches for each generated query."""
    queries = state.get("search_queries", [])
    all_results: List[Dict[str, Any]] = []
    all_sources: List[Dict[str, Any]] = []

    for query in queries:
        results = execute_search(query)
        all_results.append({"query": query, "results": results})
        for r in results:
            source = {"title": r.get("title", ""), "url": r.get("url", "")}
            if source not in all_sources:
                all_sources.append(source)

    return {
        "search_results": all_results,
        "sources": all_sources,
        "status": "summarizing",
    }


def summarizer(state: ResearchState) -> Dict[str, Any]:
    """Synthesize search results into structured draft sections."""
    topic = state["topic"]
    search_results = state.get("search_results", [])

    # Flatten results into a readable string
    results_text = ""
    for item in search_results:
        results_text += f"\nQuery: {item['query']}\n"
        for r in item.get("results", []):
            results_text += f"- {r.get('title', '')}: {r.get('content', '')}\n"

    system_prompt = get_prompt("summarizer-system")
    user_prompt = get_prompt("summarizer-user")

    messages = [
        SystemMessage(content=system_prompt.prompt),
        HumanMessage(
            content=user_prompt.compile(topic=topic, search_results=results_text)
        ),
    ]
    response = model.invoke(messages)
    text = _extract_text(response)

    # Store the entire text as a single section for now
    sections = [{"heading": "Key Findings", "content": text}]

    return {
        "draft_sections": sections,
        "status": "reviewing",
    }


def critic(state: ResearchState) -> Dict[str, Any]:
    """Review draft sections and return PASS or REVISE feedback."""
    topic = state["topic"]
    draft_sections = state.get("draft_sections", [])

    sections_text = ""
    for sec in draft_sections:
        sections_text += f"\n## {sec.get('heading', 'Section')}\n{sec.get('content', '')}\n"

    system_prompt = get_prompt("critic-system")
    user_prompt = get_prompt("critic-user")

    messages = [
        SystemMessage(content=system_prompt.prompt),
        HumanMessage(
            content=user_prompt.compile(topic=topic, draft_sections=sections_text)
        ),
    ]
    response = model.invoke(messages)
    text = _extract_text(response)

    feedback = text.strip()
    return {
        "critic_feedback": feedback,
    }


def reviser(state: ResearchState) -> Dict[str, Any]:
    """Revise draft sections based on critic feedback."""
    topic = state["topic"]
    draft_sections = state.get("draft_sections", [])
    feedback = state.get("critic_feedback", "")

    sections_text = ""
    for sec in draft_sections:
        sections_text += f"\n## {sec.get('heading', 'Section')}\n{sec.get('content', '')}\n"

    system_prompt = get_prompt("reviser-system")
    user_prompt = get_prompt("reviser-user")

    messages = [
        SystemMessage(content=system_prompt.prompt),
        HumanMessage(
            content=user_prompt.compile(
                topic=topic,
                draft_sections=sections_text,
                feedback=feedback,
            )
        ),
    ]
    response = model.invoke(messages)
    text = _extract_text(response)

    revised_sections = [{"heading": "Key Findings", "content": text}]

    return {
        "draft_sections": revised_sections,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "status": "reviewing",
    }


def assembler(state: ResearchState) -> Dict[str, Any]:
    """Compile draft sections and sources into a final Markdown report."""
    topic = state["topic"]
    draft_sections = state.get("draft_sections", [])
    sources = state.get("sources", [])

    sections_text = ""
    for sec in draft_sections:
        sections_text += f"\n## {sec.get('heading', 'Section')}\n{sec.get('content', '')}\n"

    sources_text = ""
    for i, src in enumerate(sources, start=1):
        sources_text += f"{i}. [{src.get('title', 'Source')}]({src.get('url', '')})\n"

    system_prompt = get_prompt("assembler-system")
    user_prompt = get_prompt("assembler-user")

    messages = [
        SystemMessage(content=system_prompt.prompt),
        HumanMessage(
            content=user_prompt.compile(
                topic=topic,
                draft_sections=sections_text,
                sources=sources_text,
            )
        ),
    ]
    response = model.invoke(messages)
    text = _extract_text(response)

    return {
        "final_report": text,
        "status": "complete",
    }
