"""
daily_discovery_feed.py — small daily hashtag pass that finds NEW medical-mom
candidates WITH the qualifying post(s) as evidence.

Unlike the big batch scraper, this mimics Cherwin's feed browsing:
  - rotates through a pool of proven hashtags (8/day, so each repeats every ~4 days)
  - keeps the exact post(s) that surfaced each account (URL + caption + tag)
  - dedupes against EVERYTHING we already know (COMMENTS, Medical Mom DM Outreach,
    master_handles.json, Early Access exclusion set, prior rejects)
  - light org filtering only — the real judgment pass is Claude in-session,
    which reads outputs/daily_discovery_candidates.json, applies the gold-standard
    test, and writes survivors to the COMMENTS tab with the Evidence column filled.

Run:  python scripts/daily_discovery_feed.py
      python scripts/daily_discovery_feed.py --tags-per-day 8 --posts-per-tag 30 --min-followers 500
      python scripts/daily_discovery_feed.py --apify-token <KEY>

Output: outputs/daily_discovery_candidates.json
NEVER pass proxy config to Apify actors (permanent rule).
"""

import os, re, sys, json, time, math, argparse, datetime
import gspread
from google.oauth2.service_account import Credentials
from apify_client import ApifyClient
from dotenv import dotenv_values

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV  = dotenv_values(os.path.join(BASE, ".env"))

SHEET_ID    = ENV.get("GOOGLE_SHEET_ID")
CREDS_PATH  = ENV.get("GOOGLE_CREDS_PATH")
ENGAGE_ID   = "1uZMIrY316Lyf7MWQCJ25AjZdNnr8TohdLLuCnU-ty6Y"   # ENGAGEMENT_LIST sheet
OUT_FILE    = os.path.join(BASE, "outputs", "daily_discovery_candidates.json")
REJECT_FILE = os.path.join(BASE, "outputs", "discovery_rejects.json")
MASTER_FILE = os.path.join(BASE, "outputs", "master_handles.json")
EA_CACHE    = os.path.join(BASE, "outputs", "early_access_handles_cache.json")

# ── Proven hashtag pool (productive tags from B45/B46/B48/B49/B51/B54/B55) ─────
HASHTAG_POOL = [
    "medicalmom", "medicalmomlife", "medicalmama", "medicallycomplex",
    "medicalkid", "medicalkiddo", "complexneeds", "hospitallife",
    "trachmom", "tracheostomy", "gtubemom", "gtubebaby", "feedingtubemom",
    "raredisease", "rareparent", "nicumom", "nicubaby", "preemiemom",
    "heartmom", "heartwarrior", "chdwarrior", "cancermom",
    "childhoodcancermom", "leukemiamom", "epilepsymom", "seizurewarrior",
    "cfmom", "spinabifida", "undiagnosed", "medicalmomcommunity",
    "medicalmomjourney", "specialneedsmom",
]

ORG_HANDLE_HINTS = ["foundation", "org", "charity", "nonprofit", "hospital",
                    "clinic", "center", "official", "association", "society",
                    "alliance", "institute", "network", "support"]
ORG_CAPTION_HINTS = ["register now", "join us", "our program", "our mission",
                     "donate at", "our team", "our services", "we support families",
                     "link in bio to donate", "follow us"]


def is_english(text):
    if not text:
        return True
    ascii_chars = sum(1 for ch in text if ord(ch) < 128)
    return ascii_chars / max(len(text), 1) > 0.7


def looks_org(handle, caption):
    h = handle.lower()
    if any(k in h for k in ORG_HANDLE_HINTS) and not any(
            p in h for p in ["mom", "mama", "mum", "dad", "parent"]):
        return True
    c = (caption or "").lower()
    return sum(1 for k in ORG_CAPTION_HINTS if k in c) >= 2


