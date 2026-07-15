"""
runner3.py  —  CAIT Daily Runner  (copy of runner2.py — local reference)

Comments tab  : editable caption, Regenerate Comment, Done / Skip / Previous
Validation tab: Approve / Not Valid for Medical Mom DM Outreach
Email tab     : Open profile + DM Sent for accounts with Status=Emailed

Start : python scripts/runner3.py
URL   : http://localhost:5564
"""

import os, re, json, time, datetime, threading
import requests
import gspread
from flask import Flask, jsonify, request, render_template_string
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SHEET_ID   = os.environ.get("GOOGLE_SHEET_ID")
CREDS_PATH = os.environ.get("GOOGLE_CREDS_PATH")
BASE       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT        = os.path.join(BASE, "outputs")
os.makedirs(OUT, exist_ok=True)
REQ_FILE   = os.path.join(OUT, "runner_request.json")
RES_FILE   = os.path.join(OUT, "runner_result.json")
PORT       = int(os.environ.get("PORT", 5564))

app = Flask(__name__)

# ── Google Sheets ───────────────────────────────────────────────────────────────

def make_gc():
    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if creds_json:
        info = json.loads(creds_json)
        # Fix private key newlines if mangled by env var storage
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    else:
        creds = Credentials.from_service_account_file(
            CREDS_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds)

def open_sheets(gc):
    ss = gc.open_by_key(SHEET_ID)
    return ss.worksheet("COMMENTS"), ss.worksheet("Medical Mom DM Outreach"), ss.worksheet("Email")

def read_share(ws):
    """Load ALL COMMENTS rows for Share Post tab — no Runner Status filter."""
    rows = ws.get_all_values()
    if not rows:
        return []
    hdrs = [h.strip() for h in rows[0]]
    hi   = {h: i for i, h in enumerate(hdrs)}
    def g(row, col):
        i = hi.get(col)
        return row[i].strip() if i is not None and i < len(row) else ""
    queue = []
    for i, row in enumerate(rows[1:], 2):
        handle = g(row, "Handle")
        if not handle:
            continue
        ig = g(row, "IG Profile Link") or \
             "https://www.instagram.com/{}/".format(handle.lstrip("@").lower())
        queue.append({"row": i, "handle": handle, "ig_link": ig})
    return queue

def read_comments(ws):
    rows = ws.get_all_values()
    if not rows:
        return [], {}
    hdrs = [h.strip() for h in rows[0]]
    hi   = {h: i for i, h in enumerate(hdrs)}

    for needed in ["Runner Status", "Approval", "Evidence"]:
        if needed not in hi:
            ws.update_cell(1, len(hdrs) + 1, needed)
            hdrs.append(needed)
            hi[needed] = len(hdrs) - 1

    def g(row, col):
        i = hi.get(col)
        return row[i].strip() if i is not None and i < len(row) else ""

    queue = []
    for i, row in enumerate(rows[1:], 2):
        handle  = g(row, "Handle")
        comment = g(row, "Generated Comment")
        status  = g(row, "Runner Status")
        if not handle or not comment or "Posted" in status:
            continue
        ig = g(row, "IG Profile Link") or \
             "https://www.instagram.com/{}/".format(handle.lstrip("@").lower())
        queue.append({
            "row":       i,
            "handle":    handle,
            "ig_link":   ig,
            "post_url":  g(row, "Post URL"),
            "caption":   g(row, "Post Caption")[:800],
            "comment":   comment,
            "dm1":       g(row, "DM Part 1"),
            "sensitive": "[SENSITIVE" in g(row, "Notes"),
            "approval":  g(row, "Approval"),
            "evidence":  g(row, "Evidence")[:600],
        })

    col_map = {h: j + 1 for j, h in enumerate(hdrs)}
    return queue, col_map

def read_email(ws):
    rows = ws.get_all_values()
    if not rows:
        return [], {}
    hdrs = [h.strip() for h in rows[0]]
    hi   = {h: i for i, h in enumerate(hdrs)}

    def g(row, col):
        i = hi.get(col)
        return row[i].strip() if i is not None and i < len(row) else ""

    queue = []
    for i, row in enumerate(rows[1:], 2):
        handle = g(row, "Handle").lstrip("@").strip()
        status = g(row, "Status")
        if not handle or status != "Emailed":
            continue
        ig = g(row, "IG Profile Link") or \
             "https://www.instagram.com/{}/".format(handle.lower())
        queue.append({
            "row":       i,
            "handle":    handle,
            "ig_link":   ig,
            "email":     g(row, "Emails"),
            "notes":     g(row, "Notes"),
            "diagnosis": g(row, "Diagnosis"),
        })
    col_map = {h: j + 1 for j, h in enumerate(hdrs)}
    return queue, col_map

def read_validation(ws):
    rows = ws.get_all_values()
    if not rows:
        return [], {}
    hdrs = [h.strip() for h in rows[0]]
    hi   = {h: i for i, h in enumerate(hdrs)}

    def g(row, col):
        i = hi.get(col)
        return row[i].strip() if i is not None and i < len(row) else ""

    queue = []
    for i, row in enumerate(rows[1:], 2):
        handle = g(row, "Handle")
        notes  = g(row, "Notes").upper()
        if handle and "APPROVE" not in notes and "NOT VALID" not in notes:
            ig = g(row, "IG Profile Link") or \
                 "https://www.instagram.com/{}/".format(handle.lstrip("@").lower())
            queue.append({
                "row":      i,
                "handle":   handle,
                "ig_link":  ig,
                "category": g(row, "Category"),
                "hashtag":  g(row, "Source Hashtag"),
                "display":  g(row, "Display Name"),
            })
    col_map = {h: j + 1 for j, h in enumerate(hdrs)}
    return queue, col_map

# ── Global state ────────────────────────────────────────────────────────────────

gc_client = None
ws_c = ws_v = ws_e = None
cq = []; cc = {}
vq = []; vc = {}
eq = []; ec = {}

# ── Routes ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(PAGE)

@app.route("/api/cq")
def api_cq():
    return jsonify(cq)

@app.route("/api/vq")
def api_vq():
    return jsonify(vq)

@app.route("/api/reload-cq")
def api_reload_cq():
    global cq, cc, ws_c
    try:
        ws_c, _, _ = open_sheets(gc_client)
        cq, cc     = read_comments(ws_c)
        return jsonify({"ok": True, "count": len(cq)})
    except Exception as ex:
        return jsonify({"ok": False, "error": str(ex)})

@app.route("/api/reload-vq")
def api_reload_vq():
    global vq, vc, ws_v
    try:
        _, ws_v, _ = open_sheets(gc_client)
        vq, vc     = read_validation(ws_v)
        return jsonify({"ok": True, "count": len(vq)})
    except Exception as ex:
        return jsonify({"ok": False, "error": str(ex)})

