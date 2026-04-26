"""Mock Capitol Hill trade signal source.

V1 returns a hard-coded list of fictional Periodic Transaction Report
(PTR) style entries. No network calls are made. No real disclosures
are fetched.

Important: this module returns disclosed transactions only. It does
NOT make, imply, or support any allegation of insider trading or
misconduct. PTR filings are publicly disclosed under the STOCK Act
and are presented here purely as public-record signals.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List


@dataclass(frozen=True)
class CapitolTradeSignal:
    filer: str                 # e.g. "Rep. Jane Doe (Mock)"
    chamber: str               # "House" or "Senate"
    committee: str             # primary committee assignment relevant here
    ticker: str
    company: str
    sector: str
    transaction_type: str      # "Purchase" / "Sale" / "Exchange"
    amount_range: str          # PTRs are disclosed in ranges
    transaction_date: str      # ISO date
    disclosure_date: str       # ISO date
    source_url: str            # link to the public PTR filing (mock)

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_recent_signals() -> List[CapitolTradeSignal]:
    """Return a deterministic list of mock Capitol Hill trade signals."""
    return [
        CapitolTradeSignal(
            filer="Rep. Jane Doe (Mock)",
            chamber="House",
            committee="Energy and Commerce",
            ticker="ACME",
            company="Acme Health Systems Inc.",
            sector="Healthcare",
            transaction_type="Purchase",
            amount_range="$15,001 - $50,000",
            transaction_date="2026-04-15",
            disclosure_date="2026-04-21",
            source_url="https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure",
        ),
        CapitolTradeSignal(
            filer="Sen. John Roe (Mock)",
            chamber="Senate",
            committee="Armed Services",
            ticker="BFCL",
            company="Beacon Federal Cloud, Inc.",
            sector="Technology / Government Cloud",
            transaction_type="Sale",
            amount_range="$50,001 - $100,000",
            transaction_date="2026-04-18",
            disclosure_date="2026-04-22",
            source_url="https://efdsearch.senate.gov/search/",
        ),
        CapitolTradeSignal(
            filer="Rep. Pat Example (Mock)",
            chamber="House",
            committee="Transportation and Infrastructure",
            ticker="NWLG",
            company="Northwind Logistics Corp.",
            sector="Industrials / Logistics",
            transaction_type="Purchase",
            amount_range="$1,001 - $15,000",
            transaction_date="2026-04-19",
            disclosure_date="2026-04-23",
            source_url="https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure",
        ),
    ]
