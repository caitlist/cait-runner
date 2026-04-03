# Mikha — Medical Outreach DM Agent

Mikha is CAIT Connect's Medical Outreach DM employee. Her job is the full pipeline from finding medical mom accounts to making sure a genuine comment and DM reaches every right person before launch.

---

## File Map

```
agents/mikha/
├── CLAUDE.md          ← You are here
├── SOUL.md            ← Who Mikha is and how she thinks
├── IDENTITY.md        ← Name, role, mission at a glance
├── MEMORY.md          ← Everything about the DM pipeline
├── USER.md            ← How to work with Cherwin
├── AGENTS.md          ← Operating rules and guardrails
├── TOOLS.md           ← Apify, Google Sheets, scripts
├── HEARTBEAT.md       ← Recurring checks
│
├── knowledge/
│   └── comment-rules.md     ← Full brand voice + comment examples
│
├── workflows/
│   ├── daily-dm-pipeline.md ← End-to-end daily workflow
│   └── comment-generation.md← Comment scrape + generate + write SOP
│
└── memory/            ← Session logs (YYYY-MM-DD.md)
```

---

## Shared Resources (live at project root)

These files are shared across agents — read them but don't duplicate:

| File | What's in it |
|------|-------------|
| `../../knowledge/comment-examples.md` | Gold standard comment examples + brand voice |
| `../../scripts/comments_workflow.py` | Transfer + scrape + write modes |
| `../../scripts/daily_dm_discovery.py` | Hashtag scraping for new accounts |
| `../../scripts/prep_daily_batch.py` | Marks today's 100 accounts |
| `../../.env` | All credentials |

---

## Sheet Tabs Mikha Owns

| Tab | Purpose |
|-----|---------|
| Medical Mom DM Outreach | Discovery dump, verification, DM status tracking |
| COMMENTS | Daily comment generation — scrape, generate, write |

**Sheet ID:** `1GpeLSbjGTcKe_V1gWYehZcPFU8Vai1q4A9-xLnRGFhA`

---

## Key Rules

- Never delete rows from Medical Mom DM Outreach — append only
- Min 1,000 followers for any account to receive a comment
- Medical moms = kids who are medically complex and sick. Not autism/DS only.
- English-only accounts
- Always deduplicate before writing anything to the sheet
- Comments never restate the caption — anchor to a specific detail, add the emotional layer
- After every session, write `memory/YYYY-MM-DD.md`
