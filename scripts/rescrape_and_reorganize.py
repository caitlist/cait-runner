"""
rescrape_and_reorganize.py
--------------------------
One-time script:
1. Reads Medical Mom DM Outreach sheet
2. Keeps rows 1-298 untouched (header + approved/reviewed)
3. Extracts rows 299+ as old unreviewed — separates Adult Cancer from the rest
4. Scrapes 104 hashtags discovered from #medicallycomplexkids (15 posts each)
5. Filters + deduplicates new accounts against all existing handles in sheet
6. Mixes new accounts + Adult Cancer old accounts by category rotation (diversity)
7. Writes back: row 299+ = [mixed new + adult cancer] then [old non-adult-cancer below]
"""

import os, re, json, time, datetime, random
from collections import defaultdict, Counter
import gspread
from google.oauth2.service_account import Credentials
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN  = os.environ.get("APIFY_TOKEN")
SHEET_ID     = os.environ.get("GOOGLE_SHEET_ID")
CREDS_PATH   = os.environ.get("GOOGLE_CREDS_PATH")
TAB_NAME     = "Medical Mom DM Outreach"
HEADERS      = ["Handle", "IG Profile Link", "Category", "Source Hashtag",
                "Display Name", "Name Used", "DM Status", "Notes"]
HASHTAG_ACTOR = "apify/instagram-hashtag-scraper"
KEEP_ROWS     = 298   # rows 1-298 stay untouched (row 1 = header)
POSTS_PER_TAG = 15    # "not too much"

# ── Recommended hashtags to scrape ────────────────────────────────────────────
NEW_HASHTAGS = [
    # Rare / Mitochondrial conditions
    "trisomy13", "pfeiffersyndrome", "rubinsteintaybisyndrome", "leighsyndrome",
    "metabolicdisorder", "mitocondrialdisease", "mitostrong", "mitokid",
    # Epilepsy variants
    "infantilespasms", "infantilespasmsawareness",
    # Trach / Vent
    "ventdependent", "trachbaby", "trachkids", "trachealagenesis",
    # Hydrocephalus
    "shunt",
    # CHD
    "hlhs", "chdkid",
    # Community / caregiver discovery
    "disabilityparenting", "specialneedsparenting", "rarediseseparenting", "raisingrare",
    "parentadvocate", "medicalparents", "medicalparenting",
    "caregiversupport", "caregiverlife", "caregivers",
    "medicallycomplexfamily",
]

# ── Category assignment by hashtag keyword ────────────────────────────────────
def assign_category(hashtag: str) -> str:
    h = hashtag.lower().replace("_", "")
    if any(k in h for k in ["epilepsy", "seizure", "dravet", "infantilespasm"]):
        return "Epilepsy / Seizure Disorders"
    if any(k in h for k in ["cerebralpals", "cpawareness", "cpwarrior"]):
        return "Cerebral Palsy"
    if any(k in h for k in ["nicu", "preemie", "premature"]):
        return "NICU / Preemie"
    if any(k in h for k in ["trach", "gtube", "feedingtube", "ventdepend", "tracheal"]):
        return "G-tube / Trach / Feeding Tube"
    if any(k in h for k in ["chdkid", "hlhs", "congenitalheart", "bivent", "mitralvalve"]) or h == "chd":
        return "CHD (Congenital Heart)"
    if any(k in h for k in ["spinabifida", "spina"]):
        return "Spina Bifida"
    if any(k in h for k in ["t1d", "diabetes", "type1"]):
        return "T1D / Pediatric Diabetes"
    if any(k in h for k in ["hydrocephalus", "shunt", "pialsynangiosis"]):
        return "Hydrocephalus"
    if any(k in h for k in ["eoe", "eosinophilic"]):
        return "EoE / Pediatric Feeding Disorders"
    if any(k in h for k in ["mito", "metabolic", "leigh", "trisomy", "pfeiffer",
                              "rubinstein", "raredisease", "raredisese", "raisingrare"]):
        return "Rare Disease"
    if "downsyndrome" in h or h == "down":
        return "Rare Disease"
    return "Medically Complex (General)"

# ── English detection ─────────────────────────────────────────────────────────
def is_english(text: str) -> bool:
    if not text:
        return True
    ascii_count = sum(1 for c in text if ord(c) < 128)
    return ascii_count / max(len(text), 1) > 0.7

