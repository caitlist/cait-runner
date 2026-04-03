# AGENTS.md — Operating Rules

---

## Non-Negotiable Rules

1. **Read ALL tabs before every write.** No exceptions. The dedup set must be current before a single row is written.
2. **Zero duplicates across the entire sheet.** An account/URL/group name found in ANY tab (except ADHD) is a duplicate. Skip it and continue.
3. **Never touch the US ADHD tab.** Not to read for dedup (it is excluded from dedup reads too — see note below), not to write. Permanently off-limits.
   - *Note on ADHD tab:* The tab is excluded from dedup reads because it is a completed, separate vertical. Duplication risk from ADHD accounts appearing in other tabs is low — omit from dedup scan for now.
4. **5 entries per category is the default batch size.** Do not run larger batches without Cherwin's explicit approval.
5. **Female accounts only** for all Instagram lists (50 Million List, CAIT Community).
6. **USA-only** for all Facebook and Instagram lists. Require at least one USA signal: bio mentions USA/state, US hashtags, US location tag, or US organization affiliation.
7. **15+ real comments per post minimum** for Instagram qualification. Emoji-only or one-word comments do not count toward this threshold.
8. **Inactive accounts are disqualified.** No posts in the last 30 days = skip.
9. **Never draft outreach copy** unless Cherwin explicitly asks — that is a separate skill.
10. **Never spend on external APIs without approval.** Hunter.io credits, Apify actor runs beyond free tier, any paid tool — confirm cost first.

---

## Approval Required Before Action

- Any scrape run larger than 5 per category
- Any new API or tool that incurs cost
- Any change to qualification thresholds
- Any change to column structure in the sheet
- Any run that touches a new tab not currently in the workflow

---

## Cost Guardrails

- **Apify:** Use free tier actors where possible. Check Apify credit balance before running any actor. Flag if a run would exceed 10,000 results without approval.
- **Hunter.io:** Not configured yet. Do not use. Bio + website scraping only for email enrichment.
- **Reddit API:** Free. No cost guardrails needed.
- **Google Sheets API:** Free within rate limits. If hitting rate limits (429 errors), add exponential backoff — do not retry immediately.

---

## Qualification Standards Summary

*(Full detail in knowledge/qualification-standards.md)*

**Instagram — both tabs:**
- Female account
- USA-based indicator
- Active in last 30 days
- 15+ real comments average across last 3 posts
- Audience = parents/caregivers (not clinicians only)

**CAIT Community tab — additional:**
- Must sell a product, course, or service
- Email required — no email = lower priority (still add, note "email not found" in Email Source column)

**Facebook groups:**
- USA group (check group name, description, or admin bio for USA indicators)
- Active group (posts within last 7 days)
- 500+ members minimum
- Admin contact info collected where available

**Reddit communities:**
- 1,000+ members minimum (exceptions for extremely niche high-signal communities)
- Active (posts within last 7 days)
- Relevant to caregiving, medical parenting, or specific diagnosis

---

## File Path Rules

- All scripts live in `scripts/`
- All knowledge files live in `knowledge/`
- All workflows live in `workflows/`
- Run logs and session notes go to `memory/YYYY-MM-DD.md`
- Weekly synthesis goes to `memory/insights.md`
- CSV fallback outputs go to `outputs/`
- Never commit `.env` — it is in `.gitignore`
