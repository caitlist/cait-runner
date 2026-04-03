---
name: qualify-account
description: Use when you need to manually evaluate whether an Instagram, Facebook group, or Reddit community meets CAIT's qualification standards. Pass an account handle, group name, or URL and get a pass/fail with reasoning. Also use when reviewing borderline cases that scripts flagged for human review.
---

## What This Skill Does

Applies CAIT's full qualification rubric to a single account or community and returns a clear pass/fail with tier assignment and a one-line rationale. Used for manual review and for borderline cases flagged in the Notes column.

## When to Use It

- Cherwin pastes a handle or group link and asks "does this qualify?"
- A script flagged an account as "gender unclear" or "borderline engagement"
- Reviewing a Tier 1 account before Cherwin decides to prioritize outreach
- Spot-checking entries already in the sheet

## Steps

### For Instagram Accounts

1. Check: Is this a female account?
   - Yes / No / Unclear → flag if unclear
2. Check: Is there a USA signal in bio, location, or content?
   - Yes / No
3. Check: Has this account posted in the last 30 days?
   - Yes / No
4. Check: What is the avg comment count across the last 3 posts?
   - Count real comments only (3+ words, not pure emoji)
   - Meets 15+ floor: Yes / No
5. Check: Is the audience caregiving parents? (not clinician-only)
   - Yes / No / Mixed
6. For CAIT Community: Does this account sell a product, course, or service?
   - Yes (describe it) / No

**Output:**
```
Result: PASS / FAIL / BORDERLINE
Tier: 1 / 2 / 3 / N/A
Reason: [one sentence]
Recommended action: [write to sheet / skip / flag for Cherwin]
Notes to add to sheet: [any relevant context]
```

### For Facebook Groups

1. Is this a USA group? (name, description, admin bio signals)
2. Member count 500+?
3. Active in last 7 days?
4. Topic matches a CAIT diagnosis category?

**Output:** PASS / FAIL + reason

### For Reddit Communities

1. 1,000+ subscribers?
2. Active (posts in last 7 days)?
3. Parent/caregiver-focused?
4. Relevant diagnosis or medical parenting topic?

**Output:** PASS / FAIL + reason

## Output

One of:
- **PASS** — ready to add to sheet (with tier and notes)
- **FAIL** — disqualified (with specific reason)
- **BORDERLINE** — meets most criteria but has a flag (with specific issue and recommendation)
