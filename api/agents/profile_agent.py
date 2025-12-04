from agents.base_agent import BaseAgent


class ProfileAgent(BaseAgent):
    def __init__(self):
        super().__init__("profile")

    def analyze_profile(self, profile_data: dict, mode="precision"):
        text = f"Données de l'utilisateur : {profile_data}"
        return self.run(text, mode)
