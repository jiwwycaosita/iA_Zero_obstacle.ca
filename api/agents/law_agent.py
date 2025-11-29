"""Agent focusing on legal context and next steps."""
from __future__ import annotations

from api.agents.base_agent import BaseAgent


class LawAgent(BaseAgent):
    """Offer general legal considerations without legal advice."""

    def __init__(self, **kwargs):
        super().__init__(agent_name="law_agent", **kwargs)

    def review(self, legal_question: str, mode: str | None = None, **kwargs) -> str:
        """Review a legal scenario and outline considerations."""

        return self.run(legal_question, mode=mode, **kwargs)
