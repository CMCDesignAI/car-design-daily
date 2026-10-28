#!/usr/bin/env python3
"""Render the AI Model Daily section from ai/issues/<date>/data.json.
Outputs: ai/issues/<date>/index.html for every issue, ai/index.html (= latest issue), ai/archive/index.html.
Shares assets/style.css and the topbar/switcher with tools/build.py (car section).
Usage: python3 tools/build_ai.py [--site-url https://user.github.io/repo]"""
import json, os, glob, html, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import gallery, write_page, check_wakelock, topbar, theme_init, theme_toggle, ROOT, SITE, archive_rows, thumb_for
e = html.escape
FONTS = '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Noto+Sans+TC:wght@400;600;700&family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">'

def issues():
    return [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(f"{ROOT}/ai/issues/*/data.json"), reverse=True)]

def links(ls):
    return "".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(n)} ↗</a>' for n, u in ls)

def figure(im, img, eager=False, cls="news-img"):
    if not im: return ""
    if isinstance(im, dict) and "image" in im: return gallery(im, img, eager, cls=cls)
    return (f'<figure class="{cls}"><div class="ratio"><img src="{img}{e(im["file"])}" alt="{e(im["alt"])}" loading="{"eager" if eager else "lazy"}" decoding="async" width="1600" height="900"></div>'
            f'<figcaption>圖片來源：<a href="{e(im["credit_url"])}" target="_blank" rel="noopener">{e(im["credit"])}</a></figcaption></figure>')

def story(s, img):
    if s.get("one"): return story_lite(s, img)
    return (f'<article class="story" id="{e(s["id"])}">{figure(s if s.get("image") else None, img)}<div class="shead"><span class="tag">{e(s["org"])} · {e(s["tag"])}</span><span class="date">{e(s["date"])}</span>'
            f'<h3>{e(s["title"])}</h3><p class="orig">{e(s["orig"])}</p><p class="sum">{e(s["summary"])}</p></div>'
            f'{"" if s.get("image") else "<p class=\"noimg\">來源頁沒有可用的官方圖片，因此不放圖。</p>"}<div class="src">來源：{links(s["links"])}</div></article>')

def gloss(g):
    """Lite format: first-use jargon explanations, rendered as small inline notes."""
    if not g: return ""
    return '<p class="gloss">' + "".join(f'<span><b>{e(t)}</b>：{e(x)}</span>' for t, x in g) + '</p>'

def story_lite(s, img):
    """Lite format (from 2026-10-13 preview): one plain sentence up front, details folded into <details>."""
    return (f'<article class="story lite" id="{e(s["id"])}">{figure(s if s.get("image") else None, img)}<div class="shead"><span class="tag">{e(s["org"])} · {e(s["tag"])}</span><span class="date">{e(s["date"])}</span>'
            f'<h3>{e(s.get("short_title") or s["title"])}</h3><p class="one">{e(s["one"])}</p>{gloss(s.get("gloss"))}</div>'
            f'<details class="more"><summary>看更多</summary><p class="orig">{e(s["orig"])}</p><p class="sum">{e(s["summary"])}</p><div class="src">來源：{links(s["links"])}</div></details></article>')

def tutorial(t):
    """v4 教學區 card: title, what you'll learn, difficulty, VRAM, folded steps + source links."""
    steps = "".join(f"<li>{e(x)}</li>" for x in t.get("steps", []))
    return (f'<article class="story lite tut" id="{e(t["id"])}"><div class="shead"><span class="tag">{e(t["level"])} · VRAM {e(t["vram"])}</span><span class="date">{e(t.get("kind","教學"))}</span>'
            f'<h3>{e(t["title"])}</h3><p class="one">{e(t["learn"])}</p>{gloss(t.get("gloss"))}</div>'
            f'<details class="more"><summary>看更多：步驟</summary><ol class="steps">{steps}</ol><div class="src">教學來源：{links(t["links"])}</div></details></article>')

