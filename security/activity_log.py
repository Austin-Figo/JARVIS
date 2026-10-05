"""Append-only local audit log for JARVIS actions."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any


class ActivityLog:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path(__file__).resolve().parents[1] / "logs" / "activity.jsonl"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def record(self, event: str, **details: Any) -> None:
        entry = {"timestamp": int(time.time() * 1000), "event": event, **details}
        with self._lock, self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        with self._lock, self._path.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()[-limit:]
        entries: list[dict[str, Any]] = []
        for line in reversed(lines):
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries
