"""
reenrich_empty_emails.py
-------------------------
Reads the CAIT Community tab, finds all rows with empty email,
re-runs enrichment (now with Apollo), and updates those cells in place.

Usage:
    python scripts/reenrich_empty_emails.py
"""

import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

from scripts.enrich_email import enrich_email

load_dotenv()

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
CREDS_PATH = os.environ.get("GOOGLE_CREDS_PATH")
TAB_NAME = "CAIT Community"

# Actual column layout of the CAIT Community tab (1-based):
# 1: IG Handle, 2: Category, 3: Followers, 4: Avg Comments,
# 5: Email, 6: Website, 7: Products / Courses, 8: Priority Tier, 9: Notes
COL_HANDLE   = 1
COL_EMAIL    = 5
COL_WEBSITE  = 6


def get_client():
    creds = Credentials.from_service_account_file(
        CREDS_PATH,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return gspread.authorize(creds)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--empty-only", action="store_true",
                        help="Only re-enrich rows with no email (default: enrich ALL rows)")
    args = parser.parse_args()

    mode = "empty rows only" if args.empty_only else "ALL rows"
    print(f"=== Re-enriching emails in CAIT Community ({mode}) ===\n")

    client = get_client()
    sheet = client.open_by_key(SHEET_ID)
    ws = sheet.worksheet(TAB_NAME)

    all_rows = ws.get_all_values()
    header = all_rows[0] if all_rows else []
    data_rows = all_rows[1:]  # skip header

    print(f"Total rows (excl. header): {len(data_rows)}")

    updated = 0
    skipped = 0

    for i, row in enumerate(data_rows, start=2):  # start=2 because row 1 is header
        # Pad short rows
        while len(row) < 10:
            row.append("")

        handle  = row[COL_HANDLE - 1].strip().lstrip("@")
        email   = row[COL_EMAIL - 1].strip()
        website = row[COL_WEBSITE - 1].strip()

        if not handle:
            continue

        # Skip rows that already have an email if --empty-only flag is set
        if args.empty_only and email:
            skipped += 1
            continue

        # Use the handle as a name proxy for LinkedIn name search
        # (works well for public figures: melrobbins, nedratawwab, hubermanlab, etc.)
        name_proxy = handle.replace("_", " ").replace(".", " ").strip()

        print(f"[row {i}] @{handle} | current email: '{email or 'empty'}'")

        result = enrich_email(
            username=handle,
            bio="",
            website=website,
            full_name=name_proxy,
        )

        found = result["email"]

        if not found:
            print(f"  Not found")
        elif found == email:
            print(f"  Same as existing: {found} — no change")
            skipped += 1
        else:
            if email and email != found:
                combined = f"{found} | was: {email}"
                ws.update_cell(i, COL_EMAIL, combined)
                print(f"  Updated via {result['email_source']}: {found}  (replaced: {email})")
            else:
                ws.update_cell(i, COL_EMAIL, found)
                print(f"  Found via {result['email_source']}: {found}")
            updated += 1
            time.sleep(1)

        time.sleep(0.5)

    print(f"\n=== Done ===")
    print(f"Updated: {updated} | Unchanged/skipped: {skipped}")
