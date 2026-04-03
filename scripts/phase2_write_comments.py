"""
phase2_write_comments.py
------------------------
Writes all Phase 2 generated comments to the Google Sheet.
Keyed by row number. Runs once, writes Generated Comment and Notes columns.
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

print("Reading sheet headers...")
all_values = ws.get_all_values()
headers = [h.strip() for h in all_values[0]]
col = {h: i for i, h in enumerate(headers)}
print(f"Headers found: {list(col.keys())}")

gen_comment_col = col['Generated Comment'] + 1
notes_col = col['Notes'] + 1

# ── Comments by row number ─────────────────────────────────────────────────
# SENSITIVE flagged where needed. SKIP = no comment written.

comments = {
    # VIPs rows 2-19
    2: 'The way kids don\'t even know what autistic means, just that it sounds like an insult, is exactly the problem this kind of education is meant to fix. Teaching that autism isn\'t a punchline but a real way of experiencing the world is such a powerful thing to build early. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f4d6',
    3: 'The families behind these hashtags are real and the weight of severe autism is something the mainstream conversation rarely captures. We left you a little something in your DMs whenever you get a moment. \U0001f499',
    4: 'Leo and Lulu turning out to be cousins from the same breeder after she spotted the video online is the kind of story that feels made up but isn\'t. Getting to grow up together as family is everything. We slid into your DMs with a little something, take a peek when you get a second! \U0001f43e',
    5: 'After 14 years of relying on others to tell you about his day, now having Tommy text you himself, posting the Goofy GIF he found funny and then asking if you like Goofy too, that kind of personality coming through in a message fills your whole heart. We actually sent you a message, would love for you to take a peek when you get a chance. \u2764\ufe0f',
    6: 'Teaching a cat to do tricks and then getting surprise jump attacks as the bonus deal you did not sign up for is the most honest cat ownership experience. We slid into your DMs with a little something, take a peek when you get a second! \U0001f431',
    7: 'Building her room around what actually matters, safe, comfortable, joyful, deeply loved, instead of chasing what milestones should look like, that is exactly the kind of love that says everything without needing to explain itself. We left you a little something in your DMs, would love for you to take a peek when life slows down for a second. \U0001f49d',
    8: 'Happy World Down Syndrome Day to Millie girl. Praying alongside you that we all learn to see people with fresh eyes and love them exactly as they are. We slid into your DMs with something we think you\'ll love, take a peek when Millie\'s settled in! \U0001f33c',
    9: 'Happy World Down Syndrome Day to Huddy and Melanie. That kind of love is something else entirely. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f49b\U0001f49b',
    10: 'Dreaming of mornings like this when your family was divided during Luca\'s treatment, and now waking up under one roof every single day with everyone heading off together, the gratitude in that is real and earned. We sent you a little something in your DMs that we think you will love. \u2728',
    11: 'Whatever that reaction was to, that energy and that community\'s ability to celebrate together says everything. We slid into your DMs with something we think you\'ll love, take a peek when the celebration settles! \U0001f308',
    12: 'Ozzy Jo\'s friends and teachers who treat her equal to her peers without hesitation are exactly the village that makes the whole journey feel lighter. The message that differences are worth celebrating, not working around, is one more families need to hear. We left you a little something in your DMs, would love for you to take a peek when you get a moment. \U0001f49b\U0001f49b',
    13: 'Not creating a world that is easier for Bedford but building environments where he can add value by actually being with everyone else, that distinction matters more than most people realize. Running that race with a little red walker right next to you is something else entirely. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f9e1',
    14: 'Charlie serving #CharlieScowl at her own tea party at ten years old is the most her thing imaginable and you would not change a single thing. Being trusted with such a radiant spirit is the right way to describe it. We sent you a little something in your DMs that we think you will love. \U0001f370',
    15: 'Ollie growing up so quickly, that proud mix of joy and a little ache in your chest at the same time is something only a heart warrior mama really understands. We slid into your DMs with a little something, take a peek when he\'s settled in! \u2764\ufe0f',
    16: 'That g-tube smile saying everything it needs to, a little reminder to find the joy where you can on any given day, is exactly what some people needed to land on this morning. We left you a little something in your DMs, take a peek when you get a moment! \U0001f49b',
    17: 'Rare diseases affecting millions of families while still feeling invisible to most of the world, Sanfilippo Syndrome being one of the ones that needs the most awareness and understanding, is exactly why accounts like this one matter. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f49c',
    18: 'The best birthday party ever for Cam, the kind of day that deserves all the posts it takes to capture it right. We sent you a little something in your DMs that we think you will love. \U0001f389',
    19: '[SENSITIVE \u2014 review before pasting] Brielle waiting until you stepped away from her bedside says something about the kind of love that is too big to put into words. Carrying you with us. We left you something in your DMs whenever you come up for air. \U0001f90d',

    # Non-VIP accounts needing comments
    30: 'Building a solution from real conversations with the epilepsy community, turning shared experiences into something that actually protects what protects them when every second matters, that kind of gratitude-driven design says everything about why it works. We sent you a little something in your DMs that we think you will love. \U0001f49c',
    31: 'A heart monitor for 7 days while also navigating W\'s very specific feelings about anything that shouldn\'t be there, the plaster anecdote making that very clear, those quiet logistical puzzles on top of everything else. Wishing you a genuinely restful 10 days. We left you something in your DMs whenever you come up for air. \U0001f49b',
    33: 'Looking for moments to pause during years of caregiving, a quiet dinner with your son or walking the hospital hallway with music playing, those small things keeping you steady inside controlled chaos is such a meaningful way to look at what actually gets people through. We sent you a little something in your DMs that we think you will love. \U0001f40e',
    35: 'Building seizure, medication, and trigger tracking tools from inside the epilepsy journey, using professional knowledge to fill a gap you personally lived, is the kind of resource families will genuinely use rather than set aside. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f49c',
    36: '[SENSITIVE \u2014 review before pasting] Holding gratitude and heartbreak in the same place, asking why us but not them, refusing to talk about faith and miracles in a way that erases the families who prayed just as hard and still had to say goodbye, that is the most honest version of this story anyone has written. We would love to chat when you have some time, we sent you something we think could help. \U0001f90d',
    39: '[SENSITIVE \u2014 review before pasting] "For the parents whose arms are empty but whose love still fills every corner of the world" is going to stay with a lot of people who needed to feel carried today. Every heartbeat, every flicker of hope is right. We left you something in your DMs whenever you come up for air. \U0001f90d',
    40: 'A therapy specifically addressing fear of cancer recurrence in parents of survivors, filling a gap that is so rarely acknowledged publicly, is the kind of study that reaches families who have been waiting for someone to name what they are carrying. We sent you a little something in your DMs that we think you will love. \U0001f397\ufe0f',
    42: 'Thankful for the good days and a little warrior who keeps showing up, that kind of gratitude hits differently when you know exactly what the hard ones feel like. We slid into your DMs with something we think you\'ll love, take a peek when you get a moment! \U0001f9e1',
    # 44 nansel2966 = SKIP
    49: 'You, him, and Mickey against the world, Theodore Jacob\'s face in that photo says everything it needs to. We sent you a little something in your DMs that we think you will love. \U0001f3f0',
    51: 'The conversations that continue long after the work ends and the trust that builds year after year with the families ABR reaches, what happens in Toledo genuinely doesn\'t stay in Toledo. We would love to chat when you have some time, we sent you something we think could help. \U0001f331',
    53: 'Henry graduating from badgering his parents to commanding his very own in-home lift is the arc of a true king and no one can argue with his logic. We sent you a little something in your DMs that we think you will love. \U0001f451',
    54: 'Getting in before the March 31 deadline for $5 off each Laps of Love registration, Buffalo showing up for CP awareness month the way it always does. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f34b',
    58: '[SENSITIVE \u2014 review before pasting] 100+ prematurity topics, suggested questions for the care team, preemie-specific growth charts, and a journal for milestones and feelings all in one place, the MyPreemie app being built so families feel more prepared for every conversation along the way is exactly the kind of support that should exist from day one. When you have a moment, we\'d love for you to check your DMs, we\'ve sent something your way. \U0001f49c',
    60: 'Every time you say yes with your own timeline attached and God answers faster, Christmas break to Autumn in under two days, and now a new placement two weeks in and going smoother than you could have imagined, the pattern is becoming hard to argue with. We slid into your DMs with something we think you\'ll love, take a peek when the new family routine settles! \U0001f338',
    61: '[SENSITIVE \u2014 review before pasting] Socks designed for the smallest feet that actually stay on and actually fit, the kind of detail that says someone who has been in that NICU room thought about every single piece of this. We sent you a little something in your DMs that we think you will love. \U0001f476',
    63: '[SENSITIVE \u2014 review before pasting] Adults who were once born very prematurely looking back on their lives and what matters now, hearing from the ones who started so small that there is a whole beautiful journey beyond the NICU, that is the kind of perspective preemie families need to hold onto. We would love to chat when you have some time, we sent you something we think could help. \U0001f499',
    65: 'The tube feeding community noticing and sharing with each other is how the resources that actually help reach the families who need them most. We left you a little something in your DMs, take a peek when you get a moment! \U0001f331',
    67: 'Two kids who should never have had to leave the warmth of their own mothers, and now getting to grow and learn and have moments together with a shared experience that connects them, watching that connection matter in the middle of something so hard says everything. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f90d',
    68: 'FreeArm and Medical Mama Bear teaming up to pair hands-free feeding support with pump stickers that add personality and joy to the equipment is exactly the kind of collab the tubie community needed. We sent you a little something in your DMs that we think you will love. \U0001f44f',
    69: 'Easter presale live with limited orders and the holiday weekend coming fast, if you blink on this one you will miss it. We slid into your DMs with a little something, take a peek when you get a second! \U0001f430',
    72: 'Still on a retreat high and already counting down to camp is the best kind of problem to have, and those Thieu Nhi 3 kids showing up together like that says everything about what this community builds. We slid into your DMs with something we think you\'ll love, take a peek when the retreat energy settles! \U0001f31f',
    73: 'Bass Pro Shops pyramid as a consolation prize for the Memphis zoo washed out by thunderstorms, Christmas music through the RV while the pups settle in, that is exactly the right kind of adventure for a CHD family who knows how to find the good in every stop. We sent you a little something in your DMs that we think you will love. \u2764\ufe0f',
    74: 'Boycotting halftime shows in favor of your kids making their own is genuinely the best new family tradition anyone has proposed and the video cannot arrive fast enough. We slid into your DMs with a little something, take a peek when the show is over! \U0001f38a',
    75: 'The ongoing check-ins, the way getting sick hits harder, the quiet fears that never fully leave, those are the parts of CHD that people on the outside rarely see. The faith meeting you in those unseen moments, not just after the dust settles, is the part that makes the difference. We actually sent you a message, would love for you to take a peek when you get a chance. \u2764\ufe0f',
    76: 'A twin flame friendship that understands you like no one else and is just down for whatever is the kind you do not come across often. We slid into your DMs with a little something, take a peek when the celebration winds down! \U0001f91f',
    78: 'Closing spring break with food, community, and genuine care for families in recovery, making sure everyone can take part and enjoy time together at the park, that is what real community support looks like in action. We left you a little something in your DMs, take a peek when the event wraps! \U0001f91f',
    79: 'Speech therapy working on tongue movement, swallowing reflex timing, and breath-suck-swallow coordination all in one session, each small piece clicking into place for António is real measurable progress. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f499',
    80: 'Ending the season second overall with five brand new teammates and going 3-1, the pride behind that is something else entirely. We sent you a little something in your DMs that we think you will love. \U0001f94b',
    81: 'Walking into the state capitol for the first time to advocate for people with disabilities and rare diseases and leaving already wanting to do more of it is exactly how real advocacy starts. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f49c',
    82: 'A leadership role built to strengthen the philanthropic support powering work for Duchenne families across Canada, finding someone passionate about building those partnerships for this exact mission matters more than a generic nonprofit hire. We sent you a little something in your DMs that we think you will love. \U0001f499',
    83: 'Caregiving not pausing just because you are on a trip, extra awareness and a mental load that never fully turns off even in the middle of arrowhead digging on challenging terrain, and then watching Matthew experience something brand new making all of it worth it. We sent you a little something in your DMs that we think you will love. \U0001f49c',
    84: '[SENSITIVE \u2014 review before pasting] Five years from the diagnosis, through brain cancer and four years and five months of fighting with the odds stacked against her, and Adeline taking her last breath on November 14. The Saint Patrick prayer you chose says what words alone cannot. Carrying you and Ed with us. We left you something in your DMs whenever you come up for air. \U0001f90d',
    # 85 michellevaughanklett = non-medical, SKIP
    # 86 janellestephaniephotography = non-medical, SKIP
    87: 'Happy birthday to Johnny! We slid into your DMs with a little something, take a peek when you get a second! \u2764\ufe0f',
    # 88 gudgoldmediablogspot = non-medical, SKIP
    90: 'The favorite Christmas is always the one that hits different for reasons that are hard to explain and easy to feel. We sent you a little something in your DMs that we think you will love. \U0001f499',
    91: 'Pre-celebrating the breastfeeding guide built by physicians who have actually been in the room, the lactation Bible that care teams and families have both been waiting for. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f4da',
    92: 'Two years in, still you, still a superhero, the diaversary poem landing that simply and that confidently is the tone that carries people through. Happy diaversary! We slid into your DMs with something we think you\'ll love, take a peek when the celebration settles! \U0001f499',
    93: 'Campbell first, diabetes second, working on that every single day from age 2 to now at 5, wanting to actually see his smile going down the water slide instead of having your head buried in the device is the most honest description of T1D parenting balance. We sent you a little something in your DMs that we think you will love. \U0001f499',
    94: 'Taking baseball days from overwhelming to T1D-friendly from security check to shady blood sugar break spots, that kind of reframe changes how families actually get to experience life outside the house. We slid into your DMs with a little something, take a peek when you get a second! \u26be',
    95: 'Finally committing to color on the fall piece in a new medium with the black and white scan as your safety net, that decision to go for it anyway and make it real is the right call. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f338',
    96: 'Kaser going 3-1 with five brand new teammates and the Dexcom visible right there in the tournament photo, stocking up on all things sugar and showing up ready is the whole T1D parent experience in one day. We sent you a little something in your DMs that we think you will love. \u26be',
    97: 'Modifying after Monday\'s soreness instead of pushing through and risking it, and still getting it done for week 2, that is actually the smarter play. We slid into your DMs with a little something, take a peek when you get a second! \U0001f4aa',
    98: 'Purple for Josey and leaning into the natural grey, a hair day with your person that feels like a proper reset is the best kind of Tuesday. We sent you a little something in your DMs that we think you will love. \U0001f49c',
    # 99 bweeei = gaming, SKIP
    # 100 shemoves_health_and_wellness = beauty business, SKIP
    # 101 evergreenhydro.aus = hydroponics, SKIP
    # 102 bighornsurvival = camping gear, SKIP
    # 103 scminer_media = crypto mining, SKIP
    # 104 jfk_premiumdetailing = car detailing, SKIP
    # 105 martin.rosendahl = nature photography, SKIP
    106: 'Detailed reading assessments with clear next steps for every child\'s learning profile, having that level of specificity instead of a general referral is exactly what parents and teachers have been looking for. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f4da',
    107: '"Your worth was never in your body, your money, or your relationships" being the line that actually lands, the kind of clarity that shifts the pattern rather than just naming it. We sent you a little something in your DMs that we think you will love. \U0001f49b',
    108: 'Day 100 of 100 completed and almost done with PreK-4, Jaxson doing that whole challenge all the way through is something to celebrate properly. We slid into your DMs with something we think you\'ll love, take a peek when he\'s settled in! \U0001f680',
    109: 'Making the credit list on the name suggestion for a local Nova Scotia entrepreneur\'s protein gummies is a very specific kind of win that absolutely counts. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f4aa',
    110: 'Developmental disability awareness month getting this kind of community push, showing up this Thursday for an organization worth it, is exactly how the conversation reaches people who need it most. We sent you a little something in your DMs that we think you will love. \U0001f9e0',
    111: 'A family-centered yoga session brought into a speech and OT practice meets families where they actually are, mind, body, and all the stress that lives between therapy appointments. We would love to chat when you have some time, we sent you something we think could help. \U0001f9d8',
    # 112 steph_ampersandgo = school fundraiser, SKIP
    113: '[SENSITIVE \u2014 review before pasting] Your voice, your touch, and your presence meaning everything to your baby even with all the wires and monitors, the bonding tips that help parents feel less helpless in those earliest days are exactly what families need most in those moments. We sent you a little something in your DMs that we think you will love. \U0001f9e1',
    114: '[SENSITIVE \u2014 review before pasting] Connection continuing to grow in ways that matter deeply no matter how it looks inside the NICU, that reminder from a community that actually understands the journey is what parents need to hear on the hardest days. We actually sent you a message, would love for you to take a peek when you get a chance. \U0001f499',
    115: '[SENSITIVE \u2014 review before pasting] A single trigger word landing with that much weight for families navigating prenatal diagnosis, the space being held here for people carrying stories no one else is talking about is something else entirely. We left you something in your DMs whenever you come up for air. \U0001f90d',
    116: 'Giving a bag of clothes and having someone pay for your coffee the next day, that chain of small kindness being a reminder that light is still here and darkness will not overcome it is exactly what some people needed to read today. We slid into your DMs with something we think you\'ll love, take a peek when you get a moment! \u2728',
    117: '[SENSITIVE \u2014 review before pasting] A session specifically on developmental care and parental anxiety with a medical director who actually understands the NICU world, the kind of conversation that fills a gap most parents did not even know they could ask about. We would love to chat when you have some time, we sent you something we think could help. \U0001f499',
    118: '[SENSITIVE \u2014 review before pasting] No one prepares you for walking out of that hospital without your baby, the emotions and heartbreak of that moment are real and giving yourself grace while trusting the NICU team is exactly the right thing to hold onto. She is growing stronger every day. We left you something in your DMs whenever you come up for air. \U0001f380',
    119: '[SENSITIVE \u2014 review before pasting] Not just processing the past but building tools to actually move forward, having a sounding board from someone who has been in that NICU room while navigating decisions, resources, and how to advocate with confidence, that is what makes this kind of coaching different. We would love to chat when you have some time, we sent you something we think could help. \U0001f499',
}

# Notes to write for non-medical accounts (to flag for Cherwin)
notes_flags = {
    44:  'SKIP - political content, not medical',
    85:  'SKIP - luxury fashion/resort, not medical family',
    86:  'SKIP - photography business, not medical',
    88:  'SKIP - Nigerian entertainment blog, not medical',
    99:  'SKIP - gaming content (Genshin Impact), not medical',
    100: 'SKIP - beauty/facial business, not medical',
    101: 'SKIP - hydroponics business, not medical',
    102: 'SKIP - camping/survival gear, not medical',
    103: 'SKIP - crypto mining equipment, not medical',
    104: 'SKIP - car detailing business, not medical',
    105: 'SKIP - nature photography, not medical',
    112: 'SKIP - school fundraiser, not medical',
}

print(f"Writing {len(comments)} comments + {len(notes_flags)} notes flags...")

cells = []

for row_num, comment in comments.items():
    cells.append(gspread.Cell(row_num, gen_comment_col, comment))

for row_num, note in notes_flags.items():
    cells.append(gspread.Cell(row_num, notes_col, note))

ws.update_cells(cells, value_input_option='USER_ENTERED')
print(f"Done! {len(comments)} comments written, {len(notes_flags)} non-medical flags written.")

# Summary
sensitive = [r for r, c in comments.items() if c.startswith('[SENSITIVE')]
print(f"\nSENSITIVE (review before pasting): {len(sensitive)} accounts")
print(f"  Rows: {sorted(sensitive)}")
print(f"\nSKIPPED (non-medical/political): rows {sorted(notes_flags.keys())}")
print(f"\nTotal accounts with comments ready: {len(comments)}")
