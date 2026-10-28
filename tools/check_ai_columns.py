#!/usr/bin/env python3
"""名家專欄 guard (AI Model Daily). Checks ai/issues/<date>/data.json → columns[]:
- required fields; platform/creator_key from tools/ai_creators.json (status core, or suggested only if approved)
- source date within 7 days before the issue date (not in the future)
- 2–4 points; ≤6 cards per issue, ≤2 per creator
- image: bare filename that exists in img/ (or image null → must say why in note)
- 30-day dedupe against ai-columns-log.json (same url or key on an earlier date) and against other issues' columns
Usage: python3 tools/check_ai_columns.py [YYYY-MM-DD]   (default: latest issue). Exit 1 on any problem."""
import json, glob, os, sys, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda s: dt.date.fromisoformat(s)
issues = sorted(glob.glob(f"{ROOT}/ai/issues/*/data.json"))
date = sys.argv[1] if len(sys.argv) > 1 else os.path.basename(os.path.dirname(issues[-1]))
data = json.load(open(f"{ROOT}/ai/issues/{date}/data.json", encoding="utf-8"))
cols = data.get("columns") or []
reg = json.load(open(f"{ROOT}/tools/ai_creators.json", encoding="utf-8"))["creators"]
ok_keys = {c["key"] for c in reg if c["status"] in ("core", "approved")}
log = json.load(open(f"{ROOT}/ai-columns-log.json", encoding="utf-8")) if os.path.exists(f"{ROOT}/ai-columns-log.json") else []
bad = []
if len(cols) > 6: bad.append(f"{len(cols)} cards (max 6)")
per = {}
for c in cols:
    cid = c.get("id", "?")
    for k in ("id", "creator", "creator_key", "platform", "date", "title", "one", "points", "url"):
        if not c.get(k): bad.append(f"{cid}: missing {k}")
    if c.get("creator_key") not in ok_keys: bad.append(f"{cid}: creator_key {c.get('creator_key')!r} not core/approved in ai_creators.json")
    if c.get("platform") not in ("YouTube", "Bilibili", "Facebook", "Threads", "Medium", "X", "Web"): bad.append(f"{cid}: bad platform {c.get('platform')!r}")
    per[c.get("creator_key")] = per.get(c.get("creator_key"), 0) + 1
    try:
        age = (D(date) - D(c["date"])).days
        if age < 0 or age > 7: bad.append(f"{cid}: source date {c['date']} not within 7 days of {date}")
    except Exception: bad.append(f"{cid}: bad date {c.get('date')!r}")
    if not 2 <= len(c.get("points") or []) <= 4: bad.append(f"{cid}: needs 2–4 points")
    im = c.get("image")
    if im:
        f = im.get("file", "")
        if "/" in f: bad.append(f"{cid}: image.file must be bare filename")
        elif not os.path.isfile(f"{ROOT}/ai/issues/{date}/img/{f}"): bad.append(f"{cid}: missing img/{f}")
        if not im.get("credit"): bad.append(f"{cid}: image.credit missing")
    elif not c.get("note"): bad.append(f"{cid}: no image and no note explaining why")
    for x in log:
        if x.get("date", "") < date and (D(date) - D(x["date"])).days <= 30 and (x.get("url") == c.get("url") or x.get("key") == cid):
            bad.append(f"{cid}: already ran {x['date']} (30-day dedupe)")
    for p in issues:
        od = os.path.basename(os.path.dirname(p))
        if od < date and (D(date) - D(od)).days <= 30:
            for oc in json.load(open(p, encoding="utf-8")).get("columns") or []:
                if oc.get("url") == c.get("url"): bad.append(f"{cid}: same url in {od} issue")
for k, n in per.items():
    if n > 2: bad.append(f"{k}: {n} cards (max 2 per creator)")
for b in bad: print("FAIL", b)
print(f"check_ai_columns {date}: {len(cols)} card(s), {len(bad)} problem(s)"); sys.exit(1 if bad else 0)
