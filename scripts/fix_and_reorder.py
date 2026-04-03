"""
fix_and_reorder.py
------------------
Step 1: Clear wrong comments from VIP rows 2-19 (they got comments intended for other accounts)
Step 2: Write correct comments to the correct rows (looked up by handle)
Step 3: Reorder the sheet so all 'To Send - 2026-03-24' rows are together at top
         (VIPs rows 2-19 stay, remaining To Send rows move to rows 20+)
         Uses moveDimension to preserve cell formatting/colors.
"""
import os, gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
load_dotenv()

creds = Credentials.from_service_account_file(
    os.environ['GOOGLE_CREDS_PATH'],
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(os.environ['GOOGLE_SHEET_ID'])
ws = spreadsheet.worksheet('Medical Mom DM Outreach')
sheet_id = ws.id

# ── Step 1 & 2: Fix comments ──────────────────────────────────────────────────

print("Reading sheet...")
all_values = ws.get_all_values()
headers = [h.strip() for h in all_values[0]]
col = {h: i for i, h in enumerate(headers)}
handle_idx = col['Handle']
gen_comment_col = col['Generated Comment'] + 1  # 1-based for gspread Cell

# Correct comments keyed by handle (lowercase, no @)
# Emojis: matched to post type not just hearts
correct_comments = {
    'townekids': 'Finding a team that families can actually trust with their child\'s care is everything. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f9e1',
    'unchainedsouldesignsllc': 'Sunshine, fresh air, and laughter on a heavy day, holding onto that kind of moment a little tighter makes all the sense in the world. We left you a little something in your DMs, would love for you to take a peek when life slows down for a second. \U0001f90d',
    'thelittlest3': 'Going through a gallbladder removal, an MRI, a liver specialist, and a colonoscopy all while still wanting to donate a kidney for Ro. Caleb\'s commitment to your family is something else entirely. We sent you a little something in your DMs that we think you will love. \U0001f9e1',
    'chdinvisiblewarriors': 'Just laughter, sunshine, and a little girl being exactly who she\'s meant to be, that kind of day is what the whole journey is for. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f49b',
    'mommyschronicles': 'A gorgeous day, lots accomplished, and a full heart, the kind of Saturday that makes you exhale a little. We slid into your DMs with a little something, take a peek when you get a moment! \u2728',
    'georges_happy_hearts_project_': 'George graduating from the CVICU on his due date two years ago today, that timing is almost too meaningful to put into words. Watching him go from that moment to pure joy and full of life says everything. When you have a moment, we\'d love for you to check your DMs, we\'ve sent something your way! \U0001f499',
    'a__schiro': 'Brooklyn\'s first soccer practice with tears halfway through and still having so much fun, that is such a real and perfect first day. Rooting for her from wherever you are right now. We slid into your DMs with something we think you\'ll love, take a peek when Brooklyn\'s settled in for the night! \u26bd',
    'brookeslick': 'Soccer season solidarity, you are not alone in this. We slid into your DMs with a little something, take a peek when you get a second! \U0001f62d',
    'jillybeansewing': 'All those pieces finally coming together in the layout, that step where the work starts becoming something real is the best part of the whole process. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f9f5',
    'stellaraeofsunshine': 'Sonny at one year, already giving out smiles for free and making everyone\'s day a little brighter, that kind of sunshine is everything. Happy birthday to him. We sent you a little something in your DMs that we think you will love. \u2600\ufe0f',
    'iramshasiddique': 'Sleepless nights, silent prayers, and endless hard work showing up in one result, watching someone you love prove that kind of strength is genuinely one of the best feelings. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f90d',
    'blakelybrave': 'Healing being two things at once, feeling grateful and still scared, stronger and still changed, that is the most honest way anyone has described what this journey does to a family. We would love to chat when you have some time, we sent you something we think could help. \U0001f49b',
    'bravemumtribe': 'Doing an NGT flush one-handed while making breakfast and not even noticing, "adjusted doesn\'t mean okay, just means your nervous system found a way to function in abnormal" is one of the most real things written about this life. We left you a little something in your DMs, would love for you to take a peek when life slows down for a second. \U0001f9e1',
    'yeomansleejenny': 'That excitement when the most-wanted fragrance finally lands and orders are already flying, if it sells out this fast every time you know it is worth the wait. We slid into your DMs with a little something, take a peek when you get a moment! \u2728',
    'megsalshouse': 'Daniela officially in the family now, welcome is an understatement when the love is already this obvious. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f90d',
    'solson1120': '5am being announced that loudly, the birds and the worm have nothing on this kind of alarm clock. We slid into your DMs with a little something, take a peek when you get a second! \U0001f605',
    '_e.doni': 'A year of HYROX and marathons coming back in one recap, from almost breaking 60 in Dallas to pacing Alan through his first marathon, the memories built in those races go so much further than any medal. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f3c3',
    'hollyjoflora': 'Faith showing up in the middle of the collapse and not after the dust settles, that is the kind of honest that makes people feel less alone in their own breaking points. We just sent you a DM, we really love the kind of stories you share. Would mean the world if you had a moment to take a look. \U0001f90d',
    'joc_bostwick': '30 weeks and finding the small things that actually help, the yoga ball and pillow support doing more work than anyone in the first trimester prepares you for. We sent you a little something in your DMs when you get a chance. \U0001f33c',
    'brianawglover': 'Being intentional with how you show up changes everything, even on the quietest days. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f49c',
    'testa_seat': 'One day apart, one seating change, the difference in alignment and how much easier eating became almost immediately is exactly the kind of progress families need to see to believe it. We sent you a little something in your DMs that we think you will love. \U0001f64c',
    'cpfamily.mauritius': 'The distinction between the condition itself not progressing and what happens without the right support, that clarity matters so much for families who are still figuring out what comes next. We would love to chat when you have some time, we sent you something we think could help. \U0001f9e1',
    'make_lemon_aide_for_cp': 'Getting in at the lowest rate for the Buffalo CP event before April 1, if this community shows up the way it does it is going to be a strong one. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f34b',
    'oscarscptherealguide': 'Acting as physio, OT, SALT, dysphagia support, dietician, and team leader all at once just to give Oscar the same chances, that weight is real and it is not just a you thing. We would love to chat when you have some time, we sent you something we think could help. \U0001f9e1',
    'kindship_au': 'Finding the right therapist when you are navigating all of this is genuinely life-changing, the kind of resource you never take for granted once you have it. We sent you a little something in your DMs that we think you will love. \U0001f49a',
    'reality.of.an.ivf.family': '9 months old and not in the mood for photos while still fighting through being sick, honestly completely fair. Getting to be such a big boy comparatively says everything about how far he has come. We slid into your DMs with something we think you\'ll love, take a peek when he\'s settled in! \U0001f331',
    'grahamsfoundation': 'Wells at 25 weeks, 1 lb 3 oz, 101 days fighting, and now 8 months old, grabbing, reaching, playing, smiling and lighting up every room. That update fills your whole heart. When you have a moment, we\'d love for you to check your DMs, we\'ve sent something your way! \U0001f499',
    'mrs.aieshariley': 'Spring nails done right, that kind of fresh set is the self-care that counts. We slid into your DMs with a little something, take a peek when you get a second! \U0001f338',
    'perfectlypreemie': 'NICU gowns sized from Micro to Preemie, designed so care teams can do their job while keeping the tiniest ones comfortable, the thoughtfulness behind that says this was built by someone who actually understands what those families are going through. We sent you a little something in your DMs that we think you will love. \U0001f476',
    'mykidsinspiration': 'A keepsake page built to hold the gestation, the weight, the early NICU days, having a gentle place to preserve both the facts and the feelings of those first days is the kind of thing families will come back to for years. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f4d6',
    'canadianpreemies': 'The drop-off in support after NICU discharge is so real and so rarely talked about, 40% of mothers struggling with depression, 30% with PTSD, and families often navigating it alone once the initial wave fades. Peer support groups filling that gap matter so much. We would love to chat when you have some time, we sent you something we think could help. \U0001f499',
    'tinkstonic': 'A spring blend that hits a full macros breakdown and still uses real whole food ingredients, beef powder, sweet potato, beet, and peach all going into one clean mix for tube-fed kids. We sent you a little something in your DMs that we think you will love. \U0001f955',
    'wholestorymeals': 'All nine essential amino acids, iron, magnesium, zinc, fiber, and B vitamins from one tiny seed most people walk right past in the grocery store, and naturally gluten-free on top of it. No fluff, no filler is exactly right. We sent you a little something in your DMs that we think you will love. \U0001f33f',
    'griffsgotgrit': 'If it touched the mouth it counts, that is the official law of feeding therapy and no one can argue with it. Rooting so hard for Griff. We slid into your DMs with something we think you\'ll love, take a peek when Griff\'s done with today! \U0001f64c',
    'justenoughmanna': 'The quiet grief that lives alongside chosen love, not regretting a single moment and still carrying what you did not get to have, both things being true at the same time and that deserves to be said. We would love to chat when you have some time, we sent you something we think could help. \U0001f90d',
    'freearm.tube.feeding.assistant': 'Breakfast with friends and a tubie in the wild, these moments of just living life are the whole point. We slid into your DMs with a little something, take a peek when you get a second! \U0001f37b',
    'whitney_raye': 'Easter cookie pre-sale with personalized bunny options and pickup right before the weekend, the kind of local find that goes fast. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f430',
    'blendedtubefeeding': 'A cap that cuts the mess from syringe feeding blended food, made from food safe plastic and built by someone in the tube feeding community, the fact that @3dtubiedad made this is everything. We sent you a little something in your DMs that we think you will love. \U0001f44f',
    'aaronandambersfamily': 'AJ handing out stickers and buttons to familiar faces while being fully committed to protesting nail trims, even with all the pieces still being dialed in those dance parties are clearly non-negotiable. We left you a little something in your DMs, would love for you to take a peek when AJ\'s settled in for the night. \U0001f49b',
    'the_chd_life_': 'Not a fairytale but a testimony, those are two very different things and the testimony hits harder every time. We actually sent you a message, would love for you to take a peek when you get a chance. \u2764\ufe0f',
    'oliver_chdbaby': 'A smiley face balloon arriving on the ward after the Fontan, those little things that break up the long hospital days matter more than anyone on the outside can really understand. We sent you a little something in your DMs that we think you will love. \U0001f388',
}

# Step 1: Clear VIP rows 2-19 of any wrong comments
print("Clearing VIP rows 2-19 of any wrong comments...")
clear_cells = [gspread.Cell(r, gen_comment_col, '') for r in range(2, 20)]
ws.update_cells(clear_cells, value_input_option='USER_ENTERED')

# Step 2: Find each handle's actual current row and write correct comment
print("Writing correct comments by handle lookup...")
write_cells = []
found_handles = set()
for row_num, row in enumerate(all_values[1:], start=2):
    h = row[handle_idx].strip().lstrip('@').lower() if handle_idx < len(row) else ''
    if h in correct_comments and h not in found_handles:
        write_cells.append(gspread.Cell(row_num, gen_comment_col, correct_comments[h]))
        found_handles.add(h)

ws.update_cells(write_cells, value_input_option='USER_ENTERED')
print(f"  Written comments for {len(write_cells)} accounts")
missing = set(correct_comments.keys()) - found_handles
if missing:
    print(f"  NOT FOUND in sheet: {missing}")

# ── Step 3: Reorder sheet ─────────────────────────────────────────────────────

print("\nReading sheet for reorder...")
all_values = ws.get_all_values()  # refresh after writes
status_idx = col['DM Status']

TARGET_STATUS = 'To Send - 2026-03-24'
VIP_ROWS = set(range(2, 20))  # rows 2-19 are VIPs, stay in place

# Find all non-VIP To Send rows, in current order
to_send_rows = []
for row_num, row in enumerate(all_values[1:], start=2):
    if row_num in VIP_ROWS:
        continue
    status = row[status_idx].strip() if status_idx < len(row) else ''
    if status == TARGET_STATUS:
        to_send_rows.append(row_num)

print(f"Found {len(to_send_rows)} non-VIP To Send rows to move to top")
print(f"First few: {to_send_rows[:10]}")

# Build moveDimension requests
# Target positions: 20, 21, 22, ... (right after VIPs at rows 2-19)
# Process in ASCENDING order — remaining rows are unaffected by each move
# (because when moving row S to row D where S > D, rows > S are unchanged)
requests = []
target = 20  # 1-based target row for next To Send account
for source in to_send_rows:
    if source == target:
        target += 1
        continue  # already in the right place
    # moveDimension: source row moves to target position
    # 0-based: source_idx = source - 1, dest_idx = target - 1
    requests.append({
        "moveDimension": {
            "source": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": source - 1,   # 0-based inclusive
                "endIndex": source           # 0-based exclusive
            },
            "destinationIndex": target - 1  # 0-based insertion point
        }
    })
    target += 1

if requests:
    print(f"Sending {len(requests)} moveDimension requests...")
    spreadsheet.batch_update({"requests": requests})
    print("Sheet reordered!")
else:
    print("Sheet already in correct order, no moves needed.")

print("\nDone! All To Send accounts are now together at the top.")
print("VIPs: rows 2-19")
print(f"Other To Send accounts: rows 20-{19 + len(to_send_rows)}")
