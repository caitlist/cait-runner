"""
scrape_tiktok_medical_parents.py
----------------------------------
Scrapes TikTok medical parent hashtags via Apify, scores creators,
then CROSS-CHECKS each passing account for an Instagram presence
(since CAIT contacts via Instagram only).

Cross-check logic:
  1. Parse the TikTok bio for an Instagram handle or instagram.com link
  2. If not found in bio, try the same username on Instagram
  3. Only add accounts that have a verified Instagram with 1,000+ followers

Profile link stored as https://www.instagram.com/{ig_handle}/ (not TikTok link).

This is Track 1 of the 500+ accounts pipeline.
"""

import re, time, math
import gspread
from google.oauth2.service_account import Credentials
from apify_client import ApifyClient
from dotenv import dotenv_values

vals = dotenv_values("c:/Users/lamch/Downloads/Caitlist/.env")
APIFY_TOKEN  = vals.get("APIFY_TOKEN")
SHEET_ID     = vals.get("GOOGLE_SHEET_ID")
CREDS_PATH   = vals.get("GOOGLE_CREDS_PATH")
TAB_NAME     = "Medical Mom DM Outreach"
PASS_SCORE   = 15
MIN_FOLLOWERS = 0  # No follower minimum — all active accounts qualify
POSTS_PER_TAG = 20
BATCH_SIZE   = 50

TIKTOK_HASHTAGS = [
    "medicalmom", "medicalmomlife", "medicallycomplex", "specialneedsmom",
    "nicumom", "tubemom", "gtubemom", "trachmom", "epilepsymom",
    "prematurebaby", "nicubaby", "rarediseasemom", "disabilitymom",
    "specialneedsmama",
]

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


def assign_category(hashtag):
    h = hashtag.lower()
    if any(k in h for k in ["epilepsy","seizure","dravet"]):
        return "Epilepsy / Seizure Disorders"
    if any(k in h for k in ["gtube","tube","trach","feeding"]):
        return "G-tube / Trach / Feeding Tube"
    if any(k in h for k in ["nicu","preemie","premature"]):
        return "NICU / Preemie"
    if any(k in h for k in ["raredisease","disability"]):
        return "Rare / Disability"
    if any(k in h for k in ["special"]):
        return "Special Needs"
    return "Medically Complex (General)"


def score_account_from_bio(handle, display_name, bio):
    """Score using bio text only (for TikTok pre-filter before IG verification)."""
    score = 0
    b = (bio or "").lower()
    n = (display_name or "").lower()
    h = handle.lower()
    for sig in ORG_BIO_SIGNALS:
        if sig in b:
            score -= 40
            break
    for sig in BUSINESS_SIGNALS:
        if sig in b:
            score -= 25
            break
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


def extract_ig_from_bio(bio):
    """Try to find an Instagram handle from a TikTok bio."""
    if not bio:
        return None
    b = bio.lower()
    # instagram.com/handle link
    m = re.search(r'instagram\.com/([a-zA-Z0-9._]+)/?', bio)
    if m:
        return m.group(1).lower()
    # ig: handle or ig: @handle
    m = re.search(r'\big[:\s]+@?([a-zA-Z0-9._]{2,30})\b', bio, re.IGNORECASE)
    if m:
        return m.group(1).lower()
    # linktr.ee and other link-in-bio tools don't give us the IG directly
    return None


def is_english(text):
    if not text:
        return True
    ascii_count = sum(1 for c in text if ord(c) < 128)
    return ascii_count / len(text) > 0.7


def scrape_ig_profiles(client, handles, batch_num, total):
    """Scrape Instagram profiles for a batch of handles."""
    urls = list(dict.fromkeys(f"https://www.instagram.com/{h.lstrip('@')}/".lower() for h in handles))
    print(f"  IG batch {batch_num}/{total}: {len(handles)} profiles...", end=" ", flush=True)
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


