"""Assembles a Patreon-ready DrZeroTrust briefing from mock signals.

The generator is pure: given lists of signals and a date, it returns
a markdown string. Persisting the file is the caller's responsibility.

Voice: sharp, clear, analytical, practical. Cybersecurity-meets-
market-intelligence. No hype, no fearmongering, no buy/sell calls,
no allegations of insider trading or other misconduct.
"""

from __future__ import annotations

from datetime import date
from typing import Iterable, List, Tuple

from .capitol_trades_monitor import CapitolTradeSignal
from .sec_cyber_monitor import SecCyberSignal


# Sector context. The "why" column is intentionally generic — it
# describes the *committee jurisdiction*, not any specific filer.
SECTOR_CONTEXT: dict[str, dict] = {
    "Healthcare": {
        "committees": [
            "House Energy and Commerce",
            "Senate Health, Education, Labor, and Pensions",
        ],
        "why": (
            "These committees own health-data privacy, HHS/CMS oversight, "
            "and Medicare reimbursement policy — the fastest path from a "
            "cyber event to a P&L impact in healthcare."
        ),
    },
    "Industrials / Logistics": {
        "committees": [
            "House Transportation and Infrastructure",
            "Senate Commerce, Science, and Transportation",
        ],
        "why": (
            "These committees handle freight, surface transport, and "
            "supply-chain resilience policy — directly adjacent to "
            "logistics-sector cyber risk."
        ),
    },
    "Technology / Government Cloud": {
        "committees": [
            "House Armed Services",
            "Senate Armed Services",
            "House Oversight and Accountability",
        ],
        "why": (
            "These committees shape DoD IT modernization, FedRAMP "
            "expectations, and federal cyber-incident reporting — the "
            "policy surface that prices government-cloud names."
        ),
    },
}


DISCLAIMER = (
    "**Not investment advice.** This briefing is an educational summary of "
    "publicly available regulatory filings. Nothing here is a recommendation "
    "to buy, sell, or hold any security. No statement in this post alleges "
    "insider trading, market manipulation, or any other misconduct by any "
    "person or entity. Always do your own research and consult a licensed "
    "financial professional before acting."
)


_PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}


def _priority_rank(priority: str) -> int:
    return _PRIORITY_RANK.get(priority.lower(), 0)


def _max_priority(priorities: Iterable[str]) -> str:
    items = [p for p in priorities if p]
    if not items:
        return "Medium"
    return max(items, key=_priority_rank)


# ---------- section builders ----------


def _build_opening_note() -> str:
    return (
        "This briefing tracks **public disclosures** that may carry "
        "market-relevant cyber, policy, and governance signals. The goal is "
        "not prediction — it is **convergence-watching**: identifying names "
        "where SEC cyber-incident filings, congressional financial "
        "disclosures, and committee jurisdiction line up at the same time. "
        "Treat each item below as a research prompt, not a conclusion."
    )


def _build_bluf(
    sec_signals: List[SecCyberSignal],
    capitol_signals: List[CapitolTradeSignal],
) -> str:
    bullets: List[str] = []

    bullets.append(
        f"**{len(sec_signals)} SEC cyber-incident disclosure(s)** and "
        f"**{len(capitol_signals)} Capitol Hill transaction disclosure(s)** "
        "cleared the public record this cycle."
    )

    overlap = sorted(
        {s.ticker for s in sec_signals} & {t.ticker for t in capitol_signals}
    )
    if overlap:
        bullets.append(
            f"**{len(overlap)} ticker(s) appear on both lists** — "
            f"{', '.join(overlap)} — meaning cyber, policy, and market "
            "signals stack on the same name in the same window."
        )

    high_count = sum(1 for s in sec_signals if s.priority.lower() == "high")
    high_count += sum(1 for t in capitol_signals if t.priority.lower() == "high")
    if high_count:
        bullets.append(
            f"**{high_count} signal(s) flagged High priority** based on "
            "filing severity, committee-jurisdiction overlap, or both."
        )

    sectors = sorted(
        {s.sector for s in sec_signals} | {t.sector for t in capitol_signals}
    )
    if sectors:
        bullets.append(
            "**Sector exposure this cycle:** " + ", ".join(sectors) + "."
        )

    bullets.append(
        "Public disclosures are signals, not verdicts. Use them to direct "
        "research, not to draw conclusions about any individual or entity."
    )

    return "\n".join(f"- {b}" for b in bullets[:5])


