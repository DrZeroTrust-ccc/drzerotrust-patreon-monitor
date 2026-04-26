"""Entrypoint: generate one DrZeroTrust Market Signal Watch markdown draft.

Default run uses mock data only:
    python -m src.main

Pull real SEC EDGAR cyber-incident filings (last 24 hours) instead of
the SEC mock:
    python -m src.main --sec-real

Capitol Hill, Google Drive, and Patreon are still mock / no-op.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path
from typing import List, Optional, Sequence

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv(*args, **kwargs):  # type: ignore[misc]
        return False

from . import capitol_trades_monitor, sec_cyber_monitor
from .google_drive_archive import GoogleDriveArchive
from .post_generator import build_post, output_filename
from .sec_cyber_monitor import LiveFetchResult, SecCyberSignal
from .state_store import StateStore


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
STATE_DIR = PROJECT_ROOT / "state"


def _parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="src.main",
        description=(
            "Generate one DrZeroTrust Market Signal Watch markdown draft. "
            "Defaults to mock data; pass --sec-real to pull live SEC EDGAR "
            "cyber-incident filings."
        ),
    )
    parser.add_argument(
        "--sec-real",
        action="store_true",
        help=(
            "Pull SEC cyber-incident filings live from EDGAR (last 24 "
            "hours). Requires SEC_USER_AGENT in the environment. All "
            "other data sources stay mock in V1."
        ),
    )
    parser.add_argument(
        "--lookback-hours",
        type=int,
        default=24,
        help="Live SEC mode only: lookback window in hours (default 24).",
    )
    return parser.parse_args(argv)


def _print_live_summary(result: LiveFetchResult) -> None:
    print(
        f"[sec-live] window: {result.window_start} → {result.window_end}",
        flush=True,
    )
    if result.error:
        print(f"[sec-live] error: {result.error}", flush=True)
        return
    print(
        f"[sec-live] candidates examined: {result.candidates_examined}, "
        f"qualified: {len(result.signals)}, rejected: {result.rejected}",
        flush=True,
    )
    if result.rejected_reasons:
        breakdown = ", ".join(
            f"{k}={v}" for k, v in sorted(result.rejected_reasons.items())
        )
        print(f"[sec-live] rejection breakdown: {breakdown}", flush=True)


def _load_sec_signals(args: argparse.Namespace) -> List[SecCyberSignal]:
    if not args.sec_real:
        return sec_cyber_monitor.fetch_recent_signals()

    user_agent = os.getenv("SEC_USER_AGENT", "").strip()
    if not user_agent:
        print(
            "[sec-live] error: SEC_USER_AGENT is not set. "
            "See .env.example. Falling back to mock SEC data.",
            file=sys.stderr,
            flush=True,
        )
        return sec_cyber_monitor.fetch_recent_signals()

    print("[sec-live] fetching live SEC EDGAR cyber-incident filings...",
          flush=True)
    result = sec_cyber_monitor.fetch_live_signals(
        user_agent=user_agent,
        lookback_hours=args.lookback_hours,
    )
    _print_live_summary(result)

    if result.error or not result.signals:
        # Live fetch returned no qualifying signals (or hit an error).
        # Don't manufacture data; the briefing simply notes "no SEC
        # signals this cycle."
        return []
    return result.signals


def main(argv: Optional[Sequence[str]] = None) -> Path:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    args = _parse_args(argv)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    sec_signals = _load_sec_signals(args)
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
    print(
        f"[ok] signals: sec={len(sec_signals)} capitol={len(capitol_signals)} "
        f"(sec-mode={'live' if args.sec_real else 'mock'})"
    )
    print(f"[ok] archive (no-op in V1): {archive_result['reason']}")
    print("[note] V1 does not post to Patreon and does not draft to Patreon.")
    return out_path


if __name__ == "__main__":
    main()
