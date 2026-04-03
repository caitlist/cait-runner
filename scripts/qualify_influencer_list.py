"""
qualify_influencer_list.py
--------------------------
Runs all accounts from the boss's influencer PDFs through Apify profile scraper.
Checks each account's last 10 posts individually for consistent 15+ comments.
Outputs a full qualification report for CAIT Community tab.

Usage:
    python scripts/qualify_influencer_list.py
"""

import os
import time
import datetime
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
PROFILE_ACTOR = "apify/instagram-scraper"

# All accounts from both PDFs — corrected handles where PDF had wrong ones
# Format: (pdf_handle, actual_handle, source_pdf)
ACCOUNTS = [
    # --- PDF 1: CAIT Macro Influencer Outreach List ---
    ("drbeckyatgoodinside",    "drbeckyatgoodinside",    "PDF1"),
    ("takingcarababies",       "takingcarababies",        "PDF1"),
    ("solidstarts",            "solidstarts",             "PDF1"),
    ("janetlansbury",          "janetlansbury",           "PDF1"),
    ("biglittlefeelings",      "biglittlefeelings",       "PDF1"),
    ("busytoddler",            "busytoddler",             "PDF1"),
    ("melrobbins",             "melrobbins",              "PDF1"),
    ("jayshetty",              "jayshetty",               "PDF1"),
    ("nedratawwab",            "nedratawwab",             "PDF1"),
    ("the.holistic.psychologist", "the.holistic.psychologist", "PDF1"),
    ("msrachelhollis",         "msrachelhollis",          "PDF1"),
    ("pedsdoctalk",            "pedsdoctalk",             "PDF1"),
    ("happiest_baby",          "happiest_baby",           "PDF1"),
    ("raisinggoodhumanspodcast", "raisinggoodhumanspodcast", "PDF1"),
    ("drjoelgator",            "drjoelgator",             "PDF1"),
    ("paigelayle",             "paigelayle",              "PDF1"),
    ("chloeshayden",           "chloeshayden",            "PDF1"),
    ("theautismdad",           "theautismdad",            "PDF1"),
    ("kristinakuzmic",         "kristinakuzmic",          "PDF1"),
    ("catandnat",              "catandnat",               "PDF1"),
    ("mommyshorts",            "mommyshorts",             "PDF1"),
    ("inspiralized",           "inspiralized",            "PDF1"),
    ("mommasgonecity",         "mommasgonecity",          "PDF1"),
    ("taza",                   "taza",                    "PDF1"),
    ("doctorshefali",          "doctorshefali",           "PDF1"),
    ("gabor_mate",             "gabor_mate",              "PDF1"),
    ("estherperelofficial",    "estherperelofficial",     "PDF1"),
    ("docamen",                "docamen",                 "PDF1"),
    ("hubermanlab",            "hubermanlab",             "PDF1"),
    ("peterattiamd",           "peterattiamd",            "PDF1"),

    # --- PDF 2: CAIT Connect Broad Doctor & Therapist List (new accounts only) ---
    ("drjuliesmith",           "drjulie",                 "PDF2"),  # actual handle is @drjulie
    ("therapyjeff",            "therapyjeff",             "PDF2"),
    ("michelinetherapist",     "micheline.maalouf",       "PDF2"),  # actual handle
    ("theshaniproject",        "theshaniproject",         "PDF2"),
    ("drmarkhyman",            "drmarkhyman",             "PDF2"),
    ("drgabriellelyon",        "drgabriellelyon",         "PDF2"),
    ("drwillcole",             "drwillcole",              "PDF2"),
    ("drericberg",             "drericberg",              "PDF2"),
    ("mamadoctorjones",        "mamadoctorjones",         "PDF2"),
    ("drginaderpt",            "dr.dan_dpt",              "PDF2"),  # actual handle
    ("bobandbrad",             "officialbobandbrad",      "PDF2"),  # actual handle
    ("thebehaviorexchange",    "thebehaviorexchange",     "PDF2"),
    ("autismlittlelearners",   "autismlittlelearners",    "PDF2"),
    ("occupationaltherapyabc", "occupationaltherapyabc",  "PDF2"),
    ("thesimpleot",            "thesimpleot",             "PDF2"),
    ("harkla_family",          "harkla_family",           "PDF2"),
    ("speechandlanguagekids",  "carrieclark_slp",         "PDF2"),  # actual handle
    ("hanen_centre",           "thehanencentre",          "PDF2"),  # actual handle
    ("biglifejournal",         "biglifejournal",          "PDF2"),
]

