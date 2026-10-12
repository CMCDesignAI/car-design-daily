#!/usr/bin/env python3
"""Render the AI Model Daily section from ai/issues/<date>/data.json.
Outputs: ai/issues/<date>/index.html for every issue, ai/index.html (= latest issue), ai/archive/index.html.
Shares assets/style.css and the topbar/switcher with tools/build.py (car section).
Usage: python3 tools/build_ai.py [--site-url https://user.github.io/repo]"""
import json, os, glob, html, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import topbar, theme_init, theme_toggle, ROOT, SITE
e = html.escape
FONTS = '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Noto+Sans+TC:wght@400;600;700&family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">'

def issues():
    return [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(f"{ROOT}/ai/issues/*/data.json"), reverse=True)]

def links(ls):
    return "".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(n)} ↗</a>' for n, u in ls)

def figure(im, img, eager=False, cls="news-img"):
    if not im: return ""
    return (f'<figure class="{cls}"><div class="ratio"><img src="{img}{e(im["file"])}" alt="{e(im["alt"])}" loading="{"eager" if eager else "lazy"}" decoding="async" width="1600" height="900"></div>'
            f'<figcaption>圖片來源：<a href="{e(im["credit_url"])}" target="_blank" rel="noopener">{e(im["credit"])}</a></figcaption></figure>')

def story(s, img):
    return (f'<article class="story" id="{e(s["id"])}">{figure(s.get("image"), img)}<div class="shead"><span class="tag">{e(s["org"])} · {e(s["tag"])}</span><span class="date">{e(s["date"])}</span>'
            f'<h3>{e(s["title"])}</h3><p class="orig">{e(s["orig"])}</p><p class="sum">{e(s["summary"])}</p></div>'
            f'{"" if s.get("image") else "<p class=\"noimg\">來源頁沒有可用的官方圖片，因此不放圖。</p>"}<div class="src">來源：{links(s["links"])}</div></article>')

def sec_head(n, zh, en):
    return f'<div class="sec-head"><span class="num">{n:02d}</span><h2>{zh}</h2><span class="en">{en}</span></div>'

def lb_chart(b):
    """Horizontal bar chart (inline SVG) for one leaderboard. Rows flagged "new"/"up" get highlighted."""
    rows = b["rows"][:10]
    hi, lo = max(r["score"] for r in rows), min(r["score"] for r in rows)
    base = lo - max(8, round((hi - lo) * 0.5))          # axis floor so gaps stay readable
    W, L, R, rh, top = 720, 300, 70, 34, 6
    bw = W - L - R
    g = []
    for i, r in enumerate(rows):
        y = top + i * rh
        w = max(4, bw * (r["score"] - base) / (hi - base))
        cls = "lb-bar" + (" lead" if i == 0 else "") + (" chg" if r.get("new") or r.get("up") else "")
        tag = " · 新進" if r.get("new") else (" · 上升" if r.get("up") else "")
        pre = " · 暫定" if r.get("note") == "Preliminary" else ""
        g.append(f'<text class="lb-rank" x="0" y="{y+21}">{r["rank"]:02d}</text>'
                 f'<text class="lb-name" x="34" y="{y+15}">{e(r["model"])}</text><text class="lb-org" x="34" y="{y+29}">{e(r["org"])}{pre}{tag}</text>'
                 f'<rect class="{cls}" x="{L}" y="{y+8}" width="{w:.1f}" height="16" rx="3"></rect>'
                 f'<text class="lb-score" x="{L+w+8:.1f}" y="{y+21}">{r["score"]}{f" ±{r[chr(99)+chr(105)]}" if r.get("ci") else ""}</text>')
    H = top + len(rows) * rh + 4
    return (f'<figure class="lbcard"><figcaption class="lbhead"><h3>{e(b["title"])}</h3><span class="en">{e(b["en"])}</span></figcaption>'
            f'<svg class="lbsvg" viewBox="0 0 {W} {H}" role="img" aria-label="{e(b["title"])} 前 10 名">{"".join(g)}</svg>'
            f'<p class="lbsrc">來源：<a href="{e(b["source_url"])}" target="_blank" rel="noopener">{e(b["source"])} ↗</a> · 資料更新 {e(b["as_of"])} · 抓取 {e(b["fetched"])} · 軸起點 {base}</p></figure>')

