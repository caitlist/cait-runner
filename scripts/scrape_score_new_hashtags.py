"""
scrape_score_new_hashtags.py
-----------------------------
Scrapes a given list of hashtags, scores new accounts not already in the sheet,
and appends passing ones to the bottom (never touches rows 1-298 or existing scored rows).

Usage:
  python scripts/scrape_score_new_hashtags.py --batch 1   # Rare Syndromes A+B (34 tags)
  python scripts/scrape_score_new_hashtags.py --batch 2   # Condition-Specific (32 tags)
  python scripts/scrape_score_new_hashtags.py --batch 3   # Broad/General (21 tags)
"""

import os, re, time, math, sys, argparse, json
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
POSTS_PER_TAG = 20

# ── BATCH 1: Rare Syndromes (34 tags) — run first, highest priority ────────────
BATCH_1 = [
    # Existing rare syndromes
    "cdkl5", "rettsyndrome", "angelmansyndrome", "dup15q", "dravetsyndrome",
    "lissencephaly", "foxg1", "tuberoussclerosis", "sturgeweber",
    "kabukisyndrome", "noonansyndrome", "praderwillisyndrome", "williamssyndrome",
    "chargesyndrome", "battendisease", "edsmom", "fragilexmom",
    "sicklecellmom", "hydrocephalusmom", "smamom", "vacterl",
    "corneliadelange", "chiarimom", "downsyndromemom",
    # New rare syndromes
    "22qdeletion", "phelanmcdermid", "hlhsmom", "cdhmom",
    "gastroschisissurvivor", "oimom", "mitomom", "pkumom",
    "biliarymom", "cleftmom", "digeorgesyndrome",
]

# ── BATCH 2: Condition-Specific (32 tags) — CHD, Epilepsy, CP, Cancer, NICU ───
BATCH_2 = [
    # CHD / Heart
    "chdmom", "heartmom", "chdwarrior", "heartbaby", "heartwarrior",
    # Epilepsy
    "epilepsymom", "epilepsyfamily", "seizuremom",
    # Cerebral Palsy
    "cpmom", "cerebralpalsymom",
    # Pediatric Cancer
    "childhoodcancermom", "cancerwarrior", "pediatriccancermom",
    # Spina Bifida
    "spinabifidamom", "spinabifidawarrior",
    # Rare Disease general
    "rarediseasemom", "rarediseasewarrior",
    # Cystic Fibrosis / T1D
    "cfmom", "t1dmom",
    # Respiratory / Lung
    "oxygenbabies", "chroniclungdisease", "bpdpreemie", "preemiemom",
    # G-tube / Trach / Feeding / NICU
    "tubiemom", "trachmom", "ventilatormom", "feedingtube", "gbutton",
    "nicuparent", "nicumom", "nicugrad", "medicallycomplexchild",
]

# ── BATCH 3: Broad/General (21 tags) — only run if more accounts needed ────────
BATCH_3 = [
    # General Medical Mom
    "medicalmom", "medicalmomlife",
    # Special Needs / Autism
    "specialneedsmom", "autismmom",
    # Allergy / Immune
    "foodallergymom", "allergyfamily", "eczemachild",
    "mastcellactivation", "autoimmunechild",
    # New broad rare
    "pulmonaryhypertensionmom", "shortbowelsyndrome", "hirschsprungsdisease",
    "marfanmom", "sotos", "apert", "treachercollins",
    "leighsyndrome", "mucopolysaccharidosis", "metabolicdisordermom",
    "craniosynostosissurvivor", "metabolicdiseasemom",
]

BATCH_MAP = {1: BATCH_1, 2: BATCH_2, 3: BATCH_3}

parser = argparse.ArgumentParser()
parser.add_argument("--batch", type=int, choices=[1, 2, 3], required=True,
                    help="Which batch to run: 1=Rare Syndromes, 2=Condition-Specific, 3=Broad/General")
args = parser.parse_args()

HASHTAGS_TO_SCRAPE = BATCH_MAP[args.batch]
SAVE_FILE = f"outputs/batch{args.batch}_candidates.json"
print(f"\n=== BATCH {args.batch} — {len(HASHTAGS_TO_SCRAPE)} hashtags ===\n")

MIN_FOLLOWERS = 0  # No follower minimum — all active accounts qualify

