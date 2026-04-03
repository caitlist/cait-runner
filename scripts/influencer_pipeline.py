"""
influencer_pipeline.py
----------------------
Verifies and scores influencer accounts for CAIT Connect's launch pipeline.

Two scoring systems run side-by-side:
  - ER Score (Tiered): engagement rate % benchmarked against follower tier
  - Comment Score (Pure): absolute avg comment volume, boss-friendly metric

Output: "Influencer Pipeline" Google Sheet tab + CSV fallback

Usage:
    # Verify seed accounts (Phase 1)
    python scripts/influencer_pipeline.py --mode verify --handles kayandtayofficial sophiahillll carlinbates98

    # Verify from a file (one handle per line)
    python scripts/influencer_pipeline.py --mode verify --file inputs/seed_accounts.txt --category "Loop Giveaway Moms"

    # Dry run (no sheet write)
    python scripts/influencer_pipeline.py --mode verify --handles someaccount --dry-run
"""

import os
import re
import sys
import csv
import time
import datetime
import argparse

import gspread
from google.oauth2.service_account import Credentials
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
GOOGLE_CREDS_PATH = os.environ.get("GOOGLE_CREDS_PATH")

PROFILE_ACTOR = "apify/instagram-scraper"
TIKTOK_ACTOR = "clockworks/tiktok-scraper"

OUTPUT_TAB = "Influencer Pipeline"
OUTPUT_HEADERS = [
    "Handle", "Name", "Followers",
    "Avg Likes", "Avg Comments (real)",
    "Engagement Rate %", "ER Score", "Comment Score",
    "Macro/Micro", "Loop Giveaway History", "Platform",
    "Category", "Notes", "Active (30 days)", "USA Signal",
    "Last Verified",
]

# ── USA signals (reused from instagram_discovery.py) ─────────────────────────
USA_SIGNALS = [
    "usa", "u.s.a", "united states", "america", "american",
    "iep", "medicaid", "ssi", "ssdi", "childrens hospital",
    "alabama", "alaska", "arizona", "arkansas", "california",
    "colorado", "connecticut", "florida", "georgia", "hawaii",
    "illinois", "indiana", "kentucky", "louisiana", "maryland",
    "massachusetts", "michigan", "minnesota", "mississippi",
    "missouri", "new york", "north carolina", "ohio", "oklahoma",
    "oregon", "pennsylvania", "tennessee", "texas", "virginia",
    "washington", "wisconsin",
    " al ", " ak ", " az ", " ar ", " ca ", " co ", " ct ", " fl ",
    " ga ", " hi ", " id ", " il ", " in ", " ia ", " ks ", " ky ",
    " la ", " me ", " md ", " ma ", " mi ", " mn ", " ms ", " mo ",
    " ny ", " nc ", " oh ", " ok ", " or ", " pa ", " tn ", " tx ",
    " va ", " wa ", " wi ",
]


# ── Tiered ER thresholds ──────────────────────────────────────────────────────
ER_TIERS = [
    # (min_followers, max_followers, low_floor, high_floor)
    (500_000, 5_000_000, 0.8,  2.0),   # Macro
    (100_000,   500_000, 1.5,  3.5),   # Mid-tier
    (10_000,    100_000, 3.0,  6.0),   # Micro
]


def calculate_er(avg_likes: float, avg_comments: float, followers: int) -> float:
    if not followers:
        return 0.0
    return round((avg_likes + avg_comments) / followers * 100, 2)


def apply_er_score(er_pct: float, followers: int) -> str:
    """Return HIGH / NORMAL / LOW ROI / UNRATED based on tiered thresholds."""
    for min_f, max_f, low_floor, high_floor in ER_TIERS:
        if min_f <= followers <= max_f:
            if er_pct >= high_floor:
                return "HIGH"
            elif er_pct < low_floor:
                return "LOW ROI"
            else:
                return "NORMAL"
    # Outside defined tiers (e.g. <10k or >5M)
    if followers < 10_000:
        return "HIGH" if er_pct >= 6 else ("LOW ROI" if er_pct < 3 else "NORMAL")
    return "UNRATED"  # >5M mega accounts


