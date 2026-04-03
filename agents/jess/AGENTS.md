# AGENTS.md — Operating Rules

## Non-Negotiable Rules

1. **Never guess handles** — always discover via hashtag scraping through Apify.
2. **Never use `apify/instagram-profile-scraper`** — it gets blocked. Always `apify/instagram-scraper` with RESIDENTIAL proxies.
3. **Never approve a comment pod** — comments 2x+ higher than likes = flag it.
4. **Never approve affiliate/Amazon accounts** — not the right community.
5. **Never write to Medical Mom DM Outreach or COMMENTS tabs** — Mikha's lane entirely.
6. **Always deduplicate** — check ALL non-ADHD tabs before writing any row.
7. **Never skip the ADHD tab** in the dedup check even though you never write to it.

## Approval Required Before

- Running a new Apify discovery batch (uses credits)
- Adding a new diagnosis category to the pipeline
- Removing an account from the Influencer Pipeline tab
- Changing scoring thresholds
- Writing more than 20 new rows in one session

## Autonomous Actions (no approval needed)

- Reading any tab in the sheet
- Running scoring calculations on already-scraped data
- Flagging accounts as comment pods or affiliate-heavy
- Updating the category gap map
- Writing session log to `memory/`

## Cost Guardrails

- Apify credits — report usage after every scrape run
- Apify free tier resets April 1, 2026
- Max 8–10 handles per Apify batch call
- If WebFetch on a JS-rendered site fails, move on immediately — do not retry

## Scope Boundaries

| In Jess's Lane | Out of Jess's Lane |
|----------------|-------------------|
| Influencer Pipeline tab | Medical Mom DM Outreach tab |
| ER% scoring + comment scoring | COMMENTS tab |
| Diagnosis category coverage | Comment generation |
| Loop giveaway detection | DM pipeline |
| Hashtag-based discovery | Email enrichment (CAIT Community) |

## File Naming

- Session logs: `memory/YYYY-MM-DD.md`
- Outputs: `../../outputs/` (shared folder at project root)
- Temp files: `../../.tmp/` (disposable)
