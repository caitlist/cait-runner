"""
comments_workflow.py
--------------------
Three-mode script for the daily COMMENTS tab workflow.

Modes:
  --mode transfer   Read Medical Mom DM Outreach, find Notes="Approved" AND
                    DM Status != "IG DM", copy Handle + IG Profile Link to
                    COMMENTS tab (deduped).

  --mode scrape     Read COMMENTS tab rows missing Post Caption, scrape latest
                    non-pinned post via Apify, write Post URL + Post Caption to
                    sheet, output captions JSON for Claude to read.

  --mode write      Read outputs/comments_to_write.json (keyed by row number),
                    write Generated Comment + Date + Notes to COMMENTS tab.

Usage:
  python scripts/comments_workflow.py --mode transfer
  python scripts/comments_workflow.py --mode scrape
  python scripts/comments_workflow.py --mode write
"""

import os
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

APIFY_TOKEN      = os.environ.get("APIFY_TOKEN")
GOOGLE_SHEET_ID  = os.environ.get("GOOGLE_SHEET_ID")
GOOGLE_CREDS_PATH = os.environ.get("GOOGLE_CREDS_PATH")

PROFILE_ACTOR    = "apify/instagram-scraper"

SENSITIVE_KEYWORDS = [
    "icu", "picu", "nicu", "passed away", "gone too soon", "in memory",
    "loss", "losing", "lost my", "funeral", "died", "death", "terminal",
    "last days", "final days", "emergency surgery", "hospice", "code blue",
    "infant loss", "baby loss", "angel baby", "we lost",
]

CAPTIONS_JSON = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "outputs", "captions_for_comments.json"
)
COMMENTS_JSON = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "outputs", "comments_to_write.json"
)
POST_OPTIONS_JSON = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "outputs", "post_options.json"
)

# ── Sheet helpers ─────────────────────────────────────────────────────────────

def open_sheet():
    creds = Credentials.from_service_account_file(
        GOOGLE_CREDS_PATH,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(GOOGLE_SHEET_ID)
    return ss


def col_index(headers, name):
    """Return 0-based index of a column name."""
    try:
        return headers.index(name)
    except ValueError:
        raise ValueError(f"Column '{name}' not found in headers: {headers}")


# ── SENSITIVE detection ───────────────────────────────────────────────────────

def is_sensitive(caption: str) -> bool:
    low = caption.lower()
    return any(kw in low for kw in SENSITIVE_KEYWORDS)


# ── Apify scraping ────────────────────────────────────────────────────────────

def scrape_profiles(handles: list[str]) -> list[dict]:
    """Scrape Instagram profiles via Apify with RESIDENTIAL proxies."""
    client = ApifyClient(APIFY_TOKEN)
    results = []

    for i in range(0, len(handles), 10):
        batch = handles[i : i + 10]
        clean = [h.lstrip("@").lower().strip() for h in batch]
        print(f"  [Apify] Batch {i // 10 + 1}: {clean}")
        try:
            run_input = {
                "directUrls": [f"https://www.instagram.com/{u}/" for u in clean],
                "resultsType": "details",
                "resultsLimit": 20,
                "proxy": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"],
                },
            }
            run = client.actor(PROFILE_ACTOR).call(run_input=run_input)
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            results.extend(items)
            print(f"  [Apify] Got {len(items)} profiles back")
            time.sleep(3)
        except Exception as e:
            print(f"  [Apify] Error on batch starting at {i}: {e}")

    return results


RELEVANT_KEYWORDS = [
    "mom", "mama", "mother", "dad", "parent", "caregiver",
    "baby", "daughter", "son", "kid", "child", "toddler",
    "medical", "hospital", "diagnosis", "therapy", "therapist",
    "autism", "adhd", "cerebral palsy", "cp ", "down syndrome",
    "trach", "gtube", "feeding tube", "hlhs", "chd", "t1d",
    "diabetes", "seizure", "epilepsy", "rare disease", "special needs",
    "nicu", "picu", "icu", "surgery", "appointment", "specialist",
    "ot", "pt ", "slp", "iep", "wheelchair", "walker",
    "nonverbal", "milestone", "progress", "warrior", "fighter",
    "blessed", "grateful", "advocate", "awareness",
]

