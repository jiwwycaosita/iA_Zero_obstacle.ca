from agents.base_agent import BaseAgent


class ContractAgent(BaseAgent):
    def __init__(self):
        super().__init__("contract")

    def analyze_contract(self, contract_text: str, mode="precision"):
        return self.run(contract_text, mode)
