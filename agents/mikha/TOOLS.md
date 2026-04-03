# TOOLS.md — Mikha's Tools & Environment

## Credentials

All in `../../.env`. Never hardcode.

```
APIFY_TOKEN           — Apify API key for Instagram scraping
GOOGLE_SHEET_ID       — 1GpeLSbjGTcKe_V1gWYehZcPFU8Vai1q4A9-xLnRGFhA
GOOGLE_CREDS_PATH     — Path to Google service account JSON
```

## Apify

- **Actor for profile scraping:** `apify/instagram-scraper`
- **Actor for hashtag scraping:** `apify/instagram-hashtag-scraper`
- **Always use RESIDENTIAL proxies** — `apifyProxyGroups: ["RESIDENTIAL"]`
- **Never use** `apify/instagram-profile-scraper` — gets blocked
- Batch size: max 10 handles per call
- Free tier resets: April 1, 2026
- Console: https://console.apify.com

## Google Sheets (gspread)

```python
from google.oauth2.service_account import Credentials
import gspread

creds = Credentials.from_service_account_file(
    os.environ['GOOGLE_CREDS_PATH'],
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
gc = gspread.authorize(creds)
ss = gc.open_by_key(os.environ['GOOGLE_SHEET_ID'])
```

Batch writes: `ws.update_cells(cells, value_input_option='USER_ENTERED')`

## Scripts (at project root `../../scripts/`)

| Script | What it does |
|--------|-------------|
| `daily_dm_discovery.py` | Hashtag scraping, writes new accounts to Medical Mom DM Outreach |
| `comments_workflow.py --mode transfer` | Copies APPROVE rows to COMMENTS tab |
| `comments_workflow.py --mode scrape` | Scrapes latest post per COMMENTS row, writes caption |
| `comments_workflow.py --mode write` | Writes generated comments to COMMENTS tab |
| `prep_daily_batch.py` | Marks today's accounts with DM Status |

## Comment Generation

Comment generation happens **in-session via Claude Code** — not a separate API call. No external LLM key needed.

Flow:
1. `--mode scrape` outputs `../../outputs/captions_for_comments.json`
2. Claude reads JSON, generates comments in-session
3. Claude writes `../../outputs/comments_to_write.json`
4. `--mode write` reads that JSON and writes to sheet

## Running Scripts

```bash
# From project root (c:/Users/lamch/Downloads/Caitlist)
python -X utf8 scripts/daily_dm_discovery.py --limit 50 --max-posts 100
python -X utf8 scripts/comments_workflow.py --mode transfer
python -X utf8 scripts/comments_workflow.py --mode scrape
python -X utf8 scripts/comments_workflow.py --mode write
```

## Environment Quirk

Always use `-X utf8` flag on Windows to avoid encoding errors with emoji/special characters.
