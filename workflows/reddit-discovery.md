# Workflow: Reddit Community Discovery

## Objective
Find active Reddit communities for medical parenting and autism caregiving, collect community and mod info, and write qualified entries to the correct tab.

## When to Run
On demand. Run per target tab:
- `reddit_medical_moms` → writes to "US Reddit Medical Moms"
- `reddit_autism` → writes to "US Autism Reddit Group Communities"

## Required Inputs
- Category flag: `reddit_medical_moms` or `reddit_autism`
- Batch size (default: 5)
- Reddit API credentials in `.env`
- Google Sheets credentials in `.env`

## Steps

### Step 1 — Load the Dedup Set
Run: `scripts/read_sheet.py`
Returns master set of all known community names and URLs.

### Step 2 — Run Reddit Subreddit Search
Run: `scripts/reddit_discovery.py --category [category]`

**Search terms by category:**

For `reddit_medical_moms`:
- "medical parents"
- "medically complex"
- "special needs parents"
- "medical moms"
- "rare disease parents"
- "medically fragile"
- "pediatric hospital"
- "NICU parents"

For `reddit_autism`:
- "autism parenting"
- "autism parents"
- "ASD parenting"
- "autistic child"
- "autism moms"
- "autism support"
- "ABA parents"
- "autism families"

Also check these specific subreddits directly for `reddit_autism`:
- r/Autism_Parenting
- r/autism (check if parent-friendly)
- r/ABA
- r/AspergerParents
- r/specialeducation

Also check these for `reddit_medical_moms`:
- r/MedicalParents (check if exists)
- r/specialneedskids
- r/rarediseases
- r/NICU
- r/CysticFibrosis (parent community)
- r/Epilepsy
- r/DownSyndrome
- r/type1diabetes

### Step 3 — Qualify Each Subreddit
For each subreddit found:

Apply filters from `knowledge/qualification-standards.md` — Reddit section:
- 1,000+ subscribers (hard floor)
- Active (posts within last 7 days)
- Relevant to caregiving parents (not just the condition generally — look for parent/family focus)
- Has active moderators

**How to check relevance:**
- Read subreddit description and rules
- Check top 5 recent posts — are they from parents/caregivers?
- Check flair options if available — parent-focused flairs are a signal

### Step 4 — Collect Mod Info
For each qualified subreddit:
- List up to 3 mod usernames from sidebar
- Format: "u/modname1, u/modname2"
- Note if community has a Discord or external website listed in sidebar

### Step 5 — Dedup Check
Before writing:
- Normalize subreddit name (lowercase, remove r/)
- Check against dedup set (subreddit name and URL)
- Skip if found in any tab

### Step 6 — Build Sheet Rows
For each qualified subreddit:
- Community Name: `r/subredditname`
- Group Link: `https://reddit.com/r/subredditname`
- Number of Members: subscriber count
- Admin: mod usernames comma-separated

### Step 7 — Write to Sheet
Run: `scripts/write_sheet.py --tab [tab_name] --data [results]`
Stop at batch size (5). Append only.

### Step 8 — Log the Run
Write to `memory/YYYY-MM-DD.md`:
- Subreddits found vs. qualified vs. written
- Which search terms worked best
- Any subreddits that were good but fell below the member threshold (note for future)
- Related subreddits spotted in sidebars for future runs

## Expected Output
5 new rows in the target tab. CSV fallback in `outputs/` if Sheets fails.

## Error Handling

| Error | Response |
|-------|----------|
| Reddit API rate limited | Wait 60 seconds, retry. PRAW handles backoff automatically. |
| Subreddit private/banned | Skip, log as unavailable |
| Search returns no relevant results | Try next set of search terms |
| All found subreddits are duplicates | Log that category is saturated at current search depth. Suggest new terms. |

## Notes
- Reddit is the easiest platform to research — API is free, reliable, and doesn't block scrapers.
- Smaller subreddits (1K–5K members) can be extremely high quality if the community is active and specific.
- Look at the sidebar of each qualified subreddit — it often links to 2–3 related communities.
- Mod usernames are sufficient contact info for Reddit — note them in the Admin column.
- Some diagnosis-specific subreddits (e.g., r/CysticFibrosis, r/DownSyndrome) serve both patients and parents — include them if parent-focused posts are common.
