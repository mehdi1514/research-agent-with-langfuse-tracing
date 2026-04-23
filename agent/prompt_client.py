"""Langfuse Prompt Management client with local fallback.

Fetches prompts from Langfuse at runtime. If Langfuse is unreachable,
falls back to the local PROMPTS dict in agent.prompts.
"""

from langfuse import Langfuse
from dotenv import load_dotenv

load_dotenv()

from agent.prompts import PROMPTS

# Initialize Langfuse client for prompt management
_langfuse = Langfuse()


class _LocalPrompt:
    """Minimal stand-in for a Langfuse prompt object using local strings."""

    def __init__(self, text: str):
        self.prompt = text
        self.name = "local-fallback"
        self.version = 0

    def compile(self, **kwargs) -> str:
        """Fill template variables. Falls back to plain string if formatting fails."""
        try:
            return self.prompt.format(**kwargs)
        except (KeyError, ValueError):
            # If variables don't match, return raw prompt (best effort)
            return self.prompt


def get_prompt(name: str, label: str = "production"):
    """Fetch a prompt from Langfuse Prompt Management.

    Args:
        name: Prompt name (e.g., "coordinator-system").
        label: Version label to fetch (default "production").

    Returns:
        A Langfuse Prompt object or a _LocalPrompt fallback.
    """
    try:
        return _langfuse.get_prompt(name, label=label)
    except Exception:
        # Graceful fallback to local prompt
        print(f"Using fallback ${name} prompt")
        return _LocalPrompt(PROMPTS[name])
