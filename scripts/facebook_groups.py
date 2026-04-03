"""
facebook_groups.py
------------------
Searches for Facebook parent groups using Apify's Google Search Scraper
(apify/google-search-scraper). No rental required — pay per use only.

Uses Google dork queries: site:facebook.com/groups "[diagnosis] moms" USA
to discover group URLs and metadata from Google search results.

Usage:
    python scripts/facebook_groups.py --category facebook_autism
    python scripts/facebook_groups.py --category facebook_medical_moms
    python scripts/facebook_groups.py --category facebook_philippines
    python scripts/facebook_groups.py --category facebook_all
"""

import os
import re
import sys
import time
import argparse

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.environ.get("APIFY_TOKEN")

# Apify actor: apify/google-search-scraper
# No rental required — pay per use (~$0.002 per query)
GOOGLE_SEARCH_ACTOR_ID = "apify/google-search-scraper"

# ------------------------------------------------------------------
# Search queries per category
# All use Google dork: site:facebook.com/groups to surface FB group URLs
# ------------------------------------------------------------------
SEARCH_QUERIES = {
    "facebook_autism": [
        'site:facebook.com/groups "autism moms" USA',
        'site:facebook.com/groups "autism parents" "United States"',
        'site:facebook.com/groups "autism families" USA',
        'site:facebook.com/groups "autism parent support" USA',
        'site:facebook.com/groups "ASD parents" USA',
    ],
    "facebook_medical_moms": [
        'site:facebook.com/groups "medical moms" USA',
        'site:facebook.com/groups "medically complex" parents USA',
        'site:facebook.com/groups "special needs" medical moms USA',
        'site:facebook.com/groups "medically fragile" parents USA',
        'site:facebook.com/groups "medical mom support" USA',
    ],
    "facebook_trach": [
        'site:facebook.com/groups "trach moms" OR "tracheostomy" parents',
        'site:facebook.com/groups "trach baby" parents support',
    ],
    "facebook_feeding_tube": [
        'site:facebook.com/groups "feeding tube" moms USA',
        'site:facebook.com/groups "g-tube" parents USA',
        'site:facebook.com/groups "tube fed" kids parents',
    ],
    "facebook_epilepsy": [
        'site:facebook.com/groups "epilepsy moms" USA',
        'site:facebook.com/groups "seizure" parents USA support',
        'site:facebook.com/groups "Dravet syndrome" parents',
    ],
    "facebook_t1d": [
        'site:facebook.com/groups "type 1 diabetes" moms USA',
        'site:facebook.com/groups "T1D" parents USA',
        'site:facebook.com/groups "pediatric diabetes" parents USA',
    ],
    "facebook_down_syndrome": [
        'site:facebook.com/groups "Down syndrome" moms USA',
        'site:facebook.com/groups "Trisomy 21" parents USA',
        'site:facebook.com/groups "Down syndrome" parents support USA',
    ],
    "facebook_cerebral_palsy": [
        'site:facebook.com/groups "cerebral palsy" parents USA',
        'site:facebook.com/groups "CP moms" support USA',
    ],
    "facebook_nicu": [
        'site:facebook.com/groups "NICU moms" USA',
        'site:facebook.com/groups "preemie" parents USA',
        'site:facebook.com/groups "premature baby" parents USA',
    ],
    "facebook_pediatric_cancer": [
        'site:facebook.com/groups "pediatric cancer" moms USA',
        'site:facebook.com/groups "childhood cancer" parents USA',
    ],
    "facebook_cystic_fibrosis": [
        'site:facebook.com/groups "cystic fibrosis" parents USA',
        'site:facebook.com/groups "CF moms" support USA',
    ],
    "facebook_rare_disease": [
        'site:facebook.com/groups "rare disease" parents USA',
        'site:facebook.com/groups "undiagnosed" children parents USA',
        'site:facebook.com/groups "Angelman syndrome" parents',
        'site:facebook.com/groups "Rett syndrome" parents',
    ],
    "facebook_philippines": [
        'site:facebook.com/groups autism Philippines',
        'site:facebook.com/groups "special needs" Philippines parents',
        'site:facebook.com/groups "medical moms" Philippines',
        'site:facebook.com/groups autism moms Manila OR Cebu OR Davao',
        'site:facebook.com/groups "Down syndrome" Philippines',
        'site:facebook.com/groups epilepsy Philippines parents',
    ],
}

# All USA categories combined
FACEBOOK_ALL_USA_CATEGORIES = [
    "facebook_autism",
    "facebook_medical_moms",
    "facebook_trach",
    "facebook_feeding_tube",
    "facebook_epilepsy",
    "facebook_t1d",
    "facebook_down_syndrome",
    "facebook_cerebral_palsy",
    "facebook_nicu",
    "facebook_pediatric_cancer",
    "facebook_cystic_fibrosis",
    "facebook_rare_disease",
]

