"""
instagram_foundations.py
------------------------
Discovers and qualifies medical parent foundations & advocacy organizations
on Instagram using a curated seed list (not hashtag scraping).

Unlike journey accounts (50 Million List) or therapist sellers (CAIT Community),
foundations are institutional accounts — different qualification rules apply.

Usage:
    python scripts/instagram_foundations.py --batch-size 20 --dry-run
    python scripts/instagram_foundations.py --batch-size 20
"""

import os
import re
import sys
import time
import argparse
import datetime

import requests
from bs4 import BeautifulSoup
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY")

PROFILE_ACTOR = "apify/instagram-scraper"  # NOT profile-scraper — gets blocked

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    )
}

EMAIL_STRICT = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

# Seed list of known medical parent foundations & advocacy orgs
# Handles are best-guess — Apify will validate. If a handle returns nothing,
# it's logged as "handle not found" and skipped.
SEED_LIST = [
    # Down Syndrome
    {
        "org_name": "National Down Syndrome Society",
        "handle": "ndssorg",
        "website": "https://www.ndss.org",
        "diagnosis": "Down syndrome",
    },
    {
        "org_name": "Global Down Syndrome Foundation",
        "handle": "globaldownsyndrome",
        "website": "https://www.globaldownsyndrome.org",
        "diagnosis": "Down syndrome",
    },
    # Epilepsy
    {
        "org_name": "Epilepsy Foundation",
        "handle": "epilepsyfdn",
        "website": "https://www.epilepsy.com",
        "diagnosis": "Epilepsy",
    },
    {
        "org_name": "Dravet Syndrome Foundation",
        "handle": "dravetsyndromefoundation",
        "website": "https://www.dravetfoundation.org",
        "diagnosis": "Epilepsy / Dravet syndrome",
    },
    {
        "org_name": "LGS Foundation",
        "handle": "lgsfoundation",
        "website": "https://www.lgsfoundation.org",
        "diagnosis": "Epilepsy / Lennox-Gastaut",
    },
    # Pediatric Cancer
    {
        "org_name": "St. Baldrick's Foundation",
        "handle": "stbaldricks",
        "website": "https://www.stbaldricks.org",
        "diagnosis": "Pediatric cancer",
    },
    {
        "org_name": "Alex's Lemonade Stand Foundation",
        "handle": "alexslemonade",
        "website": "https://www.alexslemonade.org",
        "diagnosis": "Pediatric cancer",
    },
    {
        "org_name": "American Childhood Cancer Organization",
        "handle": "accorg",
        "website": "https://www.acco.org",
        "diagnosis": "Pediatric cancer",
    },
    # Cystic Fibrosis
    {
        "org_name": "Cystic Fibrosis Foundation",
        "handle": "cf_foundation",
        "website": "https://www.cff.org",
        "diagnosis": "Cystic fibrosis",
    },
    # Rare Diseases
    {
        "org_name": "National Organization for Rare Disorders",
        "handle": "nord_rare",
        "website": "https://www.rarediseases.org",
        "diagnosis": "Rare diseases",
    },
    # Type 1 Diabetes
    {
        "org_name": "Breakthrough T1D (formerly JDRF)",
        "handle": "breakthrought1d",
        "website": "https://www.breakthrought1d.org",
        "diagnosis": "Type 1 diabetes",
        # NOTE: Rebranded from JDRF June 2024. Previously flagged stale — confirmed active
        # post-rebrand (~112K followers). @beyondtype1 also covers this category.
    },
    {
        "org_name": "Beyond Type 1",
        "handle": "beyondtype1",
        "website": "https://beyondtype1.org",
        "diagnosis": "Type 1 diabetes",
    },
    # Autism
    {
        "org_name": "Autism Society of America",
        "handle": "autismsociety",
        "website": "https://autismsociety.org",
        "diagnosis": "Autism",
    },
    {
        "org_name": "NEXT for AUTISM",
        "handle": "nextforautism",
        "website": "https://www.nextforautism.org",
        "diagnosis": "Autism",
    },
    # NOTE: Autism Speaks (@autismspeaks) is large but controversial in the autism
    # community. Flagged here for Cherwin to decide — not included in default run.
    # Cerebral Palsy
    {
        "org_name": "Cerebral Palsy Research Foundation",
        "handle": "researchforcp",
        "website": "https://cprf.org",
        "diagnosis": "Cerebral palsy",
    },
    # Medically Complex / CSHCN
    {
        "org_name": "Family Voices",
        "handle": "familyvoicesnational",
        "website": "https://familyvoices.org",
        "diagnosis": "Medically complex / CSHCN",
    },
    # NICU / Premature Birth
    {
        "org_name": "March of Dimes",
        "handle": "marchofdimes",
        "website": "https://www.marchofdimes.org",
        "diagnosis": "NICU / Premature birth",
    },
    {
        "org_name": "Graham's Foundation",
        "handle": "grahamsfoundation",
        "website": "https://grahamsfoundation.org",
        "diagnosis": "NICU / Premature birth",
    },
    {
        "org_name": "Dear NICU Mama",
        "handle": "dearnicumama",
        "website": "https://www.dearnicumama.com",
        "diagnosis": "NICU / Premature birth",
    },
    {
        "org_name": "Project NICU",
        "handle": "projectnicu",
        "website": "https://projectnicu.org",
        "diagnosis": "NICU / Premature birth",
    },
    {
        "org_name": "Hand to Hold",
        "handle": "handtohold",
        "website": "https://handtohold.org",
        "diagnosis": "NICU / Premature birth",
    },
    # Medically Complex / Special Needs
    {
        "org_name": "Special Needs Network",
        "handle": "specialneedsnetwork",
        "website": "https://www.snnla.org",
        "diagnosis": "Medically complex / Special needs",
    },
    # Rare Disease Community
    {
        "org_name": "Rare Village",
        "handle": "therarevillage",
        "website": "https://therarevillage.com",
        "diagnosis": "Rare diseases",
    },
    {
        "org_name": "The Children's Rare Disorders Fund",
        "handle": "thecrdfund",
        "website": "https://www.thecrdfund.org",
        "diagnosis": "Rare diseases",
    },
    # Congenital Heart Disease (CHD)
    {
        "org_name": "Mended Little Hearts",
        "handle": "mendedlittleheartsnational",
        "website": "https://mendedlittlehearts.org",
        "diagnosis": "CHD / Congenital heart disease",
    },
    {
        "org_name": "Children's Heart Foundation",
        "handle": "thechf",
        "website": "https://www.childrensheartfoundation.org",
        "diagnosis": "CHD / Congenital heart disease",
    },
    # Spina Bifida
    {
        "org_name": "Spina Bifida Association",
        "handle": "spinabifidaassn",
        "website": "https://www.spinabifidaassociation.org",
        "diagnosis": "Spina bifida",
    },
    # Muscular Dystrophy
    {
        "org_name": "Parent Project Muscular Dystrophy",
        "handle": "parentprojectmd",
        "website": "https://www.parentprojectmd.org",
        "diagnosis": "Muscular dystrophy / Duchenne",
    },
    # Rett Syndrome
    {
        "org_name": "International Rett Syndrome Foundation",
        "handle": "rettsyndromeorg",
        "website": "https://www.rettsyndrome.org",
        "diagnosis": "Rett syndrome",
    },
    # PKU / Metabolic Disorders
    {
        "org_name": "National PKU Alliance",
        "handle": "national_pku_alliance",
        "website": "https://www.npkua.org",
        "diagnosis": "PKU / Metabolic disorders",
    },
    # Hydrocephalus
    {
        "org_name": "Hydrocephalus Association",
        "handle": "hydroassoc",
        "website": "https://www.hydroassoc.org",
        "diagnosis": "Hydrocephalus",
    },
    # Feeding / G-tube
    {
        "org_name": "Oley Foundation",
        "handle": "the_oley_foundation",
        "website": "https://oley.org",
        "diagnosis": "Feeding / G-tube / Home nutrition",
        # NOTE: Oley acquired the Feeding Tube Awareness Foundation in Spring 2025.
        # They are now the active successor org carrying that mission.
    },
    {
        "org_name": "Tubie Friends",
        "handle": "tubiefriends",
        "website": "https://www.tubiefriends.org",
        "diagnosis": "Feeding / G-tube",
        # NOTE: Parent-run nonprofit, ~2.8K followers. Small but active and mission-aligned.
    },
    {
        "org_name": "Feeding Matters",
        "handle": "feedingmatters",
        "website": "https://www.feedingmatters.org",
        "diagnosis": "Feeding / Pediatric feeding disorders",
        # NOTE: Was flagged stale (153 days) in prior session. Org is operationally active
        # (running 2026 conference). Script will re-evaluate IG post frequency — disqualifies
        # automatically if still outside 90-day window.
    },
    # ADHD
    {
        "org_name": "CHADD",
        "handle": "chadd_help4adhd",
        "website": "https://chadd.org",
        "diagnosis": "ADHD",
        # NOTE: Children and Adults with ADHD. ~19K followers, credentialed, no controversy.
    },
    # Autism (additional — controversial, Cherwin approved with flag)
    {
        "org_name": "TACA (The Autism Community in Action)",
        "handle": "tacanow",
        "website": "https://tacanow.org",
        "diagnosis": "Autism",
        # NOTE: ~26K followers, active. CONTROVERSY FLAG: Legacy association with anti-vaccine
        # movement (2008 march, Wakefield defense). Renamed from "Talk About Curing Autism" in 2019.
        # Mikha must be aware before outreach — risk of alienating neurodiversity-affirming families.
        # Cherwin approved inclusion with this flag noted in sheet Notes column.
    },
]

