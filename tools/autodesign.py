#!/usr/bin/env python3
"""Auto&Design (autodesignmagazine.com) queue for Car Design Daily section 02.
  fetch [--days 60]          pull EN feeds (main + category feeds, paged) into data/autodesign_queue.json
  pick --date D [--n N] [--exclude "kw1,kw2"] [--img-dir issues/D/img]
                             choose today's items (auto N: 2 if a new Meet the Designer or Design Story batch, else 1),
                             download og:image, print JSON stubs; the routine fills title/summary in 繁中 and
                             puts them in data.json["autodesign"].
  commit --date D --ids a,b  mark ids used (data/autodesign_log.json, never repeated)
  status                     queue size / weeks covered
Public RSS only, no login. Never copies full text: keeps a ~600-char excerpt for summarising."""
import argparse, json, os, re, sys, html, urllib.request, email.utils, datetime as dt
import xml.etree.ElementTree as ET
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = f"{ROOT}/data/autodesign_queue.json"; LOG = f"{ROOT}/data/autodesign_log.json"
BASE = "https://autodesignmagazine.com/en"
FEEDS = {"": "News", "category/meet-the-designer-en-2": "Meet the Designer", "category/design-story-en": "Design Story",
         "category/newsstand": "Design Story", "category/concept-en": "Concept", "category/extra-en": "Extra", "category/news-en": "News"}
RANK = {"Meet the Designer": 0, "Design Story": 1, "Concept": 2, "Extra": 3, "News": 4}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"}
NS = {"content": "http://purl.org/rss/1.0/modules/content/"}
def get(u, t=20):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
def load(p, d):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return d
def save(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
def text(h): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h or ""))).strip()
def fetch(days):
    q = load(Q, {"items": {}}); used = set(load(LOG, {"used": {}})["used"]); cut = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    new = 0
    for path, col in FEEDS.items():
        for page in range(1, 6):
            u = f"{BASE}/{path}/feed/".replace("//feed", "/feed") + (f"?paged={page}" if page > 1 else "")
            try: root = ET.fromstring(get(u))
            except Exception: break
            items = root.findall("./channel/item"); old = False
            for it in items:
                link = it.findtext("link").strip(); pd = email.utils.parsedate_to_datetime(it.findtext("pubDate"))
                if pd < cut: old = True; continue
                cats = [c.text or "" for c in it.findall("category")]
                title = html.unescape(it.findtext("title") or "")
                c = col
                if title.upper().startswith("MEET THE DESIGNER"): c = "Meet the Designer"
                elif col == "News":
                    for k in ("DESIGN STORY", "CONCEPT", "EXTRA"):
                        if k in [x.upper() for x in cats]: c = k.title() if k != "DESIGN STORY" else "Design Story"
                iid = link.rstrip("/").rsplit("/", 1)[-1]
                cur = q["items"].get(iid)
                if cur:
                    if RANK[c] < RANK[cur["column"]]: cur["column"] = c
                    continue
                body = it.findtext("content:encoded", namespaces=NS) or it.findtext("description") or ""
                m = re.search(r'<img[^>]+src="([^"]+)"', body)
                q["items"][iid] = dict(id=iid, title_en=title, column=c, date=pd.date().isoformat(), url=link,
                    tags=[x for x in cats if x.upper() not in ("NEWS", "EXTRA")], excerpt=text(body)[:600],
                    image=m.group(1) if m else None, added=dt.date.today().isoformat(), used=iid in used)
                new += 1
            if old or len(items) < 10: break
    save(Q, q); return new
def og(url):
    try:
        m = re.search(r'og:image" content="([^"]+)', get(url).decode("utf-8", "ignore")); return m.group(1) if m else None
    except Exception: return None
def pick(date, n, exclude, imgdir):
    q = load(Q, {"items": {}}); used = load(LOG, {"used": {}})["used"]
    ex = [x.strip().lower() for x in (exclude or "").split(",") if x.strip()]
    pool = [x for x in q["items"].values() if x["id"] not in used and not x.get("used")]
    pool = [x for x in pool if not any(k in (x["title_en"] + " " + " ".join(x["tags"])).lower() for k in ex)]
    if n is None:  # 2 when a fresh interview or a new issue batch (>=3 Design Story same day) arrived in the last 7 days
        d0 = (dt.date.fromisoformat(date) - dt.timedelta(days=7)).isoformat()
        fresh = [x for x in pool if x["date"] >= d0]
        ds = {}
        for x in fresh:
            if x["column"] == "Design Story": ds[x["date"]] = ds.get(x["date"], 0) + 1
        n = 2 if any(x["column"] == "Meet the Designer" for x in fresh) or any(v >= 3 for v in ds.values()) else 1
    # columns first (MtD > Design Story > Concept > Extra > News); within a tier oldest first
    pool.sort(key=lambda x: (RANK[x["column"]], x["date"]))
    out = []
    for x in pool[:n]:
        img = og(x["url"]) or x.get("image"); f = None
        if img and imgdir:
            os.makedirs(imgdir, exist_ok=True); ext = os.path.splitext(img.split("?")[0])[1] or ".jpg"
            f = f"ad-{x['id'][:50]}{ext}"
            try: open(os.path.join(imgdir, f), "wb").write(get(img, 30))
            except Exception: f = None
        out.append(dict(id="ad-" + x["id"][:50], column=x["column"], date=x["date"], orig=x["title_en"], url=x["url"],
            excerpt=x["excerpt"], title="", summary="",
            image=(dict(file=f, alt=x["title_en"], credit="Auto&Design", credit_url=x["url"]) if f else None), image_url=img))
    print(json.dumps(out, ensure_ascii=False, indent=1))
def commit(date, ids):
    lg = load(LOG, {"used": {}}); q = load(Q, {"items": {}})
    for i in ids:
        k = i[3:] if i.startswith("ad-") else i
        full = next((x for x in q["items"] if x[:50] == k), k)
        lg["used"][full] = date
        if full in q["items"]: q["items"][full]["used"] = True
    save(LOG, lg); save(Q, q); print("logged", ids)
def status():
    q = load(Q, {"items": {}}); used = load(LOG, {"used": {}})["used"]
    left = [x for x in q["items"].values() if x["id"] not in used and not x.get("used")]
    by = {}
    for x in left: by[x["column"]] = by.get(x["column"], 0) + 1
    print(json.dumps(dict(unused=len(left), by_column=by, used=len(used), weeks_at_1_per_day=round(len(left) / 7, 1)), ensure_ascii=False))
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--date"); ap.add_argument("--n", type=int)
    ap.add_argument("--days", type=int, default=60); ap.add_argument("--exclude"); ap.add_argument("--img-dir"); ap.add_argument("--ids", default="")
    a = ap.parse_args()
    if a.cmd == "fetch": print("new", fetch(a.days)); status()
    elif a.cmd == "pick": pick(a.date, a.n, a.exclude, a.img_dir)
    elif a.cmd == "commit": commit(a.date, [x for x in a.ids.split(",") if x])
    elif a.cmd == "status": status()