def column(c, img):
    """名家專欄 card (from 2026-10-28 preview): creator · platform, source date, thumbnail, one line + 2–4 visible points."""
    pts = "".join(f"<li>{e(x)}</li>" for x in c.get("points", []))
    im = c.get("image")
    fig = ""
    if im:
        play = '<span class="pbtn">▶</span>' if c.get("platform") in ("YouTube", "Bilibili") else ""
        fig = (f'<figure class="news-img"><a class="ratio colthumb" href="{e(c["url"])}" target="_blank" rel="noopener" aria-label="開啟原{"片" if play else "文"}：{e(c["title"])}">'
               f'<img src="{img}{e(im["file"])}" alt="{e(im["alt"])}" loading="lazy" decoding="async" width="1280" height="720">{play}</a>'
               f'<figcaption>圖片來源：<a href="{e(im.get("credit_url") or c["url"])}" target="_blank" rel="noopener">{e(im["credit"])}</a></figcaption></figure>')
    more = links(c.get("links") or [])
    return (f'<article class="story lite col" id="{e(c["id"])}">{fig}<div class="shead"><span class="tag">{e(c["creator"])} · {e(c["platform"])}</span><span class="date">{e(c["date"])}</span>'
            f'<h3>{e(c.get("short_title") or c["title"])}</h3><p class="one">{e(c["one"])}</p><ul class="cpts">{pts}</ul>{gloss(c.get("gloss"))}</div>'
            f'<details class="more"><summary>看更多</summary>{f"<p class=\"orig\">{e(c['orig'])}</p>" if c.get("orig") else ""}'
            f'<div class="src"><a href="{e(c["url"])}" target="_blank" rel="noopener">{"看原片" if c.get("platform") in ("YouTube", "Bilibili") else "看原文"} ↗</a>{more}</div></details></article>')

def sec_head(n, zh, en):
    return f'<div class="sec-head"><span class="num">{n:02d}</span><h2>{zh}</h2><span class="en">{en}</span></div>'

def lb_chart(b):
    """One leaderboard card: status badge + inline-SVG horizontal bars (top 10) + zh-TW analysis.
    Row flags written by tools/lb_diff.py: new (NEW tag), move (+n up / -n down), delta (score change)."""
    rows = b["rows"][:10]
    st = b.get("status", "baseline")
    hi, lo = max(r["score"] for r in rows), min(r["score"] for r in rows)
    base = lo - max(8, round((hi - lo) * 0.5))          # axis floor so gaps stay readable
    W, L, R, rh, top = 720, 300, 120, 34, 6
    bw = W - L - R
    g = []
    for i, r in enumerate(rows):
        y = top + i * rh
        w = max(4, bw * (r["score"] - base) / (hi - base))
        mv = r.get("move", 0) if st == "changed" else 0
        new = r.get("new") and st == "changed"
        cls = "lb-bar" + (" lead" if i == 0 else "") + (" chg" if (new or mv) else "")
        pre = " · 暫定" if r.get("note") == "Preliminary" else ""
        mark = ('<tspan class="lb-new"> NEW</tspan>' if new else
                f'<tspan class="lb-up"> ↑{mv}</tspan>' if mv > 0 else f'<tspan class="lb-down"> ↓{-mv}</tspan>' if mv < 0 else "")
        dl = r.get("delta") if st == "changed" else None
        ci = f" ±{r['ci']}" if r.get("ci") else ""
        dls = f'<tspan class="lb-delta"> {dl:+d}</tspan>' if dl else ""
        g.append(f'<text class="lb-rank" x="0" y="{y+21}">{r["rank"]:02d}</text>'
                 f'<text class="lb-name" x="34" y="{y+15}">{e(r["model"])}{mark}</text><text class="lb-org" x="34" y="{y+29}">{e(r["org"])}{pre}</text>'
                 f'<rect class="{cls}" x="{L}" y="{y+8}" width="{w:.1f}" height="16" rx="3"></rect>'
                 f'<text class="lb-score" x="{L+w+8:.1f}" y="{y+21}">{r["score"]}{ci}'
                 f'{dls}</text>')
    H = top + len(rows) * rh + 4
    badge = {"unchanged": f'榜單無重大變化 · 資料更新 {e(b["as_of"])}',
             "changed": f'榜單有變動 · 對比 {e(b.get("compared_to") or "")}',
             "baseline": "首份快照（Baseline）· 之後每日對比"}.get(st, "")
    carry = (f" · 沿用 {e(b['carried_from'])} 的資料（最新檢查 {e(b.get('latest_as_of') or b.get('fetched',''))}）"
             if st == "unchanged" and b.get("carried_from") else "")
    out = ""
    if st == "changed":
        if b.get("dropped"):
            out = '<p class="lbout">跌出前 10：' + "、".join(f'{e(x["model"])}（前次 #{x["rank"]}）' for x in b["dropped"]) + '</p>'
        if b.get("analysis"):
            out += f'<p class="lbana">{e(b.get("analysis_short") or b["analysis"])}</p>'
    return (f'<figure class="lbcard"><figcaption class="lbhead"><h3>{e(b["title"])}</h3><span class="en">{e(b["en"])}</span></figcaption>'
            f'<p class="lbbadge {st}">{badge}</p>'
            f'<svg class="lbsvg" viewBox="0 0 {W} {H}" role="img" aria-label="{e(b["title"])} 前 10 名">{"".join(g)}</svg>{out}'
            f'<p class="lbsrc">來源：<a href="{e(b["source_url"])}" target="_blank" rel="noopener">{e(b["source"])} ↗</a> · 資料更新 {e(b["as_of"])} · 抓取 {e(b.get("fetched",""))}'
            f'{carry} · 軸起點 {base}</p></figure>')