# Org-specific qualification: more lenient than individual accounts
FOLLOWER_FLOOR = 1_000          # Orgs below this aren't meaningful partnership targets
DAYS_SINCE_POST = 90            # Orgs post less frequently than individuals
SKIP_DOMAINS = {
    "tap.bio", "lnk.bio", "portaly.cc", "flodesk.com",
    "myflodesk.com", "spoti.fi", "komi.io", "linktr.ee",
}

# Pages to check for exec contact info
LEADERSHIP_PATHS = [
    "/about",
    "/about-us",
    "/leadership",
    "/team",
    "/staff",
    "/our-team",
    "/board",
    "/contact",
    "/contact-us",
    "/partnerships",
    "/partner-with-us",
]

EXEC_TITLE_SIGNALS = [
    "executive director", "president", "ceo", "chief executive",
    "director of communications", "director of partnerships",
    "director of programs", "vp of", "vice president",
    "communications manager", "partnerships manager",
]


# ---------------------------------------------------------------------------
# Apify: scrape profiles from seed handles
# ---------------------------------------------------------------------------

def scrape_profiles(handles: list[str]) -> list[dict]:
    """Fetch Instagram profile data for a list of handles via Apify."""
    client = ApifyClient(APIFY_TOKEN)
    results = []

    for i in range(0, len(handles), 20):
        batch = handles[i:i+20]
        try:
            run_input = {
                "directUrls": [f"https://www.instagram.com/{h}/" for h in batch],
                "resultsType": "details",
                "resultsLimit": 5,   # Only need recent posts to check activity
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
            print(f"[foundations] Apify error for batch {i}: {e}")

    return results


# ---------------------------------------------------------------------------
# Qualification: org-specific rules (no gender filter, no engagement floor)
# ---------------------------------------------------------------------------

def most_recent_post_days_ago(posts: list) -> int | None:
    """Return how many days ago the most recent post was published."""
    today = datetime.date.today()
    for post in posts:
        if not isinstance(post, dict):
            continue
        timestamp = post.get("timestamp") or post.get("takenAt") or ""
        if not timestamp:
            continue
        try:
            if isinstance(timestamp, (int, float)):
                post_date = datetime.datetime.utcfromtimestamp(timestamp).date()
            else:
                post_date = datetime.date.fromisoformat(str(timestamp)[:10])
            return (today - post_date).days
        except Exception:
            continue
    return None


def qualify_org(profile: dict, seed: dict) -> dict | None:
    """
    Apply org qualification filters. Returns qualified dict or None.
    """
    username = (profile.get("username") or "").lower().strip()
    bio = profile.get("biography") or profile.get("bio") or ""
    followers = profile.get("followersCount") or profile.get("followers") or 0
    is_private = profile.get("isPrivate") or False
    website = profile.get("externalUrl") or profile.get("website") or seed.get("website", "")

    # Must be public
    if is_private:
        print(f"[foundations] SKIP @{username} — private account")
        return None

    # Must have a username
    if not username:
        return None

    # Follower floor
    if int(followers) < FOLLOWER_FLOOR:
        print(f"[foundations] SKIP @{username} — {followers} followers (below {FOLLOWER_FLOOR:,} floor)")
        return None

    # Activity check — posted within last 90 days
    posts = profile.get("latestPosts") or profile.get("posts") or []
    days_ago = most_recent_post_days_ago(posts)
    if days_ago is not None and days_ago > DAYS_SINCE_POST:
        print(f"[foundations] SKIP @{username} — last post {days_ago} days ago (stale)")
        return None

    # Skip link aggregator domains (not useful for enrichment)
    website_domain = re.sub(r"https?://(www\.)?", "", website).split("/")[0].lower()
    if website_domain in SKIP_DOMAINS:
        website = seed.get("website", "")  # Fall back to known website

    return {
        "org_name": seed["org_name"],
        "username": username,
        "profile_link": f"https://instagram.com/{username}",
        "website": website or seed.get("website", ""),
        "diagnosis": seed["diagnosis"],
        "followers": int(followers),
        "email": "",
        "email_source": "not found",
        "exec_contact_name": "",
        "exec_contact_title": "",
        "notes": "",
        "_bio": bio,
    }


# ---------------------------------------------------------------------------
# Exec contact enrichment
# ---------------------------------------------------------------------------

def extract_email(text: str) -> str | None:
    match = EMAIL_STRICT.search(text)
    if match:
        return match.group().lower().strip()
    return None


def scrape_page(url: str, timeout: int = 8) -> str:
    """Fetch a URL and return its text content, or empty string on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            return soup.get_text(separator=" ", strip=True)
    except Exception:
        pass
    return ""


def find_exec_contact_on_website(website: str) -> dict:
    """
    Scrape org website leadership/about/contact pages for exec name + email.
    Returns {"name": ..., "title": ..., "email": ..., "source": ...}
    """
    base = website.rstrip("/")
    result = {"name": "", "title": "", "email": "", "source": "not found"}

    for path in LEADERSHIP_PATHS:
        url = base + path
        text = scrape_page(url)
        if not text:
            continue

        # Look for exec title signals
        text_lower = text.lower()
        for title in EXEC_TITLE_SIGNALS:
            if title in text_lower:
                # Try to find adjacent name (crude: look for Title Pattern "Name, Title")
                # Pattern: any 2-3 capitalized words near a title mention
                pattern = re.compile(
                    r"([A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?)"
                    r"(?:[,\s\|]{1,10}" + re.escape(title) + r"|"
                    + re.escape(title) + r"[,\s\|]{1,10})",
                    re.IGNORECASE
                )
                match = pattern.search(text)
                if match:
                    result["name"] = match.group(1).strip()
                    result["title"] = title.title()

                email = extract_email(text)
                if email:
                    result["email"] = email
                    result["source"] = f"website:{path}"
                    return result

                # Found title but no email on this page — keep looking
                if result["name"]:
                    result["source"] = f"website:{path} (no email)"
                break

        # Even without a title match, grab any email on the page
        if not result["email"]:
            email = extract_email(text)
            if email:
                result["email"] = email
                result["source"] = f"website:{path}"

        if result["email"]:
            return result

        time.sleep(0.5)

    return result


def hunter_domain_search(domain: str) -> dict:
    """Search Hunter.io for org email by domain."""
    if not HUNTER_API_KEY:
        return {}
    try:
        resp = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={"domain": domain, "api_key": HUNTER_API_KEY, "limit": 3},
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            emails = data.get("emails", [])
            # Prefer director/communications/partnerships over generic contacts
            for priority_word in ["director", "communications", "partnerships", "executive", "president"]:
                for e in emails:
                    position = (e.get("position") or "").lower()
                    if priority_word in position:
                        return {
                            "email": e.get("value", ""),
                            "name": f"{e.get('first_name', '')} {e.get('last_name', '')}".strip(),
                            "title": e.get("position", ""),
                            "source": "hunter",
                        }
            # Fallback: first email
            if emails:
                e = emails[0]
                return {
                    "email": e.get("value", ""),
                    "name": f"{e.get('first_name', '')} {e.get('last_name', '')}".strip(),
                    "title": e.get("position", ""),
                    "source": "hunter",
                }
    except Exception:
        pass
    return {}


def enrich_org(org: dict) -> dict:
    """
    Find exec contact for an org.
    Pipeline: bio email → website About/Team scrape → Hunter domain search
    """
    # 1. Bio email
    bio_email = extract_email(org.get("_bio", ""))
    if bio_email:
        org["email"] = bio_email
        org["email_source"] = "bio"
        return org

    website = org.get("website", "")
    if not website:
        return org

    # 2. Website scrape
    website_result = find_exec_contact_on_website(website)
    if website_result["email"]:
        org["email"] = website_result["email"]
        org["email_source"] = website_result["source"]
        if website_result["name"]:
            org["exec_contact_name"] = website_result["name"]
        if website_result["title"]:
            org["exec_contact_title"] = website_result["title"]
        return org

    if website_result["name"]:
        org["exec_contact_name"] = website_result["name"]
        org["exec_contact_title"] = website_result.get("title", "")

    # 3. Hunter domain search
    domain = re.sub(r"https?://(www\.)?", "", website).split("/")[0]
    if domain:
        hunter_result = hunter_domain_search(domain)
        if hunter_result.get("email"):
            org["email"] = hunter_result["email"]
            org["email_source"] = hunter_result.get("source", "hunter")
            if not org["exec_contact_name"] and hunter_result.get("name"):
                org["exec_contact_name"] = hunter_result["name"]
            if not org["exec_contact_title"] and hunter_result.get("title"):
                org["exec_contact_title"] = hunter_result["title"]

    return org


# ---------------------------------------------------------------------------
# Main run function
# ---------------------------------------------------------------------------

def run(batch_size: int = 20) -> list[dict]:
    """
    Full pipeline:
      1. Pull profile data for all seed handles via Apify
      2. Qualify against org-specific filters
      3. Enrich with exec contact info
      4. Return qualified list

    No category or diagnosis args needed — seed list covers all.
    """
    print(f"\n[foundations] Starting discovery from {len(SEED_LIST)} seed orgs")

    # Build handle → seed lookup
    handle_to_seed = {s["handle"]: s for s in SEED_LIST}
    handles = [s["handle"] for s in SEED_LIST]

    # Scrape all profiles
    print(f"[foundations] Scraping {len(handles)} profiles via Apify...")
    profiles = scrape_profiles(handles)
    print(f"[foundations] Got {len(profiles)} profiles back from Apify")

    # Build lookup by username from Apify results
    profile_by_handle = {}
    for p in profiles:
        uname = (p.get("username") or "").lower().strip()
        if uname:
            profile_by_handle[uname] = p

    # Check which seeds came back
    for seed in SEED_LIST:
        if seed["handle"] not in profile_by_handle:
            print(f"[foundations] WARNING: handle @{seed['handle']} ({seed['org_name']}) not returned by Apify — may be wrong handle")

    # Qualify
    qualified = []
    for seed in SEED_LIST:
        handle = seed["handle"]
        profile = profile_by_handle.get(handle)

        if not profile:
            continue

        result = qualify_org(profile, seed)
        if not result:
            continue

        print(f"[foundations] Qualified: {result['org_name']} (@{result['username']}) | {result['followers']:,} followers | {result['diagnosis']}")
        qualified.append(result)

    # Email enrichment intentionally skipped — foundations are contacted via Instagram DM
    # not email. The partnerships team will reach out directly on IG.

    print(f"\n[foundations] Done. {len(qualified)} orgs ready to write.")
    return qualified[:batch_size]


# ---------------------------------------------------------------------------
# CLI for standalone testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    results = run(batch_size=args.batch_size)

    print(f"\n{'='*60}")
    print(f"Results preview ({len(results)} orgs):")
    print(f"{'='*60}")
    for r in results:
        print(f"\n  {r['org_name']} (@{r['username']})")
        print(f"  Diagnosis: {r['diagnosis']}")
        print(f"  Followers: {r['followers']:,}")
        print(f"  Website:   {r['website']}")
        print(f"  Email:     {r['email'] or 'not found'} ({r['email_source']})")
        if r["exec_contact_name"]:
            print(f"  Contact:   {r['exec_contact_name']} — {r['exec_contact_title']}")
