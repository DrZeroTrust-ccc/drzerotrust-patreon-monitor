"""SEC cyber-incident signal source.

Two modes:

- **Mock** (default): a fixed list of fictional disclosures. No network.
  Used by `python -m src.main` and by every unit test.

- **Live** (`--sec-real`): pulls Form 8-K and 8-K/A filings from SEC
  EDGAR full-text search over a recent window, fetches each
  candidate's primary document, and applies a content filter that
  requires either an explicit *Item 1.05* heading or *Item 8.01*
  paired with specific-incident language. Generic cybersecurity
  governance / risk-factor language is rejected.

Live mode uses public SEC endpoints and is read-only. SEC fair-access
rules require a descriptive `User-Agent`; set `SEC_USER_AGENT` in your
environment.

This module never asserts that a breach occurred unless the filing
text says so. The output is public-signal research, not a verdict
about any company or person.
"""

from __future__ import annotations

import html as html_lib
import json
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional

try:
    import requests
except ImportError:  # pragma: no cover - dependency missing only at install time
    requests = None  # type: ignore[assignment]


EFTS_URL = "https://efts.sec.gov/LATEST/search-index"
ARCHIVE_BASE = "https://www.sec.gov/Archives/edgar/data"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# Phrases that nominate a filing as a candidate for content review.
CYBER_INDICATORS = [
    "Item 1.05",
    "Material Cybersecurity Incident",
    "cybersecurity incident",
    "cyber incident",
    "data breach",
    "security incident",
    "unauthorized access",
    "unauthorized activity",
    "ransomware",
    "malware",
    "network intrusion",
    "threat actor",
    "exfiltration",
    "encrypted systems",
    "business interruption",
    "operational disruption",
    "customer data",
    "personal information",
    "law enforcement",
    "forensic investigation",
    "material impact",
    "reasonably likely material impact",
]

# At least one of these must appear in the relevant Item section for
# Item 8.01 filings (and to confirm Item 1.05 disclosures are about
# an actual incident, not a procedural reference).
SPECIFIC_INCIDENT_KEYWORDS = [
    "ransomware",
    "malware",
    "unauthorized access",
    "unauthorized activity",
    "network intrusion",
    "threat actor",
    "exfiltration",
    "encrypted systems",
    "data breach",
    "security incident",
    "operational disruption",
    "business interruption",
    "cybersecurity incident",
    "cyber incident",
    "customer data",
    "personal information",
]

HIGH_PRIORITY_KEYWORDS = [
    "ransomware",
    "exfiltration",
    "exfiltrated",
    "operational disruption",
    "business interruption",
    "encrypted systems",
    "customer data",
    "personal information",
    "material impact",
    "material adverse",
    "financial impact",
]

LOW_PRIORITY_MARKERS = [
    "no material impact",
    "not material",
    "no material adverse",
    "limited impact",
    "no current evidence",
    "not reasonably likely to be material",
    "no evidence of material",
]

ITEM_HEADER_RE = re.compile(r"Item\s+(\d+\.\d+)\b", re.IGNORECASE)


# ---------- dataclass ----------


@dataclass(frozen=True)
class SecCyberSignal:
    company: str
    ticker: str                # may be empty when EDGAR has no mapping
    cik: str
    sector: str                # may be empty in live mode (no SIC enrichment yet)
    filing_type: str           # "8-K" or "8-K/A"
    filing_date: str           # ISO date string
    accession_number: str
    sec_url: str
    item_number: str           # "1.05" / "8.01"
    is_amendment: bool
    incident_type: str
    summary: str
    quoted_excerpt: str
    materiality_status: str
    impact_status: str
    market_relevance: str
    what_to_watch_next: str
    priority: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LiveFetchResult:
    signals: List[SecCyberSignal] = field(default_factory=list)
    candidates_examined: int = 0
    rejected: int = 0
    rejected_reasons: dict[str, int] = field(default_factory=dict)
    window_start: str = ""
    window_end: str = ""
    error: Optional[str] = None


