# MEMORY.md — Mikha's Long-Term Context

---

## About CAIT Connect

AI-powered caregiving app for parents of medically complex and neurodevelopmental children. Helps families track health, behavior, therapy — with context-aware AI that gets smarter over time. HIPAA-protected. USA launch April 2026. Goal: 230K+ families at launch.

---

## About the Pipeline

Mikha's pipeline has two output streams:
1. **Comments** — genuine IG comments posted before the DM lands (warms the account)
2. **DMs** — sent manually by the human Mikha from Instagram, using the sheet as the send list

Every account goes through: Discovery → Verification → Transfer → Scrape → Generate Comment → DM

---

## Sheet State

**Sheet ID:** `1GpeLSbjGTcKe_V1gWYehZcPFU8Vai1q4A9-xLnRGFhA`

| Tab | State |
|-----|-------|
| Medical Mom DM Outreach | 734 rows as of 2026-03-25. 605 pending verification. 30 IG DM done. |
| COMMENTS | Active — daily comment tab. Columns: Handle, IG Profile Link, Post URL, Post Caption, Generated Comment, Date, Notes, Commented |

---

## Verification System

Notes column in Medical Mom DM Outreach uses a dropdown:
- **APPROVE** — account qualifies, move to COMMENTS
- **NOT VALID** — disqualified, stays in sheet but never transferred
- **blank** — pending Cherwin's review

Transfer rule: Notes = "APPROVE" AND DM Status ≠ "IG DM"

---

## Discovery

Script: `scripts/daily_dm_discovery.py`
- Scrapes Instagram hashtags via Apify (instagram-hashtag-scraper actor)
- Self-learning: auto-discovers new hashtags from scraped captions
- English filter, dedup across all sheet tabs
- Writes to Medical Mom DM Outreach with Source Hashtag column
- Run: `python -X utf8 scripts/daily_dm_discovery.py --limit 50 --max-posts 100`

**Apify resets:** April 1, 2026 (exhausted from March runs)

---

## Comment Generation Rules (critical)

Full examples in `../../knowledge/comment-examples.md`

**#1 rule:** Never restate or paraphrase the caption. Anchor to a specific detail, then add the emotional layer — say the thing the parent already knows but rarely hears out loud.

**Structure:** [Specific detail anchor] + [Emotional observation] + [DM nudge — varied] + [1 emoji at end]

- 2–4 sentences max
- Use child's name when it appears naturally
- 1 emoji at the very end — hearts preferred (❤️ 🤍 🫶)
- No em dashes — ever
- "We" not "I", or no subject at all
- Never mention CAIT, the app, or any product
- SENSITIVE posts (grief/loss/death/ICU): still generate comment, flag [SENSITIVE], no nudge
- DM nudge: rotate from approved list — never repeat back-to-back, never "take a peek"

---

## Follower Threshold

Minimum 1,000 followers to receive a comment. Accounts below threshold: flagged in Notes as "Under 1000 followers", Post Caption set to SKIP message, no comment generated.

---

## DM Template (Mikha sends manually)

```
Hi [Name]

We came across your page and just wanted to say how much we admire everything you're managing, it's a lot.

We've been building something with our medical parent community from day one that helps take things out of your head — like tracking symptoms, medications, and everything going on day-to-day, without needing to remember it all.

It has a similar intelligence to ChatGPT, but feels much more personal and built for real family life.

Many medical parents have told us it's been a game changer for them and something they wish they had much earlier.

We're opening early access to a small group before launch — if it feels like it could help at all, we'd be happy to share it with you

We also offer a small honorarium as a thank you for your time all we ask is for your honest feedback to see how this could help you each day.

If you're open, we'd be happy to share more details

Mikha
Brand Partnership Lead
caitconnect.com
```

---

## What's Working

- Hashtag scraping via Apify finds genuine medical mom accounts
- Self-learning hashtag expansion (auto-discovers from captions)
- Comment generation in-session (Claude Code reads captions, generates, writes back)
- Transfer/scrape/write workflow via `scripts/comments_workflow.py`

---

## Known Issues / Watch Points

- 605 accounts pending Cherwin verification as of 2026-03-25
- Apify free tier exhausted — resets April 1
- SENSITIVE posts need Cherwin review before pasting — don't skip this step
- Comment pods (accounts where comments >> likes 2x+) should be flagged

---

## Key Decisions

- Daily .md send files retired — Cherwin manages DM sending manually from sheet
- "take a peek" phrase permanently banned from DM nudges — overused
- Min 1,000 followers added 2026-03-25
- Cancer adults category approved but not yet added to discovery (next scrape)
- Notes column uses APPROVE / NOT VALID (all caps) — not "Approved" / "Not Valid"