DIAGNOSIS_KEYWORDS = [
    # ── Trisomy / Chromosomal ──────────────────────────────────────────────────
    "trisomy","trisomy13","trisomy18","trisomy21","down syndrome","downs syndrome",
    "edwards syndrome","patau syndrome","22q","22q deletion","digeorge",
    "phelan-mcdermid","phelan mcdermid","dup15q","angelman","angelman syndrome",
    "williams syndrome","noonan syndrome","kabuki syndrome","cornelia de lange",
    "prader-willi","prader willi","charge syndrome","fragile x","fragilex",
    # ── Epilepsy / Seizure ────────────────────────────────────────────────────
    "epilepsy","seizure","dravet","cdkl5","infantile spasm","west syndrome",
    "lennox-gastaut","rett syndrome","rett","foxg1","lissencephaly",
    # ── Brain / Neurological ──────────────────────────────────────────────────
    "cerebral palsy","cp warrior","cpmom","hydrocephalus","shunt","chiari",
    "tuberous sclerosis","sturge-weber","sturge weber","batten disease","batten",
    "leigh syndrome","mitochondrial","mito","metabolic disorder","metabolic disease",
    "pku","phenylketonuria","mucopolysaccharidosis","mps","sotos","apert",
    "treacher collins","craniosynostosis",
    # ── Heart / CHD ───────────────────────────────────────────────────────────
    "chd","congenital heart","hlhs","heart defect","heart warrior","hypoplastic left heart",
    # ── Muscle / Spine ────────────────────────────────────────────────────────
    "spina bifida","sma","spinal muscular atrophy","vacterl","eds","ehlers-danlos",
    "marfan","osteogenesis imperfecta","skeletal dysplasia","achondroplasia",
    # ── Feeding / GI / Lung ───────────────────────────────────────────────────
    "trach","tracheostomy","ventilator","vent dependent","g-tube","gtube","feeding tube",
    "nicu","preemie","premature","short bowel syndrome","short bowel","hirschsprung",
    "gastroschisis","biliary atresia","cdh","diaphragmatic hernia",
    "pulmonary hypertension","cleft palate","cleft lip",
    # ── Cancer ────────────────────────────────────────────────────────────────
    "cancer","leukemia","tumor","chemotherapy","chemo","neuroblastoma",
    "medulloblastoma","retinoblastoma",
    # ── Immune / Metabolic ────────────────────────────────────────────────────
    "t1d","type 1 diabetes","type1","juvenile diabetes","cystic fibrosis","cf warrior","cfmom",
    "sickle cell","eoe","eosinophilic","autoimmune","mast cell",
    # ── Autism / Developmental ────────────────────────────────────────────────
    "autism","asd","nonverbal",
    # ── General ───────────────────────────────────────────────────────────────
    "rare disease","rare condition","rare syndrome","undiagnosed",
    "medically complex","medically fragile","medically complicated",
    "special needs","complex medical",
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

def is_english(text):
    if not text:
        return True
    ascii_count = sum(1 for c in text if ord(c) < 128)
    return ascii_count / len(text) > 0.8

def assign_category(hashtag):
    h = hashtag.lower()
    if any(k in h for k in ["epilepsy","seizure","dravet","infantilespasm"]):
        return "Epilepsy / Seizure Disorders"
    if any(k in h for k in ["trach","gtube","feedingtube","ventdepend","tracheal","tubie","gbutton"]):
        return "G-tube / Trach / Feeding Tube"
    if any(k in h for k in ["chdmom","hlhs","heartmom","heartwarrior","heartbaby","chdwarrior"]):
        return "CHD (Congenital Heart)"
    if any(k in h for k in ["hydrocephalus","shunt"]):
        return "Hydrocephalus"
    if any(k in h for k in ["mito","mitomom","metabolic","leigh","trisomy","pfeiffer","rubinstein","raredisease","pku","biliary","digeorge","phelan","22q","fragile","dup15","foxg1","lissencephaly","kabuki","noonan","prader","williams","charge","batten","edsmom","sma","vacterl","corneliadelange","chiari","hlhsmom","cdhmom","oi","cleft","gastroschisis","sotos","apert","treacher","mucopolysaccharidosis"]):
        return "Rare / Mitochondrial"
    if any(k in h for k in ["nicu","preemie","premature","nicugrad"]):
        return "NICU / Preemie"
    if any(k in h for k in ["cancer","leukemia","tumor","chemo","pediatriccancer"]):
        return "Pediatric Cancer"
    if any(k in h for k in ["cerebralpalsy","cpmom"]):
        return "Cerebral Palsy"
    if any(k in h for k in ["spinabifida"]):
        return "Spina Bifida"
    if any(k in h for k in ["autism","autismmom"]):
        return "Autism / Neurodevelopmental"
    if any(k in h for k in ["downsyndrome"]):
        return "Down Syndrome"
    if any(k in h for k in ["t1d","cfmom","sicklecell"]):
        return "Chronic Condition"
    if any(k in h for k in ["allergy","eczema","mastcell","autoimmune"]):
        return "Allergy / Immune"
    if any(k in h for k in ["pulmonary","shortbowel","hirschsprung","marfan","craniosynostosis"]):
        return "Rare / Mitochondrial"
    return "Medically Complex (General)"

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

# ── Step 1: Scrape hashtags (or load from saved file if limit was hit before) ───
client = ApifyClient(APIFY_TOKEN)
new_accounts = []
seen = set(existing_handles)

if os.path.exists(SAVE_FILE):
    print(f"[1] Found saved candidates at {SAVE_FILE} — loading instead of re-scraping...")
    with open(SAVE_FILE) as f:
        new_accounts = json.load(f)
    for acc in new_accounts:
        seen.add(acc["handle"])
    print(f"  Loaded {len(new_accounts)} saved candidates")
else:
    print(f"\n[1] Scraping {len(HASHTAGS_TO_SCRAPE)} hashtags...")
    for tag in HASHTAGS_TO_SCRAPE:
        print(f"  #{tag}...", end=" ", flush=True)
        try:
            run = client.actor("apify/instagram-hashtag-scraper").call(run_input={
                "hashtags": [tag],
                "resultsLimit": POSTS_PER_TAG,
                "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
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
                display = item.get("ownerFullName") or item.get("fullName") or ""
                cat = assign_category(tag)
                new_accounts.append({
                    "handle": owner,
                    "ig_link": f"https://www.instagram.com/{owner}/",
                    "category": cat,
                    "hashtag": tag,
                    "display": display,
                })
                count += 1
            print(f"{count} new")
            # Save after every tag so progress is never lost
            os.makedirs("outputs", exist_ok=True)
            with open(SAVE_FILE, "w") as f:
                json.dump(new_accounts, f)
            time.sleep(2)
        except Exception as e:
            print(f"ERROR: {e}")
            print(f"  Partial results saved to {SAVE_FILE} ({len(new_accounts)} accounts so far)")

print(f"\n  Total new unique accounts: {len(new_accounts)}")

if not new_accounts:
    print("Nothing new to score.")
    exit(0)

# ── Step 2: Scrape profiles ────────────────────────────────────────────────────
handles = [a["handle"] for a in new_accounts]
print(f"\n[2] Scraping {len(handles)} profiles...")
BATCH_SIZE = 50
all_profiles = {}
total_batches = math.ceil(len(handles) / BATCH_SIZE)
for i in range(0, len(handles), BATCH_SIZE):
    batch = handles[i:i + BATCH_SIZE]
    profiles = scrape_profiles(client, batch, i // BATCH_SIZE + 1, total_batches)
    all_profiles.update(profiles)
print(f"  Profiles retrieved: {len(all_profiles)}")

# ── Step 3: Score ──────────────────────────────────────────────────────────────
print("\n[3] Scoring...")
passed = []
dist = {"pass": 0, "fail": 0, "no_profile": 0}

if len(all_profiles) == 0:
    # Profile scraping failed (Apify limit) — write all candidates directly.
    # Hashtag source is strong enough signal for specific diagnosis tags.
    print("  WARNING: No profiles retrieved — writing all candidates based on hashtag signal alone.")
    for acc in new_accounts:
        passed.append([acc["handle"], acc["ig_link"], acc["category"], acc["hashtag"],
                       acc.get("display", ""), "", "", "unscored"])
    dist["pass"] = len(passed)
else:
    for acc in new_accounts:
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
        if sc >= PASS_SCORE and followers >= MIN_FOLLOWERS:
            passed.append([acc["handle"], acc["ig_link"], acc["category"], acc["hashtag"],
                           full_name, "", "", ""])
            dist["pass"] += 1
        else:
            dist["fail"] += 1

print(f"  Passed:      {dist['pass']}")
print(f"  Failed:      {dist['fail']}")
print(f"  No profile:  {dist['no_profile']}")

# ── Step 4: Append to bottom ───────────────────────────────────────────────────
if passed:
    print(f"\n[4] Appending {len(passed)} accounts to bottom of sheet...")
    current_rows = ws.get_all_values()
    next_row = len(current_rows) + 1
    end_row = next_row + len(passed) - 1
    ws.update(f"A{next_row}:H{end_row}", passed, value_input_option="USER_ENTERED")
    print(f"  Written rows {next_row}-{end_row}")
    # Clean up save file — data is now in the sheet
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)
        print(f"  Cleaned up {SAVE_FILE}")

print(f"\n=== DONE ===")
print(f"  New accounts found:  {len(new_accounts)}")
print(f"  Passed scoring:      {len(passed)}")
print(f"  Added to sheet:      {len(passed)}")