# ---------- mock signals (unchanged behavior) ----------


def fetch_recent_signals() -> List[SecCyberSignal]:
    """Return a deterministic list of mock SEC cyber-incident signals."""
    return [
        SecCyberSignal(
            company="Acme Health Systems Inc.",
            ticker="ACME",
            cik="0000000000",
            sector="Healthcare",
            filing_type="8-K",
            filing_date="2026-04-22",
            accession_number="0000000000-26-000001",
            sec_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000000000&type=8-K",
            item_number="1.05",
            is_amendment=False,
            incident_type="Cybersecurity incident (sector: healthcare)",
            summary=(
                "Disclosed a cybersecurity incident affecting an internal "
                "patient-scheduling system. Investigation is ongoing and the "
                "filing states no material financial impact has been "
                "determined."
            ),
            quoted_excerpt=(
                "...the Company identified a cybersecurity incident affecting "
                "an internal patient-scheduling system..."
            ),
            materiality_status="Unspecified at filing",
            impact_status="Operational impact unspecified",
            market_relevance=(
                "Healthcare cyber events frequently move in waves: an "
                "initial 8-K is often followed by an amended filing once "
                "scope is better understood. Reimbursement-sensitive "
                "operators tend to see knock-on effects in claims processing "
                "and revenue cycle."
            ),
            what_to_watch_next=(
                "Look for an 8-K/A within 30-60 days, any HHS OCR "
                "breach-portal entry, and whether the next 10-Q quantifies "
                "remediation spend."
            ),
            priority="High",
        ),
        SecCyberSignal(
            company="Northwind Logistics Corp.",
            ticker="NWLG",
            cik="0000000001",
            sector="Industrials / Logistics",
            filing_type="8-K",
            filing_date="2026-04-23",
            accession_number="0000000001-26-000001",
            sec_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000000001&type=8-K",
            item_number="1.05",
            is_amendment=False,
            incident_type="Third-party / supply-chain cyber incident",
            summary=(
                "Reported unauthorized access at a third-party "
                "freight-tracking vendor. Containment is in progress and the "
                "company describes operational impact as limited at the time "
                "of filing."
            ),
            quoted_excerpt=(
                "...unauthorized access at a third-party freight-tracking "
                "vendor; containment is ongoing..."
            ),
            materiality_status="Limited impact claimed",
            impact_status="Operational impact described as limited",
            market_relevance=(
                "Third-party / supply-chain incidents in freight tend to "
                "produce delayed earnings drag rather than headline shocks. "
                "Watch for vendor concentration disclosures and any contract "
                "renegotiation language in subsequent filings."
            ),
            what_to_watch_next=(
                "Look for vendor-naming in the next 10-Q risk factors and "
                "any guidance commentary on logistics throughput in the next "
                "earnings call."
            ),
            priority="Medium",
        ),
        SecCyberSignal(
            company="Beacon Federal Cloud, Inc.",
            ticker="BFCL",
            cik="0000000002",
            sector="Technology / Government Cloud",
            filing_type="8-K",
            filing_date="2026-04-24",
            accession_number="0000000002-26-000001",
            sec_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000000002&type=8-K",
            item_number="1.05",
            is_amendment=False,
            incident_type="Federal-customer environment cyber incident",
            summary=(
                "Notified investors of a security incident touching a "
                "non-classified federal customer environment. The company "
                "states there is no current evidence of customer data "
                "exfiltration."
            ),
            quoted_excerpt=(
                "...security incident affecting a non-classified federal "
                "customer environment; no current evidence of customer data "
                "exfiltration..."
            ),
            materiality_status="Unspecified at filing",
            impact_status="No current evidence of data exfiltration",
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
        ),
    ]


# ---------- live: text helpers ----------


