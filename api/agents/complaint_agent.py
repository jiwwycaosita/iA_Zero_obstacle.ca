from agents.base_agent import BaseAgent


class ComplaintAgent(BaseAgent):
    def __init__(self):
        super().__init__("complaint")

    def generate_complaint(self, situation: str, target_org: str, mode="performance"):
        text = f"Situation: {situation}\nOrganisme ciblé: {target_org}"
        return self.run(text, mode)
