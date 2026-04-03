"""
daily_runner.py
---------------
Click-through browser UI for the daily CAIT workflow.

  Comments tab  — work through accounts, copy comment, mark Done
  Validation tab — approve / reject Medical Mom DM Outreach accounts

Usage:
  python scripts/daily_runner.py

Opens http://localhost:5560 automatically.

Change Post / Regenerate Comment:
  - Click the button in the browser
  - Runner writes outputs/runner_request.json
  - Go to Claude Code and say "handle request"
  - Claude writes outputs/runner_result.json
  - Runner auto-updates within 2 seconds
"""

import os
import json
import time
import datetime
import threading
import webbrowser

import gspread
from flask import Flask, jsonify, request, render_template_string
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

GOOGLE_SHEET_ID   = os.environ.get("GOOGLE_SHEET_ID")
GOOGLE_CREDS_PATH = os.environ.get("GOOGLE_CREDS_PATH")
BASE_DIR          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS_DIR       = os.path.join(BASE_DIR, "outputs")
POST_OPTIONS_JSON = os.path.join(OUTPUTS_DIR, "post_options.json")
RUNNER_REQUEST    = os.path.join(OUTPUTS_DIR, "runner_request.json")
RUNNER_RESULT     = os.path.join(OUTPUTS_DIR, "runner_result.json")

app = Flask(__name__)

# ── Sheet helpers ──────────────────────────────────────────────────────────────

