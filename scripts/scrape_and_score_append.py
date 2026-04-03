"""
scrape_and_score_append.py
--------------------------
1. Scrapes 4 missing hashtags (caregiversupport, caregiverlife, caregivers, medicallycomplexfamily)
2. Scores both: existing pending rows in sheet (299+) AND new accounts from hashtags
3. Keeps passing rows in place (299+), appends new passing accounts to the bottom
"""

import os, time, math
import gspread
from google.oauth2.service_account import Credentials
from apify_client import ApifyClient
from dotenv import dotenv_values

vals = dotenv_values("c:/Users/lamch/Downloads/Caitlist/.env")
APIFY_TOKEN = vals.get("APIFY_TOKEN")
SHEET_ID    = vals.get("GOOGLE_SHEET_ID")
CREDS_PATH  = vals.get("GOOGLE_CREDS_PATH")
TAB_NAME    = "Medical Mom DM Outreach"
KEEP_ROWS   = 298
PASS_SCORE  = 15

DIAGNOSIS_KEYWORDS = [
    "trisomy","trisomy13","trisomy18","trisomy21","epilepsy","seizure","dravet","infantile spasm",
    "cerebral palsy","cp warrior","cpmom","cystic fibrosis","cf warrior","cfmom",
    "chd","congenital heart","hlhs","heart defect","heart warrior","spina bifida",
    "hydrocephalus","shunt","trach","tracheostomy","ventilator","vent dependent",
    "g-tube","gtube","feeding tube","nicu","preemie","premature",
    "t1d","type 1 diabetes","type1","juvenile diabetes","rare disease","rare condition",
    "undiagnosed","mitochondrial","mito","leigh syndrome","pfeiffer","rubinstein",
    "down syndrome","cancer","leukemia","tumor","chemotherapy","chemo",
    "autism","asd","nonverbal","metabolic disorder","metabolic disease",
    "eoe","eosinophilic","medically complex","medically fragile","medically complicated",
]
PARENT_KEYWORDS = [
    "mom","mama","mommy","momma","mum","mummy","mother",
    "dad","daddy","father","papa","parent","caregiver","caretaker",
]
PERSONAL_JOURNEY_KEYWORDS = [
    "our journey","our story","my journey","my story","our life","our world",
    "raising","living with","warrior","fighter","advocate","advocacy",
    "hospital","medical","therapy","treatment","surgery","diagnosis","diagnosed",
    "rare","complex","special needs","son","daughter","baby","child","kid",
    "little one","rainbow baby","angel baby","nicu grad",
]
ORG_BIO_SIGNALS = [
    "nonprofit","non-profit","501(c)","registered charity","our mission","we are dedicated",
    "our organization","foundation","our foundation","our clinic","we provide services","we offer",
    "our team of","contact us","info@","admin@","press inquiries","media contact",
    "donate","donations welcome","follow for awareness","spreading awareness",
]
BUSINESS_SIGNALS = [
    "amazon storefront","amazon store","shop my","use code","discount code","affiliate",
    "collab@","collabs@","business inquiries","business only","pr inquiries",
    "sponsored","brand deal","link in bio for discount","click link to shop","shop now","buy now",
]
IG_CATEGORY_ORG = [
    "nonprofit organization","hospital","medical center","clinic","charity organization",
    "health/beauty","pharmaceutical company","government organization",
    "educational research center","community organization","advocacy organization",
    "children hospital",
]

def score_account(handle, display_name, bio, followers, posts, is_business, ig_category):
    score = 0
    b = (bio or "").lower()
    n = (display_name or "").lower()
    h = handle.lower()
    if ig_category and any(cat in ig_category.lower() for cat in IG_CATEGORY_ORG):
        return -100
    if posts == 0:
        return -100
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
    diag_hit = False
    for kw in DIAGNOSIS_KEYWORDS:
        if kw in b:
            score += 35
            diag_hit = True
            break
    if not diag_hit:
        for kw in DIAGNOSIS_KEYWORDS:
            if kw in n or kw in h:
                score += 20
                break
    parent_hit = False
    for kw in PARENT_KEYWORDS:
        if kw in b or kw in n:
            score += 25
            parent_hit = True
            break
    journey_hits = sum(1 for kw in PERSONAL_JOURNEY_KEYWORDS if kw in b)
    score += min(journey_hits * 8, 25)
    if not diag_hit and not parent_hit and journey_hits == 0 and len(b) > 20:
        score -= 20
    if len(b) > 80:
        score += 5
    elif len(b) == 0:
        score -= 5
    return score

def scrape_profiles(client, handles, batch_num, total):
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

