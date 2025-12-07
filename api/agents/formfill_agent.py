from agents.base_agent import BaseAgent
import json


class FormFillAgent(BaseAgent):
    def __init__(self):
        super().__init__("formfill")

    def fill_form(self, form_schema: dict, user_profile: dict, mode="performance"):
        text = (
            f"Formulaire: {json.dumps(form_schema, indent=2)}\n"
            f"Profil utilisateur: {json.dumps(user_profile, indent=2)}"
        )
        return self.run(text, mode)
