"""Tests for the live-mode SEC cyber-incident classifier.

These tests use saved fixture filings — no live SEC calls are made.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.sec_cyber_monitor import (
    LiveFetchResult,
    SecCyberSignal,
    classify_filing,
    fetch_live_signals,
)


FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _classify(name: str, *, form: str = "8-K", **overrides) -> SecCyberSignal | None:
    defaults = dict(
        form=form,
        company="Test Co.",
        cik="0009999991",
        ticker="TEST",
        accession="0009999991-26-000001",
        filing_date="2026-04-25",
        sec_url="https://www.sec.gov/Archives/edgar/data/9999991/000999999126000001/test-index.htm",
    )
    defaults.update(overrides)
    return classify_filing(_load(name), **defaults)


# ---------- positive cases ----------


def test_item_105_ransomware_classifies_high():
    sig = _classify("8k_item_105_ransomware.html")
    assert sig is not None
    assert sig.item_number == "1.05"
    assert sig.is_amendment is False
    assert sig.priority == "High"
    assert sig.incident_type.lower().startswith("ransomware")
    assert "exfiltrat" in sig.impact_status.lower() or \
        "operational" in sig.impact_status.lower() or \
        "customer" in sig.impact_status.lower()
    assert "material impact" in sig.materiality_status.lower() or \
        "forward-looking material-impact" in sig.materiality_status.lower()
    assert sig.summary  # non-empty
    assert sig.quoted_excerpt
    assert sig.market_relevance
    assert sig.what_to_watch_next


def test_item_105_no_material_impact_classifies_low():
    sig = _classify("8k_item_105_no_material_impact.html")
    assert sig is not None
    assert sig.item_number == "1.05"
    assert sig.priority == "Low"
    assert "no material impact" in sig.materiality_status.lower()


def test_item_801_with_cyber_language_classifies_medium():
    sig = _classify("8k_item_801_cyber.html")
    assert sig is not None
    assert sig.item_number == "8.01"
    assert sig.priority == "Medium"


def test_8ka_amendment_classifies_high_and_marks_amendment():
    sig = _classify("8ka_amendment.html", form="8-K/A")
    assert sig is not None
    assert sig.is_amendment is True
    assert sig.filing_type == "8-K/A"
    assert sig.priority == "High"
    assert "exfiltrat" in sig.incident_type.lower()


# ---------- negative cases ----------


def test_generic_risk_factor_filing_is_rejected():
    assert _classify("8k_risk_factor_only.html") is None


def test_periodic_filings_are_rejected_by_form():
    assert _classify("8k_item_105_ransomware.html", form="10-K") is None
    assert _classify("8k_item_105_ransomware.html", form="10-Q") is None
    assert _classify("8k_item_105_ransomware.html", form="S-1") is None
    assert _classify("8k_item_105_ransomware.html", form="DEF 14A") is None


def test_filing_with_no_items_is_rejected():
    text = "<html><body>This filing contains no Item headers at all.</body></html>"
    assert classify_filing(
        text, form="8-K", company="X", cik="1", ticker="X",
        accession="a", filing_date="2026-04-25", sec_url="https://x",
    ) is None


# ---------- live fetch error paths (no network) ----------


def test_fetch_live_signals_requires_user_agent():
    result = fetch_live_signals(user_agent="")
    assert isinstance(result, LiveFetchResult)
    assert result.error is not None
    assert "SEC_USER_AGENT" in result.error
    assert result.signals == []


def test_fetch_live_signals_handles_search_failure(monkeypatch):
    """Simulate a network/EDGAR failure — function should return cleanly."""

    def boom(*_args, **_kwargs):
        raise RuntimeError("simulated EDGAR outage")

    monkeypatch.setattr("src.sec_cyber_monitor._search_efts", boom)

    result = fetch_live_signals(user_agent="DrZeroTrust Test test@example.com")
    assert result.error is not None
    assert "simulated EDGAR outage" in result.error
    assert result.signals == []