def leaderboard(lb):
    if not lb: return ""
    head_ = '<section id="board"><div class="sec-head"><span class="num">≡</span><h2>本週榜單</h2><span class="en">Leaderboards</span></div>'
    if lb.get("mode") == "note":
        return head_ + f'<p class="lbnote">{e(lb["note"])}</p></section>'
    chg = "".join(f"<li>{e(c)}</li>" for c in lb.get("changes", []))
    return (head_ + (f'<ul class="lbchg">{chg}</ul>' if chg else "")
            + '<div class="lbgrid">' + "".join(lb_chart(b) for b in lb["boards"]) + '</div></section>')

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
    nav = f'<nav class="nav">{"<a href=\"#closed\">閉源模型</a>" if closed else ""}{"<a href=\"#board\">榜單</a>" if d.get("leaderboards") else ""}{"<a href=\"#open\">開源模型</a>" if opn else ""}<a href="#watch">追蹤清單</a><a href="#news">其他新聞</a><a href="#video">推薦影片</a><a href="#caveats">注意事項</a><a href="{aibase}archive/">往期</a></nav>'
    H = [head(title, d["lede"], f"{root}assets/style.css", canon, ogimg), '<body class="mode-ai">', topbar(root, "ai", aibase, nav)]
    H.append(f'''<main class="wrap">
<div class="mast"><div class="kicker">Issue No. {d['issue_no']:03d} · AI Model Digest</div>
<h1>AI Model Daily</h1>
<div class="meta"><span><b>{y} 年 {int(m)} 月 {int(dd)} 日</b> {e(d['weekday'])}</span><span>追蹤模型 {len(d['watch'])} 個 · 更新 {nupd} 則</span>{f"<span>閉源 {len(closed)} 則</span>" if closed else ""}{f"<span>開源 {len(opn)} 則</span>" if opn else ""}<span>其他新聞 {len(d['news'])} 則</span><span>推薦影片 {1 if d.get('video') else 0} 支</span></div>
<p class="lede">{e(d['lede'])}</p></div>''')
    n = 0
    # closed-source models (from 2026-10-12; absent in older issues)
    if closed:
        n += 1
        H.append(f'<section id="closed">{sec_head(n, "閉源模型" if opn else "閉源模型動態", "Closed Models")}<div class="news">' + "".join(story(s, img) for s in closed) + '</div></section>')
    # leaderboard module (unnumbered), right after the closed section
    H.append(leaderboard(d.get("leaderboards")))
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
            ups.append(f'<li class="upd"><div class="uhead"><span class="date">{e(u["date"])}</span><h4>{e(u["title"])}</h4></div>'
                       f'{figure(u.get("image"), img, eager=(k == 0), cls="uimg")}<p>{e(u["summary"])}</p><div class="src">{links(u["links"])}</div></li>')
            if u.get("image"): k += 1
        H.append(f'<article class="wcard" id="{e(w["id"])}"><div class="whead"><span class="tag">{e(w["kind"])}</span><span class="count">{len(w["updates"])} 則更新</span>'
                 f'<h3>{e(w["model"])}</h3><p class="status">{e(w["status"])}</p></div><ol class="ulist">{"".join(ups)}</ol></article>')
    H.append('</div></section>')
    # other news
    n += 1
    H.append(f'<section id="news">{sec_head(n, "其他新聞", "More News")}<div class="news">' + "".join(story(s, img) for s in d["news"]) + '</div></section>')
    # 03 video
    v = d.get("video")
    if v:
        n += 1
        H.append(f'''<section id="video">{sec_head(n, "推薦影片", "Watch This")}
<div class="vid"><div class="vframe"><div class="ratio" id="yt" data-id="{e(v["youtube_id"])}"><a href="{e(v["url"])}" target="_blank" rel="noopener" class="play" aria-label="在 YouTube 播放：{e(v["title"])}"><img src="{img}{e(v["thumb"]["file"])}" alt="{e(v["thumb"]["alt"])}" loading="lazy" decoding="async" width="1280" height="720"><span class="pbtn">▶</span></a></div>
<p class="vcap">縮圖：{e(v["thumb"]["credit"])} · 點擊即在頁面內播放（youtube-nocookie）</p></div>
<div class="vtext"><span class="tag">{e(v["channel"])}</span><span class="date">{e(v["date"])}</span><h3>{e(v["title"])}</h3><p class="orig">{e(v["orig"])}</p><p>{e(v["summary"])}</p><div class="src"><a href="{e(v["url"])}" target="_blank" rel="noopener">在 YouTube 觀看 ↗</a></div></div></div>
<script>(function(){{var b=document.getElementById('yt');if(!b)return;b.querySelector('a').addEventListener('click',function(ev){{ev.preventDefault();var f=document.createElement('iframe');f.src='https://www.youtube-nocookie.com/embed/'+b.dataset.id+'?autoplay=1';f.title='YouTube video';f.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';f.allowFullscreen=true;b.innerHTML='';b.appendChild(f);}});}})();</script></section>''')
    # 04 caveats
    cv = "".join(f"<li>{e(c)}</li>" for c in d["caveats"])
    n += 1
    H.append(f'<section id="caveats">{sec_head(n, "注意事項", "Caveats")}<ul class="caveats">{cv}</ul></section>')
    li = "".join(f'<li><a href="{aibase}issues/{x["date"]}/">No.{x["issue_no"]:03d} · {x["date"]}</a> — {e(x["watch"][0]["model"])} 等 {len(x["watch"])} 個追蹤模型</li>' for x in all_issues)
    H.append(f'<section class="archive" id="archive"><div class="sec-head"><span class="num">∞</span><h2>往期</h2><span class="en">Archive</span></div><ul>{li}</ul></section>')
    H.append(f'''</main><footer><div class="wrap">AI Model Daily · 每日整理閉源與開源模型的重要發布、每週排行榜，並追蹤指定開源模型的更新與其他工具新聞。摘要為編輯整理，事實以原始來源為準；圖片取自官方或來源頁的分享圖（og:image），版權屬原權利人，均標示來源並連結原頁；不使用 AI 生成圖像代表真實產品。<br>Issue {d["issue_no"]:03d} · {date}</div></footer>
{theme_toggle("ai")}
</body></html>''')
    return "\n".join(H)

