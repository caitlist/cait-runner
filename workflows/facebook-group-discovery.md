# Workflow: Facebook Group Discovery

## Objective
Find active, USA-based Facebook parent groups for a specified diagnosis category and write qualified entries to the correct sheet tab.

## When to Run
On demand. Run per category:
- `facebook_medical_moms` → writes to "US Facebook Medical Moms"
- `facebook_autism_groups` → writes to "US Autism Facebook Group Communities"

## Required Inputs
- Category flag: `facebook_medical_moms` or `facebook_autism_groups`
- Batch size (default: 5)
- Apify token in `.env`
- Google Sheets credentials in `.env`

## Steps

### Step 1 — Load the Dedup Set
Run: `scripts/read_sheet.py`
- Reads ALL non-ADHD tabs
- Returns master set of all known group names and URLs
- Nothing in this set gets written again — ever

### Step 2 — Run Apify Facebook Group Search
Run: `scripts/facebook_groups.py --category [category]`

**Search queries to try (in order, stop when 5 qualified results found):**

For `facebook_medical_moms`:
1. "medical moms USA"
2. "medically complex children parents USA"
3. "special needs medical moms"
4. "medical mom support group"
5. "medically fragile child parents"

For `facebook_autism_groups`:
1. "autism moms USA"
2. "autism parents United States"
3. "ASD parents support USA"
4. "autism families America"
5. "autism mom group"

**Actor:** `apify/facebook-groups-scraper`
**maxItems:** 50 per search (filter down to 5 qualified)

### Step 3 — Qualify Each Result
For each group returned by Apify:
- Check name contains no duplicate match from dedup set
- Confirm USA signal in name or description
- Member count 500+
- Activity signal present (recent posts visible)
- Topic matches the category

Apply all filters from `knowledge/qualification-standards.md` — Facebook Groups section.

### Step 4 — Collect Admin Info
For each qualified group:
- Note admin name from group "About" section
- If admin profile is visible, note any contact info
- Format: "Admin Name — contact if available"

### Step 5 — Dedup Check
Before writing each entry:
- Check group name (normalized: lowercase, strip punctuation) against dedup set
- Check group URL against dedup set
- If either matches — skip, log as duplicate

### Step 6 — Write to Sheet
Run: `scripts/write_sheet.py --tab [tab_name] --data [results]`
- Appends to end of existing data
- Writes exactly: Community Name | Group Link | Number of Members | Admin
- Stops at batch size (5 default)

### Step 7 — Log the Run
Write to `memory/YYYY-MM-DD.md`:
- How many groups found
- How many qualified
- How many were duplicates (and what they were)
- Which search queries yielded the best results
- Any new search terms to try next run

## Expected Output
5 new rows in the target tab. CSV fallback in `outputs/` if Sheets API fails.

## Error Handling

| Error | Response |
|-------|----------|
| Apify actor fails | Log error, try next search query. If all fail, write to memory and stop. |
| Google Sheets 429 (rate limit) | Wait 60 seconds, retry once. If still failing, write CSV to outputs/. |
| No qualified results after all queries | Log exhaustion in memory. Flag category as saturated or suggest new search terms. |
| Facebook blocks scrape | Log in memory. Try again next day. Do not retry immediately. |

## Notes
- Facebook group search via Apify can be inconsistent. If a run returns 0 results, try different search terms before assuming the category is saturated.
- Prefer groups with "support" or "community" in the name — these tend to be more active than "awareness" groups.
- Groups with 10,000+ members but no visible recent activity should be skipped — zombie groups.
- Admin contact is a nice-to-have, not a blocker. Write the entry even if admin info is unavailable.