def apply_comment_score(avg_comments: float) -> str:
    """Boss-facing metric: pure comment volume, no follower math."""
    if avg_comments >= 200:
        return "HIGH VALUE"
    elif avg_comments >= 50:
        return "SOLID"
    elif avg_comments >= 15:
        return "BORDERLINE"
    else:
        return "LOW"


def get_tier_label(followers: int) -> str:
    if followers >= 500_000:
        return "Macro"
    elif followers >= 100_000:
        return "Mid-tier"
    elif followers >= 10_000:
        return "Micro"
    else:
        return "Nano"


def check_usa_signal(bio: str, name: str) -> bool:
    combined = f"{bio} {name}".lower()
    return any(s in combined for s in USA_SIGNALS)


def check_active(posts: list) -> tuple[bool, str]:
    """
    Returns (is_active, last_post_str).
    Active = most recent non-pinned post within 30 days.
    """
    today = datetime.date.today()
    cutoff = today - datetime.timedelta(days=30)

    for post in posts:
        if not isinstance(post, dict):
            continue
        if post.get("isPinned") or post.get("pinned"):
            continue

        ts = post.get("timestamp") or post.get("takenAtTimestamp") or 0
        try:
            if isinstance(ts, (int, float)) and ts > 1_000_000:
                post_date = datetime.date.fromtimestamp(ts)
            elif isinstance(ts, str) and ts:
                # ISO format: "2024-01-15T12:00:00.000Z"
                post_date = datetime.date.fromisoformat(ts[:10])
            else:
                continue
            last_post_str = post_date.isoformat()
            days_ago = (today - post_date).days
            return (post_date >= cutoff), f"{last_post_str} ({days_ago}d ago)"
        except Exception:
            continue

    return False, "unknown"


def extract_post_metrics(profile: dict) -> dict:
    """
    Pull avg likes, avg comments, activity from last 10 non-pinned posts.
    Returns: {avg_likes, avg_comments, active, last_post, posts_checked,
              comment_counts, like_counts, passes_floor}
    """
    posts = profile.get("latestPosts") or profile.get("posts") or []
    comment_counts = []
    like_counts = []

    for post in posts:
        if not isinstance(post, dict):
            continue
        if post.get("isPinned") or post.get("pinned"):
            continue
        comment_counts.append(post.get("commentsCount") or 0)
        like_counts.append(post.get("likesCount") or 0)
        if len(comment_counts) >= 12:
            break

    active, last_post = check_active(posts)

    if not comment_counts:
        return {
            "avg_likes": 0, "avg_comments": 0,
            "active": False, "last_post": "no posts",
            "posts_checked": 0, "comment_counts": [],
            "like_counts": [], "passes_floor": False,
        }

    avg_comments = round(sum(comment_counts) / len(comment_counts), 1)
    avg_likes = round(sum(like_counts) / len(like_counts), 1) if like_counts else 0.0

    # Engagement floor: 7/10 posts must have ≥15 comments
    posts_with_15 = sum(1 for c in comment_counts[:10] if c >= 15)
    threshold = max(1, round(min(len(comment_counts), 10) * 0.7))
    passes_floor = posts_with_15 >= threshold

    return {
        "avg_likes": avg_likes,
        "avg_comments": avg_comments,
        "active": active,
        "last_post": last_post,
        "posts_checked": len(comment_counts),
        "comment_counts": comment_counts,
        "like_counts": like_counts,
        "passes_floor": passes_floor,
    }


