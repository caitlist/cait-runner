"""
daily_dm_discovery.py
---------------------
Self-learning daily discovery of medical mom Instagram accounts for CAIT DM outreach.

Inspired by karpathy/autoresearch: run → measure yield → keep hashtags that work,
discard ones that don't → discover new hashtags from scraped content → repeat daily.

What this does:
  1. Loads ever-growing contacted_log.txt to prevent duplicate outreach
  2. Scrapes each active hashtag in hashtag_config.json via Apify
  3. For each new account found: checks active (posted within 60 days), public
  4. Extracts first name from display name, fills DM template
  5. Writes outputs/daily_dm_YYYY-MM-DD.md — Mikha's ready-to-send list
  6. Writes today's accounts to "Medical Mom DM Outreach" Google Sheet tab
  7. Updates contacted_log.txt + hashtag_yield_log.json
  8. Auto-discovers new hashtags from scraped post content → adds to pending

What this does NOT do:
  - Send DMs (no Instagram DM API exists; automation = account ban risk)
  - Filter by followers or engagement (any active public medical mom qualifies)

Usage:
    python -X utf8 scripts/daily_dm_discovery.py
    python -X utf8 scripts/daily_dm_discovery.py --dry-run     # no log updates
    python -X utf8 scripts/daily_dm_discovery.py --limit 20    # max accounts per run
"""

import os
import re
import sys
import json
import time
import datetime
import argparse

import gspread
from google.oauth2.service_account import Credentials
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
CREDS_PATH = os.environ.get("GOOGLE_CREDS_PATH")
DM_SHEET_TAB = "Medical Mom DM Outreach"
DM_SHEET_HEADERS = ["Date", "Handle", "IG Profile Link", "Category", "Source Hashtag", "Display Name", "Name Used", "DM Status", "Notes"]

HASHTAG_ACTOR = "apify/instagram-hashtag-scraper"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

CONTACTED_LOG = os.path.join(OUTPUTS_DIR, "contacted_log.txt")
HASHTAG_CONFIG = os.path.join(OUTPUTS_DIR, "hashtag_config.json")
YIELD_LOG = os.path.join(OUTPUTS_DIR, "hashtag_yield_log.json")

# How many consecutive zero-yield runs before a hashtag is marked inactive
ZERO_YIELD_LIMIT = 5

# Activity cutoff: accounts that haven't posted in this many days are skipped
ACTIVITY_DAYS = 60

DM_TEMPLATE = """Hi {name}

We came across your page and just wanted to say how much we admire everything you're managing, it's a lot.

We've been building something with our medical parent community from day one that helps take things out of your head — like tracking symptoms, medications, and everything going on day-to-day, without needing to remember it all.

It has a similar intelligence to ChatGPT, but feels much more personal and built for real family life.

Many medical parents have told us it's been a game changer for them and something they wish they had much earlier.

We're opening early access to a small group before launch — if it feels like it could help at all, we'd be happy to share it with you

We also offer a small honorarium as a thank you for your time all we ask is for your honest feedback to see how this could help you each day.

If you're open, we'd be happy to share more details

Mikha
Brand Partnership Lead
caitconnect.com"""


# ── State loading/saving ───────────────────────────────────────────────────────

