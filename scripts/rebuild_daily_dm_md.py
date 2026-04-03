"""
rebuild_daily_dm_md.py
----------------------
Rebuilds the daily_dm markdown file in the exact order rows appear
in the Google Sheet for DM Status = "To Send - 2026-03-24".
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
ws = gc.open_by_key(os.environ['GOOGLE_SHEET_ID']).worksheet('Medical Mom DM Outreach')

print("Reading sheet...")
all_values = ws.get_all_values()
headers = [h.strip() for h in all_values[0]]
col = {h: i for i, h in enumerate(headers)}

TARGET_STATUS = 'To Send - 2026-03-24'

# Collect rows in sheet order (skip VIPs rows 2-19, only non-VIP To Send)
accounts = []
for row_num, row in enumerate(all_values[1:], start=2):
    if row_num < 20:  # VIP rows — skip
        continue
    status = row[col['DM Status']].strip() if col['DM Status'] < len(row) else ''
    if status != TARGET_STATUS:
        continue
    handle = row[col['Handle']].strip().lstrip('@') if col['Handle'] < len(row) else ''
    category = row[col['Category']].strip() if col['Category'] < len(row) else ''
    name_used = row[col['Name Used']].strip() if col['Name Used'] < len(row) else ''
    notes = row[col['Notes']].strip() if col['Notes'] < len(row) else ''

    # Skip flagged non-medical accounts
    if notes.startswith('SKIP'):
        continue

    accounts.append({
        'handle': handle,
        'category': category,
        'name_used': name_used,
    })

print(f"Found {len(accounts)} qualifying accounts in sheet order")

DM_TEMPLATE = """Hi {name}

We came across your page and just wanted to say how much we admire everything you're managing, it's a lot.

We've been building something with our medical parent community from day one that helps take things out of your head \u2014 like tracking symptoms, medications, and everything going on day-to-day, without needing to remember it all.

It has a similar intelligence to ChatGPT, but feels much more personal and built for real family life.

Many medical parents have told us it's been a game changer for them and something they wish they had much earlier.

We're opening early access to a small group before launch \u2014 if it feels like it could help at all, we'd be happy to share it with you

We also offer a small honorarium as a thank you for your time all we ask is for your honest feedback to see how this could help you each day.

If you're open, we'd be happy to share more details

Mikha
Brand Partnership Lead
caitconnect.com"""

lines = [
    f"# CAIT Daily DM List \u2014 2026-03-24",
    f"Total accounts: {len(accounts)}",
    "",
    "> Send each DM manually via Instagram. Do NOT copy-paste the same message to many accounts in quick succession \u2014 space them out.",
    "",
    "---",
    "",
]

for acct in accounts:
    handle = acct['handle']
    category = acct['category']
    name = acct['name_used'] if acct['name_used'] else handle

    lines.append(f"## @{handle} \u2014 {category}")
    lines.append(f"Profile: https://instagram.com/{handle}")
    lines.append(f"Name used: {name}")
    lines.append("")
    lines.append("---")
    lines.append(DM_TEMPLATE.format(name=name))
    lines.append("---")
    lines.append("")
    lines.append("")

output = "\n".join(lines)
out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs', 'daily_dm_2026-03-24.md')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"Rebuilt: {out_path}")
print(f"Total entries: {len(accounts)}")
