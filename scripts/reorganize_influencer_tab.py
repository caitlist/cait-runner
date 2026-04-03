"""
reorganize_influencer_tab.py
----------------------------
Restores from CSV backups, cleans, reorganizes, and color-codes the
"Influencer Pipeline" Google Sheet tab.

What it does:
  1. Reads all CSV backups from outputs/influencer_pipeline_*_2026-03-23.csv
  2. Corrects category labels per HANDLE_CATEGORY_OVERRIDES
  3. Removes rows: 0 followers, avg comments < 50, or inactive
  4. Renames "LOW ROI" -> "LOW%" in ER Score column
  5. Rewrites tab with clean 12-column schema + category summary at top
  6. Applies color coding per category
  7. Prints game plan for filling gaps

Run:
    python -X utf8 scripts/reorganize_influencer_tab.py
"""

import csv
import glob
import os
import sys
import time
from collections import defaultdict

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SHEET_ID   = os.environ.get("GOOGLE_SHEET_ID")
CREDS_PATH = os.environ.get("GOOGLE_CREDS_PATH")
OUTPUT_TAB = "Influencer Pipeline"
CSV_PATTERN = "outputs/influencer_pipeline_*_2026-03-23.csv"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ── Per-handle category overrides (correct mislabels + seed categorization) ──
HANDLE_CATEGORY_OVERRIDES = {
    # Seed verification — Loop Giveaway Moms
    "kayandtayofficial":  "Loop Giveaway Moms",
    "sophiahillll":       "Loop Giveaway Moms",
    "carlinbates98":      "Loop Giveaway Moms",
    "shelbreese":         "Loop Giveaway Moms",
    "devincordle":        "Loop Giveaway Moms",
    "abbyelizabethoward": "Loop Giveaway Moms",
    "emily.fauver":       "Loop Giveaway Moms",
    "micahandsarahhh":    "Loop Giveaway Moms",
    "gunnsgirls":         "Loop Giveaway Moms",
    "aivanelli":          "Loop Giveaway Moms",
    # Seed verification — Autism Mom Influencers
    "myarfidlife":        "Autism Mom Influencers",
    "storiesaboutautism": "Autism Mom Influencers",
    "nicolegottesmann":   "Autism Mom Influencers",
    # Seed verification — Down Syndrome Mom
    "makingmilliestones": "Down Syndrome Mom",
    "ourhuddybuddy":      "Down Syndrome Mom",
    "jess.hentges":       "Down Syndrome Mom",
    # Seed verification — Medical Moms
    "wonderfullifewithbedford": "Medical Moms Macro",
    "milas_crew":               "Medical Moms Micro",
    # Seed verification — Therapist Macro
    "courtneyenglish.ot":    "Therapist Macro",
    "thesensoryproject208":  "Therapist Macro",
    # Seed verification — Doctor Influencers
    "dr.beachgem10":  "Doctor Influencers",
    "dr.tommymartin": "Doctor Influencers",
    # Seed verification — Diabetic Adults
    "addytayler_t1d": "Diabetic Adults",
    # Mislabeled as "Doctor Influencers" — fixes
    "thekingofchemo":      "Adults with Cancer",
    "myjourneytojustlive": "Adults with Cancer",
    "ohyouresotough":      "Adults with Cancer",
    "chrispunsalan":       "Adult Caregivers",
    # T1D batch — T1D Moms
    "sugarmamastrong":   "Diabetic Moms (T1D child)",
    "lifeonsweetstreet": "Diabetic Moms (T1D child)",
    "dmomblog":          "Diabetic Moms (T1D child)",
    "t1dmomma":          "Diabetic Moms (T1D child)",
    "sweetlymanagedlife":"Diabetic Moms (T1D child)",
    "t1dparentstrong":   "Diabetic Moms (T1D child)",
    "type1amy":          "Diabetic Moms (T1D child)",
    # T1D batch — Diabetic Adults
    "diabeticsdoingthings": "Diabetic Adults",
    "sugarcoateddiabetic":  "Diabetic Adults",
    "t1dstrong":            "Diabetic Adults",
}