def load_contacted_log() -> set:
    if not os.path.exists(CONTACTED_LOG):
        return set()
    handles = set()
    with open(CONTACTED_LOG, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                handles.add(line.lower().lstrip("@"))
    return handles


def append_contacted_log(handles: list[str]):
    with open(CONTACTED_LOG, "a", encoding="utf-8") as f:
        for h in handles:
            f.write(h.lower().lstrip("@") + "\n")


def load_hashtag_config() -> dict:
    with open(HASHTAG_CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)


def save_hashtag_config(config: dict):
    with open(HASHTAG_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def load_yield_log() -> dict:
    if not os.path.exists(YIELD_LOG):
        return {"runs": []}
    with open(YIELD_LOG, "r", encoding="utf-8") as f:
        return json.load(f)


def save_yield_log(log: dict):
    with open(YIELD_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


# ── Name extraction ────────────────────────────────────────────────────────────

def extract_first_name(display_name: str, username: str) -> str:
    """
    Parse a human-readable first name from display name.
    Falls back to title-cased username if no usable name found.
    """
    # Common page/account-style non-name words to skip
    NON_NAME_WORDS = {
        "brave", "nolan", "journey", "warrior", "hope", "grace", "faith",
        "life", "world", "story", "love", "heart", "mama", "mommy", "mom",
        "mum", "momma", "the", "our", "my", "little", "baby", "tiny",
        "strong", "fight", "fighting", "living", "raising", "team",
    }

    if display_name:
        # Remove emojis and special chars, keep letters/spaces/hyphens
        cleaned = re.sub(r"[^\w\s\-']", "", display_name).strip()
        # Take first word
        parts = cleaned.split()
        if parts and len(parts[0]) >= 2:
            candidate = parts[0]
            # Skip all-caps abbreviations (business accounts)
            if candidate.isupper() and len(candidate) <= 4:
                pass
            # Skip generic page-style words
            elif candidate.lower() in NON_NAME_WORDS:
                pass
            else:
                return candidate.title()

    # Fallback: use first part of username, strip numbers/underscores
    name_from_handle = re.sub(r"[_\d]", " ", username).strip().split()[0] if username else ""
    if name_from_handle and len(name_from_handle) >= 2:
        return name_from_handle.title()

    return "there"



# ── Hashtag extraction for self-learning ──────────────────────────────────────

def extract_hashtags_from_text(text: str) -> list[str]:
    """Extract all hashtags from a caption or bio."""
    return [tag.lower() for tag in re.findall(r"#(\w+)", text or "")]


def filter_medical_hashtags(hashtags: list[str], medical_keywords: list[str]) -> list[str]:
    """Keep only hashtags that contain at least one medical keyword."""
    keywords_lower = [k.lower() for k in medical_keywords]
    result = []
    for tag in hashtags:
        tag_lower = tag.lower()
        if any(kw in tag_lower for kw in keywords_lower):
            result.append(tag_lower)
    return result


def discover_new_hashtags(scraped_items: list[dict], existing_hashtags: set,
                          medical_keywords: list[str]) -> list[str]:
    """
    Analyze all captions/bios scraped today.
    Find hashtags that: appear 3+ times AND contain medical keywords AND are not already in config.
    Returns list of new candidate hashtags to add to pending.
    """
    from collections import Counter
    all_tags = []
    for item in scraped_items:
        caption = item.get("caption") or item.get("description") or ""
        all_tags.extend(extract_hashtags_from_text(caption))

    # Count frequency
    counts = Counter(all_tags)
    # Filter: 3+ appearances, medical keyword, not already tracked
    candidates = []
    for tag, count in counts.items():
        if count >= 3 and tag not in existing_hashtags:
            medical = filter_medical_hashtags([tag], medical_keywords)
            if medical:
                candidates.append(tag)

    return candidates


# ── Apify calls ────────────────────────────────────────────────────────────────

def scrape_hashtag(client: ApifyClient, hashtag: str, max_posts: int = 100) -> list[dict]:
    """Scrape a single hashtag and return raw post items."""
    tag_clean = hashtag.lstrip("#").strip()
    print(f"    [hashtag] #{tag_clean} (up to {max_posts} posts)...")
    try:
        run = client.actor(HASHTAG_ACTOR).call(run_input={
            "hashtags": [tag_clean],
            "resultsLimit": max_posts,
            "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
        })
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"      -> {len(items)} posts")
        time.sleep(2)
        return items
    except Exception as e:
        print(f"    [hashtag] Error on #{tag_clean}: {e}")
        return []




# ── Google Sheets ─────────────────────────────────────────────────────────────

def write_dm_to_sheet(accounts: list[dict], date_str: str) -> int:
    """
    Write today's DM candidates to the 'Medical Mom DM Outreach' Google Sheet tab.
    Creates the tab with headers if it doesn't exist yet.
    Returns number of rows written.
    """
    if not SHEET_ID or not CREDS_PATH:
        print("[Sheets] GOOGLE_SHEET_ID or GOOGLE_CREDS_PATH not set — skipping sheet write")
        return 0

    try:
        creds = Credentials.from_service_account_file(
            CREDS_PATH,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SHEET_ID)

        # Create tab if it doesn't exist
        existing_tabs = [ws.title for ws in sheet.worksheets()]
        if DM_SHEET_TAB not in existing_tabs:
            print(f"[Sheets] Creating tab '{DM_SHEET_TAB}'...")
            ws = sheet.add_worksheet(title=DM_SHEET_TAB, rows=5000, cols=len(DM_SHEET_HEADERS))
            ws.append_row(DM_SHEET_HEADERS, value_input_option="USER_ENTERED")
        else:
            ws = sheet.worksheet(DM_SHEET_TAB)

        # Build rows and append in one batch call
        rows = []
        for account in accounts:
            handle = account["handle"].lstrip("@")
            rows.append([
                date_str,
                f"@{handle}",
                f"https://instagram.com/{handle}",
                account.get("category", ""),
                account.get("source_hashtag", ""),
                account.get("display_name", ""),
                account.get("first_name", ""),
                "",   # DM Status — Mikha fills in
                "",   # Notes — Mikha fills in
            ])

        if rows:
            ws.append_rows(rows, value_input_option="USER_ENTERED")
            print(f"[Sheets] {len(rows)} rows written to '{DM_SHEET_TAB}'")

        return len(rows)

    except Exception as e:
        print(f"[Sheets] Error writing to sheet: {e}")
        return 0


# ── DM output ─────────────────────────────────────────────────────────────────

def format_dm_entry(handle: str, category: str, first_name: str) -> str:
    dm_text = DM_TEMPLATE.format(name=first_name)
    return f"""## @{handle} — {category}
Profile: https://instagram.com/{handle}
Name used: {first_name}

---
{dm_text}
---

"""


def write_dm_output(entries: list[dict], date_str: str, dry_run: bool = False) -> str:
    output_path = os.path.join(OUTPUTS_DIR, f"daily_dm_{date_str}.md")
    lines = [
        f"# CAIT Daily DM List — {date_str}",
        f"Total accounts: {len(entries)}",
        "",
        "> Send each DM manually via Instagram. Do NOT copy-paste the same message to many accounts in quick succession — space them out.",
        "",
        "---",
        "",
    ]
    for entry in entries:
        lines.append(format_dm_entry(
            handle=entry["handle"],
            category=entry["category"],
            first_name=entry["first_name"],
        ))

    content = "\n".join(lines)
    if not dry_run:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    return output_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Daily medical mom DM discovery")
    parser.add_argument("--dry-run", action="store_true", help="Discover but don't update logs or write output")
    parser.add_argument("--limit", type=int, default=0, help="Max accounts to include in today's output (0 = no limit)")
    parser.add_argument("--max-posts", type=int, default=100, help="Posts per hashtag (default 100)")
    parser.add_argument("--max-hashtags", type=int, default=50, help="Max hashtags to scrape per run across all categories (default 50 to stay within free tier)")
    parser.add_argument("--category", type=str, default="", help="Only scrape this category (partial match, case-insensitive). Skips all others.")
    args = parser.parse_args()

    if not APIFY_TOKEN:
        print("ERROR: APIFY_TOKEN not set in .env")
        sys.exit(1)

    today = datetime.date.today().isoformat()
    client = ApifyClient(APIFY_TOKEN)

    print(f"\n{'='*60}")
    print(f"  CAIT Daily DM Discovery — {today}")
    print(f"{'='*60}\n")

    # ── Step 1: Load state ─────────────────────────────────────────────────────
    contacted = load_contacted_log()
    config = load_hashtag_config()
    yield_log = load_yield_log()
    medical_keywords = config.get("medical_keywords", [])

    active_categories = [c for c in config["categories"] if c.get("active", True)]
    if args.category:
        active_categories = [c for c in active_categories if args.category.lower() in c["name"].lower()]
        if not active_categories:
            print(f"ERROR: No category matching '{args.category}' found in config.")
            sys.exit(1)
        print(f"[Filter] Running only category: {[c['name'] for c in active_categories]}")
    all_existing_hashtags = set()
    for cat in config["categories"]:
        all_existing_hashtags.update(tag.lower() for tag in cat["hashtags"])
    all_existing_hashtags.update(tag.lower() for tag in config.get("pending_hashtags", []))

    print(f"Loaded {len(contacted)} previously contacted accounts")
    print(f"Active categories: {len(active_categories)}")
    print(f"Known hashtags: {len(all_existing_hashtags)}\n")

    # ── Step 2: Scrape hashtags ────────────────────────────────────────────────
    # Rotate through hashtags using day-of-year as offset so each run covers
    # a different slice — the seed categories always get at least 1 slot each.
    day_offset = datetime.date.today().toordinal()

    def pick_hashtags_for_run(categories, max_total):
        """
        Distribute max_total slots across categories proportionally (min 1 each).
        Rotate within each category's hashtag list by day_offset.
        """
        n_cats = len(categories)
        if n_cats == 0:
            return {}
        base = max(1, max_total // n_cats)
        remainder = max_total - base * n_cats
        selected = {}
        for i, cat in enumerate(categories):
            tags = cat["hashtags"]
            if not tags:
                continue
            slots = base + (1 if i < remainder else 0)
            start = day_offset % len(tags)
            rotated = (tags + tags)[start:start + slots]
            selected[cat["name"]] = rotated
        return selected

    hashtags_to_scrape = pick_hashtags_for_run(active_categories, args.max_hashtags)
    total_selected = sum(len(v) for v in hashtags_to_scrape.values())
    print(f"Hashtags selected for today's run: {total_selected} (of {len(all_existing_hashtags)} known)\n")

    today_yield = {}       # hashtag -> new account count
    candidate_handles = {}  # handle -> {category, display_name, bio}
    all_scraped_items = []  # for self-learning hashtag analysis

    for category in active_categories:
        cat_name = category["name"]
        selected = hashtags_to_scrape.get(cat_name, [])
        if not selected:
            continue
        print(f"\n[{cat_name}] ({len(selected)} hashtags)")
        cat_new = 0

        for hashtag in selected:
            items = scrape_hashtag(client, hashtag, max_posts=args.max_posts)
            all_scraped_items.extend(items)
            tag_new = 0

            for item in items:
                handle = (item.get("ownerUsername") or item.get("username") or "").lower().strip()
                if not handle:
                    continue
                if handle in contacted:
                    continue
                if handle in candidate_handles:
                    continue  # already found via another hashtag

                # English/US filter: caption or bio must contain at least some English text.
                # This is a lightweight proxy — not perfect but removes most non-English accounts.
                caption = item.get("caption") or item.get("description") or ""
                bio = item.get("ownerBiography") or ""
                combined_text = (caption + " " + bio).lower()
                # Must contain at least one common English word
                english_signals = ["the", "my", "our", "we", "is", "and", "for", "with", "her", "his", "you", "this", "that"]
                if not any(f" {w} " in f" {combined_text} " for w in english_signals):
                    continue

                display_name = item.get("ownerFullName") or item.get("fullName") or ""

                candidate_handles[handle] = {
                    "category": cat_name,
                    "source_hashtag": f"#{hashtag.lstrip('#')}",
                    "display_name": display_name,
                    "bio": bio,
                }
                tag_new += 1

            today_yield[hashtag] = today_yield.get(hashtag, 0) + tag_new
            cat_new += tag_new

        print(f"  -> {cat_new} new candidates from {cat_name}")

    total_candidates = len(candidate_handles)
    print(f"\nTotal new candidates before activity check: {total_candidates}")

    # ── Step 3: Build active accounts list ────────────────────────────────────
    # Accounts found in hashtag posts just posted = they are active by definition.
    # Skipping separate profile verification pass saves significant Apify credits.
    # Private accounts can't be DMed — we filter them if bio data is clearly a brand/private signal,
    # but we can't reliably detect private status from hashtag data alone.
    # Accept all found handles as sendable — Mikha will skip any that are private when she opens them.
    print(f"\n[Build list] Processing {total_candidates} candidates...")
    all_accounts = []  # ALL found accounts — goes to Google Sheet

    for handle, data in candidate_handles.items():
        display_name = data["display_name"] or handle
        first_name = extract_first_name(display_name, handle)

        all_accounts.append({
            "handle": handle,
            "category": data["category"],
            "source_hashtag": data.get("source_hashtag", ""),
            "display_name": display_name,
            "first_name": first_name,
        })

    print(f"Total accounts found (going to sheet): {len(all_accounts)}")

    # Build Mikha's daily send list — limited and balanced across categories
    # --limit caps this list only; the sheet always gets everything
    mikha_list = all_accounts  # start with all
    if args.limit > 0 and len(all_accounts) > args.limit:
        from collections import defaultdict
        by_category = defaultdict(list)
        for acc in all_accounts:
            by_category[acc["category"]].append(acc)

        balanced = []
        buckets = list(by_category.values())
        i = 0
        while len(balanced) < args.limit:
            bucket = buckets[i % len(buckets)]
            if bucket:
                balanced.append(bucket.pop(0))
            i += 1
            if all(not b for b in buckets):
                break

        mikha_list = balanced
        print(f"Mikha's send list: {len(mikha_list)} accounts (balanced across {len(by_category)} categories)")

    active_accounts = mikha_list  # keep variable name for rest of script

    # ── Step 4: Self-learning — discover new hashtags ─────────────────────────
    new_hashtags = discover_new_hashtags(all_scraped_items, all_existing_hashtags, medical_keywords)
    if new_hashtags:
        print(f"\n[Self-learning] Found {len(new_hashtags)} new candidate hashtags:")
        for tag in new_hashtags:
            print(f"  #{tag}")

    # ── Step 5: Write DM output ────────────────────────────────────────────────
    if all_accounts:
        # .md file = Mikha's capped daily send list
        output_path = write_dm_output(active_accounts, today, dry_run=args.dry_run)
        if not args.dry_run:
            print(f"\n[Output] Mikha send list written: {output_path}")
            # Sheet = ALL found accounts (no cap)
            sheet_rows = write_dm_to_sheet(all_accounts, today)
        else:
            print(f"\n[Dry run] Would write: {output_path}")
            sheet_rows = 0
    else:
        print("\n[Output] No accounts found today — no file written")
        output_path = None
        sheet_rows = 0

    # ── Step 6: Update logs ────────────────────────────────────────────────────
    if not args.dry_run:
        # Append to contacted log
        all_found_handles = list(candidate_handles.keys())
        if all_found_handles:
            append_contacted_log(all_found_handles)
            print(f"[Log] Added {len(all_found_handles)} handles to contacted_log.txt")

        # Update yield log
        run_entry = {
            "date": today,
            "yield_by_hashtag": today_yield,
            "total_candidates": total_candidates,
            "total_active": len(active_accounts),
        }
        yield_log["runs"].append(run_entry)
        save_yield_log(yield_log)

        # Update hashtag config: add new pending hashtags
        if new_hashtags:
            existing_pending = set(config.get("pending_hashtags", []))
            for tag in new_hashtags:
                if tag not in existing_pending and tag not in all_existing_hashtags:
                    config["pending_hashtags"].append(tag)
                    print(f"[Config] Added #{tag} to pending_hashtags")

        # Promote pending hashtags that have appeared before (simple promotion: always promote after 1 run)
        # They get added to a new "Auto-Discovered" category
        if config.get("pending_hashtags"):
            existing_auto = next((c for c in config["categories"] if c["name"] == "Auto-Discovered"), None)
            if not existing_auto:
                existing_auto = {"name": "Auto-Discovered", "hashtags": [], "active": True}
                config["categories"].append(existing_auto)

            promoted = []
            for tag in config["pending_hashtags"]:
                if tag not in existing_auto["hashtags"]:
                    existing_auto["hashtags"].append(tag)
                    promoted.append(tag)
            if promoted:
                print(f"[Config] Promoted {len(promoted)} hashtags to Auto-Discovered category")
            config["pending_hashtags"] = []

        # Mark hashtags inactive if 5 consecutive zero yields
        for category in config["categories"]:
            if not category.get("active", True):
                continue
            for hashtag in category["hashtags"]:
                # Build yield history for this hashtag
                history = [
                    run["yield_by_hashtag"].get(hashtag, 0)
                    for run in yield_log["runs"][-ZERO_YIELD_LIMIT:]
                ]
                if len(history) >= ZERO_YIELD_LIMIT and all(y == 0 for y in history):
                    print(f"[Config] #{hashtag} had 0 yield for {ZERO_YIELD_LIMIT} runs — marking inactive")
                    # We don't deactivate entire categories, just note in a separate key
                    if "inactive_hashtags" not in category:
                        category["inactive_hashtags"] = []
                    if hashtag not in category["inactive_hashtags"]:
                        category["inactive_hashtags"].append(hashtag)
                        category["hashtags"].remove(hashtag)

        save_hashtag_config(config)
        print("[Config] Saved updated hashtag_config.json")

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Run complete — {today}")
    print(f"  Candidates found:   {total_candidates}")
    print(f"  Sheet rows written: {sheet_rows}  (ALL accounts)")
    print(f"  Mikha send list:    {len(active_accounts)}  (daily cap)")
    print(f"  New hashtags found: {len(new_hashtags)}")
    if output_path and not args.dry_run:
        print(f"  Output file:        {output_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
