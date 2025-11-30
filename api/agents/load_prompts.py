"""Utility functions to load prompt templates for iA agents."""

from pathlib import Path
from typing import Optional

import yaml

VALID_MODES = {"precision", "performance", "efficacite"}


def load_prompt(agent: str, mode: str, prompts_dir: Optional[Path] = None) -> str:
    """Load a prompt for a given agent and mode.

    Args:
        agent: Name of the agent, matching a YAML file in the prompts directory
            (without the ``.yaml`` extension).
        mode: One of ``precision``, ``performance`` or ``efficacite`` (case-insensitive).
        prompts_dir: Optional path to the prompts directory. Defaults to the repository
            ``prompts`` folder located two levels above this file.

    Returns:
        The prompt text for the requested agent and mode.

    Raises:
        ValueError: If ``agent`` is empty, the ``mode`` is unsupported, or the YAML
            file does not contain a string for the requested mode.
        FileNotFoundError: If the prompts directory or agent file cannot be located.
        KeyError: If the requested mode is not present in the YAML file.
    """

    if not agent:
        raise ValueError("Agent name must be provided.")

    normalized_mode = mode.lower()
    if normalized_mode not in VALID_MODES:
        raise ValueError(
            f"Unsupported mode '{mode}'. Expected one of: {', '.join(sorted(VALID_MODES))}."
        )

    base_dir = Path(prompts_dir) if prompts_dir else Path(__file__).resolve().parents[2] / "prompts"
    if not base_dir.exists():
        raise FileNotFoundError(f"Prompts directory not found: {base_dir}")

    prompt_file = base_dir / f"{agent}.yaml"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found for agent '{agent}': {prompt_file}")

    data = yaml.safe_load(prompt_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Prompt file {prompt_file} must contain a mapping of modes.")

    if normalized_mode not in data:
        raise KeyError(f"Mode '{normalized_mode}' not found in {prompt_file.name}.")

    prompt = data[normalized_mode]
    if not isinstance(prompt, str):
        raise ValueError(
            f"Prompt for mode '{normalized_mode}' in {prompt_file.name} must be a string."
        )

    return prompt.strip()
