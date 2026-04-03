# Workflow: Influencer Discovery

## Objective
Find, score, and write qualified influencer accounts to the Influencer Pipeline tab — one strong account per diagnosis category minimum.

## When to Run
On-demand. Triggered when Cherwin says "run Jess" or a category gap needs filling.

## Required Inputs
- Target category (e.g. "CHD", "T1D")
- Hashtags for that category (see `knowledge/diagnosis-categories.md`)
- Apify credits available

---

## Steps

### Step 1 — Check the gap map
Read Influencer Pipeline tab. Build category counts. Identify the emptiest or weakest category to tackle.

Report to Cherwin:
```
CHD: 3 entries (1 strong)
T1D: 2 entries (0 strong)   ← weakest
CP: 4 entries (2 strong)
...
```

### Step 2 — Select hashtags
From `knowledge/diagnosis-categories.md`, pick 2–3 hashtags for the target category.
Check `../../scripts/hashtag_config.json` for the current rotation.

### Step 3 — Scrape hashtag for handles
Use Apify `apify/instagram-hashtag-scraper` to pull accounts posting under the target hashtag.
Filter: 40K–250K followers, English content, posted within 30 days.
Collect 8–10 candidate handles.

### Step 4 — Score candidates
```bash
python -X utf8 scripts/influencer_pipeline.py --mode verify --handles handle1 handle2 handle3 --category "T1D"
```
- Scrapes profile details via `apify/instagram-scraper` with RESIDENTIAL proxies
- Calculates: ER%, avg comment count, follower tier
- Detects: loop giveaway history, USA signals, last post date
- Writes to Influencer Pipeline tab (after dedup check)

### Step 5 — Review results
After the run, report:
- How many were scored
- How many are "strong" (50+ avg comments, ER in Good/High range)
- Any comment pods flagged
- Any affiliate/Amazon accounts flagged
- Net new strong accounts for the category

### Step 6 — Flag borderline cases
If an account is close but not clearly strong or disqualified, note it in the Notes column and flag to Cherwin. Don't silently skip or silently approve borderline accounts.

---

## Expected Output
- New rows written to Influencer Pipeline tab with all scoring columns filled
- Comment pods flagged in Notes
- Affiliate accounts flagged in Notes
- Category gap map updated

## Error Handling

| Error | Action |
|-------|--------|
| Handle-guessing returns no results | Stop — never guess handles. Switch to hashtag scraping. |
| WebFetch fails on JS-rendered site | Move on immediately. Don't retry. |
| Apify credits exhausted | Report to Cherwin. Resets April 1. |
| All candidates in a category score weak | Expand hashtag list, try broader terms |
| Comment pod detected | Flag in Notes, report to Cherwin, do not approve |

## Notes
- Always use RESIDENTIAL proxies — no exceptions
- Max 8–10 handles per Apify batch
- Run 8 candidates, not 20 — speed matters, Apify credits are finite
- Dedup check must cover ALL non-ADHD tabs, not just Influencer Pipeline
- If a category hashtag is thin, try the broader parent hashtag (e.g. #heartmom instead of #chdmom)