# ── Fallback CSV category name → CATEGORY_TARGETS key ────────────────────────
CSV_CATEGORY_MAP = {
    # Original session CSV category names (different from CATEGORY_TARGETS keys)
    "Autism Mom Influencers":        "Autism Mom Influencers",
    "Down Syndrome Mom Influencers": "Down Syndrome Mom",
    "Medical Moms":                  "Medical Moms Macro",
    "Therapist Influencers (Macro)": "Therapist Macro",
    "Doctor Influencers":            "Doctor Influencers",
    "Regular Mom Influencers":       "Regular Mom Influencers",
    # Discover-mode CSVs use exact CATEGORY_TARGETS key names — pass through
    "Loop Giveaway Moms":            "Loop Giveaway Moms",
    "Down Syndrome Mom":             "Down Syndrome Mom",
    "Medical Moms Macro":            "Medical Moms Macro",
    "Medical Moms Micro":            "Medical Moms Micro",
    "Therapist Macro":               "Therapist Macro",
    "Adults with Cancer":            "Adults with Cancer",
    "Adult Caregivers":              "Adult Caregivers",
    "Diabetic Moms (T1D child)":     "Diabetic Moms (T1D child)",
    "Diabetic Adults":               "Diabetic Adults",
    # Per-handle resolution required
    "Seed Verification":             None,
    "T1D and Diabetic Adults":       None,
    "Final Cleanup Batch":           None,
}

# ── Category targets ──────────────────────────────────────────────────────────
CATEGORY_TARGETS = {
    "Loop Giveaway Moms":          20,
    "Autism Mom Influencers":      30,
    "Down Syndrome Mom":           10,
    "Medical Moms Macro":          20,
    "Medical Moms Micro":          10,
    "Therapist Macro":             20,
    "Doctor Influencers":          10,
    "Adults with Cancer":          10,
    "Adult Caregivers":            10,
    "Diabetic Moms (T1D child)":   10,
    "Diabetic Adults":             10,
    "Regular Mom Influencers":     20,
}

CATEGORY_ORDER = list(CATEGORY_TARGETS.keys())

# ── Handles already in other tabs — excluded per zero-dups rule ───────────────
CROSS_TAB_EXCLUDE = {
    "thekinected_ot",    # in CAIT Community tab
    "thesimpleot",       # in CAIT Community tab
}

# ── Color map (RGB 0-1 scale) ─────────────────────────────────────────────────
CATEGORY_COLORS = {
    "Loop Giveaway Moms":          {"red": 0.78, "green": 0.90, "blue": 1.00},
    "Autism Mom Influencers":      {"red": 0.87, "green": 0.78, "blue": 1.00},
    "Down Syndrome Mom":           {"red": 1.00, "green": 0.87, "blue": 0.68},
    "Medical Moms Macro":          {"red": 0.78, "green": 0.95, "blue": 0.78},
    "Medical Moms Micro":          {"red": 0.70, "green": 0.94, "blue": 0.94},
    "Therapist Macro":             {"red": 1.00, "green": 0.97, "blue": 0.70},
    "Doctor Influencers":          {"red": 1.00, "green": 0.78, "blue": 0.84},
    "Adults with Cancer":          {"red": 1.00, "green": 0.78, "blue": 0.78},
    "Adult Caregivers":            {"red": 0.90, "green": 0.90, "blue": 0.90},
    "Diabetic Moms (T1D child)":   {"red": 1.00, "green": 0.87, "blue": 0.80},
    "Diabetic Adults":             {"red": 1.00, "green": 0.80, "blue": 0.78},
    "Regular Mom Influencers":     {"red": 0.90, "green": 0.85, "blue": 1.00},
}

SUMMARY_GREEN  = {"red": 0.72, "green": 0.94, "blue": 0.72}
SUMMARY_YELLOW = {"red": 1.00, "green": 0.96, "blue": 0.70}
SUMMARY_RED    = {"red": 1.00, "green": 0.78, "blue": 0.78}
DARK_HEADER_BG = {"red": 0.20, "green": 0.20, "blue": 0.30}
DARK_HEADER_FG = {"red": 1.00, "green": 1.00, "blue": 1.00}