def leaderboard(lb):
    """Shown every day at the very top (after masthead/lede). Data comes from tools/lb_diff.py."""
    if not lb or not lb.get("boards"): return ""
    return ('<section id="board"><div class="sec-head"><span class="num">≡</span><h2>本週榜單</h2><span class="en">Leaderboards</span></div>'
            '<div class="lbgrid">' + "".join(lb_chart(b) for b in lb["boards"]) + '</div></section>')

def head(title, desc, css, canon, ogimg):
    return f'''<!doctype html><html lang="zh-Hant-TW"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<meta property="og:type" content="article"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
{f'<meta property="og:image" content="{ogimg}"><meta name="twitter:card" content="summary_large_image">' if ogimg else ''}
{f'<link rel="canonical" href="{canon}">' if canon else ''}
<meta name="theme-color" content="#0a0c10">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{FONTS}
<link rel="stylesheet" href="{css}">
{theme_init("ai")}
</head>'''

def page(d, root, aibase, all_issues, is_latest):
    date = d["date"]; y, m, dd = date.split("-")
    img = f"issues/{date}/img/" if is_latest else "img/"
    title = f"AI Model Daily · {y}.{m}.{dd}"
    first = next((u["image"] for w in d["watch"] for u in w["updates"] if u.get("image")), None)
    ogimg = f"{SITE}/ai/issues/{date}/img/{first['file']}" if (SITE and first) else ""
    canon = f"{SITE}/ai/issues/{date}/" if SITE else ""
    nupd = sum(len(w["updates"]) for w in d["watch"])
    closed = d.get("closed") or []
    opn = d.get("open") or []
    nav = f'<nav class="nav">{"<a href=\"#board\">榜單</a>" if d.get("leaderboards") else ""}{"<a href=\"#closed\">閉源模型</a>" if closed else ""}{"<a href=\"#open\">開源模型</a>" if opn else ""}{"<a href=\"#ainews\">AI 新聞</a>" if d.get("ainews") else ""}<a href="#watch">追蹤清單</a>{"<a href=\"#columns\">名家專欄</a>" if d.get("columns") else ""}{"<a href=\"#learn\">教學區</a>" if d.get("tutorials") else "<a href=\"#news\">其他新聞</a>"}{"<a href=\"#video\">推薦影片</a>" if d.get("video") else ""}<a href="#caveats">注意事項</a><a href="{aibase}archive/">往期</a></nav>'
    H = [head(title, d["lede"], f"{root}assets/style.css", canon, ogimg), '<body class="mode-ai">', topbar(root, "ai", aibase, nav)]
    H.append(f'''<main class="wrap">
<div class="mast"><div class="kicker">Issue No. {d['issue_no']:03d} · AI Model Digest</div>
<h1>AI Model Daily</h1>
<div class="meta"><span><b>{y} 年 {int(m)} 月 {int(dd)} 日</b> {e(d['weekday'])}</span><span>追蹤模型 {len(d['watch'])} 個 · 更新 {nupd} 則</span>{f"<span>閉源 {len(closed)} 則</span>" if closed else ""}{f"<span>開源 {len(opn)} 則</span>" if opn else ""}{f"<span>AI 新聞 {len(d['ainews'])} 則</span><span>教學 {len(d.get('tutorials') or [])} 篇</span>" if d.get("ainews") else f"<span>其他新聞 {len(d['news'])} 則</span>"}{f"<span>名家專欄 {len(d['columns'])} 則</span>" if d.get("columns") else ""}<span>推薦影片 {1 if d.get('video') else 0} 支</span></div>
<p class="lede">{e(d['lede'])}</p></div>''')
    n = 0
    # leaderboard module (unnumbered): every day, always at the very top, right after the masthead/lede
    H.append(leaderboard(d.get("leaderboards")))
    ainews = d.get("ainews")
    if ainews:   # v4 (from 2026-10-13 preview): one AI 新聞 section replaces 閉源/開源/其他新聞
        n += 1
        H.append(f'<section id="ainews">{sec_head(n, "AI 新聞", "AI News")}<div class="news">' + "".join(story(s, img) for s in ainews) + '</div></section>')
        closed, opn = [], []
    # closed-source models (from 2026-10-12; absent in older issues)
    if closed:
        n += 1
        H.append(f'<section id="closed">{sec_head(n, "閉源模型" if opn else "閉源模型動態", "Closed Models")}<div class="news">' + "".join(story(s, img) for s in closed) + '</div></section>')
    # open-source models (from 2026-10-12 v3)
    if opn:
        n += 1
        H.append(f'<section id="open">{sec_head(n, "開源模型", "Open Models")}<div class="news">' + "".join(story(s, img) for s in opn) + '</div></section>')
    # watch list (open-source)
    n += 1
    H.append(f'<section id="watch">{sec_head(n, "追蹤清單", "Watch List")}<div class="wgrid">')
    k = 0
    for w in d["watch"]:
        ups = []
        for u in w["updates"]:
            if u.get("one"):
                ups.append(f'<li class="upd lite"><div class="uhead"><span class="date">{e(u["date"])}</span><h4>{e(u.get("short_title") or u["title"])}</h4></div>'
                           f'<p class="one">{e(u["one"])}</p>{gloss(u.get("gloss"))}<details class="more"><summary>看更多</summary>{figure(u.get("image"), img, cls="uimg")}<p>{e(u["summary"])}</p><div class="src">{links(u["links"])}</div></details></li>')
                if u.get("image"): k += 1
                continue
            ups.append(f'<li class="upd"><div class="uhead"><span class="date">{e(u["date"])}</span><h4>{e(u["title"])}</h4></div>'
                       f'{figure(u.get("image"), img, eager=(k == 0), cls="uimg")}<p>{e(u["summary"])}</p><div class="src">{links(u["links"])}</div></li>')
            if u.get("image"): k += 1
        H.append(f'<article class="wcard" id="{e(w["id"])}"><div class="whead"><span class="tag">{e(w["kind"])}</span><span class="count">{f"{len(w['updates'])} 則更新" if w["updates"] else "今日無更新"}</span>'
                 f'<h3>{e(w["model"])}</h3><p class="status">{e(w["status"])}</p></div>{f'<ol class="ulist">{"".join(ups)}</ol>' if ups else ""}</article>')
    H.append('</div></section>')
    # 名家專欄 (creator picks): only when the issue has columns[]; absent/empty → hidden
    if d.get("columns"):
        n += 1
        H.append(f'<section id="columns">{sec_head(n, "名家專欄", "Creator Picks")}<p class="secnote">知名 AI 創作者近 7 天的實用工作流／工具分享，節錄重點；內容以原片／原文為準。</p><div class="news">' + "".join(column(c, img) for c in d["columns"]) + '</div></section>')
    # v4 tutorials
    if d.get("tutorials"):
        n += 1
        H.append(f'<section id="learn">{sec_head(n, "教學區", "Learn")}<div class="news">' + "".join(tutorial(t) for t in d["tutorials"]) + '</div></section>')
    # other news (pre-v4 only)
    if d["news"] and not ainews:
     n += 1
     H.append(f'<section id="news">{sec_head(n, "其他新聞", "More News")}<div class="news">' + "".join(story(s, img) for s in d["news"]) + '</div></section>')
    # 03 video
    v = d.get("video")
    if v:
        n += 1
        H.append(f'''<section id="video">{sec_head(n, "推薦影片", "Watch This")}
<div class="vid"><div class="vframe"><div class="ratio" id="yt" data-id="{e(v["youtube_id"])}"><a href="{e(v["url"])}" target="_blank" rel="noopener" class="play" aria-label="在 YouTube 播放：{e(v["title"])}"><img src="{img}{e(v["thumb"]["file"])}" alt="{e(v["thumb"]["alt"])}" loading="lazy" decoding="async" width="1280" height="720"><span class="pbtn">▶</span></a></div>
<p class="vcap">縮圖：{e(v["thumb"]["credit"])} · 點擊即在頁面內播放（youtube-nocookie）</p></div>
<div class="vtext"><span class="tag">{e(v["channel"])}</span><span class="date">{e(v["date"])}</span><h3>{e(v["title"])}</h3>{f'<p class="one">{e(v["one"])}</p>' if v.get("one") else f'<p class="orig">{e(v["orig"])}</p><p>{e(v["summary"])}</p>'}<div class="src"><a href="{e(v["url"])}" target="_blank" rel="noopener">在 YouTube 觀看 ↗</a></div></div></div>
<script>(function(){{var b=document.getElementById('yt');if(!b)return;b.querySelector('a').addEventListener('click',function(ev){{ev.preventDefault();var f=document.createElement('iframe');f.src='https://www.youtube-nocookie.com/embed/'+b.dataset.id+'?autoplay=1';f.title='YouTube video';f.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';f.allowFullscreen=true;b.innerHTML='';b.appendChild(f);}});}})();</script></section>''')
    # 04 caveats
    cv = "".join(f"<li>{e(c)}</li>" for c in d["caveats"])
    n += 1
    H.append(f'<section id="caveats">{sec_head(n, "注意事項", "Caveats")}<ul class="caveats">{cv}</ul></section>')
    prev = [x for x in all_issues if x["date"] < date][:7]
    li = archive_rows([(f'{aibase}issues/{x["date"]}/', None, x["issue_no"], x["date"], x["weekday"], ai_headline(x)) for x in prev], False)
    if prev: H.append(f'<section class="archive" id="archive"><div class="sec-head"><span class="num">∞</span><h2>往期</h2><span class="en">Archive</span><a class="amore" href="{aibase}archive/">全部往期 →</a></div><ul>{li}</ul></section>')
    H.append(f'''</main><footer><div class="wrap">AI Model Daily · 每日整理閉源與開源模型的重要發布、每週排行榜，並追蹤指定開源模型的更新與其他工具新聞。摘要為編輯整理，事實以原始來源為準；圖片取自官方或來源頁的分享圖（og:image），版權屬原權利人，均標示來源並連結原頁；不使用 AI 生成圖像代表真實產品。<br>Issue {d["issue_no"]:03d} · {date}</div></footer>
{theme_toggle("ai")}
</body></html>''')
    return "\n".join(H)

