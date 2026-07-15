"""
slack_notify.py — post summaries + upload screenshots to Slack.

Used at the end of every Playwright posting session:
  - upload all of today's screenshots to the CAIT Slack channel
  - post a one-message summary (posted / DMs sent / failures)

Credentials (in .env — never commit):
  SLACK_BOT_TOKEN   xoxb-... bot token with chat:write + files:write
  SLACK_CHANNEL_ID  channel ID (e.g. C0123ABCDEF) — bot must be invited to it

CLI:
  python scripts/slack_notify.py --test
  python scripts/slack_notify.py --summary "Posted 20 comments, sent 40 DMs"
  python scripts/slack_notify.py --screenshots 2026-07-14          # uploads outputs/screenshots/*_2026-07-14.png
  python scripts/slack_notify.py --summary "..." --screenshots 2026-07-14
"""

import os, sys, glob, json, argparse
import requests
from dotenv import dotenv_values

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV  = dotenv_values(os.path.join(BASE, ".env"))

TOKEN   = ENV.get("SLACK_BOT_TOKEN")   or os.environ.get("SLACK_BOT_TOKEN")
CHANNEL = ENV.get("SLACK_CHANNEL_ID")  or os.environ.get("SLACK_CHANNEL_ID")

API = "https://slack.com/api"


def _check_creds():
    if not TOKEN or not CHANNEL:
        print("ERROR: SLACK_BOT_TOKEN and/or SLACK_CHANNEL_ID missing from .env")
        print("Setup: api.slack.com/apps -> create app -> OAuth scopes chat:write + files:write")
        print("       -> install to workspace -> invite bot to channel -> paste token + channel ID into .env")
        sys.exit(1)


def post_summary(text, channel=None):
    """Post a plain text message. Returns ts of the message or None."""
    _check_creds()
    r = requests.post(f"{API}/chat.postMessage",
                      headers={"Authorization": f"Bearer {TOKEN}"},
                      json={"channel": channel or CHANNEL, "text": text},
                      timeout=30)
    j = r.json()
    if not j.get("ok"):
        print(f"chat.postMessage failed: {j.get('error')}")
        return None
    return j.get("ts")


def upload_file(path, channel=None, title=None, thread_ts=None):
    """Upload one file via the external-upload flow (files.upload is deprecated)."""
    _check_creds()
    fname = os.path.basename(path)
    size  = os.path.getsize(path)

    # Step 1: get upload URL
    r = requests.post(f"{API}/files.getUploadURLExternal",
                      headers={"Authorization": f"Bearer {TOKEN}"},
                      data={"filename": fname, "length": size},
                      timeout=30)
    j = r.json()
    if not j.get("ok"):
        print(f"  {fname}: getUploadURLExternal failed: {j.get('error')}")
        return False

    # Step 2: upload bytes
    with open(path, "rb") as f:
        up = requests.post(j["upload_url"], files={"file": (fname, f)}, timeout=120)
    if up.status_code != 200:
        print(f"  {fname}: byte upload failed HTTP {up.status_code}")
        return False

    # Step 3: complete + share to channel
    payload = {
        "files":      json.dumps([{"id": j["file_id"], "title": title or fname}]),
        "channel_id": channel or CHANNEL,
    }
    if thread_ts:
        payload["thread_ts"] = thread_ts
    r2 = requests.post(f"{API}/files.completeUploadExternal",
                       headers={"Authorization": f"Bearer {TOKEN}"},
                       data=payload, timeout=30)
    j2 = r2.json()
    if not j2.get("ok"):
        print(f"  {fname}: completeUploadExternal failed: {j2.get('error')}")
        return False
    return True


def upload_screenshots(date_str, channel=None, thread_ts=None):
    """Upload all outputs/screenshots/*_{date}.png. Returns (ok_count, fail_count)."""
    pattern = os.path.join(BASE, "outputs", "screenshots", f"*_{date_str}.png")
    paths = sorted(glob.glob(pattern))
    if not paths:
        print(f"No screenshots matching {pattern}")
        return 0, 0
    print(f"Uploading {len(paths)} screenshots to Slack...")
    ok = fail = 0
    for p in paths:
        handle = os.path.basename(p).rsplit("_", 1)[0]
        if upload_file(p, channel=channel, title=f"@{handle}", thread_ts=thread_ts):
            ok += 1
            print(f"  OK @{handle}")
        else:
            fail += 1
    print(f"Done: {ok} uploaded, {fail} failed")
    return ok, fail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="send a test message")
    ap.add_argument("--summary", help="text to post as summary message")
    ap.add_argument("--screenshots", help="date (YYYY-MM-DD) — upload all screenshots for that date")
    ap.add_argument("--channel", help="override channel ID")
    args = ap.parse_args()

    if args.test:
        ts = post_summary("CAIT runner Slack integration test — it works! 🤍", channel=args.channel)
        print("Test message sent" if ts else "Test FAILED")
        return

    thread_ts = None
    if args.summary:
        thread_ts = post_summary(args.summary, channel=args.channel)
        print("Summary posted" if thread_ts else "Summary FAILED")

    if args.screenshots:
        # screenshots go in a thread under the summary when both are given
        upload_screenshots(args.screenshots, channel=args.channel, thread_ts=thread_ts)

    if not args.summary and not args.screenshots:
        print("Nothing to do. Use --test, --summary, or --screenshots.")


if __name__ == "__main__":
    main()
