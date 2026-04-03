"""
write_sheet.py
--------------
Writes qualified entries to the correct CAIT Google Sheet tab.
Always performs a fresh dedup check before writing.

Usage:
    from scripts.write_sheet import write_rows
    write_rows(tab_name="US Reddit Medical Moms", rows=[...])
"""

import os
import csv
import time
import datetime

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

from scripts.read_sheet import get_dedup_set, is_duplicate, SKIP_TABS

load_dotenv()

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
CREDS_PATH = os.environ.get("GOOGLE_CREDS_PATH")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

# Map tab names to their column schemas
# "instagram" schema: Username | Profile Link | Followers | Avg Comments | Avg Likes | Email | Email Source | Website | Category | Notes
# "community" schema: Community Name | Group Link | Number of Members | Admin

TAB_SCHEMAS = {
    "50 Million List": "instagram",
    "CAIT Community": "instagram",
    "US autism Facebook Group Communities": "community",
    "US Facebook Medical Moms": "community",
    "US Reddit Medical Moms": "community",
    "US autism Reddit Group Communities": "community",
    "Foundations & Organizations": "foundations",
    "Philippines Facebook Groups": "community",
}


def get_client():
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    return gspread.authorize(creds)


def write_rows(tab_name: str, rows: list[dict], batch_size: int = 5) -> dict:
    """
    Write rows to the specified tab after dedup check.

    Each row for instagram tabs should be a dict:
        {username, profile_link, followers, avg_comments, avg_likes,
         email, email_source, website, category, notes}

    Each row for community tabs should be a dict:
        {community_name, group_link, num_members, admin}

    Returns: {written: int, skipped_duplicates: int, errors: int}
    """
    if tab_name in SKIP_TABS:
        raise ValueError(f"Tab '{tab_name}' is permanently off-limits. Do not write to ADHD tab.")

    if tab_name not in TAB_SCHEMAS:
        raise ValueError(f"Unknown tab name: '{tab_name}'. Check sheet-structure.md for valid tab names.")

    schema = TAB_SCHEMAS[tab_name]

    # Fresh dedup set every time
    print(f"[write_sheet] Loading dedup set...")
    known = get_dedup_set()
    print(f"[write_sheet] Dedup set loaded: {len(known)} known identifiers")

    client = get_client()
    sheet = client.open_by_key(SHEET_ID)

    # Auto-create tab if it doesn't exist (foundations tab on first run)
    existing_tabs = [ws.title for ws in sheet.worksheets()]
    if tab_name not in existing_tabs:
        print(f"[write_sheet] Tab '{tab_name}' not found — creating it...")
        sheet.add_worksheet(title=tab_name, rows=200, cols=12)
        ws = sheet.worksheet(tab_name)
        if schema == "foundations":
            ws.append_row(
                ["Org Name", "IG Handle", "Profile Link", "Website",
                 "Diagnosis Focus", "Followers", "Email", "Email Source",
                 "Exec Contact Name", "Exec Contact Title", "Notes"],
                value_input_option="USER_ENTERED"
            )
        elif schema == "community":
            ws.append_row(
                ["Community Name", "Group Link", "Number of Members", "Admin"],
                value_input_option="USER_ENTERED"
            )
        print(f"[write_sheet] Tab '{tab_name}' created.")

    worksheet = sheet.worksheet(tab_name)

    written = 0
    skipped = 0
    errors = 0
    csv_fallback_rows = []

    for row in rows:
        if written >= batch_size:
            break

        try:
            if schema == "instagram":
                identifier = row.get("username", "").lower().strip().lstrip("@")
                link = row.get("profile_link", "") or f"https://instagram.com/{identifier}"
                if is_duplicate(identifier, known) or is_duplicate(link, known):
                    print(f"[write_sheet] DUPLICATE skipped: {identifier}")
                    skipped += 1
                    continue

                # Determine priority tier label
                avg_comments = row.get("avg_comments", 0)
                if avg_comments >= 100:
                    priority_tier = "1 — High Priority"
                elif avg_comments >= 30:
                    priority_tier = "1"
                else:
                    priority_tier = "2"

                sheet_row = [
                    f"@{identifier}",
                    row.get("full_name", ""),
                    row.get("category", ""),
                    str(row.get("followers", "")),
                    str(avg_comments),
                    row.get("email", ""),
                    row.get("website", ""),
                    row.get("products", ""),
                    priority_tier,
                    row.get("notes", ""),
                ]

            elif schema == "community":
                community_name = row.get("community_name", "").strip()
                group_link = row.get("group_link", "").strip()
                if is_duplicate(community_name, known) or is_duplicate(group_link, known):
                    print(f"[write_sheet] DUPLICATE skipped: {community_name}")
                    skipped += 1
                    continue

                sheet_row = [
                    community_name,
                    group_link,
                    str(row.get("num_members", "")),
                    row.get("admin", ""),
                ]

            elif schema == "foundations":
                identifier = row.get("username", "").lower().strip().lstrip("@")
                link = f"https://instagram.com/{identifier}"
                if is_duplicate(identifier, known) or is_duplicate(link, known):
                    print(f"[write_sheet] DUPLICATE skipped: {identifier}")
                    skipped += 1
                    continue

                sheet_row = [
                    row.get("org_name", ""),
                    f"@{identifier}",
                    link,
                    row.get("website", ""),
                    row.get("diagnosis", ""),
                    str(row.get("followers", "")),
                    row.get("email", ""),
                    row.get("email_source", ""),
                    row.get("exec_contact_name", ""),
                    row.get("exec_contact_title", ""),
                    row.get("notes", ""),
                ]

            worksheet.append_row(sheet_row, value_input_option="USER_ENTERED")
            # Update local known set to prevent same-run duplicates
            if schema == "instagram":
                known.add(identifier)
                known.add(link.lower())
            elif schema == "foundations":
                known.add(identifier)
                known.add(link.lower())
            else:
                known.add(community_name.lower())
                known.add(group_link.lower())

            written += 1
            print(f"[write_sheet] Written ({written}/{batch_size}): {sheet_row[0]}")
            time.sleep(1)  # Rate limit courtesy

            csv_fallback_rows.append(sheet_row)

        except gspread.exceptions.APIError as e:
            if "429" in str(e):
                print("[write_sheet] Rate limited. Waiting 60 seconds...")
                time.sleep(60)
                try:
                    worksheet.append_row(sheet_row, value_input_option="USER_ENTERED")
                    written += 1
                except Exception as retry_err:
                    print(f"[write_sheet] Retry failed: {retry_err}")
                    _write_csv_fallback(tab_name, [sheet_row], schema)
                    errors += 1
            else:
                print(f"[write_sheet] API error: {e}")
                _write_csv_fallback(tab_name, [sheet_row], schema)
                errors += 1

        except Exception as e:
            print(f"[write_sheet] Unexpected error: {e}")
            _write_csv_fallback(tab_name, [sheet_row], schema)
            errors += 1

    print(f"\n[write_sheet] Done. Written: {written} | Skipped (duplicates): {skipped} | Errors: {errors}")
    return {"written": written, "skipped_duplicates": skipped, "errors": errors}


def _write_csv_fallback(tab_name: str, rows: list, schema: str):
    """Write rows to CSV in outputs/ when Sheets API fails."""
    os.makedirs("outputs", exist_ok=True)
    date_str = datetime.date.today().isoformat()
    safe_tab = tab_name.replace(" ", "-").replace("/", "-")
    path = f"outputs/{safe_tab}-{date_str}.csv"

    if schema == "instagram":
        headers = ["IG Handle", "Full Name", "Category", "Followers",
                   "Avg Comments", "Email", "Website", "Products / Courses",
                   "Priority Tier", "Notes"]
    elif schema == "foundations":
        headers = ["Org Name", "IG Handle", "Profile Link", "Website",
                   "Diagnosis Focus", "Followers", "Email", "Email Source",
                   "Exec Contact Name", "Exec Contact Title", "Notes"]
    else:
        headers = ["Community Name", "Group Link", "Number of Members", "Admin"]

    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerows(rows)

    print(f"[write_sheet] CSV fallback written to: {path}")
