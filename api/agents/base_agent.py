from connectors.openai_connector import OpenAIConnector
from agents.load_prompts import load_prompt


class BaseAgent:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.connector = OpenAIConnector()

    def run(self, user_input: str, mode: str = "precision") -> dict:
        """Charge le prompt du bon agent et exécute la requête."""
        prompt = load_prompt(self.agent_name, mode)
        full_input = f"{prompt}\n\nCONTEXTE UTILISATEUR:\n{user_input}"
        result = self.connector.complete(full_input)
        return result