# ── Extract first name ────────────────────────────────────────────────────────
def extract_first_name(display_name: str, username: str) -> str:
    skip = {"brave","journey","warrior","hope","grace","faith","life","world",
            "story","love","heart","mama","mommy","mom","mum","momma","the",
            "our","my","little","baby","tiny","strong","fight","fighting",
            "living","raising","team"}
    if display_name:
        cleaned = re.sub(r"[^\w\s\-']", "", display_name).strip()
        parts = cleaned.split()
        if parts and len(parts[0]) >= 2:
            c = parts[0]
            if not (c.isupper() and len(c) <= 4) and c.lower() not in skip:
                return c.title()
    name = re.sub(r"[_\d]", " ", username or "").strip().split()
    return name[0].title() if name and len(name[0]) >= 2 else "there"

# ── Scrape one hashtag ────────────────────────────────────────────────────────
def scrape_hashtag(client, hashtag, limit=15):
    tag = hashtag.lstrip("#").strip()
    print(f"  Scraping #{tag}...", end=" ", flush=True)
    try:
        run = client.actor(HASHTAG_ACTOR).call(run_input={
            "hashtags": [tag],
            "resultsLimit": limit,
            "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
        })
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"{len(items)} posts")
        time.sleep(1)
        return items
    except Exception as e:
        print(f"ERROR: {e}")
        return []

# ── Extract accounts from scraped posts ───────────────────────────────────────
def extract_accounts(items, hashtag, seen_handles):
    category = assign_category(hashtag)
    accounts = []
    for item in items:
        handle = (item.get("ownerUsername") or item.get("username") or "").strip().lower()
        if not handle or handle in seen_handles:
            continue
        display = item.get("ownerFullName") or item.get("fullName") or ""
        bio     = item.get("biography") or ""
        caption = item.get("caption") or ""
        # English filter
        if not is_english(caption) and not is_english(bio):
            continue
        seen_handles.add(handle)
        name_used = extract_first_name(display, handle)
        accounts.append({
            "date":     datetime.date.today().strftime("%Y-%m-%d"),
            "handle":   "@" + handle,
            "ig_link":  f"https://www.instagram.com/{handle}/",
            "category": category,
            "hashtag":  hashtag,
            "display":  display,
            "name_used": name_used,
            "dm_status": "",
            "notes":    "",
        })
    return accounts

# ── Round-robin mix by category ───────────────────────────────────────────────
def mix_by_category(accounts):
    by_cat = defaultdict(list)
    for acc in accounts:
        by_cat[acc["category"]].append(acc)
    cats = list(by_cat.keys())
    random.shuffle(cats)
    result = []
    while any(by_cat[c] for c in cats):
        for cat in cats:
            if by_cat[cat]:
                result.append(by_cat[cat].pop(0))
    return result

# ── Google Sheets ─────────────────────────────────────────────────────────────
def make_gc():
    creds = Credentials.from_service_account_file(
        CREDS_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds)

def row_to_dict(row, hi):
    def g(col):
        i = hi.get(col)
        return row[i].strip() if i is not None and i < len(row) else ""
    return {
        "date":     g("Date"),
        "handle":   g("Handle"),
        "ig_link":  g("IG Profile Link"),
        "category": g("Category"),
        "hashtag":  g("Source Hashtag"),
        "display":  g("Display Name"),
        "name_used":g("Name Used"),
        "dm_status":g("DM Status"),
        "notes":    g("Notes"),
    }