def build_row(profile: dict, category: str, platform: str = "Instagram",
              loop_history: str = "Unknown") -> dict:
    """Build a complete output row from a scraped profile."""
    username = (profile.get("username") or "").lower().strip()
    full_name = profile.get("fullName") or profile.get("full_name") or ""
    followers = int(profile.get("followersCount") or profile.get("followers") or 0)
    bio = profile.get("biography") or profile.get("bio") or ""
    is_private = profile.get("isPrivate") or False

    metrics = extract_post_metrics(profile)
    avg_likes = metrics["avg_likes"]
    avg_comments = metrics["avg_comments"]
    active = metrics["active"]
    last_post = metrics["last_post"]
    passes_floor = metrics["passes_floor"]

    er_pct = calculate_er(avg_likes, avg_comments, followers)
    er_score = apply_er_score(er_pct, followers)
    comment_score = apply_comment_score(avg_comments)
    tier_label = get_tier_label(followers)
    usa = check_usa_signal(bio, full_name)

    # Notes assembly
    notes_parts = []
    if is_private:
        notes_parts.append("PRIVATE")
    if not passes_floor:
        notes_parts.append(f"engagement floor fail ({metrics['posts_checked']} posts checked)")
    if not active:
        notes_parts.append(f"INACTIVE — last post: {last_post}")
    if avg_comments >= 200:
        notes_parts.append("Top commenter — HIGH VALUE")
    if er_score == "LOW ROI" and avg_comments >= 50:
        notes_parts.append("Low ER% but strong absolute comments — worth reviewing")

    return {
        "Handle": f"@{username}",
        "Name": full_name,
        "Followers": followers,
        "Avg Likes": avg_likes,
        "Avg Comments (real)": avg_comments,
        "Engagement Rate %": er_pct,
        "ER Score": er_score,
        "Comment Score": comment_score,
        "Macro/Micro": tier_label,
        "Loop Giveaway History": loop_history,
        "Platform": platform,
        "Category": category,
        "Notes": " | ".join(notes_parts) if notes_parts else "OK",
        "Active (30 days)": "Y" if active else f"N — {last_post}",
        "USA Signal": "Y" if usa else "?",
        "Last Verified": datetime.date.today().isoformat(),
        # Internal — used for sorting/reporting, not written to sheet
        "_passes_floor": passes_floor,
        "_er_score": er_score,
        "_comment_score": comment_score,
        "_avg_comments": avg_comments,
        "_er_pct": er_pct,
    }


# ── Apify scraping ─────────────────────────────────────────────────────────────
def scrape_instagram_batch(handles: list[str]) -> list[dict]:
    """Scrape Instagram profiles via Apify with RESIDENTIAL proxies. Batch of 10."""
    client = ApifyClient(APIFY_TOKEN)
    results = []

    for i in range(0, len(handles), 10):
        batch = handles[i:i+10]
        clean = [h.lstrip("@").lower().strip() for h in batch]
        print(f"  [IG] Batch {i//10 + 1}/{(len(handles)-1)//10 + 1}: {clean}")
        try:
            run_input = {
                "directUrls": [f"https://www.instagram.com/{u}/" for u in clean],
                "resultsType": "details",
                "resultsLimit": 12,
                "proxy": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"],
                },
            }
            run = client.actor(PROFILE_ACTOR).call(run_input=run_input)
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            results.extend(items)
            print(f"  [IG] Got {len(items)} profiles back")
            time.sleep(3)
        except Exception as e:
            print(f"  [IG] Error on batch {i}: {e}")

    return results


def scrape_tiktok_batch(handles: list[str]) -> list[dict]:
    """Scrape TikTok profiles via Apify. Falls back to UNVERIFIED if actor unavailable."""
    client = ApifyClient(APIFY_TOKEN)
    results = []

    for i in range(0, len(handles), 10):
        batch = handles[i:i+10]
        clean = [h.lstrip("@").lower().strip() for h in batch]
        print(f"  [TT] Batch {i//10 + 1}: {clean}")
        try:
            run_input = {
                "profiles": [f"https://www.tiktok.com/@{u}" for u in clean],
                "resultsPerPage": 12,
                "shouldDownloadVideos": False,
                "shouldDownloadCovers": False,
            }
            run = client.actor(TIKTOK_ACTOR).call(run_input=run_input)
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            results.extend(items)
            print(f"  [TT] Got {len(items)} profiles back")
            time.sleep(2)
        except Exception as e:
            print(f"  [TT] TikTok scrape error (actor may not be rented): {e}")
            # Return stub records marked UNVERIFIED
            for h in clean:
                results.append({
                    "username": h,
                    "fullName": "",
                    "followersCount": 0,
                    "biography": "",
                    "latestPosts": [],
                    "_unverified": True,
                    "_unverified_reason": str(e),
                })

    return results


