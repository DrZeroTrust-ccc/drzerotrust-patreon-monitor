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
    filer: str                  # e.g. "Rep. Jane Doe (Mock)"
    role: str                   # "U.S. Representative" / "U.S. Senator"
    chamber: str                # "House" or "Senate"
    committee: str              # primary committee assignment relevant here
    committee_relevance: str    # plain-language note on jurisdiction overlap
    ticker: str
    company: str
    sector: str
    transaction_type: str       # "Purchase" / "Sale" / "Exchange"
    amount_range: str           # PTRs are disclosed in ranges
    transaction_date: str       # ISO date
    disclosure_date: str        # ISO date
    market_relevance: str       # why this matters to a markets reader
    what_to_watch_next: str     # the follow-on signal to track
    priority: str               # "High" / "Medium" / "Low"
    source_url: str             # link to the public PTR filing (mock)

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_recent_signals() -> List[CapitolTradeSignal]:
    """Return a deterministic list of mock Capitol Hill trade signals."""
    return [
        CapitolTradeSignal(
            filer="Rep. Jane Doe (Mock)",
            role="U.S. Representative",
            chamber="House",
            committee="Energy and Commerce",
            committee_relevance=(
                "Energy and Commerce holds primary jurisdiction over health "
                "data privacy, HHS oversight, and Medicare reimbursement "
                "rules — all directly downstream of healthcare cyber events."
            ),
            ticker="ACME",
            company="Acme Health Systems Inc.",
            sector="Healthcare",
            transaction_type="Purchase",
            amount_range="$15,001 - $50,000",
            transaction_date="2026-04-15",
            disclosure_date="2026-04-21",
            market_relevance=(
                "A disclosed purchase in a healthcare name during a period of "
                "active sector cyber incidents is the kind of public-record "
                "data point that belongs on a research watchlist, regardless "
                "of intent."
            ),
            what_to_watch_next=(
                "Watch for follow-on PTRs from the same filer in adjacent "
                "healthcare names and any committee hearings touching health "
                "data security in the next 60 days."
            ),
            priority="High",
            source_url="https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure",
        ),
        CapitolTradeSignal(
            filer="Sen. John Roe (Mock)",
            role="U.S. Senator",
            chamber="Senate",
            committee="Armed Services",
            committee_relevance=(
                "Senate Armed Services oversees DoD IT modernization and the "
                "federal cloud customer base, putting it close to the policy "
                "surface for government-cloud vendors."
            ),
            ticker="BFCL",
            company="Beacon Federal Cloud, Inc.",
            sector="Technology / Government Cloud",
            transaction_type="Sale",
            amount_range="$50,001 - $100,000",
            transaction_date="2026-04-18",
            disclosure_date="2026-04-22",
            market_relevance=(
                "A disclosed sale in a government-cloud name during a window "
                "of FedRAMP-relevant cyber disclosure is a signal worth "
                "logging — not a verdict, just a data point."
            ),
            what_to_watch_next=(
                "Watch for any classified or unclassified hearings on federal "
                "cloud security posture, CISA advisories naming the vendor, "
                "and subsequent PTRs in adjacent gov-cloud peers."
            ),
            priority="High",
            source_url="https://efdsearch.senate.gov/search/",
        ),
        CapitolTradeSignal(
            filer="Rep. Pat Example (Mock)",
            role="U.S. Representative",
            chamber="House",
            committee="Transportation and Infrastructure",
            committee_relevance=(
                "Transportation and Infrastructure handles freight, surface "
                "transport, and supply-chain resilience — adjacent to "
                "logistics-sector cyber risk."
            ),
            ticker="NWLG",
            company="Northwind Logistics Corp.",
            sector="Industrials / Logistics",
            transaction_type="Purchase",
            amount_range="$1,001 - $15,000",
            transaction_date="2026-04-19",
            disclosure_date="2026-04-23",
            market_relevance=(
                "A small disclosed purchase in a logistics name during a "
                "sector cyber event maps neatly onto the filer's committee "
                "remit. Belongs on the watchlist; does not imply intent."
            ),
            what_to_watch_next=(
                "Watch for committee hearings on supply-chain cyber, any "
                "follow-on PTRs in freight peers, and the company's next "
                "10-Q risk-factor language."
            ),
            priority="Medium",
            source_url="https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure",
        ),
    ]