def archive_page(all_issues):
    li = "".join(f'<li><a href="../issues/{x["date"]}/">No.{x["issue_no"]:03d} · {x["date"]} {e(x["weekday"])}</a> — {e("、".join(w["model"] for w in x["watch"]))}</li>' for x in all_issues)
    return f'''{head("往期 · AI Model Daily", "AI Model Daily 往期列表", "../../assets/style.css", f"{SITE}/ai/archive/" if SITE else "", "")}
<body class="mode-ai">{topbar("../../", "ai", "../")}
<main class="wrap"><section class="archive"><div class="sec-head"><span class="num">∞</span><h2>往期</h2><span class="en">Archive</span></div><ul>{li}</ul></section></main>{theme_toggle("ai")}</body></html>'''

if __name__ == "__main__":
    al = issues()
    for d in al:
        open(f"{ROOT}/ai/issues/{d['date']}/index.html", "w", encoding="utf-8").write(page(d, "../../../", "../../", al, False))
    open(f"{ROOT}/ai/index.html", "w", encoding="utf-8").write(page(al[0], "../", "./", al, True))
    os.makedirs(f"{ROOT}/ai/archive", exist_ok=True)
    open(f"{ROOT}/ai/archive/index.html", "w", encoding="utf-8").write(archive_page(al))
    print("built ai", [d["date"] for d in al])
