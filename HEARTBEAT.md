# HEARTBEAT.md — Scheduled Tasks

No automated heartbeat configured yet. All runs are on-demand until deployed to OpenClaw.

---

## Planned Heartbeat Schedule (Post-OpenClaw Deploy)

**Weekly (Monday, UTC+8):**
- Run `scripts/run_discovery.py` for each active category
- Batch size: Cherwin-approved target per category
- Write results to Google Sheet
- Update `memory/insights.md` with weekly synthesis

**Monthly:**
- Review all tabs for stale entries (accounts deactivated, groups deleted)
- Flag any entries with 0 engagement or dead links to Cherwin for removal
- Update `memory/insights.md` with pipeline health report
