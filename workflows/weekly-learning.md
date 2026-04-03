# Workflow: Weekly Self-Learning & Memory Update

## Objective
Read the week's run logs, extract patterns and insights, and update memory so every future run benefits from what was learned.

## When to Run
Every Sunday, or after completing a full round of all 5 category discovery runs.

## Required Inputs
- All `memory/YYYY-MM-DD.md` files from the past 7 days
- Current `memory/insights.md`
- Current state of the Google Sheet (row counts per tab)

## Steps

### Step 1 — Read the Week's Run Logs
Read all daily memory files from the past 7 days.
Extract:
- Total accounts/groups found
- Total qualified
- Total written to sheet
- Duplicate rate (how many found were already in the sheet)
- Email find rate (for CAIT Community runs)
- Which search queries yielded the most qualifying results
- Which categories were most productive
- Which categories appeared saturated

### Step 2 — Pull Current Sheet Counts
Run: `scripts/read_sheet.py --count-only`
Get current row counts per tab to update the pipeline progress table in `MEMORY.md`.

### Step 3 — Identify Patterns

**Search query performance:**
- Which queries consistently return qualifying results?
- Which return noise (wrong geo, wrong gender, inactive accounts)?
- What new search terms emerged from bio/hashtag discovery?

**Category coverage:**
- Which diagnosis categories are well-covered?
- Which have almost no entries?
- Are there new niches that appeared in discovery (new hashtags, new diagnosis communities)?

**Enrichment patterns:**
- What email find rate for CAIT Community accounts?
- Which account types (BCBA, SLP, educator) have the best email findability?
- What websites tend to have visible emails vs. none?

**Duplicate patterns:**
- Are a lot of results already in the sheet? That signals a category is saturated at current search depth.
- Try different hashtags or search angles next week.

### Step 4 — Update memory/insights.md
Append a new dated section:

```markdown
## Week of YYYY-MM-DD

### What Worked
- [Search query or approach that yielded the best results]

### What Didn't Work
- [Queries that returned noise, categories that are saturated]

### New Discovery
- [New hashtags, niches, or account types discovered this week]

### Email Enrichment
- [Find rate this week, which methods worked]

### Pipeline Status
- [Updated counts, what gaps remain]

### Recommended Focus for Next Week
- [Top 2-3 priorities based on what the data shows]
```

### Step 5 — Update MEMORY.md Pipeline Table
Update the pipeline progress table with current row counts and last run date.

### Step 6 — Update diagnosis-categories.md (If New Hashtags Found)
If new diagnosis-specific hashtags were discovered in bios or posts this week, add them to the relevant category in `knowledge/diagnosis-categories.md`.

## Expected Output
- Updated `memory/insights.md` with new weekly section
- Updated pipeline table in `MEMORY.md`
- Any new hashtags added to `knowledge/diagnosis-categories.md`

## Notes
- This workflow makes the agent compoundingly smarter. Do not skip it.
- The insights.md file is the long-term brain — it should grow every week.
- If duplicate rate is above 60% for a category, that category needs new search angles before the next run.
