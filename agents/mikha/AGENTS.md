# AGENTS.md — Operating Rules

## Non-Negotiable Rules

1. **Never delete rows** from Medical Mom DM Outreach. Append only. Deleting = permanently lost accounts.
2. **Never write to Influencer Pipeline tab** — that is Jess's lane entirely.
3. **Never mention CAIT, the app, or any product** in a comment posted on someone else's account.
4. **Never use em dashes** in any comment — use commas or periods.
5. **Never restate the caption** — comments must add something the caption didn't say.
6. **Always deduplicate** before writing any row to the sheet.
7. **Always read the sheet** before writing anything — never assume state.

## Approval Required Before

- Running discovery (uses Apify credits)
- Bulk-writing more than 50 rows to the sheet
- Changing the DM template
- Modifying any script that touches the Medical Mom DM Outreach tab
- Adding or removing hashtags from the discovery config

## Autonomous Actions (no approval needed)

- Reading any tab in the sheet
- Transferring APPROVE accounts to COMMENTS tab
- Generating comments from already-scraped captions
- Flagging SENSITIVE posts
- Writing session log to `memory/`

## Cost Guardrails

- Apify scraping uses credits — report usage after every scrape run
- Apify free tier resets April 1, 2026
- Do not run discovery more than once per day unless Cherwin explicitly asks
- Batches of max 10 handles per Apify call (RESIDENTIAL proxy rate limit)

## Scope Boundaries

| In Mikha's Lane | Out of Mikha's Lane |
|-----------------|---------------------|
| Medical Mom DM Outreach tab | Influencer Pipeline tab |
| COMMENTS tab | CAIT Community tab |
| Discovery via medical hashtags | Foundations & Organizations tab |
| Comment generation | ER% / engagement scoring |
| DM pipeline tracking | Email enrichment |

## File Naming

- Session logs: `memory/YYYY-MM-DD.md`
- Outputs: `../../outputs/` (shared folder at project root)
- Temp files: `../../.tmp/` (disposable)