# ── Sheet writing ──────────────────────────────────────────────────────────────
def get_sheet():
    """Return the gspread worksheet for OUTPUT_TAB, creating it if needed."""
    creds = Credentials.from_service_account_file(
        GOOGLE_CREDS_PATH,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(GOOGLE_SHEET_ID)

    # Get or create the tab
    try:
        ws = sh.worksheet(OUTPUT_TAB)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=OUTPUT_TAB, rows=500, cols=len(OUTPUT_HEADERS))
        ws.append_row(OUTPUT_HEADERS, value_input_option="USER_ENTERED")
        print(f"  [sheet] Created new tab: {OUTPUT_TAB}")

    # Ensure header row exists
    existing_headers = ws.row_values(1)
    if not existing_headers or existing_headers[0] != "Handle":
        ws.insert_row(OUTPUT_HEADERS, 1, value_input_option="USER_ENTERED")

    return ws


def write_influencer_tab(rows: list[dict], dry_run: bool = False) -> dict:
    """Write rows to Influencer Pipeline tab. Dedup by handle."""
    if dry_run:
        print(f"  [dry-run] Would write {len(rows)} rows — skipping sheet write")
        return {"written": 0, "skipped": 0}

    ws = get_sheet()
    # Build set of existing handles
    existing = set()
    all_values = ws.get_all_values()
    for row in all_values[1:]:  # skip header
        if row and row[0]:
            existing.add(row[0].lower().strip())

    to_write = []
    skipped = 0
    for row in rows:
        handle = row["Handle"].lower().strip()
        if handle in existing:
            skipped += 1
            continue
        to_write.append([
            row["Handle"], row["Name"], row["Followers"],
            row["Avg Likes"], row["Avg Comments (real)"],
            row["Engagement Rate %"], row["ER Score"], row["Comment Score"],
            row["Macro/Micro"], row["Loop Giveaway History"], row["Platform"],
            row["Category"], row["Notes"], row["Active (30 days)"],
            row["USA Signal"], row["Last Verified"],
        ])
        existing.add(handle)
        time.sleep(0.3)

    if to_write:
        ws.append_rows(to_write, value_input_option="USER_ENTERED")

    print(f"  [sheet] Written: {len(to_write)}, Skipped (dup): {skipped}")
    return {"written": len(to_write), "skipped": skipped}


def save_csv(rows: list[dict], label: str = "output"):
    """CSV fallback in outputs/ folder. Appends to existing file to avoid overwrite."""
    os.makedirs("outputs", exist_ok=True)
    fname = f"outputs/influencer_pipeline_{label}_{datetime.date.today().isoformat()}.csv"
    file_exists = os.path.isfile(fname)
    with open(fname, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_HEADERS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)
    print(f"  [csv] {'Appended' if file_exists else 'Saved'} {len(rows)} rows → {fname}")
    return fname


# ── Reporting ──────────────────────────────────────────────────────────────────
def print_category_report(rows: list[dict], category: str):
    """Print formatted table + top 3 + flags for a category."""
    print(f"\n{'='*80}")
    print(f"  CATEGORY: {category} — {len(rows)} accounts")
    print(f"{'='*80}")

    header = f"{'#':<3} {'Handle':<28} {'Followers':>10} {'Avg Likes':>10} {'Avg Cmts':>9} {'ER%':>6} {'ER Score':<10} {'Cmnt Score':<12} {'Tier':<10} {'Active':<5} {'USA':<4}"
    print(header)
    print("-" * len(header))

    for i, r in enumerate(rows, 1):
        print(
            f"{i:<3} {r['Handle']:<28} {r['Followers']:>10,} "
            f"{r['Avg Likes']:>10,.0f} {r['Avg Comments (real)']:>9.1f} "
            f"{r['Engagement Rate %']:>6.2f} {r['ER Score']:<10} "
            f"{r['Comment Score']:<12} {r['Macro/Micro']:<10} "
            f"{'Y' if 'Y' in r['Active (30 days)'] else 'N':<5} "
            f"{r['USA Signal']:<4}"
        )
        if r["Notes"] != "OK":
            print(f"    >> {r['Notes']}")

    # Top 3 by comment score (absolute volume)
    sorted_by_comments = sorted(rows, key=lambda x: x["_avg_comments"], reverse=True)
    print(f"\n  TOP 3 (by avg comments):")
    for r in sorted_by_comments[:3]:
        print(f"    {r['Handle']} -- {r['Avg Comments (real)']} avg comments, {r['Comment Score']}, ER {r['Engagement Rate %']}%")

    # Flags
    low_roi = [r for r in rows if r["_er_score"] == "LOW ROI" and r["_avg_comments"] < 50]
    inactive = [r for r in rows if "N --" in r["Active (30 days)"]]
    floor_fails = [r for r in rows if not r.get("_passes_floor", True)]

    if low_roi:
        print(f"\n  [LOW ROI] low ER% AND low comment volume: {', '.join(r['Handle'] for r in low_roi)}")
    if inactive:
        print(f"  [INACTIVE]: {', '.join(r['Handle'] for r in inactive)}")
    if floor_fails:
        print(f"  [FLOOR FAIL]: {', '.join(r['Handle'] for r in floor_fails)}")

    unverified = [r for r in rows if "UNVERIFIED" in r.get("Notes", "")]
    if unverified:
        print(f"  [UNVERIFIED]: {', '.join(r['Handle'] for r in unverified)}")