def _strip_html(text: str) -> str:
    """Best-effort HTML → clean text. Keeps inline content readable."""
    # Remove style/script blocks
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text,
                  flags=re.IGNORECASE | re.DOTALL)
    # Replace tags with spaces so words don't collide
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_items(text: str) -> dict[str, str]:
    """Return {item_number: section_text}. Empty dict if none found.

    When the same Item appears more than once (e.g. once in a table of
    contents and once as the actual section body), we keep the longest
    occurrence so the body wins over the TOC stub.
    """
    matches = list(ITEM_HEADER_RE.finditer(text))
    items: dict[str, str] = {}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section = text[start:end].strip()
        existing = items.get(m.group(1), "")
        if len(section) > len(existing):
            items[m.group(1)] = section
    return items


def _has_any(text: str, needles: Iterable[str]) -> bool:
    lower = text.lower()
    return any(n.lower() in lower for n in needles)


def _detect_incident_type(section: str) -> str:
    s = section.lower()
    if "ransomware" in s:
        return "Ransomware"
    if "exfiltrat" in s:
        return "Data exfiltration"
    if "data breach" in s:
        return "Data breach"
    if "unauthorized access" in s or "unauthorized activity" in s:
        return "Unauthorized access"
    if "network intrusion" in s:
        return "Network intrusion"
    if "third-party" in s or "third party" in s or "vendor" in s:
        return "Third-party / supply-chain incident"
    if "cybersecurity incident" in s or "cyber incident" in s or "security incident" in s:
        return "Cybersecurity incident"
    return "Unspecified cyber event"


def _detect_materiality(section: str) -> str:
    s = section.lower()
    for marker in LOW_PRIORITY_MARKERS:
        if marker in s:
            return f'Filer states: "{marker}"'
    if "reasonably likely material impact" in s or "reasonably likely to be material" in s:
        return "Forward-looking material-impact language"
    if "material impact" in s or "material adverse" in s:
        return "Material impact language present"
    if "determining" in s and "material" in s:
        return "Materiality assessment ongoing"
    return "Unspecified at filing"


def _detect_impact(section: str) -> str:
    s = section.lower()
    flags: List[str] = []
    if "operational disruption" in s or "business interruption" in s:
        flags.append("operational disruption")
    if "encrypted systems" in s or "encrypt" in s and "system" in s:
        flags.append("encrypted systems")
    if "exfiltrat" in s:
        flags.append("data exfiltration")
    if "customer data" in s or "personal information" in s:
        flags.append("customer/personal data exposure")
    if "law enforcement" in s:
        flags.append("law enforcement engaged")
    if not flags:
        return "Not specified in filing"
    return "; ".join(flags)


def _summarize(section: str, max_chars: int = 280) -> str:
    section = section.strip()
    if len(section) <= max_chars:
        return section
    cut = section[:max_chars]
    # Trim back to a sentence boundary if possible
    for sep in (". ", "; ", ", "):
        idx = cut.rfind(sep)
        if idx > max_chars - 80:
            return cut[: idx + 1].strip() + " ..."
    return cut.strip() + " ..."


def _extract_excerpt(section: str, keywords: Iterable[str], window: int = 280) -> str:
    lower = section.lower()
    for kw in keywords:
        idx = lower.find(kw.lower())
        if idx >= 0:
            start = max(0, idx - 80)
            end = min(len(section), idx + window)
            excerpt = section[start:end].strip()
            if start > 0:
                excerpt = "..." + excerpt
            if end < len(section):
                excerpt = excerpt + "..."
            return excerpt
    return _summarize(section, 280)


def _classify_priority(section: str, item_number: str) -> str:
    s = section.lower()
    has_high = any(k in s for k in (k.lower() for k in HIGH_PRIORITY_KEYWORDS))
    has_low = any(m in s for m in LOW_PRIORITY_MARKERS)

    if item_number == "1.05":
        if has_high and not has_low:
            return "High"
        if has_low:
            return "Low"
        return "High"  # Item 1.05 itself is a strong signal
    # Item 8.01
    if has_high and not has_low:
        return "Medium"
    if has_low:
        return "Low"
    return "Medium"


