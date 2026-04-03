"""
scrape_follower_network.py
---------------------------
Discovers medical parents via follower network scraping.

Pipeline:
  Phase 1 — Scrape #medicalmom hashtag → collect top posters by follower count
             (these become the seed accounts)
  Phase 2 — Scrape followers of each seed (up to MAX_FOLLOWERS_PER_SEED each)
             Processes seed by seed — stops if budget limit reached
  Phase 3 — Deduplicate against existing sheet handles + across seeds
  Phase 4 — Score each handle via Apify profile scraper (PASS_SCORE=15)
  Phase 5 — INSERT passing accounts at row INSERT_ROW, pushing existing rows down
             Source column = "followers:@seedhandle" so Cherwin knows origin

Budget: BUDGET_USD = 5.00 — script stops before exceeding this limit.
        Checked after every Apify actor call.

Run:
  python scripts/scrape_follower_network.py
"""

import re, time, math
from collections import Counter
import gspread
from google.oauth2.service_account import Credentials
from apify_client import ApifyClient
from dotenv import dotenv_values

vals = dotenv_values("c:/Users/lamch/Downloads/Caitlist/.env")
APIFY_TOKEN = vals.get("APIFY_TOKEN")
SHEET_ID    = vals.get("GOOGLE_SHEET_ID")
CREDS_PATH  = vals.get("GOOGLE_CREDS_PATH")

TAB_NAME               = "Medical Mom DM Outreach"
PASS_SCORE             = 15
MIN_FOLLOWERS          = 0
BATCH_SIZE             = 50
INSERT_ROW             = 512   # New rows inserted here, pushing rows 512+ down
BUDGET_USD             = 5.00  # Hard stop — script will not exceed this
HASHTAG_POSTS_LIMIT    = 200   # Posts to scrape from #medicalmom to find seeds
TOP_FREQ_CANDIDATES    = 30    # Profile-check this many frequent posters to rank by followers
TOP_N_SEEDS            = 5     # Use top N auto-discovered accounts as seeds
POSTS_PER_SEED         = 10    # Recent posts to pull from each seed
COMMENTS_PER_POST      = 100   # Commenters to extract per post
# 5 seeds × 10 posts × 100 comments = up to 5,000 handles (more targeted than followers)

# ── Manual seeds — always included, merged with auto-discovered seeds ──────────
# Add known large medical mom accounts here
MANUAL_SEEDS = [
    "risewithraedynhayz",
]

# ── Scoring constants ──────────────────────────────────────────────────────────
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


# ── Budget tracker ─────────────────────────────────────────────────────────────
total_spent = 0.0

def track_spend(run, label):
    """Read cost from Apify run result and add to total. Returns cost of this run."""
    global total_spent
    cost = 0.0
    try:
        usage = run.get("usageTotalUsd") or 0.0
        if usage == 0:
            # Fallback: estimate from compute units (1 CU ≈ $0.004)
            cu = (run.get("stats") or {}).get("computeUnits", 0)
            usage = round(cu * 0.004, 4)
        cost = float(usage)
    except Exception:
        pass
    total_spent += cost
    print(f"  [{label}] Cost: ${cost:.3f} | Total spent: ${total_spent:.3f} / ${BUDGET_USD:.2f}")
    return cost

def budget_ok(reserve=0.50):
    """Return True if there's still budget remaining (with reserve for next call)."""
    return total_spent + reserve < BUDGET_USD

def budget_abort(label):
    print(f"\n  !! Budget limit ${BUDGET_USD:.2f} approached after '{label}' — stopping early.")
    print(f"  !! Total spent: ${total_spent:.3f}")


# ── Scoring ────────────────────────────────────────────────────────────────────
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
    urls = list(dict.fromkeys(
        f"https://www.instagram.com/{h.lstrip('@')}/" for h in handles
    ))
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
        track_spend(run, f"profile-batch-{batch_num}")
        time.sleep(2)
        return result, run
    except Exception as e:
        print(f"ERROR: {e}")
        return {}, {}


# ── Connect to sheet ───────────────────────────────────────────────────────────
print("Connecting to Google Sheet...")
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

client = ApifyClient(APIFY_TOKEN)

# ── Phase 1: Scrape #medicalmom hashtag → find seed accounts ──────────────────
print(f"\n[1] Scraping #medicalmom ({HASHTAG_POSTS_LIMIT} posts) to find top accounts...")
poster_counts = {}

