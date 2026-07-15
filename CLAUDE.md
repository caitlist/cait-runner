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
- [knowledge/engagement-sop.md](knowledge/engagement-sop.md) — Full manual SOP for new hire: hashtag search, adding accounts, validating, commenting, DM templates

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
- [scripts/influencer_pipeline.py](scripts/influencer_pipeline.py) — verifies influencer handles via Apify, applies dual scoring (ER% tiered + comment volume), writes to "Influencer Pipeline" tab. CLI: `python scripts/influencer_pipeline.py --mode verify --handles handle1 handle2 --category "Name"`
- [scripts/runner2.py](scripts/runner2.py) — **daily runner on port 5564 (PERMANENT)**. Tabs: Comments Queue (CQ) + Validation Queue (VQ) + Email + Share Post. Hot-reload: /api/reload-cq and /api/reload-vq. Render runs this via Procfile (`web: python scripts/runner2.py`). runner3.py = identical copy, kept as reference.
- [scripts/runner3.py](scripts/runner3.py) — copy of runner2.py (local reference only — Render runs runner2.py)
- [scripts/score_followers.py](scripts/score_followers.py) — reads handles from `outputs/followers_raw.txt`, deduplicates against sheet, scrapes Apify, scores (PASS_SCORE=15 AND followers>=1000), writes per-batch to Medical Mom DM Outreach
- [scripts/sheet9_to_followers.py](scripts/sheet9_to_followers.py) — reads Sheet9 tab directly from Google Sheets, extracts IG URLs, writes to outputs/followers_raw.txt for score_followers.py
- [scripts/filter_by_followers.py](scripts/filter_by_followers.py) — sorts existing Medical Mom DM Outreach rows by follower count (1000+ / <1000 / unknown). Default start row 1129
- [scripts/insert_t1d_batch.py](scripts/insert_t1d_batch.py) — deletes existing sheet entries for a handle list, re-inserts all at target row (use for any manual batch that needs clean placement)
- [scripts/comments_workflow.py](scripts/comments_workflow.py) — transfer approved accounts to COMMENTS tab (--mode transfer), scrape latest posts (--mode scrape --start-row N), write comments to sheet (--mode write)
- [scripts/move_follower_scrape.py](scripts/move_follower_scrape.py) — moves the follower-scrape block to a target row (insert position), pushing everything else down
- [scripts/score_engagement.py](scripts/score_engagement.py) — discovers high-engagement accounts (Autism Mom / OT / SLP) by avg comments/post (last 10 non-pinned). Writes to HIGH ENGAGERS tab. Saves candidates + profiles to disk after every tag/batch — resume-safe. CLI: `python scripts/score_engagement.py --min-comments 15 --dry-run`
- [scripts/find_loop_giveaway_organizers.py](scripts/find_loop_giveaway_organizers.py) — finds Instagram loop giveaway organizer accounts by scraping 8 loop giveaway hashtags, counting posts per ownerUsername (3+ posts OR 2+ different tags = likely organizer), then profile-scrapes top 30 candidates. Outputs `outputs/loop_giveaway_organizers.json`. Run: `python scripts/find_loop_giveaway_organizers.py`

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

## Current Status (as of 2026-04-16)

### Sheet Row Counts (last verified 2026-04-16)
| Tab | Rows |
|-----|------|
| Medical Mom DM Outreach | ~1,849 (95 T1D kids/adults Batch 6 at rows 1332–1426) |
| COMMENTS | 53 rows scraped, ready to generate (rows 2–54) |
| Email | 426 (has Diagnosis column) |
| Sheet9 | 2,318 |
| Influencer Pipeline | 122 |
| Foundations & Organizations | 41 |
| 50 Million List | 136 |
| CAIT Community | 27 |

### Playwright Posting Method (confirmed 2026-04-23)
```
1. browser_navigate(post_url)
2. browser_fill_form([{selector: "[aria-label='Add a comment…']", value: comment_text}])
3. browser_press_key(key="End")         ← triggers React onChange, shows Post button
4. browser_evaluate("() => { const el = Array.from(document.querySelectorAll('*')).find(b => b.textContent.trim() === 'Post' && b.className.includes('x1i10hfl')); if(el){ el.click(); return 'posted'; } return 'no post btn'; }")
```
Post button is a DIV not a `<button>`. Use 20-second gaps between posts.

