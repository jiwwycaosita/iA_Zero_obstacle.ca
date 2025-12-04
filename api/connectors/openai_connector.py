"""Connector for interacting with OpenAI's GPT-4 model."""

from __future__ import annotations

from typing import Any, Dict, List

import openai


class OpenAIConnector:
    """Simple wrapper around the OpenAI Chat Completions API."""

    def __init__(self, api_key: str, model: str = "gpt-4") -> None:
        self.api_key = api_key
        self.model = model

    def interpret_diff(self, prompt: str) -> str:
        """Use GPT-4 to interpret and rephrase the provided diff description."""
        openai.api_key = self.api_key
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=self._build_messages(prompt),
            temperature=0.2,
            max_tokens=500,
        )
        return response["choices"][0]["message"]["content"].strip()

    def _build_messages(self, prompt: str) -> List[Dict[str, Any]]:
        system_prompt = (
            "Tu es un assistant qui explique clairement les changements dans un index sémantique. "
            "Présente des recommandations actionnables lorsque pertinent."
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
