"""
score_and_filter.py
-------------------
Silently scores all 577 pending accounts (rows 299+) in the sheet.
Accounts that don't pass are removed. No scores are written to the sheet.
Only real medical moms / families / caregivers make it through.
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
KEEP_ROWS   = 298
PASS_SCORE  = 15   # minimum score to stay in the sheet

# ── Scoring ───────────────────────────────────────────────────────────────────

DIAGNOSIS_KEYWORDS = [
    "trisomy", "trisomy13", "trisomy18", "trisomy21",
    "epilepsy", "seizure", "dravet", "infantile spasm",
    "cerebral palsy", "cp warrior", "cpmom",
    "cystic fibrosis", "cf warrior", "cfmom",
    "chd", "congenital heart", "hlhs", "heart defect", "heart warrior",
    "spina bifida",
    "hydrocephalus", "shunt",
    "trach", "tracheostomy", "ventilator", "vent dependent", "g-tube", "gtube", "feeding tube",
    "nicu", "preemie", "premature",
    "t1d", "type 1 diabetes", "type1", "juvenile diabetes",
    "rare disease", "rare condition", "undiagnosed",
    "mitochondrial", "mito", "leigh syndrome",
    "pfeiffer", "rubinstein", "down syndrome",
    "cancer", "leukemia", "tumor", "chemotherapy", "chemo",
    "autism", "asd", "nonverbal",
    "metabolic disorder", "metabolic disease",
    "eoe", "eosinophilic",
    "medically complex", "medically fragile",
    "medically complicated",
]

PARENT_KEYWORDS = [
    "mom", "mama", "mommy", "momma", "mum", "mummy",
    "mother", "dad", "daddy", "father", "papa",
    "parent", "caregiver", "caretaker",
]

PERSONAL_JOURNEY_KEYWORDS = [
    "our journey", "our story", "my journey", "my story",
    "our life", "our world", "raising", "living with",
    "warrior", "fighter", "advocate", "advocacy",
    "hospital", "medical", "therapy", "treatment", "surgery", "diagnosis",
    "diagnosed", "rare", "complex", "special needs",
    "son", "daughter", "baby", "child", "kid", "little one",
    "rainbow baby", "angel baby", "nicu grad",
]

ORG_BIO_SIGNALS = [
    "nonprofit", "non-profit", "501(c)", "registered charity",
    "our mission", "we are dedicated", "our organization",
    "foundation", "our foundation", "our clinic", "we provide services",
    "we offer", "our team of", "contact us", "info@", "admin@",
    "press inquiries", "media contact", "donate", "donations welcome",
    "follow for awareness", "spreading awareness",
]

BUSINESS_SIGNALS = [
    "amazon storefront", "amazon store", "shop my", "use code",
    "discount code", "affiliate", "collab@", "collabs@",
    "business inquiries", "business only", "pr inquiries",
    "sponsored", "brand deal", "link in bio for discount",
    "click link to shop", "shop now", "buy now",
]

IG_CATEGORY_ORG = [
    "nonprofit organization", "hospital", "medical center", "clinic",
    "charity organization", "health/beauty", "pharmaceutical company",
    "government organization", "educational research center",
    "community organization", "advocacy organization",
    "children's hospital",
]

def score_account(handle: str, display_name: str, bio: str,
                  followers: int, posts: int,
                  is_business: bool, ig_category: str) -> int:
    score = 0
    b = (bio or "").lower()
    n = (display_name or "").lower()
    h = handle.lower()

    # ── Hard disqualifiers ──────────────────────────────────────────────────
    # Instagram says it's a business/org category
    if ig_category and any(cat in ig_category.lower() for cat in IG_CATEGORY_ORG):
        return -100

    # Zero posts = inactive/bot
    if posts == 0:
        return -100

    # ── Org/business signals ────────────────────────────────────────────────
    for sig in ORG_BIO_SIGNALS:
        if sig in b:
            score -= 40
            break

    for sig in BUSINESS_SIGNALS:
        if sig in b:
            score -= 25
            break

    if is_business:
        score -= 20

    # ── Diagnosis keyword in bio ─────────────────────────────────────────────
    diag_hit = False
    for kw in DIAGNOSIS_KEYWORDS:
        if kw in b:
            score += 35
            diag_hit = True
            break  # count once

    # Diagnosis in display name
    if not diag_hit:
        for kw in DIAGNOSIS_KEYWORDS:
            if kw in n or kw in h:
                score += 20
                break

    # ── Parent/caregiver identity ────────────────────────────────────────────
    parent_hit = False
    for kw in PARENT_KEYWORDS:
        if kw in b or kw in n:
            score += 25
            parent_hit = True
            break

    # ── Personal journey signals ─────────────────────────────────────────────
    journey_hits = sum(1 for kw in PERSONAL_JOURNEY_KEYWORDS if kw in b)
    score += min(journey_hits * 8, 25)   # cap at 25

    # ── No medical signal at all ─────────────────────────────────────────────
    if not diag_hit and not parent_hit and journey_hits == 0 and len(b) > 20:
        score -= 20

    # ── Bio length (empty bio = neutral, long bio = real person) ────────────
    if len(b) > 80:
        score += 5
    elif len(b) == 0:
        score -= 5   # slight penalty, no info

    return score

# ── Apify profile scrape ──────────────────────────────────────────────────────
def scrape_profiles(client, handles: list[str], batch_num: int, total: int) -> dict:
    urls = list(dict.fromkeys(f"https://www.instagram.com/{h.lstrip('@')}/" for h in handles))
    print(f"  Batch {batch_num}/{total}: {len(handles)} profiles...", end=" ", flush=True)
    try:
        run = client.actor("apify/instagram-scraper").call(run_input={
            "directUrls":   urls,
            "resultsType":  "details",
            "resultsLimit": len(handles),
            "proxy":        {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
        })
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        result = {}
        for item in items:
            h = (item.get("username") or "").lower().lstrip("@")
            if h:
                result[h] = item
        print(f"{len(result)} back")
        time.sleep(2)
        return result
    except Exception as e:
        print(f"ERROR: {e}")
        return {}

# ── Google Sheets ─────────────────────────────────────────────────────────────
def make_gc():
    creds = Credentials.from_service_account_file(
        CREDS_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=== SCORE & FILTER PENDING ACCOUNTS ===\n")

    # 1. Read sheet
    print("[1] Reading sheet...")
    gc = make_gc()
    ss = gc.open_by_key(SHEET_ID)
    ws = ss.worksheet(TAB_NAME)
    all_rows = ws.get_all_values()

    hdrs = [h.strip() for h in all_rows[0]]
    hi   = {h: i for i, h in enumerate(hdrs)}
    pending_rows = all_rows[KEEP_ROWS:]   # rows 299+

    def g(row, col):
        i = hi.get(col)
        return row[i].strip() if i is not None and i < len(row) else ""

    print(f"  Pending rows: {len(pending_rows)}")

    # Extract handles — deduplicate while preserving order
    seen = set()
    handles = []
    for row in pending_rows:
        h = g(row, "Handle").lstrip("@").lower()
        if h and h not in seen:
            seen.add(h)
            handles.append(h)

    # 2. Scrape all profiles
    print(f"\n[2] Scraping {len(handles)} profiles...")
    client      = ApifyClient(APIFY_TOKEN)
    BATCH_SIZE  = 50
    all_profiles = {}
    total_batches = math.ceil(len(handles) / BATCH_SIZE)

    for i in range(0, len(handles), BATCH_SIZE):
        batch    = handles[i:i + BATCH_SIZE]
        batch_n  = i // BATCH_SIZE + 1
        profiles = scrape_profiles(client, batch, batch_n, total_batches)
        all_profiles.update(profiles)

    print(f"\n  Profiles retrieved: {len(all_profiles)}")

    # 3. Score and filter
    print("\n[3] Scoring accounts...")
    kept    = []
    removed = 0
    score_dist = {"pass": 0, "fail": 0, "no_profile": 0}

    for row in pending_rows:
        handle  = g(row, "Handle").lstrip("@").lower()
        display = g(row, "Display Name")
        if not handle:
            continue

        profile = all_profiles.get(handle)
        if not profile:
            # No profile returned — keep if we had Apify errors, skip if clearly private/deleted
            if len(all_profiles) == 0:
                # Apify failed entirely — keep everything, don't wipe
                kept.append(row)
                score_dist["pass"] += 1
            else:
                score_dist["no_profile"] += 1
                removed += 1
            continue

        bio         = profile.get("biography") or ""
        full_name   = profile.get("fullName") or display or ""
        followers   = profile.get("followersCount") or 0
        posts       = profile.get("postsCount") or 0
        is_biz      = profile.get("isBusinessAccount") or False
        ig_cat      = profile.get("businessCategoryName") or ""

        score = score_account(handle, full_name, bio, followers, posts, is_biz, ig_cat)

        if score >= PASS_SCORE:
            # Update display name from fresh profile data
            dn_col = hi.get("Display Name")
            if dn_col is not None and full_name and dn_col < len(row):
                row = list(row)
                row[dn_col] = full_name
            kept.append(row)
            score_dist["pass"] += 1
        else:
            removed += 1
            score_dist["fail"] += 1

    print(f"  Passed: {score_dist['pass']}")
    print(f"  Failed (low score): {score_dist['fail']}")
    print(f"  Skipped (no profile/private): {score_dist['no_profile']}")
    print(f"  Total removed: {removed}")

    # 4. Rewrite sheet
    print(f"\n[4] Writing {len(kept)} accounts back to sheet (row 299+)...")
    ws.batch_clear(["A299:H20000"])
    time.sleep(2)

    if kept:
        BATCH = 500
        for i in range(0, len(kept), BATCH):
            chunk     = kept[i:i + BATCH]
            start_row = 299 + i
            end_row   = start_row + len(chunk) - 1
            ws.update(f"A{start_row}:H{end_row}", chunk, value_input_option="USER_ENTERED")
            print(f"  Written rows {start_row}-{end_row}")
            time.sleep(1)

    print(f"\n=== DONE ===")
    print(f"  Before: {len(pending_rows)}")
    print(f"  After:  {len(kept)}")
    print(f"  Removed: {removed}")

if __name__ == "__main__":
    main()
