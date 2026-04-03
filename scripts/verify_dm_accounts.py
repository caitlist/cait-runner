"""
verify_dm_accounts.py
----------------------
Scrapes Instagram profile bios for accounts in the "Medical Mom DM Outreach" sheet
and labels each one — NO accounts are removed or excluded.

Labels written to a "Quality" column:
  Medical Mom ✓    — bio/posts clearly mention caring for a sick child
  Medical Parent   — some medical family signals, less specific
  Clinic/Org       — looks like a business, practice, or organization
  Personal         — regular person account, no medical parenting signals
  Unclear          — not enough profile data to classify

Mikha and Cherwin decide what to do with each label. Nothing is deleted.

Usage:
    # Verify unverified accounts in batches of 50 (default)
    python -X utf8 scripts/verify_dm_accounts.py

    # Verify a specific number
    python -X utf8 scripts/verify_dm_accounts.py --limit 100

    # Dry run — scrape and classify but don't update sheet
    python -X utf8 scripts/verify_dm_accounts.py --dry-run
"""

import os
import re
import sys
import time
import datetime
import argparse

import gspread
from google.oauth2.service_account import Credentials
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
CREDS_PATH = os.environ.get("GOOGLE_CREDS_PATH")
DM_SHEET_TAB = "Medical Mom DM Outreach"

PROFILE_ACTOR = "apify/instagram-scraper"

# ── Classification keywords ───────────────────────────────────────────────────

# Strong signals that this is a family caring for a medically complex child
MEDICAL_MOM_SIGNALS = [
    # Specific conditions
    "epilepsy", "seizure", "dravet", "chd", "heart defect", "congenital heart",
    "nicu", "preemie", "premature", "micro preemie", "micropreemie",
    "gtube", "g-tube", "feeding tube", "ng tube", "ngtube",
    "trach", "tracheostomy", "ventilator",
    "cancer", "leukemia", "tumor", "oncology",
    "cystic fibrosis", " cf ", "cfkid",
    "type 1", "t1d", "t1 diabetes", "juvenile diabetes",
    "rare disease", "rare condition", "rare diagnosis",
    "cerebral palsy", " cp mom", "cpmom",
    "spina bifida", "sbmom", "sb mom",
    "hydrocephalus",
    "medically complex", "medical complexity",
    "medical mom", "medical mama", "medmom",
    "hospital mom", "icu mom", "picu", "hospital life",
    "warrior kid", "warrior baby", "fighter",
    "down syndrome", "trisomy",
    "chromosome", "genetic disorder",
    "rare syndrome",
    # General medical parenting
    "my son has", "my daughter has", "our son has", "our daughter has",
    "fighting for my", "advocating for my",
    "infusion", "port access", "medication schedule",
    "pediatric", "children's hospital", "childrens hospital",
    "special needs mom", "special needs mama",
    "medkids", "medical family",
]

# Signals pointing to a business, practice, or organization
ORG_SIGNALS = [
    "clinic", "therapy center", "therapy clinic",
    "bcba", "board certified", "aba therapy",
    "occupational therapist", " ot ", "speech therapist", " slp ",
    "physical therapist", " pt ",
    "llc", "inc.", " llp ", "practice",
    "services", "we provide", "we offer", "our team",
    "foundation", "nonprofit", "non-profit", "501c",
    "organization", "association",
    "consulting", "consultant",
    "certified coach", "health coach",
    "telehealth", "telemedicine",
]


def classify_profile(bio: str, posts: list) -> str:
    """
    Label an account based on bio + recent post captions.
    Returns one of: Medical Mom ✓ | Medical Parent | Clinic/Org | Personal | Unclear
    """
    bio_lower = (bio or "").lower()

    # Get text from up to 5 recent posts
    post_text = " ".join(
        (p.get("caption") or "") for p in (posts or [])[:5]
    ).lower()

    combined = bio_lower + " " + post_text

    # Score each category
    medical_hits = [s for s in MEDICAL_MOM_SIGNALS if s in combined]
    org_hits = [s for s in ORG_SIGNALS if s in combined]

    medical_score = len(medical_hits)
    org_score = len(org_hits)

    if medical_score >= 3:
        return "Medical Mom ✓"
    elif medical_score >= 1 and org_score == 0:
        return "Medical Parent"
    elif medical_score >= 1 and org_score >= 1:
        # Both signals — could be a medical mom who also runs a small service
        return "Medical Parent"
    elif org_score >= 2:
        return "Clinic/Org"
    elif org_score == 1:
        return "Org Signal"
    elif not bio_lower.strip() and not post_text.strip():
        return "Unclear"
    else:
        return "Personal"


# ── Google Sheets ─────────────────────────────────────────────────────────────

def open_sheet():
    creds = Credentials.from_service_account_file(
        CREDS_PATH,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID).worksheet(DM_SHEET_TAB)


