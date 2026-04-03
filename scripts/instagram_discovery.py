"""
instagram_discovery.py
----------------------
Discovers and qualifies Instagram accounts via Apify.
Handles both journey accounts (50 Million List) and professional accounts (CAIT Community).

Usage:
    python scripts/instagram_discovery.py --category instagram_cait_community --diagnosis autism
    python scripts/instagram_discovery.py --category instagram_50million --diagnosis medically_complex
"""

import os
import re
import sys
import time
import datetime
import argparse

import gspread
from google.oauth2.service_account import Credentials
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.environ.get("APIFY_TOKEN")

HASHTAG_ACTOR = "apify/instagram-hashtag-scraper"
PROFILE_ACTOR = "apify/instagram-scraper"  # NOT profile-scraper — gets blocked

# USA signals for bio/location detection
USA_SIGNALS = [
    "usa", "u.s.a", "united states", "america", "american",
    "iep", "medicaid", "ssi", "ssdi", "childrens hospital",
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga",
    "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md",
    "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj",
    "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc",
    "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy",
    "alabama", "alaska", "arizona", "arkansas", "california",
    "colorado", "connecticut", "florida", "georgia", "hawaii",
    "illinois", "indiana", "kentucky", "louisiana", "maryland",
    "massachusetts", "michigan", "minnesota", "mississippi",
    "missouri", "new york", "north carolina", "ohio", "oklahoma",
    "oregon", "pennsylvania", "tennessee", "texas", "virginia",
    "washington", "wisconsin",
]

# Female name/bio signals
FEMALE_SIGNALS = [
    "mom", "mama", "mother", "mommy", "she/her", "she / her",
    "wife", "daughter", "girl", "woman", "lady", "mrs", "ms.", "mrs.",
]

MALE_SIGNALS = [
    "dad", "father", "daddy", "he/him", "he / him", "husband",
    "mr.", "sir", "dude",
]

# Hashtags by category
DISCOVERY_HASHTAGS = {
    "instagram_cait_community": [
        # OT
        "pediatricot", "occupationaltherapy", "otforkids", "sensoryprocessing",
        "otlife", "pediatricoccupationaltherapy",
        # SLP
        "slp", "speechtherapist", "speechlanguagepathology", "speechlanguagepathologist",
        "pediatricspeech", "feedingtherapist", "slplife",
        # PT / Physical Therapy
        "physicaltherapist", "pediatricpt", "pediatricphysicaltherapy",
        # Play therapy / Child psych
        "playtherapist", "playtherapy", "childtherapist", "kidstherapist",
        "childpsychologist", "pediatricpsychology", "pediatricpsychologist",
        # Sleep consultant
        "sleepconsultant", "certifiedsleepconsultant", "infantsleepconsultant",
        "pediatricsleep",
        # Pediatric medicine
        "pediatrician", "pedsrn", "pediatricnurse", "pediatricnursing",
        # Education / advocacy
        "specialeducationteacher", "iepadvocate", "autismeducator",
    ],
    "instagram_50million": {
        "medically_complex": [
            "medicalmom", "medicallycomplex", "medicalkid", "complexneeds",
            "medicallyfrailchild", "hospitallife", "childrenshospital", "medicalmama",
        ],
        "autism": [
            "autismmom", "autismparent", "autismfamily", "autismlife",
            "autismwarrior", "autismacceptance", "asdmom",
        ],
        "down_syndrome": [
            "downsyndrome", "downsyndromeawareness", "t21", "trisomy21",
            "downsyndromelife", "ds_awareness",
        ],
        "t1d": [
            "t1dmom", "type1diabetes", "t1dparent", "t1dlife",
            "diabetesmom", "bloodsugarwarrior",
        ],
        "epilepsy": [
            "epilepsymom", "epilepsywarrior", "seizurelife",
            "epilepsyfamily", "dravetsyndrome",
        ],
        "pediatric_cancer": [
            "childhoodcancer", "pediatriccancer", "cancermom",
            "cancerwarrior", "goldribbon",
        ],
        "cystic_fibrosis": [
            "cfwarrior", "cysticfibrosis", "cflife", "cfmom",
        ],
    },
}