### Completed ✅
- Full agent structure, all knowledge/workflow/script files built
- DM outreach pipeline live — Medical Mom DM Outreach tab + COMMENTS tab
- Daily runner at `scripts/runner2.py` — port **5564** local, port **10000** on Render
- Render self-ping added (every 14 min) — prevents free tier sleep / 521 errors (commit 93ac426)
- Comment generation: read `knowledge/comment-examples.md` first, generate in-session. **Always run --mode scrape first to get live COMMENTS tab — never use stale JSON**
- **Watch-before-generate rule** — During comment generation, for each COMMENTS tab row: if the caption is under 150 characters OR contains no specific narrative detail (only emojis, hashtags, or generic phrases like "had the best day", "feeling blessed", "love this"), AND the post URL contains `/reel/` → call `/watch` on that post URL FIRST to get the video transcript before generating the comment. Use specific moments, quotes, or details from the transcript to anchor the comment. Skip `/watch` if the caption already has rich detail (child's name, diagnosis mentioned, specific event described). This fires automatically — no need to ask.
- Auto-scoring pipeline: `scrape_score_new_hashtags.py`, `scrape_platform_articles.py`, `scrape_tiktok_medical_parents.py`
- `score_followers.py` — scores from CSV/follower exports, 1K minimum, writes per-batch
- `sheet9_to_followers.py` — reads Sheet9 tab directly from Google Sheets, extracts IG URLs
- `filter_by_followers.py` — sorts existing sheet rows by follower count
- `insert_t1d_batch.py` — deletes existing entries for a handle list, re-inserts all at target row
- `move_follower_scrape.py` — moves follower-scrape block to any target row
- Sheet9 scored: 299 accounts at rows 1246+ (moved from 1362 → 1238 → pushed by 8 T1D inserts)
- Email tab DM Sent bug fixed: now uses col map + removes from in-memory queue on mark
- Render 521 / host-down fixed: self-ping thread keeps free tier awake permanently
- Render migrated to cait-runner-3 (https://cait-runner-3.onrender.com) — new Render account, same config as cait-runner-2
- Share Post tab added to runner — paste post URL once, copy each handle with one tap, Done only removes from Share Post
- Engagement SOP written for new hire — knowledge/engagement-sop.md
- Email tab Diagnosis column: runner2.py reads "Diagnosis" from Email tab, shows as badge next to Open Profile (commit 057451b)
- Batch 6 T1D kids & adults: 28 new hashtags added, 95 accounts scored + written to rows 1332–1426
- Profile save fix: scrape_score_new_hashtags.py now saves profiles to `outputs/batch{N}_profiles.json` after every 50-profile batch — credits-lost = no data lost
- **Collab post detection fixed**: Apify `latestPosts` uses `ownerUsername` not `coauthorProducers`. comments_workflow.py now skips posts where `ownerUsername != account handle`. Use `--force` to re-scrape all when fixing collab bugs.
- **Playwright MCP live**: posts comments via Edge CDP endpoint (localhost:9222). Config in `~/.claude.json` mcpServers. User opens dedicated Edge shortcut with remote debugging, then reloads Claude Code. All 34 COMMENTS tab accounts posted (rows 2–35).
- Batch 7 T1D Community & Lifestyle: 26 hashtags, 55 scored accounts inserted after last validated row. scrape_score_new_hashtags.py now has batch 7 defined.
- **Insert rule**: Always insert new scored accounts at the row AFTER the last validated row (APPROVE/Not Valid), pushing everything down. Never hardcode row numbers.
- Sheet sort: rows 1366+ sorted T1D first (rows 1366–1474), then non-T1D. Within T1D: 1000+ followers first.

### Sheet Row Counts (last verified 2026-04-28)
| Tab | Rows |
|-----|------|
| Medical Mom DM Outreach | ~2,088. Last validated: row 1622. Batch 23 (GoFundMe) at rows 2028–2030 (3 accounts). CAIT×Claude CSV scored: 58 accounts appended after row 2030. |
| COMMENTS | 18 accounts transferred — scrape pending (needs Apify) |
| Email | 159 |
| Influencer Pipeline | 122 |
| Foundations & Organizations | 41 |
| HIGH ENGAGERS | 15 (Autism Mom 9, SLP 5, OT 1 — avg comments/post metric) |

### International Beta Tester Block (rows 1623–1663)
| Rows | Country | Count | Key hashtags used |
|------|---------|-------|-------------------|
| 1623–1628 | UK R1 | 6 | #specialneedsmumuk, #senparenting |
| 1629–1633 | India R1 | 5 | #autismmomindia, #t1dindia, #specialneedsindia |
| 1634–1636 | Malaysia | 3 | #autismmommalaysia, #specialneedsmalaysia |
| 1637 | Indonesia | 1 | #specialneedsindonesia |
| 1638–1655 | UK R2 | 18 | #autismmum, #senmum, #ehcp, #sendmum, #cancermum |
| 1656–1663 | India R2 | 8 | #autismindia, #downsyndromeIndia, #specialkidsindia |

Script batches 12–22 added to `scripts/scrape_score_new_hashtags.py`. Run with `--posts-per-tag 50` for international batches.
**Completed**: Indonesia R2 (Batch 21) — 3 accounts. South Africa R2 (Batch 22) — 0 passed (tags private/empty).
**Key learning**: "mum" spelling = near-100% UK signal. Bahasa tags need separate profile recheck. Clinics/doctors slip through India scoring — watch for "dr" prefix handles.

### Key Rules (updated 2026-04-22)
- **5K follower minimum** — universal across ALL pipelines as of 2026-04-22. Use `--min-followers 5000` on all scrape/score scripts.
- **Column I = follower count** — scripts write 9 cols (A:I). Col H = APPROVE/Not Valid. Col I = "X,XXX followers".
- **Adults only for T1D** — all other diagnoses require parent accounts. Child must have condition. Adult self-posts disqualified.
- **Parent-anchored hashtags** — use -mom/-mama/-dad/-parent suffix tags. Warrior/awareness tags pull adults and orgs.
- **Insert after last validated row** — always insert new batches at row after last APPROVE/Not Valid, pushing everything down. Never append to bottom.
- **Excluded categories** — Do NOT scrape: Down Syndrome, Cerebral Palsy, Hearing loss, Vision/CVI.

### Playwright fill_form Note (2026-04-24)
- Use `selector: "[aria-label='Add a comment…']"` in fill_form — `ref` is page-specific and goes stale across navigations. Selector works reliably on every post page.

### Key Rules (updated 2026-04-28)
- **GoFundMe = instant pass** — if "gofundme" appears in bio, score_account() returns 100 immediately. Strongest signal of genuine medical family. Added to scrape_score_new_hashtags.py.
- **score_followers.py Unicode fix** — added `sys.stdout.reconfigure(encoding='utf-8')` to fix Windows cp1252 crash on arrow character.
- **Render URL** — now https://cait-runner-3.onrender.com (new account, same config as cait-runner-2).
- **comments_workflow.py dotenv fix** — changed from `load_dotenv()` to `dotenv_values()` so Apify token always reads fresh from .env. load_dotenv() won't override existing env vars.
- **SAFE ROW MOVE rule (CRITICAL)** — NEVER use source-tag matching to identify rows to move. Source tags overlap across batches and will catch validated rows. ALWAYS use positional tail move: record N_before, run script, delete rows N_before+1 to N_after, insert at target row.

### Key Rules (updated 2026-04-28c)
- **score_followers.py fixes** — MIN_FOLLOWERS corrected from 1000 → 5000. Col I now writes follower count ("X,XXX followers"). Both bugs fixed 2026-04-28.
- **Always check last validated row live before inserting** — never assume it's row 1623 or any hardcoded number. Read the sheet, find last row where col H = "APPROVE" or "Not Valid", insert at that row + 1.
- **Verify CSV source before scoring** — confirm accounts are medical parents (not doctors, clinics, orgs) before running through score_followers.py. Scoring catches many but not all wrong types.

### Key Rules (updated 2026-04-29)
- **India hashtag approach is EXHAUSTED** — all compound India-suffix tags (#chdmomindia, #type1diabetesindia, #nicumomindia, etc.) return NO RESULTS on Instagram. Do NOT add more India hashtag batches. To find more Indian accounts: scrape followers of known large Indian medical accounts (anmolchaudharyofficial 344K, awetisminsights 76K, thebiggishboy 168K) via Apify paid follower scraper.
- **Backup CSV fully exhausted** — outputs/followers_raw_backup.txt (1,132 handles) fully processed. 0 remaining.
- **Batches 24–26 all returned 0** — rare cancer tags (B24), India compound tags (B25), India T1D+cancer (B26) all dead. Hashtag approach is saturating for niche/international categories.
- **comments_to_write.json format** — must be `{str(row): comment_string}` plain dict, NOT nested dict. Script line 444 does the conversion.

### Key Rules (updated 2026-04-29b)
- **No em dashes in comments** — never use — in generated Instagram comments. Replace with a comma instead.
- **429 = Instagram rate limit, not Apify credits** — new Apify account does NOT help. 429s are Instagram throttling Apify's shared proxy pool. Only fix: wait 12–24 hours before retrying.
- **Runner "Posted" status ≠ actually commented** — runner marks "Posted [date]" when user clicks Done after DM. Playwright is still needed for the actual Instagram comment.
- **Batch 27 (Australia R1) ready** — 16 tags (ndismum, ndisparents, ndiskids, ndislife, autismmumaustralia, etc.). Retry tomorrow morning: `python scripts/scrape_score_new_hashtags.py --batch 27 --posts-per-tag 50 --min-followers 5000`

### Key Rules (updated 2026-05-05)
- **Asian diaspora compound hashtags EXHAUSTED** — identity+diagnosis compound tags (#filipinoautismmom, #asianspecialneedsmom, #hmongspecialneedsmom, #koreanautismmom, etc.) don't exist on Instagram at usable volume. Batch 40 tested 16 tags, 3 candidates, 0 passed. Do NOT create more Asian identity+diagnosis hashtag batches. Unlike the Black community (#blackmomautism has real volume), Asian diaspora parents use general diagnosis tags only. Only viable paths: paid Apify follower scraping ($49/mo), manual browsing, or commenter scraping on known org posts.
- **Apify credits (May)** — $1.36/$5 used as of 2026-05-05. ~$3.64 remaining. Credits reset monthly.

### Key Rules (updated 2026-05-06)
- **Asian batches B41–B44 = English-only hashtags** — no native language hashtags (Japanese script, Korean, Thai, Vietnamese etc.) because accounts found via non-English tags likely don't speak English (CAIT is English-only app). Scorer DOES have native language medical/parent keywords added to help score bilingual bios.
- **No minimum followers for Asian batches B41–B44** — omit `--min-followers` flag entirely (default = 0). Scorer passes any account with score ≥ 5 and at least 1 follower.
- **B41 = country test batch** — run with `--posts-per-tag 20` first to identify which countries have real volume before going deeper. 2 tags per country: Philippines, Vietnam, Thailand, Korea, Japan, Taiwan, Bangladesh, Pakistan, India (new angle), Singapore (new angle).
- **B42 = Philippines deep, B43 = Korea+Japan deep, B44 = Vietnam+Thailand+SEA deep** — run only for countries that showed volume in B41.
- **Run command for Asian batches**: `python scripts/scrape_score_new_hashtags.py --batch 41 --posts-per-tag 20` (test), then `--posts-per-tag 50` for deep dives. No `--min-followers` flag.
- **COMMENTS tab Runner Status vs actual posting** — "Posted [date]" in Runner Status col = Cherwin clicked Done in the runner app (marks DM sent). Does NOT mean the Instagram comment was actually posted via Playwright. Always check which rows have Runner Status before Playwright session.

### Key Rules (updated 2026-05-06b)
- **B41 country test ran — 39 accounts written then DELETED** — most were orgs/community pages, not real moms. Country-specific hashtags (#autismphilippines, #autismkorea) pull org accounts, not individual parents.
- **Country-specific hashtag strategy ABANDONED for Asian outreach** — real Asian medical moms use general diagnosis hashtags (#autismmom, #t1dmom, #heartmom) same as US moms, not country-specific tags. @heyitsr0sie (14.9K, autistic son Ethan) is the gold standard — uses #autismawareness not #autismphilippines.
- **Gold standard account: @heyitsr0sie** — 14.9K followers, NOT a business account, bio says "yes i'm a mommy #autismawareness", personal posts about autistic son Ethan (haircut struggles, sensory sensitivity). This is what we're looking for: real person, specific named child, personal daily life content, genuine engagement.
- **Scorer upgraded (2026-05-06b)** — three new layers added to scrape_score_new_hashtags.py:
  1. `score_content(posts)` — looks at latestPosts captions: "my son/daughter", "he was diagnosed", "our journey" = personal (+5 each, max +20); "join us", "register now", "our program" = org (-10 each)
  2. `is_org_handle(handle, hashtag)` — handle = exact hashtag name → org (-40); 2+ org terms + no digits → org (-40); handle has "mom/mama/dad/parent" → person (override)
  3. `MIN_FOLLOWERS=500` hardcoded for batches 41-44; country batch pass score raised 5→10; 30+ new ORG_BIO_SIGNALS added
- **BATCH_45: Global Medical Moms Deep Scrape** — PENDING. Use ~41 general parent-anchored diagnosis tags at 150 posts/tag. Goes 3-5x deeper than batches 1-11. Asian moms appear naturally because they use the same general hashtags. All diagnoses covered: autism, T1D, epilepsy, CHD, cancer, NICU, HIE, rare disease, medical complex, special needs, trach/gtube, ADHD, allergy, SMA, sensory/SPD, TBI, CF, sickle cell.

### Key Rules (updated 2026-05-06c)
- **BATCH_46 (Childhood Cancer) complete** — 16 tags, 45 accounts passed scoring, now at rows 1815–1859. Any race/ethnicity. Min followers 500. Tags: childhoodcancermom, cancermom, leukemiamom, braintumormom, neuroblastomamom, goldribbonmom, etc.
- **BATCH_47 (Latina Medical Moms) defined** — 16 tags: latinamom, latinaspecialneedsmom, latinamomautism, latinaautismmom, hispanichemom, chicanamother, latinamomlife, momlatina, etc. All diagnoses. 500 min followers. Run: `python scripts/scrape_score_new_hashtags.py --batch 47 --posts-per-tag 50 --min-followers 500`
- **Insert-after-validated rule violation + fix pattern** — B46 script appended to bottom (rows 2143–2187) instead of inserting after last validated row. Fix: safe positional tail move — `ws.delete_rows(2143, 2187)` then `ws.insert_rows([['']*9]*45, row=1815)` then `ws.update('A1815:I1859', tail_rows)`. This is the correct recovery pattern any time append-to-bottom happens by mistake.
- **Apify balance ~$0.84 remaining** — after B46 + B47 planning. Reset June 1. Run B45/B47/B48 after reset.
- **--force flag destroys manually-entered captions** — if user manually adds a caption to the sheet, do NOT run `--mode scrape --force`. Ask user to paste the caption text in chat instead and generate comment from that.

### Key Rules (updated 2026-05-11)
- **BATCH_45 redefined — SOP Medical Hashtags (not general autism)** — pivot from 150-posts/tag general tags to SOP master hashtag list. Excluded: Autism, Down Syndrome, Cerebral Palsy, T1D (not needed this round). ~50 tags. Categories: Medically Complex, Epilepsy/Seizure, CHD, Cystic Fibrosis. Run after June 1 Apify reset.
- **BATCH_48 = second half of SOP hashtag list** — ~45 tags. Categories: Pediatric Cancer, NICU/Preemie, Feeding/Gtube, Rare/Genetic Syndromes + HIE, Spina Bifida. Run after B45.
- **Hashtag strategy = SOP-anchored** — the engagement SOP document is the canonical source. Autism is NOT medically complex enough for B45/B48. Focus: medically complex kids with specific diagnoses.
- **COMMENTS tab rows 9–41 posted (2026-05-11)** — all posted via Playwright at 4s gaps except rows 20 (@itskaylayounger), 23 (@kkatiejohnston — video post), 26 (@momofmightykids). SENSITIVE rows 24 + 32 approved and posted mid-session.

### Key Rules (updated 2026-05-12)
- **BATCH_45 narrowed — Medically Complex General ONLY** — 15 tags: medicalmom, medicallycomplex, medicalkid, complexneeds, medicallyfrailchild, hospitallife, medicalmama, specialneedsmom, raredisease, undiagnosed, trachmom, tracheostomy, medicalkiddo, rareparent, sickiekid. Epilepsy/CHD/CF deferred to later run.
- **B45 NOT in COUNTRY_BATCHES** — plain US batch. Standard PASS_SCORE=15. No org reporting, no content scorer. Orgs silently fail.
- **B45 3K min followers hardcoded** — `if args.batch == 45 and MIN_FOLLOWERS < 3000: MIN_FOLLOWERS = 3000`. No flag needed at runtime.
- **B45 run command**: `python scripts/scrape_score_new_hashtags.py --batch 45 --posts-per-tag 100`
- **B45 ran 2026-05-12** — 13 accounts passed scoring, at rows 1860–1872. 6 flagged as likely orgs for Cherwin to mark Not Valid: @clinuvel_pharmaceuticals, @nord_rare, @rarediseaseadvisor, @ucchvas, @socal.epilepsy, @autisticinclusive.
- **--max-followers flag removed** — not needed, keep scoring simple.

### Key Rules (updated 2026-04-29c) ← PERMANENT, NEVER REVERT
- **NEVER pass proxy config to Apify actors** — do NOT use `"proxy": {"useApifyProxy": True}` or `"apifyProxyGroups": ["RESIDENTIAL"]` in ANY Apify run_input in ANY script. Omit the proxy field entirely. When proxy is specified and 0 residential proxies are available (free plan), Instagram blocks all requests with 429s immediately. Without proxy field, actor uses its own default connection and works fine. Fixed across all 23 scripts 2026-04-29. Run `grep -r "apifyProxyGroups\|useApifyProxy" scripts/` to catch any new violations.
- **International org strategy** — when scraping country hashtags, flag accounts that look like organizations (foundations, societies, associations, clinics) separately from individual parent accounts. Orgs are follower-scrape seeds, not direct DM targets. Report them to Cherwin so he can check their followers for individual medical parent accounts.
- **Batches 25, 26 confirmed dead** — re-ran after proxy fix. India compound hashtags return NO RESULTS on Instagram regardless of proxy. Truly exhausted.
- **Batch 27 Australia R1** — ready to run. Not re-run yet.

### Key Rules (updated 2026-04-30)
- **Org scoring strengthened** — `ORG_BIO_SIGNALS` now includes: society, ngo, support group, resource center, alliance, council, institute, coalition, bureau, join our community, our community, our network, our programs, our services, follow us, our page, our platform, we help families, we support families. Therapists/clinicians NOT included — they are individuals.
- **Country batch org reporting** — `COUNTRY_BATCHES = {12..39}`. After scoring, failed accounts with 5K+ followers matching `ORG_FLAG_KEYWORDS` are printed as "ORGS FOUND — check their followers." Never written to sheet. Non-country batches: orgs fail silently as before.
- **India next step: follower scraping only** — hashtag approach fully exhausted (confirmed twice). Need paid Apify ($49/mo) to scrape followers of: indiaautismcenter (51K), awetisminsights (77K), apd_india (24K), cankidskidscan (10K), anmolchaudharyofficial (344K), thebiggishboy (168K).
- **TBI = medically complex, valid for outreach** — Batch 32 complete: 3 accounts (rows 2132–2134) + shannelpearman (row 2135).
- **Malaysia + HK hashtag approach exhausted** — compound country tags return 0 or sub-5K accounts. Like India, Malaysia/HK need follower scraping of known large accounts.
- **Regular moms allowed for Asian batches** — country batches use effective PASS_SCORE=5 (vs 15 for US batches). Catches lifestyle moms without medical signal in bio.
- **scrape_score_new_hashtags.py Unicode fix** — `sys.stdout.reconfigure(encoding='utf-8')` added at top. Fixes cp1252 crash on emoji/special chars in org seed bio print.
- **Asian lifestyle batches added** — B36 Singapore (#sgmom, #sgmum, #sgfamily etc.), B38 Malaysia (#malaysianmom, #mommalaysia etc.). B37 HK + B39 Thailand skipped per user decision.
- **Apify credits exhausted** — B38 Malaysia hit monthly limit. Re-run next month.
- **HK org seed** — @yogachung (72K, BEYOND Foundation HK, Ambassador RDA HK). Good follower-scrape seed when Apify upgraded.
- **Parallel batch collision** — never run two batches simultaneously. Both read next_row at same time and overwrite each other. Always run sequentially.

### Key Rules (updated 2026-05-12b)
- **BATCH_49 (Medical Moms + Autism Moms) complete** — 20 tags: medicalmom, medicalmomlife, medicalmama, specialneedsmom, medicallycomplex, medicalkid, medicalkiddo, hospitallife, complexneeds, medicalkids + autismmom, autismmomlife, autismmama, autismparent, autismfamily, autismjourney, raisingautism, autismdad, nonverbalmom, autismkid. 39 accounts passed scoring, inserted at rows 1928–1966.
- **B49 2K min hardcoded** — `if args.batch == 49 and MIN_FOLLOWERS < 2000: MIN_FOLLOWERS = 2000`. No flag needed at runtime.
- **B49 run command**: `py scripts/scrape_score_new_hashtags.py --batch 49 --posts-per-tag 100`
- **B49 NOT in COUNTRY_BATCHES** — plain US batch, PASS_SCORE=15, no org reporting.
- **COMMENTS tab fully posted (2026-05-12b)** — all 29 rows posted via Playwright at 4s gaps. @judith_riva (SENSITIVE) approved and posted mid-session. @raising_rouses deleted by Cherwin before session started.

### Sheet Row Counts (last verified 2026-05-12b)
| Tab | Rows |
|-----|------|
| Medical Mom DM Outreach | ~2,239. Last validated: row 1927. B49 Medical+Autism Moms at rows 1928–1966 (39 accounts, pending validation). Rows 1967+ = other batches pending. |
| COMMENTS | 0 rows — fully cleared. All 29 posted. |
| Email | 159 |
| Influencer Pipeline | 122 |
| Foundations & Organizations | 41 |
| HIGH ENGAGERS | 15 |

### New Batch Reference (B27–B44)
| Batch | Market | Tags | Result |
|-------|--------|------|--------|
| B27 | Australia R1 | ndismum, autismmumaustralia, etc. | 1 (@strongherside 28K, row 1806) |
| B28 | Latina/Hispanic | mamaespecial, autismmomlatina, etc. | pending — run when Apify credits reset |
| B29 | Black/AA | blackmomautism, melaninspecialneedsmom, etc. | 5 (rows 1798–1803, validated) |
| B30 | Singapore R1 | autismsingapore, t1dsingapore, etc. | 1 — Not Valid (clinic) |
| B31 | Malaysia R2 | mum variants, Bahasa | 0 — exhausted |
| B32 | TBI | tbimom, braininjurymom, pediatrictbi | 3 valid (rows 1807–1809) + anchor_rehab Not Valid (row 1808) |
| B33 | Hong Kong | autismmomhongkong, specialneedshk | 0 — org seed: @yogachung 72K |
| B34 | Singapore R2 | sg suffix | 1 (@wiishinstar 9K, row 1804 — pending validation) |
| B35 | Thailand | autismmomthailand, etc. | 1 (@tuttidada 10.9K, row 1805 — pending validation) |
| B36 | Singapore lifestyle | sgmom, sgmum, sgfamily, etc. | 5 (rows 1810–1814 — pending validation) |
| B37 | HK lifestyle | skipped | — |
| B38 | Malaysia lifestyle | malaysianmom, mommalaysia, etc. | 0 — Apify credits exhausted, re-run May |
| B39 | Thailand lifestyle | skipped | — |
| B40 | Asian diaspora medical | filipinoautismmom, asianspecialneedsmom, hmongspecialneedsmom, etc. | 0 — hashtag approach confirmed dead for Asian compound tags |
| B41 | Asia Country Test | autismphilippines, autismvietnam, autismkorea, etc. | ABANDONED — 39 accounts all orgs/community pages, deleted from sheet |
| B42 | Philippines Deep | autismmomph, epilepsyph, heartwarriorph, etc. | On hold — country approach abandoned |
| B43 | Korea + Japan Deep | autismkorea deep, autismjapan deep (English only) | On hold — country approach abandoned |
| B44 | Vietnam + Thailand + SEA Deep | autismvietnam deep, autismthailand deep, etc. | On hold — country approach abandoned |
| B45 | Medically Complex General | medicalmom, medicallycomplex, medicalkid, complexneeds, trachmom, raredisease, etc. (15 tags) | 13 accounts — rows 1860–1872 (pending validation). 6 likely orgs flagged. |
| B46 | Childhood Cancer (any race) | childhoodcancermom, cancermom, leukemiamom, braintumormom, goldribbonmom, etc. | 45 accounts — rows 1815–1859 |
| B47 | Latina Medical Moms (any diagnosis) | latinaspecialneedsmom, latinamomautism, latinaautismmom, latinamedicalmom, latinacancermom, hispaniccancermom, hispanicspecialneedsmom, latinaheartmom, autismomlatina, mamaespecial, mamadeautista, mamaautismo, hijoespecial (14 tags) | 4 accounts — rows 2036–2039 (pending validation). 1K min. |
| B48 | SOP second half: NICU/Preemie, Feeding/Gtube, Spina Bifida, CF, CHD deep, Rare/Genetic moms (42 tags) | nicubaby, preemie, preemieparent, feedingtherapy, gtube, gtubekid, spinabifida, cfwarrior, cysticfibrosis, hlhswarrior, dup15qmom, etc. | 32 accounts — rows 2004–2035 (pending validation). 2K min. |
| B49 | Medical Moms + Autism Moms (general identity tags) | medicalmom, medicalmomlife, autismmom, autismmomlife, autismparent, raisingautism, etc. (20 tags) | 39 accounts — rows 1928–1966 (pending validation). 2K min followers. |
| B50 | Black Medical Moms (any diagnosis, beyond B29) | blackmedicalmom, blackmedicalmama, blackmedicalkid, melaninmedicalfamily, melaninmedicalmom, blackspecialneedsfamily, blackmomspecialneeds, blackcancermom, blackheartmom, blackheartwarrior, blackchronicillnesskid, blackmomraredisease (12 tags) | 2 accounts — rows 2040–2041 (pending validation). 1K min. |
| B51 | Medically Complex + Medical Mom deep pass | medicallycomplex, medicalmom, medicalmama, medicalmomlife, medicalkid, medicalkiddo, medicalkids, complexneeds, hospitallife, medicallyfrailchild (10 tags, 150 posts/tag) | 24 accounts — rows 1958–1981 (pending validation). 1K min. Dedup handled overlap with B45/B49. |

### Key Rules (updated 2026-05-13)
- **B47 restrategized** — removed all general Latina lifestyle tags (#latinamom, #latinamomlife, #latinachingona etc.). Kept only compound tags: Latina+medical/special needs. Added Spanish compound tags for bilingual moms. Any diagnosis (not just autism). 1K min hardcoded.
- **B50 new batch** — Black medical moms going beyond B29's autism focus. Any diagnosis. Tags NOT in B29. 1K min hardcoded.
- **Playwright gap = 6 seconds** — increased from 4s to 6s between posts as of 2026-05-13.
- **Apify new account active** — fresh credits available. Billing cycle resets June 8.
- **General identity/lifestyle tags = wrong approach for diversity batches** — broad tags (#latinamom, #blackmom) pull lifestyle moms with no medical signal. Only use compound identity+diagnosis tags for diversity batches.

### Key Rules (updated 2026-05-15)
- **B47 ran** — 4 accounts (vibeswithjennie, uptownmamisnyc, milegasi, la_ena93). Compound-only tags produce small but targeted pool as expected.
- **B50 ran** — 2 accounts (toreia, bruddaroots). Same reason — compound tags = small but right.
- **B48 coded and ran** — 42 tags, 2K min followers hardcoded. Categories: NICU/Preemie (fresh tags), Feeding/G-tube (fresh tags), Spina Bifida, Cystic Fibrosis, CHD deep (hlhs variants), Rare/Genetic mom variants. 32 accounts passed. All fresh tags not in B1/B2/B10.
- **B48 tag note** — feedingtherapy/gtubekid may pull therapy clinic accounts. Cherwin should spot-check when validating.
- **Apify billing cycle = June 8 reset** — confirmed from API. Not June 1.

### Key Rules (updated 2026-05-16)
- **COMMENTS posted (2026-05-15/16)** — 20 comments posted via Playwright (rows 4,5,6,7,9,10,11,12,13,14,15,17,18,19,20,21,23,24,25,26). Rows 2,3,8,16,22 skipped (no comment). Row 5 (@electriccoconut) had limited comments but went through.
- **B51 Medically Complex deep pass** — 10 tags × 150 posts/tag, 24 accounts passed, inserted at rows 1958–1981 (after last validated row 1957 — Cherwin had been validating). 1K min hardcoded. NOT in COUNTRY_BATCHES. Run command: `py scripts/scrape_score_new_hashtags.py --batch 51 --posts-per-tag 150`
- **Apify budget after B51** — ~$0.54 remaining this cycle (resets June 8). Enough for one more comment scrape session, not another hashtag batch.
- **Watch-before-generate rule live** — during generate, auto-call `/watch` on reel posts where caption < 150 chars OR generic. No reels in today's batches so rule was not triggered. Rule is permanent in CLAUDE.md.
- **Last validated row = 1957** — Cherwin has been validating actively between sessions. Always check live before inserting.

### Key Rules (updated 2026-05-19)
- **COMMENTS old tab posted (2026-05-19)** — rows 2–27 posted via Playwright (6s gaps), skipping rows 18 (@rockwithrach) and 26 (@eli_89_88). SENSITIVE rows 2, 16, 24 approved and posted.
- **New COMMENTS tab: 28 accounts (rows 2–29)** — all 28 comments generated and written. Em dash sweep done (rows 2, 6, 7, 12, 14, 17, 26, 27 fixed). SENSITIVE rows 4, 9, 15, 28 approved.
- **Row 27 (@alex_the_great_cpkid) alt post** — main post had empty caption; updated to alt URL https://www.instagram.com/p/DYFEMskI8WX/ (Whiteleys Retreat post). Comment generated from that caption.
- **Row 29 (@eiansjourney) via /watch** — all post captions empty; used /watch on reel to see 38s hospital toddler video. Comment anchored to specific video details (monitoring leads, nasal cannula, Eian vocalizing "Ah!").
- **Skin tone emoji modifier bug** — `🎻` is U+1F3BB (violin 🎻), NOT skin tone modifier. Fix: omit skin tone modifiers entirely from all emoji in generated comments. Affected rows 11 and 14 this session.
- **Read from sheet for Playwright** — user may edit comments between sessions. Always read live sheet col E before Playwright posting. Never use in-memory values from generate session.

### Key Rules (updated 2026-05-20)
- **COMMENTS posted (2026-05-19/20)** — 24 comments posted via Playwright (6s gaps), skipping rows 2, 18, 21, 27 per Cherwin. Rows 6 (@ethans.curls), 10 (@thebunnyfamilee), 24 (@mama.munn) showed "limited" on first attempt but all went through on retry. COMMENTS tab fully cleared.
- **Scrape URL freshness** — if an account posts new content after the scrape runs, the URL in the sheet will be stale. Swap col C manually before Playwright if you see a newer post.
- **New COMMENTS tab (2026-05-20): 26 handles** — written directly from user-provided profile URLs (not via --mode transfer). savvbeee appeared twice in list, deduplicated to 26. 25 comments generated and written. Row 24 (@_amandatrojan) blocked by Apify, no comment. Row 10 (@musingsofamedicalmom) SENSITIVE (terminal diagnosis post).
- **User-provided handles → COMMENTS tab** — when Cherwin pastes profile URLs directly, extract handles, write Handle + IG Profile Link to COMMENTS tab, run --mode scrape, then generate. No need to route through Medical Mom DM Outreach.
- **5 accounts under 1K followers in this batch** — jordithehiero (682), parkers_journey24 (238), raisingnathanbrave (804), thelionfoundation25 (607), stormysmokes1 (344). User added them directly so generated anyway.

### Key Rules (updated 2026-05-21)
- **COMMENTS posted (2026-05-20/21)** — 24 comments posted via Playwright (rows 2–28, skipping 11, 16, 22). Row 10 (@musingsofamedicalmom, SENSITIVE terminal diagnosis) approved and posted mid-session.
- **New COMMENTS batch (2026-05-21): 28 accounts (rows 2–29)** — 28 URLs pasted (27 unique after oibelieveinisaiah dup + @mere.white manually inserted at row 22). All 28 comments generated. SENSITIVE: rows 8 (@rollin.n.rockin), 17 (@prayersforsophie brain surgery), 21 (@maggieslittleliverstory PICU). Playwright pending.
- **Apify credits exhausted — resets June 1** — current account (bautistakare29@gmail.com) at $5.41/$5.00. Cycle ends May 31, resets June 1. Previous "June 8" note was incorrect.
- **Manual caption → generate without scraping** — when user inserts a handle + caption directly into the sheet and says "generate", read col D from live sheet and generate from that. No scrape needed.
- **Apify billing cycle correction** — resets June 1 (end of calendar month), not June 8. June 8 was a one-time anomaly from new account signup timing.

### Key Rules (updated 2026-05-21b)
- **Re-scrape before Playwright** — always run `--mode scrape --force` before any Playwright session to check for newer posts. Compare old vs new post URLs. For any row where URL changed: if new URL contains `/reel/` run `/watch` first, then regenerate comment. Non-reel changed posts: regenerate from new caption directly.
- **--force scrape overwrites manually-entered captions** — before running `--force`, read and save any manually-entered col D captions (e.g. @mere.white). Restore them to col D immediately after scrape completes.
- **DM nudge MUST explicitly say "DMs"** — phrases like "We sent a little love your way" with no DM mention are wrong. Users won't know where to look. Every comment must include one of the approved phrases from comment-examples.md that explicitly says "DMs". Vary the phrasing across the batch — never repeat back-to-back.
- **Apify credits active (new cycle)** — scrape succeeded 2026-05-21b, credits available. Monitor balance.

### Key Rules (updated 2026-05-26)
- **COMMENTS posted (2026-05-21b/26)** — 26 comments posted via Playwright (rows 3–29, skipping rows 2, 11, 18). SENSITIVE rows 17 (@prayersforsophie) and 21 (@maggieslittleliverstory) approved and posted. Row 3 wrong comment deleted by Cherwin, new comment re-posted.
- **New COMMENTS batch (2026-05-26): 21 rows (rows 2–21)** — 20 handles from user-pasted profile URLs, 1 dup (skelly0415) removed. Scraped via Apify. 19 comments generated + written. Row 8 (@emmaintexas) had no posts initially — user added birthday post URL/caption later, comment generated. Row 19 (@olivia_lipomyelomeningocele) inserted by user mid-session; handle extracted from profile URL. SENSITIVE: rows 12 (@zoeysfight) and 17 (@live.like_levi) — Cherwin must approve before posting.
- **No DM nudge for specific rows** — rows 18 (@jordithehiero) and 19 (@olivia_lipomyelomeningocele) in this batch have comment only, no DM nudge per Cherwin's instruction. This is account-specific — not a general rule.
- **Profile URL → handle extraction** — when user pastes Instagram profile URLs with `?igsh=` tracking params, extract handle via regex `instagram\.com/([^/?]+)`. Write handle to col A, keep full URL in col B.
- **Apify billing cycle resets June 1** — confirmed. Credits used this session for 19-account scrape.

### Key Rules (updated 2026-05-26b)
- **COMMENTS posted (2026-05-26b)** — 17 comments posted via Playwright (6s gaps), skipping rows 4, 10, 15. Row 19 (@olivia_lipomyelomeningocele) comment regenerated via /watch before posting (23s baby-in-pram reel). Row 5 (@dnaiyahthemiraclebaby) typo fixed ("everyting really is govan" → "everything really is golden") before posting. COMMENTS tab fully cleared.
- **Instagram /p/ URLs can be reels** — Instagram uses /p/ for both photos AND reels. Cannot determine content type from URL alone. When user confirms it's a reel, run /watch immediately. When uncertain and caption is short/generic, ask before generating.
- **QA Sheet connected** — Sheet ID: `1WFqLoIBFckYz-VZsUBFczALLz1rtp_sFJz1u5Eyk5y8`. Tabs: Template (gid=0), Cherwin (gid=675218711), Gen (gid=1288761154), Alyssa (gid=182642775). Service account cait-list-agent@sixth-backbone-490610-d8.iam.gserviceaccount.com needs Editor access (not Viewer) to write.
- **QA format rules** — PROBLEM labels: red (255,0,0). FEATURE/EXPECTED RESULT/ACTUAL RESULT: black. 1 blank row after each ACTUAL RESULT. Start by copyPaste Gen → Cherwin (PASTE_NORMAL copies fonts/colors/spacing). Then insert rows for extra content (Gen has 2 problems/day; insert extra rows to accommodate more). Screenshots section stays at row 41.
- **scripts/qa_write.py** — rewrites Cherwin's QA tab: clear → copy Gen → insert 16 rows before row 25 → clear Monday col B+C rows 8–39 → write content with red PROBLEM labels, BLACK for all other labels. Update rows_data list and re-run for each new QA session.

### Key Rules (updated 2026-05-27)
- **COMMENTS posted (2026-05-27)** — 18 comments posted via Playwright (6s gaps), skipping rows 4 (@jesskkramer) and 9 (@stefanietrask). Row 3 (@bethany.hildebrandt) SENSITIVE approved and posted. COMMENTS tab fully cleared.
- **Row 19 alt post used** — @inrareformmom latest post was just "#memorialday 🇺🇸" (15 chars, no content to anchor to). Used rank 2 sibling post (Johnny/Dominic, #specialneedsmom) and updated col C URL before posting. When latest post has no usable content, check alternatives and use the next meaningful post.
- **Page drift fix pattern** — if fill_form lands on wrong page URL after navigate, re-navigate explicitly and redo fill. Check page URL in tool result before filling.

### Key Rules (updated 2026-05-29)
- **COMMENTS tab workflow changed (PERMANENT)** — Cherwin now pastes profile URLs directly into col B of COMMENTS tab. No longer uses `--mode transfer`. When col A is empty and col B has URLs: extract handles via `instagram.com/([^/?]+)` regex, write to col A, run `--mode scrape`, then generate. `--mode transfer` is obsolete for daily workflow.
- **QA column structure** — Mon=B+C, Tue=F+G, Wed=J+K, Thu=N+O, Fri=R+S. Same-feature problems on same day: omit second FEATURE row, continue directly with PROBLEM label.
- **QA format rules (PERMANENT — DO NOT CHANGE)** — scripts/qa_write.py must always: (1) insert 50 rows before row 22 (index 21→71) to push Gen screenshot section down; (2) unmerge entire content area rows 8–71 after copy from Gen; (3) write label+content to adjacent columns (B+C, F+G, R+S etc.), never skip columns; (4) apply `wrapStrategy: WRAP` to every written cell; (5) run final `repeatCell` WRAP pass across all day columns rows 8–65. Confirmed correct format 2026-06-02. Never revert insert point or remove unmerge step.
- **QA Problems 25–29 logged** — P25/P26 → May 27 (J+K rows 8–16). P27/P28/P29 → May 28 (N+O rows 8–20).
- **Apify credits refilled (2026-05-29)** — Cherwin updated Apify account. Credits available now. Billing cycle: resets June 1 (end of calendar month).

### Key Rules (updated 2026-06-01)
- **Regular moms ≠ medical moms** — allergy, SPD, ADHD, preemie, asthma moms are still "medical moms by behavior" (doctor checkups, medications, appointments). Do NOT use them in regular mom batches. Regular moms = new/first-time moms, large family moms, general lifestyle moms only.
- **Beta Testers tab** — original B52 run wrote to "Beta Testers" tab. As of 2026-06-02 those 42 rows were moved to Medical Mom DM Outreach and B52 now routes directly to Medical Mom DM Outreach.
- **MAX_FOLLOWERS cap** — scrape_score_new_hashtags.py now supports upper follower limit. B52 uses 10K–55K. Other batches unaffected (MAX_FOLLOWERS=0 = no cap).
- **B52 Regular Moms Beta** — 22 tags, MIN=10K, MAX=55K, PASS_SCORE=15. Run: `py scripts/scrape_score_new_hashtags.py --batch 52 --posts-per-tag 150 --insert-row <last_validated+1>`
- **Apify credits reset June 1** — confirmed. Full $5 available each calendar month.

### Key Rules (updated 2026-06-02)
- **@daisyweston = gold standard regular mom** — 11,620 followers, UK, Mum of 4, rainbow babies 🌈🌈, twins with additional needs, lifestyle content + viral on hospital post. Boss confirmed this is exactly what to find.
- **Regular mom scorer upgraded** — 3 new signals in score_account(): 🌈 rainbow emoji in bio (+15), "mum/mom of [N]" regex pattern (+10), "justgiving" in bio (+15).
- **B52 routes to Medical Mom DM Outreach** — Beta Testers tab routing removed. All B52/B53+ accounts go directly to Medical Mom DM Outreach, inserted after last validated row.
- **move_beta_to_outreach.py** — utility script to migrate any tab to Medical Mom DM Outreach after last validated row. Already ran: 42 Beta Testers accounts at rows 2079–2120.
- **Apify free plan = 1 page per hashtag** — ~20-27 posts per tag regardless of --posts-per-tag value. Expected yield per B52/B53 run: ~10-30 accounts (tighter with engagement filter).
- **B53 US SAHM Kids-Lifestyle** — 21 tags, 21 accounts at rows 2136–2156. Run WITHOUT engagement filter (filter added after run). Spot-check quality when validating. Re-run with filter if needed: `py scripts/scrape_score_new_hashtags.py --batch 53 --posts-per-tag 150 --insert-row <last_validated+1>`
- **Engagement filter for regular moms (B52/B53)** — pass decision now requires ER ≥ 1.5% OR avg_comments ≥ 8 from latestPosts. Filters ghost-follower accounts. Added after B53 first run — applies to all future runs.
- **32 accounts in COMMENTS tab** — transferred 2026-06-02, scrape + generate pending.

### Key Rules (updated 2026-06-05)
- **Playwright gap reduced** — no fixed gap needed for regular mom batches; use ~3s (not 6s) as confirmed by Cherwin 2026-06-05.
- **Marketing list pipeline started** — boss requirement: 75 medical moms + 30 autism moms, 10K–500K followers (aim 10–100K sweet spot), high engagement, paid affiliates. July 15 launch deadline.
- **Beta tester exclusion list** — 83 handles from Beta Program V2 PDF (June 4, 2026). All excluded from marketing pool. Stored in scripts/fetch_live_followers.py BETA_TESTERS set.
- **Marketing candidate pool** — 2,575 unique handles compiled from ALL tabs (Medical Mom DM Outreach all rows regardless of approval status, Influencer Pipeline, HIGH ENGAGERS, 50 Million List, Email, Influencer Listing Page, Country Check). Saved to `outputs/marketing_candidates.json`.
- **fetch_live_followers.py** — new script. Runs Apify on all 2,575 handles to get live follower counts. Resume-safe (saves after every batch of 50). Results → `outputs/marketing_live_followers.json`. Run: `py scripts/fetch_live_followers.py`. Key rotation: `py scripts/fetch_live_followers.py --apify-token <NEW_KEY>`
- **HIGH ENGAGERS autism moms = tentative top 30 seeds** — 6 confirmed autism moms with 10K+ followers and very high avg comments: @twins_tides_and_autism_vibes (62K, 157 cmts), @twinningwithautism (43K, 91 cmts), @emilywkingphd (20K, 82 cmts), @anu_malhi (95K, 75 cmts), @the.spectrum.and.me (21K, 67 cmts), @aussieautismfamily (45K, 28 cmts).
- **Apify key rotation** — Cherwin has multiple Apify keys. When monthly limit hit, pass new key via --apify-token flag. Script is resume-safe — never loses progress. Always check `outputs/marketing_live_followers.json` for current checkpoint.

### Key Rules (updated 2026-06-05c)
- **Marketing pipeline scripts** — 4 new scripts built:
  - `scripts/build_marketing_shortlist.py` — applies steps 1–4 (filter/categorize/flag intl), writes 436 accounts to "Marketing Shortlist" tab. Re-run anytime to refresh.
  - `scripts/fetch_engagement.py` — Step 5 engagement scrape (436 accounts). Resume-safe → `outputs/marketing_engagement.json`. Run: `py scripts/fetch_engagement.py`. Key swap: `--apify-token <KEY>`
  - `scripts/write_engagement_to_sheet.py` — reads both JSON files, rewrites Marketing Shortlist with all engagement columns. Run after scrape completes or anytime for partial view.
  - `scripts/fetch_englist_followers.py` — scrapes follower counts for 1,140 new handles from Engagement List sheet 4 tabs. Resume-safe → `outputs/englist_followers.json`.
- **Engagement List sheet** — ID: `1uZMIrY316Lyf7MWQCJ25AjZdNnr8TohdLLuCnU-ty6Y`. Key tabs: CAIT APP REVIEWERS (US) (1,723 rows), Medically Complex (303), Autism (61), 50 Million (140), FOR MARKETING PURPOSE (49 manually tracked), CAIT APP REVIEWERS CATEGORIES (238 with diagnosis + email + status).
- **1,140 new handles** extracted from 4 engagement list tabs (CAIT APP REVIEWERS + Medically Complex + Autism + 50 Million), deduped against existing 2,575 pool. Saved to `outputs/engagement_list_handles.json`. Follower scrape running in background.
- **Pinned post logic (PERMANENT, updated 2026-06-26)** — ALWAYS filter `isPinned=True` posts FIRST for BOTH Instagram and TikTok. Then sort remaining by timestamp desc, take latest 12 (Instagram) or 20 (TikTok). Fallback: if ALL posts are pinned, use them all. Root cause confirmed 2026-06-26: Apify returns only ~12 posts total including pinned. Old viral pinned posts (e.g. 2023-2025) land at positions 10-12 after date sort and massively inflate averages (starfish.chronicles: 8,535→1,034; the.birch.family: 2,329→20; mightymadilynn: 1,730→38). The earlier "never filter pinned" rule was wrong for Instagram — retracted. Apply filter in ALL scrape scripts: `non_pinned = [p for p in posts if not p.get('isPinned', False)]; use_posts = non_pinned if non_pinned else posts`. Fixed in `scrape_ls_handles.py` and `scrape_expansion_handles.py` 2026-06-26.
- **TikTok pinned post logic (same as Instagram)** — clockworks/tiktok-scraper returns `isPinned: True/False` per post. Filter pinned FIRST, then sort non-pinned by `createTime` desc, take latest 20. TikTok pinned posts massively inflate metrics (e.g. journeywithjohnson: 2,588→13 avg comments; daniellelizabeth13: 1,224→13). Confirmed 2026-06-19.
- **Marketing Shortlist columns (final)** — Handle | IG Profile Link | Followers | Category | Avg Likes | Avg Comments | Avg Views | ER% | Comment/Like % | Posts Checked | Last Post | Days Inactive | Bio Snippet | US/Intl | Status
- **Engagement scrape complete (2026-06-05c)** — 436/436 accounts done with correct pinned logic. Median avg comments 42.2, median ER% 1.95%, 416/436 active in last 60 days. Checkpoint: `outputs/marketing_engagement.json`.

### Key Rules (updated 2026-06-05b)
- **Marketing pipeline plan (post full scrape)**: Step 1: filter 10K-500K → Step 2: remove orgs/BIZ/patients/nurses → Step 3: categorize Medical Mom / Autism Mom / Unknown → Step 4: flag international → Step 5: second Apify pass on ~200 candidates for post engagement data (avg comments/ER%) → Step 6: rank + build shortlist → Step 7: write to new "Marketing Shortlist" tab in main sheet.
- **Marketing Shortlist tab** — will be created in Sheet ID `1GpeLSbjGTcKe_V1gWYehZcPFU8Vai1q4A9-xLnRGFhA`. Columns: Handle | IG Profile Link | Followers | Category | Avg Comments | ER% | Bio Snippet | US/Intl | Status.
- **Scrape progress (2026-06-05b)** — 1,800/2,575 scraped, 275 accounts at 10K+, scrape still running in background. Will notify when complete or key limit hit.

### Sheet Row Counts (last verified 2026-06-05)
| Tab | Rows |
|-----|------|
| Medical Mom DM Outreach | ~2,300. Last validated row 2080. |
| Beta Testers | 42 rows (reference only) |
| COMMENTS | 0 — fully cleared. All 17 posted 2026-06-05 (rows 2–18, regular moms batch). |
| Email | 159 |
| Influencer Pipeline | 122 |
| Foundations & Organizations | 41 |
| HIGH ENGAGERS | 15 |

### Key Rules (updated 2026-06-09d)
- **Gmail API auth** — token at `outputs/gmail_token.json`, authenticated as cherwin@caitconnect.com. Never needs re-auth unless token expires.
- **Email send script** — `scripts/send_marketing_emails.py`. Always `--dry-run` first. Sends from cherwin@caitconnect.com. CC: mikha@caitconnect.com + partnership@caitconnect.com. Subject: "Partnership Opportunity — CAIT Connect🤍". Marks col R "Sent YYYY-MM-DD". Resume-safe.
- **Medical Mom MIME** — built from scratch (Python MIMEMultipart). Autism Mom uses template raw MIME (draft `r3624019993263736147`, placeholder "Denise"). Medical Mom template draft (`r5641676594799007651`, placeholder "Courtney") NOT used for sending — has corrupt HTML (width:1440px). Signature JPEG extracted from Autism template (CID: `ii_19eab58e32fcd916ff21`).
- **QP encoding rule** — NEVER try to search/replace body text in raw MIME bytes from Gmail API `format='raw'`. Content is QP-encoded (`=3D` for `=`, `=\r\n` soft wraps). Build fresh MIME instead.
- **585-pool preserved** — `outputs/marketing_pool_585.json` has all 585 accounts with 10K+ followers from original 2,575 scrape. Includes accounts deleted from Marketing Shortlist as Unknown — some may be medical moms. Review in future session.

### Key Rules (updated 2026-06-10)
- **Marketing Shortlist name column = "Name" (col F)** — NOT "Full Name". Script uses `ci("Name")` to look up display name for email greeting.
- **MANUAL_NAMES override dict** — 80+ accounts have hardcoded first names in send_marketing_emails.py. Child-named accounts use `is_child=True` flag → email says "Hi Jamison's Mom," etc. Never remove entries from this dict without verifying the account is really a parent.
- **Bad email detection** — `is_bad_email()` skips: PNG/webp/jpg filenames, `@2x.`/`@1x.` assets, `%`-prefixed URLs, GoFundMe privacy-requests, brand support emails (Eufy, ShopMy, tubbytodd), wrong org/foundation emails. SKIP_EMAILS set in script. ~70 entries total.
- **Email source quality rule** — Good emails come from bio/linktree (person's own contact). Bad emails are scraped from linked sponsor pages, charity sites, or embedded assets. When in doubt, check the account's bio or linktree directly.
- **"Hi there," is acceptable** — ~14 accounts have no extractable name. Email says "Hi there," which is still personal enough to send.

### Key Rules (updated 2026-06-10b)
- **3 Gmail templates (PERMANENT)** — Medical Mom (`r5641676594799007651`, placeholder "Courtney"), Autism (`r3624019993263736147`, placeholder "Denise"), Down Syndrome (`r3389878446385466373`, placeholder "Name"). Used as **plain-text body source only** — never use their raw HTML (corrupt wrappers). Body text is extracted and rebuilt into the correct HTML format.
- **send_marketing_emails.py simplified** — no more scratch-building. All 3 templates use `get_raw_template()` → `replace_bytes()` → swap headers. "Other" and "Unknown" categories route to medical template.
- **Gmail OAuth must include gmail.compose scope** — token at `outputs/gmail_token.json`. If drafts.create fails with 403, re-run `py scripts/setup_gmail_auth.py` to re-authenticate.
- **Marketing Shortlist layout** — rows 2–121 = 111 valid personal emails (sorted to top). Rows 122–363 = filtered/no-email accounts. Col T = "Draft Status" (Drafted YYYY-MM-DD or blank).
- **scripts/create_drafts.py** — creates Gmail drafts for all valid accounts using `build_email_raw()`. Skips already-drafted and recently-sent rows, marks col T. Resume-safe. Run: `py scripts/create_drafts.py`
- **111 drafts created 2026-06-10c** — all in correct format. 9 bad emails permanently blocked in SKIP_EMAILS.

### Key Rules (updated 2026-06-10c) ← PERMANENT EMAIL FORMAT — NEVER CHANGE
- **Email HTML format (ALL categories)** — always use `build_email_raw(tmpl_key, fname)` in `create_drafts.py`. NEVER use raw Gmail draft HTML. The correct format confirmed from Cherwin's sent emails:
  ```
  MIME: multipart/related > multipart/alternative (text/plain QP + text/html) + image/jpeg base64
  HTML wrapper: <div style="font-size:inherit" dir="auto">
  Paragraph separator: <br style="font-size:inherit"><br style="font-size:inherit">
  Bullet separator: <br style="font-size:inherit"> (single)
  Signature: <div style="font-size:inherit" dir="auto"><div><img src="cid:sig_cait_01" style="max-width: 100%;"></div></div>
  ```
- **Plain text uses CRLF** — Gmail draft plain text has `\r\n` line endings. Always normalize to `\n` before processing (split on `\n\n` not `\r\n\r\n`). Failure = all paragraphs collapse into one block.
- **Soft-wrapped lines must be joined** — continuation lines in plain text are joined with a space to form single-line paragraphs in HTML. Only bullets (`•`) stay on separate lines.
- **Category → template routing (PERMANENT)**: Medical Mom/T1D/Regular Mom/Other/Unknown → `medical`; Autism Mom/ADHD Mom → `autism`; Down Syndrome → `downsyndrome`.

### Key Rules (updated 2026-06-16)
- **Launch Shortlist pipeline started** — boss wants ONE consolidated "Launch Shortlist": 50 high-engagement Medical Moms, 25 high-engagement T1D kids/parents, 25 high-engagement T1D adults, 20 top influencers, plus a "Full List" tab (every handle scraped, pass/fail + reason) and a separate "Beta Testers" tab. Plan: `C:\Users\lamch\.claude\plans\vast-bubbling-hanrahan.md`.
- **Step 1 complete** — `scripts/build_master_handle_list.py` pulls handles from 25 tabs across 6 Google Sheets (MAIN, ENGAGEMENT_LIST, LAUNCH_LIST, MACRO, PARENT_INFLUENCERS, PERSONAL), handles headerless/dual-table tabs. Merged in 4 historical "deleted handle" JSON pools (marketing_pool_585, marketing_candidates, engagement_list_handles, englist_followers) plus the 82-handle Beta Program V2 PDF (tagged `is_beta_tester`, matches `scripts/check_beta_overlap.py`). **Result: 4,103 unique handles** in `outputs/master_handles.json` — breakdown: 82 beta testers, 67 orgs, 605 already-live (≤2 weeks old), 406 influencer-pool candidates, 70 recovered-from-deleted.
- **Blocker resolved 2026-06-16b** — before spending any Apify credits, scope was trimmed: skip 605 already-live handles (Marketing Shortlist/LAUNCH_LIST Cherwin tab), skip 67 orgs (excluded from individual scoring), skip 82 beta testers (own tab). **Net Step 2 target: 3,353 handles**, down from 4,103.
- **Step 2 complete (2026-06-16)** — `scripts/scrape_master_handles_live.py`: `apify/instagram-scraper` details mode, no proxy field, batches of 50, checkpoints to `outputs/master_handles_live.json` after every batch, resume-safe across Apify key swaps (`--apify-token <NEW_KEY>`). Captures followers/bio/full name/business/verified/private + email (`businessEmail`) + external_url, plus avg likes/comments/ER% from latest 12 posts sorted by date (no pinned-first). Took 3 Apify keys across 3 runs (800 → 2,700 → 3,353) — **all 3,353/3,353 handles scraped, 0 errors.** Note: `businessEmail` came back empty for 100% of records — Instagram doesn't expose it via this endpoint.
- **Step 3 complete (2026-06-16)** — `scripts/categorize_launch_shortlist.py`: merges master + live data, re-derives category from live bio only (org-bio-signal override beats any old "is_org: false" label), splits T1D into Kids/Parent vs Adult (adults-only-for-T1D rule — the one exception where adult self-posts qualify), rejects Autism/Medical Mom adult self-posts. Cross-checks derived category against the old `category_hints` (`category_matches_hint` field — 1,357/4,021 disagreed, live always wins but flagged for spot-check). Added a free bio-regex email fallback (recovers 307 emails at zero Apify cost) since the API field was empty. Output: `outputs/launch_shortlist_scored.json` — **1,090/4,021 met criteria**: 453 Medical Mom, 255 Autism Mom, 214 T1D Adult, 168 T1D Kids/Parent.
- **Step 4 complete (2026-06-16d)** — output structure changed from the original 3-tab plan per Cherwin: instead of one "Full List" tab, the full scored pool (4,021 records) is split into **"10K+ Master List"** (1,230 rows) and **"Under 10K Master List"** (2,791 rows), both showing every category pass/fail + reason, sorted by Avg Comments desc. `scripts/write_launch_shortlist_tabs.py` does the split + also builds **"Launch Shortlist"** (the boss's 4 buckets, 120 rows total, fully filled 50/25/25/20, zero overlap) + **"Beta Testers"** (82 rows). All 4 tabs written to the main sheet.
- **DS/T1D category priority bug fixed (2026-06-16d)** — `categorize_launch_shortlist.py` was silently folding Down Syndrome bios into "Medical Mom" via `GENERAL_DIAGNOSIS_KEYWORDS`. Per the existing permanent rule (category priority: **Down Syndrome > T1D > Medical Mom > Autism Mom**), DS now has its own `DOWN_SYNDROME_KEYWORDS` list and is checked first in the if/elif chain. Re-run result: 1,096/4,021 passed — 443 Medical Mom, 214 T1D Adult, 202 Autism Mom, 168 T1D Kids/Parent, 69 Down Syndrome Mom (DS not currently eligible for any of the boss's 4 buckets — open question).
- **Open items as of 2026-06-16d** — (1) decide if Down Syndrome should get bucket eligibility; (2) add a Follower Tier (10K+/Under 10K) column directly to the Launch Shortlist tab; (3) Cherwin flagged the master tabs may have meaningful inaccuracies — spot-check pending, not yet done.
- **Step 4e fixes (2026-06-16e)** — spot-check found real categorizer bugs (bare "foundation" false-positive, missing HIE/sahm/medicalmom-identity keywords). Fixed, re-ran: 1,189/4,021 pass. Follower Tier column added to Launch Shortlist tab. All 4 tabs rewritten.
- **Data Correction & Standardization pass (2026-06-16f, IN PROGRESS)** — Cherwin's follow-up requirements: (1) category must trace back to the **original source tab**, not be re-derived from bio — worked example: "Dr. Beach Gem" should show "Doctor" per source data; (2) category must be identical across every tab the handle appears in; (3) engagement metrics must exclude pinned posts (confirmed real bug — pinned posts were inflating avg comments/ER%, fixed to match Marketing Shortlist's "sort all by date, take latest 12" method); (4) "10k Above" (renamed from "10K+ Master List") = complete no-exclusions master dataset; Marketing Shortlist must be a strict filtered subset of it, never independent; (5) no creators dropped for not fitting a bucket — Doctors/Nurses/Therapists/Orgs/Researchers stay in the master pool; (6) preserve canonical entries on duplicates, never silently delete. `scripts/categorize_launch_shortlist.py` rewritten: 3-tier resolution — source-sheet category (via `outputs/source_categories.json`, built by `fetch_source_categories.py`, 17-tab `SOURCE_CATEGORY_PRIORITY`) wins outright > bio-inference fallback (only when no source signal exists) > "stay as is" (preserve prior run's value when neither yields a signal — explicit Cherwin instruction, never invent a category). New `list_bucket` field separates the literal `category` string (now any exact value, e.g. "Doctor") from eligibility for the boss's 4 Launch Shortlist buckets. Orgs no longer auto-fail — `met_criteria="Yes"`, `list_bucket=None` (no-exclusions policy). `scripts/write_launch_shortlist_tabs.py` rewritten to bucket by `list_bucket`, added a `"Category Source"` column, added write-back of corrected categories into 5 original tabs (Medical Mom DM Outreach, Influencer Pipeline, 50 Million List, CAIT Community, Marketing Shortlist) via `sync_category_writeback()`, and a sanity check confirming every Marketing Shortlist handle is present in 10k Above. **Blocked on a background Apify rescrape of all 3,353 handles** (pinned-post-fix, task `b8dordc0o` — `outputs/master_handles_live.json` reset and being rebuilt fresh, old version backed up to `outputs/master_handles_live_BACKUP_before_pinned_fix.json`). Both rewritten scripts have NOT been re-run yet — waiting on the rescrape to finish.

### Key Rules (updated 2026-06-16g)
- **`is_live` cached data silently goes stale — found via milas_crew** — `get_record()` in `categorize_launch_shortlist.py` always prefers `is_live`-flagged cached data over a fresh scrape, and `scrape_master_handles_live.py` explicitly skips any `is_live: True` handle. The 605 handles merged in from the original Marketing Shortlist pass (~2026-06-05) had NEVER been refreshed by any subsequent rescrape. `milas_crew` turned out to be genuinely dead (Apify `not_found`, confirmed via 2 independent direct lookups) despite its cached snapshot showing 15K followers active. Fixed: cleared `is_live` on all 605 in `outputs/master_handles.json`.
- **`is_live` is now `False` everywhere in master_handles.json — this is expected, not a bug.** Don't re-set it. The flag's job (protecting already-fresh data from re-scraping) is done; going forward every handle flows through the normal rescrape/cache path.
- **"Inaccurate" engagement numbers are usually staleness, not a calculation bug** — spot-checked 6 `is_live` handles against fresh Apify pulls: 5/6 were within 0-18% of cached, fully explained by normal post turnover over an 11-day-old cache. The pinned-post-exclusion + sort-by-date-take-12 methodology is correct. Don't assume a metric complaint means the formula is broken — check staleness first.
- **MANUAL_OVERRIDES pattern** — `categorize_launch_shortlist.py` has a `MANUAL_OVERRIDES` dict (handle → forced category/met_criteria/list_bucket/reason) applied after the main scoring loop, survives every re-run. Use this for one-off spot-check corrections (dead accounts, deceased child accounts, misclassified adults, wrong career labels) instead of hand-editing the scored JSON — the JSON gets fully regenerated every run.
- **Medical Mom bucket = kids only** — `list_bucket_for()` excludes any category containing "adult" (e.g. "Cancer Adult", "Type 1 Diabetes Adult") from the Medical Mom bucket. T1D Adult is the one exception with its own dedicated bucket.

### Key Rules (updated 2026-06-17)
- **Jessica's 17 accounts + Cherwin's 5 accounts (22 total, 2026-06-17/18)**
  - Jessica's 17 → in Launch Shortlist (main bucket OR overflow). Cherwin's 5 (overatkates, houseofcowles, breanna_hiland, laurenashby22, jesses_journey_2026) → master lists only, NOT Launch Shortlist.
  - All 22 confirmed in master lists: 19 in 10K Above, 3 in Under 10K (houseofcowles, breanna_hiland, jesses_journey_2026).
- **Launch Shortlist tab structure (FINAL as of 2026-06-18)** — 128 rows. Sections in order: Medical Mom #1–50 → Medical Mom Overflow #51–55 (irelandbiltoft, remi.raerogers, accessible.adventures, hannahkatelyn, heyrachelhughes) → Down Syndrome (willsjourney21 #1, erinadvocates #2) → T1D Kids/Parent #1–24 → T1D Adult #1–25 → Top Influencer #1–20 → Top Influencer Overflow #21–23 (ryleearnold1, jeraldinejeronimojorjette, galthebabydoc).
- **Launch Shortlist rebuild rules** — Medical Mom overflow rows go immediately after rank 50, renumbered 51+. Down Syndrome section goes right after Medical Mom (its own section, ranked 1–N). Top Influencer overflow goes right after rank 20, renumbered 21+. Cherwin-added accounts never go on Launch Shortlist.
- **MANUAL_OVERRIDES added (2026-06-17)**: `houseofcowles` (dead/not_found), `hannahkatelyn` (Medical Mom — RCDP, mom of Jude), `jesses_journey_2026` (Medical Mom — child Jesse has T-Cell ALL leukemia, parent-run), `laurenashby22` (Regular Mom — lifestyle mom, email in bio: laurenashby05@gmail.com).
- **Email cross-reference script: `scripts/pull_emails_from_tabs.py`** — reads 4 tabs (CAIT APP REVIEWERS CATEGORIES, MAIN/Email, Marketing Shortlist, CAIT Community), builds handle→email map, fills empty email slots in `outputs/launch_shortlist_scored.json`. Email column in those tabs = "Emails" (plural). Run before `write_launch_shortlist_tabs.py` whenever email data changes. 393 pairs collected, 214 slots filled as of 2026-06-17.
- **Gmail MCP = wrong account** — claude.ai Gmail MCP is authenticated to theangelamatias@gmail.com (Claude account), NOT cherwin@caitconnect.com. Always use `outputs/gmail_token.json` + Python Gmail API for outreach work.
- **Influencer reply drafts — 16 drafts ready (2026-06-18)** — `scripts/draft_influencer_replies.py` covers all real replies to "Partnership Opportunity" subject (17 total, 1 already sent by Cherwin = 16 remaining). All drafts use neutral language: "We'll review everything internally and update you from there." No "next steps", no "circle back soon". Carli Solomon (carli@thearteagency.com) also asks politely for Ashley's media kit (only one who didn't send anything).
- **19 total reply threads found** — search `subject:"Partnership Opportunity"` returns 99 threads, 19 had replies, 2 were bounces = 17 real people. Always run this search to catch replies with changed subject lines.
- **Reply tone rule (PERMANENT)** — never write anything that implies the influencer will definitely get a partnership. Standard close: "We'll review everything internally and update you from there." For scope/budget questions: explain early planning stage + "primarily gathering media kits and standard rates." For missing media kit: "If you don't mind, would you be able to share your media kit or standard rates? We'd love to have them on file."
- **master_handles.json now has 4,111 handles**.

### Key Rules (updated 2026-06-18b)
- **CP = valid Medical Mom diagnosis** — Cerebral Palsy is NOT excluded from the Launch Shortlist. The excluded categories rule (Down Syndrome, CP, Hearing Loss, Vision/CVI) applies to hashtag scraping only, not to the Launch Shortlist or Medical Mom bucket.
- **OVERFLOW_HANDLES = Jessica's 17 only (PERMANENT)** — Cherwin's 5 accounts (overatkates, houseofcowles, breanna_hiland, laurenashby22, jesses_journey_2026) are commented out of OVERFLOW_HANDLES. They appear on the Launch Shortlist ONLY if they earn a rank organically. Jessica's 17 are guaranteed regardless of rank.
- **Overflow section order** — Medical Mom top 50 → Medical Mom Overflow → Down Syndrome → T1D Kids → T1D Adult → Top Influencer → Top Influencer Overflow. Overflow is always immediately below its own bucket's top-N.
- **Overflow ranks = per-category sequential** — #51, #52, #53… not global pool positions. `_overflow_for_pool()` increments rank_counter only on matched OVERFLOW_HANDLES accounts.
- **MANUAL_OVERRIDES (as of 2026-06-18b)** — cumulative list of excluded/reclassified accounts: bigtimeadulting (skip/1.9M), whataboutaub (skip/1.18M), sydneyraebass (skip/1.07M), mimiandleilani (medical adult), eviemeg (medical adult), ridhayfightssma (non-US), adventures.of.mommy (do not partner), cassscroggins (regular mom), publicponder (autism mom), the_overstimulated_pancreas (T1D Kids/Parent), parkersjourney08 (beta tester), jocelynpacitto (regular mom), medicalmumma_ (excluded).
- **ariellabarbozag excluded** — Spanish-language account (non-English). CAIT is English-only. Removed from Medical Mom.
- **Email already sent** — jess.hentges contacted at jesshentges@gmail.com (not jess@pearpop.com). sarahrosesummers already contacted. 10 Medical Mom Launch Shortlist accounts with emails contacted June 9–10.

### Key Rules (updated 2026-06-18c)
- **MANUAL_OVERRIDES additions** — roccostronginc (cancer free — excluded), michellevaughanklett (Regular Mom), emileemorannn (Down Syndrome), ariellabarbozag (non-English — excluded), autismwithjayce (Autism Mom).
- **DS_OVERFLOW_HANDLES = {"willsjourney21", "erinadvocates", "emileemorannn"}** — 3 accounts in Down Syndrome section. Update this set in `write_launch_shortlist_tabs.py` whenever DS accounts are added.
- **Handle spelling matters** — always verify exact handle in scored JSON before adding to MANUAL_OVERRIDES. emileemorannn (3 n's) ≠ emileemorannnn (4 n's).
- **Apify posts_checked variability** — Apify returns 9–12 posts for `latestPosts` (variable, not a bug). Rankings based on 9-post averages are valid. Re-scrape only when metrics look implausible (like ariellabarbozag's 70 cmts when fresh scrape gave 133).
- **Status column = col N of Launch Shortlist** — "Emailed Jun 9/10", "Not Sent", "Draft Created", blank for no email. Must be maintained manually or updated alongside write_launch_shortlist_tabs.py runs.
- **auntihood was NOT emailed** — auntihood@gmail.com was NOT in Gmail sent list. Was incorrectly cached as sent. Draft created 2026-06-18c.
- **5 new Medical Mom drafts created (2026-06-18c)** — auntihood, cassadicurrier, thekristinexy, miranda.aldridge, heyrachelhughes. shannonwillardson and jess.hentges skipped per Cherwin.
- **rachelhughes@thestation.io** — flagged as possibly a management agency email. Cherwin to confirm before sending.
- **thefaruqui5 confirmed** — Medical Mom, 41.5K, 38.4 avg cmts, in 10k Above master list, below Medical Mom top 50 cutoff (~62 avg cmts). Not added to overflow.

### Launch Shortlist state (2026-06-18c)
- **130 rows**: Medical Mom 50 + Overflow 4 + DS 3 + T1D Kids 25 + T1D Adult 25 + Top Influencer 20 + Overflow 3
- All 17 of Jessica's accounts confirmed present
- Medical Mom email status: 10 sent, 5 draft-created, 1 skipped (shannonwillardson), 1 reached via alt email (jess.hentges)

### Key Rules (updated 2026-06-18e)
- **scrape_linktree_emails.py filter upgrades (2026-06-18e)** — patterns added after live-run review:
  - `sentry.io` / `ingest.us.sentry.io` / `wixpress.com` → BAD_DOMAINS (Sentry SDK + Wix tracking addresses embedded in page HTML)
  - `stanwith.me`, `bio.sites`, `microsoft.com`, `xxx.xxx` → BAD_DOMAINS
  - `customerservice`, `customercare`, `social`, `partnerships`, `appservices` → BAD_LOCAL_PREFIXES (brand team, not creator contact)
  - Unicode-escape artifact block: `re.match(r'^u00[0-9a-f]{2}$', local)` catches `u003e@` (`>`), `u002f@` (`/`)
  - Sentry UUID block: `re.match(r'^[0-9a-f]{32}$', local)` catches 32-char hex local-parts
  - **`sgac@thestyledgetawayco.com` = shared LTK agency email** — appears for 4+ handles (@taylorfrankiepaul, @darylanndenner, @apriljoy_ful, @rachparcell, @carcabaroad). One agency managing multiple unrelated creators. Not a direct personal contact. Kept in JSON for now.
- **Scrape ran with old filters** — btlpoq32d launched before filter fixes were applied. After completion, run a cleanup pass to remove bad emails written by the old filter before running write_launch_shortlist_tabs.py. Bad handles to clear: autumncalabrese (sentry UUID), destini.ann/abanaturally/thesensoryproject208/healingwithhope_sierra (u003e artifacts), laylaleannetaylor (u002f artifact), maycineeley (customerservice prefix), followyourchild/lesley.osei/annaowen/sophiasjourneyx (sentry UUIDs), thegenesisfamily (appservices@microsoft.com), momcomindia (customercare prefix), varsha_balani_ (customersupport@icicilombard), everyday_ot_ireland (xxx@xxx.xxx).

### Key Rules (updated 2026-06-18d)
- **TikTok giveaway hashtag niche doesn't exist** — compound tags (#medicalmomgiveaway, #heartmomgiveaway, etc.) return 0 posts on TikTok. Medical moms who run giveaways use `#giveaway` + their normal diagnosis hashtags in post captions. `scripts/scrape_tiktok_giveaway_moms.py` → `outputs/tiktok_giveaway_moms.csv` (14 accounts).
- **Email sheet sources fully exhausted** — all tabs across 2 sheets scanned. Tabs with NO email column: 50 Million List, Influencer Pipeline, Medically Complex, Autism, FOR MARKETING PURPOSE, ENGAGEMENT_LIST 50 Million. CAIT APP REVIEWERS (US) added as Priority 6 source but only yielded +1 (already covered by CATEGORIES). Total: 394 sheet pairs + ~63 bio regex = 457 emails in scored JSON.
- **External URL email scraper built** — `scripts/scrape_linktree_emails.py`. Fetches 656 handles (10k+, no email, has external_url). Bad-email filter blocks: image filename artifacts (@2x.png, .js version strings), GoFundMe/gofund.me, all charity/donation domains, Amazon/YouTube/LTK/Beacons, example.com, noreply/support/donate prefixes, info@ on non-agency domains. Keeps: personal gmail/yahoo/outlook/icloud, agency emails, personal website contact. Run: `python scripts/scrape_linktree_emails.py` (re-runnable, saves to scored JSON). After completion, re-run `write_launch_shortlist_tabs.py` to propagate new emails to sheet tabs.
- **pull_emails_from_tabs.py updated** — CAIT APP REVIEWERS (US) added as Priority 6. FOR MARKETING PURPOSE corrected to use "Emails" column name (still skipped — column not found, different structure).

### Key Rules (updated 2026-06-19)
- **Launch Shortlist full rescrape done** — all 133 handles re-scraped with pinned-post filtering (2026-06-19). Results in `outputs/ls_rescrape.json`. Sheet cols D/I/J/K updated for all 133 rows.
- **Pinned post inflation was real and large** — thefitnesswaytocope dropped 837→214 (3 pinned), wonderfullifewithbedford 806→296 (4 pinned), auntihood 451→192 (3 pinned). Rankings have shifted significantly.
- **ameliasarmy confirmed weak** — real avg_comments = 15.7 (not 62.8). Old 62.8 was a stale artifact. Ranks #303 in Medical Mom pool. Should be removed from top 50 — pending Cherwin confirmation.
- **lobro15 one-viral-post warning** — 62.8 avg_comments technically correct but driven by a single May 7 post (469 cmts, 14K likes). Under 10K followers (9,699). Inactive since May 24. Not representative of typical performance.
- **avg_comments can drop dramatically even with 0 pinned** — libraa_snowszzn (154→62), miranda.aldridge (103→49), jhoannaxo (101→54) dropped with zero pinned posts. Cause: old cache had different/older posts; new scrape got different latest 12. Always re-scrape before ranking decisions.
- **Influencer reply drafts — 4 new (2026-06-19)** — auntihood (asked for deliverables, we asked for media kit), kristine/Addison Dolan (sent media kit, we acknowledged), heyrachelhughes/Maria Paula (sent rates, we acknowledged + congrats on baby), zaccheo (sent rates, short reply). All in Cherwin's Drafts folder.

### Key Rules (updated 2026-06-19b)
- **Launch Shortlist rebuilt with corrected metrics (2026-06-19b)** — ls_rescrape.json metrics merged into launch_shortlist_scored.json. ameliasarmy fell off naturally (15.7 avg_cmts, not in top 50). lobro15 stays at #44 (62.8 confirmed real). 132 data rows total.
- **parenthood.adventures added (Jessica request)** — Kristin Addis, luxury family travel, 586K followers, 3,256 avg_cmts, 2.03% ER. Category: Macro Mom. Top Influencer #1.
- **melissamaecarlton added (Jessica request)** — MELISSA MAE, 151K, 276.8 avg_cmts, 5.4% ER. SUDC & PPA2 awareness mom (lost Molly, still active with Abi). Medical Mom #17.
- **toxtwins added (Jessica request)** — THE TOX TWINS, twin PA moms, 206K, 590.1 avg_cmts, 5.16% ER. Email: toxtwins@jakerosen.com. Macro Mom → Top Influencer #13.
- **Jessica total: 20 accounts** — 17 original (2026-06-17) + melissamaecarlton + toxtwins + parenthood.adventures (all 2026-06-19b).
- **samninawolf scored JSON fix** — categorize script had met_criteria="No" for samninawolf in scored JSON (bio-inference override). Fixed directly in scored JSON: Autism Mom, met_criteria=Yes. DS #1 confirmed showing correctly now.
- **MANUAL_OVERRIDES pattern (IMPORTANT)** — MANUAL_OVERRIDES in categorize_launch_shortlist.py do NOT auto-apply to scored JSON unless categorize script is re-run. If categorize isn't being re-run, patch scored JSON directly with the same values.
- **Launch Shortlist structure (132 rows)** — Med Mom #1–50 → Med Overflow #51–55 (jhoannaxo, remi.raerogers, accessible.adventures, hannahkatelyn, heyrachelhughes) → DS #1–4 (samninawolf/willsjourney21/erinadvocates/emileemorannn) → T1D Kids #1–25 → T1D Adult #1–25 → Top Influencer #1–20 → Top Infl Overflow #21–23 (ryleearnold1, jeraldinejeronimojorjette, galthebabydoc).

### Key Rules (updated 2026-06-19)
- **Chronically Ill Adults = new Launch Shortlist bucket (top 25)** — added 2026-06-19. Medical Adults are no longer excluded — they now map to this bucket. Route: any category with "adult" or "self-post" in the name AND medical signal (medical, chronically ill, cancer, rare disease, epilepsy, cystic fibrosis, sickle cell, autoimmune, hie) → list_bucket = "Chronically Ill Adults". T1D Adults still go to T1D Adult bucket (checked first).
- **Launch Shortlist now has 5 buckets** — Medical Mom (50) → T1D Kids/Parent (25) → T1D Adult (25) → Chronically Ill Adults (25) → Top Influencers (20). Section order in sheet: Med Mom → Med Overflow → DS → T1D Kids → T1D Adult → Chronically Ill Adults → Top Influencer → Top Influencer Overflow.
- **65 accounts in Chronically Ill Adults pool (2026-06-19)** — 59 from source sheets (Marketing Shortlist, Gen, Cherwin, 50 Million List) with "Chronically ill Adult" / "Cancer Adult" categories had list_bucket=None in scored JSON (old code blocked all adults). Patched all 59. Top 25 fill bucket. Sources: LAUNCH_LIST/Gen has full CI Adults list compiled by Jessica.
- **faithhinitt confirmed** — Faith Hinitt, 43,810 followers, Acute Myeloid Leukemia. 279.4 avg_cmts, 6.55% ER. Email: hinittfaith@gmail.com. Scraped fresh 2026-06-19 with pinned post filter. CI Adults bucket position: pending final ranking (drops to ~#8-10 range based on metrics).
- **⚠️ CI Adults pool flags**: @bridget (1.83M), @embracingecho (1.01M), @thetiabeestokes (1.09M), @eviemeg (935K), @katygharrell (586K) have very large follower counts — same "too large" concern as bigtimeadulting/whataboutaub. Cherwin to review when validating the CI Adults bucket.
- **Jessica total: 21 accounts** — 17 original (2026-06-17) + melissamaecarlton + toxtwins + parenthood.adventures + faithhinitt.
- **New handle entry rule** — when any new handle enters Launch Shortlist, scrape it fresh via Apify (pinned posts excluded) before finalizing metrics. No stale data allowed in ranked buckets.
- **Jessica total: 21 accounts** — 17 original (2026-06-17) + melissamaecarlton + toxtwins + parenthood.adventures + faithhintt.

### Key Rules (updated 2026-06-22)
- **shannonwillardson removed from Launch Shortlist** — Medical Mom bucket, list_bucket=None, met_criteria=No. New Medical Mom #50: @kenzoskronicles (13,728 followers, 60.1 avg cmts). scored.json patched directly.
- **Launch Shortlist now 157 rows (5 buckets + overflow)** — caps: Medical Mom 50 + overflow 5 → DS 4 → T1D Kids 25 → T1D Adult 25 → CI Adults 25 → Top Influencer 20 + overflow 3. Section order permanent as of 2026-06-22.
- **OVERFLOW_HANDLES = Jessica's 21 accounts (PERMANENT)** — remi.raerogers, ashleymarryriv, the.pa.tient, erinadvocates, irelandbiltoft, galthebabydoc, heyrachelhughes, ryleearnold1, thesponslercrew, willsjourney21, jeraldinejeronimojorjette, starfish.chronicles, accessible.adventures, hannahkatelyn, thefitnesswaytocope, jhoannaxo, libraa_snowszzn, melissamaecarlton, toxtwins, parenthood.adventures, faithhinitt. These 21 are GUARANTEED to appear on the Launch Shortlist as overflow even if they don't rank in the top N. Cherwin's 5 accounts are NOT in OVERFLOW_HANDLES.
- **Influencer Replies tab now has 26 rows** — 5 new entries added 2026-06-22: @cassadicurrier, @heyrachelhughes, @thet1dmama, @vibezwith.ari, @ourlittlemms. 2 new rows added 2026-06-27: @amazingabigailgrace (row 25), @auntihood (row 26 — was missing).
- **TikTok loop giveaway pages — ecosystem is small** — scrape_tiktok_loop_giveaway_pages.py ran (15 tags × 100 posts). Only 8 dedicated pages found. Best leads: @rosalillyfamily (21.6K, collab email rosalillythrifts@gmail.com), @candycampero (7K), @savvygiveaways (6.4K TikTok). TikTok has far fewer dedicated loop giveaway pages than IG.
- **Apify billing cycle (current account bellalam2026@gmail.com)** — reset June 21, cycle ends July 20. Full $5 available.
- **9 influencer threads awaiting Cherwin reply** — cassadicurrier, heyrachelhughes, thet1dmama, alonglevert (vibezwith.ari), kelseyboone, thewoodcrew8, moonlitmaddyx, jesshentges, ourlittlemms. Draft or reply from cherwin@caitconnect.com.

### Key Rules (updated 2026-06-24)
- **Launch Shortlist caps expanded** — Medical Mom 50→200, T1D Kids 25→50, T1D Adult 25→50. Sheet now 354 rows. `write_launch_shortlist_tabs.py` overflow cutoffs updated to match.
- **T1D Pediatric/Juvenile bug fixed** — categories "T1D / Pediatric Diabetes" and "Type 1 Diabetes / Juvenile" now correctly force T1D Kids/Parent bucket regardless of bio. 107 accounts moved from T1D Adult to T1D Kids/Parent. Fixed in `list_bucket_for()` in `categorize_launch_shortlist.py`.
- **OVERFLOW_HANDLES = 23 accounts** — added hannahvsetzer (2026-06-24) and _mel.rw (2026-06-24). Full list: remi.raerogers, ashleymarryriv, the.pa.tient, erinadvocates, irelandbiltoft, galthebabydoc, heyrachelhughes, ryleearnold1, thesponslercrew, willsjourney21, jeraldinejeronimojorjette, starfish.chronicles, accessible.adventures, hannahkatelyn, thefitnesswaytocope, jhoannaxo, libraa_snowszzn, melissamaecarlton, toxtwins, parenthood.adventures, faithhinitt, hannahvsetzer, _mel.rw.
- **_mel.rw = correct handle (underscore)** — CI Adults rank 3, 82K followers, 680 avg cmts. Jessica's "mel.rw" request refers to this account.
- **DS section = Jessica's 2 only** — DS_HANDLES in write_launch_shortlist_tabs.py is {"willsjourney21", "erinadvocates"}. samninawolf and emileemorannn removed. Do NOT add DS accounts unless Jessica explicitly requests.
- **Early Access (US) handle column has trailing slashes** — e.g. `gretchen.woodson/`. Must strip trailing slash when extracting handles. Use URL column as first source, fallback to handle column with rstrip('/').
- **Apify credits exhausted 2026-06-24** — bellalam2026@gmail.com hit monthly limit during Launch Shortlist rescrape. Resets July 20. 49 handles still need scraping: 8 stale LS handles + florence_and_the_heart_machine. + 40 new Early Access/FOR MARKETING PURPOSE accounts.
- **wonderfullifewithbedford metric still inflated** — shows 806 avg_cmts (pre-pinned-fix June-16 cache). Real value is ~296 (4 pinned posts). Will correct when rescraping July 20+.
- **Gmail: 11 drafts created 2026-06-24** — for: Cassadi, Maria Paula/The Station, thet1dmama, Ari/vibezwith.ari, Kelsey Boone, Em/amazingabigailgrace, The Wood Crew, Maddy Rose/moonlitmaddyx, Jessica Rawls/PearPop (Jess Hentges' manager), Blaine/The Bookd/ourlittlemms, Britt Hendrix/bientheagency/sarahrosesummers.
- **Jessica Rawls = jessica@pearpop.com = Jess Hentges' manager at PearPop** — distinct from jess.hentges@gmail.com (contacted separately).
- **Blaine/The Bookd rates for ourlittlemms** — YouTube long form $7K, integration $3K, shorts $2K; TikTok $4K; IG Reel $4K; Stories $1.5K.
- **Master handles total: 4,157** — added 40 new handles this session (36 Early Access US valid handles + 4 FOR MARKETING PURPOSE T1D Adults). 7 garbage URL-fragment handles cleaned. florence_and_the_heart_machine. (CHD/HLHS) added from CAIT APP REVIEWERS CATEGORIES.

### Key Rules (updated 2026-06-24b)
- **No follower floor on Launch Shortlist (PERMANENT)** — 118/354 accounts are under 10K and that is correct. Launch Shortlist ranks purely by highest avg comments within each bucket. A 740-follower account with 80 avg cmts beats a 50K account with 5 avg cmts.
- **Apify token status (2026-06-24b)** — linkaichen45 (`PH1W0I4K`) exhausted after 350 LS handles. diaryrecruitment10 (`ov02ZAAF`) is the active working token. bellalam2026, danicamatias2026, bautistakare29, octicebear all exhausted.
- **`scripts/scrape_ls_handles.py`** — new script. Reads `outputs/ls_handles_to_scrape.json`, scrapes all handles via Apify, saves to `outputs/ls_rescrape_v3.json`. Resume-safe. Run: `python scripts/scrape_ls_handles.py`. Key swap: `--apify-token <KEY>`.
- **Launch Shortlist col B has quote-prefixed values** — cells stored as `'wonderfullifewithbedford` (leading apostrophe). Always `row[1].lstrip("'")` when reading col B for handle matching. Col layout: A=Rank, B=Handle, C=IG Profile Link, D=Followers, E=Category.
- **Fresh LS metrics (2026-06-24b)** — pinned-post fix fully confirmed: wonderfullifewithbedford 805→3,173 avg cmts, starfish.chronicles 8,535 (rank #1 Med Mom), _mel.rw 1,944 (CI Adults), kenzoskronicles 972 (only 13.7K followers), faithhinitt 689 (was 279).
- **Always test tokens with real actor run** — `effectivePlatformFeatures.ACTORS.isEnabled` can say False even for valid tokens. Use `apify~hello-world` test run to confirm a token actually works before trusting it.

### Key Rules (updated 2026-06-25)
- **Launch Shortlist fully verified — 0 stale (2026-06-25)** — all 351 accounts freshly scraped. Every account confirmed above all master pool challengers in their bucket.
- **Apify usage API is unreliable** — `/users/me/usage/monthly` shows $0 for ALL accounts even when exhausted. Only `apify~hello-world` actor run+abort confirms a token works.
- **jessfightscancer → list_bucket=None (PERMANENT)** — adult Stage 4 colorectal cancer patient, not a medical parent. Removed from Medical Mom. In MANUAL_OVERRIDES.
- **afresearchgrant → list_bucket=None** — possible org. In MANUAL_OVERRIDES.
- **Stale metrics can be wildly wrong** — autismandourworld stored 21.3, fresh 1,118.5 → jumped to #7 Medical Mom. Never trust stored avg_comments for accounts not in ls_rescrape_v3.json.
- **LS verification loop rule** — compare fresh LS holder metrics vs stored challenger metrics. Scrape any challenger beating a holder. Swap if still wins. Loop ends when 0 stale remain.

### Key Rules (updated 2026-06-26)
- **LS caps expanded** — Medical Mom 200→500, T1D Kids/Parent 50→150, T1D Adult 50→150 (pool only has 107). All new accounts freshly scraped via `scripts/scrape_expansion_handles.py`.
- **450 expansion scrapes** — 294 Med Mom (ranks 201–500) + 100 T1D Kids (ranks 51–150) + 56 T1D Adult (ranks 51–106). 207 records had materially different fresh vs stored metrics. ls_rescrape_v3.json now has 814 handles.
- **OVERFLOW_HANDLES = 27 (Jessica's accounts)** — +3 this session: kelliegerardi (Top Influencer #12, 1.44M), standwithlilah (Medical Mom #67, 68K), lifeofurienju (Medical Mom #45, 88K). faithhinitt stays CI Adults #6. supersofiasstory = Sofia's CP story, 112K, Medical Mom #26.
- **faithhinitt = CI Adults, NOT Top Influencer** — Faith Hinitt, Acute Myeloid Leukemia. CI Adult, not a parent, not an influencer. Permanent.
- **lifeofurienju = SENSITIVE** — memorial account for deceased child Urie Imani. Flag before any outreach.
- **Wrong dataset read risk** — when re-reading Apify results via `runs().list()`, you get the MOST RECENT run, which may be a batch run not the single account. Always read from the specific run's datasetId or the checkpointed JSON.
- **scripts/scrape_expansion_handles.py** — reads `outputs/ls_expansion_to_scrape.json`, scrapes batches of 50, checkpoints to ls_rescrape_v3.json. Resume-safe. Key swap: `--apify-token <KEY>`.
- **T1D Adult pool = 107 total** — can't fill 150 cap. To grow this bucket: need more T1D adult hashtag/follower scraping.
- **Apify token status (2026-06-26)** — diaryrecruitment10 (`ov02ZAAF`) active, partially spent. 450 scrapes cost well under $5. All others exhausted.

### Key Rules (updated 2026-06-26b)
- **Pinned post rule REVERSED for Instagram (PERMANENT HARD RULE)** — ALWAYS filter `isPinned=True` first for BOTH Instagram and TikTok. Do NOT include pinned posts. The old "sort all by date" approach failed because Apify returns only ~12 posts total: old viral pinned posts (from 2023-2025) ended up at positions 10-12 in the sort, massively inflating averages. Real examples: starfish.chronicles 8,535→1,034, the.birch.family 2,329→20, mightymadilynn 1,730→38. Rule confirmed 2026-06-26 with post-level debugging. `non_pinned = [p for p in posts if not p.get('isPinned', False)]; use_posts = non_pinned if non_pinned else posts` — use this code in EVERY scrape script.
- **Full LS re-scrape completed (2026-06-26b)** — 808 LS handles re-scraped with corrected pinned logic → `outputs/ls_rescrape_v4.json`. 71 challengers (T1D Kids 15, CI Adults 35, Top Influencer 21) scraped fresh. Challengers merged into scored.json. LS rebuilt as 811 rows.
- **@reddysameera = Indian actress (flag for review)** — Top Influencer rank #12, 2M followers, 714 avg_cmts. Sameera Reddy is an Indian Bollywood actress. India-based audience. Cherwin to review whether to exclude.
- **scrape_ls_handles.py and scrape_expansion_handles.py both fixed** — `compute_engagement` / `calc_metrics` now filter pinned first. All future scrapes via these scripts are correct. Apply same fix to ANY new scrape script.
- **Challenger verification rule (PERMANENT)** — before any account enters the Launch Shortlist, scrape it fresh (no pinned posts). Never trust stored metrics for ranking decisions.

### Key Rules (updated 2026-06-27)
- **Medical Mom top 500 fully verified** — 441 challengers freshly scraped, 34 swaps made. New floor: 8.3 avg_cmts (was 2.3). Loop complete: remaining 844 non-LS accounts have stored ≤ 2.3, below the 8.3 floor.
- **Top new entrants (2026-06-27)**: thecollectiveprotective (26.9), _keila.jones_ (26.4), hazelmae.medical (21.8), epilepsymomdiaries (20.2), mastering.mthrhd (19.8), skyewolfleystuart (18.8).
- **Overflow cutoff bug fixed** — `write_launch_shortlist_tabs.py` overflow cutoffs were stale: Med Mom was 200 (should be 500), T1D Kids/Adult were 50 (should be 150). Fixed. heyrachelhughes now correctly shows as overflow #501.
- **scrape_ls_handles.py** — now accepts `--handles-file` and `--output-file` flags for scraping any arbitrary handle list.
- **Influencer Replies PDF rates extracted** — WoodCrew (IG Reel $2,500+), moonlitmaddyx (IG Reel £2,000), bemorefab (TikTok £2,500-3,500), amazingabigailgrace (stats-only, no pricing). Media kits saved to `outputs/media_kits/`.
- **Influencer Replies: 16 with confirmed rates, 8 waiting on deliverables** — waiting: theelemonadefamily, asdmama1017, itskelseyboone, lewisempire6, thekristinexy, cassadicurrier, auntihood, amazingabigailgrace.

### Key Rules (updated 2026-06-27b)
- **OVERFLOW_HANDLES = 31** — added 2026-06-27: maycineeley, kay.dudley, kayandtayofficial, _justjessiiii.
- **sav.labrant removed** — met_criteria=No. No longer in influencer pool.
- **@kay.dudley** — Kaylee Dudley, 1.87M followers, 312.8 avg cmts, lupus lifestyle influencer, sister of @kayandtayofficial. Email: kay@currentsmgmt.com (management). category=Macro Mom → Top Influencer pool. Scraped fresh 2026-06-27.
- **Exclusions memory file complete** — `memory/project_launch_shortlist_exclusions.md` has all 42 handles ever removed/excluded. Always check before adding any handle to a bucket.
- **Category source breakdown** — Medical Mom (444): Marketing Shortlist 192, Engagement List Medically Complex 165, bio inference 82. T1D Kids (44): 42/44 bio-inferred. 1,013 accounts Unknown.

### Sheet Row Counts (last verified 2026-06-27b)
| Tab | Rows |
|-----|------|
| Launch Shortlist | 813 data rows — Med Mom 500 + overflow 1 + T1D Kids 150 + T1D Adult 107 + CI Adults 25 + overflow 1 + Top Infl 20 + overflow 7 + DS 2. OVERFLOW_HANDLES = 31. Med Mom floor: 8.3 avg_cmts. |
| Influencer Replies | 26 rows |
| 10k Above | 1,265 |
| Under 10K Master List | 2,768 |
| Beta Testers | 84 |

### Key Rules (updated 2026-06-30)
- **Early Access (US) tab = authoritative "already contacted" exclusion set** — in ENGAGEMENT_LIST sheet (`1uZMIrY316Lyf7MWQCJ25AjZdNnr8TohdLLuCnU-ty6Y`). 1,651 clean handles as of 2026-06-30. Use this (NOT Medical Mom DM Outreach) as exclusion set when finding new beta outreach targets.
- **Early Access handle cleaning** — strip @, /?hl=en query params, leading slashes. Skip rows where handle column has spaces (full names) or full URLs. Use URL column as primary source via `instagram\.com/([A-Za-z0-9._]+)`.
- **1,309 medical/complex accounts NOT in Early Access** — as of 2026-06-30. 302 mid-engagement (5–30 avg cmts) in `outputs/medical_not_in_ea.json`. Re-run cross-reference after each outreach session.
- **New comment example (June 2026)** — "What a huge decision.❤️ You can feel how much thought, love, and advocacy went into choosing what's best for [child name]..." Pattern: name child, acknowledge weight of decision first, warm send-off before DM nudge, two hearts okay on heavy posts.
- **Master handles total: 4,171** — 13 new handles added from Early Access (US) tab: celeste_thompson7, themedicalmom, lilymartin0131, bre.laurent, mightymicahmac, lindssmariejohnson_, carriekern_teamaudrey, life_withthe.moras, arielle.and.emery, kinleys.vm.story, givehollyhope, oliviazapo, the_a_couple.us. All `needs_scrape: True`.
- **COMMENTS tab** — empty as of 2026-06-30. Cherwin pastes profile URLs into col B to start next comment session.

### Key Rules (updated 2026-07-01)
- **DM workflow (PERMANENT)** — COMMENTS tab now has a "DM Part 1" column (col J). Personalized intro generated per account using bio + latest post caption. Runner buttons: "Copy DM 1" (copies personalized Part 1 from col J) + "Copy DM 2" (copies hardcoded standard closing). Playwright handles Instagram comments; runner handles DMs.
- **DM Part 1 — STRUCTURE (PERMANENT):** DM1 has TWO parts: (1) personalized intro — 2-3 sentences specific to this account, anchored to bio + latest post, warm and specific like comment style but more personal; (2) fixed CAIT paragraph — always identical, never customize. Format:
  ```
  Hi [Name],

  [Personalized intro — 2-3 sentences specific to their journey, anchored to bio/latest post]

  We've been building CAIT alongside medical families from the very beginning. Think of it as having the intelligence of ChatGPT, but personalized to you and your family. It can search the web, remembers what matters, manage medications, symptoms, appointments, notes, and can even connect health records like MyChart, so you're not carrying everything on your own.
  ```
  [Name] = parent's first name from bio. If no parent name found → "[Child's Name]'s Mom". The CAIT paragraph is ALWAYS identical — never put diagnosis names, child names, or custom text inside it. The intro paragraph IS personalized per account.
- **DM Part 2 — EXACT TEMPLATE (PERMANENT — hardcoded in runner2.py, never changes):**
  ```
  We'd truly love to invite you to try CAIT. Hearing how it's helped other medical families has meant the world to us, and we'd be honored to see if it could make even a small difference for yours. If you're open to it, we'd also love to hear your honest feedback and collaborate with you along the way, we provide an honorarium for those who participate.

  No pressure at all, we just hope CAIT can be one less thing for you to worry about. Sending you and your family so much love. 💙
  ```
- **Why DM is split into two parts** — DM1 is the warm intro + CAIT pitch (sent first). DM2 is the invitation + honorarium ask (sent as follow-up in same thread). Split feels conversational, not a pitch dump. If someone replies after DM1 Cherwin responds before sending DM2. Long single DMs get ignored or flagged by Instagram.
- **Render runs runner2.py** — Render's dashboard start command overrides the Procfile. runner2.py is always the file to edit. runner3.py is a local copy kept for reference.
- **Bio scrape for DM personalization** — use Apify instagram-scraper details mode on COMMENTS handles, save to outputs/comments_bios.json. Fields needed: full_name, biography. No proxy field. Run before generating DMs.
- **Screenshot every comment (PERMANENT)** — after each Playwright comment post, immediately take a browser screenshot and save to `outputs/screenshots/` named `{handle}_{YYYY-MM-DD}.png`. Boss requirement.
- **"Posted [date]" in runner ≠ Playwright comment posted** — runner marks Posted when Cherwin clicks Done (= DM sent). Always assume comments are NOT posted via Playwright unless explicitly confirmed in the current session.

### Key Rules (updated 2026-07-01b)
- **Screenshot scroll-before-capture (PERMANENT)** — after clicking Post and getting 'posted' result, ALWAYS run a browser_evaluate to find comment text and scrollIntoView before taking screenshot. Pattern: `const els = Array.from(document.querySelectorAll('span, div')).filter(el => el.children.length === 0 && el.textContent.includes(search)); els[0].scrollIntoView({behavior:'instant', block:'center'})`. Without this, comment is off-screen and screenshot shows wrong content.
- **Stale post URL fix pattern** — if scrape URL is old, navigate to the account profile, grab first `/p/` link from grid via `document.querySelectorAll('a[href*="/p/"]')`, check what the post is about, generate a new comment if needed, and post on that URL. Update col C in COMMENTS tab.
- **"Whenever the timing is right" DM nudge** — use this phrase (instead of "whenever you have a moment") for very heavy/sensitive posts (stroke, PICU, major surgery, grief). Softer entry point. Approved variation — add to comment-examples.md rotation.
- **Apify credits near zero** — diaryrecruitment10 (ov02ZAAF) has ~$0.001 remaining as of 2026-07-01. Cannot use Apify for any scraping until cycle resets. Use Playwright profile page scraping as fallback for latest post URL checks.
- **check_latest_posts.py** — utility script to verify queue URLs vs actual latest posts. Requires Apify credits. Located at project root (not scripts/). Delete after use.

### Key Rules (updated 2026-07-02)
- **No "God" in generated comments (PERMANENT)** — CAIT is a brand and must stay religion-neutral. Never use "God", "Jesus", "Lord", "blessing from God", "God's plan" etc. in any generated comment or DM. Still comment on religious accounts. Still be warm. Approved words: "prayer", "faith", "strength", "hope", "community". Applies even when the account name or caption uses "God" (e.g. @noahstory_gglory).
- **DM1 structure confirmed (PERMANENT)** — DM1 = personalized intro (2-3 sentences specific to their account) + fixed CAIT paragraph (always identical). The personalization is in the INTRO, not in the CAIT paragraph. Never customize the CAIT paragraph. See exact structure in Key Rules (2026-07-01) above.
- **DM1 voice ≠ comment voice (PERMANENT)** — Comments are public reactions to a specific post, third-person narration ("is a gift to every family", "incredible to follow"). DM1 intro is private, talks directly TO the person: opens with "We came across [X] and wanted to reach out", 1-2 specific sentences showing you know their story, closes with "We wanted to reach out / connect." Never use comment-style audience-facing phrases ("is a reminder to this community", "is incredible to follow", "is a gift to every family") in DM1.
- **COMMENTS tab as of 2026-07-02** — 22 rows (rows 2–23). Comments + DM1 all written. @brittany.warrior.official (row 12) = confirmed satire, skip permanently.

### Key Rules (updated 2026-07-03b)
- **DM1 format (PERMANENT CORRECTION)** — correct format confirmed from original batch examples: `"Hi [Name]!\n\nWe came across your page and just wanted to say how much we admire/love [specific detail].\n\n[CAIT paragraph]"`. CAIT paragraph = `"We've been building CAIT alongside medical families from the very beginning. Think of it as having the intelligence of ChatGPT, but personalized to you and your family. It can search the web, remembers what matters, manage medications, symptoms, appointments, notes, and can even connect health records like MyChart, so you're not carrying everything on your own."` Always bio-scrape before generating DM1s — bios contain diagnosis names, child names, foundation names that make the personalization genuine.
- **@dinaanp__medical_mom (row 3)** — child is **Eli**, brain cancer. Video text: "Just Eli kicking brain cancers butt 🔔🔔". Comment + DM1 now written. Confirmed via Playwright /watch (yt-dlp can't download IG posts without auth — use Playwright instead).
- **@brittany.warrior.official DELETED** — confirmed satire via Playwright. Bio: "America's Trashiest Satire Family." Post tagged #RealLifeSatire. Row deleted from COMMENTS tab. Never re-add.
- **Bio scrape before DM1 generation (PERMANENT)** — always run Apify instagram-scraper on all COMMENTS handles before generating DM1s. Saves to `outputs/comments_bios.json`. 21-account scrape costs ~$0.10.

### Key Rules (updated 2026-07-04)
- **COMMENTS posted (2026-07-03/04)** — 20 comments posted via Playwright (rows 2–22, skipping row 21 @hannesdays — already posted on their latest post). All SENSITIVE rows (15 hollytsummers, 16 eliasstrongandbrave, 18 somekinderwonderful) approved and posted. All screenshots saved to outputs/screenshots/. DMs sent via runner same session. COMMENTS tab fully cleared.
- **CAIT paragraph confirmed (PERMANENT)** — "We've been building CAIT alongside medical families from the very beginning. Think of it as having the intelligence of ChatGPT, but personalized to you and your family. It can search the web, remembers what matters, manage medications, symptoms, appointments, notes, and can even connect health records like MyChart, so you're not carrying everything on your own." Cherwin confirmed this is correct. Never change.
- **DM personalization quality bar (Cherwin-confirmed)** — Cherwin reviewed the full batch and explicitly confirmed this level of personalization is what he wants every time: child's actual name, specific diagnosis (the rarer the better), foundation name if present, genuine admiration. Bio scrape is mandatory before every DM generation session.
- **Skip already-posted accounts** — before Playwright, check if account was already commented on recently. Skip row, do not re-post.

### Key Rules (updated 2026-07-03)
- **COMMENTS tab as of 2026-07-03** — re-scraped via `--mode scrape --force` — 7 posts changed URLs. New comments written for rows 7, 8, 15, 16, 20, 23. Row 3 (@dinaanp__medical_mom): new post was hashtags-only (now resolved — see 2026-07-03b). Row 12 (@brittany.warrior.official): deleted (satire).
- **@gideonabelthebrave (row 22 after brittany deletion)** — 22q deletion syndrome + pediatric cancer. 100 days CVICU as newborn. Now on chemo (67 days), care moving to MD Anderson, surgery beginning of August. Parent name not in bio → DM1 opens "Hi Gideon's Mom".
- **Instagram loop giveaway organizers (2026-07-03)** — `scripts/find_loop_giveaway_organizers.py` scrapes 8 hashtags (#loopgiveaway, #loopgiveaways, #instaloopgiveaway, etc.), identifies repeat posters. Found: @inkaloops (8K, 18 posts) + @socialtraingiveaways (51K, 8 posts). Already have: savvygiveaways, pzgiveaways, betterdaysgiveaways, bigpicturegiveaways, happyhaven, socialstance, rosalillyfamily, candycampero. **Next step**: scrape followers of existing organizers to find more (~$0.05 cost).

### Key Rules (updated 2026-07-01c)
- **Apify key rotation (2026-07-01c)** — ov02ZAAF (Caitlist .env) EXHAUSTED. Two fresh keys found and confirmed working via real Instagram scrape: `nv3F9GQd` (Apify Trial folder, `.env` updated to use this), `yC01lcvS` (Resume Builder/Sourcing — backup). Keys `k516jwmC` (LinkedIn agent) and `nFiaA7hGRXBtxPX2hemnY5vdOXQyOb2Cp0Qo` (Google Maps classroom) are invalid (wrong account).
- **hello-world test ≠ real credits** — `apify~hello-world` passes even on near-zero accounts (costs < $0.001). ALWAYS test with `apify/instagram-scraper` on 1 real URL to confirm credits before starting a batch scrape.
- **8 new Jessica handles added (2026-07-01c)** — scraped fresh with nv3F9GQd. Categories: averythepokekid (Medical Mom — pancreatic cancer warrior, NOT T1D), racell0 (Medical Mom — cancer), awakeningfiresprite (Chronically Ill Adults), kinleys.vm.story (Medical Mom), darcies_story (Medical Mom), deboratlengen (Down Syndrome — added to DS_HANDLES), nurse.hadley (Top Influencer), thepasinis (Top Influencer).
- **deboratlengen = Down Syndrome** — 124K followers, 397 avg cmts, verified, managed by Social Alchemists (debora@social-alchemists.com). Added to DS_HANDLES in write_launch_shortlist_tabs.py. DS section now has 3 accounts: willsjourney21, erinadvocates, deboratlengen.
- **OVERFLOW_HANDLES = 39** — +8 this session: thepasinis, kinleys.vm.story, racell0, averythepokekid, darcies_story, nurse.hadley, deboratlengen, awakeningfiresprite.
- **Launch Shortlist = 815 rows** — as of 2026-07-01c rebuild.
- **Apify key test protocol** — run `apify/instagram-scraper` on `https://www.instagram.com/nasa/` (1 result, details mode). If SUCCEEDED = real credits. If "exceed remaining usage" error = exhausted.

### Key Rules (updated 2026-07-04b)
- **COMMENTS workflow when Cherwin pastes IG profile URLs into col B** — extract handle via `instagram\.com/([A-Za-z0-9._]+)` regex (strip trailing slash/params), write to col A, run `--mode scrape`, run Apify bio scrape (23 accounts → `outputs/comments_bios.json`), generate comments + DM1s in-session, write both to col E + col J in one batch_update pass.
- **Notable accounts (2026-07-04b batch)**: @dren54 (33K, Dan Reynolds, advocate for Brookie/CP), @savannahcbravo (20K, TX, management via jakerosenentertainment), @onepoundbabymom (5K, Audri, Micro Preemie + ASD + CP + Hearing Loss + GTube), @gemandocie (Ocie, IMAGe syndrome — very rare).
- **Apify key nv3F9GQd still active** — used for post scrape + bio scrape. yC01lcvS = backup.

### Key Rules (updated 2026-07-07)
- **Right panel scroll trick (PERMANENT)** — Instagram desktop post pages have a scrollable right panel for comments. If `[aria-label='Add a comment…']` returns "does not match any elements", run: `Array.from(document.querySelectorAll('div')).filter(d => d.scrollHeight > d.clientHeight && d.clientHeight > 200 && d.offsetWidth < 500 && d.offsetWidth > 200).forEach(p => p.scrollTop = p.scrollHeight)` — this reveals the comment box. Apply on every post before fill_form as a precaution.
- **COMMENTS tab posted (2026-07-07)** — all 23 rows posted. Row 23 @tiffygs posted by Cherwin directly (Playwright fill failed). All screenshots in outputs/screenshots/. COMMENTS tab fully cleared.
- **"just screenshot" instruction** — when Cherwin says "just screenshot", do NOT scroll, navigate, or re-run any evaluate — only call browser_take_screenshot. He has already positioned the view.

### Key Rules (updated 2026-07-07d)
- **Geographic scope expanded (PERMANENT as of 2026-07-07)** — DM outreach is NO LONGER US-only. Canada, UK, and Australia are fully acceptable targets. All future hashtag batches may include UK/CA/AU medical moms. CAIT is English-language; "mum" spelling accounts are fine.
- **B54 Video Medical Moms (2026-07-07)** — 21 tags, 14 accounts. Key learning: reel-compound hashtags (#medicalmomreel, #chdmomreel etc.) are dead on Instagram — nobody uses them. Productive: specialneedsvlog, medicalmomcommunity, medicalmomjourney, feedingtubemom, gtubemom, trachmomlife. Reel bonus (+10 in score_content) fires when 6+ of 12 posts are reels.
- **B55 UK/Canada/Australia Medical Moms (2026-07-07)** — 26 tags, 55 accounts, 500–20K followers. Country batch (orgs flagged not written). Productive: specialneedsmum, senmum, sendmum, ndismum, ndisparent, autismmumaustralia, specialneedsaustralia. Dead: medicalmomaustralia, heartmumaustralia, all Canada compound tags.
- **B54+B55 moved to after last validated row (2026-07-07)** — 69 accounts originally appended to bottom (rows 2302–2370). Safe positional tail move executed: now at rows 2140–2208. Last validated row = 2139 (fitnfabkim, APPROVE). Old unvalidated accounts pushed to 2209+.

### Key Rules (updated 2026-07-07c)
- **Base64 comment injection (PERMANENT)** — NEVER manually type Unicode escape sequences in Playwright evaluate params. Emoji get re-encoded as wrong characters (e.g. 🦵 instead of 🤍). Always: (1) read comments from sheet into `outputs/comments_to_post.json` (UTF-8 source); (2) Python-encode: `base64.b64encode(comment.encode('utf-8')).decode('ascii')`; (3) decode in browser JS: `new TextDecoder().decode(Uint8Array.from(atob(b64), c => c.charCodeAt(0)))`. Guarantees byte-perfect emoji every time.
- **Combined scroll+fill+post evaluate (PERMANENT)** — combine right-panel scroll + base64 fill + `setTimeout(click Post, 600ms)` into ONE evaluate call. Reduces tool calls from 5-6 to 3 per row (navigate → combined evaluate → screenshot). See session memory 2026-07-07c for full JS pattern.
- **COMMENTS posted (2026-07-07c)** — all 20 rows (2-21) posted via Playwright. Rows 2 + 3 posted with wrong emoji 🦵 (user approved). All 6 SENSITIVE rows approved and posted. Row 13 (@letscurelucas) used user-edited comment (no DM nudge). All screenshots saved to outputs/screenshots/. COMMENTS tab fully cleared.

### Key Rules (updated 2026-07-07b)
- **New COMMENTS batch (2026-07-07b): 20 accounts (rows 2–21)** — 21 URLs pasted by Cherwin, 1 dup (busybeing.elyse row 6) removed. Handles extracted to col A, scrape + bio scrape run, all 20 comments + DM1s generated and written. SENSITIVE rows: 2 (@lifewithmommanichole Stage 4 cancer + CHD), 3 (@alyssaaquintanaa Camila HLHS heart transplant), 9 (@medicalmom2021 sick in hospital without baby), 10 (@the_heartful_homemaker brain surgery/brain bleed), 15 (@raisingvalentines emotional reel), 21 (@mrs_sunday_runday daughter hospice + stroke). Playwright pending.
- **Row 15 @raisingvalentines via Playwright** — empty caption; navigated to post via browser, reel shows woman in car with text overlay "I'll always remember you saw me having a hard time and you chose to make it harder." Flagged SENSITIVE. Comment + DM1 generated from video text.

### Key Rules (updated 2026-07-08)
- **New COMMENTS batch (2026-07-08): 20 accounts (rows 2–21)** — Cherwin pasted 20 IG profile URLs into col B. Handles extracted to col A, --mode scrape run, Apify bio scrape run, all 20 comments + DM1s generated and written. Row 19 (@running.on.rare / Stephanie Primarolo, Maisie rare disease) prioritized first. SENSITIVE: row 15 @f_coley_x (needs Cherwin approval). 4 under-1K accounts included (Cherwin added directly): emmas_cure (367), jax_battling.heart (403), sierras_world_official (496), f_coley_x (964). Playwright session pending.
- **Under-1K accounts in COMMENTS batch** — when Cherwin pastes profile URLs directly, generate regardless of follower count. He chose the accounts manually.

### Key Rules (updated 2026-07-08b)
- **Handle underscores matter** — `bravelikefinley` (no underscores) = 404 not found. Correct handle is `brave_like_finley` (with underscores). Always verify exact handle spelling when Apify returns 0 followers / Page Not Found.
- **Under-1K in new batch (rows 2–3)** — marykatepender (793, Rory/Apraxia) and brave_like_finley (302, Finley/Spina Bifida+Chiari+Hydro+Trache+Gtube). Both added directly by Cherwin, generated regardless.
- **Row 21 skip comment** — running.on.rare (Stephanie): DM only, no Instagram comment.
- **Row 23 defer** — ashlee_johnsons_scents_at_home: tomorrow's batch.

### Key Rules (updated 2026-07-09)
- **COMMENTS posted (2026-07-08/09)** — 21 comments posted via Playwright: rows 2–20 + 22 + 17 (f_coley_x). Row 17 was SENSITIVE but Cherwin approved mid-session ("dont skip any everything is approve"). Row 21 (running.on.rare) skipped — DM only. Row 23 (ashlee_johnsons_scents_at_home) deferred to next batch. All 21 screenshots saved to outputs/screenshots/. COMMENTS tab fully cleared except rows 21 + 23.
- **SENSITIVE approval mid-session** — when Cherwin says "dont skip any everything is approve", post all remaining rows including SENSITIVE ones. Strip [SENSITIVE] prefix before injecting comment text.
- **Apify token active (2026-07-09)** — `.env` token `apify_api_CG...` confirmed working. Tested via real instagram-scraper run on nasa profile. SUCCEEDED with credits. Previous token notes (nv3F9GQd / ov02ZAAF) are superseded — use whatever is in .env and test before batch runs.

### Key Rules (updated 2026-07-09b)
- **New COMMENTS batch (2026-07-09b): 20 accounts (rows 2–21)** — Cherwin pasted 20 IG profile URLs into col B. Handles extracted to col A. Scrape + bio scrape run. All 20 comments + DM1s generated and written to col E + col J. SENSITIVE: rows 4 (@clairebustrom/Ellie NICU overwhelmed), 10 (@lilbit213/grief post), 20 (@ourrarelife/Gracelyn terminal diagnosis). Playwright pending.
- **@lilbit213 grief post clarification** — Caption says "Thank you for how you loved my son." Elias (her 24-week micro preemie, microcephaly warrior) is ALIVE. Someone else who loved Elias passed away (likely a caregiver/nurse/family friend). Comment reflects this correctly.
- **6 under-1K accounts in batch** — teamunitasmaximus (558), natalialiahhh (313), mightymedicalmoms (558), nikkib3.20 (527), our_49xy_journey (782), littlelightofminellc (395). Cherwin added directly — generated regardless.

### Key Rules (updated 2026-07-09c)
- **COMMENTS posted (2026-07-09c)** — all 20 rows (2–21) posted via Playwright. All screenshots saved to outputs/screenshots/. SENSITIVE rows 4 (clairebustrom/Ellie NICU), 10 (lilbit213/grief Elias alive), 20 (ourrarelife/Gracelyn terminal) all posted — Cherwin approved all at session start ("i approve all post"). COMMENTS tab fully cleared.
- **"I approve all" instruction** — when Cherwin says "i approve all post" at session start, post all rows including SENSITIVE without pausing for individual approval. Strip [SENSITIVE] prefix before base64 encoding as usual.

### Key Rules (updated 2026-07-10)
- **New COMMENTS batch (2026-07-10): 21 accounts (rows 2–22)** — Cherwin pasted 21 IG profile URLs into col B. Handles extracted to col A. Scrape run (alexisellliston took 10 Apify retries but succeeded). Bio scrape run. All 21 comments + DM1s generated and written to col E + col J. No SENSITIVE rows in this batch.
- **@jociane_oliveir (row 2) — Portuguese account** — 48.6K followers, posts in Portuguese. Comment generated in English. Cherwin approved — posted 2026-07-10.
- **ellie_vs_pfic1 (row 17) — comment edited by Cherwin in sheet** — always read live col E before Playwright, not in-memory value.
- **Notable accounts**: we.are.takingcare (Benjamin NCBRS 8th bday), sadie.madison.kisling (Sadie Sturge Weber), lianabwellness (Atlas HIE+CP pool push), juuliavillan (Lilly CF+gtube), sophiealice_senmum (UK SEN Florence), bravelikenolan (Nolan ESRD+liver transplant), ellie_vs_pfic1 (Ellie PFIC1+ostomy).
- **@actuallyitsjackie (row 18) — comment box found on retry (next session)** — previous session had no box; new session navigated fresh and box appeared. Comment posted successfully.

### Key Rules (updated 2026-07-10b)
- **COMMENTS posted (2026-07-10/11)** — All 22 rows posted via Playwright. Rows 2–17 posted first session. Rows 18–22 posted second session (actuallyitsjackie box appeared on fresh navigate). All 22 screenshots saved to outputs/screenshots/. COMMENTS tab fully cleared.

### Key Rules (updated 2026-07-11b)
- **New COMMENTS batch (2026-07-11b): 20 accounts (rows 2–21)** — Cherwin pasted 20 IG profile URLs into col B. Handles extracted to col A. Scrape + bio scrape run. All 20 comments + DM1s generated and written to col E + col J. SENSITIVE: row 15 (sophia_duke, grief at golf camp — Dawson) + row 20 (isaac_fighting_battens_disease, CLN2 Batten terminal, 10th birthday). Playwright pending.
- **PowerShell dollar-sign expansion bug** — `@"..."@` double-quoted here-strings expand `$3` to empty string. Always use `@'...'@` single-quoted here-strings when writing Python scripts via PowerShell that contain dollar signs. Fixed acureforeverett DM1 via separate fix_row5.py with single-quoted here-string.
- **acureforeverett (Everett)** — HK1 ultra-rare condition, family fundraising $3 million for a cure. Category: Medical Mom.
- **Notable accounts (2026-07-11b batch)**: jilldmadero (Maverick, trach → swallow study), lauraashley.fahy (Leah, Dravet syndrome), thekidwithanostomy (Zacari, ostomy/autism/Hirschsprung's), overatkates (Frank, Group B Strep awareness/CP), emmy_says_ (Emersyn, gestalt language processing), travelwithautismkids (Sicily/autism travel), medical.mama.moments (Levi, short gut/SBS/TPN), feeling_grounded (Pitt Hopkins rare disease parenting), teamsofiastrong (Sofia, anoxic brain injury, 6th bday), life.with.alvina (Alvina, STXBP1, shopping cart milestone), holdingbothtruths (Cal, Cockayne syndrome/equine therapy), coffey_house (Friedreich's ataxia/FA family), joashline (Andrew, SYNGAP1 advocacy), fearless.fiona (Fiona, Rett Syndrome), sarajerm (Cri Du Chat awareness).

### Key Rules (updated 2026-07-13b)
- **Comment + DM1 personalization standard (PERMANENT as of 2026-07-13b)** — Before generating any comment or DM1, find what is important to THIS specific person: what they're proud of, what their page is really about, what they'd genuinely want to hear. Draw from bio + latest post + their overall story. The comment/DM1 should feel like it was written by someone who actually studied their page. If it could have been written for any account, it's wrong. If it could only be written for this person at this moment, it's right. This applies to every single account going forward — no exceptions.
- **Row 10 added to COMMENTS** — stein.fitness.and.nutrition (Jenna Stein, 25.5K followers, NASM certified personal trainer + nutrition coach, medical mama). Son has Moebius syndrome + G-tube + trach. Post: first time publicly sharing son's story, anchored to him learning to clap independently. Comment + DM1 written and confirmed.
- **stein.fitness.and.nutrition handle fix** — handle was stored with leading `\r\n` in sheet. Cleaned via gspread update_cell. Rule: always `.strip()` handles when reading from sheet (already in rules — applies here too).

### Key Rules (updated 2026-07-13)
- **COMMENTS posted (2026-07-11b/13)** — Playwright continuation: rows 13–19 posted (teamsofiastrong, life.with.alvina, sophia_duke, holdingbothtruths, coffey_house, joashline, fearless.fiona). Rows 20 + 21 skipped per Cherwin. All screenshots saved to outputs/screenshots/. COMMENTS tab fully cleared.
- **OVERFLOW_HANDLES = 40 (as of 2026-07-13)** — therealsteffig added (Jessica request). thefitnesswaytocope was already in list (#15 from original 17). Full set now has 36 Jessica accounts + 4 Cherwin accounts. Cherwin's 4 (maycineeley, kay.dudley, kayandtayofficial, _justjessiiii) appear only if they earn rank naturally — still in OVERFLOW_HANDLES set in write_launch_shortlist_tabs.py.
- **therealsteffig = age-restricted Instagram profile** — Apify returns bio but 0 followers/posts (`isRestrictedProfile: True`, `restrictionReason: "You must be 13 years old or over"`). Bio: Steffi Gonzalez, Orlando FL, Latina beauty/Disney/accessibility influencer, Sephora Squad. Email: Steffi@kannco.com. Metrics must be obtained manually. Will appear on Launch Shortlist as overflow regardless of rank. Run write_launch_shortlist_tabs.py to rebuild when ready.
- **Age-restricted profiles** — when Apify returns 0 followers with `isRestrictedProfile: True`, metrics cannot be scraped. Report to Cherwin, add to OVERFLOW_HANDLES if Jessica's request, and flag as "metrics manual" in any ranking context.
- **New COMMENTS batch (2026-07-13): 8 accounts (rows 2–9)** — stein.fitness.nutrition = confirmed 404 (deleted). Remaining 8 scraped + bio scraped. Comments + DM1s generated and written. SENSITIVE: row 3 (isaac_fighting_battens_disease, CLN2 Batten terminal) + row 7 (amalietelo, Lissencephaly, 5 nights PCH). Playwright pending.
- **HCP DM1 personalization rule** — when an account is a nurse/HCP (bio says "RN", "nurse", "pediatric nurse", "OT", "SLP" etc.), DM1 intro must acknowledge their clinical role AND mention CAIT already has nurses/HCPs in the community. Approved phrasing: "We actually have several nurses and healthcare providers in our CAIT family already and absolutely love working with all of them!" Confirmed for misstiffjones (CdLS mama + pediatric RN) 2026-07-13.
- **stein.fitness.nutrition = permanent 404** — confirmed not_found via 2 separate Apify runs. Deleted from COMMENTS tab. Never re-add.
- **zayvis_journey trailing \\r bug** — handle stored with trailing carriage return in sheet. Fix: always strip handles with `.strip()` when reading from sheet. gspread batch_update was used to correct.

### Key Rules (updated 2026-07-14)
- **Playwright: rows 2–10 fully posted (2026-07-14)** — all 10 comments posted, all screenshots saved to outputs/screenshots/. Row 7 (amalietelo) posted without DM nudge per Cherwin. All SENSITIVE rows (3 isaac, 7 amalietelo) approved and posted.
- **New COMMENTS batch (2026-07-14): rows 11–22 fully posted** — all 12 comments posted via Playwright. SENSITIVE rows 12 (thejodiewallace) + 13 (the_victoriaannemarie) approved and posted. Row 17 (brericken) needed re-navigate. Row 18 (nancymmccullough) needed Comment SVG click before "Add a comment…" box appeared. All 12 screenshots saved to outputs/screenshots/. COMMENTS tab fully cleared.
- **Comment SVG click pattern** — when `[aria-label="Add a comment…"]` returns "no box" but page has `[aria-label="Comment"]` SVG, dispatch a click event on that SVG first: `document.querySelector('[aria-label="Comment"]').dispatchEvent(new MouseEvent('click', {bubbles:true}))`. Then retry fill on next evaluate call. Box appears after the SVG click triggers it.
- **Notable accounts in new batch**: motleybree (tube-fed inclusive brand project), mals_journey30 (HIE+CP+epilepsy), tylerthetough (medical mama rare genetic condition + g-tube, marriage post), michelleandfamilyiow (UK/Isle of Wight, From Plate to Syringe tube feeding real food blends), taceyinthebetween (OEIS complex/cloacal exstrophy — extremely rare, surgery at Children's National), smile_for_luca (Luca Moebius Syndrome, first TikTok friend meetup).
- **Row 7 no DM nudge rule** — when Cherwin says "no need dm nudge on comments" for a specific row, strip only the DM nudge sentence but keep rest of comment. Apply only to that row.

### Sheet Row Counts (last verified 2026-07-14)
| Tab | Rows |
|-----|------|
| Launch Shortlist | 815 rows. DS section: 3 (willsjourney21, erinadvocates, deboratlengen). OVERFLOW_HANDLES = 40. |
| COMMENTS | 0 — fully cleared. All 22 rows (2–22) posted 2026-07-14. |
| Medical Mom DM Outreach | 2,370 rows. Last validated row: 2139. B54+B55 at rows 2140–2208. |
| Email | 159 |
| Influencer Pipeline | 122 |
| Foundations & Organizations | 41 |
| HIGH ENGAGERS | 15 |

### Key Rules (updated 2026-07-14b) — PIPELINE AUTOMATION BUILD
- **Runner has 2 new tabs (runner2.py + runner3.py synced)** — **Add Links** (Cherwin pastes IG links from his phone → handles extracted server-side, deduped, appended to COMMENTS col A+B; post/reel URLs saved to Post URL col with handle blank for Claude to resolve) and **Review** (all pending accounts as scrollable cards: editable Comment + DM1, SENSITIVE badge, Evidence block, per-card Approve + sticky Approve All). New routes: `/api/add-links`, `/api/save-review`, `/api/approve`, `/api/approve-all`, `/api/set-share-url`, `/api/get-share-url`.
- **COMMENTS tab has 2 new columns (auto-created by runner)** — "Approval" (Approved/blank, written by Review tab) and "Evidence" (why an auto-discovered account qualified — post links + reason, written by Claude during discovery pass). Once Cherwin starts using the Review tab, Playwright sessions must only post rows where Approval = "Approved".
- **"Runner Config" sheet tab** — B1 = share post URL for the batch. Set from Review tab, read by the local Playwright session for the DM share step. Lives in the sheet so it works across Render/local.
- **scripts/slack_notify.py** — posts summary (chat.postMessage) + uploads screenshots (external upload flow). Needs `SLACK_BOT_TOKEN` + `SLACK_CHANNEL_ID` in .env (bot scopes: chat:write + files:write, bot invited to channel). CLI: `--test`, `--summary "..."`, `--screenshots YYYY-MM-DD` (screenshots thread under summary when both given). Run at end of every Playwright session.
- **scripts/daily_discovery_feed.py** — daily discovery mimicking Cherwin's feed browsing: rotates 8 tags/day from a 32-tag proven pool (day-of-year rotation), keeps 1–3 **evidence posts** (URL + caption + tag) per candidate, dedupes against master_handles.json + COMMENTS + Medical Mom DM Outreach + Early Access (US) (cached 3 days at outputs/early_access_handles_cache.json) + outputs/discovery_rejects.json. Profile-scrapes candidates (500 min followers default), flags orgs, outputs `outputs/daily_discovery_candidates.json`.
- **Discovery judgment pass (Claude, in-session, after the script)** — read the candidates JSON, apply the gold-standard test (@heyitsr0sie/@daisyweston: real person, named child, medical condition, personal content, English), write survivors to COMMENTS with Evidence col filled ("found via #tag: [post_url] — reason"), log rejects to outputs/discovery_rejects.json as {handle: reason} so they're never re-surfaced.
- **New daily flow (target)** — (1) discovery auto-feeds COMMENTS + Cherwin adds finds via Add Links tab; (2) Claude scrapes + generates comments/DM1s; (3) Cherwin reviews/edits/Approve All on phone; (4) Playwright: comment → like → screenshot → DM1 → DM2 → share post per approved row; (5) slack_notify.py uploads screenshots + summary. Cherwin's manual steps: finding (optional), approving, keeping Edge open.
- **Playwright DM automation (Phase B — NOT yet tested)** — after comment+like+screenshot: navigate profile → Message → base64-inject DM1 → send → DM2 (exact template from runner copyDM2) → send → share post (share dialog on the post; fallback: post URL as 3rd DM). Test on 2–3 accounts with Cherwin watching before any full batch. Auto-stop on Instagram "limited" warnings and report to Slack.
- **Deploy note** — runner changes require commit + push for Render to pick them up.

### Pending — Next Steps
0. **AUTOMATION ROLLOUT — PAUSED 2026-07-14, RESUME 2026-07-15 per Cherwin** — all code built + verified locally, NOTHING deployed. Old workflow stays until rollout. Resume order: (a) commit + push runner2/runner3 so Render gets the new tabs; (b) Cherwin creates Slack bot (api.slack.com/apps → chat:write + files:write → install → invite to channel → token + channel ID into .env); (c) test `slack_notify.py --test`; (d) first `daily_discovery_feed.py` run + Claude judgment pass; (e) Playwright DM automation test on 2–3 accounts with Cherwin watching.
1. **Launch Shortlist rebuild** — run `py scripts/write_launch_shortlist_tabs.py` to reflect therealsteffig in OVERFLOW_HANDLES (now 40 total).
3. **therealsteffig metrics** — Cherwin to manually check follower count (Instagram age-restricted).
4. **Loop giveaway** — scrape followers of @savvygiveaways + @inkaloops to find more organizer accounts (~$0.05 Apify cost).
5. Cherwin review @reddysameera (Top Influencer #12) — Indian actress, likely non-US audience.
6. Scrape 41 unscraped handles (florence_and_the_heart_machine. + 40 new Early Access/FOR MARKETING PURPOSE) — use current .env token. After scrape: re-run categorize + rebuild.
7. Send/review 11 Gmail drafts created 2026-06-24.
8. Review CI Adults very-large accounts: @bridget (1.83M), @embracingecho (1.01M), @thetiabeestokes (1.09M), @eviemeg (935K), @katygharrell (586K) — decide if any should be list_bucket=None.
9. Cherwin validate Medical Mom DM Outreach batch rows: B45 (1860–1872), B47+B50 (2036–2041), B48 (2004–2035), B49 (1928–1966), B51 (1958–1981), B52 (2079–2120).
10. T1D Adult bucket only 107/150 — grow via T1D adult hashtag scraping.
11. Send deliverables to: theelemonadefamily, asdmama1017, itskelseyboone, thekristinexy, cassadicurrier, auntihood, amazingabigailgrace so they can quote rates.

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
