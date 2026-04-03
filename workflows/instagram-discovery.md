# Workflow: Instagram Discovery

## Objective
Find qualified Instagram accounts for either the 50 Million List (journey accounts/influencers) or CAIT Community tab (therapists, BCBAs, educators with products), enrich with email where required, and write to the correct tab.

## When to Run
On demand. Run per target tab:
- `instagram_50million` → writes to "50 Million List"
- `instagram_cait_community` → writes to "CAIT Community"

## Required Inputs
- Category flag: `instagram_50million` or `instagram_cait_community`
- Diagnosis category to target (e.g., `autism`, `medically_complex`, `down_syndrome`, `t1d`)
- Batch size (default: 5)
- Apify token in `.env`
- Google Sheets credentials in `.env`

## Steps

### Step 1 — Load the Dedup Set
Run: `scripts/read_sheet.py`
Returns master set of all known usernames and URLs across all non-ADHD tabs.

### Step 2 — Select Search Hashtags
Load from `knowledge/diagnosis-categories.md` — select hashtags for the target diagnosis.

**For `instagram_cait_community`**, prioritize hashtags that surface professional accounts:
- #bcba #bcbastudent #behaviortherapist
- #pediatricot #occupationaltherapy #sensoryprocessing
- #slp #speechtherapist #speechlanguagepathologist
- #pediatricspeech #feedingtherapy
- #pediatrician #pedsrn #pediatricnurse
- #specialeducationteacher #iepadvocate #autismeducator

**For `instagram_50million`**, use diagnosis-specific hashtags from `knowledge/diagnosis-categories.md`.

### Step 3 — Run Apify Hashtag Search
Run: `scripts/instagram_discovery.py --category [category] --hashtags [list]`

**Actor:** `apify/instagram-hashtag-scraper`
**maxItems:** 100 posts per hashtag (will yield ~30–50 unique profiles)
**Goal:** Collect profile usernames for qualification

### Step 4 — Run Profile Qualification
For each unique profile discovered:

Run: `scripts/instagram_discovery.py --qualify --usernames [list]`
Uses `apify/instagram-profile-scraper` to pull profile data.

Apply ALL filters from `knowledge/qualification-standards.md`:
1. Female account check (bio, name, profile photo context)
2. USA signal (bio keywords, location, hashtags used)
3. Active in last 30 days
4. 15+ real comments avg across last 3 posts
5. Audience = parents/caregivers (not clinician-only)
6. For CAIT Community: sells a product or course

**Scoring:** Note tier (1/2/3) based on follower count and engagement level.

### Step 5 — Dedup Check
For each qualified account:
- Normalize username (lowercase, strip @)
- Check against dedup set — skip if found anywhere in sheet

### Step 6 — Email Enrichment (CAIT Community tab — required; 50 Million List — optional)
Run: `scripts/enrich_email.py --usernames [qualified_list]`

Pipeline:
1. Bio regex scan for email pattern
2. Follow link in bio → scrape website contact/about/work-with-me pages
3. Look for mailto: links on website
4. If still not found: log "not found" in Email Source column
5. Hunter.io: skip until configured

For CAIT Community: still add the entry even if email not found — note "not found" in Email Source. Do not discard qualified accounts just for missing email.

### Step 7 — Build Sheet Rows
For each qualified, enriched account compile:
- Username (no @)
- Profile Link (https://instagram.com/username)
- Followers
- Avg Comments (real, last 3 posts)
- Avg Likes (last 3 posts)
- Email (or blank)
- Email Source ("bio", "website", or "not found")
- Website (from bio, or blank)
- Category (diagnosis focus)
- Notes (tier, product/course name for CAIT Community, flags)

### Step 8 — Write to Sheet
Run: `scripts/write_sheet.py --tab [tab_name] --data [results]`
Stop at batch size. Append only — never overwrite.

### Step 9 — Log the Run
Write to `memory/YYYY-MM-DD.md`:
- Accounts found vs. qualified vs. written
- Which hashtags performed best
- New hashtags discovered in bios/posts (add to diagnosis-categories.md)
- Email find rate (how many out of 5 had emails — for CAIT Community runs)
- Any accounts worth flagging for Cherwin review (Tier 1, exceptional engagement)

## Expected Output
5 new rows in the target tab. CSV fallback in `outputs/` if Sheets fails.

## Error Handling

| Error | Response |
|-------|----------|
| Apify hashtag scraper returns 0 results | Try next hashtag from list. Log which hashtags returned 0. |
| Profile scraper blocked/rate limited | Pause 5 minutes, retry once. Log if still failing. |
| All 5 qualified accounts are duplicates | Try next hashtag batch. Log that category may be partially saturated. |
| Website scraper returns no email | Mark "not found" in Email Source. Still write the row. |

## Notes
- Always try at least 3 different hashtags per run — engagement varies by hashtag.
- For CAIT Community runs: quality takes priority over speed. 5 excellent entries beat 5 borderline ones.
- When an account has 100+ avg comments, add "FLAG: Tier 1" to Notes column — Cherwin reviews these manually.
- New hashtags found in discovered profiles should be noted in the run log and considered for future runs.
