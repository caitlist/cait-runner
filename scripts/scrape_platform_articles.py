"""
scrape_platform_articles.py
----------------------------
Scrapes publicly accessible influencer ranking articles from platforms like
influencer-hero.com, amraandelma.com, adhdonline.com, etc.

Extracts Instagram handles from each article, deduplicates against the sheet,
then runs each handle through Apify profile scraping + scoring.
Only verified medical parents (score >= 15) are appended to the sheet.

This is Track 0 of the 500+ accounts pipeline.
"""

import re, time, math
import requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
from apify_client import ApifyClient
from dotenv import dotenv_values

vals = dotenv_values("c:/Users/lamch/Downloads/Caitlist/.env")
APIFY_TOKEN = vals.get("APIFY_TOKEN")
SHEET_ID    = vals.get("GOOGLE_SHEET_ID")
CREDS_PATH  = vals.get("GOOGLE_CREDS_PATH")
TAB_NAME      = "Medical Mom DM Outreach"
PASS_SCORE    = 15
MIN_FOLLOWERS = 0  # No follower minimum — all active accounts qualify
BATCH_SIZE    = 50

ARTICLE_SOURCES = [
    {"url": "https://www.amraandelma.com/50-top-patient-influencers/",                                         "category": "Patient Advocacy"},
    {"url": "https://adhdonline.com/articles/follow-me-a-directory-of-the-top-adhd-instagram-influencers-and-experts/", "category": "ADHD/Neurodivergent"},
    {"url": "https://themighty.com/topic/autism-spectrum-disorder/actually-autistic-instagram",                "category": "Autism"},
]

# IG path segments that are NOT usernames
IG_NON_HANDLE_PATHS = {
    "p", "reel", "tv", "reels", "stories", "explore", "accounts",
    "directory", "hashtag", "about", "help", "legal", "press",
    "api", "oauth", "challenge", "embed", "login", "privacy",
    "terms", "contact", "blog", "jobs", "security", "favicon.ico",
    "static", "images", "shared_data",
}

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


def extract_handles_from_url(url, category):
    """Fetch an article and extract Instagram handles from it."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"    FETCH ERROR: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    handles = set()

    # Pattern 1: href links to instagram.com
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        m = re.search(r'instagram\.com/([A-Za-z0-9._]+)/?', href)
        if m:
            h = m.group(1).lower()
            if h and h not in IG_NON_HANDLE_PATHS and len(h) >= 2:
                handles.add(h)

    # Pattern 2: instagram.com/handle in plain text
    for m in re.finditer(r'instagram\.com/([A-Za-z0-9._]+)/?', soup.get_text()):
        h = m.group(1).lower()
        if h and h not in IG_NON_HANDLE_PATHS and len(h) >= 2:
            handles.add(h)

    # Pattern 3: @handle mentions in text
    for m in re.finditer(r'@([A-Za-z0-9._]{2,30})', soup.get_text()):
        h = m.group(1).lower()
        # Skip obviously non-IG mentions (emails, etc.)
        if "." not in h or h.endswith(".com") or h.endswith(".org"):
            pass
        handles.add(h)

    return [(h, category) for h in handles]


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
    urls = list(dict.fromkeys(f"https://www.instagram.com/{h.lstrip('@')}/".lower() for h in handles))
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


# ── Connect ────────────────────────────────────────────────────────────────────
creds = Credentials.from_service_account_file(
    CREDS_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets"])
gc = gspread.authorize(creds)
ws = gc.open_by_key(SHEET_ID).worksheet(TAB_NAME)

all_rows = ws.get_all_values()
existing_handles = set()
for row in all_rows[1:]:
    h = row[0].strip().lstrip("@").lower()
    if h:
        existing_handles.add(h)
print(f"Existing handles in sheet: {len(existing_handles)}")

# ── Step 1: Scrape articles ────────────────────────────────────────────────────
print(f"\n[1] Scraping {len(ARTICLE_SOURCES)} article sources...")
all_candidates = {}  # handle -> category (deduped, last category wins)
seen = set(existing_handles)

for source in ARTICLE_SOURCES:
    url = source["url"]
    cat = source["category"]
    domain = re.sub(r'^https?://(www\.)?', '', url).split('/')[0]
    print(f"  {domain} ({cat})...", end=" ", flush=True)
    extracted = extract_handles_from_url(url, cat)
    new_count = 0
    for handle, category in extracted:
        if handle not in seen:
            seen.add(handle)
            all_candidates[handle] = {"category": category, "source": domain}
            new_count += 1
    print(f"{len(extracted)} extracted, {new_count} new unique")
    time.sleep(1)

print(f"\n  Total new unique handles: {len(all_candidates)}")

if not all_candidates:
    print("No new handles found. Exiting.")
    exit(0)

# ── Step 2: Scrape profiles ────────────────────────────────────────────────────
client = ApifyClient(APIFY_TOKEN)
handles_list = list(all_candidates.keys())
print(f"\n[2] Scraping {len(handles_list)} profiles via Apify...")
all_profiles = {}
total_batches = math.ceil(len(handles_list) / BATCH_SIZE)
for i in range(0, len(handles_list), BATCH_SIZE):
    batch = handles_list[i:i + BATCH_SIZE]
    profiles = scrape_profiles(client, batch, i // BATCH_SIZE + 1, total_batches)
    all_profiles.update(profiles)
print(f"  Profiles retrieved: {len(all_profiles)}")

if len(all_profiles) == 0:
    print("ERROR: Apify returned 0 profiles — aborting to protect sheet")
    exit(1)

# ── Step 3: Score ──────────────────────────────────────────────────────────────
print("\n[3] Scoring and verifying medical parent status...")
passed = []
dist = {"pass": 0, "fail": 0, "no_profile": 0}

for handle, meta in all_candidates.items():
    profile = all_profiles.get(handle)
    if not profile:
        dist["no_profile"] += 1
        continue
    bio       = profile.get("biography") or ""
    full_name = profile.get("fullName") or ""
    followers = profile.get("followersCount") or 0
    posts     = profile.get("postsCount") or 0
    is_biz    = profile.get("isBusinessAccount") or False
    ig_cat    = profile.get("businessCategoryName") or ""
    sc = score_account(handle, full_name, bio, followers, posts, is_biz, ig_cat)
    if sc >= PASS_SCORE and followers >= MIN_FOLLOWERS:
        ig_link = f"https://www.instagram.com/{handle}/"
        # Source hashtag column = source domain so Cherwin knows it's from a real platform
        passed.append([handle, ig_link, meta["category"], meta["source"],
                       full_name, "", "", ""])
        dist["pass"] += 1
    else:
        dist["fail"] += 1

print(f"  Passed (verified medical parents): {dist['pass']}")
print(f"  Failed (not medical parents):      {dist['fail']}")
print(f"  No profile:                        {dist['no_profile']}")

# ── Step 4: Append to bottom ───────────────────────────────────────────────────
if passed:
    print(f"\n[4] Appending {len(passed)} verified medical parents to sheet...")
    current_rows = ws.get_all_values()
    next_row = len(current_rows) + 1
    end_row = next_row + len(passed) - 1
    ws.update(f"A{next_row}:H{end_row}", passed, value_input_option="USER_ENTERED")
    print(f"  Written rows {next_row}-{end_row}")
else:
    print("\nNo accounts passed scoring.")

print(f"\n=== DONE ===")
print(f"  Handles extracted from articles: {len(all_candidates)}")
print(f"  Profiles scraped via Apify:      {len(all_profiles)}")
print(f"  Verified medical parents added:  {len(passed)}")