# ── Main entry point ───────────────────────────────────────────────────────────
def verify_handles(handles: list[str], category: str, platform: str = "Instagram",
                   loop_history_map: dict = None, dry_run: bool = False) -> list[dict]:
    """
    Full pipeline: scrape → score → report → write.
    Returns list of built rows.
    """
    loop_history_map = loop_history_map or {}

    print(f"\n[pipeline] Verifying {len(handles)} accounts — category: {category}, platform: {platform}")

    if platform == "TikTok":
        raw_profiles = scrape_tiktok_batch(handles)
    else:
        raw_profiles = scrape_instagram_batch(handles)

    if not raw_profiles:
        print("[pipeline] No profiles returned — check Apify token and handles")
        return []

    # Map returned profiles back to input handles
    profile_map = {}
    for p in raw_profiles:
        u = (p.get("username") or "").lower().strip()
        if u:
            profile_map[u] = p

    rows = []
    no_data = []

    for handle in handles:
        clean = handle.lstrip("@").lower().strip()
        profile = profile_map.get(clean)

        if not profile:
            no_data.append(handle)
            # Write stub row so handle isn't lost
            rows.append({
                "Handle": f"@{clean}", "Name": "", "Followers": 0,
                "Avg Likes": 0, "Avg Comments (real)": 0,
                "Engagement Rate %": 0, "ER Score": "UNVERIFIED",
                "Comment Score": "UNVERIFIED",
                "Macro/Micro": "Unknown", "Loop Giveaway History": loop_history_map.get(clean, "Unknown"),
                "Platform": platform, "Category": category,
                "Notes": "UNVERIFIED — Apify returned no data",
                "Active (30 days)": "?", "USA Signal": "?",
                "Last Verified": datetime.date.today().isoformat(),
                "_passes_floor": False, "_er_score": "UNVERIFIED",
                "_comment_score": "UNVERIFIED", "_avg_comments": 0, "_er_pct": 0,
            })
            continue

        # Handle TikTok unverified stubs
        if profile.get("_unverified"):
            rows.append({
                "Handle": f"@{clean}", "Name": "", "Followers": 0,
                "Avg Likes": 0, "Avg Comments (real)": 0,
                "Engagement Rate %": 0, "ER Score": "UNVERIFIED",
                "Comment Score": "UNVERIFIED",
                "Macro/Micro": "Unknown", "Loop Giveaway History": loop_history_map.get(clean, "Unknown"),
                "Platform": platform, "Category": category,
                "Notes": f"UNVERIFIED — TikTok actor unavailable: {profile.get('_unverified_reason', '')}",
                "Active (30 days)": "?", "USA Signal": "?",
                "Last Verified": datetime.date.today().isoformat(),
                "_passes_floor": False, "_er_score": "UNVERIFIED",
                "_comment_score": "UNVERIFIED", "_avg_comments": 0, "_er_pct": 0,
            })
            continue

        row = build_row(profile, category, platform, loop_history_map.get(clean, "Unknown"))
        rows.append(row)

    if no_data:
        print(f"  [pipeline] No data returned for: {', '.join(no_data)}")

    # Print report
    print_category_report(rows, category)

    # Write to sheet + CSV
    write_influencer_tab(rows, dry_run=dry_run)
    save_csv(rows, label=category.lower().replace(" ", "_"))

    return rows


# ── Discover mode helpers ──────────────────────────────────────────────────────

HASHTAG_ACTOR = "apify/instagram-hashtag-scraper"

