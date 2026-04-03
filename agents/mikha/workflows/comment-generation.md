# Workflow: Comment Generation

## Objective
Generate a genuine, brand-voice-compliant Instagram comment for every account in the COMMENTS tab that has a scraped caption but no generated comment yet.

## When to Run
After scrape mode completes. Triggered when Cherwin says "generate comments."

## Required Inputs
- `outputs/captions_for_comments.json` — produced by scrape mode
- `knowledge/comment-examples.md` — gold standard examples (read before generating)

---

## Steps

### Step 1 — Read the knowledge file
Always read `../../knowledge/comment-examples.md` before generating any comments. Do not rely on memory alone.

### Step 2 — Read captions JSON
Read `outputs/captions_for_comments.json`. Each entry contains:
```json
{
  "row": 5,
  "handle": "username",
  "ig_link": "https://instagram.com/username",
  "post_url": "https://instagram.com/p/abc123/",
  "caption": "...",
  "sensitive": false
}
```

### Step 3 — Generate comments in-session
For each entry, write a comment that:
- Anchors to ONE specific detail from the caption (name, number, event, phrase)
- Adds the emotional observation layer — what that detail MEANS, not what it says
- Ends with a varied DM nudge (rotate through approved list — never repeat back-to-back)
- Ends with 1 emoji (hearts preferred: ❤️ 🤍 🫶)
- Is 2–4 sentences max
- Contains no em dashes, no "I", no CAIT/product mention

For SENSITIVE entries:
- Still generate a comment
- Prefix with `[SENSITIVE — review before pasting]`
- Do NOT include a DM nudge
- Keep it warm, brief, human

### Step 4 — Write comments_to_write.json
Output format:
```json
[
  {
    "row": 5,
    "handle": "username",
    "comment": "The full comment text here. We left something in your DMs whenever you come up for air. ❤️",
    "notes": ""
  },
  {
    "row": 8,
    "handle": "sensitiveuser",
    "comment": "[SENSITIVE — review before pasting] Carrying both the weight and the love at the same time. 🤍",
    "notes": "[SENSITIVE]"
  }
]
```

### Step 5 — Write to sheet
```bash
python -X utf8 scripts/comments_workflow.py --mode write
```

---

## Expected Output
- Generated Comment column filled in COMMENTS tab
- Date column filled with timestamp
- SENSITIVE posts flagged in Notes column

## Quality Check Before Writing
- No comment sounds like a caption summary
- No two comments in the batch use the same DM nudge phrase
- No em dashes anywhere
- Every comment ends with exactly 1 emoji at the very end
- SENSITIVE posts have no DM nudge