try:
    run = client.actor("apify/instagram-hashtag-scraper").call(run_input={
        "hashtags":     ["medicalmom"],
        "resultsLimit": HASHTAG_POSTS_LIMIT,
        "proxy":        {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
    })
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    track_spend(run, "hashtag-medicalmom")
    print(f"  Posts retrieved: {len(items)}")
    for item in items:
        owner = (item.get("ownerUsername") or item.get("owner", {}).get("username") or "").lower().lstrip("@")
        if owner:
            poster_counts[owner] = poster_counts.get(owner, 0) + 1
    print(f"  Unique posters found: {len(poster_counts)}")
except Exception as e:
    print(f"  ERROR scraping hashtag: {e}")
    exit(1)

if not poster_counts:
    print("No posters found. Exiting.")
    exit(1)

if not budget_ok():
    budget_abort("hashtag scrape")
    exit(1)

# Get profiles of most frequent posters to rank by follower count
top_by_freq = sorted(poster_counts.keys(), key=lambda h: poster_counts[h], reverse=True)[:TOP_FREQ_CANDIDATES]
print(f"\n  Getting profiles for top {len(top_by_freq)} frequent posters (to rank by followers)...")

seed_profiles = {}
total_seed_batches = math.ceil(len(top_by_freq) / BATCH_SIZE)
for i in range(0, len(top_by_freq), BATCH_SIZE):
    batch = top_by_freq[i:i + BATCH_SIZE]
    profiles, run = scrape_profiles(client, batch, i // BATCH_SIZE + 1, total_seed_batches)
    seed_profiles.update(profiles)
    if not budget_ok():
        budget_abort("seed profile scrape")
        break

# Rank seeds by follower count
ranked_seeds = sorted(
    [(h, seed_profiles.get(h, {}).get("followersCount", 0)) for h in top_by_freq if h in seed_profiles],
    key=lambda x: x[1],
    reverse=True
)[:TOP_N_SEEDS]

print(f"\n  Selected seeds (top {TOP_N_SEEDS} by followers):")
for handle, fc in ranked_seeds:
    print(f"    @{handle} — {fc:,} followers")

seed_handles = [h for h, _ in ranked_seeds]

# Merge manual seeds (skip if already in auto list)
for ms in MANUAL_SEEDS:
    ms = ms.lower().lstrip("@")
    if ms not in seed_handles:
        seed_handles.append(ms)
        print(f"    @{ms} — manual seed (added)")

print(f"  Total seeds: {len(seed_handles)}")

# ── Phase 2: Scrape commenters on seed accounts' posts ────────────────────────
# People who comment on medical mom content are more likely to be medical parents
# than passive followers. 5 seeds × 10 posts × 100 comments = ~5,000 handles.
print(f"\n[2] Scraping commenters on seed posts ({POSTS_PER_SEED} posts × {COMMENTS_PER_POST} comments each, ${BUDGET_USD - total_spent:.2f} remaining)...")
follower_source = {}  # commenter_handle -> seed_handle
seen = set(existing_handles)
seeds_completed = 0

for seed in seed_handles:
    if not budget_ok(reserve=1.00):  # Keep $1 reserve for scoring phase
        budget_abort(f"before scraping @{seed}")
        break

    # Step A: get recent post URLs for this seed
    print(f"  @{seed} — fetching {POSTS_PER_SEED} posts...", end=" ", flush=True)
    try:
        run = client.actor("apify/instagram-scraper").call(run_input={
            "directUrls":   [f"https://www.instagram.com/{seed}/"],
            "resultsType":  "posts",
            "resultsLimit": POSTS_PER_SEED,
            "proxy":        {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
        })
        posts = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        track_spend(run, f"posts-@{seed}")
        post_urls = [p.get("url") or p.get("shortCode") and f"https://www.instagram.com/p/{p['shortCode']}/"
                     for p in posts if p.get("url") or p.get("shortCode")]
        post_urls = [u for u in post_urls if u]
        print(f"{len(post_urls)} posts")
    except Exception as e:
        print(f"ERROR fetching posts: {e}")
        continue

    if not post_urls:
        continue

    if not budget_ok(reserve=1.00):
        budget_abort(f"after posts-@{seed}")
        break

    # Step B: scrape comments on those posts
    print(f"    Scraping comments on {len(post_urls)} posts...", end=" ", flush=True)
    try:
        run = client.actor("apify/instagram-scraper").call(run_input={
            "directUrls":   post_urls,
            "resultsType":  "comments",
            "resultsLimit": COMMENTS_PER_POST,
            "proxy":        {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
        })
        comments = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        track_spend(run, f"comments-@{seed}")
        new_count = 0
        for c in comments:
            ch = (c.get("ownerUsername") or c.get("owner", {}).get("username") or "").lower().lstrip("@")
            if ch and ch not in seen and ch != seed:
                seen.add(ch)
                follower_source[ch] = seed
                new_count += 1
        print(f"{len(comments)} comments, {new_count} new unique handles")
        seeds_completed += 1
        time.sleep(3)
    except Exception as e:
        print(f"ERROR fetching comments: {e}")

print(f"\n  Seeds completed: {seeds_completed}/{len(seed_handles)}")
print(f"  Total unique new follower handles: {len(follower_source)}")

if not follower_source:
    print("No new followers found. Sheet unchanged.")
    exit(0)

# ── Phase 3: Score follower profiles ──────────────────────────────────────────
follower_handles = list(follower_source.keys())
print(f"\n[3] Scraping {len(follower_handles)} follower profiles for scoring...")
print(f"    Budget remaining: ${BUDGET_USD - total_spent:.2f}")

all_profiles = {}
total_batches = math.ceil(len(follower_handles) / BATCH_SIZE)
for i in range(0, len(follower_handles), BATCH_SIZE):
    if not budget_ok(reserve=0.10):
        budget_abort(f"scoring batch {i // BATCH_SIZE + 1}")
        print(f"  Scored {len(all_profiles)}/{len(follower_handles)} profiles before budget stop")
        break
    batch = follower_handles[i:i + BATCH_SIZE]
    profiles, run = scrape_profiles(client, batch, i // BATCH_SIZE + 1, total_batches)
    all_profiles.update(profiles)

print(f"  Profiles retrieved: {len(all_profiles)}")

if len(all_profiles) == 0:
    print("ERROR: Apify returned 0 profiles — aborting to protect sheet")
    exit(1)

# ── Phase 4: Apply scoring ────────────────────────────────────────────────────
print("\n[4] Scoring...")
passed = []
dist = {"pass": 0, "fail": 0, "no_profile": 0}

for handle, seed in follower_source.items():
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
        ig_link    = f"https://www.instagram.com/{handle}/"
        source_tag = f"followers:@{seed}"
        passed.append([handle, ig_link, "Medically Complex (General)", source_tag,
                       full_name, "", "", ""])
        dist["pass"] += 1
    else:
        dist["fail"] += 1

print(f"  Passed (verified medical parents): {dist['pass']}")
print(f"  Failed (not medical parents):      {dist['fail']}")
print(f"  No profile:                        {dist['no_profile']}")

# Debug: show score distribution for failed accounts (helps tune threshold)
if dist["pass"] == 0 and dist["fail"] > 0:
    scores = []
    for handle, seed in follower_source.items():
        profile = all_profiles.get(handle)
        if not profile:
            continue
        bio       = profile.get("biography") or ""
        full_name = profile.get("fullName") or ""
        followers = profile.get("followersCount") or 0
        posts     = profile.get("postsCount") or 0
        is_biz    = profile.get("isBusinessAccount") or False
        ig_cat    = profile.get("businessCategoryName") or ""
        sc = score_account(handle, full_name, bio, followers, posts, is_biz, ig_cat)
        scores.append((sc, handle, bio[:60]))
    scores.sort(reverse=True)
    print(f"\n  DEBUG — top 10 scores (all failed, threshold={PASS_SCORE}):")
    for sc, h, b in scores[:10]:
        print(f"    score={sc:4d}  @{h}  bio: {b!r}")

# ── Phase 5: Insert at row INSERT_ROW ─────────────────────────────────────────
if passed:
    print(f"\n[5] Inserting {len(passed)} accounts at row {INSERT_ROW} (pushing rows {INSERT_ROW}+ down)...")
    ws.insert_rows(passed, row=INSERT_ROW, value_input_option="USER_ENTERED")
    print(f"  Done. Rows {INSERT_ROW}-{INSERT_ROW + len(passed) - 1} written.")
    print(f"  Previous rows {INSERT_ROW}+ shifted down by {len(passed)}.")
else:
    print("\nNo accounts passed scoring. Sheet unchanged.")

print(f"\n=== DONE ===")
print(f"  Total Apify spend this run:        ${total_spent:.3f}")
print(f"  Budget:                            ${BUDGET_USD:.2f}")
print(f"  Seeds used:                        {seeds_completed}/{len(seed_handles)}")
print(f"  Followers collected:               {len(follower_source)}")
print(f"  Profiles scored:                   {len(all_profiles)}")
print(f"  Verified medical parents added:    {len(passed)}")
if passed:
    print(f"\n  Source breakdown:")
    sources = Counter(row[3] for row in passed)
    for src, cnt in sources.most_common():
        print(f"    {src}: {cnt} accounts")