# ── Connect ────────────────────────────────────────────────────────────────────
creds = Credentials.from_service_account_file(
    CREDS_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets"])
gc = gspread.authorize(creds)
ws = gc.open_by_key(SHEET_ID).worksheet(TAB_NAME)

all_rows = ws.get_all_values()
existing_ig_handles = set()
for row in all_rows[1:]:
    h = row[0].strip().lstrip("@").lower()
    if h:
        existing_ig_handles.add(h)
print(f"Existing IG handles in sheet: {len(existing_ig_handles)}")

# ── Step 1: Scrape TikTok hashtags ────────────────────────────────────────────
client = ApifyClient(APIFY_TOKEN)
tiktok_candidates = []
seen_tiktok = set()

print(f"\n[1] Scraping {len(TIKTOK_HASHTAGS)} TikTok hashtags...")
for tag in TIKTOK_HASHTAGS:
    print(f"  #{tag}...", end=" ", flush=True)
    try:
        run = client.actor("clockworks/tiktok-scraper").call(run_input={
            "hashtags":       [tag],
            "resultsPerPage": POSTS_PER_TAG,
            "proxyConfiguration": {"useApifyProxy": True},
        })
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        count = 0
        for item in items:
            author = item.get("authorMeta") or item.get("author") or {}
            handle = (
                author.get("name") or author.get("uniqueId") or
                item.get("authorUniqueId") or ""
            ).lower().lstrip("@")
            if not handle or handle in seen_tiktok:
                continue
            bio     = author.get("signature") or author.get("bio") or item.get("authorSignature") or ""
            name    = author.get("nickName") or author.get("nickname") or author.get("name") or ""
            caption = item.get("text") or item.get("desc") or ""
            if not is_english(bio) and not is_english(caption):
                continue
            # Quick pre-filter: must score >= PASS_SCORE from TikTok bio alone
            sc = score_account_from_bio(handle, name, bio)
            if sc < PASS_SCORE:
                continue
            seen_tiktok.add(handle)
            ig_in_bio = extract_ig_from_bio(bio)
            tiktok_candidates.append({
                "tiktok_handle": handle,
                "display":       name,
                "bio":           bio,
                "category":      assign_category(tag),
                "hashtag":       tag,
                "ig_from_bio":   ig_in_bio,
            })
            count += 1
        print(f"{count} pre-passed")
        time.sleep(2)
    except Exception as e:
        print(f"ERROR: {e}")

print(f"\n  TikTok accounts pre-passing scoring: {len(tiktok_candidates)}")

if not tiktok_candidates:
    print("Nothing to cross-check.")
    exit(0)

# ── Step 2: Build Instagram handle candidates for cross-check ─────────────────
# For each TikTok account:
#   - If bio had an IG handle → try that first
#   - Otherwise → try same TikTok username on Instagram
print("\n[2] Building Instagram cross-check list...")
ig_to_check = {}   # ig_handle -> tiktok account dict

for acc in tiktok_candidates:
    if acc["ig_from_bio"]:
        ig_h = acc["ig_from_bio"]
        print(f"  @{acc['tiktok_handle']} → IG from bio: @{ig_h}")
    else:
        ig_h = acc["tiktok_handle"]  # try same username
    if ig_h not in existing_ig_handles:
        ig_to_check[ig_h] = acc

print(f"  IG handles to verify: {len(ig_to_check)}")

if not ig_to_check:
    print("All IG handles already in sheet or none to check.")
    exit(0)

# ── Step 3: Verify Instagram accounts via Apify ───────────────────────────────
print(f"\n[3] Verifying {len(ig_to_check)} Instagram accounts...")
all_ig_profiles = {}
handles_list = list(ig_to_check.keys())
total_batches = math.ceil(len(handles_list) / BATCH_SIZE)
for i in range(0, len(handles_list), BATCH_SIZE):
    batch = handles_list[i:i + BATCH_SIZE]
    profiles = scrape_ig_profiles(client, batch, i // BATCH_SIZE + 1, total_batches)
    all_ig_profiles.update(profiles)
print(f"  IG profiles found: {len(all_ig_profiles)}")

if len(all_ig_profiles) == 0:
    print("ERROR: Apify returned 0 IG profiles — aborting")
    exit(1)

# ── Step 4: Final filter — IG must exist + 1,000 followers ────────────────────
print("\n[4] Applying final filter (IG exists + 1,000+ followers)...")
passed = []
dist = {"pass": 0, "no_ig": 0, "under_1k": 0}

for ig_handle, acc in ig_to_check.items():
    profile = all_ig_profiles.get(ig_handle)
    if not profile:
        dist["no_ig"] += 1
        print(f"  SKIP @{ig_handle} — no Instagram account found")
        continue
    followers = profile.get("followersCount") or 0
    if followers < MIN_FOLLOWERS:
        dist["under_1k"] += 1
        print(f"  SKIP @{ig_handle} — only {followers:,} IG followers")
        continue
    ig_link = f"https://www.instagram.com/{ig_handle}/"
    passed.append([ig_handle, ig_link, acc["category"], acc["hashtag"],
                   profile.get("fullName") or acc["display"], "", "", ""])
    dist["pass"] += 1

print(f"  Passed (verified on IG, 1k+ followers): {dist['pass']}")
print(f"  No IG account found:                    {dist['no_ig']}")
print(f"  Under 1,000 IG followers:               {dist['under_1k']}")

# ── Step 5: Append to bottom ───────────────────────────────────────────────────
if passed:
    print(f"\n[5] Appending {len(passed)} verified accounts to sheet...")
    current_rows = ws.get_all_values()
    next_row = len(current_rows) + 1
    end_row = next_row + len(passed) - 1
    ws.update(f"A{next_row}:H{end_row}", passed, value_input_option="USER_ENTERED")
    print(f"  Written rows {next_row}-{end_row}")

print(f"\n=== DONE ===")
print(f"  TikTok pre-passed:       {len(tiktok_candidates)}")
print(f"  IG accounts checked:     {len(ig_to_check)}")
print(f"  Final verified + added:  {len(passed)}")
