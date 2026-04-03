"""
scrape_hie_hashtags.py
-----------------------
Scrapes all HIE-related hashtags, scores for medical parents,
and inserts passing accounts at row 892 (pushing existing rows down).
"""
import math, time, json, os
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
POSTS_PER_TAG = 20
INSERT_ROW  = 892
SAVE_FILE   = "outputs/hie_candidates.json"

HIE_HASHTAGS = [
    "hiemom", "hiewarrior", "hieawareness", "hiestrong", "hiebaby",
    "hiefamily", "hiesurvivor", "hieparent", "hienewborn", "hiejourney",
    "hypoxicischemicencephalopathy", "hypoxicischemic", "neonatalbraininjury",
    "birthinjurymom", "birthinjuryawareness", "neonatalencephalopathy",
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
    "educational research center","community organization","advocacy organization","children hospital",
]
DIAGNOSIS_KEYWORDS = [
    "trisomy","trisomy13","trisomy18","trisomy21","down syndrome","downs syndrome",
    "edwards syndrome","patau syndrome","22q","22q deletion","digeorge",
    "phelan-mcdermid","phelan mcdermid","dup15q","angelman","angelman syndrome",
    "williams syndrome","noonan syndrome","kabuki syndrome","cornelia de lange",
    "prader-willi","prader willi","charge syndrome","fragile x","fragilex",
    "epilepsy","seizure","dravet","cdkl5","infantile spasm","west syndrome",
    "lennox-gastaut","rett syndrome","rett","foxg1","lissencephaly",
    "cerebral palsy","cp warrior","cpmom","hydrocephalus","shunt","chiari",
    "tuberous sclerosis","sturge-weber","sturge weber","batten disease","batten",
    "leigh syndrome","mitochondrial","mito","metabolic disorder","metabolic disease",
    "pku","phenylketonuria","mucopolysaccharidosis","mps","sotos","apert",
    "treacher collins","craniosynostosis","hie","hypoxic ischemic","brain injury",
    "birth injury","neonatal","encephalopathy",
    "chd","congenital heart","hlhs","heart defect","heart warrior","hypoplastic left heart",
    "spina bifida","sma","spinal muscular atrophy","vacterl","eds","ehlers-danlos",
    "marfan","osteogenesis imperfecta","skeletal dysplasia","achondroplasia",
    "trach","tracheostomy","ventilator","vent dependent","g-tube","gtube","feeding tube",
    "nicu","preemie","premature","short bowel syndrome","short bowel","hirschsprung",
    "gastroschisis","biliary atresia","cdh","diaphragmatic hernia",
    "pulmonary hypertension","cleft palate","cleft lip",
    "cancer","leukemia","tumor","chemotherapy","chemo","neuroblastoma",
    "t1d","type 1 diabetes","type1","juvenile diabetes","cystic fibrosis","cfmom",
    "sickle cell","eoe","eosinophilic","autoimmune","mast cell",
    "autism","asd","nonverbal",
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

# ── Connect ────────────────────────────────────────────────────────────────────
creds = Credentials.from_service_account_file(CREDS_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets"])
gc = gspread.authorize(creds)
ws = gc.open_by_key(SHEET_ID).worksheet(TAB_NAME)
all_rows = ws.get_all_values()
existing_handles = set(r[0].strip().lstrip("@").lower() for r in all_rows[1:] if r[0].strip())
print(f"Existing handles in sheet: {len(existing_handles)}")

client = ApifyClient(APIFY_TOKEN)

# ── Step 1: Scrape hashtags ────────────────────────────────────────────────────
if os.path.exists(SAVE_FILE):
    print(f"[1] Loading saved candidates from {SAVE_FILE}...")
    with open(SAVE_FILE) as f:
        new_accounts = json.load(f)
    print(f"  Loaded {len(new_accounts)} saved candidates")
else:
    new_accounts = []
    seen = set(existing_handles)
    print(f"\n[1] Scraping {len(HIE_HASHTAGS)} HIE hashtags ({POSTS_PER_TAG} posts each)...")
    for tag in HIE_HASHTAGS:
        print(f"  #{tag}...", end=" ", flush=True)
        try:
            run = client.actor("apify/instagram-hashtag-scraper").call(run_input={
                "hashtags":     [tag],
                "resultsLimit": POSTS_PER_TAG,
                "proxy":        {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
            })
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            count = 0
            for item in items:
                owner = (item.get("ownerUsername") or item.get("owner", {}).get("username") or "").lower().lstrip("@")
                if not owner or owner in seen:
                    continue
                caption = item.get("caption") or ""
                bio = item.get("biography") or ""
                if not is_english(caption) and not is_english(bio):
                    continue
                seen.add(owner)
                new_accounts.append({
                    "handle":  owner,
                    "ig_link": f"https://www.instagram.com/{owner}/",
                    "category": "HIE / Brain Injury",
                    "hashtag": tag,
                    "display": item.get("ownerFullName") or "",
                })
                count += 1
            print(f"{count} new")
            os.makedirs("outputs", exist_ok=True)
            with open(SAVE_FILE, "w") as f:
                json.dump(new_accounts, f)
            time.sleep(2)
        except Exception as e:
            print(f"ERROR: {e}")

print(f"\n  Total candidates: {len(new_accounts)}")
if not new_accounts:
    print("Nothing found.")
    exit(0)

# ── Step 2: Scrape profiles ────────────────────────────────────────────────────
handles = [a["handle"] for a in new_accounts]
print(f"\n[2] Scraping {len(handles)} profiles...")
BATCH_SIZE = 50
all_profiles = {}
total_batches = math.ceil(len(handles) / BATCH_SIZE)
for i in range(0, len(handles), BATCH_SIZE):
    batch = handles[i:i+BATCH_SIZE]
    urls = [f"https://www.instagram.com/{h}/" for h in batch]
    print(f"  Batch {i//BATCH_SIZE+1}/{total_batches}...", end=" ", flush=True)
    try:
        run = client.actor("apify/instagram-scraper").call(run_input={
            "directUrls":   urls,
            "resultsType":  "details",
            "resultsLimit": len(batch),
            "proxy":        {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
        })
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        for item in items:
            h = (item.get("username") or "").lower().lstrip("@")
            if h:
                all_profiles[h] = item
        print(f"{len(items)} back")
        time.sleep(2)
    except Exception as e:
        print(f"ERROR: {e}")

print(f"  Profiles retrieved: {len(all_profiles)}")

# ── Step 3: Score ──────────────────────────────────────────────────────────────
print(f"\n[3] Scoring...")
passed = []
dist = {"pass": 0, "fail": 0, "no_profile": 0}

if len(all_profiles) == 0:
    print("  WARNING: No profiles retrieved — writing all candidates based on hashtag signal.")
    for acc in new_accounts:
        passed.append([acc["handle"], acc["ig_link"], acc["category"], acc["hashtag"], acc.get("display",""), "", "", "unscored"])
else:
    for acc in new_accounts:
        profile = all_profiles.get(acc["handle"])
        if not profile:
            dist["no_profile"] += 1
            continue
        bio       = profile.get("biography") or ""
        full_name = profile.get("fullName") or acc.get("display", "")
        followers = profile.get("followersCount") or 0
        posts     = profile.get("postsCount") or 0
        is_biz    = profile.get("isBusinessAccount") or False
        ig_cat    = profile.get("businessCategoryName") or ""
        sc = score_account(acc["handle"], full_name, bio, followers, posts, is_biz, ig_cat)
        if sc >= PASS_SCORE:
            passed.append([acc["handle"], acc["ig_link"], acc["category"], acc["hashtag"], full_name, "", "", ""])
            dist["pass"] += 1
        else:
            dist["fail"] += 1

print(f"  Passed:     {dist['pass']}")
print(f"  Failed:     {dist['fail']}")
print(f"  No profile: {dist['no_profile']}")

# ── Step 4: Insert at row 892 ──────────────────────────────────────────────────
if passed:
    print(f"\n[4] Inserting {len(passed)} accounts at row {INSERT_ROW} (pushing rows down)...")
    ws.insert_rows(passed, row=INSERT_ROW, value_input_option="USER_ENTERED")
    print(f"  Done. Rows {INSERT_ROW}-{INSERT_ROW + len(passed) - 1} inserted.")
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)

print(f"\n=== DONE ===")
print(f"  Candidates found:  {len(new_accounts)}")
print(f"  Passed scoring:    {len(passed)}")
print(f"  Inserted at row:   {INSERT_ROW}")
