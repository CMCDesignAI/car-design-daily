#!/usr/bin/env python3
"""Fetch Artificial Analysis Video Arena (AA-Video-T2V, Overall) top 10 -> board JSON on stdout.
Usage: python3 tools/lb_fetch_aa_video.py --date YYYY-MM-DD [--html file]
Parses the server-rendered leaderboard table (rank | range | logo alt "<Org> logo" | model | Elo | ±CI | samples | released).
The page shows no explicit data date, so as_of = fetch date."""
import re, html, json, sys, argparse, subprocess
URL = "https://artificialanalysis.ai/video/leaderboard/text-to-video"
ap = argparse.ArgumentParser(); ap.add_argument("--date", required=True); ap.add_argument("--html"); a = ap.parse_args()
s = open(a.html, encoding="utf-8").read() if a.html else subprocess.run(
    ["curl", "-sL", "-m", "25", "-A", "Mozilla/5.0", URL], capture_output=True, text=True).stdout
rows = []
for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", s, flags=re.S):
    org = re.search(r'alt="([^"]+?) logo"', tr)
    cells = [html.unescape(re.sub(r"<[^>]+>", "|", td)) for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S)]
    toks = [t.strip() for c in cells for t in c.split("|") if t.strip()]
    m = re.search(r"^(\d+)\|(?:[\d-]+\|)?(?:[^|]+ logo\|)?(.+?)\|(\d{3,4})\|(±\d+|Anchor)\|.*?\|([\d,]+)\|(\w{3} \d{4})", "|".join(toks))
    if not m: continue
    rows.append({"rank": int(m[1]), "model": m[2], "org": org[1] if org else "", "score": int(m[3]),
                 **({"ci": int(m[4][1:])} if m[4].startswith("±") else {}), "released": m[6]})
    if len(rows) == 10: break
if len(rows) < 10: sys.exit(f"parse failed: {len(rows)} rows")
print(json.dumps({"id": "video", "title": "文生影片排行", "en": "Text-to-Video · AA-Video-T2V v2.1",
    "source": "Artificial Analysis · AA-Video-T2V v2.1（盲測 Elo）", "source_url": URL, "as_of": a.date,
    "fetched": a.date, "metric": "Elo", "rows": rows}, ensure_ascii=False, indent=1))