def ai_headline(x):
    for k in ("closed", "open", "ainews"):
        for st in x.get(k) or []:
            if st.get("title"): return st["title"]
    return "、".join(w["model"] for w in x["watch"])

def ai_cover(x, base_dir):
    ims = [st.get("image") for k in ("closed", "open", "ainews") for st in (x.get(k) or [])] + [u.get("image") for w in x["watch"] for u in w["updates"]]
    for im in ims:
        if im and im.get("file") and os.path.exists(f"{base_dir}/img/{im['file']}"): return f"{base_dir}/img/{im['file']}"
    return None

def archive_page(all_issues):
    rows = []
    for x in all_issues:
        bd = f"{ROOT}/ai/issues/{x['date']}"; src = ai_cover(x, bd)
        th = thumb_for(src, bd) if src else None
        kw = " ".join([st.get("org","") + " " + st.get("title","") for k in ("closed", "open", "ainews", "news") for st in (x.get(k) or []) if isinstance(st, dict)] + [w["model"] for w in x["watch"]] + [u.get("title","") for w in x["watch"] for u in w["updates"] if isinstance(u, dict)])
        rows.append((f'../issues/{x["date"]}/', f'../issues/{x["date"]}/{th}' if th else None, x["issue_no"], x["date"], x["weekday"], ai_headline(x), kw))
    li = archive_rows(rows, True)
    return f'''{head("往期 · AI Model Daily", "AI Model Daily 往期列表", "../../assets/style.css", f"{SITE}/ai/archive/" if SITE else "", "")}
<body class="mode-ai">{topbar("../../", "ai", "../")}
<main class="wrap"><section class="archive full"><div class="sec-head"><span class="num">∞</span><h2>往期</h2><span class="en">Archive</span></div>{li}</section></main>{theme_toggle("ai")}</body></html>'''

def prune_columns_log(latest):
    """名家專欄 30-day dedupe log: drop entries older than 30 days before the latest issue (runs on every build/publish)."""
    import datetime as dt
    p = f"{ROOT}/ai-columns-log.json"
    if not os.path.exists(p): return
    log = json.load(open(p, encoding="utf-8"))
    cut = (dt.date.fromisoformat(latest) - dt.timedelta(days=30)).isoformat()
    keep = [x for x in log if x.get("date", "") >= cut]
    if len(keep) != len(log):
        json.dump(keep, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"ai-columns-log: pruned {len(log) - len(keep)} entr(ies) older than {cut}")

if __name__ == "__main__":
    al = issues()
    prune_columns_log(al[0]["date"])
    for d in al:
        write_page(f"{ROOT}/ai/issues/{d['date']}/index.html", page(d, "../../../", "../../", al, False))
    write_page(f"{ROOT}/ai/index.html", page(al[0], "../", "./", al, True))
    os.makedirs(f"{ROOT}/ai/archive", exist_ok=True)
    write_page(f"{ROOT}/ai/archive/index.html", archive_page(al))
    check_wakelock()
    print("built ai", [d["date"] for d in al])
