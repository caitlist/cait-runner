# Google Sheet Structure

**Sheet ID:** `1GpeLSbjGTcKe_V1gWYehZcPFU8Vai1q4A9-xLnRGFhA`

This file defines every tab, its column schema, and the exact rules for writing to each.

---

## Tab: 50 Million List

**Purpose:** Mid-to-high engagement Instagram journey accounts and influencers CAIT is considering for promotion partnerships. These ARE CAIT's users.

**Status:** Has existing data — read before writing.

**Column Schema:**

| Column | Field | Notes |
|--------|-------|-------|
| A | Username | Instagram username without @ |
| B | Profile Link | Full URL: https://instagram.com/username |
| C | Followers | Number only (e.g., 45000) |
| D | Avg Comments | Average across last 3 posts (real comments only) |
| E | Avg Likes | Average across last 3 posts |
| F | Email | Email address if found, blank if not |
| G | Email Source | "bio", "website", "hunter", or "not found" |
| H | Website | Website URL from bio if present |
| I | Category | Diagnosis focus (e.g., "autism", "medically complex", "T1D", "Down syndrome") |
| J | Notes | Tier, partnership angle, any flags for Cherwin review |

**Qualification required:** Female, USA, active, 15+ real comments avg.

---

## Tab: CAIT Community

**Purpose:** Therapists, BCBAs, OTs, SLPs, educators, pediatric doctors selling courses or products. These people will have a profile/storefront inside the CAIT app community feature.

**Status:** Has existing data — read before writing.

**Column Schema:** Same as 50 Million List (A through J)

**Additional requirements:** Must sell a product/course. Email required (run full enrichment). Note product/course name in Notes column.

**Notes column format for this tab:**
`[Credential] | [Product/Course name] | [Tier] | [Partnership angle]`
Example: `BCBA | Parent ABA Bootcamp course | Tier 2 | ABA tracking angle`

---

## Tab: Foundations & Organizations

**Purpose:** Medical parent foundations, advocacy orgs, and trusted community hubs on Instagram. Used by Mikha (Partnership Lead) for IG DM outreach — inviting orgs to establish a dedicated space inside CAIT.

**Status:** Active — 28 rows as of 2026-03-19. Read before writing.

**Outreach context:** Mikha DMs these orgs directly on IG. Pitch = CAIT is like ChatGPT built for their community, 230K waitlist, invite to establish a space inside the app. Notes column has the personalized hook line per org.

**Column Schema:**

| Column | Field | Notes |
|--------|-------|-------|
| A | Org Name | Full official org name |
| B | IG Handle | @handle format |
| C | Profile Link | https://instagram.com/handle |
| D | Website | Org website |
| E | Diagnosis Focus | e.g. "Down syndrome", "Epilepsy", "NICU / Premature birth" |
| F | Followers | Raw integer |
| G | Email | Blank — not needed, contact via IG DM |
| H | Email Source | Blank |
| I | Exec Contact Name | If found during research |
| J | Exec Contact Title | e.g. "Executive Director" |
| K | Notes | Personalized hook for Mikha's DM — what community trust this org has built |

**Qualification rules (different from individual accounts):**
- Public account, 1,000+ followers, active within 90 days
- No gender filter, no engagement floor
- USA-based org

**Run command:**
```bash
python scripts/run_discovery.py --category instagram_foundations --batch-size 20
```

---

## Tab: US ADHD Facebook Group Communities

**Status: SKIP ENTIRELY. DO NOT READ. DO NOT WRITE. DO NOT TOUCH.**

---

## Tab: US Autism Facebook Group Communities

**Purpose:** USA-based Facebook groups for autism families — admin contact info for outreach.

**Status:** Has existing data — read before writing. Add 5 new unique entries.

**Column Schema:**

| Column | Field | Notes |
|--------|-------|-------|
| A | Community Name | Full group name as it appears on Facebook |
| B | Group Link | Full Facebook group URL |
| C | Number of Members | Member count at time of research |
| D | Admin | Admin name and/or contact info if found |

---

## Tab: US Facebook Medical Moms

**Purpose:** USA-based Facebook groups for medical moms (diagnosis-agnostic or medically complex).

**Status:** Has existing data — read before writing. Add 5 new unique entries.

**Column Schema:** Same as Facebook tabs (Community Name | Group Link | Number of Members | Admin)

---

## Tab: Philippines Facebook Groups

**Purpose:** Philippines-based Facebook groups and pages for caregiving parents across all CAIT diagnosis categories. Used by Mikha for DM outreach when expanding to Philippines market.

**Status:** Active — 25 rows as of 2026-03-19. Read before writing.

**Column Schema:** Same as Facebook tabs (Community Name | Group Link | Number of Members | Admin)

**Notes:**
- Many entries are Facebook Pages (not Groups) — member counts shown as "X (page likes)" where group member count was not publicly available
- Philippines signal confirmed via group/page name containing: Philippines, Pilipinas, Filipino, Pinay, Manila, Cebu, Davao, etc.
- "Verify on FB" in Number of Members means count was not surfaced by web search — verify directly before outreach

**Run command:**
```bash
python scripts/run_discovery.py --category facebook_philippines --batch-size 25
```

---

## Tab: US Reddit Medical Moms

**Purpose:** Reddit communities for medical parenting — general medically complex.

**Status:** Empty — add 5 new entries.

**Column Schema:** Same as community tabs (Community Name | Group Link | Number of Members | Admin)

**Notes for Reddit:** Community Name = subreddit name (e.g., "r/MedicalParents"). Group Link = full URL. Number of Members = subscriber count. Admin = mod usernames (comma-separated if multiple).

---

## Tab: US Autism Reddit Group Communities

**Purpose:** Reddit communities specifically for autism families.

**Status:** Empty — add 5 new entries.

**Column Schema:** Same as community tabs.

---

## Deduplication Rules

**Read order for dedup (every run, before any write):**
1. 50 Million List
2. CAIT Community
3. US Autism Facebook Group Communities
4. US Facebook Medical Moms
5. Philippines Facebook Groups
6. US Reddit Medical Moms
7. US Autism Reddit Group Communities

**Skip:** US ADHD Facebook Group Communities (do not read)

**What constitutes a duplicate:**
- Same Instagram username (case-insensitive)
- Same profile URL
- Same Facebook group URL
- Same subreddit URL or name
- Same group/community name (fuzzy match — "Autism Moms USA" and "Autism Moms - USA" are duplicates)

---

## Write Rules

1. Always append to the end of existing data — never overwrite
2. Do not write a header row — headers already exist in row 1
3. Write rows in the same column order as the schema above
4. Leave Email and Email Source blank for community tabs (Facebook/Reddit)
5. If Google Sheets API fails, write to `outputs/TAB-NAME-YYYY-MM-DD.csv` as fallback
6. Log every write in `memory/YYYY-MM-DD.md` — what was added, to which tab, from which source