@app.route("/api/eq")
def api_eq():
    return jsonify(eq)

@app.route("/api/reload-eq")
def api_reload_eq():
    global eq, ec, ws_e
    try:
        _, _, ws_e = open_sheets(gc_client)
        eq, ec     = read_email(ws_e)
        return jsonify({"ok": True, "count": len(eq)})
    except Exception as ex:
        return jsonify({"ok": False, "error": str(ex)})

@app.route("/api/sq")
def api_sq():
    return jsonify(sq)

@app.route("/api/reload-sq")
def api_reload_sq():
    global sq, ws_c
    try:
        ws_c, _, _ = open_sheets(gc_client)
        sq         = read_share(ws_c)
        return jsonify({"ok": True, "count": len(sq)})
    except Exception as ex:
        return jsonify({"ok": False, "error": str(ex)})

@app.route("/api/mark-dm-sent", methods=["POST"])
def api_mark_dm_sent():
    global eq
    d = request.json
    row = int(d["row"])
    col = ec.get("Status")
    if col:
        ws_e.update_cell(row, col, "DM Sent")
    eq = [item for item in eq if item["row"] != row]
    return jsonify(ok=True)

@app.route("/api/save-comment", methods=["POST"])
def api_save_comment():
    d   = request.json
    col = cc.get("Generated Comment")
    if col:
        ws_c.update_cell(int(d["row"]), col, d["comment"].strip())
    return jsonify(ok=True)

@app.route("/api/mark-posted", methods=["POST"])
def api_mark_posted():
    d   = request.json
    row = int(d["row"])
    cells = []
    if cc.get("Runner Status"):
        now = datetime.datetime.now()
        cells.append(gspread.Cell(row, cc["Runner Status"],
                                  "Posted {} {}".format(now.day, now.strftime("%b"))))
    if cc.get("Generated Comment") and d.get("comment"):
        cells.append(gspread.Cell(row, cc["Generated Comment"], d["comment"].strip()))
    if cells:
        ws_c.update_cells(cells, value_input_option="USER_ENTERED")
    return jsonify(ok=True)

@app.route("/api/mark-validation", methods=["POST"])
def api_mark_validation():
    d   = request.json
    col = vc.get("Notes")
    if col:
        ws_v.update_cell(int(d["row"]), col, d["verdict"])
    return jsonify(ok=True)

# ── Add Links (mobile intake) ───────────────────────────────────────────────────

IG_RESERVED_PATHS = {"p", "reel", "reels", "tv", "stories", "explore", "accounts",
                     "direct", "about", "legal", "developer", "web", "share", "invites"}

def parse_ig_links(text):
    """Split pasted text into profile handles and post URLs."""
    profiles, posts = [], []
    for m in re.finditer(r'https?://(?:www\.)?instagram\.com/([A-Za-z0-9._]+)(/[^\s]*)?', text):
        seg, rest = m.group(1), (m.group(2) or "")
        if seg.lower() in IG_RESERVED_PATHS:
            posts.append("https://www.instagram.com/{}{}".format(seg, rest.split("?")[0]))
        else:
            h = seg.strip(".").strip()
            if h:
                profiles.append(h)
    return profiles, posts

@app.route("/api/add-links", methods=["POST"])
def api_add_links():
    global ws_c
    d = request.json or {}
    profiles, post_urls = parse_ig_links(d.get("links", ""))
    if not profiles and not post_urls:
        return jsonify(ok=False, error="No Instagram links found in the text")
    try:
        ws_c, _, _ = open_sheets(gc_client)
        rows = ws_c.get_all_values()
        if not rows:
            return jsonify(ok=False, error="COMMENTS tab has no header row")
        hdrs = [h.strip() for h in rows[0]]
        hi   = {h: i for i, h in enumerate(hdrs)}
        existing = set()
        for r in rows[1:]:
            ih = hi.get("Handle", 0)
            if ih < len(r) and r[ih].strip():
                existing.add(r[ih].strip().lstrip("@").lower())
            iu = hi.get("Post URL")
            if iu is not None and iu < len(r) and r[iu].strip():
                existing.add(r[iu].strip().rstrip("/").lower())
        width = len(hdrs)
        new_rows, added, skipped = [], [], 0
        seen_now = set()
        for h in profiles:
            key = h.lower()
            if key in existing or key in seen_now:
                skipped += 1; continue
            seen_now.add(key)
            row = [""] * width
            if "Handle" in hi:
                row[hi["Handle"]] = h
            if "IG Profile Link" in hi:
                row[hi["IG Profile Link"]] = "https://www.instagram.com/{}/".format(h)
            new_rows.append(row); added.append("@" + h)
        for u in post_urls:
            key = u.rstrip("/").lower()
            if key in existing or key in seen_now:
                skipped += 1; continue
            seen_now.add(key)
            row = [""] * width
            if "Post URL" in hi:
                row[hi["Post URL"]] = u
            elif "IG Profile Link" in hi:
                row[hi["IG Profile Link"]] = u
            new_rows.append(row); added.append(u.replace("https://www.instagram.com", "ig.com"))
        if new_rows:
            ws_c.append_rows(new_rows, value_input_option="USER_ENTERED")
        return jsonify(ok=True, added=len(new_rows), skipped=skipped, items=added)
    except Exception as ex:
        return jsonify(ok=False, error=str(ex))

# ── Review / Approval ───────────────────────────────────────────────────────────

@app.route("/api/save-review", methods=["POST"])
def api_save_review():
    d   = request.json
    row = int(d["row"])
    cells = []
    if cc.get("Generated Comment") and d.get("comment") is not None:
        cells.append(gspread.Cell(row, cc["Generated Comment"], d["comment"].strip()))
    if cc.get("DM Part 1") and d.get("dm1") is not None:
        cells.append(gspread.Cell(row, cc["DM Part 1"], d["dm1"].strip()))
    if cells:
        ws_c.update_cells(cells, value_input_option="USER_ENTERED")
    return jsonify(ok=True)

@app.route("/api/approve", methods=["POST"])
def api_approve():
    d   = request.json
    col = cc.get("Approval")
    if col:
        ws_c.update_cell(int(d["row"]), col, "Approved" if d.get("approved", True) else "")
    return jsonify(ok=True)

@app.route("/api/approve-all", methods=["POST"])
def api_approve_all():
    d    = request.json or {}
    rows = d.get("rows", [])
    col  = cc.get("Approval")
    if col and rows:
        cells = [gspread.Cell(int(r), col, "Approved") for r in rows]
        ws_c.update_cells(cells, value_input_option="USER_ENTERED")
    return jsonify(ok=True, count=len(rows))

# ── Runner Config (share post URL — read by the local Playwright session) ───────

