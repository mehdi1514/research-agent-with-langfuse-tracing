from unittest.mock import MagicMock, patch

import pytest

from agent import nodes


# ---------------------------------------------------------------------------
# Helper: build a mock LLM response
# ---------------------------------------------------------------------------

def _make_llm_response(text: str):
    mock = MagicMock()
    mock.content = text
    return mock


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------

@patch.object(nodes, "model")
def test_coordinator_generates_queries(mock_model):
    mock_model.invoke.return_value = _make_llm_response(
        "1. LLM pricing trends 2025\n2. OpenAI vs Google pricing\n3. Enterprise LLM costs"
    )
    state = {"topic": "LLM pricing trends in 2025"}
    result = nodes.coordinator(state)

    assert "search_queries" in result
    assert len(result["search_queries"]) == 3
    assert result["status"] == "searching"
    mock_model.invoke.assert_called_once()


@patch.object(nodes, "model")
def test_coordinator_strips_bullets(mock_model):
    mock_model.invoke.return_value = _make_llm_response(
        "- query one\n- query two\n5. query five"
    )
    state = {"topic": "test"}
    result = nodes.coordinator(state)

    queries = result["search_queries"]
    assert all(not q.startswith(("-", "1.", "5.")) for q in queries)


# ---------------------------------------------------------------------------
# Web Searcher
# ---------------------------------------------------------------------------

@patch("agent.nodes.execute_search")
def test_web_searcher_populates_results(mock_search):
    mock_search.return_value = [
        {"title": "Result A", "url": "https://a.com", "content": "content A", "score": 0.9},
        {"title": "Result B", "url": "https://b.com", "content": "content B", "score": 0.8},
    ]
    state = {
        "topic": "test",
        "search_queries": ["query 1", "query 2"],
    }
    result = nodes.web_searcher(state)

    assert len(result["search_results"]) == 2
    assert len(result["sources"]) == 2
    assert result["status"] == "summarizing"
    assert mock_search.call_count == 2


@patch("agent.nodes.execute_search")
def test_web_searcher_graceful_empty(mock_search):
    mock_search.return_value = []
    state = {"topic": "test", "search_queries": ["q1"]}
    result = nodes.web_searcher(state)

    assert result["search_results"] == [{"query": "q1", "results": []}]
    assert result["sources"] == []


# ---------------------------------------------------------------------------
# Summarizer
# ---------------------------------------------------------------------------

@patch.object(nodes, "model")
def test_summarizer_creates_sections(mock_model):
    mock_model.invoke.return_value = _make_llm_response(
        "## Executive Summary\nThis is a summary.\n## Key Findings\nFinding one."
    )
    state = {
        "topic": "test",
        "search_results": [
            {"query": "q1", "results": [{"title": "T", "content": "C"}]}
        ],
    }
    result = nodes.summarizer(state)

    assert "draft_sections" in result
    assert len(result["draft_sections"]) == 1
    assert result["status"] == "reviewing"
    mock_model.invoke.assert_called_once()


# ---------------------------------------------------------------------------
# Critic
# ---------------------------------------------------------------------------

@patch.object(nodes, "model")
def test_critic_returns_pass(mock_model):
    mock_model.invoke.return_value = _make_llm_response("PASS: Comprehensive and well structured.")
    state = {"topic": "test", "draft_sections": [{"heading": "H", "content": "C"}]}
    result = nodes.critic(state)

    assert "critic_feedback" in result
    assert result["critic_feedback"].lower().startswith("pass")


@patch.object(nodes, "model")
def test_critic_returns_revise(mock_model):
    mock_model.invoke.return_value = _make_llm_response("REVISE: Add more data on pricing.")
    state = {"topic": "test", "draft_sections": [{"heading": "H", "content": "C"}]}
    result = nodes.critic(state)

    assert result["critic_feedback"].lower().startswith("revise")


# ---------------------------------------------------------------------------
# Reviser
# ---------------------------------------------------------------------------

@patch.object(nodes, "model")
def test_reviser_updates_sections(mock_model):
    mock_model.invoke.return_value = _make_llm_response("## Key Findings\nRevised content.")
    state = {
        "topic": "test",
        "draft_sections": [{"heading": "Key Findings", "content": "Old content."}],
        "critic_feedback": "Add more detail.",
        "iteration_count": 0,
    }
    result = nodes.reviser(state)

    assert "draft_sections" in result
    assert result["iteration_count"] == 1
    assert result["status"] == "reviewing"
    assert "revised" in result["draft_sections"][0]["content"].lower()


# ---------------------------------------------------------------------------
# Assembler
# ---------------------------------------------------------------------------

@patch.object(nodes, "model")
def test_assembler_produces_markdown(mock_model):
    mock_model.invoke.return_value = _make_llm_response("# Report\n## TOC\nContent here.")
    state = {
        "topic": "test",
        "draft_sections": [{"heading": "Findings", "content": "Some findings."}],
        "sources": [{"title": "Source 1", "url": "https://example.com"}],
    }
    result = nodes.assembler(state)

    assert "final_report" in result
    assert result["status"] == "complete"
    mock_model.invoke.assert_called_once()
