"""
filter_pending_accounts.py
--------------------------
Cleans up Medical Mom DM Outreach rows 299+ by:
1. Scraping full profiles for all pending accounts
2. Removing non-English accounts
3. Removing organizations, foundations, centers, clinics, etc.
4. Keeping only real people — moms, families, caregivers
5. Rewrites the cleaned list back to the sheet (row 299+)
"""

import os, re, time, math
import gspread
from google.oauth2.service_account import Credentials
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
SHEET_ID    = os.environ.get("GOOGLE_SHEET_ID")
CREDS_PATH  = os.environ.get("GOOGLE_CREDS_PATH")
TAB_NAME    = "Medical Mom DM Outreach"
KEEP_ROWS   = 298   # rows 1-298 untouched

# ── Organization detection ────────────────────────────────────────────────────
ORG_NAME_KEYWORDS = [
    "foundation", "center", "centre", "clinic", "clinics", "hospital",
    "organization", "organisation", "institute", "society", "association",
    "network", "alliance", "program", "programme", "charity", "fund", "trust",
    "nonprofit", "non-profit", "llc", "inc.", " inc", "corp", "official",
    "therapy services", "therapies", "medical group", "health system",
    "children's", "childrens", "pediatric", "paediatric",
    "awareness", "advocacy", "support group", "community", "team",
    "research", "cure", "fighting", "warriors (org)", "angels",
]

ORG_HANDLE_KEYWORDS = [
    "foundation", "clinic", "hospital", "center", "centre", "org",
    "institute", "nonprofit", "charity", "official", "hq", "team",
    "pediatric", "paediatric", "medicalgroup", "healthsystem",
]

REAL_PERSON_BIO_SIGNALS = [
    "mom", "mama", "mommy", "mum", "mother", "dad", "daddy", "father",
    "parent", "wife", "husband", "family", "daughter", "son", "baby",
    "our journey", "my journey", "our story", "my story",
    "raising", "living with", "warrior", "fighter",
]

def is_org(handle: str, display_name: str, bio: str) -> bool:
    h = handle.lower()
    n = (display_name or "").lower()
    b = (bio or "").lower()

    # Check handle
    for kw in ORG_HANDLE_KEYWORDS:
        if kw in h:
            return True

    # Check display name
    for kw in ORG_NAME_KEYWORDS:
        if kw in n:
            return True

    # Bio signals for org
    org_bio_phrases = [
        "nonprofit", "non-profit", "501(c)", "registered charity",
        "official account", "our mission", "we are dedicated",
        "our organization", "our foundation", "our clinic",
        "we provide", "we offer", "our team of", "contact us at",
        "info@", "admin@", "press@", "media@",
    ]
    for phrase in org_bio_phrases:
        if phrase in b:
            return True

    return False

def is_english(text: str) -> bool:
    if not text:
        return True  # no bio = can't tell, give benefit of doubt
    # Count ASCII printable chars
    ascii_count = sum(1 for c in text if ord(c) < 128)
    ratio = ascii_count / max(len(text), 1)
    if ratio < 0.6:
        return False
    # Check for CJK, Arabic, Cyrillic, etc.
    non_latin = sum(1 for c in text if ord(c) > 1000)
    if non_latin / max(len(text), 1) > 0.1:
        return False
    return True

def has_real_person_signal(bio: str) -> bool:
    """Returns True if bio has at least one signal of a real person/family."""
    if not bio:
        return True  # no bio = benefit of doubt
    b = bio.lower()
    return any(sig in b for sig in REAL_PERSON_BIO_SIGNALS)

