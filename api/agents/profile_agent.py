"""Agent focused on analyzing user profiles."""
from __future__ import annotations

from api.agents.base_agent import BaseAgent


class ProfileAgent(BaseAgent):
    """Analyze and summarize profile information."""

    def __init__(self, **kwargs):
        super().__init__(agent_name="profile_agent", **kwargs)

    def analyze(self, profile_text: str, mode: str | None = None, **kwargs) -> str:
        """Run a profile analysis."""

        return self.run(profile_text, mode=mode, **kwargs)