def get_config_ws():
    ss = gc_client.open_by_key(SHEET_ID)
    try:
        return ss.worksheet("Runner Config")
    except gspread.exceptions.WorksheetNotFound:
        w = ss.add_worksheet("Runner Config", rows=10, cols=3)
        w.update("A1", [["Share Post URL"]])
        return w

@app.route("/api/set-share-url", methods=["POST"])
def api_set_share_url():
    d = request.json or {}
    try:
        w = get_config_ws()
        w.update("B1", [[d.get("url", "").strip()]])
        return jsonify(ok=True)
    except Exception as ex:
        return jsonify(ok=False, error=str(ex))

@app.route("/api/get-share-url")
def api_get_share_url():
    try:
        w = get_config_ws()
        return jsonify(ok=True, url=w.acell("B1").value or "")
    except Exception as ex:
        return jsonify(ok=False, error=str(ex))

@app.route("/api/request-action", methods=["POST"])
def api_request_action():
    d   = request.json
    req = {
        "id":        str(time.time()),
        "action":    d["action"],
        "handle":    d["handle"],
        "row":       d["row"],
        "caption":   d.get("caption", ""),
        "post_url":  d.get("post_url", ""),
        "seen_urls": d.get("seen_urls", []),
    }
    if os.path.exists(RES_FILE): os.remove(RES_FILE)
    with open(REQ_FILE, "w", encoding="utf-8") as f:
        json.dump(req, f, indent=2, ensure_ascii=False)
    return jsonify(ok=True)

@app.route("/api/check-result")
def api_check_result():
    if not os.path.exists(RES_FILE):
        return jsonify(ready=False)
    try:
        with open(RES_FILE, encoding="utf-8") as f:
            r = json.load(f)
        return jsonify(ready=True, **r)
    except Exception:
        return jsonify(ready=False)

@app.route("/api/clear-result", methods=["POST"])
def api_clear_result():
    for p in [RES_FILE, REQ_FILE]:
        if os.path.exists(p): os.remove(p)
    return jsonify(ok=True)

