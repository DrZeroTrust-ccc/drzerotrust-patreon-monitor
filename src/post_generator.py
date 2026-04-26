"""Assembles a Patreon-ready markdown draft from mock signals.

The generator is pure: given lists of signals and a date, it returns
a markdown string. Persisting the file is the caller's responsibility.
"""

from __future__ import annotations

from datetime import date
from typing import Iterable, List

from .capitol_trades_monitor import CapitolTradeSignal
from .sec_cyber_monitor import SecCyberSignal


# Heuristic mapping from sector to congressional committees whose
# jurisdiction tends to overlap. Used purely as an educational
# context cue. Not a claim about any specific filer.
SECTOR_TO_COMMITTEES: dict[str, list[str]] = {
    "Healthcare": [
        "House Energy and Commerce",
        "Senate Health, Education, Labor, and Pensions",
    ],
    "Industrials / Logistics": [
        "House Transportation and Infrastructure",
        "Senate Commerce, Science, and Transportation",
    ],
    "Technology / Government Cloud": [
        "House Armed Services",
        "Senate Armed Services",
        "House Oversight and Accountability",
    ],
}


DISCLAIMER = (
    "**Not investment advice.** This post is an educational summary of "
    "publicly available regulatory filings. Nothing here is a "
    "recommendation to buy, sell, or hold any security. No statement in "
    "this post alleges insider trading, market manipulation, or any "
    "other misconduct by any person or entity. Always do your own "
    "research and consult a licensed financial professional before "
    "making any investment decision."
)


def _format_sec_section(signals: Iterable[SecCyberSignal]) -> str:
    lines: List[str] = []
    for s in signals:
        lines.append(
            f"- **{s.company} ({s.ticker})** — {s.sector}\n"
            f"  - Filing: {s.filing_type}, filed {s.filed_at}\n"
            f"  - Summary: {s.summary}\n"
            f"  - Source: <{s.source_url}>"
        )
    return "\n".join(lines) if lines else "_No SEC cyber-incident signals this cycle._"


def _format_capitol_section(signals: Iterable[CapitolTradeSignal]) -> str:
    lines: List[str] = []
    for t in signals:
        lines.append(
            f"- **{t.filer}** ({t.chamber}, {t.committee})\n"
            f"  - {t.transaction_type} of {t.company} ({t.ticker}) — {t.sector}\n"
            f"  - Amount range: {t.amount_range}\n"
            f"  - Transaction date: {t.transaction_date} | Disclosed: {t.disclosure_date}\n"
            f"  - Source: <{t.source_url}>"
        )
    return "\n".join(lines) if lines else "_No Capitol Hill trade disclosures this cycle._"


def _format_relevance_section(
    sec_signals: Iterable[SecCyberSignal],
    capitol_signals: Iterable[CapitolTradeSignal],
) -> str:
    sectors = {s.sector for s in sec_signals} | {t.sector for t in capitol_signals}
    if not sectors:
        return "_No sector overlap to report this cycle._"
    rows = ["| Sector | Committees with overlapping jurisdiction |",
            "|---|---|"]
    for sector in sorted(sectors):
        committees = SECTOR_TO_COMMITTEES.get(sector, [])
        rows.append(
            f"| {sector} | "
            f"{', '.join(committees) if committees else '_no mapping_'} |"
        )
    return "\n".join(rows)


def _format_watchlist_table(
    sec_signals: Iterable[SecCyberSignal],
    capitol_signals: Iterable[CapitolTradeSignal],
) -> str:
    by_ticker: dict[str, dict] = {}
    for s in sec_signals:
        by_ticker.setdefault(s.ticker, {
            "company": s.company,
            "sector": s.sector,
            "sec": False,
            "capitol": False,
        })["sec"] = True
    for t in capitol_signals:
        by_ticker.setdefault(t.ticker, {
            "company": t.company,
            "sector": t.sector,
            "sec": False,
            "capitol": False,
        })["capitol"] = True

    if not by_ticker:
        return "_Watchlist is empty this cycle._"

    rows = [
        "| Ticker | Company | Sector | SEC Cyber Signal | Capitol Trade Signal |",
        "|---|---|---|---|---|",
    ]
    for ticker in sorted(by_ticker):
        info = by_ticker[ticker]
        rows.append(
            f"| {ticker} | {info['company']} | {info['sector']} | "
            f"{'Yes' if info['sec'] else 'No'} | "
            f"{'Yes' if info['capitol'] else 'No'} |"
        )
    return "\n".join(rows)


def _format_source_links(
    sec_signals: Iterable[SecCyberSignal],
    capitol_signals: Iterable[CapitolTradeSignal],
) -> str:
    lines: List[str] = []
    for s in sec_signals:
        lines.append(f"- {s.company} ({s.ticker}) {s.filing_type}: <{s.source_url}>")
    for t in capitol_signals:
        lines.append(
            f"- {t.filer} PTR for {t.ticker}: <{t.source_url}>"
        )
    return "\n".join(lines) if lines else "_No sources this cycle._"


def build_post(
    post_date: date,
    sec_signals: List[SecCyberSignal],
    capitol_signals: List[CapitolTradeSignal],
) -> str:
    """Return the full Patreon-ready markdown post as a string."""
    title = f"DrZeroTrust Market Signal Watch — {post_date.isoformat()}"

    teaser = (
        "A quick scan of where publicly disclosed cyber-incident filings "
        "and publicly disclosed Capitol Hill trades are pointing this "
        "week. Educational only — no recommendations, no allegations."
    )

    executive_summary = (
        f"This cycle surfaces {len(sec_signals)} SEC cyber-incident "
        f"disclosure(s) and {len(capitol_signals)} Capitol Hill "
        "transaction disclosure(s). We map the sectors involved to the "
        "congressional committees whose jurisdiction overlaps with those "
        "industries, and consolidate everything into a single watchlist "
        "for your own further research."
    )

    caveats = (
        "- All signals are sourced from public regulatory filings.\n"
        "- Capitol Hill trades are disclosed in **ranges**, not exact amounts.\n"
        "- Sector-to-committee mapping is a heuristic context cue, not a "
        "claim about any specific filer.\n"
        "- This post does **not** allege insider trading or any other "
        "misconduct.\n"
        "- V1 of this system is generated from **mock data** for format "
        "validation."
    )

    sections = [
        f"# {title}",
        "",
        f"_{teaser}_",
        "",
        "## Executive Summary",
        executive_summary,
        "",
        "## SEC Cyber Incident Signals",
        _format_sec_section(sec_signals),
        "",
        "## Capitol Hill Trade Signals",
        _format_capitol_section(capitol_signals),
        "",
        "## Sector-to-Committee Relevance",
        _format_relevance_section(sec_signals, capitol_signals),
        "",
        "## Watchlist",
        _format_watchlist_table(sec_signals, capitol_signals),
        "",
        "## Source Links",
        _format_source_links(sec_signals, capitol_signals),
        "",
        "## Caveats",
        caveats,
        "",
        "---",
        DISCLAIMER,
        "",
    ]
    return "\n".join(sections)


def output_filename(post_date: date) -> str:
    return f"drzerotrust-market-signal-watch-{post_date.isoformat()}.md"