# Signals that the group is for parents/caregivers of children
CAREGIVER_SIGNALS = [
    "mom", "moms", "mama", "mamas", "mommy",
    "dad", "dads", "daddy",
    "parent", "parents", "parenting",
    "caregiver", "caregivers",
    "family", "families",
    "raising",
]

# Groups for adults with the diagnosis — reject
ADULT_PATIENT_SIGNALS = [
    "adults with autism",
    "adults with adhd",
    "autistic adults",
    "living with autism",
    "for autistic people",
    "for people with autism",
    "autistic self",
    "aspie",
    "i have autism",
]

USA_SIGNALS = [
    "usa", "united states", "u.s.", "america", "american",
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming",
    "dfw", "nyc", "la ", "chicago",
]

PHILIPPINES_SIGNALS = [
    "philippines", "pilipinas", "filipino", "pilipino",
    "manila", "cebu", "davao", "quezon", "ph ", ".ph", "pinay", "pinoy",
]


def extract_member_count(text: str) -> int:
    """Try to extract member count from Google snippet text."""
    if not text:
        return 0
    # Patterns: "142,000 members", "10K members", "142K"
    text = text.replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*[Kk]\s*members", text)
    if match:
        return int(float(match.group(1)) * 1000)
    match = re.search(r"(\d+(?:\.\d+)?)\s*[Mm]\s*members", text)
    if match:
        return int(float(match.group(1)) * 1_000_000)
    match = re.search(r"(\d{3,})\s*members", text)
    if match:
        return int(match.group(1))
    return 0


import re as _re


def _extract_group_name_from_url(url: str) -> str:
    """Pull group name slug from Facebook URL as fallback."""
    try:
        slug = url.split("/groups/")[-1].strip("/").split("/")[0]
        if slug.isdigit():
            return ""  # Pure numeric ID — not a usable name
        # Convert slug to readable name: hyphens/underscores to spaces, title case
        return slug.replace("-", " ").replace("_", " ").title()
    except Exception:
        return ""


def _is_valid_group_name(name: str) -> bool:
    """
    Return True if the name looks like a real Facebook group name.
    Rejects: post titles, questions, truncated snippets, numeric IDs, URL slugs.
    """
    if not name:
        return False
    name_s = name.strip()

    # Too long — truncated post snippet
    if len(name_s) > 80:
        return False

    # Contains "..." — truncated post snippet
    if "..." in name_s:
        return False

    # Pure numeric ID (group IDs shown when page isn't indexed)
    if name_s.isdigit():
        return False

    # Single camelCase or all-lowercase word with no spaces — URL slug used as name
    # e.g. "Supportautism", "Autismparenting", "Createdincanva", "Mmbcolorado"
    if " " not in name_s and name_s[0].isupper() and name_s[1:].islower():
        # Single word title-cased from slug — reject if it looks like a slug
        if len(name_s) > 8:  # Real group names with no space tend to be acronyms (NICU, ASD, T1D)
            return False

    # Ends with "?" — always a post/question
    if name_s.endswith("?"):
        return False

    # Starts with a question word — post, not group name
    question_starts = (
        "what ", "which ", "where ", "who ", "how ", "why ",
        "does ", "is ", "are ", "can ", "has ", "have ",
        "should ", "would ", "could ", "do "
    )
    name_lower = name_s.lower()
    if any(name_lower.startswith(q) for q in question_starts):
        return False

    # Personal/narrative statement starts — clearly a post
    personal_starts = (
        "i'm ", "i am ", "i've ", "i have ", "once i ", "just a ",
        "hi ", "hey ", "hello ", "dear ", "as a mom", "as school",
        "sunday facts", "celebrating ", "carrigan ", "advice for",
        "mother ", "mother with ", "mothers ", "states that ",
        "caregivers can ", "women living ", "childhood epilepsy ",
        "raising a child", "parents of children with down",
        "special needs mom seeking", "medical mom support and",
    )
    if any(name_lower.startswith(p) for p in personal_starts):
        return False

    # Contains "..." at any point or other post artifacts
    post_artifacts = (
        "...", "free new ", "freebie", "doctor alert",
        "ng/j/g", "camelcase", "createdinca",
        "amazon wish list", "wish lists for support",
        "seeking professional collaborations",
        "support and gifting",
    )
    if any(a in name_lower for a in post_artifacts):
        return False

    # Must contain at least one letter (not just symbols/numbers)
    if not _re.search(r"[a-zA-Z]", name_s):
        return False

    return True


