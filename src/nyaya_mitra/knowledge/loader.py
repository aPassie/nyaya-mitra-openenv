"""kb loader. reads schemes, frameworks, and dlsa directory from data/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_ROOT = Path(__file__).parent / "data"


class KnowledgeBase:
    def __init__(self, data_root: Path = DATA_ROOT) -> None:
        self.data_root = data_root
        self.schemes: dict[str, dict[str, Any]] = {}
        self.frameworks: dict[str, dict[str, Any]] = {}
        self.dlsa: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        for f in sorted((self.data_root / "schemes").glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            self.schemes[data["scheme_id"]] = data
        for f in sorted((self.data_root / "frameworks").glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            self.frameworks[data["framework_id"]] = data
        dlsa_path = self.data_root / "dlsa_directory.json"
        if dlsa_path.exists():
            self.dlsa = json.loads(dlsa_path.read_text(encoding="utf-8"))

    def scheme_ids(self) -> list[str]:
        return sorted(self.schemes.keys())

    def framework_ids(self) -> list[str]:
        return sorted(self.frameworks.keys())

    def all_contact_ids(self) -> set[str]:
        ids: set[str] = set()
        nalsa = self.dlsa.get("NALSA") or {}
        if "contact_id" in nalsa:
            ids.add(nalsa["contact_id"])
        for slsa in (self.dlsa.get("SLSAs") or {}).values():
            if "contact_id" in slsa:
                ids.add(slsa["contact_id"])
        for dlsa in (self.dlsa.get("DLSAs") or {}).values():
            if "contact_id" in dlsa:
                ids.add(dlsa["contact_id"])
        return ids
