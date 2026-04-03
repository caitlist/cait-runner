# MEMORY.md — CAIT Lister Long-Term Memory

---

## About the Business

CAIT Connect Corp is a pre-launch AI-first app for parents of medically complex children and those with neurodevelopmental conditions. Think ChatGPT built specifically for caregiving families.

**What CAIT does:**
- Tracks symptoms, medications, therapy notes, behavioral patterns, sleep, and stress
- Generates clinician-ready PDF summaries parents can bring to appointments
- Organizes everything into AI-powered Smart Folders
- Provides context-aware guidance that gets smarter the more a family uses it
- HIPAA-protected — the CAIT team cannot see user conversations

**Launch:** April 2026, USA only. India and South America in later phases.

**Current status:** Pre-launch. Beta testing with select families. 230K waitlist built in 5 months across Instagram, Facebook, and Reddit.

---

## About the Owner

**Cherwin Lam** — day-to-day operator, social media, marketing, QA testing, influencer outreach. Based in Philippines (UTC+8). Casual communicator, iterative, prefers structured outputs. Wants Claude to make judgment calls. Address as Cherwin.

**Hannah Samuel** — strategy lead and boss. Major decisions escalate via Cherwin.

---

## Key Goals for This Agent

1. Build a qualified pipeline of 50+ CAIT Community accounts (therapists, BCBAs, educators) with contact emails before April 2026
2. Build 100+ medically complex journey accounts for the 50 Million List tab
3. Build 100 USA Facebook parent groups across all diagnosis categories with admin contact info
4. Build 50 Reddit caregiving communities with mod info
5. Cover all diagnosis categories — not just autism and T1D
6. Zero duplicates across the entire sheet, ever

---

## The Google Sheet

**ID:** `1GpeLSbjGTcKe_V1gWYehZcPFU8Vai1q4A9-xLnRGFhA`

This is the single source of truth. Cherwin reviews it directly — no briefing emails, no Slack.

**Tabs summary:**
- `50 Million List` — Instagram journey accounts + influencers (Instagram column schema)
- `CAIT Community` — Therapists, BCBAs, OTs, educators with products (Instagram column schema + email required)
- `US ADHD Facebook Group Communities` — **SKIP ENTIRELY. DO NOT TOUCH.**
- `US Autism Facebook Group Communities` — Autism Facebook groups (community column schema)
- `US Facebook Medical Moms` — Medical mom Facebook groups (community column schema)
- `US Reddit Medical Moms` — Medical parenting Reddit (community column schema)
- `US Autism Reddit Group Communities` — Autism Reddit communities (community column schema)

---

## Diagnosis Category Priority

**Highest priority:**
- Medically complex (any serious pediatric condition requiring ongoing care)
- Autism

**High priority:**
- Down syndrome
- Type 1 Diabetes
- Epilepsy / Dravet syndrome
- Cystic fibrosis
- Pediatric cancer

**Include where found:**
- Cerebral palsy
- ARFID
- Rare diseases (Sanfilippo, Moebius, etc.)
- NICU / premature birth
- Feeding therapy
- Pediatric heart conditions

---

## Key Decisions Made

- 2026-03-18: Default batch size is 5 per category. Cherwin reviews quality before any scale-up.
- 2026-03-18: Email enrichment pipeline is bio scrape → website scrape → Hunter.io (Hunter not yet configured, skip for now)
- 2026-03-18: US ADHD tab is fully populated and permanently off-limits for writes
- 2026-03-18: Duplicate check is cross-sheet (all non-ADHD tabs), not per-tab
- 2026-03-18: Female accounts only for all Instagram lists
- 2026-03-18: USA-only indicators required for Instagram and Facebook — bio keywords, hashtags, or location tags
- 2026-03-18: Outreach copy is a separate skill — this agent delivers lists only unless explicitly asked

---

## What's Working / What's Not

*(Updated after each run — seed entries below)*

- Reddit API via PRAW is reliable and free. Good starting point for community discovery.
- Facebook group discovery via Apify requires validation — member counts can be outdated.
- Instagram bio scraping for emails works roughly 30–40% of the time. Website scrape adds another 20–30%.
- Medically complex is the broadest and most productive category — prioritize it.
- CAIT Community tab has the highest value per entry (email + product context) but also the highest enrichment cost. Quality over speed here.

---

## Pipeline Progress

*(Updated after each run)*

| Tab | Target | Current | Last Run |
|-----|--------|---------|----------|
| 50 Million List | 100 | unknown — read sheet to check | — |
| CAIT Community | 50 | unknown — read sheet to check | — |
| US Autism Facebook Group Communities | 100 | has data — read to check | — |
| US Facebook Medical Moms | 100 | has data — read to check | — |
| US Reddit Medical Moms | 50 | 0 (empty) | — |
| US Autism Reddit Group Communities | 50 | 0 (empty) | — |
| Medical Mom DM Outreach | ongoing | **799 data rows** (as of 2026-03-31) | 2026-03-31 |

## DM Outreach Pipeline Status (as of 2026-03-31)

- **799 data rows** in Medical Mom DM Outreach tab
- 3 scraper scripts running on Apify (requires paid plan — free plan exhausted monthly):
  - `scrape_score_new_hashtags.py` — 35 medical hashtags
  - `scrape_tiktok_medical_parents.py` — TikTok cross-check → IG verify
  - `scrape_platform_articles.py` — 3 medical sources only (amraandelma, adhdonline, themighty)
- Runner on port 5564. ngrok for remote access (`ngrok http 5564`).
- Comment workflow: transfer → scrape → generate (in-session Claude) → write
- Article scraper trimmed 2026-03-31: removed 6 influencer-hero.com general lists. General influencer sources banned permanently.
