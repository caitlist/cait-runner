"""
reddit_discovery.py
-------------------
Discovers active Reddit communities for medical parenting and autism caregiving
using Reddit's public JSON API — no credentials required.

Usage:
    python scripts/reddit_discovery.py --category reddit_medical_moms
    python scripts/reddit_discovery.py --category reddit_autism
"""

import os
import sys
import time
import argparse

import requests
from dotenv import load_dotenv

load_dotenv()

MIN_SUBSCRIBERS = 1000

HEADERS = {
    "User-Agent": "cait-lister/1.0 (research bot; contact: caitconnect.app)",
}

# Search terms per category
SEARCH_TERMS = {
    "reddit_medical_moms": [
        "medical parents",
        "medically complex child",
        "special needs parents",
        "medical moms",
        "rare disease parents",
        "medically fragile",
        "NICU parents",
        "pediatric illness",
    ],
    "reddit_autism": [
        "autism parenting",
        "autism parents",
        "ASD parenting",
        "autistic child",
        "autism families",
        "ABA therapy parents",
    ],
}

# Known subreddits to check directly.
# RULE: only include subs where the audience is parents/caregivers OF children —
# not subs for adults living with the condition themselves.
KNOWN_SUBREDDITS = {
    "reddit_medical_moms": [
        "specialneedskids",      # parents of kids with special needs
        "NICUParents",           # NICU parents
        "NICU",                  # NICU community (check via qualifier)
        "MedicalParents",        # explicitly parents
        "raredisease",           # check via qualifier — may be mixed
        "TubeFeeding",           # check via qualifier — often caregivers
        "Preemie",               # preemie parents
        "beyondthebump",         # parenting community
        "Mommit",                # moms community
        "Parenting",             # general parenting
        "specialneedskids",      # parents of special needs kids
    ],
    "reddit_autism": [
        "Autism_Parenting",      # explicitly parenting
        "autismmoms",            # autism moms
        "AutismInChildren",      # focused on children
        "AspergerParents",       # parents of Asperger/ASD kids
        "ABA",                   # ABA therapy (check via qualifier)
        "SPD",                   # sensory processing — mostly parents
        "specialeducation",      # parents/educators (check via qualifier)
    ],
    # EXCLUDED (do not add back):
    # "autism" — primary audience is autistic adults/self-advocates
    # "AutisticParents" — autistic PEOPLE who are parents, not parents OF autistic kids
    # "neurodiversity" — self-advocacy, not caregivers
    # "chronicillness" — people living WITH illness, not parents
    # "DisabledParents" — disabled people who are parents, not parents of disabled kids
    # "CysticFibrosis", "Epilepsy", "type1diabetes", "DownSyndrome" — primarily people WITH the condition
    # "aspergers", "aspergirls", "AutisticAdults", "adultchildren", "CPTSD" — adults with diagnosis
}

# At least one of these must appear in name/title/description to pass
CAREGIVER_SIGNALS = [
    "parent", "parents", "parenting",
    "mom", "moms", "mama", "mamas",
    "dad", "dads",
    "caregiver", "caregivers",
    "raising",
    "families of", "parents of",
    "my child", "my son", "my daughter", "my kid",
]

# If any of these appear in name/description the sub is disqualified —
# it's a community FOR the diagnosed person, not for their caregivers.
ADULT_PATIENT_SIGNALS = [
    "for autistic adults",
    "adults on the spectrum",
    "adults with autism",
    "adults with adhd",
    "adults with add",
    "autistic adults",
    "adults diagnosed",
    "self-diagnosed",
    "if you have autism",
    "if you have adhd",
    "living with autism",
    "living with adhd",
    "living with cptsd",
    "living with ptsd",
    "support for adults",
    "i have autism",
    "i have adhd",
    "i am autistic",
    "we are autistic",
    "aspie",
    "asperger",
    "aspergirls",
    "autistic people",
]

# Humor, satire, and venting subs — not support communities
HUMOR_SIGNALS = [
    "humor", "humour", "satire", "satirical",
    "funny", "laugh", "meme", "memes",
    "cringe", "shitpost", "shit post",
    "things parents say", "things moms say", "things dads say",
    "things kids say",
    "screenshots", "screen shots",
]

# Subreddit names to always block (exact match on lowercased display_name)
BLOCKLIST = {
    "childfree", "antinatalism", "cf4cf", "truechildfree",
    "aspiememes", "dankmemes", "memes",
    # Adult/self-advocacy subs — FOR the diagnosed person, not caregivers
    "autism",             # primary: autistic adults/self-advocates
    "autisticadults",
    "aspergers",
    "aspergirls",
    "aspie",
    "neurodiversity",     # self-advocacy community
    "autisticparents",    # autistic people who are parents
    "chronicillness",     # people WITH illness
    "disabledparents",    # disabled people who are parents
    "cptsd",
    "ptsd",
    "bpd",
    "adultchildren",
    "raisedbynarcissists",
    "bipolar",
    "depression",
    "anxiety",
    "adhd",               # primarily adults with ADHD
    "adhdwomen",
    "adhdmeme",
    # Humor / satire / venting subs (confirmed bad)
    "insaneparents",
    "shitmomgroupssay",
    "wokekids",
    "raisedbyborderlines",
    "emotionalneglect",
    "weightlossafterbaby",
    "electivecsection",
}

DISQUALIFY_SIGNALS = [
    "child free", "childfree", "don't want children", "antinatalism",
]


