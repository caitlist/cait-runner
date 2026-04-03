"""
enrich_email.py
---------------
Finds contact email for an Instagram account using free methods:
1. Bio regex scan
2. Link-in-bio → website scrape
3. Website contact/about page scrape
4. Hunter.io (when configured)

Usage:
    from scripts.enrich_email import enrich_email
    result = enrich_email(username="someaccount", bio="Contact me...", website="https://...")
"""

import os
import re
import time

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY")
APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY")

# Regex for email detection (handles standard and some obfuscated formats)
EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+\s*[@＠at]\s*[a-zA-Z0-9.\-]+\s*[.\s]\s*[a-zA-Z]{2,}",
    re.IGNORECASE,
)

EMAIL_STRICT = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

# Pages to check on a website
CONTACT_PATHS = [
    "/contact",
    "/contact-us",
    "/get-in-touch",
    "/work-with-me",
    "/collab",
    "/partnerships",
    "/hire-me",
    "/about",
    "/about-me",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    )
}


def normalize_email(raw: str) -> str | None:
    """Clean up obfuscated email patterns."""
    # Replace [at], (at), " at " with @
    raw = re.sub(r"\s*[\[\(]?\s*at\s*[\]\)]?\s*", "@", raw, flags=re.IGNORECASE)
    # Replace [dot], (dot), " dot " with .
    raw = re.sub(r"\s*[\[\(]?\s*dot\s*[\]\)]?\s*", ".", raw, flags=re.IGNORECASE)
    # Remove spaces around @ and .
    raw = re.sub(r"\s+", "", raw)
    # Validate the result
    if EMAIL_STRICT.match(raw):
        return raw.lower()
    return None


def extract_email_from_text(text: str) -> str | None:
    """Extract first valid email from a block of text."""
    # Try strict regex first
    match = EMAIL_STRICT.search(text)
    if match:
        email = match.group().lower().strip()
        # Filter out fake/placeholder emails
        if any(skip in email for skip in ["example.com", "yourname@", "email@email"]):
            return None
        return email

    # Try fuzzy regex for obfuscated formats
    match = EMAIL_REGEX.search(text)
    if match:
        return normalize_email(match.group())

    return None