NEW_HEADERS = [
    "Handle", "Category", "Followers",
    "Avg Comments", "Avg Likes", "Engagement Rate %",
    "ER Score", "Comment Score",
    "Active?", "USA Signal", "Included", "Notes",
]

DISCOVERY_METHODS = {
    "Loop Giveaway Moms":
        "Manual IG search on tagged posts: @pzsocialgiveaways @socialstance @savvygiveaways",
    "Autism Mom Influencers":
        "Apify hashtag scraper: #autismmom #autismfamily #autismparent",
    "Down Syndrome Mom":
        "Apify hashtag scraper: #downsyndromemom #t21mom #trisomy21",
    "Medical Moms Macro":
        "REALITY CHECK: no 500K+ medical moms exist on IG. Expand to 100K+ mid-tier or use TikTok.",
    "Medical Moms Micro":
        "Apify hashtag scraper: #medicalmom #medkid #complexneeds #hospitallife",
    "Therapist Macro":
        "Apify hashtag scraper: #slp #occupationaltherapy #bcba #speechtherapist",
    "Doctor Influencers":
        "Apify hashtag scraper: #pediatrician #mommd #doctoroninstagram",
    "Adults with Cancer":
        "Apify hashtag scraper: #cancerwarrior #cancerjourney #cancerawareness",
    "Adult Caregivers":
        "Apify hashtag scraper: #caregiverlife #sandwichgeneration #eldercare",
    "Diabetic Moms (T1D child)":
        "TikTok-first (clockworks/tiktok-scraper) — this niche has migrated off IG",
    "Diabetic Adults":
        "TikTok-first (clockworks/tiktok-scraper) — this niche has migrated off IG",
    "Regular Mom Influencers":
        "TikTok + curated web list — mommy blogger era is over on IG",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_sheet():
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    try:
        return sh.worksheet(OUTPUT_TAB)
    except gspread.WorksheetNotFound:
        print(f"[ERROR] Tab '{OUTPUT_TAB}' not found.")
        sys.exit(1)


def safe_float(val):
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0


def normalize_handle(h):
    return str(h).lstrip("@").lower().strip()


def is_active(val):
    return str(val).strip().lower() in ("yes", "true", "1", "active", "y")


def build_notes(row):
    """Collapse Platform, Loop Giveaway History, Name, Macro/Micro, Notes into one cell."""
    parts = []
    name     = str(row.get("Name", "")).strip()
    platform = str(row.get("Platform", "")).strip()
    loop     = str(row.get("Loop Giveaway History", "")).strip()
    macro    = str(row.get("Macro/Micro", "")).strip()
    notes    = str(row.get("Notes", "")).strip()

    if platform and platform.lower() not in ("instagram", ""):
        parts.append(f"Platform: {platform}")
    if loop and loop.lower() not in ("unknown", "n/a", ""):
        parts.append(f"Loop: {loop}")
    if macro and macro.lower() not in ("", "unknown"):
        parts.append(macro)
    if name:
        parts.append(f"Name: {name}")
    if notes and notes not in ("", "—"):
        parts.append(notes)

    return " | ".join(parts)


def resolve_category(handle_key, csv_category):
    """Return the correct CATEGORY_TARGETS key for this handle."""
    if handle_key in HANDLE_CATEGORY_OVERRIDES:
        return HANDLE_CATEGORY_OVERRIDES[handle_key]
    mapped = CSV_CATEGORY_MAP.get(csv_category)
    return mapped  # may be None for unresolved "Final Cleanup Batch" etc.


# ── Main ──────────────────────────────────────────────────────────────────────

def read_sheet_data(ws) -> list[dict]:
    """
    Read data rows from the sheet, skipping the summary block at the top.
    Finds the header row by looking for a row starting with "Handle".
    Returns list of dicts keyed by column header.
    """
    all_values = ws.get_all_values()
    header_row_idx = None
    for i, row in enumerate(all_values):
        if row and row[0].strip().lower() == "handle":
            header_row_idx = i
            break

    if header_row_idx is None:
        return []

    headers = all_values[header_row_idx]
    data = []
    for row in all_values[header_row_idx + 1:]:
        if not row or not row[0].strip():
            continue
        record = dict(zip(headers, row))
        data.append(record)
    return data


def main():
    # ── Step 1: Load from sheet (primary) + CSV fallback for first-run ────────
    print("Reading from Google Sheet...")
    ws = get_sheet()
    sheet_rows = read_sheet_data(ws)
    print(f"  Found {len(sheet_rows)} data rows in sheet")

    # Always load from CSVs — discover mode writes in a different column order
    # than reorganize's schema, so sheet rows are unreliable as input source.
    # CSVs are the authoritative source; the sheet is write-only for this script.
    if True:
        csv_files = sorted(glob.glob(CSV_PATTERN))
        if not csv_files:
            print(f"[ERROR] Sheet empty and no CSVs found at: {CSV_PATTERN}")
            sys.exit(1)
        print(f"  Sheet empty — loading from {len(csv_files)} CSV backups...")
        raw_by_handle = {}
        for fpath in csv_files:
            fname = os.path.basename(fpath)
            with open(fpath, encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            print(f"    {fname}: {len(rows)} rows")
            for row in rows:
                key = normalize_handle(row.get("Handle", ""))
                if not key:
                    continue
                existing_cat = raw_by_handle.get(key, {}).get("Category", "")
                if key not in raw_by_handle or existing_cat in ("Seed Verification", "Final Cleanup Batch"):
                    raw_by_handle[key] = row
    else:
        # Use sheet rows directly — they already have resolved categories
        raw_by_handle = {}
        for row in sheet_rows:
            key = normalize_handle(row.get("Handle", ""))
            if key:
                raw_by_handle[key] = row

    print(f"  Total unique handles to process: {len(raw_by_handle)}")

    # ── Step 2: Resolve categories + filter ──────────────────────────────────
    kept    = []
    removed = []

    for key, row in raw_by_handle.items():
        handle      = str(row.get("Handle", "")).strip()
        # For sheet rows: "Category" is already the resolved name
        # For CSV rows: may need CSV_CATEGORY_MAP resolution
        raw_cat     = str(row.get("Category", "")).strip()
        followers   = safe_float(row.get("Followers", 0))
        avg_comments = safe_float(row.get("Avg Comments (real)", row.get("Avg Comments", 0)))
        active_val  = row.get("Active (30 days)", row.get("Active?", ""))

        # Skip handles already present in other sheet tabs (zero-dups rule)
        if key in CROSS_TAB_EXCLUDE:
            removed.append((handle, "already in CAIT Community tab — cross-tab dup"))
            continue

        # Handle-level overrides take priority over any category in the data
        if key in HANDLE_CATEGORY_OVERRIDES:
            category = HANDLE_CATEGORY_OVERRIDES[key]
        elif raw_cat in CATEGORY_TARGETS:
            category = raw_cat
        else:
            # CSV fallback path
            category = resolve_category(key, raw_cat)

        if category is None:
            removed.append((handle, f"unresolvable category ({raw_cat})"))
            continue

        if followers == 0:
            removed.append((handle, "0 followers — dead/failed scrape"))
            continue

        if avg_comments < 50:
            removed.append((handle, f"{avg_comments:.0f} avg comments < 50 (not high engagement)"))
            continue

        if not is_active(active_val):
            removed.append((handle, f"inactive ({active_val})"))
            continue

        kept.append((category, row))

    print(f"\n  Kept: {len(kept)}")
    print(f"  Removed: {len(removed)}")

    # ── Step 3: Build clean rows ──────────────────────────────────────────────
    clean_rows = []
    for category, row in kept:
        handle       = str(row.get("Handle", "")).strip()
        followers    = int(safe_float(row.get("Followers", 0)))
        avg_comments = round(safe_float(row.get("Avg Comments (real)", row.get("Avg Comments", 0))), 1)
        avg_likes    = round(safe_float(row.get("Avg Likes", 0)), 1)
        er_pct       = round(safe_float(row.get("Engagement Rate %", 0)), 2)
        er_score     = str(row.get("ER Score", "")).replace("LOW ROI", "LOW%").strip()
        comment_score = str(row.get("Comment Score", "")).strip()
        usa_signal   = str(row.get("USA Signal", "Unknown")).strip()
        notes        = build_notes(row)

        clean_rows.append({
            "Handle":            handle,
            "Category":          category,
            "Followers":         followers,
            "Avg Comments":      avg_comments,
            "Avg Likes":         avg_likes,
            "Engagement Rate %": er_pct,
            "ER Score":          er_score,
            "Comment Score":     comment_score,
            "Active?":           "Yes",
            "USA Signal":        usa_signal,
            "Included":          "Yes",
            "Notes":             notes,
        })

    # ── Step 4: Sort by category order, then avg comments descending ──────────
    def sort_key(r):
        cat_idx = CATEGORY_ORDER.index(r["Category"]) if r["Category"] in CATEGORY_ORDER else 999
        return (cat_idx, -r["Avg Comments"])

    clean_rows.sort(key=sort_key)

    # ── Step 5: Count per category ────────────────────────────────────────────
    cat_counts = defaultdict(int)
    for r in clean_rows:
        cat_counts[r["Category"]] += 1

    # ── Step 6: Compose all rows ──────────────────────────────────────────────
    #
    # Row  1 : Title
    # Row  2 : ER formula note
    # Row  3 : blank
    # Row  4 : Summary header
    # Rows 5-16 : Summary data (12 categories)
    # Row 17 : blank separator
    # Row 18 : Data column headers
    # Row 19+: Data rows
    #
    TITLE_ROW       = 1
    ER_NOTE_ROW     = 2
    SUMMARY_HDR_ROW = 4
    SUMMARY_START   = 5
    SUMMARY_END     = SUMMARY_START + len(CATEGORY_TARGETS) - 1   # 16
    DATA_HDR_ROW    = SUMMARY_END + 2                              # 18
    DATA_START_ROW  = DATA_HDR_ROW + 1                            # 19

    sheet_rows = []

    sheet_rows.append(["INFLUENCER PIPELINE"] + [""] * 11)

    sheet_rows.append([
        "ER% = (Avg Likes + Avg Comments) / Followers x 100   |   "
        "Included = Active + SOLID (>=50 avg comments) or HIGH VALUE (>=200)"
    ] + [""] * 11)

    sheet_rows.append([""] * 12)  # blank

    sheet_rows.append(["Category", "Target", "Found", "Gap", "Status"] + [""] * 7)

    summary_statuses = {}
    for cat in CATEGORY_ORDER:
        target = CATEGORY_TARGETS[cat]
        found  = cat_counts.get(cat, 0)
        gap    = max(0, target - found)
        if found >= target:
            status = "MET"
        elif found >= target * 0.5:
            status = "PARTIAL"
        else:
            status = "NEEDS MORE"
        summary_statuses[cat] = status
        sheet_rows.append([cat, target, found, gap, status] + [""] * 7)

    sheet_rows.append([""] * 12)  # blank separator

    sheet_rows.append(NEW_HEADERS)

    for r in clean_rows:
        sheet_rows.append([
            r["Handle"], r["Category"], r["Followers"],
            r["Avg Comments"], r["Avg Likes"], r["Engagement Rate %"],
            r["ER Score"], r["Comment Score"],
            r["Active?"], r["USA Signal"], r["Included"], r["Notes"],
        ])

    # ── Step 7: Clear and write ───────────────────────────────────────────────
    print("\nClearing sheet and rewriting...")
    ws = get_sheet()
    ws.clear()
    time.sleep(1)

    ws.update(values=sheet_rows, range_name="A1", value_input_option="USER_ENTERED")
    print(f"  Written {len(sheet_rows)} total rows ({len(clean_rows)} data rows)")
    time.sleep(2)

    # ── Step 8: Formatting ────────────────────────────────────────────────────
    print("Applying formatting...")

    ws.format(f"A{TITLE_ROW}:L{TITLE_ROW}", {
        "backgroundColor": DARK_HEADER_BG,
        "textFormat": {"bold": True, "fontSize": 13, "foregroundColor": DARK_HEADER_FG},
        "horizontalAlignment": "CENTER",
    })
    time.sleep(0.5)

    ws.format(f"A{ER_NOTE_ROW}:L{ER_NOTE_ROW}", {
        "backgroundColor": {"red": 0.95, "green": 0.95, "blue": 0.95},
        "textFormat": {"italic": True, "fontSize": 9},
    })
    time.sleep(0.5)

    ws.format(f"A{SUMMARY_HDR_ROW}:E{SUMMARY_HDR_ROW}", {
        "backgroundColor": {"red": 0.80, "green": 0.80, "blue": 0.80},
        "textFormat": {"bold": True},
    })
    time.sleep(0.5)

    for i, cat in enumerate(CATEGORY_ORDER):
        row_num = SUMMARY_START + i
        status  = summary_statuses[cat]
        bg = SUMMARY_GREEN if status == "MET" else (SUMMARY_YELLOW if status == "PARTIAL" else SUMMARY_RED)
        ws.format(f"A{row_num}:E{row_num}", {"backgroundColor": bg})
        time.sleep(0.25)

    ws.format(f"A{DATA_HDR_ROW}:L{DATA_HDR_ROW}", {
        "backgroundColor": DARK_HEADER_BG,
        "textFormat": {"bold": True, "foregroundColor": DARK_HEADER_FG},
        "horizontalAlignment": "CENTER",
    })
    time.sleep(0.5)

    # Color category data blocks
    current_cat   = None
    cat_start_row = DATA_START_ROW
    format_blocks = []

    for i, r in enumerate(clean_rows):
        cat     = r["Category"]
        row_num = DATA_START_ROW + i
        if cat != current_cat:
            if current_cat is not None:
                color = CATEGORY_COLORS.get(current_cat)
                if color:
                    format_blocks.append((f"A{cat_start_row}:L{row_num - 1}", color))
            current_cat   = cat
            cat_start_row = row_num

    if current_cat is not None:
        last_row = DATA_START_ROW + len(clean_rows) - 1
        color = CATEGORY_COLORS.get(current_cat)
        if color:
            format_blocks.append((f"A{cat_start_row}:L{last_row}", color))

    for range_str, color in format_blocks:
        ws.format(range_str, {"backgroundColor": color})
        time.sleep(0.35)

    # ── Step 9: Print results ─────────────────────────────────────────────────
    W = 72
    print("\n" + "=" * W)
    print("CATEGORY SUMMARY")
    print("=" * W)
    print(f"  {'Category':<30}  {'Target':>6}  {'Found':>5}  {'Gap':>5}  Status")
    print("-" * W)

    total_target = 0
    total_found  = 0
    for cat in CATEGORY_ORDER:
        target = CATEGORY_TARGETS[cat]
        found  = cat_counts.get(cat, 0)
        gap    = max(0, target - found)
        status = summary_statuses[cat]
        total_target += target
        total_found  += found
        print(f"  {cat:<30}  {target:>6}  {found:>5}  {gap:>5}  {status}")

    print("-" * W)
    print(f"  {'TOTAL':<30}  {total_target:>6}  {total_found:>5}  {max(0, total_target - total_found):>5}")

    print("\n" + "=" * W)
    print("REMOVED ACCOUNTS")
    print("=" * W)
    for h, reason in removed:
        print(f"  {h}: {reason}")

    print("\n" + "=" * W)
    print("GAME PLAN — HOW TO FILL GAPS")
    print("=" * W)
    for cat in CATEGORY_ORDER:
        target = CATEGORY_TARGETS[cat]
        found  = cat_counts.get(cat, 0)
        gap    = max(0, target - found)
        if gap == 0:
            continue
        method = DISCOVERY_METHODS.get(cat, "Manual research")
        print(f"\n  [{cat}] Need {gap} more")
        print(f"    -> {method}")

    print("\n" + "=" * W)
    print(f"  DONE. Kept {len(kept)} | Removed {len(removed)} | Sheet: {len(sheet_rows)} rows written")
    print("=" * W)


if __name__ == "__main__":
    main()
