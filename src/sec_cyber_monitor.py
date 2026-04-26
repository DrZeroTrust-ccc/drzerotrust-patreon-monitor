"""Mock SEC cyber-incident signal source.

V1 returns a hard-coded list of fictional 8-K Item 1.05 style cyber
incident disclosures. No network calls are made. No real filings are
fetched. The shape of the returned data mirrors what a future EDGAR
ingestion layer is expected to produce.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List


@dataclass(frozen=True)
class SecCyberSignal:
    company: str
    ticker: str
    sector: str
    filing_type: str           # e.g. "8-K Item 1.05"
    filed_at: str              # ISO date string
    summary: str
    source_url: str            # link to the public filing (mock)

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_recent_signals() -> List[SecCyberSignal]:
    """Return a deterministic list of mock SEC cyber-incident signals."""
    return [
        SecCyberSignal(
            company="Acme Health Systems Inc.",
            ticker="ACME",
            sector="Healthcare",
            filing_type="8-K Item 1.05",
            filed_at="2026-04-22",
            summary=(
                "Disclosed a cybersecurity incident affecting an internal "
                "scheduling system. Investigation ongoing; no material "
                "financial impact reported at time of filing."
            ),
            source_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000000000&type=8-K",
        ),
        SecCyberSignal(
            company="Northwind Logistics Corp.",
            ticker="NWLG",
            sector="Industrials / Logistics",
            filing_type="8-K Item 1.05",
            filed_at="2026-04-23",
            summary=(
                "Reported unauthorized access to a third-party freight "
                "tracking vendor. Containment in progress; operational "
                "impact described as limited."
            ),
            source_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000000001&type=8-K",
        ),
        SecCyberSignal(
            company="Beacon Federal Cloud, Inc.",
            ticker="BFCL",
            sector="Technology / Government Cloud",
            filing_type="8-K Item 1.05",
            filed_at="2026-04-24",
            summary=(
                "Notified investors of a security incident touching a "
                "non-classified federal customer environment. Company "
                "states no evidence of customer data exfiltration."
            ),
            source_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000000002&type=8-K",
        ),
    ]
