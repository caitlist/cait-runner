# CLAUDE.md — CAIT List Research & Outreach Intelligence Agent
# This file is auto-loaded by Claude Code at the start of every session.

---

## Who We Are

CAIT Connect is a pre-launch AI-powered caregiving app for parents of medically complex and neurodevelopmental children. We help families track health, behavior, and therapy — and provide context-aware AI guidance that gets smarter over time. HIPAA-protected. USA launch April 2026.

This agent's job: build a qualified, enriched pipeline of accounts, communities, and organizations across every CAIT diagnosis category — so the partnerships team can contact the right people at launch with zero manual list-building.

**This is not a scraper. This is a list intelligence employee.**

---

## Agent Identity

- [SOUL.md](SOUL.md) — who this agent is, how it thinks, what it never does
- [IDENTITY.md](IDENTITY.md) — name, role, mission
- [AGENTS.md](AGENTS.md) — non-negotiable operating rules and guardrails
- [USER.md](USER.md) — Cherwin's profile, how to work with him
- [MEMORY.md](MEMORY.md) — business context, what's working, key decisions

---

## Knowledge Base

- [knowledge/cait-product.md](knowledge/cait-product.md) — what CAIT is, value props by audience segment
- [knowledge/diagnosis-categories.md](knowledge/diagnosis-categories.md) — all target diagnoses, community characteristics
- [knowledge/qualification-standards.md](knowledge/qualification-standards.md) — exact filters for every platform and list type
- [knowledge/platform-norms.md](knowledge/platform-norms.md) — Instagram, Facebook, Reddit research norms
- [knowledge/partnership-angles.md](knowledge/partnership-angles.md) — why each account type would partner with CAIT
- [knowledge/sheet-structure.md](knowledge/sheet-structure.md) — Google Sheet tab names, column schemas, rules

---

## Workflows

- [workflows/facebook-group-discovery.md](workflows/facebook-group-discovery.md) — finding USA Facebook groups by diagnosis
- [workflows/instagram-discovery.md](workflows/instagram-discovery.md) — finding qualified Instagram accounts
- [workflows/reddit-discovery.md](workflows/reddit-discovery.md) — finding Reddit caregiving communities
- [workflows/enrichment.md](workflows/enrichment.md) — email and contact enrichment pipeline
- [workflows/weekly-learning.md](workflows/weekly-learning.md) — weekly synthesis and memory update

---

## Scripts

- [scripts/read_sheet.py](scripts/read_sheet.py) — reads ALL tabs, builds master dedup set
- [scripts/facebook_groups.py](scripts/facebook_groups.py) — Apify Facebook group search
- [scripts/instagram_discovery.py](scripts/instagram_discovery.py) — Apify Instagram profile discovery
- [scripts/reddit_discovery.py](scripts/reddit_discovery.py) — Reddit API community discovery
- [scripts/enrich_email.py](scripts/enrich_email.py) — bio + website scrape for contact email
- [scripts/write_sheet.py](scripts/write_sheet.py) — dedup check + write to correct tab
- [scripts/run_discovery.py](scripts/run_discovery.py) — main orchestrator, runs a full category discovery
- [scripts/influencer_pipeline.py](scripts/influencer_pipeline.py) — **NEW 2026-03-23** — verifies influencer handles via Apify, applies dual scoring (ER% tiered + comment volume), writes to "Influencer Pipeline" tab. CLI: `python scripts/influencer_pipeline.py --mode verify --handles handle1 handle2 --category "Name"`

---

## Skills

- [.claude/skills/qualify-account/SKILL.md](.claude/skills/qualify-account/SKILL.md) — qualification scoring logic
- [.claude/skills/enrich-contact/SKILL.md](.claude/skills/enrich-contact/SKILL.md) — email and context enrichment
- [.claude/skills/draft-outreach/SKILL.md](.claude/skills/draft-outreach/SKILL.md) — outreach copy (fires only when explicitly requested)

---

## Google Sheet (Single Source of Truth)

**Sheet ID:** `1GpeLSbjGTcKe_V1gWYehZcPFU8Vai1q4A9-xLnRGFhA`

Tabs and their purpose:
| Tab | Purpose | Status |
|-----|---------|--------|
| 50 Million List | Mid-to-high engagement journey accounts + influencers | Has data — read before write |
| CAIT Community | Therapists, BCBAs, OTs, SLPs, educators selling courses/products | Has data — read before write |
| US ADHD Facebook Group Communities | ADHD groups | **SKIP ENTIRELY — do not read, do not write** |
| US Autism Facebook Group Communities | Autism Facebook groups | Has data — read before write, add 5 |
| US Facebook Medical Moms | Medical mom Facebook groups | Has data — read before write, add 5 |
| US Reddit Medical Moms | Medical parenting Reddit communities | 5 rows |
| US Autism Reddit Group Communities | Autism Reddit communities | 2 rows |
| Foundations & Organizations | Medical parent foundations & advocacy orgs on IG — Mikha outreach via DM | 28 rows — active |

**Zero duplicates rule — non-negotiable:** Before every write, read ALL non-ADHD tabs. Any account/URL/name found in ANY tab is off-limits.

---

## Tools & Credentials

- [TOOLS.md](TOOLS.md) — Apify, Reddit API, Google Sheets API, email enrichment tools
- `.env` — all credentials (never commit)

---

## Current Status (as of 2026-03-19)

### Completed ✅
- Full agent structure built
- All knowledge, workflow, and script files created
- CAIT Community: 27 rows, 25 with emails (2 empty: @thesimpleot, @thekinected_ot)
- Reddit: 5 rows Medical Moms, 2 rows Autism (general subs — Cherwin deprioritized Reddit)
- **Foundations & Organizations: 28 rows across all diagnosis categories — ready for Mikha outreach**
- Foundations script built: `scripts/instagram_foundations.py` (curated seed list, no email enrichment, IG DM only)

### Pending — Next Session
1. Facebook tabs (US Autism + US Medical Moms) — blocked on memo23 actor rental at https://console.apify.com/actors/LbOjFS8sWIy3wl0ak
2. Find active feeding/G-tube org for Foundations tab (Feeding Matters is stale)
3. Breakthrough T1D has no active IG since rebrand — monitor
4. Mikha to begin DM outreach from Foundations & Organizations tab

---

## How to Run

```bash
# Install deps
pip install gspread google-auth apify-client praw requests beautifulsoup4 python-dotenv

# Run a discovery batch (5 results, writes to sheet)
python scripts/run_discovery.py --category facebook_medical_moms
python scripts/run_discovery.py --category facebook_autism_groups
python scripts/run_discovery.py --category instagram_cait_community
python scripts/run_discovery.py --category reddit_medical_moms
python scripts/run_discovery.py --category reddit_autism

# Check what's already in the sheet (dedup preview)
python scripts/read_sheet.py
```

---

## Revenue Goal

CAIT's goal is to build a trusted community of 230K+ families at launch. This agent's job is to make sure every meaningful account in the caregiving space is found, qualified, and in the pipeline before April 2026.
