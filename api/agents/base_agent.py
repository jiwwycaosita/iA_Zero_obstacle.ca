"""Shared agent helpers and a base class for agent implementations."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from api.connectors.openai_connector import OpenAIConnector

logger = logging.getLogger(__name__)

# Default prompts to make agents usable without external prompt files.
BUILTIN_PROMPTS: Dict[str, Dict[str, str]] = {
    "profile_agent": {
        "default": "You are a helpful profile analysis assistant. Summarize and improve the provided profile.",
        "concise": "Provide a short, helpful assessment of the user's profile with key improvements.",
    },
    "formfill_agent": {
        "default": "Guide the user in completing forms with clear, direct instructions and helpful suggestions.",
    },
    "finance_agent": {
        "default": "Analyze the user's financial situation and offer practical recommendations.",
    },
    "law_agent": {
        "default": "Provide general legal considerations and next steps. Avoid giving legal advice.",
    },
    "complaint_agent": {
        "default": "Help draft a concise and respectful complaint using the user's details.",
    },
    "contract_agent": {
        "default": "Identify key contract risks and summarize obligations using the supplied information.",
    },
}


def load_prompts(agent_name: str) -> Dict[str, str]:
    """Load prompts for an agent from disk, falling back to built-in defaults.

    The function looks for ``api/prompts/<agent_name>.json`` containing a mapping of
    mode to prompt text. If the file does not exist or cannot be parsed, built-in
    defaults are returned.
    """

    prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
    prompt_file = prompts_dir / f"{agent_name}.json"

    if prompt_file.exists():
        try:
            with prompt_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return {str(key): str(value) for key, value in data.items()}
            logger.warning("Prompt file %s is not a mapping; using defaults.", prompt_file)
        except json.JSONDecodeError:
            logger.warning("Prompt file %s could not be decoded; using defaults.", prompt_file)
        except OSError:
            logger.exception("Failed to read prompt file %s; using defaults.", prompt_file)

    return BUILTIN_PROMPTS.get(agent_name, {"default": "You are a helpful AI assistant."})


class BaseAgent:
    """Base class encapsulating prompt selection and OpenAI invocation."""

    def __init__(
        self,
        agent_name: str,
        connector: OpenAIConnector | None = None,
        default_mode: str = "default",
    ) -> None:
        self.agent_name = agent_name
        self.connector = connector or OpenAIConnector()
        self.prompts = load_prompts(agent_name)
        self.default_mode = default_mode

    def available_modes(self) -> Iterable[str]:
        """Return the configured prompt modes for this agent."""

        return self.prompts.keys()

    def _build_messages(
        self, user_input: str, mode: str | None = None, context: Mapping[str, Any] | None = None
    ) -> list[dict[str, str]]:
        prompt_mode = mode or self.default_mode
        if prompt_mode not in self.prompts:
            raise ValueError(f"Unknown mode '{prompt_mode}'. Available modes: {', '.join(self.available_modes())}")

        prompt_text = self.prompts[prompt_mode]
        if context:
            try:
                prompt_text = prompt_text.format(**context)
            except Exception:  # pragma: no cover - defensive formatting
                logger.warning("Failed to format prompt text with context; using raw prompt.")

        return [
            {"role": "system", "content": prompt_text},
            {"role": "user", "content": user_input},
        ]

    def run(
        self,
        user_input: str,
        mode: str | None = None,
        context: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """Execute the agent using the selected prompt mode."""

        messages = self._build_messages(user_input, mode=mode, context=context)
        return self.connector.chat(messages, **kwargs)