def ensure_quality_column(ws) -> tuple[list, int]:
    """
    Ensure 'Quality' column exists in the sheet.
    Returns (headers, quality_col_index_1based).
    """
    headers = ws.row_values(1)
    headers_stripped = [h.strip() for h in headers]

    if "Quality" not in headers_stripped:
        # Append Quality header to row 1
        quality_col = len(headers) + 1
        ws.update_cell(1, quality_col, "Quality")
        headers_stripped.append("Quality")
        print(f"[Sheets] Added 'Quality' column at position {quality_col}")
    else:
        quality_col = headers_stripped.index("Quality") + 1  # 1-based

    return headers_stripped, quality_col


def get_unverified_rows(ws, headers: list, quality_col: int, limit: int) -> list[dict]:
    """
    Return rows that have no Quality value yet, up to `limit`.
    Each returned dict includes: row_number (1-based), handle.
    """
    all_values = ws.get_all_values()
    col = {h.strip(): i for i, h in enumerate(headers)}

    handle_idx = col.get("Handle")
    if handle_idx is None:
        print("[ERROR] 'Handle' column not found")
        sys.exit(1)

    quality_idx = quality_col - 1  # 0-based

    results = []
    for row_num, row in enumerate(all_values[1:], start=2):  # row 1 = headers
        while len(row) < len(headers):
            row.append("")
        while len(row) < quality_col:
            row.append("")

        quality_val = row[quality_idx].strip() if quality_idx < len(row) else ""
        if quality_val:
            continue  # already verified

        handle = row[handle_idx].strip().lstrip("@")
        if not handle:
            continue

        results.append({"row": row_num, "handle": handle})
        if len(results) >= limit:
            break

    return results


# ── Apify ─────────────────────────────────────────────────────────────────────

def scrape_profiles_batch(handles: list[str]) -> dict[str, dict]:
    """
    Scrape up to 10 Instagram profiles per Apify call.
    Returns {handle: profile_dict}.
    """
    client = ApifyClient(APIFY_TOKEN)
    results = {}

    for i in range(0, len(handles), 10):
        batch = handles[i:i + 10]
        clean = [h.lstrip("@").lower().strip() for h in batch]
        print(f"  [Apify] Batch {i // 10 + 1}: {clean}")
        try:
            run = client.actor(PROFILE_ACTOR).call(run_input={
                "directUrls": [f"https://www.instagram.com/{u}/" for u in clean],
                "resultsType": "details",
                "resultsLimit": 6,
                "proxy": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"],
                },
            })
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            for item in items:
                username = (item.get("username") or "").lower().strip()
                if username:
                    results[username] = item
            print(f"    -> {len(items)} profiles returned")
            time.sleep(3)
        except Exception as e:
            print(f"  [Apify] Error on batch {i}: {e}")

    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Verify DM outreach accounts — labels only, nothing excluded")
    parser.add_argument("--limit", type=int, default=50, help="How many unverified accounts to process this run (default 50)")
    parser.add_argument("--dry-run", action="store_true", help="Classify but don't update sheet")
    args = parser.parse_args()

    if not APIFY_TOKEN:
        print("ERROR: APIFY_TOKEN not set in .env")
        sys.exit(1)
    if not SHEET_ID or not CREDS_PATH:
        print("ERROR: GOOGLE_SHEET_ID or GOOGLE_CREDS_PATH not set in .env")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  CAIT DM Account Verification")
    print(f"  Processing up to {args.limit} accounts")
    print(f"  Labels only — nothing removed or excluded")
    print(f"{'='*60}\n")

    ws = open_sheet()
    headers, quality_col = ensure_quality_column(ws)

    unverified = get_unverified_rows(ws, headers, quality_col, limit=args.limit)
    print(f"Found {len(unverified)} unverified accounts (processing {len(unverified)})\n")

    if not unverified:
        print("All accounts already verified.")
        return

    handles = [r["handle"] for r in unverified]
    print(f"Scraping {len(handles)} profiles via Apify...")
    profiles = scrape_profiles_batch(handles)

    # Classify and collect results
    label_counts = {}
    updates = []  # (row_num, label)

    for row_info in unverified:
        handle = row_info["handle"]
        profile = profiles.get(handle.lower(), {})

        bio = profile.get("biography") or profile.get("bio") or ""
        posts = profile.get("latestPosts") or profile.get("posts") or []
        is_private = profile.get("isPrivate", False)

        if not profile:
            label = "Unclear"
        elif is_private:
            label = "Private"
        else:
            label = classify_profile(bio, posts)

        label_counts[label] = label_counts.get(label, 0) + 1
        updates.append((row_info["row"], label))
        print(f"  @{handle:<30} → {label}")

    # Write to sheet in one batch
    if not args.dry_run and updates:
        print(f"\n[Sheets] Writing {len(updates)} Quality labels...")
        cell_updates = []
        for row_num, label in updates:
            cell_updates.append(gspread.Cell(row_num, quality_col, label))
        ws.update_cells(cell_updates, value_input_option="USER_ENTERED")
        print("[Sheets] Done.")
    elif args.dry_run:
        print("\n[Dry run] Sheet not updated.")

    print(f"\n{'='*60}")
    print(f"  Verification complete")
    print(f"  Accounts processed: {len(updates)}")
    print()
    for label, count in sorted(label_counts.items(), key=lambda x: -x[1]):
        print(f"    {label:<25} {count}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