# New 12-column headers matching reorganize_influencer_tab.py output
DISCOVER_HEADERS = [
    "Handle", "Category", "Followers",
    "Avg Comments", "Avg Likes", "Engagement Rate %",
    "ER Score", "Comment Score",
    "Active?", "USA Signal", "Included", "Notes",
]


def discover_handles_from_hashtags(hashtags: list[str], max_posts: int = 200) -> list[str]:
    """
    Run Apify hashtag scraper to extract unique post authors.
    Returns list of raw usernames (no @ prefix).
    """
    client = ApifyClient(APIFY_TOKEN)
    found = set()

    for tag in hashtags:
        tag_clean = tag.lstrip("#")
        print(f"  [hashtag] Scraping #{tag_clean} (up to {max_posts} posts)...")
        try:
            run = client.actor(HASHTAG_ACTOR).call(run_input={
                "hashtags": [tag_clean],
                "resultsLimit": max_posts,
                "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
            })
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            for item in items:
                owner = (item.get("ownerUsername") or item.get("username") or "").lower().strip()
                if owner:
                    found.add(owner)
            print(f"    -> {len(items)} posts, {len(found)} unique authors so far")
            time.sleep(2)
        except Exception as e:
            print(f"    [hashtag] Error on #{tag_clean}: {e}")

    return list(found)


def get_existing_handles_from_sheet() -> set:
    """Read current Influencer Pipeline tab and return set of existing handles (normalized)."""
    ws = get_sheet()
    all_vals = ws.get_all_values()
    existing = set()
    for row in all_vals:
        if row and row[0]:
            h = row[0].lstrip("@").lower().strip()
            if h and h not in ("handle", "category", "influencer pipeline", "er%"):
                existing.add(h)
    return existing


def build_discover_row(scored_row: dict) -> list:
    """Map a verified scored row to the new 12-column discover format."""
    handle = scored_row["Handle"]
    category = scored_row["Category"]
    followers = scored_row["Followers"]
    avg_comments = scored_row["Avg Comments (real)"]
    avg_likes = scored_row["Avg Likes"]
    er_pct = scored_row["Engagement Rate %"]
    er_score = scored_row["ER Score"].replace("LOW ROI", "LOW%")
    comment_score = scored_row["Comment Score"]
    active = "Yes" if scored_row["Active (30 days)"].startswith("Y") else "No"
    usa = scored_row["USA Signal"]

    # Condense notes
    parts = []
    name = scored_row.get("Name", "").strip()
    macro = scored_row.get("Macro/Micro", "").strip()
    notes = scored_row.get("Notes", "").strip()
    if macro and macro.lower() not in ("", "unknown"):
        parts.append(macro)
    if name:
        parts.append(f"Name: {name}")
    if notes and notes not in ("OK", ""):
        parts.append(notes)
    notes_cell = " | ".join(parts)

    return [
        handle, category, followers,
        avg_comments, avg_likes, er_pct,
        er_score, comment_score,
        active, usa, "Yes", notes_cell,
    ]


def write_discovered_rows(rows: list[dict], dry_run: bool = False) -> dict:
    """
    Write discover-mode rows in the NEW 12-column format.
    Deduplicates against all existing handles in the sheet.
    Only writes rows that pass the quality bar: Active + SOLID/HIGH VALUE.
    """
    KEEP_SCORES = {"HIGH VALUE", "SOLID"}

    qualified = [
        r for r in rows
        if r.get("_comment_score") in KEEP_SCORES
        and r.get("Active (30 days)", "").startswith("Y")
        and r.get("Followers", 0) > 0
    ]

    print(f"  [discover] {len(rows)} verified -> {len(qualified)} pass quality bar (Active + SOLID/HIGH VALUE)")

    if dry_run:
        print(f"  [dry-run] Would write {len(qualified)} rows")
        return {"written": 0, "skipped_quality": len(rows) - len(qualified), "skipped_dup": 0}

    if not qualified:
        return {"written": 0, "skipped_quality": len(rows), "skipped_dup": 0}

    existing = get_existing_handles_from_sheet()
    ws = get_sheet()

    to_write = []
    skipped_dup = 0
    for r in qualified:
        key = r["Handle"].lstrip("@").lower().strip()
        if key in existing:
            skipped_dup += 1
            continue
        to_write.append(build_discover_row(r))
        existing.add(key)

    if to_write:
        ws.append_rows(to_write, value_input_option="USER_ENTERED")

    print(f"  [sheet] Written: {len(to_write)} | Skipped (dup): {skipped_dup} | Skipped (low quality): {len(rows) - len(qualified)}")
    return {"written": len(to_write), "skipped_quality": len(rows) - len(qualified), "skipped_dup": skipped_dup}