def is_collab_post(post: dict) -> bool:
    """Return True if this is a collaboration post (multiple accounts co-posting)."""
    coauthors = post.get("coauthorProducers") or post.get("coAuthorProducers") or []
    return len(coauthors) > 0


def get_best_post(profile: dict) -> dict | None:
    """Return the latest solo (non-collab) post by date.
    Pinned posts are included — date is the only sorting factor."""
    posts = profile.get("latestPosts") or profile.get("posts") or []
    def ts(p):
        return p.get("timestamp") or p.get("takenAtTimestamp") or 0
    sorted_posts = sorted(posts, key=ts, reverse=True)
    solo_posts = [p for p in sorted_posts if not is_collab_post(p)]
    return solo_posts[0] if solo_posts else None


def build_post_url(post: dict) -> str:
    url = post.get("url") or post.get("postUrl") or ""
    if url:
        return url
    short = post.get("shortCode") or post.get("shortcode") or ""
    if short:
        return f"https://www.instagram.com/p/{short}/"
    return ""


# ── Mode: transfer ────────────────────────────────────────────────────────────

def mode_transfer(ss):
    outreach_ws = ss.worksheet("Medical Mom DM Outreach")
    comments_ws = ss.worksheet("COMMENTS")

    print("Reading Medical Mom DM Outreach...")
    outreach_vals = outreach_ws.get_all_values()
    o_headers = [h.strip() for h in outreach_vals[0]]
    o_col = {h: i for i, h in enumerate(o_headers)}

    handle_col   = o_col.get("Handle")
    link_col     = o_col.get("IG Profile Link")
    status_col   = o_col.get("DM Status")
    notes_col    = o_col.get("Notes")

    if any(c is None for c in [handle_col, link_col, status_col, notes_col]):
        print("ERROR: Missing expected columns in Medical Mom DM Outreach.")
        return

    print("Reading COMMENTS tab (for dedup)...")
    comments_vals = comments_ws.get_all_values()
    existing_handles = set()
    if len(comments_vals) > 1:
        c_headers = [h.strip() for h in comments_vals[0]]
        try:
            c_handle_col = c_headers.index("Handle")
            for row in comments_vals[1:]:
                if row[c_handle_col].strip():
                    existing_handles.add(row[c_handle_col].strip().lstrip("@").lower())
        except (ValueError, IndexError):
            pass

    approved = []
    for row in outreach_vals[1:]:
        if len(row) <= max(handle_col, link_col, status_col, notes_col):
            continue
        notes  = row[notes_col].strip()
        status = row[status_col].strip()
        handle = row[handle_col].strip().lstrip("@")
        link   = row[link_col].strip()

        if notes.upper() != "APPROVE":
            continue
        if status == "IG DM":
            continue
        if not handle:
            continue
        if handle.lower() in existing_handles:
            continue

        approved.append([handle, link])
        existing_handles.add(handle.lower())

    if not approved:
        print("No new Approved accounts to transfer.")
        return

    print(f"Transferring {len(approved)} accounts to COMMENTS tab...")
    comments_ws.append_rows(approved, value_input_option="USER_ENTERED")
    print(f"Done. Transferred: {[row[0] for row in approved]}")


# ── Mode: scrape ──────────────────────────────────────────────────────────────

