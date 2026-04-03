"""
seed_facebook_groups.py
-----------------------
One-time seed script: writes 25 USA + 25 Philippines Facebook groups to the sheet.

USA Autism groups → "US autism Facebook Group Communities"
USA Medical groups → "US Facebook Medical Moms"
Philippines groups → "Philippines Facebook Groups" (new tab, auto-created)

Member counts marked "Verify on FB" where not publicly available from web search.

Usage:
    python scripts/seed_facebook_groups.py
"""

import sys
import os

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.write_sheet import write_rows

# ------------------------------------------------------------------
# USA — Autism (→ "US autism Facebook Group Communities")
# ------------------------------------------------------------------
USA_AUTISM = [
    {
        "community_name": "Autism Parents Support Group",
        "group_link": "https://www.facebook.com/groups/autismparenting/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Autism Parents Support & Discussion Group",
        "group_link": "https://www.facebook.com/groups/AutismParentsSupport/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Autism & Special Needs Parents Support Group",
        "group_link": "https://www.facebook.com/groups/autismparentsupportgroup/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Texas Autism Moms and Dads",
        "group_link": "https://www.facebook.com/groups/885526781555294/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "DFW Autism Parents",
        "group_link": "https://www.facebook.com/groups/dfwasg/",
        "num_members": "Verify on FB",
        "admin": "",
    },
]

