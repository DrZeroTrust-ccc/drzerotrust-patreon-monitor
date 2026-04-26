"""Tiny JSON-backed state store.

Tracks which signals have already been included in a published draft so
future runs don't re-surface the same signal. V1 only writes a stub
record after a successful draft generation; it is not yet wired to a
deduplication step.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class StateStore:
    def __init__(self, state_dir: Path) -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.state_dir / "state.json"

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"runs": [], "seen_signals": []}
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: Dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def record_run(self, output_path: Path, signal_count: int) -> None:
        data = self.load()
        data["runs"].append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "output": str(output_path),
                "signal_count": signal_count,
            }
        )
        self.save(data)