def reddit_get(url: str, params: dict = None) -> dict | None:
    """GET request to Reddit JSON API with polite rate limiting."""
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            print("[reddit] Rate limited — waiting 30s...")
            time.sleep(30)
            resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(f"[reddit] Request error: {e}")
    return None


def search_subreddits(query: str, limit: int = 15) -> list[str]:
    """Search Reddit for subreddits matching a query."""
    data = reddit_get(
        "https://www.reddit.com/subreddits/search.json",
        params={"q": query, "limit": limit, "type": "sr"},
    )
    if not data:
        return []
    children = data.get("data", {}).get("children", [])
    return [c["data"]["display_name"] for c in children]


def get_subreddit_info(name: str) -> dict | None:
    """Fetch subreddit about data."""
    data = reddit_get(f"https://www.reddit.com/r/{name}/about.json")
    if not data:
        return None
    return data.get("data", {})


def check_activity(name: str) -> bool:
    """Check if subreddit had a post in the last 7 days."""
    data = reddit_get(
        f"https://www.reddit.com/r/{name}/new.json",
        params={"limit": 5},
    )
    if not data:
        return False
    posts = data.get("data", {}).get("children", [])
    for post in posts:
        age_days = (time.time() - post["data"].get("created_utc", 0)) / 86400
        if age_days <= 7:
            return True
    return False


def qualify_subreddit(name: str, category: str) -> dict | None:
    """Check subreddit against all qualification filters."""
    # Block known irrelevant communities by name
    if name.lower() in BLOCKLIST:
        print(f"[reddit] r/{name} — blocklisted, skipping")
        return None

    info = get_subreddit_info(name)
    if not info:
        return None

    # Skip private, banned, or restricted
    sub_type = info.get("subreddit_type", "")
    if sub_type not in ("public", "restricted"):
        return None

    subscribers = info.get("subscribers") or 0
    if subscribers < MIN_SUBSCRIBERS:
        print(f"[reddit] r/{name} — too small ({subscribers:,} subscribers)")
        return None

    # Audience check — must be FOR parents/caregivers of children, not adults with the condition
    description = (info.get("public_description") or info.get("description") or "").lower()
    title = (info.get("title") or "").lower()
    name_lower = name.lower()
    combined = f"{title} {description} {name_lower}"

    # Hard disqualify: anti-parent or self-diagnosis/adult-patient community
    if any(sig in combined for sig in DISQUALIFY_SIGNALS):
        print(f"[reddit] r/{name} — disqualified (anti-parent signal), skipping")
        return None

    if any(sig in combined for sig in ADULT_PATIENT_SIGNALS):
        print(f"[reddit] r/{name} — disqualified (adult/self-diagnosis audience), skipping")
        return None

    if any(sig in combined for sig in HUMOR_SIGNALS):
        print(f"[reddit] r/{name} — disqualified (humor/satire/venting sub), skipping")
        return None

    # Require at least one explicit caregiver-of-child signal
    has_caregiver_signal = any(kw in combined for kw in CAREGIVER_SIGNALS)
    if not has_caregiver_signal:
        print(f"[reddit] r/{name} — no caregiver-of-child signal found, skipping")
        return None

    # Activity check
    if not check_activity(name):
        print(f"[reddit] r/{name} — inactive (no posts in 7 days)")
        return None

    # Get mods (top 3, skip AutoModerator)
    mods_data = reddit_get(f"https://www.reddit.com/r/{name}/about/moderators.json")
    mods = []
    if mods_data:
        for mod in mods_data.get("data", {}).get("children", [])[:5]:
            mod_name = mod.get("name", "")
            if mod_name and mod_name != "AutoModerator":
                mods.append(f"u/{mod_name}")
            if len(mods) >= 3:
                break

    print(f"[reddit] Qualified: r/{name} | {subscribers:,} subscribers")

    return {
        "community_name": f"r/{info.get('display_name', name)}",
        "group_link": f"https://reddit.com/r/{info.get('display_name', name)}",
        "num_members": subscribers,
        "admin": ", ".join(mods),
    }


def run(category: str, batch_size: int = 5) -> list[dict]:
    """Full pipeline: known list + search → qualify → return results."""
    print(f"\n[reddit] Starting discovery for category: {category}")

    candidates = set(KNOWN_SUBREDDITS.get(category, []))

    for query in SEARCH_TERMS.get(category, []):
        print(f"[reddit] Searching: '{query}'")
        found = search_subreddits(query)
        candidates.update(found)
        time.sleep(1)

    print(f"[reddit] Checking {len(candidates)} candidate subreddits...")

    qualified = []
    seen = set()

    for name in candidates:
        if len(qualified) >= batch_size * 3:
            break
        if name.lower() in seen:
            continue
        seen.add(name.lower())

        result = qualify_subreddit(name, category)
        if result:
            qualified.append(result)
        time.sleep(1)  # Polite delay

    qualified.sort(key=lambda x: x["num_members"], reverse=True)

    print(f"\n[reddit] Found {len(qualified)} qualified communities")
    return qualified[:batch_size * 2]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", required=True,
                        choices=["reddit_medical_moms", "reddit_autism"])
    parser.add_argument("--batch-size", type=int, default=5)
    args = parser.parse_args()

    results = run(args.category, args.batch_size)
    print(f"\nResults preview ({len(results)} communities):")
    for r in results:
        print(f"  {r['community_name']} | {r['num_members']:,} members | mods: {r['admin']}")
