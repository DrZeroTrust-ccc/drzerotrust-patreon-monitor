# DrZeroTrust Patreon Monitor

A draft-generation system that produces Patreon-ready markdown posts
("Market Signal Watch") summarizing publicly available signals from:

- **SEC Cyber Incident filings** (8-K Item 1.05 and similar disclosures)
- **Capitol Hill financial transaction disclosures** (STOCK Act / PTR filings)

Version 1 is **offline and mock-only**. It does not connect to any external
API, does not scrape any site, and does not publish anything to Patreon.
It exists to validate the post format, file layout, and module boundaries
before any live integrations are added.

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

## Generate a draft

```bash
python -m src.main
```

You should see a new file in `output/` named
`drzerotrust-market-signal-watch-YYYY-MM-DD.md`.

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
