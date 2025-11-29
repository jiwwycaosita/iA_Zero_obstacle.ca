"""Agent that helps draft complaints."""
from __future__ import annotations

from api.agents.base_agent import BaseAgent


class ComplaintAgent(BaseAgent):
    """Draft respectful complaints based on user details."""

    def __init__(self, **kwargs):
        super().__init__(agent_name="complaint_agent", **kwargs)

    def draft(self, complaint_details: str, mode: str | None = None, **kwargs) -> str:
        """Draft a complaint message."""

        return self.run(complaint_details, mode=mode, **kwargs)
