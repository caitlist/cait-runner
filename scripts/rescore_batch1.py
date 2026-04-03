"""
rescore_batch1.py
-----------------
Rescores the 212 batch 1 accounts already in the sheet using updated DIAGNOSIS_KEYWORDS.
Prints pass/fail counts. Does not modify the sheet.
"""
import json, math, time
from apify_client import ApifyClient
from dotenv import dotenv_values

vals = dotenv_values("c:/Users/lamch/Downloads/Caitlist/.env")
APIFY_TOKEN = vals["APIFY_TOKEN"]

with open("outputs/batch1_candidates.json") as f:
    accounts = json.load(f)

print(f"Rescoring {len(accounts)} accounts with updated keywords...")

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
    "treacher collins","craniosynostosis",
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

client = ApifyClient(APIFY_TOKEN)
BATCH_SIZE = 50
handles = [a["handle"] for a in accounts]
all_profiles = {}
total_batches = math.ceil(len(handles) / BATCH_SIZE)

print(f"Scraping {len(handles)} profiles in {total_batches} batches...")
for i in range(0, len(handles), BATCH_SIZE):
    batch = handles[i:i+BATCH_SIZE]
    urls = [f"https://www.instagram.com/{h}/" for h in batch]
    print(f"  Batch {i//BATCH_SIZE+1}/{total_batches}...", end=" ", flush=True)
    try:
        run = client.actor("apify/instagram-scraper").call(run_input={
            "directUrls": urls,
            "resultsType": "details",
            "resultsLimit": len(batch),
            "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
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

print(f"Profiles retrieved: {len(all_profiles)}")

passed, failed = [], []
for acc in accounts:
    profile = all_profiles.get(acc["handle"])
    if not profile:
        passed.append(acc["handle"])  # keep if Apify didn't return it
        continue
    bio       = profile.get("biography") or ""
    full_name = profile.get("fullName") or acc.get("display", "")
    followers = profile.get("followersCount") or 0
    posts     = profile.get("postsCount") or 0
    is_biz    = profile.get("isBusinessAccount") or False
    ig_cat    = profile.get("businessCategoryName") or ""
    sc = score_account(acc["handle"], full_name, bio, followers, posts, is_biz, ig_cat)
    if sc >= 15:
        passed.append(acc["handle"])
    else:
        failed.append((acc["handle"], sc, bio[:80]))

print(f"\n=== RESCORE RESULTS ===")
print(f"Passed: {len(passed)}/{len(accounts)}")
print(f"Failed: {len(failed)}")
if failed:
    print("\nFailed accounts (handle | score | bio preview):")
    for h, sc, bio in failed:
        print(f"  {h} | score={sc} | {bio!r}")

import os
os.remove("outputs/batch1_candidates.json")
print("\nSave file cleaned up.")