# ── HTML ────────────────────────────────────────────────────────────────────────

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CAIT Runner 3</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f5f7;min-height:100vh;padding:16px}
.tabs{display:flex;gap:6px;justify-content:center;margin-bottom:12px;flex-wrap:wrap}
.tab{border:none;border-radius:20px;padding:8px 18px;font-size:14px;font-weight:600;cursor:pointer;background:#e0e0e0;color:#555}
.tab.on{background:#007aff;color:#fff}
.hdr{text-align:center;margin-bottom:12px}
.bar{background:#e0e0e0;border-radius:8px;height:6px;max-width:360px;margin:6px auto;overflow:hidden}
.fill{background:#007aff;height:100%;border-radius:8px;transition:width .3s}
.pt{font-size:13px;color:#888;margin-top:4px}
.card{background:#fff;border-radius:16px;padding:20px;max-width:680px;margin:0 auto;box-shadow:0 2px 14px rgba(0,0,0,.08)}
.hr2{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:14px}
.hn{font-size:20px;font-weight:700;color:#1d1d1f}
.badge{font-size:11px;font-weight:600;padding:3px 9px;border-radius:20px;color:#fff}
.bg{background:#34c759}.br{background:#ff3b30}.bo{background:#ff9500}.bb{background:#007aff}
.lbl{font-size:11px;font-weight:600;color:#aaa;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}
.sublbl{font-size:10px;color:#bbb;font-weight:400;text-transform:none;letter-spacing:0;margin-left:6px}
.opbtn{display:inline-flex;align-items:center;gap:6px;background:#f0f0f0;border:none;border-radius:8px;padding:7px 13px;font-size:13px;color:#333;cursor:pointer;margin-bottom:10px;font-weight:500}
.opbtn:hover{background:#e5e5e5}
.section{margin-bottom:14px}
textarea{width:100%;border:1.5px solid #e0e0e0;border-radius:10px;padding:10px;font-size:13px;line-height:1.6;resize:vertical;font-family:inherit;color:#1d1d1f;transition:border-color .2s;background:#fff}
textarea:focus{outline:none;border-color:#007aff}
textarea.readonly-look{background:#f9f9f9;color:#888}
#cap-area{min-height:70px}
#com-area{min-height:95px;font-size:14px}
.ch{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.cc{font-size:12px;color:#bbb}
.brow{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:7px}
.btn{border:none;border-radius:10px;padding:11px 14px;font-size:13px;font-weight:600;cursor:pointer;transition:opacity .15s;flex:1;min-width:80px;white-space:nowrap}
.btn:disabled{opacity:.35;cursor:not-allowed}
.blue{background:#007aff;color:#fff}
.green{background:#34c759;color:#fff}
.red{background:#ff3b30;color:#fff}
.purple{background:#5856d6;color:#fff}
.teal{background:#30b0c7;color:#fff}
.gray{background:#e8e8ed;color:#1d1d1f}
.banner{background:#fff3cd;border:1px solid #ffc107;border-radius:10px;padding:12px 14px;margin-bottom:12px;font-size:13px;display:none;align-items:center;gap:10px}
.banner.on{display:flex}
.dot{width:10px;height:10px;border-radius:50%;background:#ff9500;animation:pulse 1s infinite;flex-shrink:0}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#1d1d1f;color:#fff;padding:10px 20px;border-radius:20px;font-size:13px;opacity:0;transition:opacity .25s;pointer-events:none;z-index:999;white-space:nowrap}
.toast.on{opacity:1}
.toast.err{background:#ff3b30}
.done-card{text-align:center;padding:60px 20px}
.done-card h2{font-size:24px;margin-bottom:10px}
.done-card p{color:#888;font-size:14px}
.pill{background:#f0f0f0;border-radius:8px;padding:5px 10px;font-size:12px;color:#555;font-weight:500}
.pills{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.refresh-row{display:flex;justify-content:center;margin-bottom:6px}
.refresh-btn{border:none;background:none;color:#007aff;font-size:12px;cursor:pointer;padding:2px 8px;border-radius:6px}
.refresh-btn:hover{background:#e8f0ff}
</style>
</head>
<body>

<div class="tabs">
  <button class="tab on" id="tC" onclick="goTab('c')">Comments</button>
  <button class="tab"    id="tR" onclick="goTab('r')">Review</button>
  <button class="tab"    id="tA" onclick="goTab('a')">Add Links</button>
  <button class="tab"    id="tV" onclick="goTab('v')">Validation</button>
  <button class="tab"    id="tE" onclick="goTab('e')">Email</button>
  <button class="tab"    id="tS" onclick="goTab('s')">Share Post</button>
</div>
<div class="hdr">
  <div class="bar"><div class="fill" id="fill" style="width:0%"></div></div>
  <div class="pt" id="pt">Loading...</div>
  <div class="refresh-row">
    <button class="refresh-btn" onclick="refreshQueue()">&#8635; Refresh queue</button>
  </div>
</div>
<div id="app"><p style="text-align:center;padding:40px;color:#888">Loading...</p></div>
<div class="toast" id="toast"></div>

<script>
var TAB='c';
var CQ=[], CDone=new Set(), CIdx=0, COrigs={};
var VQ=[], VDone=new Set(), VIdx=0, VQLoaded=false;
var EQ=[], EDone=new Set(), EIdx=0, EQLoaded=false;
var SQ=[];
var poll=null;

// Boot: load Comments immediately, then Validation + Email in background
async function boot(){
  try {
    var cr = await fetch('/api/cq').then(function(r){ return r.json(); });
    CQ = cr;
    CQ.forEach(function(x){ COrigs[x.row] = x.comment; });
    showC(0);
    setInterval(refreshQueue, 30000);
  } catch(err) {
    document.getElementById('app').innerHTML =
      '<div class="card done-card"><p style="color:#ff3b30">Failed to load queue. Is the server running?</p></div>';
    document.getElementById('pt').textContent = 'Error';
    return;
  }
  // Load Validation silently in background
  try {
    var vr = await fetch('/api/vq').then(function(r){ return r.json(); });
    VQ = vr; VQLoaded = true;
  } catch(err) {}
  // Load Email silently in background
  try {
    var er = await fetch('/api/eq').then(function(r){ return r.json(); });
    EQ = er; EQLoaded = true;
  } catch(err) {}
  // Load Share Post silently in background
  try {
    var sr = await fetch('/api/sq').then(function(r){ return r.json(); });
    SQ = sr;
  } catch(err) {}
  loadShareURL();
}

async function refreshQueue(){
  try {
    var r = await fetch('/api/reload-cq').then(function(x){ return x.json(); });
    if(!r.ok) return;
    var existingRows = new Set(CQ.map(function(x){ return x.row; }));
    var cr = await fetch('/api/cq').then(function(x){ return x.json(); });
    var added = 0;
    cr.forEach(function(x){
      if(!existingRows.has(x.row)){
        CQ.push(x);
        COrigs[x.row] = x.comment;
        added++;
      } else {
        var idx = CQ.findIndex(function(q){ return q.row === x.row; });
        if(idx >= 0 && !CDone.has(x.row)) CQ[idx] = x;
      }
    });
    prog();
    if(added > 0) toast(added + ' new account' + (added > 1 ? 's' : '') + ' added to queue');
  } catch(err) {}
}

function goTab(t){
  TAB = t;
  document.getElementById('tC').classList.toggle('on', t === 'c');
  document.getElementById('tR').classList.toggle('on', t === 'r');
  document.getElementById('tA').classList.toggle('on', t === 'a');
  document.getElementById('tV').classList.toggle('on', t === 'v');
  document.getElementById('tE').classList.toggle('on', t === 'e');
  document.getElementById('tS').classList.toggle('on', t === 's');
  if(t === 'c'){ showC(CIdx); return; }
  if(t === 'r'){ showR(); return; }
  if(t === 'a'){ showA(); return; }
  if(t === 's'){ showS(); return; }
  if(t === 'v'){
    if(!VQLoaded){
      document.getElementById('app').innerHTML =
        '<div class="card done-card"><p>Loading validation accounts...</p></div>';
      document.getElementById('pt').textContent = 'Loading...';
      var chk = setInterval(function(){
        if(VQLoaded){ clearInterval(chk); showV(VIdx); }
      }, 300);
      return;
    }
    showV(VIdx); return;
  }
  if(t === 'e'){
    if(!EQLoaded){
      document.getElementById('app').innerHTML =
        '<div class="card done-card"><p>Loading email accounts...</p></div>';
      document.getElementById('pt').textContent = 'Loading...';
      var chk2 = setInterval(function(){
        if(EQLoaded){ clearInterval(chk2); showE(EIdx); }
      }, 300);
      return;
    }
    showE(EIdx);
  }
}

function prog(){
  if(TAB === 'a'){
    document.getElementById('fill').style.width = '0%';
    document.getElementById('pt').textContent = 'Paste Instagram links below';
    return;
  }
  if(TAB === 'r'){
    var rp = CQ.filter(function(x){ return !CDone.has(x.row); });
    var ra = rp.filter(function(x){ return x.approval === 'Approved'; }).length;
    document.getElementById('fill').style.width = (rp.length ? ra/rp.length*100 : 0) + '%';
    document.getElementById('pt').textContent = ra + ' of ' + rp.length + ' approved';
    return;
  }
  var done = TAB === 'c' ? CDone.size : TAB === 'v' ? VDone.size : TAB === 'e' ? EDone.size : 0;
  var tot  = TAB === 'c' ? CQ.length  : TAB === 'v' ? VQ.length  : TAB === 'e' ? EQ.length  : SQ.length;
  var rem  = tot - done;
  document.getElementById('fill').style.width = (tot > 0 ? done/tot*100 : 0) + '%';
  document.getElementById('pt').textContent =
    rem > 0 ? (done+1) + ' of ' + tot + ' — ' + rem + ' remaining' : 'All ' + tot + ' done \u2713';
}

// ── COMMENTS TAB ───────────────────────────────────────────────────────────────
function showC(idx){
  if(CQ.length === 0){ allDone('No accounts in queue yet.'); return; }
  idx = Math.max(0, Math.min(idx, CQ.length - 1));
  CIdx = idx; stopPoll(); prog();
  var it = CQ[idx];
  var posted = CDone.has(it.row);

  document.getElementById('app').innerHTML =
    '<div class="card">' +

    '<div class="hr2">' +
      '<div class="hn">' + e(it.handle) + '</div>' +
      (posted ? '<span class="badge bg">\u2713 Posted</span>' : '') +
      (!posted && it.sensitive ? '<span class="badge br">\u26a0 Review first</span>' : '') +
    '</div>' +

    '<div class="banner" id="ban"><div class="dot"></div>' +
      '<span id="banmsg">Waiting for Claude Code...</span></div>' +

    '<div class="section">' +
      '<div class="lbl">Post</div>' +
      (it.post_url
        ? '<button class="opbtn" onclick="openURL(\'' + e(it.post_url) + '\')">&#128279; Open Post &#8599;</button>'
        : '<p style="color:#bbb;font-size:13px;margin-bottom:8px">No post saved</p>') +
    '</div>' +

    '<div class="section">' +
      '<div class="lbl">Caption <span class="sublbl">paste a different caption, then Regenerate</span></div>' +
      '<textarea id="cap-area" oninput="onCapInput(' + idx + ')">' + e(it.caption || '') + '</textarea>' +
    '</div>' +

    '<div class="section">' +
      '<div class="ch">' +
        '<div class="lbl">Comment</div>' +
        '<span class="cc" id="cc">' + it.comment.length + ' chars</span>' +
      '</div>' +
      '<textarea id="com-area" oninput="onComInput()"' + (posted ? ' class="readonly-look" readonly' : '') + '>' + e(it.comment) + '</textarea>' +
    '</div>' +

    '<div class="brow">' +
      '<button class="btn purple" onclick="openIG(' + idx + ')">Open Profile (DM)</button>' +
      '<button class="btn teal"   onclick="copyDM1(' + idx + ')">Copy DM 1</button>' +
      '<button class="btn blue"   onclick="copyDM2()">Copy DM 2</button>' +
    '</div>' +
    (!posted ?
    '<div class="brow">' +
      '<button class="btn teal" onclick="regenerate(' + idx + ')">\u2726 Regenerate Comment</button>' +
      '<button class="btn gray" onclick="resetComment(' + idx + ')">\u21ba Reset</button>' +
    '</div>' : '') +

    '<div class="brow">' +
      '<button class="btn gray" onclick="cPrev()" ' + (idx === 0 ? 'disabled' : '') + '>\u2190 Previous</button>' +
      (!posted
        ? '<button class="btn gray"  onclick="cSkip(' + idx + ')">Skip</button>' +
          '<button class="btn green" onclick="markDone(' + idx + ')">Done \u2713</button>'
        : '<button class="btn gray"  onclick="showC(' + Math.min(idx+1, CQ.length-1) + ')">Next \u2192</button>') +
    '</div>' +

    '</div>';

  if(!posted){
    document.getElementById('com-area').addEventListener('blur', function(){ saveCommentSilent(idx); });
  }
}

function onCapInput(idx){
  var el = document.getElementById('cap-area');
  if(el && CQ[idx]) CQ[idx].caption = el.value;
}
function onComInput(){
  var b = document.getElementById('com-area');
  if(b) document.getElementById('cc').textContent = b.value.length + ' chars';
}

async function saveCommentSilent(idx){
  var it = CQ[idx]; if(!it) return;
  var t = (document.getElementById('com-area') || {}).value;
  if(!t) return; t = t.trim();
  if(t === it.comment) return;
  await fetch('/api/save-comment', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({row: it.row, comment: t})});
  CQ[idx].comment = t;
}

async function copyDM1(idx){
  var it = CQ[idx]; if(!it) return;
  var t = it.dm1 || '';
  if(!t){ toast('No DM Part 1 for this account', true); return; }
  await navigator.clipboard.writeText(t);
  toast('Copied DM Part 1!');
}

async function copyDM2(){
  var t = "We'd truly love to invite you to try CAIT. Hearing how it's helped other medical families has meant the world to us, and we'd be honored to see if it could make even a small difference for yours. If you're open to it, we'd also love to hear your honest feedback and collaborate with you along the way, we provide an honorarium for those who participate.\n\nNo pressure at all, we just hope CAIT can be one less thing for you to worry about. Sending you and your family so much love. 💙";
  await navigator.clipboard.writeText(t);
  toast('Copied DM Part 2!');
}

function openIG(idx){ window.open(CQ[idx].ig_link, '_blank'); }
function openURL(url){ window.open(url, '_blank'); }

function resetComment(idx){
  var orig = COrigs[CQ[idx].row] || CQ[idx].comment;
  var b = document.getElementById('com-area');
  if(b){ b.value = orig; onComInput(); toast('Reset to original'); }
}

async function markDone(idx){
  stopPoll();
  var it = CQ[idx];
  var comment = ((document.getElementById('com-area') || {}).value || '').trim() || it.comment;
  var r = await fetch('/api/mark-posted', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({row: it.row, comment: comment})});
  if(!r.ok){ toast('Sheet update failed', true); return; }
  CDone.add(it.row);
  toast('Done \u2713 \u2014 sheet updated');
  var next = idx + 1;
  while(next < CQ.length && CDone.has(CQ[next].row)) next++;
  if(CQ.length - CDone.size === 0){ prog(); allDone('All accounts done!'); }
  else if(next < CQ.length){ showC(next); }
  else{ var f = CQ.findIndex(function(x){ return !CDone.has(x.row); }); showC(f >= 0 ? f : 0); }
}

function cPrev(){ if(CIdx > 0){ stopPoll(); showC(CIdx - 1); } }

function cSkip(idx){
  stopPoll();
  var n = CQ.length, next = (idx + 1) % n, tries = 0;
  while(CDone.has(CQ[next].row) && tries++ < n) next = (next + 1) % n;
  if(next !== idx) showC(next);
}

async function regenerate(idx){
  var it = CQ[idx];
  var caption = (document.getElementById('cap-area') || {}).value || it.caption || '';
  await fetch('/api/request-action', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      action:   'change_comment',
      handle:   it.handle,
      row:      it.row,
      caption:  caption.trim(),
      post_url: it.post_url || '',
      seen_urls: [],
    })});
  var b = document.getElementById('ban');
  var m = document.getElementById('banmsg');
  if(b && m){ m.textContent = '\u26a1 Go to Claude Code and say "handle request"'; b.classList.add('on'); }
  startPoll(idx);
}

function startPoll(idx){
  stopPoll();
  poll = setInterval(async function(){
    var d = await fetch('/api/check-result').then(function(r){ return r.json(); });
    if(!d.ready) return;
    if(d.row !== CQ[idx].row) return;
    stopPoll();
    var b = document.getElementById('ban'); if(b) b.classList.remove('on');
    await fetch('/api/clear-result', {method:'POST'});
    if(d.status === 'error'){ toast(d.error || 'Error', true); return; }
    if(d.comment){
      var tb = document.getElementById('com-area');
      if(tb){ tb.value = d.comment; onComInput(); }
      CQ[idx].comment = d.comment;
      await fetch('/api/save-comment', {method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({row: CQ[idx].row, comment: d.comment})});
      toast('New comment ready!');
    }
  }, 2000);
}
function stopPoll(){ if(poll){ clearInterval(poll); poll = null; } }

// ── VALIDATION TAB ─────────────────────────────────────────────────────────────
async function refreshVQ(){
  try {
    var r = await fetch('/api/reload-vq').then(function(x){ return x.json(); });
    if(!r.ok) return;
    var cr = await fetch('/api/vq').then(function(x){ return x.json(); });
    VQ = cr; VDone = new Set(); VIdx = 0;
    toast('Validation refreshed — ' + VQ.length + ' pending');
    showV(0);
  } catch(err) { toast('Refresh failed', true); }
}

function showV(idx){
  if(VQ.length === 0){ allDone('No accounts to validate.'); return; }
  idx = Math.max(0, Math.min(idx, VQ.length - 1));
  VIdx = idx; prog();
  var it = VQ[idx];
  var done = VDone.has(it.row);
  var verdict = it._v || '';

  document.getElementById('app').innerHTML =
    '<div class="card">' +
    '<div class="hr2">' +
      '<div class="hn">' + e(it.handle) + '</div>' +
      (verdict === 'APPROVE'   ? '<span class="badge bg">\u2713 Approved</span>'  : '') +
      (verdict === 'Not Valid' ? '<span class="badge br">\u2717 Not Valid</span>' : '') +
      (!done                   ? '<span class="badge bo">Pending</span>'          : '') +
    '</div>' +
    '<div class="pills">' +
      (it.category ? '<span class="pill">\ud83d\udcc2 ' + e(it.category) + '</span>' : '') +
      (it.hashtag  ? '<span class="pill">#' + e(it.hashtag) + '</span>'             : '') +
      (it.display  ? '<span class="pill">\ud83d\udc64 ' + e(it.display) + '</span>' : '') +
      '<span class="pill">' + (idx+1) + ' of ' + VQ.length + '</span>' +
    '</div>' +
    '<div style="margin-bottom:14px">' +
      '<button class="opbtn" onclick="openURL(\'' + e(it.ig_link) + '\')">&#128279; Open Profile &#8599;</button>' +
    '</div>' +
    '<div class="brow">' +
      '<button class="btn green" onclick="vAct(' + idx + ',\'APPROVE\')"   ' + (done ? 'disabled' : '') + '>\u2713 Approve</button>' +
      '<button class="btn red"   onclick="vAct(' + idx + ',\'Not Valid\')" ' + (done ? 'disabled' : '') + '>\u2717 Not Valid</button>' +
    '</div>' +
    '<div class="brow">' +
      '<button class="btn gray" onclick="vPrev()" ' + (idx === 0 ? 'disabled' : '') + '>\u2190 Previous</button>' +
      '<button class="btn gray" onclick="vSkip(' + idx + ')">Skip</button>' +
    '</div>' +
    '<div style="margin-top:8px;text-align:center">' +
      '<button class="refresh-btn" onclick="refreshVQ()">\u21bb Refresh from sheet</button>' +
    '</div>' +
    '</div>';
}

async function vAct(idx, verdict){
  var it = VQ[idx];
  var r = await fetch('/api/mark-validation', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({row: it.row, verdict: verdict})});
  if(!r.ok){ toast('Sheet update failed', true); return; }
  VQ[idx]._v = verdict; VDone.add(it.row);
  toast(verdict === 'APPROVE' ? 'Approved \u2713' : 'Marked Not Valid');
  var next = idx + 1;
  while(next < VQ.length && VDone.has(VQ[next].row)) next++;
  if(VQ.length - VDone.size === 0){ prog(); allDone('All validated!'); }
  else if(next < VQ.length){ showV(next); }
  else{ var f = VQ.findIndex(function(x){ return !VDone.has(x.row); }); showV(f >= 0 ? f : 0); }
}
function vPrev(){ if(VIdx > 0) showV(VIdx - 1); }
function vSkip(idx){
  var n = VQ.length, next = (idx + 1) % n, tries = 0;
  while(VDone.has(VQ[next].row) && tries++ < n) next = (next + 1) % n;
  if(next !== idx) showV(next);
}

// ── EMAIL TAB ──────────────────────────────────────────────────────────────────
async function refreshEQ(){
  try {
    var r = await fetch('/api/reload-eq').then(function(x){ return x.json(); });
    if(!r.ok) return;
    var er = await fetch('/api/eq').then(function(x){ return x.json(); });
    EQ = er; EDone = new Set(); EIdx = 0; EQLoaded = true;
    toast('Email refreshed — ' + EQ.length + ' pending');
    showE(0);
  } catch(err) { toast('Refresh failed', true); }
}

function showE(idx){
  if(EQ.length === 0){ allDone('No accounts to DM yet.'); return; }
  idx = Math.max(0, Math.min(idx, EQ.length - 1));
  EIdx = idx; prog();
  var it = EQ[idx];
  var done = EDone.has(it.row);

  document.getElementById('app').innerHTML =
    '<div class="card">' +
    '<div class="hr2">' +
      '<div class="hn">@' + e(it.handle) + '</div>' +
      (done ? '<span class="badge bg">\u2713 DM Sent</span>' : '<span class="badge bo">Emailed</span>') +
    '</div>' +
    (it.email ? '<div style="font-size:13px;color:#888;margin-bottom:10px">&#9993; ' + e(it.email) + '</div>' : '') +
    (it.notes ? '<div style="font-size:12px;color:#aaa;margin-bottom:12px">' + e(it.notes) + '</div>' : '') +
    '<div style="margin-bottom:14px;display:flex;align-items:center;gap:10px;flex-wrap:wrap">' +
      '<button class="opbtn" onclick="openURL(\'' + e(it.ig_link) + '\')">&#128279; Open Profile &#8599;</button>' +
      (it.diagnosis ? '<span style="font-size:13px;color:#fff;background:#5a6a8a;padding:4px 10px;border-radius:12px;font-weight:600">' + e(it.diagnosis) + '</span>' : '') +
    '</div>' +
    '<div class="brow">' +
      '<button class="btn green" onclick="eDone(' + idx + ')" ' + (done ? 'disabled' : '') + '>\u2713 DM Sent</button>' +
      '<button class="btn gray"  onclick="eSkip(' + idx + ')">Skip</button>' +
    '</div>' +
    '<div class="brow">' +
      '<button class="btn gray" onclick="ePrev()" ' + (idx === 0 ? 'disabled' : '') + '>\u2190 Previous</button>' +
    '</div>' +
    '<div style="margin-top:8px;text-align:center">' +
      '<button class="refresh-btn" onclick="refreshEQ()">\u21bb Refresh from sheet</button>' +
    '</div>' +
    '</div>';
}

async function eDone(idx){
  var it = EQ[idx];
  var r = await fetch('/api/mark-dm-sent', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({row: it.row})});
  if(!r.ok){ toast('Sheet update failed', true); return; }
  EDone.add(it.row);
  toast('DM Sent \u2713 — sheet updated');
  var next = idx + 1;
  while(next < EQ.length && EDone.has(EQ[next].row)) next++;
  if(EQ.length - EDone.size === 0){ prog(); allDone('All DMs sent!'); }
  else if(next < EQ.length){ showE(next); }
  else{ var f = EQ.findIndex(function(x){ return !EDone.has(x.row); }); showE(f >= 0 ? f : 0); }
}
function ePrev(){ if(EIdx > 0) showE(EIdx - 1); }
function eSkip(idx){
  var n = EQ.length, next = (idx + 1) % n, tries = 0;
  while(EDone.has(EQ[next].row) && tries++ < n) next = (next + 1) % n;
  if(next !== idx) showE(next);
}

// ── SHARE POST TAB ─────────────────────────────────────────────────────────────
function showS(){
  var postUrl = document.getElementById('_surl') ? document.getElementById('_surl').value : '';
  var tot = SQ.length;

  var rows = '';
  SQ.forEach(function(it, idx){
    rows +=
      '<div class="share-row" id="srow-' + it.row + '" style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #f0f0f0">' +
        '<div style="flex:1;font-size:15px;font-weight:600;color:#1d1d1f">' +
          e(it.handle) +
        '</div>' +
        '<button class="btn blue" style="flex:0 0 auto;min-width:90px;padding:8px 12px;font-size:13px" onclick="sCopy(' + idx + ')">' +
          'Copy' +
        '</button>' +
        '<button class="btn green" style="flex:0 0 auto;min-width:80px;padding:8px 12px;font-size:13px" onclick="sDone(' + idx + ')">' +
          'Done' +
        '</button>' +
      '</div>';
  });

  if(SQ.length === 0){
    rows = '<p style="color:#bbb;text-align:center;padding:24px">All shared! \u2713</p>';
  }

  document.getElementById('app').innerHTML =
    '<div class="card" style="max-width:720px">' +
    '<div style="margin-bottom:16px">' +
      '<div class="lbl" style="margin-bottom:6px">Post URL to share</div>' +
      '<div style="display:flex;gap:8px">' +
        '<input id="_surl" type="text" placeholder="Paste your post URL here..." value="' + e(postUrl) + '" ' +
          'style="flex:1;border:1.5px solid #e0e0e0;border-radius:10px;padding:10px;font-size:13px;font-family:inherit" ' +
          'oninput="document.getElementById(\'_surlbtn\').style.display=this.value?\'block\':\'none\'">' +
        '<button id="_surlbtn" class="btn blue" style="flex:0 0 auto;min-width:100px;display:' + (postUrl ? 'block' : 'none') + '" ' +
          'onclick="openURL(document.getElementById(\'_surl\').value)">Open Post \u2197</button>' +
      '</div>' +
      '<div style="font-size:12px;color:#aaa;margin-top:6px">Go to this post on Instagram, click Share, then use Copy below to paste the username. Click Done to remove from this list.</div>' +
    '</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">' +
      '<div style="font-size:13px;color:#888">' + tot + ' remaining</div>' +
      '<button class="refresh-btn" onclick="reloadSQ()">&#8635; Refresh</button>' +
    '</div>' +
    rows +
    '</div>';

  prog();
}

async function sCopy(idx){
  var it = SQ[idx];
  await navigator.clipboard.writeText(it.handle);
  toast('Copied @' + it.handle);
}

function sDone(idx){
  SQ.splice(idx, 1);
  showS();
}

async function reloadSQ(){
  try {
    var r = await fetch('/api/reload-sq').then(function(x){ return x.json(); });
    if(r.ok){
      var sr = await fetch('/api/sq').then(function(x){ return x.json(); });
      SQ = sr;
      showS();
      toast('Share list refreshed');
    }
  } catch(err) { toast('Reload failed', true); }
}

// ── REVIEW TAB ─────────────────────────────────────────────────────────────────
var ShareURL = '';

async function loadShareURL(){
  try {
    var r = await fetch('/api/get-share-url').then(function(x){ return x.json(); });
    if(r.ok) ShareURL = r.url || '';
  } catch(err) {}
}

function evHTML(ev){
  if(!ev) return '';
  var safe = e(ev).replace(/(https?:\/\/[^\s]+)/g,
    '<a href="$1" target="_blank" style="color:#007aff">post ↗</a>');
  return '<div style="background:#f4f8ff;border:1px solid #d8e6ff;border-radius:10px;padding:9px 11px;font-size:12px;color:#456;line-height:1.5;margin-bottom:10px"><b style="color:#007aff">Why it qualified:</b><br>' + safe + '</div>';
}

function showR(){
  var pend = CQ.filter(function(x){ return !CDone.has(x.row); });
  prog();
  if(pend.length === 0){ allDone('Nothing to review — queue is empty.'); return; }

  var cards = '';
  pend.forEach(function(it){
    var approved = it.approval === 'Approved';
    cards +=
      '<div class="card" style="margin-bottom:14px;max-width:680px" id="rcard-' + it.row + '">' +
      '<div class="hr2">' +
        '<div class="hn" style="font-size:17px">' + e(it.handle) + '</div>' +
        (approved ? '<span class="badge bg">✓ Approved</span>' : '<span class="badge bo">Pending</span>') +
        (it.sensitive ? '<span class="badge br">⚠ SENSITIVE</span>' : '') +
      '</div>' +
      evHTML(it.evidence) +
      '<div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap">' +
        (it.post_url ? '<button class="opbtn" style="margin-bottom:0" onclick="openURL(\'' + e(it.post_url) + '\')">&#128279; Post ↗</button>' : '') +
        '<button class="opbtn" style="margin-bottom:0" onclick="openURL(\'' + e(it.ig_link) + '\')">&#128100; Profile ↗</button>' +
      '</div>' +
      '<div class="section" style="margin-bottom:10px">' +
        '<div class="lbl">Comment</div>' +
        '<textarea id="rc-' + it.row + '" style="min-height:80px" onblur="rSave(' + it.row + ')">' + e(it.comment) + '</textarea>' +
      '</div>' +
      '<div class="section" style="margin-bottom:10px">' +
        '<div class="lbl">DM 1</div>' +
        '<textarea id="rd-' + it.row + '" style="min-height:110px" onblur="rSave(' + it.row + ')">' + e(it.dm1 || '') + '</textarea>' +
      '</div>' +
      '<div class="brow" style="margin-bottom:0">' +
        (approved
          ? '<button class="btn gray"  onclick="rApprove(' + it.row + ', false)">Un-approve</button>'
          : '<button class="btn green" onclick="rApprove(' + it.row + ', true)">✓ Approve</button>') +
      '</div>' +
      '</div>';
  });

  document.getElementById('app').innerHTML =
    '<div class="card" style="margin-bottom:14px;max-width:680px">' +
      '<div class="lbl" style="margin-bottom:6px">Post URL to share in DMs (once per batch)</div>' +
      '<div style="display:flex;gap:8px;margin-bottom:12px">' +
        '<input id="rsurl" type="text" placeholder="Paste post URL to share..." value="' + e(ShareURL) + '" ' +
          'style="flex:1;border:1.5px solid #e0e0e0;border-radius:10px;padding:10px;font-size:13px;font-family:inherit">' +
        '<button class="btn blue" style="flex:0 0 auto;min-width:70px" onclick="rSaveShareURL()">Save</button>' +
      '</div>' +
      '<div class="brow" style="margin-bottom:0">' +
        '<button class="btn green" onclick="rApproveAll()">✓ Approve All (' + pend.length + ')</button>' +
        '<button class="btn gray" style="flex:0 0 auto" onclick="rRefresh()">↻ Refresh</button>' +
      '</div>' +
    '</div>' + cards;
}

async function rSave(row){
  var it = CQ.find(function(x){ return x.row === row; }); if(!it) return;
  var c = (document.getElementById('rc-' + row) || {}).value;
  var d = (document.getElementById('rd-' + row) || {}).value;
  if(c === undefined && d === undefined) return;
  if((c === undefined || c.trim() === it.comment) && (d === undefined || d.trim() === (it.dm1 || ''))) return;
  try {
    await fetch('/api/save-review', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({row: row, comment: c, dm1: d})});
    if(c !== undefined) it.comment = c.trim();
    if(d !== undefined) it.dm1 = d.trim();
    toast('Saved');
  } catch(err) { toast('Save failed', true); }
}

async function rApprove(row, state){
  var it = CQ.find(function(x){ return x.row === row; }); if(!it) return;
  await rSave(row);
  try {
    var r = await fetch('/api/approve', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({row: row, approved: state})});
    if(!r.ok){ toast('Sheet update failed', true); return; }
    it.approval = state ? 'Approved' : '';
    toast(state ? 'Approved ✓' : 'Un-approved');
    showR();
  } catch(err) { toast('Failed', true); }
}

async function rApproveAll(){
  var pend = CQ.filter(function(x){ return !CDone.has(x.row) && x.approval !== 'Approved'; });
  if(pend.length === 0){ toast('Everything already approved'); return; }
  if(!confirm('Approve all ' + pend.length + ' accounts? Playwright will post + DM all of them.')) return;
  try {
    var r = await fetch('/api/approve-all', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({rows: pend.map(function(x){ return x.row; })})});
    var j = await r.json();
    if(!j.ok && !j.count){ toast('Sheet update failed', true); return; }
    pend.forEach(function(x){ x.approval = 'Approved'; });
    toast('All approved ✓ (' + pend.length + ')');
    showR();
  } catch(err) { toast('Failed', true); }
}

async function rSaveShareURL(){
  var v = (document.getElementById('rsurl') || {}).value || '';
  try {
    var r = await fetch('/api/set-share-url', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({url: v.trim()})});
    var j = await r.json();
    if(j.ok){ ShareURL = v.trim(); toast('Share URL saved'); }
    else toast(j.error || 'Failed', true);
  } catch(err) { toast('Failed', true); }
}

async function rRefresh(){
  try {
    var r = await fetch('/api/reload-cq').then(function(x){ return x.json(); });
    if(!r.ok){ toast('Reload failed', true); return; }
    var cr = await fetch('/api/cq').then(function(x){ return x.json(); });
    CQ = cr;
    CQ.forEach(function(x){ if(!(x.row in COrigs)) COrigs[x.row] = x.comment; });
    await loadShareURL();
    toast('Refreshed — ' + CQ.length + ' in queue');
    showR();
  } catch(err) { toast('Refresh failed', true); }
}

// ── ADD LINKS TAB ──────────────────────────────────────────────────────────────
function showA(){
  prog();
  document.getElementById('app').innerHTML =
    '<div class="card" style="max-width:680px">' +
    '<div class="lbl" style="margin-bottom:6px">Paste Instagram links (profiles or posts, any amount)</div>' +
    '<textarea id="alinks" style="min-height:160px;font-size:14px" placeholder="https://www.instagram.com/somehandle/\nhttps://www.instagram.com/reel/ABC123/\n..."></textarea>' +
    '<div class="brow" style="margin-top:10px;margin-bottom:0">' +
      '<button class="btn blue" id="abtn" onclick="aSubmit()">Add to Queue</button>' +
    '</div>' +
    '<div id="ares" style="margin-top:12px;font-size:13px;color:#555"></div>' +
    '<div style="font-size:12px;color:#aaa;margin-top:10px">Profile links are added with the handle. Post/reel links are saved too — Claude resolves the account during the next batch run. Duplicates are skipped automatically.</div>' +
    '</div>';
}

async function aSubmit(){
  var ta = document.getElementById('alinks');
  var btn = document.getElementById('abtn');
  var txt = (ta && ta.value || '').trim();
  if(!txt){ toast('Paste some links first', true); return; }
  btn.disabled = true; btn.textContent = 'Adding...';
  try {
    var r = await fetch('/api/add-links', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({links: txt})});
    var j = await r.json();
    if(!j.ok){ toast(j.error || 'Failed', true); }
    else {
      toast('Added ' + j.added + (j.skipped ? ' (' + j.skipped + ' duplicates skipped)' : ''));
      ta.value = '';
      var res = document.getElementById('ares');
      if(res && j.items && j.items.length){
        res.innerHTML = '<b>Added:</b><br>' + j.items.map(function(x){ return e(x); }).join('<br>');
      }
    }
  } catch(err) { toast('Request failed', true); }
  btn.disabled = false; btn.textContent = 'Add to Queue';
}

// ── shared ─────────────────────────────────────────────────────────────────────
function allDone(msg){
  prog();
  document.getElementById('app').innerHTML =
    '<div class="card done-card"><h2>\ud83c\udf89</h2><p>' + msg + '</p>' +
    '<br><button class="btn gray" style="max-width:200px;margin:0 auto" onclick="refreshQueue()">\u21bb Refresh</button>' +
    '</div>';
}
function toast(msg, err){
  var t = document.getElementById('toast');
  t.textContent = msg; t.className = 'toast' + (err ? ' err' : '');
  t.classList.add('on');
  setTimeout(function(){ t.classList.remove('on'); }, 2500);
}
function e(s){
  return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

boot();
</script>
</body>
</html>"""

# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    global gc_client, ws_c, ws_v, ws_e, cq, cc, vq, vc, eq, ec, sq

    print("Connecting to Google Sheets...")
    gc_client          = make_gc()
    ws_c, ws_v, ws_e   = open_sheets(gc_client)
    cq, cc             = read_comments(ws_c)
    vq, vc             = read_validation(ws_v)
    eq, ec             = read_email(ws_e)
    sq                 = read_share(ws_c)

    print(f"Comments queue : {len(cq)} accounts")
    print(f"Validation     : {len(vq)} accounts pending")
    print(f"Email DM queue : {len(eq)} accounts")
    print(f"Share Post     : {len(sq)} accounts")
    print(f"Opening http://localhost:{PORT} ...")

    # Keep-alive ping — prevents Render free tier from sleeping
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        def _ping():
            # Wait for Flask to finish starting, then ping immediately
            time.sleep(5)
            while True:
                try:
                    requests.get(RENDER_URL, timeout=10)
                except Exception:
                    pass
                time.sleep(840)  # every 14 minutes
        threading.Thread(target=_ping, daemon=True).start()

    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

if __name__ == "__main__":
    main()
