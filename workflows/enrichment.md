# Workflow: Email & Contact Enrichment

## Objective
Find a valid contact email for a qualified Instagram account using free methods. Used primarily for the CAIT Community tab. Secondary use for 50 Million List when email is available.

## When to Run
- Automatically as part of `workflows/instagram-discovery.md` for CAIT Community accounts
- Can also run standalone on a list of usernames that need enrichment

## Required Inputs
- Instagram username or profile URL
- Bio text (from profile scrape)
- Website URL from bio (if present)

## Pipeline (Run in Order — Stop When Email Found)

### Method 1 — Bio Scan
Regex search the bio text for email patterns.

Pattern: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`

Also check for common obfuscation:
- "name [at] domain [dot] com"
- "name(at)domain.com"
- Email emoji variations

**Email Source if found:** `bio`

### Method 2 — Link in Bio Follow
If bio contains a URL:
1. Follow the URL (handle redirects)
2. If Linktree or similar link aggregator — scan all linked URLs
3. Load each page and scan for email patterns

**Common pages to check:**
- /contact
- /about
- /work-with-me
- /collab
- /partnerships
- /hire-me

**Email Source if found:** `website`

### Method 3 — Website Deep Scrape
If the website is found but Method 2 didn't yield an email:
1. Scan the homepage for mailto: links
2. Try common contact page paths: /contact, /contact-us, /get-in-touch
3. Scan footer for email patterns (many businesses list contact email in footer)
4. Check "Privacy Policy" page — often lists a business contact email

**Email Source if found:** `website`

### Method 4 — Hunter.io (NOT YET CONFIGURED)
Skip until `HUNTER_API_KEY` is set in `.env`.

When configured:
- Use domain from website URL
- Search for first name + domain combination
- Only use verified results (confidence 80%+)

**Email Source if found:** `hunter`

### If No Email Found
- Set Email = blank
- Set Email Source = `not found`
- Still write the row — a qualified account without email is still useful
- Note in memory that this account needs enrichment in a future run

---

## Alternative Free Email Tools (Use When Volume Grows)

When Hunter.io is configured and batch sizes increase beyond 5:

**Snov.io** (50 free/month)
- Good for professional accounts with clear website domains
- `https://app.snov.io/email-finder`

**Apollo.io** (free tier — 50 exports/month)
- Strong database of professionals (BCBAs, therapists, educators)
- Search by name + company/website domain

**Clearbit Connect** (Gmail plugin — free for individual lookups)
- Useful for verifying emails found by other methods

---

## Email Validation

Before writing any email to the sheet, run a basic validation check:
1. Does it have an @ symbol and valid domain format?
2. Is the domain a real website (check if site loads)?
3. Does it look professional? (not a temp email, not obviously fake)

Do NOT validate with a paid bounce-checking service until list is at launch scale.

---

## Email Source Taxonomy

| Value | Meaning |
|-------|---------|
| `bio` | Found directly in Instagram bio text |
| `website` | Found by scraping website from bio link |
| `hunter` | Found via Hunter.io API (when configured) |
| `snov` | Found via Snov.io (when configured) |
| `not found` | All methods attempted, no email found |

---

## Logging
For each enrichment run, note in `memory/YYYY-MM-DD.md`:
- How many accounts attempted
- How many emails found and by which method
- Method success rates (this informs which method to prioritize for a given account type)