def _watchlist_rows(
    sec_signals: List[SecCyberSignal],
    capitol_signals: List[CapitolTradeSignal],
) -> List[Tuple[str, str, str, str, str]]:
    """Return one row per ticker: (signal, entity, ticker, why, priority)."""
    by_ticker: dict[str, dict] = {}
    for s in sec_signals:
        entry = by_ticker.setdefault(s.ticker, {
            "company": s.company,
            "sector": s.sector,
            "sec": None,
            "capitol": None,
        })
        entry["sec"] = s
    for t in capitol_signals:
        entry = by_ticker.setdefault(t.ticker, {
            "company": t.company,
            "sector": t.sector,
            "sec": None,
            "capitol": None,
        })
        entry["capitol"] = t

    rows: List[Tuple[str, str, str, str, str]] = []
    for ticker, info in by_ticker.items():
        sec = info["sec"]
        cap = info["capitol"]
        if sec and cap:
            signal = "Cyber + Policy"
            why = (
                f"SEC {sec.filing_type} {sec.filing_item} disclosure overlaps "
                f"with a {cap.transaction_type.lower()} from a filer on "
                f"{cap.committee}."
            )
        elif sec:
            signal = "Cyber"
            why = (
                f"SEC {sec.filing_type} {sec.filing_item} disclosure in "
                f"{sec.sector}."
            )
        else:
            signal = "Policy"
            why = (
                f"{cap.transaction_type} disclosed by a filer on "
                f"{cap.committee}, sector {cap.sector}."
            )
        priority = _max_priority(
            [sec.priority if sec else "", cap.priority if cap else ""]
        )
        rows.append((signal, info["company"], ticker, why, priority))

    rows.sort(key=lambda r: (-_priority_rank(r[4]), r[2]))
    return rows


def _build_watchlist_table(
    sec_signals: List[SecCyberSignal],
    capitol_signals: List[CapitolTradeSignal],
) -> str:
    rows = _watchlist_rows(sec_signals, capitol_signals)
    if not rows:
        return "_No watchlist entries this cycle._"

    out = [
        "| Signal | Entity | Ticker | Why It Matters | Watch Priority |",
        "|---|---|---|---|---|",
    ]
    for signal, entity, ticker, why, priority in rows:
        out.append(f"| {signal} | {entity} | {ticker} | {why} | {priority} |")
    return "\n".join(out)


def _build_sec_section(signals: List[SecCyberSignal]) -> str:
    if not signals:
        return "_No SEC cyber-incident signals this cycle._"
    blocks: List[str] = []
    for s in signals:
        blocks.append(
            f"### {s.company} ({s.ticker}) — Watch Priority: {s.priority}\n"
            f"- **Filing:** {s.filing_type} {s.filing_item}, filed {s.filed_at}\n"
            f"- **Sector:** {s.sector}\n"
            f"- **Incident summary:** {s.summary}\n"
            f"- **Market relevance:** {s.market_relevance}\n"
            f"- **What to watch next:** {s.what_to_watch_next}\n"
            f"- **Source:** <{s.source_url}>"
        )
    return "\n\n".join(blocks)


def _build_capitol_section(signals: List[CapitolTradeSignal]) -> str:
    if not signals:
        return "_No Capitol Hill trade disclosures this cycle._"
    blocks: List[str] = []
    for t in signals:
        blocks.append(
            f"### {t.filer} — Watch Priority: {t.priority}\n"
            f"- **Role:** {t.role} ({t.chamber})\n"
            f"- **Asset:** {t.company} ({t.ticker}) — {t.sector}\n"
            f"- **Transaction type:** {t.transaction_type}\n"
            f"- **Amount range:** {t.amount_range}\n"
            f"- **Transaction date:** {t.transaction_date} | "
            f"**Disclosed:** {t.disclosure_date}\n"
            f"- **Committee relevance:** {t.committee} — {t.committee_relevance}\n"
            f"- **Market relevance:** {t.market_relevance}\n"
            f"- **What to watch next:** {t.what_to_watch_next}\n"
            f"- **Source:** <{t.source_url}>"
        )
    return "\n\n".join(blocks)