# ------------------------------------------------------------------
# USA — Medical Moms / All Other Categories (→ "US Facebook Medical Moms")
# ------------------------------------------------------------------
USA_MEDICAL = [
    # Medical Moms / Medically Complex
    {
        "community_name": "Mommies of Miracles",
        "group_link": "https://www.facebook.com/groups/momsofmiracles/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    # Trach
    {
        "community_name": "Moms of Trach Babies",
        "group_link": "https://www.facebook.com/groups/momsoftrachbabies/",
        "num_members": "10,000+",
        "admin": "",
    },
    {
        "community_name": "Trach Mommies, Trach Babies & Trach Buddies!",
        "group_link": "https://www.facebook.com/groups/alltrachs/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Trach Kids with Down Syndrome",
        "group_link": "https://www.facebook.com/groups/588993674507259/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    # Epilepsy
    {
        "community_name": "Parents of Kids with Epilepsy and Seizures",
        "group_link": "https://www.facebook.com/groups/761944090544935/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Parents of Children with Epilepsy Support Group",
        "group_link": "https://www.facebook.com/groups/248750660510954/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    # Type 1 Diabetes
    {
        "community_name": "Parents of Children with Type 1 Diabetes",
        "group_link": "https://www.facebook.com/groups/104811746342626/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Parents of Type 1 Diabetics — U.S. Only",
        "group_link": "https://www.facebook.com/groups/2626141222/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    # Down Syndrome
    {
        "community_name": "Parents of Children with Down Syndrome",
        "group_link": "https://www.facebook.com/groups/132540303533527/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Down Syndrome Mommies",
        "group_link": "https://www.facebook.com/groups/downsyndromemommies/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    # Cerebral Palsy
    {
        "community_name": "Cerebral Palsy Parents Information Group",
        "group_link": "https://www.facebook.com/groups/CerebralPalsyInfo/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Mild Cerebral Palsy Parent Support Group",
        "group_link": "https://www.facebook.com/groups/mildcerebralpalsyparentsupportgroup/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    # NICU / Preemie
    {
        "community_name": "Empowering NICU Parents",
        "group_link": "https://www.facebook.com/groups/empoweringnicuparents/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Preemie & NICU Parents Support",
        "group_link": "https://www.facebook.com/groups/681978663653488/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    # Pediatric Cancer
    {
        "community_name": "Childhood Cancer Support Group (NCCS)",
        "group_link": "https://www.facebook.com/groups/childhoodcancersupportnccs/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    # Cystic Fibrosis
    {
        "community_name": "Cystic Fibrosis Community Group",
        "group_link": "https://www.facebook.com/groups/cysticfibrosisgroup/",
        "num_members": "27,000",
        "admin": "",
    },
    {
        "community_name": "Cystic Fibrosis Parents — Babies Newly Diagnosed",
        "group_link": "https://www.facebook.com/groups/213837325977225/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    # Rare Diseases
    {
        "community_name": "Rett Syndrome Family Support Forum",
        "group_link": "https://www.facebook.com/groups/250235058326930/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Angelman Syndrome Support",
        "group_link": "https://www.facebook.com/groups/348430718665860/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Trisomy Families",
        "group_link": "https://www.facebook.com/groups/trisomyfamilies/",
        "num_members": "Verify on FB",
        "admin": "",
    },
]

# ------------------------------------------------------------------
# Philippines — All categories (→ "Philippines Facebook Groups")
# NOTE: Many PH entries are Facebook Pages (not Groups).
# Member counts from page likes where group count not available.
# ------------------------------------------------------------------
PHILIPPINES = [
    # Autism
    {
        "community_name": "Autism Parents Support Group Philippines",
        "group_link": "https://www.facebook.com/groups/autismparentssupportgroupphilippines/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Autism Fam PH",
        "group_link": "https://www.facebook.com/groups/autismfamph/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Filipino Autism Parents",
        "group_link": "https://www.facebook.com/groups/FilipinoAutismParents/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Autism Society Philippines",
        "group_link": "https://www.facebook.com/autismsocietyphilippines/",
        "num_members": "91,000 (page likes)",
        "admin": "",
    },
    {
        "community_name": "Autism Partnership Manila",
        "group_link": "https://www.facebook.com/AP.Philippines/",
        "num_members": "23,000 (page likes)",
        "admin": "",
    },
    {
        "community_name": "Autism Special Education Philippines",
        "group_link": "https://www.facebook.com/AutismSpecialEducation/",
        "num_members": "15,206 (page likes)",
        "admin": "",
    },
    {
        "community_name": "Autism Pilipinas Support Group",
        "group_link": "https://www.facebook.com/APSG2021/",
        "num_members": "8,255 (page likes)",
        "admin": "",
    },
    {
        "community_name": "Autism Mommy Ph",
        "group_link": "https://www.facebook.com/autismparentguide/",
        "num_members": "3,148 (page likes)",
        "admin": "",
    },
    {
        "community_name": "ASP Davao Chapter",
        "group_link": "https://www.facebook.com/aspdavaochapter/",
        "num_members": "1,587 (page likes)",
        "admin": "",
    },
    # Down Syndrome
    {
        "community_name": "Down Syndrome Association of the Philippines",
        "group_link": "https://www.facebook.com/groups/53343128860/",
        "num_members": "20,326 (org page likes)",
        "admin": "",
    },
    # ADHD
    {
        "community_name": "ADHD Society of the Philippines",
        "group_link": "https://www.facebook.com/ADHDSOCPHILS/",
        "num_members": "38,868 (page likes)",
        "admin": "",
    },
    {
        "community_name": "ADHD Support Group Philippines",
        "group_link": "https://www.facebook.com/p/ADHD-Support-Group-Philippines-100063483804001/",
        "num_members": "4,359 (page likes)",
        "admin": "",
    },
    # Cerebral Palsy / Epilepsy
    {
        "community_name": "Cerebral Palsy Epilepsy Family Awareness Support Group PH",
        "group_link": "https://www.facebook.com/CEFASG.PH/",
        "num_members": "2,369 (page likes)",
        "admin": "",
    },
    {
        "community_name": "Cerebral Palsied Association of the Philippines",
        "group_link": "https://www.facebook.com/cpap.inc/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    # Epilepsy
    {
        "community_name": "Epilepsy Friends Philippines",
        "group_link": "https://www.facebook.com/groups/1097655150380232/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    # Rare Disease
    {
        "community_name": "Philippine Society for Orphan Disorders (PSOD)",
        "group_link": "https://www.facebook.com/PSODCareForRare/",
        "num_members": "4,479 (page likes)",
        "admin": "",
    },
    # NICU / Preemie / Medically Complex
    {
        "community_name": "Premature Babies of Philippines",
        "group_link": "https://www.facebook.com/groups/789961306254426/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Premature Birth Philippines Support Group",
        "group_link": "https://www.facebook.com/groups/prematurebirthphilippines/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    # Heart / Medically Complex
    {
        "community_name": "Let it ECHO — CHD Philippines",
        "group_link": "https://www.facebook.com/LetItECHO/",
        "num_members": "6,536 (page likes)",
        "admin": "",
    },
    # Special Needs / General
    {
        "community_name": "Special Children Philippines",
        "group_link": "https://www.facebook.com/SpecialChildrenPhilippines/",
        "num_members": "825 (page likes)",
        "admin": "",
    },
    {
        "community_name": "Children With Disabilities Foundation Philippines",
        "group_link": "https://www.facebook.com/CWDphilippines/",
        "num_members": "1,234 (page likes)",
        "admin": "",
    },
    {
        "community_name": "League of Parents of the Philippines",
        "group_link": "https://www.facebook.com/groups/1631332743666866/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Special Needs Parents Support & Discussion Group PH",
        "group_link": "https://www.facebook.com/groups/1855573214536750/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "CPMS Parent Support Group Philippines",
        "group_link": "https://www.facebook.com/cpms.parentsupportgroup/",
        "num_members": "Verify on FB",
        "admin": "",
    },
    {
        "community_name": "Autism Strong Project PH",
        "group_link": "https://www.facebook.com/AutismStrongProjectPH/",
        "num_members": "275 (page likes)",
        "admin": "",
    },
]


def main():
    print("=" * 60)
    print("CAIT Facebook Groups Seed Script")
    print("USA Autism: 5 groups -> 'US autism Facebook Group Communities'")
    print("USA Medical: 20 groups -> 'US Facebook Medical Moms'")
    print("Philippines: 25 groups -> 'Philippines Facebook Groups'")
    print("=" * 60)

    # --- USA Autism ---
    print("\n[1/3] Writing USA Autism groups...")
    result_autism = write_rows(
        tab_name="US autism Facebook Group Communities",
        rows=USA_AUTISM,
        batch_size=25,
    )

    # --- USA Medical Moms ---
    print("\n[2/3] Writing USA Medical Moms groups...")
    result_medical = write_rows(
        tab_name="US Facebook Medical Moms",
        rows=USA_MEDICAL,
        batch_size=25,
    )

    # --- Philippines ---
    print("\n[3/3] Writing Philippines groups...")
    result_ph = write_rows(
        tab_name="Philippines Facebook Groups",
        rows=PHILIPPINES,
        batch_size=25,
    )

    print("\n" + "=" * 60)
    print("SEED COMPLETE")
    print(f"  USA Autism:    {result_autism['written']} written, {result_autism['skipped_duplicates']} dupes")
    print(f"  USA Medical:   {result_medical['written']} written, {result_medical['skipped_duplicates']} dupes")
    print(f"  Philippines:   {result_ph['written']} written, {result_ph['skipped_duplicates']} dupes")
    total = result_autism['written'] + result_medical['written'] + result_ph['written']
    print(f"  TOTAL WRITTEN: {total}")
    print("=" * 60)


if __name__ == "__main__":
    main()
