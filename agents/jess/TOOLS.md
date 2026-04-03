# TOOLS.md — Jess's Tools & Environment

## Credentials

All in `../../.env`. Never hardcode.

```
APIFY_TOKEN           — Apify API key
GOOGLE_SHEET_ID       — 1GpeLSbjGTcKe_V1gWYehZcPFU8Vai1q4A9-xLnRGFhA
GOOGLE_CREDS_PATH     — Path to Google service account JSON
```

## Apify

- **Actor:** `apify/instagram-scraper` — always this one
- **Never use:** `apify/instagram-profile-scraper` — gets blocked
- **Proxies:** Always RESIDENTIAL — `apifyProxyGroups: ["RESIDENTIAL"]`
- **Batch size:** 8–10 handles per call max
- **Results limit:** 12 posts per profile (enough for ER calculation)
- **Free tier resets:** April 1, 2026
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

## Scripts

| Script | What it does |
|--------|-------------|
| `../../scripts/influencer_pipeline.py` | Scrape profiles, score ER% + comments, write to Influencer Pipeline tab |
| `../../scripts/hashtag_config.json` | Hashtag lists per diagnosis category |

## Running the Pipeline

```bash
# Verify specific handles
python -X utf8 scripts/influencer_pipeline.py --mode verify --handles handle1 handle2 --category "CHD"

# Verify from a file (one handle per line)
python -X utf8 scripts/influencer_pipeline.py --mode verify --file inputs/seed_accounts.txt --category "T1D"

# Dry run (no sheet write — test only)
python -X utf8 scripts/influencer_pipeline.py --mode verify --handles someaccount --dry-run
```

## Scoring Output Columns (Influencer Pipeline tab)

| Column | Description |
|--------|-------------|
| Handle | Instagram handle |
| Name | Display name |
| Followers | Follower count |
| Avg Likes | Average likes per post |
| Avg Comments (real) | Average comments per post |
| Engagement Rate % | ER% calculated |
| ER Score | Tiered ER benchmark score |
| Comment Score | Raw comment volume score |
| Macro/Micro | Tier classification |
| Loop Giveaway History | Flagged if detected |
| Platform | Instagram / TikTok |
| Category | Diagnosis category |
| Notes | Flags: comment pod, affiliate, borderline |
| Active (30 days) | Yes / No |
| USA Signal | Yes / No / Unknown |
| Last Verified | Date |

## Environment Quirk

Always use `-X utf8` flag on Windows to avoid encoding errors.
