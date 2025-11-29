"""Agent offering financial insights."""
from __future__ import annotations

from api.agents.base_agent import BaseAgent


class FinanceAgent(BaseAgent):
    """Provide financial analysis and suggestions."""

    def __init__(self, **kwargs):
        super().__init__(agent_name="finance_agent", **kwargs)

    def assess(self, financial_summary: str, mode: str | None = None, **kwargs) -> str:
        """Assess finances and return recommendations."""

        return self.run(financial_summary, mode=mode, **kwargs)
