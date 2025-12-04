"""Generate human-readable alerts from detected differences using GPT-4."""

from __future__ import annotations

from typing import Any

from api.connectors.openai_connector import OpenAIConnector
from api.monitoring.diff_detector import DiffDetector


class AlertGenerator:
    """Produce narrative alerts to describe changes in the semantic index."""

    def __init__(self, diff_detector: DiffDetector, llm_connector: OpenAIConnector) -> None:
        self.diff_detector = diff_detector
        self.llm_connector = llm_connector

    def create_alert(self, current_snapshot: Any = None, previous_snapshot: Any = None) -> str:
        """Generate an alert message summarizing changes between two snapshots."""
        diff = self.diff_detector.compute_diff(current_snapshot, previous_snapshot)
        diff_text = self.diff_detector.summarize_diff(diff)
        prompt = (
            "Identifie les changements clés entre deux index sémantiques. "
            "Formule un résumé concis, en français, avec l'impact potentiel pour l'utilisateur. "
            "Utilise un ton informatif et clair. Voici les différences détectées :\n" + diff_text
        )
        return self.llm_connector.interpret_diff(prompt)
