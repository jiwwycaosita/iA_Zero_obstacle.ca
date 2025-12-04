import os
import yaml


def load_prompt(agent_name: str, mode: str = "precision"):
    """
    Charge un prompt pour l'agent spécifié (profile, finance, etc.)
    mode = precision | performance | efficacite
    """
    path = f"prompts/{agent_name}_agent.prompts.yaml"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Prompt file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
        return prompts.get(mode, "")