def mode_scrape(ss, force=False):
    comments_ws = ss.worksheet("COMMENTS")

    print("Reading COMMENTS tab...")
    all_vals = comments_ws.get_all_values()
    if len(all_vals) <= 1:
        print("COMMENTS tab is empty.")
        return

    headers = [h.strip() for h in all_vals[0]]
    c = {h: i for i, h in enumerate(headers)}

    # Find rows that need scraping: have Handle but missing Post Caption (or force=True for all)
    to_scrape = []  # (sheet_row_1indexed, handle, ig_link)
    for i, row in enumerate(all_vals[1:], start=2):
        handle  = row[c["Handle"]].strip().lstrip("@") if c.get("Handle") is not None and c["Handle"] < len(row) else ""
        caption = row[c["Post Caption"]].strip() if c.get("Post Caption") is not None and c["Post Caption"] < len(row) else ""
        link    = row[c["IG Profile Link"]].strip() if c.get("IG Profile Link") is not None and c["IG Profile Link"] < len(row) else ""
        needs_scrape = force or not caption or caption in ("RESTRICTED OR NOT FOUND", "No posts found")
        if handle and needs_scrape:
            to_scrape.append((i, handle, link))

    if not to_scrape:
        print("All rows already have Post Caption. Nothing to scrape.")
        return

    print(f"Scraping {len(to_scrape)} accounts...")
    handles = [row[1] for row in to_scrape]
    profiles = scrape_profiles(handles)

    # Map handle → profile
    profile_map = {}
    for p in profiles:
        username = (p.get("username") or p.get("handle") or "").lower().strip()
        if username:
            profile_map[username] = p

    # Build updates
    cells = []
    captions_out = []
    no_post = []
    restricted = []
    under_threshold = []

    post_url_col    = headers.index("Post URL") + 1      # 1-indexed for gspread
    post_cap_col    = headers.index("Post Caption") + 1
    notes_col_idx   = headers.index("Notes") + 1

    # Ensure "Post Timestamp" column exists
    if "Post Timestamp" not in headers:
        ts_col_letter = len(headers) + 1
        comments_ws.update_cell(1, ts_col_letter, "Post Timestamp")
        headers.append("Post Timestamp")
        print("Added 'Post Timestamp' column to sheet.")
    post_ts_col = headers.index("Post Timestamp") + 1

    under_threshold = []

    for sheet_row, handle, link in to_scrape:
        profile = profile_map.get(handle.lower())
        if not profile:
            # Could be restricted / not found
            cells.append(gspread.Cell(sheet_row, post_cap_col, "RESTRICTED OR NOT FOUND"))
            restricted.append(handle)
            continue

        # Note follower count for summary but do NOT skip — 1k rule is for discovery only
        followers = profile.get("followersCount") or profile.get("followers") or 0
        if followers < 1000:
            under_threshold.append(f"{handle} ({followers})")

        post = get_best_post(profile)
        if not post:
            cells.append(gspread.Cell(sheet_row, post_cap_col, "No posts found"))
            no_post.append(handle)
            continue

        post_url = build_post_url(post)
        caption  = (post.get("caption") or "").strip()
        cap_short = caption[:2000]  # cap at 2000 chars

        sensitive_flag = is_sensitive(cap_short)
        notes_val = "[SENSITIVE]" if sensitive_flag else ""

        def ts(p):
            return p.get("timestamp") or p.get("takenAtTimestamp") or 0

        cells.append(gspread.Cell(sheet_row, post_url_col,  post_url))
        cells.append(gspread.Cell(sheet_row, post_cap_col,  cap_short))
        if notes_val:
            cells.append(gspread.Cell(sheet_row, notes_col_idx, notes_val))
        # Write Unix timestamp so runner can display post age without shortcode decode
        cells.append(gspread.Cell(sheet_row, post_ts_col, ts(post)))
        all_solo = sorted(
            [p for p in (profile.get("latestPosts") or profile.get("posts") or []) if not is_collab_post(p)],
            key=ts, reverse=True
        )
        # Find rank of selected post (1 = latest, 2 = 2nd latest, etc.)
        selected_ts   = ts(post)
        selected_rank = 1
        for rank_idx, sp in enumerate(all_solo, start=1):
            if build_post_url(sp) == post_url:
                selected_rank = rank_idx
                break

        # Build alternatives list (all solo posts except selected, with rank + timestamp)
        alternatives = []
        for rank_idx, alt in enumerate(all_solo, start=1):
            alt_url = build_post_url(alt)
            if alt_url == post_url:
                continue
            alt_cap = (alt.get("caption") or "").strip()[:500]
            alternatives.append({
                "url":       alt_url,
                "caption":   alt_cap,
                "rank":      rank_idx,
                "timestamp": ts(alt),
            })
            if len(alternatives) >= 4:
                break

        captions_out.append({
            "row":            sheet_row,
            "handle":         handle,
            "ig_link":        link,
            "post_url":       post_url,
            "caption":        cap_short,
            "sensitive":      sensitive_flag,
            "post_rank":      selected_rank,
            "post_timestamp": selected_ts,
            "alternatives":   alternatives,
        })

    if cells:
        print(f"Writing {len(cells)} cells to sheet...")
        comments_ws.update_cells(cells, value_input_option="USER_ENTERED")

    # Write captions JSON for Claude to read
    with open(CAPTIONS_JSON, "w", encoding="utf-8") as f:
        json.dump(captions_out, f, indent=2, ensure_ascii=False)

    # Write post_options JSON for daily runner
    # Format: handle → { selected: {url, caption, rank, timestamp}, alternatives: [...] }
    post_options = {
        entry["handle"].lower().lstrip("@"): {
            "selected": {
                "url":       entry["post_url"],
                "caption":   entry["caption"],
                "rank":      entry.get("post_rank", 1),
                "timestamp": entry.get("post_timestamp", 0),
            },
            "alternatives": entry.get("alternatives", []),
        }
        for entry in captions_out
    }
    # Merge with existing post_options if file exists (preserves options from previous scrapes)
    if os.path.exists(POST_OPTIONS_JSON):
        with open(POST_OPTIONS_JSON, "r", encoding="utf-8") as f:
            existing = json.load(f)
        existing.update(post_options)
        post_options = existing
    with open(POST_OPTIONS_JSON, "w", encoding="utf-8") as f:
        json.dump(post_options, f, indent=2, ensure_ascii=False)

    print(f"\nSummary:")
    print(f"  Captions found:     {len(captions_out)}")
    print(f"  Under 1k followers: {len(under_threshold)} — {under_threshold}")
    print(f"  Restricted/404:     {len(restricted)} — {restricted}")
    print(f"  No posts found:     {len(no_post)} — {no_post}")
    print(f"  SENSITIVE posts:    {sum(1 for c in captions_out if c['sensitive'])}")
    print(f"\nCaptions written to: {CAPTIONS_JSON}")
    print("Now say 'generate comments' in Claude Code to generate and write all comments.")