def scrape_page_for_email(url: str, timeout: int = 8) -> str | None:
    """Scrape a web page and extract email if found."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code != 200:
            return None

        # Check for mailto links first (most reliable)
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("mailto:"):
                email = href.replace("mailto:", "").split("?")[0].strip().lower()
                if EMAIL_STRICT.match(email):
                    return email

        # Check page text
        text = soup.get_text(separator=" ")
        return extract_email_from_text(text)

    except requests.exceptions.Timeout:
        return None
    except Exception:
        return None


def find_website_base(url: str) -> str:
    """Extract base URL from a link (e.g., https://example.com/page → https://example.com)."""
    match = re.match(r"(https?://[^/]+)", url)
    return match.group(1) if match else url


def enrich_email(
    username: str,
    bio: str = "",
    website: str = "",
    full_name: str = "",
) -> dict:
    """
    Run the full email enrichment pipeline for an Instagram account.

    Returns:
        {email: str, email_source: str}
        email is "" and email_source is "not found" if nothing found.
    """
    # --- Method 1: Bio scan ---
    if bio:
        email = extract_email_from_text(bio)
        if email:
            return {"email": email, "email_source": "bio"}

    # --- Method 2 & 3: Website scrape ---
    if website:
        # Clean up URL
        if not website.startswith("http"):
            website = "https://" + website

        # Try the homepage first
        email = scrape_page_for_email(website)
        if email:
            return {"email": email, "email_source": "website"}

        # Try common contact pages
        base = find_website_base(website)
        for path in CONTACT_PATHS:
            url = base + path
            email = scrape_page_for_email(url)
            if email:
                return {"email": email, "email_source": "website"}
            time.sleep(0.5)

    # --- Method 4: Hunter.io (if configured) ---
    if HUNTER_API_KEY and website:
        email = hunter_lookup(website)
        if email:
            return {"email": email, "email_source": "hunter"}

    # --- Method 5: Facebook page About scrape ---
    email = scrape_facebook_for_email(website, username)
    if email:
        return {"email": email, "email_source": "facebook"}

    # --- Method 6: YouTube channel About scrape ---
    email = scrape_youtube_for_email(website, username)
    if email:
        return {"email": email, "email_source": "youtube"}

    # --- Method 8: Apollo via LinkedIn — name search ---
    if APOLLO_API_KEY and full_name:
        linkedin_url = find_linkedin_by_name(full_name)
        if linkedin_url:
            print(f"[enrich] Found LinkedIn via name search: {linkedin_url}")
            email = apollo_linkedin_lookup(linkedin_url)
            if email:
                return {"email": email, "email_source": "apollo/linkedin-name"}

    # --- Method 9: Apollo via LinkedIn — website scrape ---
    if APOLLO_API_KEY and website:
        linkedin_url = find_linkedin_from_website(website)
        if linkedin_url:
            print(f"[enrich] Found LinkedIn via website: {linkedin_url}")
            email = apollo_linkedin_lookup(linkedin_url)
            if email:
                return {"email": email, "email_source": "apollo/linkedin-site"}

    # --- Method 10: Apollo.io domain search (fallback) ---
    if APOLLO_API_KEY and website:
        email = apollo_lookup(website, username)
        if email:
            return {"email": email, "email_source": "apollo/domain"}

    return {"email": "", "email_source": "not found"}


SKIP_DOMAINS = [
    "linktr.ee", "linktree.com", "stan.store", "beacons.ai",
    "bio.link", "allmylinks.com", "taplink.cc", "campsite.bio",
    "later.com", "koji.to", "bit.ly", "instagram.com",
    "tap.bio", "lnk.bio", "portaly.cc", "flodesk.com",
    "myflodesk.com", "spoti.fi", "komi.io",
]


def hunter_lookup(website: str) -> str | None:
    """
    Look up email via Hunter.io domain search.
    Only runs if HUNTER_API_KEY is configured.
    """
    if not HUNTER_API_KEY:
        return None

    try:
        domain = re.sub(r"https?://", "", website).split("/")[0]

        # Skip link aggregators — they return garbage emails
        if any(skip in domain for skip in SKIP_DOMAINS):
            return None
        resp = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={"domain": domain, "api_key": HUNTER_API_KEY, "limit": 1},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            emails = data.get("data", {}).get("emails", [])
            if emails:
                # Take the highest-confidence result
                emails.sort(key=lambda x: x.get("confidence", 0), reverse=True)
                best = emails[0]
                if best.get("confidence", 0) >= 70:
                    return best.get("value", "").lower()
    except Exception:
        pass

    return None


def scrape_facebook_for_email(website: str, username: str = "") -> str | None:
    """
    Try to find a contact email from a Facebook page's About section.
    Checks facebook.com/[username]/about — works on many public pages.
    Also looks for Facebook links on the creator's website.
    """
    facebook_urls = []

    # First: look for Facebook links on their website
    if website:
        if not website.startswith("http"):
            website = "https://" + website
        try:
            resp = requests.get(website, headers=HEADERS, timeout=8, allow_redirects=True)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "facebook.com/" in href and "/sharer" not in href and "/share" not in href:
                        match = re.search(r"(https?://(?:www\.)?facebook\.com/[^/?#\s\"]+)", href)
                        if match:
                            fb_url = match.group(1)
                            if fb_url not in facebook_urls:
                                facebook_urls.append(fb_url)
        except Exception:
            pass

    # Second: try guessing the Facebook page from the username
    if username:
        facebook_urls.append(f"https://www.facebook.com/{username}")

    for fb_url in facebook_urls[:3]:
        # Try the /about page
        about_url = fb_url.rstrip("/") + "/about"
        try:
            resp = requests.get(about_url, headers=HEADERS, timeout=8, allow_redirects=True)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # Check mailto links
                for a in soup.find_all("a", href=True):
                    if a["href"].startswith("mailto:"):
                        email = a["href"].replace("mailto:", "").split("?")[0].strip().lower()
                        if EMAIL_STRICT.match(email):
                            return email
                # Check page text
                email = extract_email_from_text(soup.get_text(separator=" "))
                if email:
                    return email
        except Exception:
            continue

    return None


def scrape_youtube_for_email(website: str, username: str = "") -> str | None:
    """
    Try to find a contact email from a YouTube channel's About page.
    Looks for YouTube links on the creator's website first, then tries by username.
    Note: YouTube About pages are JS-rendered; only works if email is in static HTML.
    """
    youtube_handles = []

    if website:
        if not website.startswith("http"):
            website = "https://" + website
        try:
            resp = requests.get(website, headers=HEADERS, timeout=8, allow_redirects=True)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "youtube.com/" in href and ("/@" in href or "/channel/" in href or "/c/" in href):
                        match = re.search(r"(https?://(?:www\.)?youtube\.com/(?:@|c/|channel/)[^/?#\s\"]+)", href)
                        if match:
                            youtube_handles.append(match.group(1))
        except Exception:
            pass

    if username:
        youtube_handles.append(f"https://www.youtube.com/@{username}")

    for yt_url in youtube_handles[:2]:
        about_url = yt_url.rstrip("/") + "/about"
        try:
            resp = requests.get(about_url, headers=HEADERS, timeout=8, allow_redirects=True)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    if a["href"].startswith("mailto:"):
                        email = a["href"].replace("mailto:", "").split("?")[0].strip().lower()
                        if EMAIL_STRICT.match(email):
                            return email
                email = extract_email_from_text(soup.get_text(separator=" "))
                if email:
                    return email
        except Exception:
            continue

    return None


def find_linkedin_by_name(full_name: str) -> str | None:
    """
    Search DuckDuckGo for '[Full Name] site:linkedin.com/in' and return
    the first matching LinkedIn profile URL.
    Requires: pip install duckduckgo_search
    """
    if not full_name or len(full_name.strip()) < 3:
        return None

    try:
        from duckduckgo_search import DDGS
        query = f'"{full_name.strip()}" site:linkedin.com/in'
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        for r in results:
            url = r.get("href", "") or r.get("url", "")
            match = re.search(r"(https?://(?:www\.)?linkedin\.com/in/[^/?#\s\"]+)", url)
            if match:
                return match.group(1)
    except Exception:
        pass

    return None


def find_linkedin_from_website(website: str) -> str | None:
    """
    Scrape a website to find the owner's LinkedIn profile URL.
    Checks homepage and common contact/about pages.
    """
    if not website:
        return None

    if not website.startswith("http"):
        website = "https://" + website

    base = find_website_base(website)
    pages_to_check = [website] + [base + path for path in CONTACT_PATHS[:4]]

    for url in pages_to_check:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "linkedin.com/in/" in href:
                    match = re.search(r"(https?://(?:www\.)?linkedin\.com/in/[^/?#\s\"]+)", href)
                    if match:
                        return match.group(1)
            time.sleep(0.3)
        except Exception:
            continue

    return None


def apollo_linkedin_lookup(linkedin_url: str) -> str | None:
    """
    Look up email via Apollo.io using a LinkedIn profile URL.
    Calls /people/match with linkedin_url — most reliable Apollo method
    for solo creators and practitioners.
    """
    if not APOLLO_API_KEY or not linkedin_url:
        return None

    try:
        resp = requests.post(
            "https://api.apollo.io/v1/people/match",
            json={
                "api_key": APOLLO_API_KEY,
                "linkedin_url": linkedin_url,
                "reveal_personal_emails": True,
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return None

        person = resp.json().get("person", {})
        if not person:
            return None

        email = person.get("email", "")
        if email and "***" not in email and EMAIL_STRICT.match(email):
            return email.lower()

    except Exception:
        pass

    return None


def apollo_lookup(website: str, username: str = "") -> str | None:
    """
    Look up email via Apollo.io people search by domain.
    Works best for solo practitioners and creators with their own website.
    Only runs if APOLLO_API_KEY is configured.

    Strategy: search Apollo for people associated with the domain.
    For solo creators this almost always returns just them.
    Skips link aggregators (linktr.ee etc.) same as Hunter.
    """
    if not APOLLO_API_KEY:
        return None

    try:
        domain = re.sub(r"https?://", "", website).split("/")[0]

        # Skip link aggregators
        if any(skip in domain for skip in SKIP_DOMAINS):
            return None

        resp = requests.post(
            "https://api.apollo.io/v1/mixed_people/search",
            json={
                "api_key": APOLLO_API_KEY,
                "q_organization_domains": domain,
                "page": 1,
                "per_page": 5,
            },
            timeout=10,
        )

        if resp.status_code != 200:
            return None

        data = resp.json()
        people = data.get("people", [])
        if not people:
            return None

        # Prefer people whose name/title suggests they're the account owner
        # (not a generic org employee) — scored by email reveal status
        for person in people:
            email = person.get("email", "")
            # Apollo returns sanitized emails like f***@domain.com if not revealed
            if email and "@" in email and "***" not in email:
                if EMAIL_STRICT.match(email):
                    return email.lower()

        # If no revealed email, try the reveal endpoint for the top result
        person_id = people[0].get("id", "")
        if person_id:
            reveal_resp = requests.post(
                "https://api.apollo.io/v1/people/match",
                json={
                    "api_key": APOLLO_API_KEY,
                    "id": person_id,
                    "reveal_personal_emails": True,
                },
                timeout=10,
            )
            if reveal_resp.status_code == 200:
                revealed = reveal_resp.json().get("person", {})
                email = revealed.get("email", "")
                if email and "***" not in email and EMAIL_STRICT.match(email):
                    return email.lower()

    except Exception:
        pass

    return None


def enrich_batch(accounts: list[dict]) -> list[dict]:
    """
    Run enrichment on a list of account dicts.
    Each dict should have: username, _bio (optional), website (optional).
    Adds email and email_source fields in place.
    """
    for account in accounts:
        username = account.get("username", "")
        bio = account.pop("_bio", "") or account.get("bio", "") or ""
        website = account.get("website", "") or ""

        print(f"[enrich] Enriching @{username}...")
        result = enrich_email(username=username, bio=bio, website=website)
        account["email"] = result["email"]
        account["email_source"] = result["email_source"]

        if result["email"]:
            print(f"[enrich]   Found via {result['email_source']}: {result['email']}")
        else:
            print(f"[enrich]   Not found")

        time.sleep(1)  # Polite delay between website requests

    return accounts


if __name__ == "__main__":
    # Quick test
    test_bio = "BCBA | Helping autism families | courses at mysite.com | reach me: hello@mysite.com"
    result = enrich_email(username="testuser", bio=test_bio)
    print(f"Test result: {result}")