def todays_tags(n):
    """Rotate the pool by day-of-year so each tag repeats every ~pool/n days."""
    doy = datetime.date.today().timetuple().tm_yday
    start = (doy * n) % len(HASHTAG_POOL)
    tags = [HASHTAG_POOL[(start + i) % len(HASHTAG_POOL)] for i in range(n)]
    return tags


def clean_handle(h):
    return (h or "").strip().lstrip("@").rstrip("/").split("?")[0].lower()


def load_known_handles(gc):
    """Every handle we already know — candidate must be new everywhere."""
    known = set()

    # 1. master_handles.json
    if os.path.exists(MASTER_FILE):
        with open(MASTER_FILE, encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else data.get("handles", data)
        if isinstance(items, dict):
            known.update(clean_handle(k) for k in items.keys())
        else:
            for it in items:
                known.add(clean_handle(it if isinstance(it, str) else it.get("handle", "")))
        print(f"  master_handles.json: {len(known)}")

    # 2. prior rejects
    if os.path.exists(REJECT_FILE):
        with open(REJECT_FILE, encoding="utf-8") as f:
            rejects = json.load(f)
        known.update(clean_handle(h) for h in rejects.keys())
        print(f"  + rejects: {len(rejects)}")

    # 3. live COMMENTS + Medical Mom DM Outreach
    ss = gc.open_by_key(SHEET_ID)
    for tab in ["COMMENTS", "Medical Mom DM Outreach"]:
        try:
            vals = ss.worksheet(tab).get_all_values()
            cnt = 0
            for row in vals[1:]:
                if row and row[0].strip():
                    known.add(clean_handle(row[0]))
                    cnt += 1
            print(f"  + {tab}: {cnt}")
        except Exception as ex:
            print(f"  WARN could not read {tab}: {ex}")

    # 4. Early Access (US) exclusion set — cached, refresh if cache > 3 days old
    ea = set()
    fresh = (os.path.exists(EA_CACHE) and
             time.time() - os.path.getmtime(EA_CACHE) < 3 * 86400)
    if fresh:
        with open(EA_CACHE, encoding="utf-8") as f:
            ea = set(json.load(f))
    else:
        try:
            ws = gc.open_by_key(ENGAGE_ID).worksheet("Early Access (US)")
            for row in ws.get_all_values()[1:]:
                for cell in row[:3]:
                    cell = cell.strip()
                    m = re.search(r'instagram\.com/([A-Za-z0-9._]+)', cell)
                    if m:
                        ea.add(clean_handle(m.group(1)))
                    elif cell and " " not in cell and "/" not in cell.rstrip("/"):
                        ea.add(clean_handle(cell))
            with open(EA_CACHE, "w", encoding="utf-8") as f:
                json.dump(sorted(ea), f)
        except Exception as ex:
            print(f"  WARN Early Access read failed: {ex}")
            if os.path.exists(EA_CACHE):
                with open(EA_CACHE, encoding="utf-8") as f:
                    ea = set(json.load(f))
    known.update(ea)
    print(f"  + Early Access: {len(ea)}")
    print(f"  TOTAL known handles: {len(known)}")
    return known


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags-per-day", type=int, default=8)
    ap.add_argument("--posts-per-tag", type=int, default=30)
    ap.add_argument("--min-followers", type=int, default=500)
    ap.add_argument("--apify-token", help="override .env token")
    ap.add_argument("--tags", nargs="+", help="explicit tags instead of rotation")
    args = ap.parse_args()

    token = args.apify_token or ENV.get("APIFY_TOKEN")
    client = ApifyClient(token)

    creds = Credentials.from_service_account_file(
        CREDS_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    gc = gspread.authorize(creds)

    print("[1] Loading known handles (dedup set)...")
    known = load_known_handles(gc)

    tags = args.tags or todays_tags(args.tags_per_day)
    print(f"\n[2] Today's tags ({len(tags)}): {', '.join('#' + t for t in tags)}")

    # candidates: handle -> {evidence: [...], ...}
    candidates = {}
    for tag in tags:
        print(f"  #{tag}...", end=" ", flush=True)
        try:
            run = client.actor("apify/instagram-hashtag-scraper").call(run_input={
                "hashtags":     [tag],
                "resultsLimit": args.posts_per_tag,
            })
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            new_here = 0
            for item in items:
                owner = clean_handle(item.get("ownerUsername") or
                                     (item.get("owner") or {}).get("username") or "")
                if not owner or owner in known:
                    continue
                caption = item.get("caption") or ""
                if not is_english(caption):
                    continue
                url = item.get("url") or ""
                ev = {
                    "post_url": url,
                    "caption":  caption[:400],
                    "tag":      tag,
                    "ts":       item.get("timestamp") or "",
                }
                if owner not in candidates:
                    candidates[owner] = {
                        "handle":   owner,
                        "ig_link":  f"https://www.instagram.com/{owner}/",
                        "evidence": [ev],
                        "org_flag": looks_org(owner, caption),
                    }
                    new_here += 1
                elif len(candidates[owner]["evidence"]) < 3 and url and \
                        url not in [e["post_url"] for e in candidates[owner]["evidence"]]:
                    candidates[owner]["evidence"].append(ev)
            print(f"{new_here} new")
            # checkpoint after every tag
            with open(OUT_FILE, "w", encoding="utf-8") as f:
                json.dump(list(candidates.values()), f, indent=1, ensure_ascii=False)
            time.sleep(2)
        except Exception as ex:
            print(f"ERROR: {ex}")

    cands = list(candidates.values())
    print(f"\n  Raw candidates: {len(cands)}")
    if not cands:
        print("Nothing new today.")
        return

    # ── Profile scrape (bio + followers) ────────────────────────────────────────
    print(f"\n[3] Profile-scraping {len(cands)} candidates...")
    BATCH = 50
    profiles = {}
    for i in range(0, len(cands), BATCH):
        batch = cands[i:i + BATCH]
        urls = [c["ig_link"] for c in batch]
        print(f"  batch {i // BATCH + 1}/{math.ceil(len(cands) / BATCH)} "
              f"({len(batch)})...", end=" ", flush=True)
        try:
            run = client.actor("apify/instagram-scraper").call(run_input={
                "directUrls":   urls,
                "resultsType":  "details",
                "resultsLimit": len(batch),
            })
            got = 0
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                h = clean_handle(item.get("username") or "")
                if h:
                    profiles[h] = item
                    got += 1
            print(f"{got} back")
            time.sleep(2)
        except Exception as ex:
            print(f"ERROR: {ex}")

    # ── Attach profile data + light filter ──────────────────────────────────────
    final = []
    for c in cands:
        p = profiles.get(c["handle"])
        if not p:
            continue
        followers = p.get("followersCount") or 0
        if followers < args.min_followers:
            continue
        if p.get("private"):
            continue
        bio = p.get("biography") or ""
        if not is_english(bio):
            continue
        c.update({
            "full_name":   p.get("fullName") or "",
            "bio":         bio,
            "followers":   followers,
            "is_business": bool(p.get("isBusinessAccount")),
            "posts_count": p.get("postsCount") or 0,
            "scraped":     datetime.date.today().isoformat(),
        })
        final.append(c)

    final.sort(key=lambda x: (x["org_flag"], -len(x["evidence"]), -x["followers"]))
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=1, ensure_ascii=False)

    orgs = sum(1 for c in final if c["org_flag"])
    print(f"\n[4] DONE — {len(final)} candidates saved to {OUT_FILE}")
    print(f"    ({orgs} flagged as possible orgs, sorted to bottom)")
    print("\nNext: Claude reads the JSON in-session, applies the gold-standard")
    print("judgment pass, and writes survivors to COMMENTS with Evidence filled.")


if __name__ == "__main__":
    main()
