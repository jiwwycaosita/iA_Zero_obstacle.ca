"""OpenAI client wrapper for text generation."""

import os
from typing import Optional

from openai import OpenAI


class OpenAIClient:
    """Lightweight OpenAI connector that supports text generation."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI connector.")

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key)

    def generate_text(self, prompt: str) -> str:
        """Generate text with the configured model.

        Args:
            prompt: User provided text prompt.
        Returns:
            Generated response string.
        """

        response = self.client.responses.create(
            model=self.model,
            input=[{"role": "user", "content": prompt}],
        )
        return response.output[0].content[0].text