def qualify_result(result: dict, geography: str = "usa") -> dict | None:
    """
    Qualify a Google search result as a Facebook group.
    Returns cleaned dict or None if disqualified.
    """
    url = result.get("url", "") or result.get("link", "") or ""
    title = result.get("title", "") or ""
    description = result.get("description", "") or result.get("snippet", "") or ""

    # Must be a Facebook group URL
    if "facebook.com/groups/" not in url.lower():
        return None

    # Extract group name from title (Google title format: "Group Name | Facebook")
    if "|" in title:
        name = title.split("|")[0].strip()
    else:
        name = title.strip()

    # Remove emoji and non-ASCII characters
    name = name.encode("ascii", errors="ignore").decode("ascii").strip()

    # If title doesn't look like a real group name, fall back to URL slug
    if not _is_valid_group_name(name):
        name = _extract_group_name_from_url(url)
        if not _is_valid_group_name(name):
            return None  # Can't get a usable name — skip

    combined = f"{name} {description}".lower()

    # Adult-patient filter
    if any(sig in combined for sig in ADULT_PATIENT_SIGNALS):
        return None

    # Geography filter — check name + description + URL
    url_and_combined = f"{url} {combined}"
    if geography == "usa":
        if not any(sig in url_and_combined for sig in USA_SIGNALS):
            return None
    elif geography == "philippines":
        if not any(sig in url_and_combined for sig in PHILIPPINES_SIGNALS):
            return None

    # Extract member count from snippet
    members = extract_member_count(description)

    return {
        "community_name": name,
        "group_link": url.split("?")[0].rstrip("/"),  # Clean URL
        "num_members": str(members) if members > 0 else "Verify on FB",
        "admin": "",
    }


def search_google_for_groups(queries: list[str], max_results_per_query: int = 10) -> list[dict]:
    """
    Run Apify Google Search Scraper for a list of queries.
    Returns raw search results.
    """
    if not APIFY_TOKEN:
        raise ValueError("APIFY_TOKEN not set in .env")

    client = ApifyClient(APIFY_TOKEN)
    all_results = []

    for query in queries:
        print(f"[facebook_groups] Google search: '{query}'")
        try:
            run_input = {
                "queries": query,
                "maxPagesPerQuery": 1,
                "resultsPerPage": max_results_per_query,
                "countryCode": "us",
                "languageCode": "en",
            }
            run = client.actor(GOOGLE_SEARCH_ACTOR_ID).call(run_input=run_input)
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            # Google scraper returns nested structure: items[0]["organicResults"]
            for item in items:
                organic = item.get("organicResults", [])
                all_results.extend(organic)
            print(f"[facebook_groups] Got {len(items)} result pages for '{query}'")
            time.sleep(1)
        except Exception as e:
            print(f"[facebook_groups] Error for query '{query}': {e}")
            continue

    return all_results


def run(category: str, batch_size: int = 25, geography: str = "usa") -> list[dict]:
    """
    Full pipeline: Google search -> extract FB group URLs -> qualify -> return results.
    """
    print(f"\n[facebook_groups] Starting search for category: {category}")

    # Resolve 'facebook_all' to all USA categories
    if category == "facebook_all":
        all_queries = []
        for cat in FACEBOOK_ALL_USA_CATEGORIES:
            all_queries.extend(SEARCH_QUERIES.get(cat, []))
        geography = "usa"
    else:
        all_queries = SEARCH_QUERIES.get(category, [])
        geography = "philippines" if category == "facebook_philippines" else "usa"

    if not all_queries:
        raise ValueError(f"No search queries defined for category: {category}")

    raw_results = search_google_for_groups(all_queries)
    print(f"[facebook_groups] Total raw results: {len(raw_results)}")

    qualified = []
    seen_names = set()
    seen_urls = set()

    for result in raw_results:
        qualified_result = qualify_result(result, geography=geography)
        if not qualified_result:
            continue

        name_key = qualified_result["community_name"].lower().strip()
        url_key = qualified_result["group_link"].lower().strip()
        if name_key in seen_names or url_key in seen_urls:
            continue

        seen_names.add(name_key)
        seen_urls.add(url_key)
        qualified.append(qualified_result)
        safe_name = qualified_result['community_name'].encode('ascii', errors='replace').decode('ascii')
        print(f"[facebook_groups] Qualified: {safe_name}")

        if len(qualified) >= batch_size * 2:
            break

    # Sort by member count descending (numeric members first, then "Verify on FB")
    def sort_key(r):
        try:
            return -int(r["num_members"].replace(",", ""))
        except (ValueError, AttributeError):
            return 0

    qualified.sort(key=sort_key)

    print(f"[facebook_groups] Found {len(qualified)} qualified groups")
    return qualified[:batch_size * 2]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--category",
        required=True,
        choices=list(SEARCH_QUERIES.keys()) + ["facebook_all"],
        help="Category to search",
    )
    parser.add_argument("--batch-size", type=int, default=25)
    args = parser.parse_args()

    results = run(args.category, args.batch_size)
    print(f"\nResults preview ({len(results)} groups):")
    for r in results:
        print(f"  - {r['community_name']} | {r['num_members']} members | {r['group_link']}")
