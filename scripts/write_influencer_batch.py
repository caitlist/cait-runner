"""
write_influencer_batch.py
--------------------------
One-time script: enrich and write all 30 confirmed influencer/expert accounts
to the CAIT Community tab.

Data source: outputs/influencer_qualification_2026-03-18.csv (Apify confirmed)
Dedup: write_sheet.py handles this — @biglittlefeelings, @melrobbins, @pedsdoctalk
       will be silently skipped if already present.

Usage:
    python scripts/write_influencer_batch.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.enrich_email import enrich_email
from scripts.write_sheet import write_rows

# All 30 confirmed accounts.
# Fields: username, followers, avg_comments, website, _bio, category,
#         products (what they sell), gender, country
# Notes col format written by this script: [Gender] | [Country] | [Tier] | [What they sell]

ACCOUNTS = [
    {
        "username": "biglittlefeelings",
        "followers": 3543698,
        "avg_comments": 3114.9,
        "website": "https://biglittlefeelings.komi.io/",
        "_bio": "Child Therapist and Parent Coach. Brain Based Parenting. Strategies that Work in Under 5 Minutes.",
        "category": "Child Therapist",
        "products": "Toddler behavior course",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "melrobbins",
        "followers": 12284668,
        "avg_comments": 2094.9,
        "website": "https://spoti.fi/4caMYrI",
        "_bio": "Hey I'm Mel. Host @themelrobbinspodcast. Author @letthemtheory, #1 sold book of 2025.",
        "category": "Author / Speaker",
        "products": "Books + courses",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "drjoelgator",
        "followers": 378898,
        "avg_comments": 2020.6,
        "website": "https://linktr.ee/drjoelgator",
        "_bio": "Helping parents make sense of children's health. Pediatrician. Author. Dad.",
        "category": "Pediatrician",
        "products": "Integrative pediatric programs",
        "gender": "M",
        "country": "USA",
    },
    {
        "username": "drmarkhyman",
        "followers": 3685453,
        "avg_comments": 2293.2,
        "website": "https://linktr.ee/drmarkhyman",
        "_bio": "Founder @clevelandclinic Functional Medicine. Co-Founder @function. 16x NYT Bestselling Author.",
        "category": "Functional Medicine MD",
        "products": "Membership + books",
        "gender": "M",
        "country": "USA",
    },
    {
        "username": "peterattiamd",
        "followers": 1609401,
        "avg_comments": 1790.4,
        "website": "https://linktr.ee/PeterAttiaMD",
        "_bio": "MD focused on longevity science, #1 NYT author (Outlive), host of The Drive podcast.",
        "category": "Longevity MD",
        "products": "Books + podcast",
        "gender": "M",
        "country": "USA",
    },
    {
        "username": "kristinakuzmic",
        "followers": 1196924,
        "avg_comments": 1929.3,
        "website": "http://linktr.ee/kristinakuzmic",
        "_bio": "Parenting non-expert, Author, Mental Health advocate. Host of the Hope & Humor podcast.",
        "category": "Parenting Author",
        "products": "Books + speaking",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "busytoddler",
        "followers": 2407853,
        "avg_comments": 2023.2,
        "website": "http://playingpreschool.com/",
        "_bio": "Making it to naps, one activity at a time. Former K&1 Teacher. Master's in Early Childhood Education.",
        "category": "Early Childhood Educator",
        "products": "Books + homeschool curriculum + activities",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "pedsdoctalk",
        "followers": 1688589,
        "avg_comments": 1411.0,
        "website": "https://linktr.ee/pedsdoctalk",
        "_bio": "Pediatrician + Mom + CMO @heypoppins. TOP Podcast @thepedsdoctalkpodcast. FREE and PAID Resources.",
        "category": "Pediatrician",
        "products": "Parenting education resources",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "doctorshefali",
        "followers": 1339469,
        "avg_comments": 600.9,
        "website": "https://www.drshefali.com/raisingconscious-daughters-sons/",
        "_bio": "Host of podcast: PARENTING & YOU. 3 x NYT Bestselling Author. CEO Conscious Coaching Institute.",
        "category": "Clinical Psychologist",
        "products": "Conscious parenting courses",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "jayshetty",
        "followers": 18456779,
        "avg_comments": 1148.6,
        "website": "https://jayshettypodcast.com/NewEpisode",
        "_bio": "Author, Podcaster, Speaker, Coach. #1 @nytimes.",
        "category": "Author / Coach",
        "products": "Courses + speaking",
        "gender": "M",
        "country": "USA",
    },
    {
        "username": "the.holistic.psychologist",
        "followers": 9072709,
        "avg_comments": 939.4,
        "website": "https://bit.ly/m/theholisticpsychologist",
        "_bio": "I teach you how to heal and consciously create a new version of yourself.",
        "category": "Clinical Psychologist",
        "products": "SelfHealers membership + books",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "hubermanlab",
        "followers": 7812078,
        "avg_comments": 866.1,
        "website": "https://www.hubermanlab.com/",
        "_bio": "Professor of Neurobiology & Ophthalmology @stanford. Neuroscience Research & Education. Host of the Huberman Lab Podcast.",
        "category": "Neuroscientist",
        "products": "Courses + podcast",
        "gender": "M",
        "country": "USA",
    },
    {
        "username": "therapyjeff",
        "followers": 1512446,
        "avg_comments": 969.0,
        "website": "https://linktr.ee/TherapyJeff",
        "_bio": "My book: Big Dating Energy. My podcast: Problem Solved.",
        "category": "Therapist",
        "products": "Book + guides",
        "gender": "M",
        "country": "USA",
    },
    {
        "username": "biglifejournal",
        "followers": 1554046,
        "avg_comments": 419.5,
        "website": "https://lnk.bio/biglifejournal",
        "_bio": "Leader in future-ready life skills. Award-winning journals & games for ages 5-99.",
        "category": "Child Development",
        "products": "Growth mindset journals + courses",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "catandnat",
        "followers": 962103,
        "avg_comments": 415.1,
        "website": "https://www.thecommonparent.com/screen-sense-ebook",
        "_bio": "BFF's with 7 Kids. Travel and making memories. Top charted podcast @catandnatunfiltered.",
        "category": "Parenting Influencer",
        "products": "Events + parenting content",
        "gender": "F",
        "country": "Canada",
    },
    {
        "username": "solidstarts",
        "followers": 4131627,
        "avg_comments": 345.1,
        "website": "https://bit.ly/welcome-solidstarts",
        "_bio": "Start solids with confidence. Baby-led weaning from pediatric pros. Award-winning app.",
        "category": "Pediatric Feeding",
        "products": "Feeding courses + app",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "drbeckyatgoodinside",
        "followers": 3479174,
        "avg_comments": 372.0,
        "website": "http://linktr.ee/drbeckyatgoodinside",
        "_bio": "Founder of @goodinside. Get 24/7 parenting support in our app. Resources for Parents of Kids Ages 0-18.",
        "category": "Clinical Psychologist",
        "products": "Good Inside membership $25/mo",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "drjulie",
        "followers": 2195271,
        "avg_comments": 465.7,
        "website": "https://linktr.ee/drjuliesmith",
        "_bio": "Clinical Psychologist | NYT Bestselling Author | 10M+ Followers. 'Open When...' & multi-million copy bestseller.",
        "category": "Clinical Psychologist",
        "products": "NYT book + digital resources",
        "gender": "F",
        "country": "UK",
    },
    {
        "username": "estherperelofficial",
        "followers": 2406794,
        "avg_comments": 451.0,
        "website": "https://stan.store/estherperel",
        "_bio": "Psychotherapist x NYT Bestselling Author. Podcast Host #WhereShouldWeBegin.",
        "category": "Psychotherapist",
        "products": "Courses + workshops",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "drericberg",
        "followers": 2663730,
        "avg_comments": 387.9,
        "website": "https://drbrg.co/3KOUrVP",
        "_bio": "Best-Selling Author. Keto, IF & Metabolic Health. 45M+ followers worldwide.",
        "category": "Functional Medicine",
        "products": "Supplements + courses",
        "gender": "M",
        "country": "USA",
    },
    {
        "username": "nedratawwab",
        "followers": 1831555,
        "avg_comments": 404.3,
        "website": "https://www.nedratawwab.com/instagram",
        "_bio": "Boundaries are the key to healthier relationships. NYT Bestselling Author, Licensed Therapist.",
        "category": "Licensed Therapist",
        "products": "Books + courses",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "takingcarababies",
        "followers": 2877485,
        "avg_comments": 301.1,
        "website": "https://www.takingcarababies.com/pages/links",
        "_bio": "Sleep classes + products to help your baby & toddler sleep tonight. Developed by Cara Dumaplin, neonatal nurse, mom of 4.",
        "category": "Pediatric Nurse",
        "products": "Sleep courses",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "drgabriellelyon",
        "followers": 1184322,
        "avg_comments": 279.3,
        "website": "https://drgabriellelyon.com/playbook/",
        "_bio": "Board-Certified Physician | 2 x NYT Bestselling Author. Forever Strong: Guide to protein, muscle & aging well.",
        "category": "Physician",
        "products": "Forever Strong book + longevity program",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "mamadoctorjones",
        "followers": 316708,
        "avg_comments": 232.1,
        "website": "",
        "_bio": "ObGyn: Periods + Pregnancy + Sex Ed. YouTuber (1.4 Million Science Lovers).",
        "category": "OB/GYN",
        "products": "Books + digital guides",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "paigelayle",
        "followers": 167411,
        "avg_comments": 123.3,
        "website": "http://paigelayle.ca/",
        "_bio": "autism & cptsd. author, keynote speaker.",
        "category": "Autism / ADHD Advocate",
        "products": "Speaking + advocacy",
        "gender": "F",
        "country": "Canada",
    },
    {
        "username": "chloeshayden",
        "followers": 382654,
        "avg_comments": 130.1,
        "website": "https://portaly.cc/Chloeshayden",
        "_bio": "If Fawn the fairy was autistic.",
        "category": "Autism Advocate",
        "products": "Books + speaking",
        "gender": "F",
        "country": "Australia",
    },
    {
        "username": "micheline.maalouf",
        "followers": 264894,
        "avg_comments": 144.4,
        "website": "https://www.michelinemaalouf.com/",
        "_bio": "Trauma therapist for Arab & diaspora. Speaker | identity healing | somatic work.",
        "category": "Trauma Therapist",
        "products": "Podcast + speaking",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "drwillcole",
        "followers": 809483,
        "avg_comments": 90.0,
        "website": "https://tap.bio/@drwillcole",
        "_bio": "health for every body: 1st online functional medicine. NYT Bestselling. ALL LINKS + Applications.",
        "category": "Functional Medicine MD",
        "products": "Books + podcast",
        "gender": "M",
        "country": "USA",
    },
    {
        "username": "thesimpleot",
        "followers": 176444,
        "avg_comments": 87.1,
        "website": "http://linktr.ee/TheSimpleOT",
        "_bio": "Sensory tools, real life, no fluff. High energy kids? Same. Making regulation make sense.",
        "category": "Pediatric OT",
        "products": "Sensory tools + digital guides",
        "gender": "F",
        "country": "USA",
    },
    {
        "username": "msrachelhollis",
        "followers": 1430079,
        "avg_comments": 62.9,
        "website": "http://msrachelhollis.com/",
        "_bio": "Writing things, chatting for a living, runnin' down a dream. 4 x NYT Bestseller.",
        "category": "Author / Speaker",
        "products": "Books + conferences",
        "gender": "F",
        "country": "USA",
    },
]


def tier_label(avg_comments: float) -> str:
    if avg_comments >= 100:
        return "Tier 1 — High Priority"
    elif avg_comments >= 30:
        return "Tier 1"
    return "Tier 2"


def build_rows() -> list[dict]:
    """Enrich emails and build rows ready for write_sheet.write_rows()."""
    rows = []
    total = len(ACCOUNTS)

    for i, acct in enumerate(ACCOUNTS, 1):
        username = acct["username"]
        print(f"\n[{i}/{total}] Enriching @{username}...")

        result = enrich_email(
            username=username,
            bio=acct.get("_bio", ""),
            website=acct.get("website", ""),
        )

        tier = tier_label(acct["avg_comments"])
        notes = (
            f"{acct['gender']} | {acct['country']} | {tier} | {acct['products']}"
        )

        rows.append({
            "username": username,
            "full_name": "",
            "category": acct["category"],
            "followers": acct["followers"],
            "avg_comments": acct["avg_comments"],
            "email": result["email"],
            "email_source": result["email_source"],
            "website": acct.get("website", ""),
            "products": acct["products"],
            "notes": notes,
        })

        if result["email"]:
            print(f"  Email: {result['email']} (via {result['email_source']})")
        else:
            print(f"  Email: not found")

    return rows


if __name__ == "__main__":
    print("=== CAIT Community — Influencer Batch Write ===")
    print(f"Accounts to process: {len(ACCOUNTS)}")
    print("Dedup check will skip @biglittlefeelings, @melrobbins, @pedsdoctalk if already in sheet.\n")

    rows = build_rows()

    print(f"\n=== Writing {len(rows)} rows to CAIT Community tab ===")
    result = write_rows(
        tab_name="CAIT Community",
        rows=rows,
        batch_size=len(ACCOUNTS),  # Write all 30 (dedup catches existing 3)
    )

    print(f"\n=== Done ===")
    print(f"Written:   {result['written']}")
    print(f"Skipped (duplicates): {result['skipped_duplicates']}")
    print(f"Errors:    {result['errors']}")
