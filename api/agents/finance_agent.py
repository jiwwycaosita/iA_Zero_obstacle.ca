from agents.base_agent import BaseAgent
import json


class FinanceAgent(BaseAgent):
    def __init__(self):
        super().__init__("finance")

    def analyze_finances(self, transactions: list, user_profile: dict, mode="precision"):
        text = f"Profil: {user_profile}\nTransactions: {json.dumps(transactions, indent=2)}"
        return self.run(text, mode)
