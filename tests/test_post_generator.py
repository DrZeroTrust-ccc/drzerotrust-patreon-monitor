"""Tests for the post generator using V1 mock data."""

from datetime import date

from src import capitol_trades_monitor, sec_cyber_monitor
from src.post_generator import build_post, output_filename


def test_output_filename_uses_iso_date():
    assert (
        output_filename(date(2026, 4, 26))
        == "drzerotrust-market-signal-watch-2026-04-26.md"
    )


def test_build_post_contains_all_required_sections():
    sec_signals = sec_cyber_monitor.fetch_recent_signals()
    capitol_signals = capitol_trades_monitor.fetch_recent_signals()
    md = build_post(date(2026, 4, 26), sec_signals, capitol_signals)

    required = [
        "# DrZeroTrust Market Signal Watch",
        "## Executive Summary",
        "## SEC Cyber Incident Signals",
        "## Capitol Hill Trade Signals",
        "## Sector-to-Committee Relevance",
        "## Watchlist",
        "## Source Links",
        "## Caveats",
        "Not investment advice",
    ]
    for section in required:
        assert section in md, f"missing section: {section}"


def test_post_contains_no_recommendation_language():
    sec_signals = sec_cyber_monitor.fetch_recent_signals()
    capitol_signals = capitol_trades_monitor.fetch_recent_signals()
    md = build_post(date(2026, 4, 26), sec_signals, capitol_signals).lower()

    forbidden = ["buy now", "sell now", "guaranteed", "insider trading"]
    for phrase in forbidden:
        assert phrase not in md, f"forbidden phrase present: {phrase}"


def test_watchlist_lists_each_mock_ticker():
    sec_signals = sec_cyber_monitor.fetch_recent_signals()
    capitol_signals = capitol_trades_monitor.fetch_recent_signals()
    md = build_post(date(2026, 4, 26), sec_signals, capitol_signals)

    for s in sec_signals:
        assert s.ticker in md
    for t in capitol_signals:
        assert t.ticker in md
