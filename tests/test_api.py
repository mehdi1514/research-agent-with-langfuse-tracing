from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _make_llm_response(text: str):
    mock = MagicMock()
    mock.content = text
    return mock


@patch("agent.nodes.execute_search")
@patch("api.router.compiled_research_graph")
def test_post_research(mock_graph, mock_search):
    """Test the POST /research endpoint returns a complete response."""
    mock_graph.invoke.return_value = {
        "topic": "LLM pricing trends in 2025",
        "status": "complete",
        "final_report": "# Report\nContent",
        "sources": [{"title": "Source", "url": "https://example.com"}],
    }

    response = client.post(
        "/api/v1/research",
        json={"topic": "LLM pricing trends in 2025", "max_iterations": 2},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "complete"
    assert data["final_report"] == "# Report\nContent"
    assert len(data["sources"]) == 1
    assert "run_id" in data
    assert "latency_seconds" in data


def test_health_check():
    """Test the health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
