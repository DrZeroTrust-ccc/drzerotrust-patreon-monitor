# DrZeroTrust Patreon Monitor

A draft-generation system that produces Patreon-ready markdown posts
("Market Signal Watch") summarizing publicly available signals from:

- **SEC Cyber Incident filings** (8-K Item 1.05 and similar disclosures)
- **Capitol Hill financial transaction disclosures** (STOCK Act / PTR filings)

Two modes:

- **Mock** (default): everything runs from hard-coded fictional data, no
  network calls. Use this to validate post format and code paths.
- **Live SEC** (`--sec-real`): pulls real Form 8-K and 8-K/A cyber-incident
  filings from SEC EDGAR over the last 24 hours and runs them through a
  content classifier. Capitol Hill, Google Drive, and Patreon stay mock
  / no-op for now.

Nothing in this repo posts to Patreon, drafts to Patreon, or scrapes
Patreon. There are no investment recommendations and no allegations of
insider trading or other misconduct.

## What V1 does

Running `python -m src.main` produces a single markdown file at:

```
output/drzerotrust-market-signal-watch-YYYY-MM-DD.md
```

The post is built from hard-coded mock data and contains:

- Title
- Teaser
- Executive Summary
- SEC Cyber Incident Signals
- Capitol Hill Trade Signals
- Sector-to-Committee Relevance
- Watchlist Table
- Source Links
- Caveats
- No-investment-advice disclaimer

## What V1 explicitly does **not** do

- No API keys are read or required.
- No network calls of any kind.
- No posting, publishing, or drafting to Patreon.
- No scraping of Patreon, SEC EDGAR, House/Senate disclosure portals, or any
  other site.
- No investment recommendations.
- No allegations of insider trading, misconduct, or wrongdoing by any
  individual or entity.

The output is an **educational signal-watch summary** built from
publicly available regulatory filings (mocked in V1). Readers must
do their own research and consult a licensed professional before
making any financial decision.

## Project layout

```
.
├── README.md
├── .env.example
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── main.py                     # entrypoint: builds one mock post
│   ├── post_generator.py           # assembles the markdown post
│   ├── state_store.py              # tracks which signals were already posted
│   ├── sec_cyber_monitor.py        # mock SEC cyber-incident signal source
│   ├── capitol_trades_monitor.py   # mock Capitol Hill trade signal source
│   └── google_drive_archive.py     # archive stub (no-op in V1)
├── output/                         # generated markdown posts land here
├── state/                          # JSON state files live here
└── tests/                          # unit tests
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # placeholders only; nothing is required for V1
```

## Generate a draft (mock mode)

```bash
python -m src.main
```

You should see a new file in `output/` named
`drzerotrust-market-signal-watch-YYYY-MM-DD.md`.

## Generate a draft with live SEC EDGAR data

```bash
# 1. Set a real, descriptive User-Agent (SEC requires this).
#    Edit .env and set SEC_USER_AGENT to your contact info, e.g.:
#    SEC_USER_AGENT="DrZeroTrust Research Bot chase@drzerotrust.com"
cp .env.example .env

# 2. Run with --sec-real
python -m src.main --sec-real
```

What `--sec-real` does:

- Queries SEC EDGAR full-text search for Form `8-K` and `8-K/A` filings
  in the last 24 hours that match cyber-incident phrasing (Item 1.05,
  ransomware, unauthorized access, exfiltration, etc.).
- Fetches each candidate filing's primary document.
- Applies a content classifier that requires either an explicit
  **Item 1.05** heading **or** **Item 8.01** paired with specific-
  incident language. Generic cybersecurity governance / risk-factor
  boilerplate is rejected.
- Computes a Watch Priority (High / Medium / Low) per filing.
- Falls back to mock data if `SEC_USER_AGENT` is unset.
- Reports `candidates examined / qualified / rejected` to the console.

Live mode is read-only. Capitol Hill, Google Drive, and Patreon are
**not** affected by this flag — they remain mock / no-op in V1.

### Notes on the live SEC mode

- A 24-hour window on a weekend or holiday often returns zero qualifying
  filings. The briefing will simply note "No SEC cyber-incident signals
  this cycle." That is the expected behavior.
- The client paces requests (~5 req/s), retries on 429/5xx with backoff,
  and always sends `User-Agent: ${SEC_USER_AGENT}`. Do not set
  `SEC_USER_AGENT` to a value that impersonates another organization.
- The classifier never asserts that a breach occurred unless the filing
  text says so. Output is public-signal research, not a verdict.

## Run tests

```bash
python -m pytest tests/
```

## Roadmap (not implemented in V1)

- Live SEC EDGAR pull for 8-K Item 1.05 cyber-incident filings.
- Live Capitol Hill PTR ingestion via official disclosure portals.
- Sector / committee mapping enrichment.
- Google Drive archival of generated drafts.
- Optional Patreon draft creation (manual review still required before any
  publication).

## Disclaimer

This project produces educational summaries of publicly available
information. It is **not** financial, legal, or tax advice. Nothing
here constitutes a recommendation to buy, sell, or hold any security.
No content in this repository alleges insider trading, market
manipulation, or any other misconduct by any person or entity.