# Deduplicate by actual handle (some appear in both PDFs)
seen = set()
UNIQUE_ACCOUNTS = []
for pdf_handle, actual_handle, source in ACCOUNTS:
    if actual_handle not in seen:
        seen.add(actual_handle)
        UNIQUE_ACCOUNTS.append((pdf_handle, actual_handle, source))


def scrape_profiles(usernames: list[str]) -> list[dict]:
    """Scrape profiles using apify/instagram-scraper (browser-based, handles blocks)."""
    client = ApifyClient(APIFY_TOKEN)
    results = []
    # Batch in groups of 10 — residential proxies are slower
    for i in range(0, len(usernames), 10):
        batch = usernames[i:i+10]
        print(f"\n[scrape] Batch {i//10 + 1}: {batch}")
        try:
            urls = [f"https://www.instagram.com/{u}/" for u in batch]
            run_input = {
                "directUrls": urls,
                "resultsType": "details",
                "resultsLimit": 12,  # last 12 posts for comment consistency check
                "proxy": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"],
                },
            }
            run = client.actor(PROFILE_ACTOR).call(run_input=run_input)
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            results.extend(items)
            print(f"[scrape] Got {len(items)} profiles back")
            time.sleep(3)
        except Exception as e:
            print(f"[scrape] Error on batch {i}: {e}")
    return results


def check_engagement(posts: list[dict], required_posts: int = 7, min_comments: int = 15) -> dict:
    """
    Check last 10 posts individually.
    Returns: {
        posts_checked, comment_counts, consistent_posts,
        passes_floor, max_comments, avg_comments
    }
    """
    posts_to_check = posts[:10]
    comment_counts = []
    for post in posts_to_check:
        if isinstance(post, dict):
            comment_counts.append(post.get("commentsCount") or 0)

    if not comment_counts:
        return {
            "posts_checked": 0,
            "comment_counts": [],
            "consistent_posts": 0,
            "passes_floor": False,
            "max_comments": 0,
            "avg_comments": 0,
        }

    consistent = sum(1 for c in comment_counts if c >= min_comments)
    avg = round(sum(comment_counts) / len(comment_counts), 1)
    max_c = max(comment_counts)

    return {
        "posts_checked": len(comment_counts),
        "comment_counts": comment_counts,
        "consistent_posts": consistent,
        "passes_floor": consistent >= required_posts,
        "max_comments": max_c,
        "avg_comments": avg,
    }


def qualify_for_cait_community(profile: dict, pdf_handle: str, source: str) -> dict:
    """Full CAIT Community qualification check."""
    username = (profile.get("username") or "").lower().strip()
    bio = profile.get("biography") or profile.get("bio") or ""
    full_name = profile.get("fullName") or profile.get("full_name") or ""
    followers = profile.get("followersCount") or profile.get("followers") or 0
    is_private = profile.get("isPrivate") or profile.get("private") or False
    website = profile.get("externalUrl") or profile.get("website") or ""
    posts = profile.get("latestPosts") or profile.get("posts") or []

    result = {
        "pdf_handle": pdf_handle,
        "username": username,
        "source": source,
        "followers": followers,
        "bio": bio[:120],
        "website": website,
        "full_name": full_name,
        "is_private": is_private,
        "engagement": {},
        "verdict": "",
        "fail_reasons": [],
    }

    # --- Hard filters ---
    if is_private:
        result["fail_reasons"].append("private account")
    if not posts:
        result["fail_reasons"].append("no posts returned")

    # --- Engagement check ---
    eng = check_engagement(posts)
    result["engagement"] = eng

    if posts and not eng["passes_floor"]:
        result["fail_reasons"].append(
            f"low engagement: {eng['consistent_posts']}/10 posts with 15+ comments "
            f"(counts: {eng['comment_counts']})"
        )

    # --- Verdict ---
    if result["fail_reasons"]:
        result["verdict"] = "FAIL"
    elif eng["max_comments"] >= 100:
        result["verdict"] = "PASS — Tier 1 HIGH PRIORITY"
    elif eng["consistent_posts"] >= 7:
        result["verdict"] = "PASS — Tier 2"
    else:
        result["verdict"] = "BORDERLINE"

    return result