# ── Mode: write ───────────────────────────────────────────────────────────────

def mode_write(ss):
    if not os.path.exists(COMMENTS_JSON):
        print(f"ERROR: {COMMENTS_JSON} not found. Claude must generate comments first.")
        return

    with open(COMMENTS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    # data format: list of {row, handle, comment, notes}
    # OR dict keyed by str(row): comment string

    comments_ws = ss.worksheet("COMMENTS")
    headers = [h.strip() for h in comments_ws.row_values(1)]
    gen_comment_col = headers.index("Generated Comment") + 1
    notes_col_idx   = headers.index("Notes") + 1
    date_col_idx    = headers.index("Date") + 1

    _now = datetime.datetime.now()
    now_str = _now.strftime("%B {d}, {h}:%M{ampm}").format(
        d=_now.day, h=_now.hour % 12 or 12,
        ampm="am" if _now.hour < 12 else "pm"
    )

    cells = []

    if isinstance(data, list):
        entries = data
    else:
        # dict format {str(row): comment}
        entries = [{"row": int(k), "comment": v, "notes": ""} for k, v in data.items()]

    for entry in entries:
        row_num = int(entry["row"])
        comment = entry.get("comment", "").strip()
        notes   = entry.get("notes", "").strip()

        if comment:
            cells.append(gspread.Cell(row_num, gen_comment_col, comment))
            cells.append(gspread.Cell(row_num, date_col_idx, now_str))
        if notes:
            # Append to existing notes (don't overwrite SENSITIVE flag)
            cells.append(gspread.Cell(row_num, notes_col_idx, notes))

    if not cells:
        print("No comments to write.")
        return

    print(f"Writing {len(entries)} comments to COMMENTS tab...")
    comments_ws.update_cells(cells, value_input_option="USER_ENTERED")
    print(f"Done. {len(entries)} comments written with timestamp {now_str}.")

    # Clean up
    os.remove(COMMENTS_JSON)
    print(f"Cleaned up {COMMENTS_JSON}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="COMMENTS tab workflow")
    parser.add_argument("--mode", required=True, choices=["transfer", "scrape", "write"],
                        help="transfer | scrape | write")
    parser.add_argument("--force", action="store_true",
                        help="scrape: re-scrape all accounts even if caption already exists")
    args = parser.parse_args()

    ss = open_sheet()

    if args.mode == "transfer":
        mode_transfer(ss)
    elif args.mode == "scrape":
        mode_scrape(ss, force=args.force)
    elif args.mode == "write":
        mode_write(ss)


if __name__ == "__main__":
    main()
