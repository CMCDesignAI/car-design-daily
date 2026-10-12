#!/usr/bin/env python3
"""Leaderboard snapshot + diff for AI Model Daily.

Usage:
  python3 tools/lb_diff.py --date YYYY-MM-DD --fresh /path/fresh.json [--dir /workspace/ai-digest/leaderboards] [--no-write-data]

fresh.json = {"boards": [{id,title,en,source,source_url,as_of,fetched,metric,rows:[{rank,model,org,score,ci?,note?}]}]}
(top 10 per board, numbers exactly as fetched).

What it does:
  1. Finds the most recent snapshot in --dir with a date strictly before --date.
  2. Per board (matched by id), diffs fresh vs previous (models matched by normalised name).
  3. status per board:
       baseline  – no previous snapshot for this board → show fresh charts.
       changed   – meaningful change → show fresh charts, rows annotated (move/new/delta).
       unchanged – no meaningful change → carry the PREVIOUS rows/as_of forward.
     Meaningful = #1 changed, or top-10 membership changed, or any model moved >= 2 ranks,
                  or any score moved >= 5 points.  (A fresh board whose as_of equals the
                  previous as_of and whose rows are identical is always unchanged.)
  4. Writes <dir>/<date>.json (the boards as DISPLAYED, so tomorrow diffs against what readers saw)
     and merges data.json["leaderboards"] in ai/issues/<date>/ (keeps any existing "analysis" text
     for a board only if its status is still "changed").
  5. Prints a plain-text diff summary to stdout for writing the zh-TW analysis.
"""
import json, os, glob, re, sys, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
norm = lambda s: re.sub(r"[\s_]+", " ", s.strip().lower())

def prev_snapshot(d, date):
    c = sorted(p for p in glob.glob(os.path.join(d, "????-??-??.json")) if os.path.basename(p)[:10] < date)
    return (json.load(open(c[-1], encoding="utf-8")), os.path.basename(c[-1])[:10]) if c else (None, None)

def diff_board(fb, pb):
    rows = [dict(r) for r in fb["rows"][:10]]
    if not pb:
        return "baseline", rows, {"summary": ["首份快照（baseline）"]}
    prev = {norm(r["model"]): r for r in pb["rows"][:10]}
    cur = {norm(r["model"]) for r in rows}
    out, big = [], False
    for r in rows:
        k = norm(r["model"]); p = prev.get(k)
        for f in ("new", "move", "delta"): r.pop(f, None)
        if not p:
            r["new"] = True; big = True; out.append(f'NEW #{r["rank"]} {r["model"]} ({r["org"]}) {r["score"]}')
            continue
        mv = p["rank"] - r["rank"]; dl = r["score"] - p["score"]
        if mv: r["move"] = mv
        if dl: r["delta"] = dl
        if abs(mv) >= 2 or abs(dl) >= 5: big = True
        if mv or dl: out.append(f'{r["model"]}: #{p["rank"]}→#{r["rank"]} ({"+" if mv>0 else ""}{mv} 名), {p["score"]}→{r["score"]} ({"+" if dl>=0 else ""}{dl})')
    dropped = [p for k, p in prev.items() if k not in cur]
    for p in dropped: out.append(f'OUT {p["model"]} (前次 #{p["rank"]} {p["score"]})')
    if dropped: big = True
    if norm(rows[0]["model"]) != norm(pb["rows"][0]["model"]):
        big = True; out.insert(0, f'NEW #1: {rows[0]["model"]} 取代 {pb["rows"][0]["model"]}')
    if not big:
        return "unchanged", [dict(r) for r in pb["rows"][:10]], {"summary": out or ["無變化"]}
    return "changed", rows, {"summary": out, "dropped": [{"model": p["model"], "org": p["org"], "rank": p["rank"], "score": p["score"]} for p in dropped]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True); ap.add_argument("--fresh", required=True)
    ap.add_argument("--dir", default="/workspace/ai-digest/leaderboards"); ap.add_argument("--no-write-data", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.dir, exist_ok=True)
    fresh = json.load(open(a.fresh, encoding="utf-8"))
    prev, prev_date = prev_snapshot(a.dir, a.date)
    pmap = {b["id"]: b for b in (prev or {}).get("boards", [])}
    boards = []
    print(f"previous snapshot: {prev_date or 'none'}")
    for fb in fresh["boards"]:
        pb = pmap.get(fb["id"])
        st, rows, info = diff_board(fb, pb)
        b = {k: v for k, v in fb.items() if k != "rows"}
        if st == "unchanged":                       # carry forward previous data
            for k in ("source", "source_url", "as_of", "metric", "title", "en"): b[k] = pb.get(k, b.get(k))
            b["carried_from"] = pb.get("carried_from") or prev_date
            b["fetched"] = fb.get("fetched"); b["latest_as_of"] = fb.get("as_of")
        b.update(status=st, rows=rows, compared_to=prev_date if pb else None, diff=info)
        if st == "changed": b["dropped"] = info.get("dropped", [])
        boards.append(b)
        print(f"\n[{fb['id']}] {st}  (as_of {b['as_of']})"); [print("  -", s) for s in info["summary"]]
    snap = {"date": a.date, "compared_to": prev_date, "boards": boards}
    json.dump(snap, open(os.path.join(a.dir, f"{a.date}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if not a.no_write_data:
        p = os.path.join(ROOT, "ai", "issues", a.date, "data.json")
        d = json.load(open(p, encoding="utf-8"))
        old = {b["id"]: b for b in (d.get("leaderboards") or {}).get("boards", [])}
        for b in boards:
            o = old.get(b["id"], {})
            if b["status"] == "changed" and o.get("status") == "changed" and o.get("analysis"): b["analysis"] = o["analysis"]
            elif b["status"] == "changed": b["analysis"] = ""      # daily run must fill (zh-TW, 3–5 sentences)
        d["leaderboards"] = {"snapshot": a.date, "compared_to": prev_date, "boards": boards}
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\nwrote data.json leaderboards; fill boards[].analysis for status=changed")

if __name__ == "__main__":
    main()
