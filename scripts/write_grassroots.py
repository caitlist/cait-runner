"""
Write grassroots Parent-Founded Community orgs to Foundations & Organizations tab.
Adds Org Type column and backfills existing rows.
"""
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os

load_dotenv()
creds = Credentials.from_service_account_file(
    os.environ.get('GOOGLE_CREDS_PATH'),
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
gc = gspread.authorize(creds)
ws = gc.open_by_key(os.environ.get('GOOGLE_SHEET_ID')).worksheet('Foundations & Organizations')

# Step 1: Add Org Type header in column L (12)
ws.update('L1', [['Org Type']])
print('Added Org Type header')

# Step 2: Backfill existing 31 rows as National/Regional Foundation
existing_count = 31
backfill = [['National/Regional Foundation']] * existing_count
ws.update(f'L2:L{existing_count + 1}', backfill)
print(f'Backfilled {existing_count} rows with National/Regional Foundation')

# Step 3: New grassroots rows
# Columns: Org Name | IG Handle | Profile Link | Website | Diagnosis Focus |
#          Followers | Email | Email Source | Exec Contact Name | Exec Contact Title | Notes | Org Type
new_rows = [
    [
        'T-Rex Little Lungs Foundation',
        '@trexlittlelungs',
        'https://www.instagram.com/trexlittlelungs/',
        '',
        'Bronchopulmonary Dysplasia (BPD)',
        '17',
        'trexlittlelungs@gmail.com',
        'IG bio',
        'Bobbi Kline',
        'Founder',
        'Mom-founded by Bobbi Kline after son Thomas spent 11 months in hospital with BPD, trach, and vent. Idaho-based. Peer support, supplies, financial help for BPD families. Already DMed by Mikha.',
        'Parent-Founded Community'
    ],
    [
        'Sisters by Heart',
        '@sistersbyheart_sbh',
        'https://www.instagram.com/sistersbyheart_sbh/',
        'sistersbyheart.org',
        'HLHS / Single Ventricle CHD',
        '4.5K',
        '',
        '',
        '',
        '',
        'All-volunteer moms of HLHS and single ventricle kids. Peer support from initial diagnosis through the Fontan and beyond. Given how you show up for heart families at every stage, your voice would mean a lot inside CAIT.',
        'Parent-Founded Community'
    ],
    [
        'Phelan-McDermid Syndrome Foundation',
        '@pmsf_official',
        'https://www.instagram.com/pmsf_official/',
        'pmsf.org',
        'Phelan-McDermid Syndrome',
        '3.7K',
        '',
        '',
        '',
        '',
        'Parent-founded for one of the rarest syndromes. Nearly one new family joins every day. Runs caregiver-to-caregiver support groups. Given the depth of support you offer, CAIT could be a natural extension of that care.',
        'Parent-Founded Community'
    ],
    [
        'Team Sanfilippo Foundation',
        '@team.sanfilippo',
        'https://www.instagram.com/team.sanfilippo/',
        'teamsanfilippo.org',
        'Sanfilippo Syndrome / MPS III',
        '',
        '',
        '',
        '',
        '',
        'Founded by parents in 2008. Research and family community for one of the most emotionally connected rare disease communities. Given how you show up for Sanfilippo families, your community would find real value in CAIT.',
        'Parent-Founded Community'
    ],
    [
        'Childhood Tracheostomy Alliance',
        '@childhoodtracheostomyalliance',
        'https://www.instagram.com/childhoodtracheostomyalliance/',
        'childhoodtrach.org',
        'Tracheostomy / Vent-Dependent',
        '497',
        '',
        '',
        '',
        '',
        'Parent and medical pro team. Runs a supply closet and caregiver grant program for vent-dependent families. Given the real operational support you provide, CAIT could sit alongside your work naturally.',
        'Parent-Founded Community'
    ],
    [
        'Moms of Trach Babies',
        '@moms_of_trach_babies',
        'https://www.instagram.com/moms_of_trach_babies/',
        '',
        'Tracheostomy / Vent-Dependent',
        '',
        '',
        '',
        '',
        '',
        'Community IG account for parents of trach children. Given how you create a space where trach parents can find others who truly understand this journey, your perspective on CAIT would be invaluable.',
        'Parent-Founded Community'
    ],
    [
        'Global Hydranencephaly Foundation',
        '@hydranencephaly',
        'https://www.instagram.com/hydranencephaly/',
        'ghflife.org',
        'Hydranencephaly',
        '',
        '',
        '',
        'Alicia Harper',
        'Founder',
        'Founded 2011 by Alicia Harper (mom of Brayden Alexander). Family-to-family support for one of the rarest brain diagnoses. Given the community you have built around the rarest of diagnoses, your insight would shape CAIT in a real way.',
        'Parent-Founded Community'
    ],
    [
        'Ollie Hinkle Heart Foundation',
        '@theohhf',
        'https://www.instagram.com/theohhf/',
        'theohhf.org',
        'CHD / Congenital Heart Disease',
        '',
        '',
        '',
        '',
        '',
        'Named after Ollie Hinkle (CHD child). Addresses unmet practical needs of heart families beyond awareness. Given how you serve heart families in the gaps that bigger orgs miss, your perspective would make CAIT better.',
        'Parent-Founded Community'
    ],
    [
        'Heart Warrior Ministries',
        '@heartwarriorministries',
        'https://www.instagram.com/heartwarriorministries/',
        'heartwarriorministries.org',
        'CHD / Congenital Heart Disease',
        '',
        '',
        '',
        '',
        '',
        'Meets CHD families at the practical, financial, emotional, and spiritual level. Community-led, not institutional. Given the depth of how you show up for heart families, your voice belongs in a space like CAIT.',
        'Parent-Founded Community'
    ],
    [
        "Holton's Heroes",
        '@holtonsheroes',
        'https://www.instagram.com/holtonsheroes/',
        'holtonsheroes.org',
        'Pediatric Brain Injury (acquired)',
        '',
        '',
        '',
        'Eric & Angela Weingrad',
        'Co-Founders',
        'Founded by Eric and Angela Weingrad to connect post-birth brain injury kids with therapy tools families could not otherwise access. Given how you close the gap between hospital discharge and real recovery, CAIT would be a natural fit.',
        'Parent-Founded Community'
    ],
    [
        'ARFID Awareness',
        '@arfidawarenessnonprofit',
        'https://www.instagram.com/arfidawarenessnonprofit/',
        'arfidawareness.org',
        'ARFID / Pediatric Feeding Disorder',
        '',
        '',
        '',
        'Michelle Dorit',
        'Founder',
        'Mom-founded 2024 by Michelle (mother of Hannah, ARFID). Partnered with Feeding Matters. Given how personally you have lived this journey and turned it into advocacy, your perspective would shape CAIT in a real way.',
        'Parent-Founded Community'
    ],
    [
        'Tubie Friends',
        '@tubiefriends',
        'https://www.instagram.com/tubiefriends/',
        'tubiefriends.com',
        'Feeding Tube / G-tube',
        '2.8K',
        '',
        '',
        '',
        '',
        'Founded by moms of tube-fed children. Makes stuffed animals with feeding tubes to normalize the experience for kids. Given the intimacy of the community you have built around feeding tube families, CAIT would be a meaningful extension of your support.',
        'Parent-Founded Community'
    ],
    [
        'CPATH Texas',
        '@cpathtexas',
        'https://www.instagram.com/cpathtexas/',
        'cpathtexas.org',
        'Cerebral Palsy',
        '',
        '',
        '',
        '',
        '',
        'Grassroots CP nonprofit in Austin TX. Grants, medical equipment, weekend family camps, adaptive sports. Community-first model. Given how you serve CP families in Texas beyond what bigger orgs reach, your insight would make CAIT better.',
        'Parent-Founded Community'
    ],
]

# Append rows
for i, row in enumerate(new_rows):
    ws.append_row(row, value_input_option='USER_ENTERED')
    print(f'  Written row {existing_count + 2 + i}: {row[0]}')

print(f'\nDone. {len(new_rows)} new grassroots rows added.')
print(f'Total rows now: {existing_count + len(new_rows)}')
