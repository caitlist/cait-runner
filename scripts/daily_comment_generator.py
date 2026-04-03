"""
daily_comment_generator.py
---------------------------
Phase 1 of the daily comment workflow.

Reads today's 100 accounts from "Medical Mom DM Outreach" sheet,
scrapes their Instagram profiles via Apify, finds the latest NON-PINNED post
for each account, extracts the caption, and writes it back to the sheet.

Phase 2 (comment generation) is handled by Claude Code in-session:
  Say "run today" and Claude reads the Post Caption column, generates
  personalized comments following the brand voice rules, and writes
  them to the Generated Comment column.

What this script does:
  1. Read today's accounts (DM Status = "To Send - YYYY-MM-DD")
  2. Scrape profiles via Apify (batches of 10, RESIDENTIAL proxies)
  3. For each profile: find latest non-pinned post within 48 hours
  4. Detect SENSITIVE posts (ICU, loss, crisis keywords)
  5. Write Post URL + Post Caption to sheet
  6. Output daily-comments-YYYY-MM-DD.csv (captions only, comments added in Phase 2)
  7. Update scripts/commented-log.csv with post URLs used

Usage:
    python -X utf8 scripts/daily_comment_generator.py
    python -X utf8 scripts/daily_comment_generator.py --dry-run
    python -X utf8 scripts/daily_comment_generator.py --date 2026-03-25
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
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
CREDS_PATH = os.environ.get("GOOGLE_CREDS_PATH")

DM_SHEET_TAB = "Medical Mom DM Outreach"
PROFILE_ACTOR = "apify/instagram-scraper"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
COMMENTED_LOG = os.path.join(SCRIPTS_DIR, "commented-log.csv")

# No age limit — always get the latest post regardless of when it was posted
POST_MAX_AGE_HOURS = None  # disabled

# Keywords that trigger SENSITIVE flag — human must review before pasting
SENSITIVE_KEYWORDS = [
    "icu", "picu", "nicu",
    "passed away", "gone too soon", "in memory of", "in loving memory",
    "heaven", "angel now", "our angel",
    "funeral", "died", "death", "passing",
    "terminal", "end of life", "hospice",
    "last days", "final days", "final hours",
    "emergency surgery", "code blue", "life support",
    "losing him", "losing her", "losing my",
    "lost my son", "lost my daughter", "lost my baby", "lost my child",
    "she is gone", "he is gone",
    "grief", "grieving",
    "collapsed", "unresponsive",
]


# ── Sheets ────────────────────────────────────────────────────────────────────

def open_sheet():
    creds = Credentials.from_service_account_file(
        CREDS_PATH,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID).worksheet(DM_SHEET_TAB)


def ensure_comment_columns(ws) -> dict:
    """
    Ensure Post URL, Post Caption, and Generated Comment columns exist.
    Returns dict of all header -> col_index (1-based).
    """
    headers = ws.row_values(1)
    headers_stripped = [h.strip() for h in headers]

    needed = ["Post URL", "Post Caption", "Generated Comment", "Notes"]
    cols_to_add = [c for c in needed if c not in headers_stripped]
    if cols_to_add:
        new_col_count = len(headers_stripped) + len(cols_to_add)
        if ws.col_count < new_col_count:
            ws.resize(cols=new_col_count)
            print(f"[Sheets] Expanded grid to {new_col_count} columns")
    for col_name in needed:
        if col_name not in headers_stripped:
            col_pos = len(headers_stripped) + 1
            ws.update_cell(1, col_pos, col_name)
            headers_stripped.append(col_name)
            print(f"[Sheets] Added column '{col_name}' at position {col_pos}")

    return {h: i + 1 for i, h in enumerate(headers_stripped)}  # 1-based


def get_todays_accounts(ws, col: dict, date_str: str) -> list[dict]:
    """
    Return accounts where DM Status = 'To Send - {date_str}'.
    Each dict includes: row_num, handle, display_name, category.
    """
    all_values = ws.get_all_values()
    handle_idx = col["Handle"] - 1
    dm_status_idx = col["DM Status"] - 1
    display_name_idx = col.get("Display Name", 0) - 1
    category_idx = col.get("Category", 0) - 1
    post_caption_idx = col.get("Post Caption", 0) - 1
    post_url_idx = col.get("Post URL", 0) - 1

    target_status = f"To Send - {date_str}"
    results = []

    for row_num, row in enumerate(all_values[1:], start=2):
        while len(row) < max(handle_idx, dm_status_idx, post_caption_idx) + 1:
            row.append("")

        dm_val = row[dm_status_idx].strip() if dm_status_idx < len(row) else ""
        if dm_val != target_status:
            continue

        handle = row[handle_idx].strip().lstrip("@") if handle_idx < len(row) else ""
        if not handle:
            continue

        # Don't skip — always rescrape to catch newer posts

        existing_url = row[post_url_idx].strip() if post_url_idx >= 0 and post_url_idx < len(row) else ""
        results.append({
            "row": row_num,
            "handle": handle,
            "display_name": row[display_name_idx].strip() if display_name_idx >= 0 and display_name_idx < len(row) else "",
            "category": row[category_idx].strip() if category_idx >= 0 and category_idx < len(row) else "",
            "existing_url": existing_url,
        })

    return results


# ── Commented log ─────────────────────────────────────────────────────────────

def load_commented_log() -> set:
    """Return set of post URLs already commented on."""
    if not os.path.exists(COMMENTED_LOG):
        return set()
    urls = set()
    with open(COMMENTED_LOG, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("post_url"):
                urls.add(row["post_url"].strip())
    return urls


def append_commented_log(entries: list[dict], dry_run: bool = False):
    """Append {post_url, username, date_commented} rows to commented-log.csv."""
    if dry_run or not entries:
        return
    file_exists = os.path.exists(COMMENTED_LOG)
    with open(COMMENTED_LOG, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["post_url", "username", "date_commented"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(entries)


# ── Post analysis ─────────────────────────────────────────────────────────────

def is_sensitive(caption: str) -> bool:
    """Return True if caption contains any sensitive keywords."""
    text = caption.lower()
    return any(kw in text for kw in SENSITIVE_KEYWORDS)


def parse_timestamp(post: dict) -> datetime.datetime | None:
    """Parse post timestamp into a datetime object."""
    ts = post.get("timestamp") or post.get("takenAtTimestamp") or 0
    try:
        if isinstance(ts, (int, float)) and ts > 1_000_000:
            return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        elif isinstance(ts, str) and ts:
            return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        pass
    return None


def find_latest_post(profile: dict) -> dict | None:
    """
    Find the most recent non-pinned post from a scraped profile.
    Returns the post dict or None if no qualifying post found.
    """
    posts = profile.get("latestPosts") or profile.get("posts") or []

    # Filter out pinned posts
    non_pinned = [
        p for p in posts
        if isinstance(p, dict) and not p.get("isPinned") and not p.get("pinned")
    ]

    if not non_pinned:
        return None

    # Sort by timestamp descending (newest first)
    def sort_key(p):
        dt = parse_timestamp(p)
        return dt if dt else datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)

    non_pinned.sort(key=sort_key, reverse=True)
    return non_pinned[0]


def is_within_hours(post: dict, max_hours: int) -> bool:
    """Return True if post was made within max_hours ago."""
    dt = parse_timestamp(post)
    if not dt:
        return False
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    age = now - dt
    return age.total_seconds() < max_hours * 3600


def get_post_url(post: dict) -> str:
    """Build the Instagram post URL from shortCode or url field."""
    short_code = post.get("shortCode") or post.get("shortcode") or ""
    if short_code:
        return f"https://www.instagram.com/p/{short_code}/"
    url = post.get("url") or post.get("link") or ""
    return url


def get_caption(post: dict) -> str:
    """Extract caption text from post, cleaned up."""
    caption = post.get("caption") or post.get("description") or ""
    # Truncate very long captions for sheet storage
    if len(caption) > 2000:
        caption = caption[:2000] + "... [truncated]"
    return caption.strip()


def summarize_caption(caption: str) -> str:
    """One-line summary of caption for CSV."""
    first_line = caption.split("\n")[0].strip()
    if len(first_line) > 120:
        first_line = first_line[:117] + "..."
    return first_line


# ── Apify scraping ─────────────────────────────────────────────────────────────

def scrape_profiles(handles: list[str]) -> dict[str, dict]:
    """
    Scrape Instagram profiles in batches of 10.
    Returns {handle: profile_dict}.
    """
    client = ApifyClient(APIFY_TOKEN)
    results = {}

    for i in range(0, len(handles), 10):
        batch = handles[i:i + 10]
        clean = [h.lstrip("@").lower().strip() for h in batch]
        print(f"  [Apify] Batch {i // 10 + 1}/{(len(handles) - 1) // 10 + 1}: {clean}")
        try:
            run = client.actor(PROFILE_ACTOR).call(run_input={
                "directUrls": [f"https://www.instagram.com/{u}/" for u in clean],
                "resultsType": "details",
                "resultsLimit": 8,  # enough to find latest non-pinned post
                "proxy": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"],
                },
            })
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            for item in items:
                username = (item.get("username") or "").lower().strip()
                if username:
                    results[username] = item
            print(f"    -> {len(items)} profiles returned")
            time.sleep(3)
        except Exception as e:
            print(f"  [Apify] Error on batch {i // 10 + 1}: {e}")

    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Scrape captions for today's 100 DM accounts")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to sheet or logs")
    parser.add_argument("--date", type=str, default=None, help="Override date (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, default=None, help="Process only first N accounts (for testing)")
    args = parser.parse_args()

    today = args.date or datetime.date.today().isoformat()

    print(f"\n{'='*60}")
    print(f"  CAIT Daily Comment Generator — Phase 1")
    print(f"  Date: {today}")
    print(f"  Finding latest posts + captions for today's 100 accounts")
    print(f"{'='*60}\n")

    if not APIFY_TOKEN:
        print("ERROR: APIFY_TOKEN not set in .env")
        sys.exit(1)

    # Load sheet
    print("Reading sheet...")
    ws = open_sheet()
    col = ensure_comment_columns(ws)

    # Get today's accounts
    accounts = get_todays_accounts(ws, col, today)
    print(f"Found {len(accounts)} accounts for today ({today})")
    if args.limit:
        accounts = accounts[:args.limit]
        print(f"  (Limiting to first {args.limit} for this run)\n")
    else:
        print()

    if not accounts:
        print(f"No accounts with DM Status = 'To Send - {today}'")
        print("Run prep_daily_batch.py first to set up today's batch.")
        return

    # Load already-commented post URLs
    commented_urls = load_commented_log()
    print(f"Loaded {len(commented_urls)} previously commented post URLs\n")

    # Scrape profiles
    handles = [a["handle"] for a in accounts]
    print(f"Scraping {len(handles)} profiles via Apify...")
    profiles = scrape_profiles(handles)
    print(f"\nProfiles returned: {len(profiles)} of {len(handles)}\n")

    # Process each account
    results = []
    no_post_count = 0
    sensitive_count = 0
    already_commented_count = 0
    new_log_entries = []

    post_url_col = col.get("Post URL")
    post_caption_col = col.get("Post Caption")
    notes_col = col.get("Notes")

    sheet_updates = []

    for account in accounts:
        handle = account["handle"]
        profile = profiles.get(handle.lower(), {})

        if not profile:
            print(f"  @{handle:<35} → No profile data returned")
            result = {
                "handle": handle,
                "post_url": "",
                "caption": "No profile data",
                "summary": "No profile data",
                "sensitive": False,
                "status": "No Profile",
                "row": account["row"],
            }
            if post_caption_col:
                sheet_updates.append((account["row"], post_caption_col, "No profile data"))
            results.append(result)
            no_post_count += 1
            continue

        latest_post = find_latest_post(profile)

        if not latest_post:
            all_posts = profile.get("latestPosts") or profile.get("posts") or []
            reason = "Apify restricted profile — no posts returned" if not all_posts else "All posts are pinned"
            print(f"  @{handle:<35} → No posts available ({reason})")
            if post_caption_col:
                sheet_updates.append((account["row"], post_caption_col, f"No post data ({reason})"))
            results.append({
                "handle": handle, "post_url": "", "caption": f"No post data ({reason})",
                "summary": reason, "sensitive": False,
                "status": "No Post", "row": account["row"],
            })
            no_post_count += 1
            continue

        # Age check disabled — always take latest post

        post_url = get_post_url(latest_post)
        caption = get_caption(latest_post)

        if post_url in commented_urls:
            print(f"  @{handle:<35} → Already commented on this post")
            if post_caption_col:
                sheet_updates.append((account["row"], post_caption_col, f"[Already commented] {caption[:200]}"))
            results.append({
                "handle": handle, "post_url": post_url, "caption": caption,
                "summary": "Already commented", "sensitive": False,
                "status": "Already Commented", "row": account["row"],
            })
            already_commented_count += 1
            continue

        sensitive = is_sensitive(caption)
        summary = summarize_caption(caption)

        # Check if post is new vs existing
        existing_url = account.get("existing_url", "")
        is_new_post = post_url != existing_url

        status = "SENSITIVE" if sensitive else "Ready"
        new_tag = " [NEW POST]" if is_new_post and existing_url else ""
        print(f"  @{handle:<35} → {status}{new_tag} | {summary[:55]}")

        if sensitive:
            sensitive_count += 1

        # Update sheet — always update URL and caption (latest post)
        if post_url_col:
            sheet_updates.append((account["row"], post_url_col, post_url))
        if post_caption_col:
            sheet_updates.append((account["row"], post_caption_col, caption))
        if notes_col and sensitive:
            sheet_updates.append((account["row"], notes_col, "SENSITIVE — review before pasting"))
        # If post changed, clear the old generated comment so Phase 2 regenerates it
        if is_new_post and existing_url:
            gen_comment_col_idx = col.get("Generated Comment")
            if gen_comment_col_idx:
                sheet_updates.append((account["row"], gen_comment_col_idx, ""))

        # Log entry (to be written after dry-run check)
        new_log_entries.append({
            "post_url": post_url,
            "username": handle,
            "date_commented": today,
        })

        results.append({
            "handle": handle,
            "post_url": post_url,
            "caption": caption,
            "summary": summary,
            "sensitive": sensitive,
            "status": status,
            "row": account["row"],
            "category": account.get("category", ""),
        })

    # Write sheet updates in one batch
    if sheet_updates and not args.dry_run:
        print(f"\n[Sheets] Writing {len(sheet_updates)} cells...")
        cells = [gspread.Cell(row, col_idx, val) for row, col_idx, val in sheet_updates]
        ws.update_cells(cells, value_input_option="USER_ENTERED")
        print("[Sheets] Done.")

    # Write CSV — sorted: SENSITIVE first, then by status
    csv_path = os.path.join(OUTPUTS_DIR, f"daily-comments-{today}.csv")
    sorted_results = (
        [r for r in results if r["sensitive"]] +
        [r for r in results if not r["sensitive"] and r["status"] == "Ready"] +
        [r for r in results if r["status"] not in ("Ready", "SENSITIVE")]
    )

    if not args.dry_run:
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["#", "Username", "Post URL", "Post Summary", "Comment Type", "Comment", "Status"])
            for i, r in enumerate(sorted_results, 1):
                comment_type = "SENSITIVE — REVIEW FIRST" if r["sensitive"] else ("STANDARD" if r["status"] == "Ready" else r["status"])
                writer.writerow([
                    i,
                    f"@{r['handle']}",
                    r["post_url"],
                    r["summary"],
                    comment_type,
                    "",  # Comment column — filled in Phase 2 by Claude
                    r["status"],
                ])
        print(f"\n[CSV] Written: {csv_path}")

    # Update commented log
    qualifying = [e for e in new_log_entries if e["post_url"]]
    append_commented_log(qualifying, dry_run=args.dry_run)
    if qualifying and not args.dry_run:
        print(f"[Log] {len(qualifying)} post URLs added to commented-log.csv")

    # Summary
    ready = len([r for r in results if r["status"] in ("Ready", "SENSITIVE")])
    print(f"\n{'='*60}")
    print(f"  Phase 1 complete — {today}")
    print(f"  Accounts processed:    {len(accounts)}")
    print(f"  Captions found:        {ready}")
    print(f"  SENSITIVE (flag):      {sensitive_count}")
    print(f"  No post / too old:     {no_post_count}")
    print(f"  Already commented:     {already_commented_count}")
    print(f"\n  NEXT STEP: Say 'run today' in Claude Code")
    print(f"  Claude will read the Post Caption column and generate")
    print(f"  personalized comments, then write them to the sheet.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