def _derive_market_relevance(incident_type: str, impact_status: str) -> str:
    parts: List[str] = []
    itype = incident_type.lower()
    impact = impact_status.lower()
    if "ransomware" in itype:
        parts.append(
            "Ransomware events typically produce a near-term operational hit "
            "and a multi-quarter remediation tail."
        )
    if "exfiltrat" in itype or "exposure" in impact or "customer/personal" in impact:
        parts.append(
            "Customer-data exposure tends to bring regulatory follow-on "
            "(state AGs, FTC, sector regulators) that often outlasts the "
            "initial filing."
        )
    if "operational disruption" in impact:
        parts.append(
            "Operational disruption frequently shows up in the next "
            "quarterly result rather than the day-of stock reaction."
        )
    if not parts:
        parts.append(
            "Initial 8-K disclosures often get amended as scope is clarified; "
            "the first filing is the start of the disclosure arc, not the end."
        )
    return " ".join(parts)


def _derive_what_to_watch(form: str, item_number: str, is_amendment: bool) -> str:
    if is_amendment:
        return (
            "Compare the amended materiality and impact language to the "
            "original 8-K; track follow-on regulatory filings, sector-"
            "specific advisories, and any litigation docket activity."
        )
    if item_number == "1.05":
        return (
            "Watch for an 8-K/A within 30-60 days, sector-regulator "
            "advisories, and any 10-Q risk-factor or remediation-cost "
            "disclosures."
        )
    return (
        "Watch for whether the issuer escalates to an Item 1.05 filing "
        "or amends with material-impact language."
    )


# ---------- live: classifier (the testable unit) ----------


def classify_filing(
    filing_text: str,
    *,
    form: str,
    company: str,
    cik: str,
    ticker: str = "",
    accession: str,
    filing_date: str,
    sec_url: str,
) -> Optional[SecCyberSignal]:
    """Apply the content rules to a single filing.

    Returns a `SecCyberSignal` when the filing qualifies, or `None`
    when the filing is excluded (generic risk-factor language only,
    no qualifying Item, etc.).
    """
    form_upper = form.upper().strip()

    # Hard-exclude periodic / registration / proxy forms even if the caller
    # passes them in by accident.
    if any(form_upper.startswith(prefix) for prefix in
           ("10-K", "10-Q", "S-1", "DEF 14A", "PRE 14A", "DEFA14A")):
        return None

    text = _strip_html(filing_text)
    items = _extract_items(text)

    is_amendment = form_upper.endswith("/A")

    chosen_section: Optional[str] = None
    item_number: Optional[str] = None

    if "1.05" in items:
        # Item 1.05 is by definition for material cybersecurity
        # incidents, so we accept it. (We still verify there's at least
        # some incident language so we don't pass through filings whose
        # "Item 1.05" only appears in a TOC or reference.)
        section = items["1.05"]
        if _has_any(section, SPECIFIC_INCIDENT_KEYWORDS) or len(section) > 120:
            chosen_section = section
            item_number = "1.05"

    if chosen_section is None and "8.01" in items:
        section = items["8.01"]
        if _has_any(section, SPECIFIC_INCIDENT_KEYWORDS):
            chosen_section = section
            item_number = "8.01"

    if chosen_section is None or item_number is None:
        return None

    incident_type = _detect_incident_type(chosen_section)
    materiality_status = _detect_materiality(chosen_section)
    impact_status = _detect_impact(chosen_section)
    summary = _summarize(chosen_section)
    excerpt = _extract_excerpt(chosen_section, SPECIFIC_INCIDENT_KEYWORDS)
    priority = _classify_priority(chosen_section, item_number)
    market_relevance = _derive_market_relevance(incident_type, impact_status)
    what_to_watch_next = _derive_what_to_watch(form_upper, item_number, is_amendment)

    return SecCyberSignal(
        company=company,
        ticker=ticker or "",
        cik=cik,
        sector="",
        filing_type=form_upper,
        filing_date=filing_date,
        accession_number=accession,
        sec_url=sec_url,
        item_number=item_number,
        is_amendment=is_amendment,
        incident_type=incident_type,
        summary=summary,
        quoted_excerpt=excerpt,
        materiality_status=materiality_status,
        impact_status=impact_status,
        market_relevance=market_relevance,
        what_to_watch_next=what_to_watch_next,
        priority=priority,
    )


