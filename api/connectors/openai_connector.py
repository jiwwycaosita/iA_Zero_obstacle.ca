"""OpenAI connector with minimal error handling for chat completions."""
from __future__ import annotations

import importlib.util
import logging
import os
from typing import Any, Iterable, Mapping, MutableMapping

OpenAI = None
if importlib.util.find_spec("openai"):
    from openai import OpenAI  # type: ignore

logger = logging.getLogger(__name__)


class OpenAIConnector:
    """Simple wrapper around the OpenAI chat completion API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        default_params: MutableMapping[str, Any] | None = None,
    ) -> None:
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if api_key is None:
            logger.warning("OPENAI_API_KEY is not set; requests will fail at runtime.")
        self.client = OpenAI(api_key=api_key) if OpenAI is not None else None
        self.model = model
        self.default_params: MutableMapping[str, Any] = default_params or {"temperature": 0.2}

    def chat(self, messages: Iterable[Mapping[str, str]], **kwargs: Any) -> str:
        """Send a chat completion request.

        Args:
            messages: Iterable of role/content dictionaries for the OpenAI API.
            **kwargs: Additional parameters forwarded to the API (e.g., temperature).

        Returns:
            The model's text content.

        Raises:
            RuntimeError: If the request cannot be completed.
        """

        if self.client is None:
            raise RuntimeError("OpenAI client is unavailable; ensure the openai package is installed.")

        payload = {**self.default_params, **kwargs}
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=list(messages),
                **payload,
            )
            message = response.choices[0].message.content
            return message or ""
        except Exception as exc:  # pragma: no cover - defensive for runtime errors
            logger.error("OpenAI chat completion failed: %s", exc, exc_info=True)
            raise RuntimeError("Failed to generate a response from OpenAI.") from exc
