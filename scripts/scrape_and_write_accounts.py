"""
scrape_and_write_accounts.py
-----------------------------
One-off: scrape specific Instagram accounts via Apify, qualify, enrich email,
and write to CAIT Community tab.

Usage:
    python scripts/scrape_and_write_accounts.py
"""

import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Fix Windows console emoji encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from apify_client import ApifyClient
from dotenv import load_dotenv

from scripts.enrich_email import enrich_email
from scripts.write_sheet import write_rows

load_dotenv()

APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
PROFILE_ACTOR = "apify/instagram-scraper"

# Accounts to scrape and write
TARGETS = [
    {"username": "thekinected_ot",      "category": "Pediatric OT"},
    {"username": "raisinglittletalkers","category": "SLP / Speech"},
    {"username": "pedsdoctalk",         "category": "Pediatrician"},
]


def scrape_profiles(usernames: list[str]) -> list[dict]:
    client = ApifyClient(APIFY_TOKEN)
    run_input = {
        "directUrls": [f"https://www.instagram.com/{u}/" for u in usernames],
        "resultsType": "details",
        "resultsLimit": 12,
        "proxy": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
        },
    }
    run = client.actor(PROFILE_ACTOR).call(run_input=run_input)
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


def qualify(profile: dict) -> dict | None:
    username = (profile.get("username") or "").lower().strip()
    bio = profile.get("biography") or profile.get("bio") or ""
    followers = profile.get("followersCount") or profile.get("followers") or 0
    website = profile.get("externalUrl") or profile.get("website") or ""
    is_private = profile.get("private") or profile.get("isPrivate") or False

    if is_private or not username:
        return None

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
        if len(comment_counts) >= 10:
            break

    posts_checked = len(comment_counts)
    posts_with_15_plus = sum(1 for c in comment_counts if c >= 15)
    avg_comments = round(sum(comment_counts) / posts_checked, 1) if posts_checked else 0
    avg_likes = round(sum(like_counts) / posts_checked, 1) if posts_checked else 0

    print(f"  Posts checked (non-pinned): {posts_checked}")
    print(f"  Posts with 15+ comments: {posts_with_15_plus}/{posts_checked}")
    print(f"  Avg comments: {avg_comments} | Avg likes: {avg_likes}")
    print(f"  Bio: {bio[:80]}")
    print(f"  Website: {website}")

    return {
        "username": username,
        "followers": int(followers),
        "avg_comments": avg_comments,
        "avg_likes": avg_likes,
        "posts_checked": posts_checked,
        "posts_with_15_plus": posts_with_15_plus,
        "website": website,
        "_bio": bio,
    }


def tier_label(avg_comments: float) -> str:
    if avg_comments >= 100:
        return "Tier 1 — High Priority"
    elif avg_comments >= 30:
        return "Tier 1"
    return "Tier 2"


if __name__ == "__main__":
    print("=== Scraping target accounts ===")
    usernames = [t["username"] for t in TARGETS]
    category_map = {t["username"]: t["category"] for t in TARGETS}

    profiles = scrape_profiles(usernames)
    print(f"Scraped {len(profiles)} profiles\n")

    rows = []
    for profile in profiles:
        username = (profile.get("username") or "").lower().strip()
        print(f"--- @{username} ---")

        data = qualify(profile)
        if not data:
            print(f"  SKIP: private or no username")
            continue

        print(f"  Enriching email...")
        email_result = enrich_email(
            username=username,
            bio=data["_bio"],
            website=data["website"],
        )
        print(f"  Email: {email_result['email'] or 'not found'} ({email_result['email_source']})")

        tier = tier_label(data["avg_comments"])
        # Determine gender signal from bio
        bio_lower = data["_bio"].lower()
        if any(s in bio_lower for s in ["she/her", "she / her", "mom", "mama", "her "]):
            gender = "F"
        elif any(s in bio_lower for s in ["he/him", "he / him", "dad", "his "]):
            gender = "M"
        else:
            gender = "?"

        notes = f"{gender} | USA | {tier} | {category_map.get(username, '')}"

        rows.append({
            "username": username,
            "full_name": "",
            "category": category_map.get(username, ""),
            "followers": data["followers"],
            "avg_comments": data["avg_comments"],
            "email": email_result["email"],
            "email_source": email_result["email_source"],
            "website": data["website"],
            "products": "",
            "notes": notes,
        })

    if not rows:
        print("\nNo rows to write.")
        sys.exit(0)

    print(f"\n=== Writing {len(rows)} rows to CAIT Community tab ===")
    result = write_rows(
        tab_name="CAIT Community",
        rows=rows,
        batch_size=len(rows),
    )
    print(f"Written: {result['written']} | Skipped: {result['skipped_duplicates']} | Errors: {result['errors']}")