# ---------- live: HTTP client ----------


class _SecClient:
    """Tiny SEC-aware HTTP client.

    Enforces a User-Agent, paces requests (default 5 req/s), and retries
    on 429 / 5xx with exponential backoff.
    """

    def __init__(self, user_agent: str, request_delay: float = 0.2,
                 max_retries: int = 3, timeout: float = 20.0) -> None:
        if requests is None:  # pragma: no cover
            raise RuntimeError(
                "The `requests` package is required for live SEC mode. "
                "Run `pip install -r requirements.txt`."
            )
        if not user_agent or not user_agent.strip():
            raise ValueError(
                "SEC_USER_AGENT is required for live SEC mode. "
                "Set it in your environment (see .env.example)."
            )
        self._ua = user_agent.strip()
        self._delay = request_delay
        self._max_retries = max_retries
        self._timeout = timeout
        self._last_request = 0.0

    def _pace(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)

    def get(self, url: str, *, params: dict | None = None,
            accept: str = "application/json, text/html, */*") -> "requests.Response":
        headers = {
            "User-Agent": self._ua,
            "Accept": accept,
            "Accept-Encoding": "gzip, deflate",
        }
        backoff = 1.0
        last_exc: Optional[Exception] = None
        for attempt in range(self._max_retries):
            self._pace()
            try:
                resp = requests.get(url, headers=headers, params=params,
                                    timeout=self._timeout)
                self._last_request = time.monotonic()
                if resp.status_code == 200:
                    return resp
                if resp.status_code in (429, 500, 502, 503, 504):
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                resp.raise_for_status()
            except requests.RequestException as exc:
                last_exc = exc
                time.sleep(backoff)
                backoff *= 2
        if last_exc is not None:
            raise last_exc
        raise RuntimeError(f"SEC request to {url} failed after retries")


# ---------- live: ticker map ----------


def _load_ticker_map(client: _SecClient) -> dict[str, str]:
    try:
        resp = client.get(TICKERS_URL)
        data = resp.json()
    except Exception:
        return {}
    out: dict[str, str] = {}
    for entry in data.values() if isinstance(data, dict) else []:
        cik = str(entry.get("cik_str", "")).lstrip("0")
        ticker = entry.get("ticker", "")
        if cik and ticker:
            out[cik] = ticker
    return out


# ---------- live: search + fetch ----------


def _build_search_query() -> str:
    # OR'd phrases. Quoted phrases require an exact run; bare words match
    # tokens. EFTS accepts a Lucene-ish syntax via the `q` param.
    phrases = [
        '"Item 1.05"',
        '"material cybersecurity incident"',
        '"cybersecurity incident"',
        '"cyber incident"',
        '"data breach"',
        '"unauthorized access"',
        "ransomware",
        '"network intrusion"',
        "exfiltration",
    ]
    return " OR ".join(phrases)


def _search_efts(client: _SecClient, start: str, end: str,
                 max_hits: int = 50) -> list[dict]:
    params = {
        "q": _build_search_query(),
        "forms": "8-K,8-K/A",
        "dateRange": "custom",
        "startdt": start,
        "enddt": end,
    }
    resp = client.get(EFTS_URL, params=params)
    payload = resp.json()
    hits = payload.get("hits", {}).get("hits", []) or []
    return hits[:max_hits]