# Professional credential keywords for CAIT Community
PROFESSIONAL_SIGNALS = [
    "bcba", "board certified behavior analyst", "behavior analyst",
    "occupational therapist", "ot,", "ot ", "o.t.",
    "speech therapist", "speech-language", "slp,", "slp ", "s.l.p.",
    "feeding therapist", "pediatrician", "pediatric nurse", "rn,", "rn ", "r.n.",
    "special education", "educator", "teacher", "coach",
]

# Product/course selling signals
SELLING_SIGNALS = [
    "course", "program", "workshop", "masterclass", "coaching",
    "book", "guide", "membership", "community", "shop", "store",
    "enroll", "join", "grab", "download", "free guide", "link in bio",
    "linktree", "stan.store", "teachable", "kajabi", "thinkific",
]


def has_usa_signal(text: str) -> bool:
    text_lower = text.lower()
    return any(signal in text_lower for signal in USA_SIGNALS)


def is_likely_female(bio: str, username: str, full_name: str) -> bool:
    combined = f"{bio} {username} {full_name}".lower()
    if any(s in combined for s in MALE_SIGNALS):
        return False
    if any(s in combined for s in FEMALE_SIGNALS):
        return True
    # If no clear signal either way, return None (uncertain)
    return None


def count_real_comments(comments: list) -> int:
    """Count comments that are actual sentences (not emoji-only or one-word)."""
    real = 0
    for c in comments:
        text = c.get("text", "") if isinstance(c, dict) else str(c)
        text = text.strip()
        # Skip pure emoji, one-word, or very short comments
        words = re.findall(r'\b\w+\b', text)
        if len(words) >= 3:
            real += 1
    return real


def discover_usernames_from_hashtag(hashtag: str, max_posts: int = 100) -> list[str]:
    """Use Apify hashtag scraper to get usernames from a hashtag."""
    client = ApifyClient(APIFY_TOKEN)
    usernames = set()

    try:
        run_input = {
            "hashtags": [hashtag],
            "resultsLimit": max_posts,
            "proxy": {"useApifyProxy": True},
        }
        run = client.actor(HASHTAG_ACTOR).call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        for item in items:
            owner = item.get("ownerUsername") or item.get("username") or ""
            if owner:
                usernames.add(owner.lower().strip())
    except Exception as e:
        print(f"[instagram] Hashtag scrape error for #{hashtag}: {e}")

    return list(usernames)


def scrape_profiles(usernames: list[str]) -> list[dict]:
    """Use Apify profile scraper to get full profile data for a list of usernames."""
    client = ApifyClient(APIFY_TOKEN)
    results = []

    # Batch in groups of 20 to avoid timeouts
    for i in range(0, len(usernames), 20):
        batch = usernames[i:i+20]
        try:
            run_input = {
                "directUrls": [f"https://www.instagram.com/{u}/" for u in batch],
                "resultsType": "details",
                "resultsLimit": 12,  # 12 posts per profile for comment check
                "proxy": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"],
                },
            }
            run = client.actor(PROFILE_ACTOR).call(run_input=run_input)
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            results.extend(items)
            time.sleep(2)
        except Exception as e:
            print(f"[instagram] Profile scrape error for batch {i}: {e}")

    return results


