#!/usr/bin/env python3
"""CMF 5-piece check: exactly 2 car + 1 trend + 1 paint + 1 material; fallback content stays in its slot with a ⚠ note.
Fails if a key/url repeats within 30 days in cmf-log.json, or a car piece reuses a design-news source URL."""
import json,sys,datetime as dt
date=sys.argv[1]; d=json.load(open(f"issues/{date}/data.json")); log=json.load(open("cmf-log.json"))
c=d.get("cmf") or []; kinds=[x.get("kind","car") for x in c]; err=[]
need={"car":2,"trend":1,"paint":1,"material":1}
if len(c)!=5: err.append(f"need 5 pieces, got {len(c)}")
for k,n in need.items():
    if kinds.count(k)!=n: err.append(f"need {n} {k}, got {kinds.count(k)} (a fallback piece keeps its slot's kind and must carry a ⚠ note)")
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
print("CMF OK" if not err else "\n".join(err)); sys.exit(1 if err else 0)
