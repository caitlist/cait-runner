"""
read_sheet.py
-------------
Reads all non-ADHD tabs from the CAIT Google Sheet and returns a master
deduplication set. Run this before EVERY write operation.

Usage:
    from scripts.read_sheet import get_dedup_set, get_tab_counts
    known = get_dedup_set()

    # or from command line for a quick count check:
    python scripts/read_sheet.py
"""

import os
import re
import sys
import time

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
CREDS_PATH = os.environ.get("GOOGLE_CREDS_PATH")

# Tabs to skip entirely — never read, never write
SKIP_TABS = {"US ADHD Facebook Group Communities"}

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


def get_client():
    if not CREDS_PATH or not os.path.exists(CREDS_PATH):
        raise FileNotFoundError(
            f"Google credentials not found at: {CREDS_PATH}\n"
            "Set GOOGLE_CREDS_PATH in your .env file."
        )
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    return gspread.authorize(creds)


def normalize(value: str) -> str:
    """Lowercase, strip whitespace and punctuation for fuzzy dedup."""
    value = value.strip().lower()
    # Remove common URL prefixes so https://instagram.com/foo == instagram.com/foo
    value = re.sub(r"https?://", "", value)
    value = re.sub(r"www\.", "", value)
    value = value.rstrip("/")
    return value


def get_dedup_set() -> set:
    """
    Reads all non-ADHD tabs and returns a set of normalized identifiers
    (URLs, usernames, group names) for cross-tab deduplication.
    """
    client = get_client()
    sheet = client.open_by_key(SHEET_ID)
    known = set()

    for worksheet in sheet.worksheets():
        tab_name = worksheet.title
        if tab_name in SKIP_TABS:
            continue

        try:
            all_rows = worksheet.get_all_values()
        except gspread.exceptions.APIError as e:
            print(f"[read_sheet] Warning: could not read tab '{tab_name}': {e}")
            time.sleep(2)
            continue

        # Skip header row (index 0)
        for row in all_rows[1:]:
            for cell in row:
                cell = cell.strip()
                if not cell:
                    continue
                normalized = normalize(cell)
                if normalized:
                    known.add(normalized)
                    # Also add just the username portion of Instagram URLs
                    if "instagram.com/" in normalized:
                        username = normalized.split("instagram.com/")[-1].split("/")[0]
                        if username:
                            known.add(username)
                    # Also add just the subreddit name portion of Reddit URLs
                    if "reddit.com/r/" in normalized:
                        sub = normalized.split("reddit.com/r/")[-1].split("/")[0]
                        if sub:
                            known.add(sub)
                            known.add(f"r/{sub}")

        # Rate limit courtesy
        time.sleep(0.5)

    return known


def get_tab_counts() -> dict:
    """Returns a dict of {tab_name: row_count} for all non-ADHD tabs."""
    client = get_client()
    sheet = client.open_by_key(SHEET_ID)
    counts = {}

    for worksheet in sheet.worksheets():
        tab_name = worksheet.title
        if tab_name in SKIP_TABS:
            continue
        try:
            all_rows = worksheet.get_all_values()
            # Subtract 1 for header row
            counts[tab_name] = max(0, len(all_rows) - 1)
        except gspread.exceptions.APIError:
            counts[tab_name] = "error"
        time.sleep(0.5)

    return counts


def is_duplicate(value: str, known: set) -> bool:
    """Check if a value (URL, username, name) is already in the known set."""
    normalized = normalize(value)
    if normalized in known:
        return True
    # Also check username extracted from URL
    if "instagram.com/" in normalized:
        username = normalized.split("instagram.com/")[-1].split("/")[0]
        if username in known:
            return True
    if "reddit.com/r/" in normalized:
        sub = normalized.split("reddit.com/r/")[-1].split("/")[0]
        if sub in known or f"r/{sub}" in known:
            return True
    return False


if __name__ == "__main__":
    print("Reading CAIT Google Sheet...")
    counts = get_tab_counts()
    print("\nCurrent row counts (excluding header):")
    for tab, count in counts.items():
        print(f"  {tab}: {count} entries")

    known = get_dedup_set()
    print(f"\nTotal unique identifiers in dedup set: {len(known)}")
    print("Ready for deduplication.")