def write_to_scrape_pool(profiles: list[dict], source_hashtags: list[str]):
    """Dump all scraped profiles to Raw Scrape Pool tab for Cherwin's review."""
    try:
        creds_path = os.environ.get("GOOGLE_CREDS_PATH")
        sheet_id = os.environ.get("GOOGLE_SHEET_ID")
        if not creds_path or not sheet_id:
            return

        creds = Credentials.from_service_account_file(
            creds_path,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(sheet_id)
        ws = sh.worksheet("Raw Scrape Pool")

        today = datetime.date.today().isoformat()
        hashtag_str = ", ".join(f"#{h}" for h in source_hashtags[:5])
        rows = []

        for p in profiles:
            username = (p.get("username") or "").strip()
            full_name = p.get("fullName") or p.get("full_name") or ""
            followers = p.get("followersCount") or p.get("followers") or 0
            bio = (p.get("biography") or p.get("bio") or "")[:120]  # truncate
            website = p.get("externalUrl") or p.get("website") or ""
            posts = p.get("latestPosts") or p.get("posts") or []

            comment_counts = [post.get("commentsCount", 0) for post in posts[:5] if isinstance(post, dict)]
            like_counts = [post.get("likesCount", 0) for post in posts[:5] if isinstance(post, dict)]
            avg_comments = round(sum(comment_counts) / len(comment_counts), 1) if comment_counts else 0
            avg_likes = round(sum(like_counts) / len(like_counts), 1) if like_counts else 0

            rows.append([
                f"@{username}",
                full_name,
                str(followers),
                str(len(comment_counts)),
                str(avg_comments),
                str(avg_likes),
                bio,
                website,
                hashtag_str,
                today,
            ])

        if rows:
            ws.append_rows(rows, value_input_option="USER_ENTERED")
            print(f"[instagram] Wrote {len(rows)} profiles to Raw Scrape Pool")

    except Exception as e:
        print(f"[instagram] Raw Scrape Pool write failed: {e}")


def qualify_profile(profile: dict, category: str) -> dict | None:
    """
    Apply all qualification filters. Returns cleaned profile dict or None.
    """
    username = (profile.get("username") or "").lower().strip()
    bio = profile.get("biography") or profile.get("bio") or ""
    full_name = profile.get("fullName") or profile.get("full_name") or ""
    followers = profile.get("followersCount") or profile.get("followers") or 0
    is_private = profile.get("isPrivate") or False
    is_verified = profile.get("isVerified") or False
    website = profile.get("externalUrl") or profile.get("website") or ""

    # Skip private accounts
    if is_private:
        return None

    # Skip accounts with no username
    if not username:
        return None

    # Geography check — relaxed for CAIT Community (therapists rarely put state in bio)
    if category != "instagram_cait_community":
        if not has_usa_signal(bio) and not has_usa_signal(full_name):
            return None

    # Gender check
    female_check = is_likely_female(bio, username, full_name)
    if female_check is False:
        return None  # Confirmed male — skip
    # If uncertain (None), include but note in Notes

    # Activity check — 10 posts individually, require 7/10 with 15+ real comments
    # Note: Apify sometimes returns pinned posts first — skip them to avoid inflated counts
    posts = profile.get("latestPosts") or profile.get("posts") or []
    if not posts:
        return None  # Can't verify activity

    comment_counts = []
    like_counts = []
    for post in posts:
        if not isinstance(post, dict):
            continue
        # Skip pinned posts (Apify bug: returned first, inflate engagement signal)
        if post.get("isPinned") or post.get("pinned"):
            continue
        comment_counts.append(post.get("commentsCount") or 0)
        like_counts.append(post.get("likesCount") or 0)
        if len(comment_counts) >= 10:
            break

    if len(comment_counts) < 5:
        return None  # Not enough non-pinned posts to evaluate

    # Require 7 out of 10 (or all available) posts to have 15+ comments
    posts_with_15_plus = sum(1 for c in comment_counts if c >= 15)
    threshold = max(1, round(len(comment_counts) * 0.7))
    if posts_with_15_plus < threshold:
        return None

    avg_comments = sum(comment_counts) / len(comment_counts)
    avg_likes = sum(like_counts) / len(like_counts) if like_counts else 0

    # Category-specific checks
    notes_parts = []

    if category == "instagram_cait_community":
        # Must show professional signals
        bio_lower = bio.lower()
        is_professional = any(s in bio_lower for s in PROFESSIONAL_SIGNALS)
        if not is_professional:
            return None

        # Must show selling signals
        is_selling = any(s in bio_lower for s in SELLING_SIGNALS)
        if not is_selling:
            notes_parts.append("no product found — may be clinic-only")

    # Determine tier
    if avg_comments >= 100:
        tier = "Tier 1 — FLAG FOR CHERWIN REVIEW"
    elif avg_comments >= 30:
        tier = "Tier 2"
    else:
        tier = "Tier 3"

    notes_parts.insert(0, tier)
    if female_check is None:
        notes_parts.append("gender unclear")

    return {
        "username": username,
        "profile_link": f"https://instagram.com/{username}",
        "followers": int(followers),
        "avg_comments": round(avg_comments, 1),
        "avg_likes": round(avg_likes, 1),
        "email": "",
        "email_source": "",
        "website": website,
        "category": "",  # Set by caller based on diagnosis
        "notes": " | ".join(notes_parts),
        "_bio": bio,  # Internal — used by enrich_email.py
    }


def run(category: str, diagnosis: str = "medically_complex", batch_size: int = 5) -> list[dict]:
    """
    Full pipeline: hashtag search → profile scrape → qualify → return results.
    """
    print(f"\n[instagram] Starting discovery: category={category}, diagnosis={diagnosis}")

    # Get hashtags
    if category == "instagram_cait_community":
        hashtags = DISCOVERY_HASHTAGS["instagram_cait_community"]
    else:
        diag_hashtags = DISCOVERY_HASHTAGS.get("instagram_50million", {})
        hashtags = diag_hashtags.get(diagnosis, diag_hashtags.get("medically_complex", []))

    if not hashtags:
        print(f"[instagram] No hashtags found for diagnosis: {diagnosis}")
        return []

    # Discover usernames from hashtags
    all_usernames = set()
    for hashtag in hashtags[:10]:  # Use first 10 hashtags
        print(f"[instagram] Scanning #{hashtag}...")
        usernames = discover_usernames_from_hashtag(hashtag, max_posts=100)
        all_usernames.update(usernames)
        time.sleep(1)
        if len(all_usernames) >= 300:
            break

    print(f"[instagram] Found {len(all_usernames)} unique usernames to qualify")

    # Scrape profiles in batches
    usernames_list = list(all_usernames)[:300]  # Cap to control Apify usage
    profiles = scrape_profiles(usernames_list)
    print(f"[instagram] Scraped {len(profiles)} profiles")

    # Dump everything to Raw Scrape Pool for Cherwin's review
    write_to_scrape_pool(profiles, hashtags[:10])

    # Qualify
    qualified = []
    seen = set()
    for profile in profiles:
        if len(qualified) >= batch_size * 3:
            break

        result = qualify_profile(profile, category)
        if not result:
            continue

        if result["username"] in seen:
            continue

        seen.add(result["username"])
        result["category"] = diagnosis.replace("_", " ")
        qualified.append(result)
        print(f"[instagram] Qualified: @{result['username']} | {result['avg_comments']} avg comments | {result['followers']} followers")

    print(f"[instagram] {len(qualified)} qualified (need {batch_size})")
    return qualified[:batch_size * 2]  # Buffer for dedup


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", required=True,
                        choices=["instagram_50million", "instagram_cait_community"])
    parser.add_argument("--diagnosis", default="medically_complex")
    parser.add_argument("--batch-size", type=int, default=5)
    args = parser.parse_args()

    results = run(args.category, args.diagnosis, args.batch_size)
    print(f"\nResults preview:")
    for r in results:
        print(f"  @{r['username']} | followers: {r['followers']} | avg comments: {r['avg_comments']} | {r['notes']}")
