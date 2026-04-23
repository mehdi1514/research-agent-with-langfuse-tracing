from unittest.mock import MagicMock, patch

import pytest

from agent.research_graph import compiled_research_graph


def _make_llm_response(text: str):
    mock = MagicMock()
    mock.content = text
    return mock


@patch("agent.nodes.execute_search")
@patch("agent.nodes.model")
def test_full_graph_end_to_end(mock_model, mock_search):
    """Run the full graph with mocked LLM and search."""
    call_count = [0]

    def side_effect(*args, **kwargs):
        call_count[0] += 1
        responses = [
            "1. query one\n2. query two",          # coordinator
            "## Findings\nSome findings here.",    # summarizer
            "PASS: good enough",                    # critic
            "# Final Report\n## TOC\nDone.",       # assembler
        ]
        return _make_llm_response(responses[min(call_count[0] - 1, len(responses) - 1)])

    mock_model.invoke.side_effect = side_effect
    mock_search.return_value = [
        {"title": "R", "url": "https://r.com", "content": "C", "score": 0.9}
    ]

    initial_state = {
        "topic": "test topic",
        "search_queries": [],
        "search_results": [],
        "draft_sections": [],
        "critic_feedback": None,
        "final_report": None,
        "sources": [],
        "status": "initialized",
        "iteration_count": 0,
    }

    config = {"configurable": {"thread_id": "test-thread-1"}}
    final_state = compiled_research_graph.invoke(initial_state, config=config)

    assert final_state["status"] == "complete"
    assert final_state["final_report"] is not None
    assert len(final_state["sources"]) > 0


@patch("agent.nodes.execute_search")
@patch("agent.nodes.model")
def test_graph_critic_loop(mock_model, mock_search):
    """Graph should loop through critic→reviser when critic says REVISE."""
    call_count = [0]

    def side_effect(*args, **kwargs):
        call_count[0] += 1
        responses = [
            "1. q1",                               # coordinator
            "## Findings\nDraft.",                 # summarizer (first)
            "REVISE: needs more detail",            # critic (first)
            "## Findings\nRevised draft.",          # reviser
            "PASS: improved",                       # critic (second)
            "# Final Report\nRevised report.",     # assembler
        ]
        return _make_llm_response(responses[min(call_count[0] - 1, len(responses) - 1)])

    mock_model.invoke.side_effect = side_effect
    mock_search.return_value = [
        {"title": "R", "url": "https://r.com", "content": "C", "score": 0.9}
    ]

    initial_state = {
        "topic": "test topic",
        "search_queries": [],
        "search_results": [],
        "draft_sections": [],
        "critic_feedback": None,
        "final_report": None,
        "sources": [],
        "status": "initialized",
        "iteration_count": 0,
    }

    config = {"configurable": {"thread_id": "test-thread-2"}}
    final_state = compiled_research_graph.invoke(initial_state, config=config)

    assert final_state["status"] == "complete"
    assert final_state["iteration_count"] == 1
