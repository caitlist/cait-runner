---
name: enrich-contact
description: Use when you need to find the contact email or additional context for a specific Instagram account. Pass a username and get back email (if found), source, website, product/course details, and a partnership angle note. Use for CAIT Community accounts where email is required before outreach.
---

## What This Skill Does

Manually runs the enrichment pipeline for a specific account. Useful when:
- A batch script couldn't find the email and Cherwin wants a second attempt
- You need to add product/course context to an existing sheet entry
- You're enriching a small set of accounts that don't justify running the full script

## When to Use It

- Cherwin says "can you find the email for @[username]"
- Script returned "not found" and you want to try manually
- Adding context (product name, course URL, partnership angle) to an existing entry

## Steps

1. **Bio scan** — Check the account bio for email pattern
   - Look for standard email, obfuscated email ([at], (dot)), or contact instructions

2. **Link in bio** — Follow any URL in the bio
   - Check homepage for mailto links and visible emails
   - Try /contact, /about, /work-with-me, /collab paths

3. **Website footer** — Scan footer for business email
   - Most professional accounts list an email in their footer

4. **Product/course context** — Identify what they sell
   - What's the product or course?
   - What's the URL?
   - Who is the audience?

5. **Partnership angle** — Based on what they sell and their audience, what is the one-sentence reason CAIT is a good fit?

## Output

```
Username: @[username]
Email: [email or "not found"]
Email Source: bio / website / hunter / not found
Website: [URL]
Product/Course: [name and brief description]
Partnership Angle: [one sentence]
Tier: 1 / 2 / 3
Notes (for sheet): [ready to paste into Notes column]
```

If Hunter.io is not yet configured, skip to "not found" after website scrape and note "Hunter not configured."