def _primary_doc_url(cik: str, accession_with_dashes: str, doc_name: str) -> str:
    cik_no_zeros = str(int(cik))
    accession_no_dashes = accession_with_dashes.replace("-", "")
    return f"{ARCHIVE_BASE}/{cik_no_zeros}/{accession_no_dashes}/{doc_name}"


def _filing_index_url(cik: str, accession_with_dashes: str) -> str:
    cik_no_zeros = str(int(cik))
    accession_no_dashes = accession_with_dashes.replace("-", "")
    return (
        f"{ARCHIVE_BASE}/{cik_no_zeros}/{accession_no_dashes}/"
        f"{accession_with_dashes}-index.htm"
    )


def _parse_hit(hit: dict) -> Optional[dict]:
    src = hit.get("_source", {}) or {}
    raw_id = hit.get("_id", "")
    if ":" not in raw_id:
        return None
    accession, doc_name = raw_id.split(":", 1)
    ciks = src.get("ciks") or []
    if not ciks:
        return None
    cik = str(ciks[0])
    form = src.get("form", "") or src.get("root_form", "") or ""
    file_date = src.get("file_date", "") or ""
    display_names = src.get("display_names") or []
    company = display_names[0] if display_names else ""
    # Strip the trailing "(CIK 0001234567) (filer)" annotation
    company = re.sub(r"\s*\(CIK\s*\d+\)\s*\(.*?\)\s*$", "", company).strip()
    return {
        "cik": cik,
        "accession": accession,
        "doc_name": doc_name,
        "form": form,
        "file_date": file_date,
        "company": company,
    }


def fetch_live_signals(
    user_agent: str,
    *,
    lookback_hours: int = 24,
    now: Optional[datetime] = None,
    max_candidates: int = 25,
    request_delay: float = 0.2,
) -> LiveFetchResult:
    """Live EDGAR fetch. Returns a structured result, never raises for
    expected error paths (network/rate-limit) — those are reported in
    `result.error`.
    """
    result = LiveFetchResult()
    try:
        client = _SecClient(user_agent=user_agent, request_delay=request_delay)
    except (ValueError, RuntimeError) as exc:
        result.error = str(exc)
        return result

    end = now or datetime.now(timezone.utc)
    start = end - timedelta(hours=lookback_hours)
    result.window_start = start.date().isoformat()
    result.window_end = end.date().isoformat()

    try:
        hits = _search_efts(client, result.window_start, result.window_end,
                            max_hits=max_candidates)
    except Exception as exc:
        result.error = f"EDGAR search failed: {exc}"
        return result

    ticker_map = _load_ticker_map(client)

    for hit in hits:
        parsed = _parse_hit(hit)
        if parsed is None:
            continue
        result.candidates_examined += 1
        form = parsed["form"]
        # The search filters on form already, but defend in depth.
        if not form.upper().startswith("8-K"):
            result.rejected += 1
            result.rejected_reasons["wrong_form"] = (
                result.rejected_reasons.get("wrong_form", 0) + 1
            )
            continue

        primary_url = _primary_doc_url(parsed["cik"], parsed["accession"],
                                       parsed["doc_name"])
        try:
            doc_resp = client.get(primary_url, accept="text/html, */*")
            filing_text = doc_resp.text
        except Exception:
            result.rejected += 1
            result.rejected_reasons["fetch_failed"] = (
                result.rejected_reasons.get("fetch_failed", 0) + 1
            )
            continue

        ticker = ticker_map.get(str(int(parsed["cik"])), "")

        signal = classify_filing(
            filing_text,
            form=form,
            company=parsed["company"],
            cik=parsed["cik"],
            ticker=ticker,
            accession=parsed["accession"],
            filing_date=parsed["file_date"],
            sec_url=_filing_index_url(parsed["cik"], parsed["accession"]),
        )

        if signal is None:
            result.rejected += 1
            result.rejected_reasons["no_qualifying_item"] = (
                result.rejected_reasons.get("no_qualifying_item", 0) + 1
            )
            continue

        result.signals.append(signal)

    return result
