#!/usr/bin/env python3
"""CMF card-grid check: 1–2 car + 2–3 trend/paint/material + 0–2 hmi (checked in detail by check_hmi.py), 4–7 cards total; fallback content keeps its kind with a ⚠ note.
Fails if a key/url repeats within 30 days in cmf-log.json, or a car piece reuses a design-news source URL."""
import json,sys,datetime as dt
date=sys.argv[1]; d=json.load(open(f"issues/{date}/data.json")); log=json.load(open("cmf-log.json"))
c=d.get("cmf") or []; kinds=[x.get("kind","car") for x in c]; err=[]
h=d.get("hmi") or []
if any(x.get("kind") for x in c):  # modular issues (2026-10-16+); legacy issues without kind skip count rules
    cars=kinds.count("car"); cm=sum(kinds.count(k) for k in ("trend","paint","material"))
    if not 1<=cars<=2: err.append(f"need 1–2 car pieces, got {cars}")
    if not 2<=cm<=3: err.append(f"need 2–3 trend/paint/material pieces, got {cm}")
    if len(h)>2: err.append(f"max 2 HMI cards, got {len(h)}")
    if not 4<=len(c)+len(h)<=7: err.append(f"card grid needs 4–7 cards total (cmf+hmi), got {len(c)+len(h)}")
    bad=[k for k in kinds if k not in ("car","trend","paint","material")]
    if bad: err.append(f"unknown kind {bad}")
dn={u for n in d["design_news"] for _,u in n.get("sources",[])}
for x in c:
    if x.get("kind","car")=="car":
        for _,u in x["sources"]:
            if u in dn: err.append(f"{x['id']} reuses design-news source {u}")
t=dt.date.fromisoformat(date); seen={}
for r in log:
    rd=dt.date.fromisoformat(r["date"])
    if r["date"]!=date and (t-rd).days<=30:
        seen[r["car_key"]]=r["date"]; seen[r["url"]]=r["date"]
for r in [r for r in log if r["date"]==date]:
    for k in (r["car_key"],r["url"]):
        if k in seen: err.append(f"dup within 30 days: {k} ({seen[k]})")
# freshness (2026-10-27+): a CMF/HMI piece must not re-run news already covered in any issue's design news/CMF
# within 30 days, and its newest source must be ≤3 days old. Stale news is allowed only as a detailed CMF report:
# set "deep": true, real image required (no swatch/⚠ note), ≥4 points covering colour/material names, finish, inspiration, where applied.
import glob,re
if date>="2026-10-27":
    prev={}
    for f in glob.glob("issues/*/data.json"):
        pd_=f.split("/")[1]
        if pd_>=date or (t-dt.date.fromisoformat(pd_)).days>30: continue
        try: od=json.load(open(f))
        except Exception: continue
        for sec in ("design_news","cmf","hmi"):
            for n in od.get(sec) or []:
                for _,u in n.get("sources",[]): prev.setdefault(u,(pd_,sec))
    for x in c+h:
        deep=x.get("deep")
        for _,u in x.get("sources",[]):
            if u in prev and not deep: err.append(f"{x.get('id')} source already used in {prev[u][0]} {prev[u][1]}: {u} (stale; replace, or make it a deep CMF report)")
        ds=[]
        for lab,_ in x.get("sources",[]):
            m=re.search(r"(\d{1,2})/(\d{1,2})[)）]",lab)
            if m:
                try: ds.append(dt.date(t.year,int(m[1]),int(m[2])))
                except ValueError: pass
        if ds and (t-max(ds)).days>3 and not deep: err.append(f"{x.get('id')} newest source is {max(ds)} (>3 days old); replace, or make it a deep CMF report")
        if deep and (not x.get("image") or x.get("swatch") or x.get("note") or len(x.get("points",[]))<4):
            err.append(f"{x.get('id')} deep report needs real image, no swatch/note, ≥4 points")
# combined cabin drawing (2026-10-19+): headliner must be a preset name
ci=(d.get("color_data") or {}).get("interior") or {}
if date>="2026-10-19" and ci:
    hv=(ci.get("vars") or {}).get("headliner")
    if hv not in (None,"light","dark"): err.append(f"interior vars.headliner must be 'light' or 'dark' (got {hv!r})")
    if any(p_[4]=="headliner" for p_ in ci.get("parts",[])): err.append("interior parts must not carry 'headliner' (use vars.headliner: light|dark)")
print("CMF OK" if not err else "\n".join(err)); sys.exit(1 if err else 0)
