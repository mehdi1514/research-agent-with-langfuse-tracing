from typing import Any, Dict, List

from langchain_tavily import TavilySearch
from dotenv import load_dotenv

load_dotenv()

# Initialize the Tavily search tool
_tavily_search = TavilySearch(
    max_results=5,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=False,
    include_images=False,
)


def execute_search(query: str) -> List[Dict[str, Any]]:
    """Execute a Tavily web search and return structured results.

    Args:
        query: The search query string.

    Returns:
        A list of result dictionaries with keys like title, url, content, score.
    """
    try:
        raw = _tavily_search.invoke(query)
        # TavilySearch returns a dict with a 'results' list
        results = raw.get("results", []) if isinstance(raw, dict) else raw
        # Normalize results to a consistent dict structure
        normalized = []
        for r in results:
            if isinstance(r, dict):
                normalized.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", r.get("snippet", "")),
                    "score": r.get("score", 0.0),
                })
        return normalized
    except Exception:
        # Graceful degradation: return empty list on failure
        return []