def open_sheets():
    creds = Credentials.from_service_account_file(
        GOOGLE_CREDS_PATH,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(GOOGLE_SHEET_ID)
    return ss.worksheet("COMMENTS"), ss.worksheet("Medical Mom DM Outreach")


def load_comments_queue(ws):
    rows = ws.get_all_values()
    if not rows:
        return [], {}
    headers = [h.strip() for h in rows[0]]
    hi = {h: i for i, h in enumerate(headers)}

    if "Runner Status" not in hi:
        next_col = len(headers) + 1
        ws.update_cell(1, next_col, "Runner Status")
        headers.append("Runner Status")
        hi["Runner Status"] = len(headers) - 1
        print("Added 'Runner Status' column.")

    queue = []
    for i, row in enumerate(rows[1:], start=2):
        def cell(col, r=row):
            idx = hi.get(col)
            return r[idx].strip() if idx is not None and idx < len(r) else ""

        handle   = cell("Handle")
        comment  = cell("Generated Comment")
        post_url = cell("Post URL")
        caption  = cell("Post Caption")
        ig_link  = cell("IG Profile Link")
        notes    = cell("Notes")
        status   = cell("Runner Status")

        if handle and comment and status != "Posted":
            if not ig_link:
                clean = handle.lstrip("@").lower().strip()
                ig_link = f"https://www.instagram.com/{clean}/"
            queue.append({
                "row":       i,
                "handle":    handle,
                "ig_link":   ig_link,
                "post_url":  post_url,
                "caption":   caption[:600] if caption else "",
                "comment":   comment,
                "notes":     notes,
                "sensitive": "[SENSITIVE" in notes,
            })

    col_map = {h: j + 1 for j, h in enumerate(headers)}
    return queue, col_map


def load_validation_queue(ws):
    rows = ws.get_all_values()
    if not rows:
        return [], {}
    headers = [h.strip() for h in rows[0]]
    hi = {h: i for i, h in enumerate(headers)}

    col_map = {h: j + 1 for j, h in enumerate(headers)}
    queue = []
    for i, row in enumerate(rows[1:], start=2):
        def cell(col, r=row):
            idx = hi.get(col)
            return r[idx].strip() if idx is not None and idx < len(r) else ""

        handle   = cell("Handle")
        notes    = cell("Notes")
        category = cell("Category")
        ig_link  = cell("IG Profile Link")
        hashtag  = cell("Source Hashtag")
        display  = cell("Display Name")

        # Only show accounts not yet reviewed
        if handle and notes == "":
            if not ig_link:
                clean = handle.lstrip("@").lower().strip()
                ig_link = f"https://www.instagram.com/{clean}/"
            queue.append({
                "row":      i,
                "handle":   handle,
                "ig_link":  ig_link,
                "category": category,
                "hashtag":  hashtag,
                "display":  display,
            })

    return queue, col_map


def load_post_options():
    if os.path.exists(POST_OPTIONS_JSON):
        with open(POST_OPTIONS_JSON, encoding="utf-8") as f:
            return json.load(f)
    return {}


# ── Global state ───────────────────────────────────────────────────────────────

ws_comments    = None
ws_outreach    = None
comments_q     = []
comments_cols  = {}
validation_q   = []
validation_cols = {}
post_options   = {}


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/comments-queue")
def api_comments_queue():
    return jsonify({"queue": comments_q})


@app.route("/api/validation-queue")
def api_validation_queue():
    return jsonify({"queue": validation_q})


@app.route("/api/post-options/<handle>")
def api_post_options(handle):
    clean = handle.lstrip("@").lower().strip()
    data  = post_options.get(clean, {})
    if isinstance(data, list):
        return jsonify({"selected": None, "alternatives": data})
    return jsonify(data)


@app.route("/api/save-comment", methods=["POST"])
def api_save_comment():
    data        = request.json
    row_num     = int(data["row"])
    new_comment = data["comment"].strip()
    col         = comments_cols.get("Generated Comment")
    if col:
        ws_comments.update_cell(row_num, col, new_comment)
        for item in comments_q:
            if item["row"] == row_num:
                item["comment"] = new_comment
    return jsonify({"ok": True})


@app.route("/api/save-post", methods=["POST"])
def api_save_post():
    data     = request.json
    row_num  = int(data["row"])
    post_url = data["post_url"].strip()
    caption  = data["caption"].strip()
    cells    = []
    url_col  = comments_cols.get("Post URL")
    cap_col  = comments_cols.get("Post Caption")
    if url_col: cells.append(gspread.Cell(row_num, url_col, post_url))
    if cap_col: cells.append(gspread.Cell(row_num, cap_col, caption))
    if cells:   ws_comments.update_cells(cells, value_input_option="USER_ENTERED")
    for item in comments_q:
        if item["row"] == row_num:
            item["post_url"] = post_url
            item["caption"]  = caption[:600]
    return jsonify({"ok": True})


@app.route("/api/mark-posted", methods=["POST"])
def api_mark_posted():
    data    = request.json
    row_num = int(data["row"])
    comment = data.get("comment", "").strip()

    cells = []
    status_col  = comments_cols.get("Runner Status")
    comment_col = comments_cols.get("Generated Comment")
    if status_col:
        now_dt = datetime.datetime.now()
        now    = f"Posted {now_dt.day} {now_dt.strftime('%b')}"
        cells.append(gspread.Cell(row_num, status_col, now))
    if comment_col and comment:
        cells.append(gspread.Cell(row_num, comment_col, comment))
    if cells:
        ws_comments.update_cells(cells, value_input_option="USER_ENTERED")

    return jsonify({"ok": True})


@app.route("/api/mark-validation", methods=["POST"])
def api_mark_validation():
    data    = request.json
    row_num = int(data["row"])
    verdict = data["verdict"]   # "APPROVE" or "Not Valid"

    notes_col = validation_cols.get("Notes")
    if notes_col:
        ws_outreach.update_cell(row_num, notes_col, verdict)
    return jsonify({"ok": True})


@app.route("/api/request-action", methods=["POST"])
def api_request_action():
    data = request.json
    req  = {
        "id":        str(time.time()),
        "action":    data["action"],
        "handle":    data["handle"],
        "row":       data["row"],
        "caption":   data.get("caption", ""),
        "post_url":  data.get("post_url", ""),
        "seen_urls": data.get("seen_urls", []),
    }
    if os.path.exists(RUNNER_RESULT):
        os.remove(RUNNER_RESULT)
    with open(RUNNER_REQUEST, "w", encoding="utf-8") as f:
        json.dump(req, f, indent=2, ensure_ascii=False)
    return jsonify({"ok": True, "request_id": req["id"]})


@app.route("/api/check-result")
def api_check_result():
    if not os.path.exists(RUNNER_RESULT):
        return jsonify({"ready": False})
    try:
        with open(RUNNER_RESULT, encoding="utf-8") as f:
            result = json.load(f)
        return jsonify({"ready": True, **result})
    except Exception:
        return jsonify({"ready": False})


@app.route("/api/clear-result", methods=["POST"])
def api_clear_result():
    if os.path.exists(RUNNER_RESULT):
        os.remove(RUNNER_RESULT)
    if os.path.exists(RUNNER_REQUEST):
        os.remove(RUNNER_REQUEST)
    return jsonify({"ok": True})


# ── HTML ───────────────────────────────────────────────────────────────────────

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CAIT Runner</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: #f5f5f7; min-height: 100vh; padding: 16px; }

/* ── Tabs ── */
.tabs { display: flex; gap: 6px; justify-content: center; margin-bottom: 14px; }
.tab-btn { border: none; border-radius: 20px; padding: 8px 22px; font-size: 14px;
           font-weight: 600; cursor: pointer; background: #e0e0e0; color: #555; }
.tab-btn.active { background: #007aff; color: white; }

/* ── Header ── */
.header { text-align: center; margin-bottom: 14px; }
.progress-bar { background: #e0e0e0; border-radius: 8px; height: 6px;
                margin: 6px auto; max-width: 360px; overflow: hidden; }
.progress-fill { background: #007aff; height: 100%; border-radius: 8px; transition: width 0.3s; }
.progress-text { font-size: 13px; color: #888; margin-top: 4px; }

/* ── Card ── */
.card { background: white; border-radius: 16px; padding: 20px;
        max-width: 660px; margin: 0 auto; box-shadow: 0 2px 14px rgba(0,0,0,0.08); }

.handle-row { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; }
.handle { font-size: 20px; font-weight: 700; color: #1d1d1f; }
.badge { font-size: 11px; font-weight: 600; padding: 3px 9px; border-radius: 20px; color: white; }
.badge-red    { background: #ff3b30; }
.badge-green  { background: #34c759; }
.badge-blue   { background: #007aff; }
.badge-orange { background: #ff9500; }

.section-label { font-size: 11px; font-weight: 600; color: #aaa;
                 text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }

.post-section { margin-bottom: 14px; }
.post-age { font-size: 13px; font-weight: 600; color: #007aff; margin-bottom: 5px; }
.post-link-btn { display: inline-flex; align-items: center; gap: 6px;
                 background: #f0f0f0; border: none; border-radius: 8px;
                 padding: 7px 13px; font-size: 13px; color: #333; cursor: pointer;
                 margin-bottom: 8px; font-weight: 500; }
.post-link-btn:hover { background: #e5e5e5; }
.caption-box { font-size: 13px; color: #555; line-height: 1.55;
               background: #f9f9f9; border-radius: 8px; padding: 10px 12px;
               max-height: 85px; overflow-y: auto; white-space: pre-wrap; }

.comment-section { margin-bottom: 16px; }
.comment-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
.char-count { font-size: 12px; color: #bbb; }
textarea { width: 100%; border: 1.5px solid #e0e0e0; border-radius: 10px;
           padding: 10px; font-size: 14px; line-height: 1.6; resize: vertical;
           min-height: 95px; font-family: inherit; color: #1d1d1f; transition: border-color 0.2s; }
textarea:focus { outline: none; border-color: #007aff; }
textarea[readonly] { background: #f9f9f9; color: #888; }

/* ── Validation info ── */
.info-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.info-pill { background: #f0f0f0; border-radius: 8px; padding: 5px 10px;
             font-size: 12px; color: #555; font-weight: 500; }

/* ── Buttons ── */
.btn-row { display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 7px; }
.btn { border: none; border-radius: 10px; padding: 11px 14px; font-size: 13px;
       font-weight: 600; cursor: pointer; transition: all 0.15s; flex: 1;
       min-width: 80px; white-space: nowrap; }
.btn:disabled { opacity: 0.35; cursor: not-allowed; }
.btn-blue   { background: #007aff; color: white; }
.btn-blue:hover:not(:disabled)   { background: #0066d6; }
.btn-green  { background: #34c759; color: white; }
.btn-green:hover:not(:disabled)  { background: #2ab34a; }
.btn-red    { background: #ff3b30; color: white; }
.btn-red:hover:not(:disabled)    { background: #d93025; }
.btn-purple { background: #5856d6; color: white; }
.btn-purple:hover:not(:disabled) { background: #4a48c4; }
.btn-orange { background: #ff9500; color: white; }
.btn-orange:hover:not(:disabled) { background: #e08600; }
.btn-teal   { background: #30b0c7; color: white; }
.btn-teal:hover:not(:disabled)   { background: #258da0; }
.btn-gray   { background: #e8e8ed; color: #1d1d1f; }
.btn-gray:hover:not(:disabled)   { background: #d5d5da; }

/* ── Pending banner ── */
.pending-banner { background: #fff3cd; border: 1px solid #ffc107; border-radius: 10px;
                  padding: 12px 14px; margin-bottom: 12px; font-size: 13px;
                  display: none; align-items: center; gap: 10px; }
.pending-banner.show { display: flex; }
.pending-dot { width: 10px; height: 10px; border-radius: 50%; background: #ff9500;
               animation: pulse 1s infinite; flex-shrink: 0; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* ── Toast ── */
.toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
         background: #1d1d1f; color: white; padding: 10px 20px; border-radius: 20px;
         font-size: 13px; opacity: 0; transition: opacity 0.25s;
         pointer-events: none; z-index: 999; white-space: nowrap; }
.toast.show { opacity: 1; }
.toast.error { background: #ff3b30; }

.center-msg { text-align: center; padding: 60px 20px; }
.center-msg h2 { font-size: 24px; margin-bottom: 10px; }
.center-msg p  { color: #888; font-size: 14px; }
</style>
</head>
<body>

<div class="tabs">
  <button class="tab-btn active" id="tabComments"    onclick="switchTab('comments')">Comments</button>
  <button class="tab-btn"        id="tabValidation"  onclick="switchTab('validation')">Validation</button>
</div>

<div class="header">
  <div class="progress-bar"><div class="progress-fill" id="progressFill" style="width:0%"></div></div>
  <div class="progress-text" id="progressText">Loading...</div>
</div>

<div id="app"><div class="center-msg"><p>Loading...</p></div></div>
<div class="toast" id="toast"></div>

<script>
// ── Shared state ──────────────────────────────────────────────────────────────
let activeTab = 'comments';

// ── Comments state ────────────────────────────────────────────────────────────
let cQueue        = [];   // full list, never spliced
let cDoneRows     = new Set();
let cCurrentIdx   = 0;
let cOrigComments = {};
let cSeenUrls     = {};
let postOptions   = {};
let pendingPoll   = null;

// ── Validation state ──────────────────────────────────────────────────────────
let vQueue      = [];
let vDoneRows   = new Set();
let vCurrentIdx = 0;

// ── Tab switching ─────────────────────────────────────────────────────────────
function switchTab(tab) {
  activeTab = tab;
  document.getElementById('tabComments').classList.toggle('active',   tab === 'comments');
  document.getElementById('tabValidation').classList.toggle('active', tab === 'validation');
  if (tab === 'comments')   showCommentCard(cCurrentIdx);
  else                      showValidationCard(vCurrentIdx);
}

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
  const [cr, vr] = await Promise.all([
    fetch('/api/comments-queue').then(r => r.json()),
    fetch('/api/validation-queue').then(r => r.json()),
  ]);
  cQueue = cr.queue;
  vQueue = vr.queue;

  cQueue.forEach(item => {
    cOrigComments[item.row] = item.comment;
    if (!cSeenUrls[item.handle]) cSeenUrls[item.handle] = [];
    if (item.post_url) cSeenUrls[item.handle].push(item.post_url);
  });

  showCommentCard(0);
}

// ── Progress ──────────────────────────────────────────────────────────────────
function updateProgress() {
  let done, total;
  if (activeTab === 'comments') {
    done  = cDoneRows.size;
    total = cQueue.length;
  } else {
    done  = vDoneRows.size;
    total = vQueue.length;
  }
  const remaining = total - done;
  const pct = total > 0 ? (done / total) * 100 : 0;
  document.getElementById('progressFill').style.width = pct + '%';
  document.getElementById('progressText').textContent =
    remaining > 0 ? `${done + 1} of ${total} — ${remaining} remaining` : `All ${total} done ✓`;
}

// ── Time helpers ──────────────────────────────────────────────────────────────
function shortcodeToTimestamp(url) {
  const m = (url || '').match(/\/(?:p|reel|tv)\/([A-Za-z0-9_-]+)/);
  if (!m) return 0;
  const alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
  let id = BigInt(0);
  for (const ch of m[1]) {
    const i = alpha.indexOf(ch);
    if (i === -1) return 0;
    id = id * BigInt(64) + BigInt(i);
  }
  const ts = Number(id >> BigInt(23));
  const now = Math.floor(Date.now() / 1000);
  // Must be between Jan 2010 and 5 years from now
  if (ts < 1262304000 || ts > now + 86400 * 1825) return 0;
  return ts;
}

function timeAgo(ts) {
  if (!ts || ts <= 0) return '';
  const d = Math.floor(Date.now() / 1000) - ts;
  if (d < 0)       return '';
  if (d < 86400)   return Math.max(1, Math.floor(d / 3600)) + 'h ago';
  if (d < 604800)  return Math.floor(d / 86400) + 'd ago';
  if (d < 2592000) return Math.floor(d / 604800) + 'w ago';
  return Math.floor(d / 2592000) + 'mo ago';
}

function ordinal(n) {
  const o = ['Latest post','2nd latest','3rd latest','4th latest','5th latest'];
  return o[n-1] || n + 'th latest';
}

// ── Post options ──────────────────────────────────────────────────────────────
async function getPostOptions(handle) {
  const key = handle.replace(/^@/, '').toLowerCase();
  if (postOptions[key] !== undefined) return postOptions[key];
  const res  = await fetch('/api/post-options/' + encodeURIComponent(handle));
  const data = await res.json();
  postOptions[key] = data;
  return data;
}

// ═══════════════════════════════════════════════════════════════════════════════
// COMMENTS TAB
// ═══════════════════════════════════════════════════════════════════════════════

async function showCommentCard(idx) {
  if (cQueue.length === 0) { showAllDone('Comments'); return; }
  idx = Math.max(0, Math.min(idx, cQueue.length - 1));
  cCurrentIdx = idx;
  stopPolling();
  updateProgress();

  const item     = cQueue[idx];
  const isPosted = cDoneRows.has(item.row);
  const opts     = await getPostOptions(item.handle);

  const postUrl   = item.post_url || '';
  const ts        = (opts.selected && opts.selected.timestamp) || shortcodeToTimestamp(postUrl);
  const age       = timeAgo(ts);
  const rankLabel = opts.selected && opts.selected.rank ? ordinal(opts.selected.rank) : '';
  const postLabel = [rankLabel, age].filter(Boolean).join(' · ');

  document.getElementById('app').innerHTML = `
    <div class="card">
      <div class="handle-row">
        <div class="handle">${esc(item.handle)}</div>
        ${isPosted ? '<span class="badge badge-green">✓ Posted</span>' : ''}
        ${!isPosted && item.sensitive ? '<span class="badge badge-red">⚠ Review first</span>' : ''}
      </div>

      <div id="pendingBanner" class="pending-banner">
        <div class="pending-dot"></div>
        <span id="pendingMsg">Waiting for Claude Code...</span>
      </div>

      <div class="post-section">
        <div class="section-label">Post</div>
        ${postLabel ? `<div class="post-age">${esc(postLabel)}</div>` : ''}
        ${postUrl
          ? `<button class="post-link-btn" onclick="window.open('${esc(postUrl)}','_blank')">🔗 Open Post ↗</button>`
          : '<div style="color:#bbb;font-size:13px;margin-bottom:8px;">No post saved</div>'}
        ${item.caption ? `<div class="caption-box">${esc(item.caption)}</div>` : ''}
      </div>

      <div class="comment-section">
        <div class="comment-header">
          <div class="section-label">Comment</div>
          <span class="char-count" id="charCount">${item.comment.length} chars</span>
        </div>
        <textarea id="commentBox" oninput="onCommentInput()" ${isPosted ? 'readonly' : ''}>${esc(item.comment)}</textarea>
      </div>

      <div class="btn-row">
        <button class="btn btn-purple" onclick="openProfile_c(${idx})">Open Profile (DM)</button>
        <button class="btn btn-blue"   onclick="copyComment(${idx})">Copy Comment</button>
      </div>
      ${!isPosted ? `
      <div class="btn-row">
        <button class="btn btn-orange" onclick="requestAction(${idx},'change_post')">↻ Change Post</button>
        <button class="btn btn-teal"   onclick="requestAction(${idx},'change_comment')">✦ Regenerate</button>
        <button class="btn btn-gray"   onclick="resetComment(${idx})">↺ Reset</button>
      </div>` : ''}
      <div class="btn-row">
        <button class="btn btn-gray"  id="prevBtn" onclick="cPrev()" ${idx === 0 ? 'disabled' : ''}>← Previous</button>
        ${!isPosted
          ? `<button class="btn btn-gray"  onclick="cSkip(${idx})">Skip</button>
             <button class="btn btn-green" onclick="markPosted(${idx})">Done ✓</button>`
          : `<button class="btn btn-gray"  onclick="showCommentCard(${Math.min(idx+1, cQueue.length-1)})">Next →</button>`}
      </div>
    </div>`;

  if (!isPosted) {
    document.getElementById('commentBox').addEventListener('blur', () => saveCommentSilent(idx));
  }
}

function onCommentInput() {
  const b = document.getElementById('commentBox');
  if (b) document.getElementById('charCount').textContent = b.value.length + ' chars';
}

async function saveCommentSilent(idx) {
  const item = cQueue[idx];
  if (!item) return;
  const t = document.getElementById('commentBox')?.value?.trim();
  if (!t || t === item.comment) return;
  await fetch('/api/save-comment', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({row: item.row, comment: t})
  });
  cQueue[idx].comment = t;
}

async function copyComment(idx) {
  await saveCommentSilent(idx);
  const t = document.getElementById('commentBox')?.value;
  if (t) { await navigator.clipboard.writeText(t); toast('Copied!'); }
}

function openProfile_c(idx) { window.open(cQueue[idx]?.ig_link, '_blank'); }

function resetComment(idx) {
  const orig = cOrigComments[cQueue[idx]?.row] || cQueue[idx]?.comment;
  const b = document.getElementById('commentBox');
  if (b) { b.value = orig || ''; onCommentInput(); toast('Reset to original'); }
}

async function markPosted(idx) {
  stopPolling();
  const item    = cQueue[idx];
  const comment = document.getElementById('commentBox')?.value?.trim() || item.comment;

  const resp = await fetch('/api/mark-posted', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({row: item.row, comment: comment})
  });
  if (!resp.ok) { toast('Sheet update failed', true); return; }

  cDoneRows.add(item.row);
  toast('Done ✓ — sheet updated');

  // Next undone
  let next = idx + 1;
  while (next < cQueue.length && cDoneRows.has(cQueue[next].row)) next++;
  const remaining = cQueue.length - cDoneRows.size;
  if (remaining === 0) { updateProgress(); showAllDone('Comments'); }
  else if (next < cQueue.length) { showCommentCard(next); }
  else {
    let first = cQueue.findIndex(i => !cDoneRows.has(i.row));
    showCommentCard(first >= 0 ? first : 0);
  }
}

function cPrev() {
  if (cCurrentIdx > 0) { stopPolling(); showCommentCard(cCurrentIdx - 1); }
}

function cSkip(idx) {
  stopPolling();
  const n = cQueue.length;
  let next = (idx + 1) % n;
  let tries = 0;
  while (cDoneRows.has(cQueue[next].row) && tries++ < n) next = (next + 1) % n;
  if (next !== idx) showCommentCard(next);
}

// ── Request / Poll (Change Post + Regenerate) ─────────────────────────────────
async function requestAction(idx, action) {
  const item = cQueue[idx];
  const seen = cSeenUrls[item.handle] || [];
  const res  = await fetch('/api/request-action', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ action, handle: item.handle, row: item.row,
                           caption: item.caption, post_url: item.post_url, seen_urls: seen })
  });
  const data = await res.json();
  showPendingBanner('⚡ Go to Claude Code and say "handle request"');
  startPolling(idx);
}

function showPendingBanner(msg) {
  const b = document.getElementById('pendingBanner');
  const m = document.getElementById('pendingMsg');
  if (b && m) { m.textContent = msg; b.classList.add('show'); }
}
function hidePendingBanner() {
  const b = document.getElementById('pendingBanner');
  if (b) b.classList.remove('show');
}

function startPolling(idx) {
  stopPolling();
  pendingPoll = setInterval(async () => {
    const res  = await fetch('/api/check-result');
    const data = await res.json();
    if (!data.ready) return;
    if (data.row !== cQueue[idx]?.row) return;

    stopPolling();
    hidePendingBanner();
    await fetch('/api/clear-result', {method: 'POST'});

    if (data.status === 'error') { toast(data.error || 'Something went wrong', true); return; }

    if (data.comment) {
      const b = document.getElementById('commentBox');
      if (b) { b.value = data.comment; onCommentInput(); }
      cQueue[idx].comment = data.comment;
      await fetch('/api/save-comment', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({row: cQueue[idx].row, comment: data.comment})
      });
    }
    if (data.post_url) {
      await fetch('/api/save-post', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({row: cQueue[idx].row, post_url: data.post_url, caption: data.caption || ''})
      });
      cQueue[idx].post_url = data.post_url;
      cQueue[idx].caption  = (data.caption || '').substring(0, 600);
      if (!cSeenUrls[cQueue[idx].handle]) cSeenUrls[cQueue[idx].handle] = [];
      cSeenUrls[cQueue[idx].handle].push(data.post_url);
      await showCommentCard(idx);
    }
    toast(data.post_url ? 'Post changed + comment updated!' : 'New comment generated!');
  }, 2000);
}

function stopPolling() {
  if (pendingPoll) { clearInterval(pendingPoll); pendingPoll = null; }
}

// ═══════════════════════════════════════════════════════════════════════════════
// VALIDATION TAB
// ═══════════════════════════════════════════════════════════════════════════════

function showValidationCard(idx) {
  if (vQueue.length === 0) { showAllDone('Validation'); return; }
  idx = Math.max(0, Math.min(idx, vQueue.length - 1));
  vCurrentIdx = idx;
  updateProgress();

  const item    = vQueue[idx];
  const isDone  = vDoneRows.has(item.row);
  const verdict = item._verdict || '';

  document.getElementById('app').innerHTML = `
    <div class="card">
      <div class="handle-row">
        <div class="handle">${esc(item.handle)}</div>
        ${verdict === 'APPROVE'    ? '<span class="badge badge-green">✓ Approved</span>'   : ''}
        ${verdict === 'Not Valid'  ? '<span class="badge badge-red">✗ Not Valid</span>'    : ''}
        ${!isDone                  ? '<span class="badge badge-orange">Pending</span>'      : ''}
      </div>

      <div class="info-row">
        ${item.category ? `<div class="info-pill">📂 ${esc(item.category)}</div>` : ''}
        ${item.hashtag  ? `<div class="info-pill">#${esc(item.hashtag)}</div>`     : ''}
        ${item.display  ? `<div class="info-pill">👤 ${esc(item.display)}</div>`   : ''}
        <div class="info-pill">${idx + 1} of ${vQueue.length}</div>
      </div>

      <div class="btn-row">
        <button class="post-link-btn" onclick="window.open('${esc(item.ig_link)}','_blank')" style="margin-bottom:0">
          🔗 Open Profile ↗
        </button>
      </div>

      <div style="margin-top:14px;">
        <div class="btn-row">
          <button class="btn btn-green" onclick="vVerdict(${idx},'APPROVE')"   ${isDone?'disabled':''}>✓ Approve</button>
          <button class="btn btn-red"   onclick="vVerdict(${idx},'Not Valid')" ${isDone?'disabled':''}>✗ Not Valid</button>
        </div>
        <div class="btn-row">
          <button class="btn btn-gray" id="vPrevBtn" onclick="vPrev()" ${idx===0?'disabled':''}>← Previous</button>
          <button class="btn btn-gray" onclick="vSkip(${idx})">Skip</button>
        </div>
      </div>
    </div>`;
}

async function vVerdict(idx, verdict) {
  const item = vQueue[idx];
  const resp = await fetch('/api/mark-validation', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({row: item.row, verdict})
  });
  if (!resp.ok) { toast('Sheet update failed', true); return; }

  vQueue[idx]._verdict = verdict;
  vDoneRows.add(item.row);
  toast(verdict === 'APPROVE' ? 'Approved ✓' : 'Marked Not Valid');

  // Advance to next undone
  let next = idx + 1;
  while (next < vQueue.length && vDoneRows.has(vQueue[next].row)) next++;
  const remaining = vQueue.length - vDoneRows.size;
  if (remaining === 0) { updateProgress(); showAllDone('Validation'); }
  else if (next < vQueue.length) { showValidationCard(next); }
  else {
    let first = vQueue.findIndex(i => !vDoneRows.has(i.row));
    showValidationCard(first >= 0 ? first : 0);
  }
}

function vPrev() {
  if (vCurrentIdx > 0) showValidationCard(vCurrentIdx - 1);
}

function vSkip(idx) {
  const n = vQueue.length;
  let next = (idx + 1) % n;
  let tries = 0;
  while (vDoneRows.has(vQueue[next].row) && tries++ < n) next = (next + 1) % n;
  if (next !== idx) showValidationCard(next);
}

// ── Shared helpers ────────────────────────────────────────────────────────────
function showAllDone(label) {
  updateProgress();
  document.getElementById('app').innerHTML = `
    <div class="card center-msg">
      <h2>All done! 🎉</h2>
      <p>${label} complete.</p>
    </div>`;
}

function toast(msg, isErr) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast' + (isErr ? ' error' : '');
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

function esc(s) {
  return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

init();
</script>
</body>
</html>
"""


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    global ws_comments, ws_outreach, comments_q, comments_cols
    global validation_q, validation_cols, post_options

    print("Connecting to Google Sheets...")
    ws_comments, ws_outreach = open_sheets()
    comments_q,  comments_cols   = load_comments_queue(ws_comments)
    validation_q, validation_cols = load_validation_queue(ws_outreach)
    post_options = load_post_options()

    print(f"Comments queue:    {len(comments_q)} accounts")
    print(f"Validation queue:  {len(validation_q)} accounts pending review")
    print("Opening http://localhost:5560 ...")

    threading.Timer(1.2, lambda: webbrowser.open("http://localhost:5560")).start()
    app.run(host="127.0.0.1", port=5560, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
