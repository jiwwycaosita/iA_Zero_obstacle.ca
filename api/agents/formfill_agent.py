"""Agent guiding users through form completion."""
from __future__ import annotations

from api.agents.base_agent import BaseAgent


class FormFillAgent(BaseAgent):
    """Provide instructions to fill forms accurately."""

    def __init__(self, **kwargs):
        super().__init__(agent_name="formfill_agent", **kwargs)

    def guide(self, form_details: str, mode: str | None = None, **kwargs) -> str:
        """Offer guidance for completing a form."""

        return self.run(form_details, mode=mode, **kwargs)
