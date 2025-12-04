"""Detect semantic index changes using DeepDiff."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from deepdiff import DeepDiff

CURRENT_INDEX_PATH = Path("data/processed/semantic_index.json")
PREVIOUS_INDEX_PATH = Path("data/processed/semantic_index_prev.json")


class DiffDetector:
    """Load semantic index snapshots and compute differences."""

    def __init__(self, current_path: Path = CURRENT_INDEX_PATH, previous_path: Path = PREVIOUS_INDEX_PATH) -> None:
        self.current_path = current_path
        self.previous_path = previous_path

    def load_index(self, path: Path) -> Dict[str, Any]:
        """Load a semantic index JSON file, returning an empty mapping if missing."""
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def compute_diff(self, current: Optional[Dict[str, Any]] = None, previous: Optional[Dict[str, Any]] = None) -> DeepDiff:
        """Compute a DeepDiff between the provided snapshots or the stored files."""
        current_snapshot = current if current is not None else self.load_index(self.current_path)
        previous_snapshot = previous if previous is not None else self.load_index(self.previous_path)
        return DeepDiff(previous_snapshot, current_snapshot, ignore_order=True)

    def summarize_diff(self, diff: DeepDiff) -> str:
        """Return a human-readable summary of the differences for downstream analysis."""
        if not diff:
            return "Aucune différence détectée entre les index sémantiques."
        return diff.pretty()