def _build_conflict_lens(
    sec_signals: List[SecCyberSignal],
    capitol_signals: List[CapitolTradeSignal],
) -> str:
    intro = (
        "**Why this lens?** Members of Congress sit on committees with "
        "jurisdiction over specific industries. When a cyber incident hits "
        "a sector and a public financial disclosure from a filer on the "
        "overseeing committee surfaces in the same window, the **public "
        "record itself** has produced a research-worthy data point. This "
        "lens does not imply intent, knowledge, or wrongdoing — it simply "
        "maps where jurisdiction and market exposure intersect."
    )

    sectors = sorted(
        {s.sector for s in sec_signals} | {t.sector for t in capitol_signals}
    )
    if not sectors:
        return intro + "\n\n_No sector overlap to map this cycle._"

    rows = [
        "| Sector | Relevant Committees | Why It Matters |",
        "|---|---|---|",
    ]
    for sector in sectors:
        ctx = SECTOR_CONTEXT.get(sector)
        committees = ", ".join(ctx["committees"]) if ctx else "_no mapping_"
        why = ctx["why"] if ctx else "_no mapping_"
        rows.append(f"| {sector} | {committees} | {why} |")
    return intro + "\n\n" + "\n".join(rows)


def _build_source_links(
    sec_signals: List[SecCyberSignal],
    capitol_signals: List[CapitolTradeSignal],
) -> str:
    lines: List[str] = []
    for s in sec_signals:
        lines.append(
            f"- {s.company} ({s.ticker}) {s.filing_type} {s.filing_item}: "
            f"<{s.source_url}>"
        )
    for t in capitol_signals:
        lines.append(f"- {t.filer} PTR for {t.ticker}: <{t.source_url}>")
    return "\n".join(lines) if lines else "_No sources this cycle._"


def _build_research_caveats() -> str:
    return (
        "- **Congressional disclosures lag the trade date.** PTR filings are "
        "due within a window after the transaction; the disclosure date is "
        "not the trade date.\n"
        "- **SEC cyber filings can be amended.** An initial 8-K Item 1.05 is "
        "frequently followed by an 8-K/A as scope and impact are clarified.\n"
        "- **Public disclosures are signals, not proof of wrongdoing.** "
        "Nothing in this briefing alleges insider trading or any other "
        "misconduct by any person or entity.\n"
        "- **This is not investment advice.** Use this briefing to direct "
        "your own research, not to make trading decisions."
    )


def _build_closing_note() -> str:
    return (
        "The point of this briefing is **public-signal convergence** — the "
        "places where cyber-incident disclosure, congressional financial "
        "activity, and committee jurisdiction line up in the same name at "
        "the same time. Convergence is not causation. It is a research "
        "prompt: a place to read more carefully, ask sharper questions, and "
        "let the public record inform your own thinking. — *DrZeroTrust*"
    )


# ---------- top-level builder ----------


def build_post(
    post_date: date,
    sec_signals: List[SecCyberSignal],
    capitol_signals: List[CapitolTradeSignal],
) -> str:
    """Return the full Patreon-ready DrZeroTrust briefing as markdown."""
    title = f"DrZeroTrust Market Signal Watch — {post_date.isoformat()}"

    sections = [
        f"# {title}",
        "",
        _build_opening_note(),
        "",
        "## Bottom Line Up Front",
        _build_bluf(sec_signals, capitol_signals),
        "",
        "## High-Priority Watchlist",
        _build_watchlist_table(sec_signals, capitol_signals),
        "",
        "## SEC Cyber Incident Signals",
        _build_sec_section(sec_signals),
        "",
        "## Capitol Hill Trade Signals",
        _build_capitol_section(capitol_signals),
        "",
        "## Sector-to-Committee Conflict Lens",
        _build_conflict_lens(sec_signals, capitol_signals),
        "",
        "## Source Links",
        _build_source_links(sec_signals, capitol_signals),
        "",
        "## Research Caveats",
        _build_research_caveats(),
        "",
        "## Closing Note",
        _build_closing_note(),
        "",
        "---",
        DISCLAIMER,
        "",
    ]
    return "\n".join(sections)


def output_filename(post_date: date) -> str:
    return f"drzerotrust-market-signal-watch-{post_date.isoformat()}.md"
