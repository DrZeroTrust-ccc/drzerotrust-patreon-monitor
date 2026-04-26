"""Tests for the post generator using V1 mock data."""

from datetime import date

from src import capitol_trades_monitor, sec_cyber_monitor
from src.post_generator import build_post, output_filename


def _build():
    sec_signals = sec_cyber_monitor.fetch_recent_signals()
    capitol_signals = capitol_trades_monitor.fetch_recent_signals()
    return sec_signals, capitol_signals, build_post(
        date(2026, 4, 26), sec_signals, capitol_signals
    )


def test_output_filename_uses_iso_date():
    assert (
        output_filename(date(2026, 4, 26))
        == "drzerotrust-market-signal-watch-2026-04-26.md"
    )


def test_build_post_contains_all_required_sections():
    _, _, md = _build()
    required = [
        "# DrZeroTrust Market Signal Watch",
        "## Bottom Line Up Front",
        "## High-Priority Watchlist",
        "## SEC Cyber Incident Signals",
        "## Capitol Hill Trade Signals",
        "## Sector-to-Committee Conflict Lens",
        "## Source Links",
        "## Research Caveats",
        "## Closing Note",
        "Not investment advice",
    ]
    for section in required:
        assert section in md, f"missing section: {section}"


def test_opening_note_explains_purpose():
    _, _, md = _build()
    assert "public disclosures" in md.lower()
    assert "convergence" in md.lower()


def test_bluf_has_three_to_five_bullets():
    _, _, md = _build()
    bluf_block = md.split("## Bottom Line Up Front", 1)[1].split("##", 1)[0]
    bullets = [
        line for line in bluf_block.splitlines() if line.startswith("- ")
    ]
    assert 3 <= len(bullets) <= 5, f"BLUF has {len(bullets)} bullets, want 3-5"


def test_watchlist_table_has_required_columns():
    _, _, md = _build()
    assert (
        "| Signal | Entity | Ticker | Why It Matters | Watch Priority |" in md
    )


def test_sec_section_has_per_signal_fields():
    sec_signals, _, md = _build()
    for s in sec_signals:
        assert s.company in md
        assert s.ticker in md
        assert s.filing_item in md
    assert "Market relevance:" in md
    assert "What to watch next:" in md


def test_capitol_section_has_per_signal_fields():
    _, capitol_signals, md = _build()
    for t in capitol_signals:
        assert t.filer in md
        assert t.role in md
        assert t.amount_range in md
    assert "Committee relevance:" in md
    assert "Market relevance:" in md


def test_conflict_lens_has_table_columns():
    _, _, md = _build()
    assert "| Sector | Relevant Committees | Why It Matters |" in md


def test_research_caveats_present():
    _, _, md = _build()
    caveats = md.split("## Research Caveats", 1)[1].split("##", 1)[0]
    assert "lag" in caveats.lower()
    assert "amended" in caveats.lower()
    assert "not proof of wrongdoing" in caveats.lower()
    assert "not investment advice" in caveats.lower()


def test_closing_note_signed_by_drzerotrust():
    _, _, md = _build()
    closing = md.split("## Closing Note", 1)[1].split("---", 1)[0]
    assert "convergence" in closing.lower()
    assert "DrZeroTrust" in closing


def test_post_contains_no_recommendation_language():
    _, _, md = _build()
    md_lower = md.lower()
    forbidden = ["buy now", "sell now", "guaranteed return", "price target"]
    for phrase in forbidden:
        assert phrase not in md_lower, f"forbidden phrase present: {phrase}"


def test_post_explicitly_denies_misconduct_allegations():
    _, _, md = _build()
    md_lower = md.lower()
    assert "no statement in this post alleges insider trading" in md_lower
    assert "not investment advice" in md_lower


def test_watchlist_lists_each_mock_ticker():
    sec_signals, capitol_signals, md = _build()
    for s in sec_signals:
        assert s.ticker in md
    for t in capitol_signals:
        assert t.ticker in md
