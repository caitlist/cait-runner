"""
prep_daily_batch.py
--------------------
Pulls the next 100 uncontacted accounts from "Medical Mom DM Outreach" sheet
and writes Mikha's daily send list.

No scraping. No Apify credits. Reads existing sheet rows only.

Usage:
    python -X utf8 scripts/prep_daily_batch.py
    python -X utf8 scripts/prep_daily_batch.py --limit 60
    python -X utf8 scripts/prep_daily_batch.py --dry-run
"""

import os
import sys
import datetime
import argparse

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
CREDS_PATH = os.environ.get("GOOGLE_CREDS_PATH")
DM_SHEET_TAB = "Medical Mom DM Outreach"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

DM_TEMPLATE = """Hi {name}

We came across your page and just wanted to say how much we admire everything you're managing, it's a lot.

We've been building something with our medical parent community from day one that helps take things out of your head — like tracking symptoms, medications, and everything going on day-to-day, without needing to remember it all.

It has a similar intelligence to ChatGPT, but feels much more personal and built for real family life.

Many medical parents have told us it's been a game changer for them and something they wish they had much earlier.

We're opening early access to a small group before launch — if it feels like it could help at all, we'd be happy to share it with you

We also offer a small honorarium as a thank you for your time all we ask is for your honest feedback to see how this could help you each day.

If you're open, we'd be happy to share more details

Mikha
Brand Partnership Lead
caitconnect.com"""


def open_sheet():
    creds = Credentials.from_service_account_file(
        CREDS_PATH,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID).worksheet(DM_SHEET_TAB)


def get_uncontacted_rows(ws) -> list[dict]:
    """
    Return all rows where DM Status is blank, in original row order.
    Columns: Date | Handle | IG Profile Link | Category | Source Hashtag |
             Display Name | Name Used | DM Status | Notes | Quality (optional)
    """
    all_values = ws.get_all_values()
    if not all_values:
        return []

    headers = [h.strip() for h in all_values[0]]

    # Map column indices
    col = {h: i for i, h in enumerate(headers)}

    # Required columns
    for required in ("Handle", "IG Profile Link", "DM Status", "Name Used", "Category"):
        if required not in col:
            print(f"[ERROR] Column '{required}' not found in sheet. Headers: {headers}")
            sys.exit(1)

    rows = []
    for row in all_values[1:]:  # skip header
        # Pad short rows
        while len(row) < len(headers):
            row.append("")

        dm_status = row[col["DM Status"]].strip()
        if dm_status:
            continue  # already sent or marked

        handle = row[col["Handle"]].strip().lstrip("@")
        if not handle:
            continue

        rows.append({
            "handle": handle,
            "profile_link": row[col["IG Profile Link"]].strip(),
            "category": row[col.get("Category", -1)].strip() if col.get("Category") is not None else "",
            "name_used": row[col["Name Used"]].strip() or "there",
            "quality": row[col["Quality"]].strip() if "Quality" in col else "",
        })

    return rows


def format_dm_entry(handle: str, profile_link: str, category: str, name: str, quality: str) -> str:
    dm_text = DM_TEMPLATE.format(name=name)
    quality_line = f"Quality: {quality}\n" if quality else ""
    return f"""## @{handle} — {category}
Profile: {profile_link}
Name used: {name}
{quality_line}
---
{dm_text}
---

"""


def write_dm_output(accounts: list[dict], date_str: str, dry_run: bool = False) -> str:
    output_path = os.path.join(OUTPUTS_DIR, f"daily_dm_{date_str}.md")
    lines = [
        f"# CAIT Daily DM List — {date_str}",
        f"Total accounts: {len(accounts)}",
        "",
        "> Send each DM manually via Instagram. Space them out — do NOT send many in quick succession.",
        "",
        "---",
        "",
    ]
    for acc in accounts:
        lines.append(format_dm_entry(
            handle=acc["handle"],
            profile_link=acc["profile_link"],
            category=acc["category"],
            name=acc["name_used"],
            quality=acc["quality"],
        ))

    content = "\n".join(lines)
    if not dry_run:
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Prep Mikha's daily DM batch from existing sheet")
    parser.add_argument("--limit", type=int, default=100, help="Accounts per day (default 100)")
    parser.add_argument("--dry-run", action="store_true", help="Preview only — no file written")
    args = parser.parse_args()

    today = datetime.date.today().isoformat()

    print(f"\n{'='*60}")
    print(f"  CAIT Daily Batch Prep — {today}")
    print(f"{'='*60}\n")

    if not SHEET_ID or not CREDS_PATH:
        print("ERROR: GOOGLE_SHEET_ID or GOOGLE_CREDS_PATH not set in .env")
        sys.exit(1)

    print(f"Reading '{DM_SHEET_TAB}' sheet...")
    ws = open_sheet()
    uncontacted = get_uncontacted_rows(ws)

    print(f"Uncontacted accounts in sheet: {len(uncontacted)}")

    if not uncontacted:
        print("No uncontacted accounts remaining — time to scrape more!")
        return

    batch = uncontacted[:args.limit]
    print(f"Selecting top {len(batch)} for today's batch\n")

    # Show quality breakdown if Quality column is populated
    quality_counts = {}
    for acc in batch:
        q = acc["quality"] or "Unverified"
        quality_counts[q] = quality_counts.get(q, 0) + 1
    if any(acc["quality"] for acc in batch):
        print("Quality breakdown in today's batch:")
        for label, count in sorted(quality_counts.items()):
            print(f"  {label}: {count}")
        print()

    output_path = write_dm_output(batch, today, dry_run=args.dry_run)

    if args.dry_run:
        print(f"[Dry run] Would write: {output_path}")
    else:
        print(f"[Output] Written: {output_path}")

    print(f"\n{'='*60}")
    print(f"  Batch ready: {len(batch)} accounts")
    print(f"  Remaining after today: {len(uncontacted) - len(batch)}")
    print(f"  Days of runway at {args.limit}/day: {(len(uncontacted) - len(batch)) // args.limit}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