# ── Connect to sheet ───────────────────────────────────────────────────────────
creds = Credentials.from_service_account_file(
    CREDS_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets"])
gc = gspread.authorize(creds)
ws = gc.open_by_key(SHEET_ID).worksheet(TAB_NAME)

all_rows = ws.get_all_values()
hdrs = [h.strip() for h in all_rows[0]]
hi = {h: i for i, h in enumerate(hdrs)}

def g(row, col):
    i = hi.get(col)
    return row[i].strip() if i is not None and i < len(row) else ""

existing_handles = set()
for row in all_rows[1:]:
    h = row[0].strip().lstrip("@").lower()
    if h:
        existing_handles.add(h)
print(f"Existing handles in sheet: {len(existing_handles)}")

# ── Step 1: Scrape 4 missing hashtags ─────────────────────────────────────────
MISSING_HASHTAGS = ["caregiversupport", "caregiverlife", "caregivers", "medicallycomplexfamily"]
client = ApifyClient(APIFY_TOKEN)
new_from_hashtags = []

print("\n[1] Scraping 4 missing hashtags...")
for tag in MISSING_HASHTAGS:
    print(f"  #{tag}...", end=" ", flush=True)
    try:
        run = client.actor("apify/instagram-hashtag-scraper").call(run_input={
            "hashtags": [tag],
            "resultsLimit": 15,
            "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
        })
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        count = 0
        for item in items:
            owner = (item.get("ownerUsername") or item.get("owner", {}).get("username") or "").lower().lstrip("@")
            if not owner or owner in existing_handles:
                continue
            existing_handles.add(owner)
            display = item.get("ownerFullName") or ""
            new_from_hashtags.append({
                "handle": owner,
                "ig_link": f"https://www.instagram.com/{owner}/",
                "category": "Caregiver Community",
                "hashtag": tag,
                "display": display,
            })
            count += 1
        print(f"{count} new")
        time.sleep(2)
    except Exception as e:
        print(f"ERROR: {e}")

print(f"  Total new from 4 hashtags: {len(new_from_hashtags)}")

# ── Step 2: Collect all handles to score ──────────────────────────────────────
pending_rows = all_rows[KEEP_ROWS:]
print(f"\n[2] Pending rows in sheet (299+): {len(pending_rows)}")

seen = set()
to_score_rows = []
for row in pending_rows:
    h = g(row, "Handle").lstrip("@").lower()
    if h and h not in seen:
        seen.add(h)
        to_score_rows.append(row)

to_score_new = []
for acc in new_from_hashtags:
    if acc["handle"] not in seen:
        seen.add(acc["handle"])
        to_score_new.append(acc)

all_handles = [g(r, "Handle").lstrip("@").lower() for r in to_score_rows] + [a["handle"] for a in to_score_new]
print(f"  Total to score: {len(all_handles)} ({len(to_score_rows)} from sheet + {len(to_score_new)} new)")

# ── Step 3: Scrape profiles ────────────────────────────────────────────────────
print(f"\n[3] Scraping {len(all_handles)} profiles...")
BATCH_SIZE = 50
all_profiles = {}
total_batches = math.ceil(len(all_handles) / BATCH_SIZE)
for i in range(0, len(all_handles), BATCH_SIZE):
    batch = all_handles[i:i + BATCH_SIZE]
    profiles = scrape_profiles(client, batch, i // BATCH_SIZE + 1, total_batches)
    all_profiles.update(profiles)
print(f"  Profiles retrieved: {len(all_profiles)}")

if len(all_profiles) == 0:
    print("ERROR: Apify returned 0 profiles — aborting to protect sheet")
    exit(1)

# ── Step 4: Score ──────────────────────────────────────────────────────────────
print("\n[4] Scoring...")
kept_sheet = []
passed_new = []
dist = {"pass": 0, "fail": 0, "no_profile": 0}

for row in to_score_rows:
    handle = g(row, "Handle").lstrip("@").lower()
    display = g(row, "Display Name")
    profile = all_profiles.get(handle)
    if not profile:
        dist["no_profile"] += 1
        continue
    bio       = profile.get("biography") or ""
    full_name = profile.get("fullName") or display or ""
    followers = profile.get("followersCount") or 0
    posts     = profile.get("postsCount") or 0
    is_biz    = profile.get("isBusinessAccount") or False
    ig_cat    = profile.get("businessCategoryName") or ""
    sc = score_account(handle, full_name, bio, followers, posts, is_biz, ig_cat)
    if sc >= PASS_SCORE:
        row = list(row)
        dn_col = hi.get("Display Name")
        if dn_col is not None and full_name and dn_col < len(row):
            row[dn_col] = full_name
        kept_sheet.append(row)
        dist["pass"] += 1
    else:
        dist["fail"] += 1

for acc in to_score_new:
    profile = all_profiles.get(acc["handle"])
    if not profile:
        dist["no_profile"] += 1
        continue
    bio       = profile.get("biography") or ""
    full_name = profile.get("fullName") or acc["display"] or ""
    followers = profile.get("followersCount") or 0
    posts     = profile.get("postsCount") or 0
    is_biz    = profile.get("isBusinessAccount") or False
    ig_cat    = profile.get("businessCategoryName") or ""
    sc = score_account(acc["handle"], full_name, bio, followers, posts, is_biz, ig_cat)
    if sc >= PASS_SCORE:
        passed_new.append([
            acc["handle"], acc["ig_link"], acc["category"], acc["hashtag"],
            full_name, "", "", ""
        ])
        dist["pass"] += 1
    else:
        dist["fail"] += 1

print(f"  Passed (existing in sheet): {len(kept_sheet)}")
print(f"  Passed (new from hashtags): {len(passed_new)}")
print(f"  Failed:                     {dist['fail']}")
print(f"  No profile:                 {dist['no_profile']}")

# ── Step 5: Rewrite sheet ──────────────────────────────────────────────────────
# Rows 1-298: untouched
# Rows 299+:  kept_sheet (scored existing that passed)
# Bottom:     passed_new appended after kept_sheet
print(f"\n[5] Writing to sheet...")
ws.batch_clear(["A299:H20000"])
time.sleep(2)

all_to_write = kept_sheet + passed_new
if all_to_write:
    BATCH = 500
    for i in range(0, len(all_to_write), BATCH):
        chunk = all_to_write[i:i + BATCH]
        start_row = 299 + i
        end_row = start_row + len(chunk) - 1
        ws.update(f"A{start_row}:H{end_row}", chunk, value_input_option="USER_ENTERED")
        print(f"  Written rows {start_row}-{end_row}")
        time.sleep(1)

print(f"\n=== DONE ===")
print(f"  Existing scored rows kept:  {len(kept_sheet)}")
print(f"  New from 4 hashtags added:  {len(passed_new)}")
print(f"  Total in sheet (row 299+):  {len(all_to_write)}")
