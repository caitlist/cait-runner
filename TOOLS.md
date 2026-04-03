# TOOLS.md — Tools & Environment

---

## Google Sheets API

**Purpose:** Single source of truth for all lists. All qualified entries are written here.

**Sheet ID:** `1GpeLSbjGTcKe_V1gWYehZcPFU8Vai1q4A9-xLnRGFhA`

**Authentication:** Service account JSON file
- Create a Google Cloud project
- Enable Google Sheets API
- Create a service account → download JSON key → save path to `.env`
- Share the Google Sheet with the service account email (Editor access)

**Library:** `gspread` + `google-auth`

**Credentials in .env:**
```
GOOGLE_SHEET_ID=1GpeLSbjGTcKe_V1gWYehZcPFU8Vai1q4A9-xLnRGFhA
GOOGLE_CREDS_PATH=path/to/service-account.json
```

**Rate limits:** 100 requests per 100 seconds per user. Add `time.sleep(1)` between batch writes.

---

## Apify

**Purpose:** Instagram profile scraping and Facebook group search (no official API available for either).

**Authentication:** API token in `.env`
```
APIFY_TOKEN=your_token_here
```

**Library:** `apify-client` (`pip install apify-client`)

**Actors to use:**

| Task | Actor ID | Notes |
|------|----------|-------|
| Instagram hashtag search | `apify/instagram-hashtag-scraper` | Finds posts → extract profile info |
| Instagram profile scraper | `apify/instagram-profile-scraper` | Scrape specific usernames for engagement data |
| Facebook group search | `apify/facebook-groups-scraper` | Search by keyword, returns group name, URL, member count |

**Important:** Always set `maxItems` to limit run size and control credit usage. Default to 50 items per search, filter down to 5 qualifying entries.

**Apify Console:** https://console.apify.com

---

## Reddit API (PRAW)

**Purpose:** Community discovery across caregiving subreddits.

**Authentication:** Reddit API app credentials
- Create app at https://www.reddit.com/prefs/apps (script type)
- Copy client_id, client_secret, user_agent

**Library:** `praw` (`pip install praw`)

**Credentials in .env:**
```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=cait-lister/1.0 by u/your_reddit_username
```

**Free tier:** 60 requests/minute for OAuth. No cost.

---

## Email Enrichment (Free Methods — No Hunter.io Yet)

Pipeline order:
1. **Bio scrape** — regex search for email pattern in Instagram bio
2. **Link in bio** → follow URL → scrape website contact/about page for email
3. **Website scrape** — look for mailto: links, contact forms, "work with me" pages
4. **Hunter.io** — NOT YET CONFIGURED. Add when ready.

**Other free/freemium email tools to consider when scaling:**
- **Snov.io** — 50 free credits/month. Good for professional email finding.
- **Apollo.io** — free tier has 50 email exports/month. Strong for therapists/educators.
- **Clearbit Connect** — Gmail plugin, free for individual lookups.
- **NeverBounce** — for bulk email validation before outreach (paid, use after list is built).

**Libraries for scraping:** `requests` + `beautifulsoup4`

---

## Environment Variables (.env)

```
ANTHROPIC_API_KEY=
GOOGLE_SHEET_ID=1GpeLSbjGTcKe_V1gWYehZcPFU8Vai1q4A9-xLnRGFhA
GOOGLE_CREDS_PATH=
APIFY_TOKEN=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=cait-lister/1.0 by u/
HUNTER_API_KEY=
```

---

## Python Dependencies

```bash
pip install gspread google-auth apify-client praw requests beautifulsoup4 python-dotenv
```

---

## CSV Fallback (If Sheets API Fails)

All scripts write to `outputs/` as CSV backup when the Sheets API is unavailable.
File naming: `outputs/CATEGORY-YYYY-MM-DD.csv`