def discover_category(hashtags: list[str], category: str, max_posts: int = 200,
                      dry_run: bool = False) -> list[dict]:
    """
    Full discover pipeline:
      hashtags → candidate handles → dedup → verify → quality filter → write
    """
    print(f"\n[discover] Category: {category}")
    print(f"  Hashtags: {hashtags}")

    # Step 1: Get candidates from hashtags
    all_candidates = discover_handles_from_hashtags(hashtags, max_posts=max_posts)
    print(f"  Found {len(all_candidates)} unique handles from hashtags")

    # Step 2: Dedup against sheet
    existing = get_existing_handles_from_sheet()
    new_candidates = [h for h in all_candidates if h.lower().strip() not in existing]
    print(f"  After dedup: {len(new_candidates)} new candidates")

    if not new_candidates:
        print("  Nothing new to verify.")
        return []

    # Step 3: Verify (scrape + score)
    rows = []
    for i in range(0, len(new_candidates), 10):
        batch = new_candidates[i:i + 10]
        batch_rows = verify_handles(batch, category=category, dry_run=True)  # dry_run=True to skip old-format write
        rows.extend(batch_rows)
        time.sleep(1)

    # Step 4: Write qualified rows in new 12-column format + CSV
    write_discovered_rows(rows, dry_run=dry_run)
    save_csv(rows, label=f"discover_{category.lower().replace(' ', '_')}")

    return rows


# ── CLI ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="CAIT Influencer Pipeline")
    parser.add_argument("--mode", choices=["verify", "discover"], default="verify")

    # verify mode args
    parser.add_argument("--handles", nargs="+", help="Instagram/TikTok handles (verify mode)")
    parser.add_argument("--file", help="File with one handle per line (verify mode)")

    # discover mode args
    parser.add_argument("--hashtags", nargs="+", help="Hashtags to scrape (discover mode, no # needed)")
    parser.add_argument("--max-posts", type=int, default=200, help="Posts per hashtag (default 200)")

    # shared
    parser.add_argument("--category", default="Uncategorized", help="Category label for the sheet")
    parser.add_argument("--platform", default="Instagram", choices=["Instagram", "TikTok"])
    parser.add_argument("--dry-run", action="store_true", help="Skip sheet write")
    args = parser.parse_args()

    if args.mode == "discover":
        if args.handles:
            # Direct handle list — skip hashtag scraping, verify and write in new 12-col format
            print(f"\n[discover] Category: {args.category} — direct handles mode")
            existing = get_existing_handles_from_sheet()
            new_handles = [h for h in args.handles if h.lstrip("@").lower().strip() not in existing]
            print(f"  {len(args.handles)} provided -> {len(new_handles)} after dedup")
            if new_handles:
                rows = []
                for i in range(0, len(new_handles), 10):
                    batch = new_handles[i:i + 10]
                    batch_rows = verify_handles(batch, category=args.category, platform=args.platform, dry_run=True)
                    rows.extend(batch_rows)
                    time.sleep(1)
                write_discovered_rows(rows, dry_run=args.dry_run)
                save_csv(rows, label=f"discover_{args.category.lower().replace(' ', '_')}")
        elif args.hashtags:
            discover_category(
                hashtags=args.hashtags,
                category=args.category,
                max_posts=args.max_posts,
                dry_run=args.dry_run,
            )
        else:
            print("--mode discover requires --hashtags or --handles")
            sys.exit(1)

    else:  # verify
        handles = []
        if args.handles:
            handles.extend(args.handles)
        if args.file:
            with open(args.file) as f:
                handles.extend(line.strip() for line in f if line.strip())

        if not handles:
            print("No handles provided. Use --handles or --file.")
            sys.exit(1)

        verify_handles(handles, category=args.category, platform=args.platform, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