def print_report(results: list[dict]):
    """Print a clean qualification report."""
    print("\n" + "="*80)
    print("CAIT COMMUNITY — INFLUENCER LIST QUALIFICATION REPORT")
    print(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*80)

    passes = [r for r in results if "PASS" in r["verdict"]]
    fails = [r for r in results if r["verdict"] == "FAIL"]
    borders = [r for r in results if r["verdict"] == "BORDERLINE"]
    no_data = [r for r in results if not r["username"]]

    print(f"\nPASS: {len(passes)}  |  FAIL: {len(fails)}  |  BORDERLINE: {len(borders)}  |  NO DATA: {len(no_data)}")

    print("\n--- PASS ---")
    for r in sorted(passes, key=lambda x: x["engagement"].get("max_comments", 0), reverse=True):
        eng = r["engagement"]
        print(f"  @{r['username']} ({r['source']}) | {r['followers']:,} followers | "
              f"{eng.get('consistent_posts', 0)}/10 posts ≥15 comments | "
              f"max: {eng.get('max_comments', 0)} | avg: {eng.get('avg_comments', 0)}")
        print(f"    counts: {eng.get('comment_counts', [])}")
        print(f"    bio: {r['bio'][:80]}")
        print(f"    verdict: {r['verdict']}")
        print()

    print("\n--- BORDERLINE ---")
    for r in borders:
        eng = r["engagement"]
        print(f"  @{r['username']} ({r['source']}) | {r['followers']:,} followers | "
              f"{eng.get('consistent_posts', 0)}/10 posts ≥15 comments | "
              f"counts: {eng.get('comment_counts', [])}")
        print()

    print("\n--- FAIL ---")
    for r in fails:
        eng = r["engagement"]
        print(f"  @{r['username'] or r['pdf_handle']} ({r['source']}) | "
              f"Reasons: {'; '.join(r['fail_reasons'])}")

    if no_data:
        print("\n--- NO DATA RETURNED (handle may be wrong or account removed) ---")
        for r in no_data:
            print(f"  PDF handle: @{r['pdf_handle']} ({r['source']})")

    # CSV output
    import csv
    os.makedirs("outputs", exist_ok=True)
    date_str = datetime.date.today().isoformat()
    csv_path = f"outputs/influencer_qualification_{date_str}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "PDF Handle", "IG Handle", "Source PDF", "Followers",
            "Posts Checked", "Consistent Posts (15+)", "Max Comments",
            "Avg Comments", "All Comment Counts", "Bio", "Website", "Verdict"
        ])
        for r in results:
            eng = r["engagement"]
            writer.writerow([
                r["pdf_handle"],
                r["username"] or r["pdf_handle"],
                r["source"],
                r["followers"],
                eng.get("posts_checked", 0),
                eng.get("consistent_posts", 0),
                eng.get("max_comments", 0),
                eng.get("avg_comments", 0),
                str(eng.get("comment_counts", [])),
                r["bio"],
                r["website"],
                r["verdict"],
            ])
    print(f"\n[output] Full report saved to: {csv_path}")


def main():
    print(f"[qualify] Running qualification for {len(UNIQUE_ACCOUNTS)} unique accounts")
    print(f"[qualify] Accounts: {[a[1] for a in UNIQUE_ACCOUNTS]}\n")

    usernames = [actual for _, actual, _ in UNIQUE_ACCOUNTS]
    handle_map = {actual: (pdf, source) for pdf, actual, source in UNIQUE_ACCOUNTS}

    # Scrape all profiles
    profiles = scrape_profiles(usernames)
    print(f"\n[qualify] Scraped {len(profiles)} profiles total")

    # Map profiles back to handles
    profile_map = {}
    for p in profiles:
        uname = (p.get("username") or "").lower().strip()
        if uname:
            profile_map[uname] = p

    # Qualify each account
    results = []
    for pdf_handle, actual_handle, source in UNIQUE_ACCOUNTS:
        profile = profile_map.get(actual_handle.lower())
        if not profile:
            # Account not found
            results.append({
                "pdf_handle": pdf_handle,
                "username": "",
                "source": source,
                "followers": 0,
                "bio": "",
                "website": "",
                "full_name": "",
                "is_private": False,
                "engagement": {},
                "verdict": "NO DATA",
                "fail_reasons": ["not returned by scraper"],
            })
        else:
            results.append(qualify_for_cait_community(profile, pdf_handle, source))

    print_report(results)


if __name__ == "__main__":
    main()
