"""
run_discovery.py
----------------
Main orchestrator. Run a full discovery pipeline for one category.
Reads the sheet -> discovers -> qualifies -> enriches -> writes -> logs.

Usage:
    # Facebook (all categories via google-search-scraper, no rental needed)
    python scripts/run_discovery.py --category facebook_autism
    python scripts/run_discovery.py --category facebook_medical_moms
    python scripts/run_discovery.py --category facebook_trach
    python scripts/run_discovery.py --category facebook_epilepsy
    python scripts/run_discovery.py --category facebook_t1d
    python scripts/run_discovery.py --category facebook_down_syndrome
    python scripts/run_discovery.py --category facebook_cerebral_palsy
    python scripts/run_discovery.py --category facebook_nicu
    python scripts/run_discovery.py --category facebook_pediatric_cancer
    python scripts/run_discovery.py --category facebook_cystic_fibrosis
    python scripts/run_discovery.py --category facebook_rare_disease
    python scripts/run_discovery.py --category facebook_feeding_tube
    python scripts/run_discovery.py --category facebook_philippines
    python scripts/run_discovery.py --category facebook_all  # runs all USA categories

    # Instagram
    python scripts/run_discovery.py --category instagram_cait_community --diagnosis autism
    python scripts/run_discovery.py --category instagram_50million --diagnosis medically_complex
    python scripts/run_discovery.py --category instagram_foundations

    # Reddit
    python scripts/run_discovery.py --category reddit_medical_moms
    python scripts/run_discovery.py --category reddit_autism

Options:
    --batch-size     Number of entries to write (default: 25 for Facebook, 5 for others)
    --diagnosis      Diagnosis category for Instagram runs (default: medically_complex)
    --dry-run        Run discovery and qualification but do NOT write to sheet
"""

import os
import sys
import argparse
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

# Tab mapping: category flag -> sheet tab name
CATEGORY_TO_TAB = {
    # Facebook USA (all via apify/google-search-scraper — no rental)
    "facebook_autism": "US autism Facebook Group Communities",
    "facebook_medical_moms": "US Facebook Medical Moms",
    "facebook_trach": "US Facebook Medical Moms",
    "facebook_feeding_tube": "US Facebook Medical Moms",
    "facebook_epilepsy": "US Facebook Medical Moms",
    "facebook_t1d": "US Facebook Medical Moms",
    "facebook_down_syndrome": "US Facebook Medical Moms",
    "facebook_cerebral_palsy": "US Facebook Medical Moms",
    "facebook_nicu": "US Facebook Medical Moms",
    "facebook_pediatric_cancer": "US Facebook Medical Moms",
    "facebook_cystic_fibrosis": "US Facebook Medical Moms",
    "facebook_rare_disease": "US Facebook Medical Moms",
    "facebook_all": "US Facebook Medical Moms",  # multi-category; autism routed separately inside facebook_groups.py
    # Facebook Philippines
    "facebook_philippines": "Philippines Facebook Groups",
    # Instagram
    "instagram_cait_community": "CAIT Community",
    "instagram_50million": "50 Million List",
    "instagram_foundations": "Foundations & Organizations",
    # Reddit
    "reddit_medical_moms": "US Reddit Medical Moms",
    "reddit_autism": "US autism Reddit Group Communities",
}

INSTAGRAM_CATEGORIES = {"instagram_cait_community", "instagram_50million", "instagram_foundations"}
FACEBOOK_CATEGORIES = {k for k in CATEGORY_TO_TAB if k.startswith("facebook_")}
REDDIT_CATEGORIES = {"reddit_medical_moms", "reddit_autism"}

ALL_CATEGORIES = list(CATEGORY_TO_TAB.keys())


def log_run(category: str, results: dict, notes: str = ""):
    """Append a run log entry to memory/YYYY-MM-DD.md."""
    os.makedirs("memory", exist_ok=True)
    date_str = datetime.date.today().isoformat()
    path = f"memory/{date_str}.md"

    timestamp = datetime.datetime.now().strftime("%H:%M")
    entry = f"""
## Run: {category} @ {timestamp}

- Written: {results.get('written', 0)}
- Skipped (duplicates): {results.get('skipped_duplicates', 0)}
- Errors: {results.get('errors', 0)}
- Tab: {CATEGORY_TO_TAB.get(category, 'unknown')}
"""
    if notes:
        entry += f"\n### Notes\n{notes}\n"

    with open(path, "a", encoding="utf-8") as f:
        if not os.path.exists(path):
            f.write(f"# Run Log — {date_str}\n")
        f.write(entry)

    print(f"[run] Run logged to memory/{date_str}.md")


def run_facebook(category: str, batch_size: int, dry_run: bool) -> dict:
    from scripts.facebook_groups import run as facebook_run
    from scripts.write_sheet import write_rows

    results = facebook_run(category=category, batch_size=batch_size)
    if not results:
        print("[run] No results from Facebook discovery.")
        return {"written": 0, "skipped_duplicates": 0, "errors": 0}

    if dry_run:
        print(f"[run] DRY RUN — would write {min(len(results), batch_size)} rows")
        for r in results[:batch_size]:
            print(f"  - {r['community_name']} | {r['num_members']} members")
        return {"written": 0, "skipped_duplicates": 0, "errors": 0}

    tab = CATEGORY_TO_TAB[category]
    return write_rows(tab_name=tab, rows=results, batch_size=batch_size)


