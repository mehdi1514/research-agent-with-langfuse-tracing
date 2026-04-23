from unittest.mock import MagicMock, patch

import pytest

from agent.prompt_client import get_prompt, _LocalPrompt
from agent.prompts import PROMPTS


@patch("agent.prompt_client._langfuse.get_prompt")
def test_get_prompt_fetches_from_langfuse(mock_get_prompt):
    """When Langfuse is available, return the fetched prompt object."""
    mock_prompt = MagicMock()
    mock_prompt.prompt = "Fetched from Langfuse"
    mock_prompt.compile.return_value = "Compiled"
    mock_get_prompt.return_value = mock_prompt

    result = get_prompt("coordinator-system")

    assert result.prompt == "Fetched from Langfuse"
    mock_get_prompt.assert_called_once_with("coordinator-system", label="production")


@patch("agent.prompt_client._langfuse.get_prompt")
def test_get_prompt_fallback_on_error(mock_get_prompt):
    """When Langfuse raises an error, fall back to the local prompt."""
    mock_get_prompt.side_effect = Exception("Langfuse down")

    result = get_prompt("coordinator-system")

    assert isinstance(result, _LocalPrompt)
    assert result.prompt == PROMPTS["coordinator-system"]


def test_local_prompt_compile():
    """_LocalPrompt.compile() fills template variables correctly."""
    local = _LocalPrompt("Hello {name}, you are {age} years old.")
    compiled = local.compile(name="Alice", age="30")
    assert compiled == "Hello Alice, you are 30 years old."


def test_local_prompt_compile_missing_vars():
    """_LocalPrompt.compile() returns raw prompt if variables don't match."""
    local = _LocalPrompt("Hello {name}")
    compiled = local.compile(wrong_var="test")
    assert compiled == "Hello {name}"