def dict_to_row(d):
    return [d["handle"], d["ig_link"], d["category"], d["hashtag"],
            d["display"], d["name_used"], d["dm_status"], d["notes"]]

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=== RESCRAPE + REORGANIZE ===\n")

    # 1. Read sheet
    print("[1] Reading sheet...")
    gc = make_gc()
    ss = gc.open_by_key(SHEET_ID)
    ws = ss.worksheet(TAB_NAME)
    all_rows = ws.get_all_values()
    if not all_rows:
        print("Sheet is empty. Aborting.")
        return

    hdrs = [h.strip() for h in all_rows[0]]
    hi   = {h: i for i, h in enumerate(hdrs)}
    data_rows = all_rows[1:]  # rows 2+ (0-indexed: rows[0] = headers)

    # Rows to keep: data_rows[0..KEEP_ROWS-2] = rows 2..298
    keep_data = data_rows[:KEEP_ROWS - 1]        # rows 2-298 (297 rows)
    old_data  = data_rows[KEEP_ROWS - 1:]         # rows 299+ (old unreviewed)

    print(f"  Kept rows 1-{KEEP_ROWS}: {len(keep_data)} data rows")
    print(f"  Old unreviewed rows 299+: {len(old_data)} rows")

    # Build seen handles set (all handles already in sheet)
    seen_handles = set()
    for row in data_rows:
        h = hi.get("Handle")
        if h is not None and h < len(row):
            handle = row[h].strip().lower().lstrip("@")
            if handle:
                seen_handles.add(handle)

    print(f"  Existing handles in sheet: {len(seen_handles)}")

    # 2. Separate old rows into Adult Cancer vs others
    adult_cancer_rows = []
    other_old_rows    = []
    cat_col = hi.get("Category")
    for row in old_data:
        cat = row[cat_col].strip() if cat_col is not None and cat_col < len(row) else ""
        if cat == "Adult Cancer":
            adult_cancer_rows.append(row)
        else:
            other_old_rows.append(row)

    print(f"  Old Adult Cancer rows: {len(adult_cancer_rows)}")
    print(f"  Other old unreviewed rows: {len(other_old_rows)}")

    # Convert adult cancer rows to dicts for mixing
    adult_cancer_dicts = [row_to_dict(row, hi) for row in adult_cancer_rows]

    # 3. Scrape all hashtags
    print(f"\n[2] Scraping {len(NEW_HASHTAGS)} hashtags ({POSTS_PER_TAG} posts each)...")
    client = ApifyClient(APIFY_TOKEN)
    all_items = []
    for tag in NEW_HASHTAGS:
        items = scrape_hashtag(client, tag, POSTS_PER_TAG)
        all_items.extend(items)

    print(f"\n  Total posts scraped: {len(all_items)}")

    # 4. Extract new unique accounts
    print("\n[3] Extracting new accounts...")
    new_accounts = []
    # Track per-hashtag to assign correct category
    items_by_tag = defaultdict(list)
    for item in all_items:
        # We don't have the source tag on the item directly, so re-process per tag
        pass

    # Re-scrape result items don't carry hashtag — re-extract per tag
    # Instead: extract during scrape (re-do with hashtag tracking)
    new_seen = set(seen_handles)  # don't add same handle twice
    new_accounts_by_tag = defaultdict(list)

    # Re-run extraction — we already scraped, rebuild from all_items
    # items have no guaranteed hashtag field, so assign based on order isn't reliable
    # Use caption hashtag matching as proxy for category
    for item in all_items:
        handle = (item.get("ownerUsername") or item.get("username") or "").strip().lower()
        if not handle or handle in new_seen:
            continue
        display = item.get("ownerFullName") or item.get("fullName") or ""
        bio     = item.get("biography") or ""
        caption = item.get("caption") or ""
        if not is_english(caption) and not is_english(bio):
            continue
        # Assign category from caption hashtags
        tags_in_post = re.findall(r"#(\w+)", (caption + " " + bio).lower())
        category = "Medically Complex (General)"
        for t in tags_in_post:
            cat = assign_category(t)
            if cat != "Medically Complex (General)":
                category = cat
                break
        new_seen.add(handle)
        name_used = extract_first_name(display, handle)
        new_accounts.append({
            "handle":   "@" + handle,
            "ig_link":  f"https://www.instagram.com/{handle}/",
            "category": category,
            "hashtag":  "medicallycomplexkids-discovery",
            "display":  display,
            "name_used": name_used,
            "dm_status": "",
            "notes":    "",
        })

    print(f"  New unique accounts found: {len(new_accounts)}")

    # 5. Mix new accounts + Adult Cancer old accounts by category
    print("\n[4] Mixing new + Adult Cancer by category rotation...")
    to_mix = new_accounts + adult_cancer_dicts
    mixed = mix_by_category(to_mix)
    print(f"  Mixed batch size: {len(mixed)}")

    # 6. Build final row order: mixed first, then old others
    final_rows = [dict_to_row(d) for d in mixed]
    final_rows += other_old_rows  # raw rows, already in sheet format

    print(f"\n[5] Writing {len(final_rows)} rows to sheet starting at row 299...")

    # Clear rows 299+ (up to a large number)
    ws.batch_clear([f"A299:H20000"])
    time.sleep(2)

    # Write in batches of 500
    if final_rows:
        batch_size = 500
        for i in range(0, len(final_rows), batch_size):
            batch = final_rows[i:i + batch_size]
            start_row = 299 + i
            end_row   = start_row + len(batch) - 1
            ws.update(f"A{start_row}:H{end_row}", batch, value_input_option="USER_ENTERED")
            print(f"  Written rows {start_row}-{end_row}")
            time.sleep(1)

    print(f"\n=== DONE ===")
    print(f"  Row 299+: {len(mixed)} mixed (new + Adult Cancer)")
    print(f"  Below:    {len(other_old_rows)} old unreviewed accounts")
    print(f"  Total new accounts added: {len(new_accounts)}")

if __name__ == "__main__":
    main()