def run_instagram(category: str, diagnosis: str, batch_size: int, dry_run: bool) -> dict:
    from scripts.write_sheet import write_rows

    # Foundations: separate pipeline — curated seed list, org qualification, exec enrichment
    if category == "instagram_foundations":
        from scripts.instagram_foundations import run as foundations_run
        # Always get all qualified results — dedup handles what gets written
        results = foundations_run(batch_size=100)
        if not results:
            print("[run] No results from foundations discovery.")
            return {"written": 0, "skipped_duplicates": 0, "errors": 0}

        if dry_run:
            print(f"[run] DRY RUN — would write {len(results)} foundations")
            for r in results:
                print(f"  {r['org_name']} (@{r['username']}) | {r['followers']:,} followers | {r['diagnosis']}")
            return {"written": 0, "skipped_duplicates": 0, "errors": 0}

        tab = CATEGORY_TO_TAB[category]
        return write_rows(tab_name=tab, rows=results, batch_size=len(results))

    # Standard Instagram discovery (50 Million List + CAIT Community)
    from scripts.instagram_discovery import run as ig_run
    from scripts.enrich_email import enrich_batch

    results = ig_run(category=category, diagnosis=diagnosis, batch_size=batch_size)
    if not results:
        print("[run] No results from Instagram discovery.")
        return {"written": 0, "skipped_duplicates": 0, "errors": 0}

    # Enrich emails
    if category == "instagram_cait_community":
        print(f"[run] Enriching emails for {len(results)} accounts...")
        results = enrich_batch(results)
        found_emails = sum(1 for r in results if r.get("email"))
        print(f"[run] Email find rate: {found_emails}/{len(results)}")

    if dry_run:
        print(f"[run] DRY RUN — would write {len(results)} rows")
        for r in results:
            print(f"  @{r['username']} | {r['followers']} followers | {r['avg_comments']} avg comments | email: {r.get('email', 'none')}")
        return {"written": 0, "skipped_duplicates": 0, "errors": 0}

    tab = CATEGORY_TO_TAB[category]
    # Write ALL qualified — not just batch_size
    return write_rows(tab_name=tab, rows=results, batch_size=len(results))


def run_reddit(category: str, batch_size: int, dry_run: bool) -> dict:
    from scripts.reddit_discovery import run as reddit_run
    from scripts.write_sheet import write_rows

    results = reddit_run(category=category, batch_size=batch_size)
    if not results:
        print("[run] No results from Reddit discovery.")
        return {"written": 0, "skipped_duplicates": 0, "errors": 0}

    if dry_run:
        print(f"[run] DRY RUN — would write {min(len(results), batch_size)} rows")
        for r in results[:batch_size]:
            print(f"  {r['community_name']} | {r['num_members']:,} members")
        return {"written": 0, "skipped_duplicates": 0, "errors": 0}

    tab = CATEGORY_TO_TAB[category]
    return write_rows(tab_name=tab, rows=results, batch_size=batch_size)


def main():
    parser = argparse.ArgumentParser(
        description="CAIT Lister — run discovery for one category"
    )
    parser.add_argument(
        "--category", required=True, choices=ALL_CATEGORIES,
        help="Category to run"
    )
    parser.add_argument(
        "--diagnosis", default="medically_complex",
        help="Diagnosis focus for Instagram runs (default: medically_complex)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=5,
        help="Number of entries to write (default: 5)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Discover and qualify but do NOT write to sheet"
    )

    args = parser.parse_args()
    category = args.category
    tab = CATEGORY_TO_TAB[category]

    print(f"\n{'='*60}")
    print(f"CAIT Lister — Discovery Run")
    print(f"Category : {category}")
    print(f"Tab      : {tab}")
    print(f"Batch    : {args.batch_size}")
    print(f"Dry run  : {args.dry_run}")
    print(f"{'='*60}\n")

    # Dispatch to the correct pipeline
    if category in FACEBOOK_CATEGORIES:
        write_results = run_facebook(category, args.batch_size, args.dry_run)
    elif category in INSTAGRAM_CATEGORIES:
        write_results = run_instagram(category, args.diagnosis, args.batch_size, args.dry_run)
    elif category in REDDIT_CATEGORIES:
        write_results = run_reddit(category, args.batch_size, args.dry_run)
    else:
        print(f"[run] Unknown category: {category}")
        sys.exit(1)

    # Log the run
    if not args.dry_run:
        log_run(category, write_results)

    print(f"\n{'='*60}")
    print(f"Run complete.")
    print(f"Written: {write_results.get('written', 0)}")
    print(f"Skipped (duplicates): {write_results.get('skipped_duplicates', 0)}")
    print(f"Errors: {write_results.get('errors', 0)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
