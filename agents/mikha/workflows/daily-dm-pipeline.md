# Workflow: Daily DM Pipeline

## Objective
Find new medical mom accounts, verify them, and get them into the COMMENTS tab ready for comment generation and DM send.

## When to Run
On-demand daily. Triggered when Cherwin says "run discovery" or the COMMENTS tab is running low.

## Required Inputs
- Apify credits available
- Google Sheets access
- `.env` loaded

---

## Steps

### Step 1 — Discovery (when pipeline needs refilling)
```bash
python -X utf8 scripts/daily_dm_discovery.py --limit 50 --max-posts 100
```
- Scrapes medical mom hashtags via Apify
- Writes new accounts to Medical Mom DM Outreach tab
- English filter, auto-dedup, self-learning hashtag expansion
- Reports: how many found, new hashtags discovered, Apify usage

### Step 2 — Verification (Cherwin's step)
Cherwin opens Medical Mom DM Outreach sheet, reviews accounts with blank Notes, and marks each:
- **APPROVE** — qualifies (medical mom, 1,000+ followers, active account)
- **NOT VALID** — doesn't qualify (wrong niche, business, non-medical)

*Auto-verify script coming — will score by bio + caption keywords and pre-mark obvious cases.*

### Step 3 — Transfer
When Cherwin says "transfer":
```bash
python -X utf8 scripts/comments_workflow.py --mode transfer
```
- Reads Medical Mom DM Outreach
- Finds rows where Notes = "APPROVE" AND DM Status ≠ "IG DM"
- Appends Handle + IG Profile Link to COMMENTS tab (deduped)
- Reports: how many transferred

### Step 4 — Scrape Latest Posts
```bash
python -X utf8 scripts/comments_workflow.py --mode scrape
```
- Reads COMMENTS tab rows missing Post Caption
- Checks follower count — skips accounts under 1,000
- Scrapes latest non-pinned post via Apify (RESIDENTIAL proxies)
- Writes Post URL + Post Caption to sheet
- Flags SENSITIVE posts in Notes column
- Outputs `outputs/captions_for_comments.json`

### Step 5 — Generate Comments
Cherwin says "generate comments" in Claude Code.
Mikha reads `outputs/captions_for_comments.json`, generates one comment per account following all brand voice rules, writes `outputs/comments_to_write.json`.

### Step 6 — Write Comments to Sheet
```bash
python -X utf8 scripts/comments_workflow.py --mode write
```
- Reads `outputs/comments_to_write.json`
- Writes Generated Comment + Date + Notes to COMMENTS tab

---

## Expected Output
- COMMENTS tab populated with: Handle, IG Link, Post URL, Post Caption, Generated Comment, Date, Notes
- SENSITIVE posts flagged for Cherwin review
- Accounts under 1,000 followers flagged in Notes

## Error Handling

| Error | Action |
|-------|--------|
| Apify credits exhausted | Report to Cherwin. Resets April 1. |
| Profile restricted/not found | Write "RESTRICTED OR NOT FOUND" to Post Caption column |
| No posts found | Write "No posts found" to Post Caption column |
| Under 1,000 followers | Write "SKIP - under 1000 followers (X)" — no comment generated |

## Notes
- Always use `-X utf8` on Windows to avoid encoding errors
- Apify batches max 10 handles — larger batches split automatically
- Never run discovery more than once per day unless Cherwin asks
