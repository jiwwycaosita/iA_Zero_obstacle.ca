from agents.base_agent import BaseAgent


class LawAgent(BaseAgent):
    def __init__(self):
        super().__init__("law")

    def find_laws(self, query: str, province: str = "federal", mode="precision"):
        text = f"Demande: {query}\nProvince: {province}"
        return self.run(text, mode)
