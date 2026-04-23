from unittest.mock import MagicMock, patch

from scripts.setup_prompts import PROMPTS


@patch("scripts.setup_prompts.langfuse")
def test_setup_prompts_creates_all(mock_langfuse):
    """The setup script should call create_prompt for every prompt in PROMPTS."""
    mock_langfuse.create_prompt.return_value = MagicMock()

    # Import and run main
    import scripts.setup_prompts as setup_module
    setup_module.main()

    assert mock_langfuse.create_prompt.call_count == len(PROMPTS)
    for name in PROMPTS:
        calls = [c for c in mock_langfuse.create_prompt.call_args_list if c[1]["name"] == name]
        assert len(calls) == 1, f"create_prompt not called for {name}"
