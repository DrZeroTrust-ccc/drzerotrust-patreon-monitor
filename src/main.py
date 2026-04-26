"""V1 entrypoint: generate exactly one mock Patreon-ready markdown draft.

Run with:
    python -m src.main
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from . import capitol_trades_monitor, sec_cyber_monitor
from .google_drive_archive import GoogleDriveArchive
from .post_generator import build_post, output_filename
from .state_store import StateStore


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
STATE_DIR = PROJECT_ROOT / "state"


def main() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    sec_signals = sec_cyber_monitor.fetch_recent_signals()
    capitol_signals = capitol_trades_monitor.fetch_recent_signals()

    today = date.today()
    markdown = build_post(today, sec_signals, capitol_signals)

    out_path = OUTPUT_DIR / output_filename(today)
    out_path.write_text(markdown, encoding="utf-8")

    state = StateStore(STATE_DIR)
    state.record_run(out_path, len(sec_signals) + len(capitol_signals))

    archive = GoogleDriveArchive()
    archive_result = archive.archive(out_path)

    print(f"[ok] wrote draft: {out_path}")
    print(f"[ok] signals: sec={len(sec_signals)} capitol={len(capitol_signals)}")
    print(f"[ok] archive (no-op in V1): {archive_result['reason']}")
    print("[note] V1 does not post to Patreon and does not call any external API.")
    return out_path


if __name__ == "__main__":
    main()
