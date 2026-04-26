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
    filing_type: str           # "8-K"
    filing_item: str           # "Item 1.05"
    filed_at: str              # ISO date string
    summary: str               # plain-language summary of the disclosure
    market_relevance: str      # why this matters to a markets reader
    what_to_watch_next: str    # the follow-on signal to track
    priority: str              # "High" / "Medium" / "Low"
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
            filing_type="8-K",
            filing_item="Item 1.05",
            filed_at="2026-04-22",
            summary=(
                "Disclosed a cybersecurity incident affecting an internal "
                "patient-scheduling system. Investigation is ongoing and the "
                "filing states no material financial impact has been determined."
            ),
            market_relevance=(
                "Healthcare cyber events frequently move in waves: an initial "
                "8-K is often followed by an amended filing once scope is "
                "better understood. Reimbursement-sensitive operators tend to "
                "see knock-on effects in claims processing and revenue cycle."
            ),
            what_to_watch_next=(
                "Look for an 8-K/A within 30-60 days, any HHS OCR breach-portal "
                "entry, and whether the next 10-Q quantifies remediation spend."
            ),
            priority="High",
            source_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000000000&type=8-K",
        ),
        SecCyberSignal(
            company="Northwind Logistics Corp.",
            ticker="NWLG",
            sector="Industrials / Logistics",
            filing_type="8-K",
            filing_item="Item 1.05",
            filed_at="2026-04-23",
            summary=(
                "Reported unauthorized access at a third-party freight-tracking "
                "vendor. Containment is in progress and the company describes "
                "operational impact as limited at the time of filing."
            ),
            market_relevance=(
                "Third-party / supply-chain incidents in freight tend to "
                "produce delayed earnings drag rather than headline shocks. "
                "Watch for vendor concentration disclosures and any contract "
                "renegotiation language in subsequent filings."
            ),
            what_to_watch_next=(
                "Look for vendor-naming in the next 10-Q risk factors and any "
                "guidance commentary on logistics throughput in the next "
                "earnings call."
            ),
            priority="Medium",
            source_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000000001&type=8-K",
        ),
        SecCyberSignal(
            company="Beacon Federal Cloud, Inc.",
            ticker="BFCL",
            sector="Technology / Government Cloud",
            filing_type="8-K",
            filing_item="Item 1.05",
            filed_at="2026-04-24",
            summary=(
                "Notified investors of a security incident touching a "
                "non-classified federal customer environment. The company "
                "states there is no current evidence of customer data "
                "exfiltration."
            ),
            market_relevance=(
                "Government-cloud names trade on certification posture as "
                "much as on revenue. Even a contained incident can pressure "
                "FedRAMP renewal timing, and that lands directly on forward "
                "bookings."
            ),
            what_to_watch_next=(
                "Track any CISA advisory referencing the affected service, "
                "FedRAMP status changes, and federal customer renewal "
                "announcements over the next two quarters."
            ),
            priority="High",
            source_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000000002&type=8-K",
        ),
    ]