# ── Apify profile scrape ──────────────────────────────────────────────────────
def scrape_profiles_batch(client, handles: list[str], batch_num: int, total_batches: int) -> dict:
    """Scrape a batch of profiles. Returns {handle: profile_data}."""
    urls = [f"https://www.instagram.com/{h.lstrip('@')}/" for h in handles]
    print(f"  Batch {batch_num}/{total_batches}: scraping {len(handles)} profiles...")
    try:
        run = client.actor("apify/instagram-scraper").call(run_input={
            "directUrls":         urls,
            "resultsType":        "details",
            "resultsLimit":       len(handles),
            "proxy":              {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
            "scrapePostsUntilDate": None,
        })
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        result = {}
        for item in items:
            h = (item.get("username") or "").lower().lstrip("@")
            if h:
                result[h] = item
        print(f"    -> Got {len(result)} profiles back")
        time.sleep(2)
        return result
    except Exception as e:
        print(f"    ERROR: {e}")
        return {}

# ── Google Sheets ─────────────────────────────────────────────────────────────
def make_gc():
    creds = Credentials.from_service_account_file(
        CREDS_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=== FILTER PENDING ACCOUNTS ===\n")

    # 1. Read sheet
    print("[1] Reading sheet...")
    gc = make_gc()
    ss = gc.open_by_key(SHEET_ID)
    ws = ss.worksheet(TAB_NAME)
    all_rows = ws.get_all_values()

    hdrs  = [h.strip() for h in all_rows[0]]
    hi    = {h: i for i, h in enumerate(hdrs)}
    pending_rows = all_rows[KEEP_ROWS:]   # rows 299+ (0-indexed: index 298+)

    print(f"  Pending rows to filter: {len(pending_rows)}")

    def g(row, col):
        i = hi.get(col)
        return row[i].strip() if i is not None and i < len(row) else ""

    # Quick pre-filter by display name + handle (no API needed)
    print("\n[2] Pre-filtering by name/handle keywords...")
    pre_pass  = []
    pre_fails = []
    for row in pending_rows:
        handle  = g(row, "Handle").lstrip("@").lower()
        display = g(row, "Display Name")
        if not handle:
            continue
        if is_org(handle, display, ""):
            pre_fails.append((handle, "org-name/handle"))
        else:
            pre_pass.append(row)

    print(f"  Removed by name/handle: {len(pre_fails)}")
    print(f"  Remaining for profile scrape: {len(pre_pass)}")

    # 3. Batch scrape profiles
    print(f"\n[3] Scraping profiles in batches of 50...")
    client     = ApifyClient(APIFY_TOKEN)
    BATCH_SIZE = 50
    all_profiles = {}

    handles_to_scrape = [g(row, "Handle").lstrip("@").lower() for row in pre_pass]
    total_batches     = math.ceil(len(handles_to_scrape) / BATCH_SIZE)

    for i in range(0, len(handles_to_scrape), BATCH_SIZE):
        batch   = handles_to_scrape[i:i + BATCH_SIZE]
        batch_n = i // BATCH_SIZE + 1
        profiles = scrape_profiles_batch(client, batch, batch_n, total_batches)
        all_profiles.update(profiles)

    print(f"\n  Total profiles retrieved: {len(all_profiles)}")

    # 4. Filter each row
    print("\n[4] Applying filters...")
    kept    = []
    removed = []

    for row in pre_pass:
        handle  = g(row, "Handle").lstrip("@").lower()
        display = g(row, "Display Name")

        profile = all_profiles.get(handle, {})
        bio     = profile.get("biography") or profile.get("bio") or ""
        full_name = profile.get("fullName") or display or ""

        # Update display name from profile if we got it
        dn_col = hi.get("Display Name")
        if dn_col is not None and full_name and dn_col < len(row):
            row = list(row)
            row[dn_col] = full_name

        # Filter: organization
        if is_org(handle, full_name, bio):
            removed.append((handle, "organization"))
            continue

        # Filter: non-English
        if not is_english(bio) or not is_english(full_name):
            removed.append((handle, "non-english"))
            continue

        # Filter: no real person signal (only if bio exists and is substantial)
        if len(bio) > 30 and not has_real_person_signal(bio):
            # Don't auto-remove — could be a medical mom who just doesn't list it
            # Only remove if it looks like an org from bio
            pass

        kept.append(row)

    print(f"  Kept: {len(kept)}")
    print(f"  Removed: {len(removed)}")

    # Show removal breakdown
    from collections import Counter
    reasons = Counter(r for _, r in removed + pre_fails)
    for reason, count in reasons.most_common():
        print(f"    {reason}: {count}")

    # 5. Rewrite sheet rows 299+
    print(f"\n[5] Writing {len(kept)} clean rows back to sheet (row 299+)...")
    ws.batch_clear([f"A299:I20000"])
    time.sleep(2)

    if kept:
        BATCH = 500
        for i in range(0, len(kept), BATCH):
            chunk     = kept[i:i + BATCH]
            start_row = 299 + i
            end_row   = start_row + len(chunk) - 1
            ws.update(f"A{start_row}:I{end_row}", chunk, value_input_option="USER_ENTERED")
            print(f"  Written rows {start_row}-{end_row}")
            time.sleep(1)

    print(f"\n=== DONE ===")
    print(f"  Total pending before: {len(pending_rows)}")
    print(f"  Total pending after:  {len(kept)}")
    print(f"  Removed:              {len(pending_rows) - len(kept)}")

if __name__ == "__main__":
    main()
