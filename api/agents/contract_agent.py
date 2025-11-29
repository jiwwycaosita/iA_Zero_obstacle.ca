"""Agent providing contract risk summaries."""
from __future__ import annotations

from api.agents.base_agent import BaseAgent


class ContractAgent(BaseAgent):
    """Summarize contracts and highlight risks."""

    def __init__(self, **kwargs):
        super().__init__(agent_name="contract_agent", **kwargs)

    def summarize(self, contract_text: str, mode: str | None = None, **kwargs) -> str:
        """Summarize a contract or agreement."""

        return self.run(contract_text, mode=mode, **kwargs)
