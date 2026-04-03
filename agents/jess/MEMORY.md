# MEMORY.md — Jess's Long-Term Context

---

## About CAIT Connect

AI-powered caregiving app for parents of medically complex and neurodevelopmental children. HIPAA-protected. USA launch April 2026. Goal: 230K+ families. Jess's job is to ensure every key diagnosis community has a trusted influencer advocate at launch.

---

## Pipeline State (as of 2026-03-25)

**Sheet tab:** Influencer Pipeline
**Sheet ID:** `1GpeLSbjGTcKe_V1gWYehZcPFU8Vai1q4A9-xLnRGFhA`

- 105 rows total checked across all batches
- 30 strong accounts verified and written to sheet
- Categories with gaps still need hashtag-based discovery

**Category fill status** (update each session):
| Category | Status |
|----------|--------|
| Congenital Heart Disease (CHD) | Has entries — verify strength |
| Type 1 Diabetes (T1D) | Has entries |
| Cerebral Palsy (CP) | Has entries |
| Down Syndrome | Has entries |
| Autism | Has entries |
| Rare/Undiagnosed Disease | Has entries |
| Feeding Issues / G-Tube | Has entries |
| Epilepsy / Seizure Disorders | Has entries |
| Premature Birth / NICU | Has entries |
| Cystic Fibrosis (CF) | Has entries |
| Cancer / Pediatric Oncology | TBD — not yet scraped |
| Adult Cancer | Approved by Cherwin — add next scrape |

---

## The Influencer Standard

**Follower range:** 40K – 250K
**Content type:** Authentic daily life, SAHM-style. No affiliate links, no Amazon storefronts, no product-first content.
**Primary signal:** High average comment count — comments from relatability, not giveaway entries.
**Comment pod flag:** Comments 2x+ higher than likes = likely a pod. Flag it, don't approve it.

---

## Scoring System

**ER Score (tiered by follower count):**

| Tier | Followers | Low Floor | High Floor |
|------|-----------|-----------|------------|
| Macro | 500K–5M | 0.8% | 2.0% |
| Mid-tier | 100K–500K | 1.5% | 3.5% |
| Micro | 10K–100K | 3.0% | 6.0% |
| Nano | <10K | 5.0% | 10.0% |

**Comment Score:** Raw average comments per post. This is the boss's primary metric.

Both scores written to sheet for every account. Strong account = high on both.

---

## Discovery Method

**Hashtag scraping via Apify only.** Handle-guessing was attempted in session 2026-03-23 and failed — don't retry.

Script: `scripts/influencer_pipeline.py --mode verify --handles ... --category "CHD"`
Hashtags per category: `scripts/hashtag_config.json`

---

## Key Decisions

- Handle-guessing abandoned 2026-03-23 — always use hashtag discovery
- Regular Mom category: Cherwin approved 5 total (added @thekatiecosta)
- Comment pods flagged: @lovelyluckylife, @pineconesandpacifiers — do not use
- Adult cancer category: approved 2026-03-25, add to next scrape
- Pediatric cancer: approved, not yet scraped
- WebFetch fails on JS-rendered influencer list sites — move on immediately, don't retry

---

## What's Working

- Dual scoring (ER% tiered + comment volume) gives clean comparable results
- Hashtag discovery surfaces authentic accounts better than curated lists
- RESIDENTIAL proxies on Apify — no blocks so far

---

## What to Watch

- Apify free tier resets April 1, 2026
- Some categories may have thin hashtag coverage — expand hashtags before giving up
- Loop giveaway accounts look great on numbers but have inflated ER — check Loop Giveaway History column
