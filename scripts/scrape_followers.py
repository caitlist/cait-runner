"""
scrape_followers.py
--------------------
Scrapes followers of a target Instagram account, scores them,
and inserts passing accounts at a specified row (pushing existing rows down).

Usage:
  python scripts/scrape_followers.py --url https://www.instagram.com/hiehelpcenter/ --insert-row 892 --limit 500
"""
import argparse, math, time, json, os
import gspread
from google.oauth2.service_account import Credentials
from apify_client import ApifyClient
from dotenv import dotenv_values

vals = dotenv_values("c:/Users/lamch/Downloads/Caitlist/.env")
APIFY_TOKEN = vals["APIFY_TOKEN"]
SHEET_ID    = vals["GOOGLE_SHEET_ID"]
CREDS_PATH  = vals["GOOGLE_CREDS_PATH"]
TAB_NAME    = "Medical Mom DM Outreach"
PASS_SCORE  = 15

parser = argparse.ArgumentParser()
parser.add_argument("--url", required=True, help="Instagram account URL to scrape followers from")
parser.add_argument("--insert-row", type=int, required=True, help="Row number to insert results at (pushes existing rows down)")
parser.add_argument("--limit", type=int, default=500, help="Max followers to scrape (default 500)")
args = parser.parse_args()

ACCOUNT_URL = args.url.rstrip("/") + "/"
account_handle = ACCOUNT_URL.rstrip("/").split("/")[-1]
SAVE_FILE = f"outputs/followers_{account_handle}.json"

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
    "educational research center","community organization","advocacy organization","children hospital",
]
DIAGNOSIS_KEYWORDS = [
    # Trisomy / Chromosomal
    "trisomy","trisomy13","trisomy18","trisomy21","down syndrome","downs syndrome",
    "edwards syndrome","patau syndrome","22q","22q deletion","digeorge",
    "phelan-mcdermid","phelan mcdermid","dup15q","angelman","angelman syndrome",
    "williams syndrome","noonan syndrome","kabuki syndrome","cornelia de lange",
    "prader-willi","prader willi","charge syndrome","fragile x","fragilex",
    # Epilepsy / Seizure
    "epilepsy","seizure","dravet","cdkl5","infantile spasm","west syndrome",
    "lennox-gastaut","rett syndrome","rett","foxg1","lissencephaly",
    # Brain / Neurological
    "cerebral palsy","cp warrior","cpmom","hydrocephalus","shunt","chiari",
    "tuberous sclerosis","sturge-weber","sturge weber","batten disease","batten",
    "leigh syndrome","mitochondrial","mito","metabolic disorder","metabolic disease",
    "pku","phenylketonuria","mucopolysaccharidosis","mps","sotos","apert",
    "treacher collins","craniosynostosis","hie","hypoxic ischemic","brain injury",
    # Heart / CHD
    "chd","congenital heart","hlhs","heart defect","heart warrior","hypoplastic left heart",
    # Muscle / Spine
    "spina bifida","sma","spinal muscular atrophy","vacterl","eds","ehlers-danlos",
    "marfan","osteogenesis imperfecta","skeletal dysplasia","achondroplasia",
    # Feeding / GI / Lung
    "trach","tracheostomy","ventilator","vent dependent","g-tube","gtube","feeding tube",
    "nicu","preemie","premature","short bowel syndrome","short bowel","hirschsprung",
    "gastroschisis","biliary atresia","cdh","diaphragmatic hernia",
    "pulmonary hypertension","cleft palate","cleft lip",
    # Cancer
    "cancer","leukemia","tumor","chemotherapy","chemo","neuroblastoma",
    "medulloblastoma","retinoblastoma",
    # Immune / Metabolic
    "t1d","type 1 diabetes","type1","juvenile diabetes","cystic fibrosis","cf warrior","cfmom",
    "sickle cell","eoe","eosinophilic","autoimmune","mast cell",
    # Autism / Developmental
    "autism","asd","nonverbal",
    # General
    "rare disease","rare condition","rare syndrome","undiagnosed",
    "medically complex","medically fragile","medically complicated",
    "special needs","complex medical","medical mom","medical parent",
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

def is_english(text):
    if not text:
        return True
    ascii_count = sum(1 for c in text if ord(c) < 128)
    return ascii_count / len(text) > 0.8

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

# ── Connect to sheet ───────────────────────────────────────────────────────────
creds = Credentials.from_service_account_file(CREDS_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets"])
gc = gspread.authorize(creds)
ws = gc.open_by_key(SHEET_ID).worksheet(TAB_NAME)

all_rows = ws.get_all_values()
existing_handles = set(r[0].strip().lstrip("@").lower() for r in all_rows[1:] if r[0].strip())
print(f"Existing handles in sheet: {len(existing_handles)}")

client = ApifyClient(APIFY_TOKEN)

# ── Step 1: Scrape followers ───────────────────────────────────────────────────
if os.path.exists(SAVE_FILE):
    print(f"[1] Loading saved followers from {SAVE_FILE}...")
    with open(SAVE_FILE) as f:
        followers_data = json.load(f)
    print(f"  Loaded {len(followers_data)} saved followers")
else:
    print(f"\n[1] Scraping up to {args.limit} followers of {ACCOUNT_URL}...")
    try:
        run = client.actor("louisdeconinck/instagram-followers-scraper").call(run_input={
            "usernames":    [account_handle],
            "resultsLimit": args.limit,
        })
        followers_data = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"  Scraped {len(followers_data)} followers")
        os.makedirs("outputs", exist_ok=True)
        with open(SAVE_FILE, "w") as f:
            json.dump(followers_data, f)
        print(f"  Saved to {SAVE_FILE}")
    except Exception as e:
        print(f"ERROR scraping followers: {e}")
        exit(1)

# ── Step 2: Filter new unique handles ─────────────────────────────────────────
print(f"\n[2] Filtering new handles...")
candidates = []
seen = set(existing_handles)
for item in followers_data:
    handle = (item.get("username") or "").lower().lstrip("@")
    if not handle or handle in seen:
        continue
    bio = item.get("biography") or ""
    if not is_english(bio):
        continue
    seen.add(handle)
    candidates.append({
        "handle":   handle,
        "ig_link":  f"https://www.instagram.com/{handle}/",
        "display":  item.get("fullName") or "",
        "bio":      bio,
        "followers": item.get("followersCount") or 0,
        "posts":    item.get("postsCount") or 0,
        "is_biz":   item.get("isBusinessAccount") or False,
        "ig_cat":   item.get("businessCategoryName") or "",
    })
print(f"  New unique candidates: {len(candidates)}")

# ── Step 3: Score ──────────────────────────────────────────────────────────────
print(f"\n[3] Scoring {len(candidates)} candidates...")
passed = []
dist = {"pass": 0, "fail": 0}
for acc in candidates:
    sc = score_account(acc["handle"], acc["display"], acc["bio"],
                       acc["followers"], acc["posts"], acc["is_biz"], acc["ig_cat"])
    if sc >= PASS_SCORE:
        passed.append([
            acc["handle"],
            acc["ig_link"],
            "Medically Complex (General)",
            f"followers:{account_handle}",
            acc["display"],
            "", "", ""
        ])
        dist["pass"] += 1
    else:
        dist["fail"] += 1

print(f"  Passed: {dist['pass']}")
print(f"  Failed: {dist['fail']}")

if not passed:
    print("No accounts passed scoring.")
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)
    exit(0)

# ── Step 4: Insert at specified row (push existing rows down) ──────────────────
print(f"\n[4] Inserting {len(passed)} accounts at row {args.insert_row}...")
ws.insert_rows(passed, row=args.insert_row, value_input_option="USER_ENTERED")
print(f"  Inserted rows {args.insert_row}-{args.insert_row + len(passed) - 1}")
print(f"  All rows below pushed down by {len(passed)}")

if os.path.exists(SAVE_FILE):
    os.remove(SAVE_FILE)
    print(f"  Save file cleaned up.")

print(f"\n=== DONE ===")
print(f"  Followers scraped:   {len(followers_data)}")
print(f"  New candidates:      {len(candidates)}")
print(f"  Passed scoring:      {len(passed)}")
print(f"  Inserted at row:     {args.insert_row}")
