#!/usr/bin/env python3
"""介面與 HMI check: 0–2 HMI cards mixed into the 色彩與材質 card grid (total grid count is checked by check_cmf.py). Each needs a local JPG image, ISO date, credit 「Brand (via site)」 or 「site 示意圖」,
credit_url, ≥1 source link, ≥2 zh-TW points. kind case|inspiration. Fails if id/url repeats within 30 days in hmi-log.json,
or if today's items are missing from the log. Usage: python3 tools/check_hmi.py YYYY-MM-DD"""
import json,sys,os,re,datetime as dt
date=sys.argv[1]; d=json.load(open(f"issues/{date}/data.json")); items=d.get("hmi") or []; err=[]
log=json.load(open("hmi-log.json")) if os.path.exists("hmi-log.json") else []
if len(items)>2: err.append(f"max 2 HMI items, got {len(items)}")
for x in items:
    i=x.get("id","?")
    if x.get("kind") not in ("case","inspiration"): err.append(f"{i}: kind must be case|inspiration")
    try: dt.date.fromisoformat(x.get("date",""))
    except Exception: err.append(f"{i}: date must be YYYY-MM-DD (real publish date)")
    im=x.get("image") or {}
    f=im.get("file","")
    if not f.lower().endswith((".jpg",".jpeg")): err.append(f"{i}: image must be a local .jpg")
    elif not os.path.exists(f"issues/{date}/img/{f}"): err.append(f"{i}: image file missing issues/{date}/img/{f}")
    cr=im.get("credit","")
    if not (re.search(r"\(via .+\)|（via .+）",cr) or cr.endswith("示意圖")): err.append(f"{i}: credit must be 'Brand (via site)' or 'site 示意圖', got {cr!r}")
    if not str(im.get("credit_url","")).startswith("http"): err.append(f"{i}: credit_url missing")
    if not im.get("alt"): err.append(f"{i}: image alt missing")
    if not any(str(u).startswith("http") for _,u in x.get("sources",[])): err.append(f"{i}: source link missing")
    if len(x.get("points",[]))<2: err.append(f"{i}: need ≥2 points")
    for k in ("title","brand","tag"):
        if not x.get(k): err.append(f"{i}: {k} missing")
t=dt.date.fromisoformat(date); seen={}
for r in log:
    if r["date"]!=date and 0<=(t-dt.date.fromisoformat(r["date"])).days<=30: seen[r["key"]]=r["date"]; seen[r["url"]]=r["date"]
today={r["key"] for r in log if r["date"]==date}
for x in items:
    u=x["sources"][0][1] if x.get("sources") else ""
    for k in (x.get("id"),u):
        if k in seen: err.append(f"dup within 30 days: {k} ({seen[k]})")
    if x.get("id") not in today: err.append(f"{x.get('id')}: add {{date,key=id,url,image}} to hmi-log.json")
print(f"HMI OK ({len(items)} item)" if not err else "\n".join(err)); sys.exit(1 if err else 0)
