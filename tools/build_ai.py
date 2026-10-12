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
    nav = f'<nav class="nav"><a href="#watch">追蹤清單</a><a href="#news">其他新聞</a><a href="#video">推薦影片</a><a href="#caveats">注意事項</a><a href="{aibase}archive/">往期</a></nav>'
    H = [head(title, d["lede"], f"{root}assets/style.css", canon, ogimg), '<body class="mode-ai">', topbar(root, "ai", aibase, nav)]
    H.append(f'''<main class="wrap">
<div class="mast"><div class="kicker">Issue No. {d['issue_no']:03d} · AI Model Digest</div>
<h1>AI Model Daily</h1>
<div class="meta"><span><b>{y} 年 {int(m)} 月 {int(dd)} 日</b> {e(d['weekday'])}</span><span>追蹤模型 {len(d['watch'])} 個 · 更新 {nupd} 則</span><span>其他新聞 {len(d['news'])} 則</span><span>推薦影片 {1 if d.get('video') else 0} 支</span></div>
<p class="lede">{e(d['lede'])}</p></div>''')
    # 01 watch list
    H.append('<section id="watch"><div class="sec-head"><span class="num">01</span><h2>追蹤清單</h2><span class="en">Watch List</span></div><div class="wgrid">')
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
    # 02 other news
    H.append('<section id="news"><div class="sec-head"><span class="num">02</span><h2>其他新聞</h2><span class="en">More News</span></div><div class="news">')
    for s in d["news"]:
        H.append(f'<article class="story" id="{e(s["id"])}">{figure(s.get("image"), img)}<div class="shead"><span class="tag">{e(s["org"])} · {e(s["tag"])}</span><span class="date">{e(s["date"])}</span>'
                 f'<h3>{e(s["title"])}</h3><p class="orig">{e(s["orig"])}</p><p class="sum">{e(s["summary"])}</p></div>'
                 f'{"" if s.get("image") else "<p class=\"noimg\">來源頁沒有可用的官方圖片，因此不放圖。</p>"}<div class="src">來源：{links(s["links"])}</div></article>')
    H.append('</div></section>')
    # 03 video
    v = d.get("video")
    if v:
        H.append(f'''<section id="video"><div class="sec-head"><span class="num">03</span><h2>推薦影片</h2><span class="en">Watch This</span></div>
<div class="vid"><div class="vframe"><div class="ratio" id="yt" data-id="{e(v["youtube_id"])}"><a href="{e(v["url"])}" target="_blank" rel="noopener" class="play" aria-label="在 YouTube 播放：{e(v["title"])}"><img src="{img}{e(v["thumb"]["file"])}" alt="{e(v["thumb"]["alt"])}" loading="lazy" decoding="async" width="1280" height="720"><span class="pbtn">▶</span></a></div>
<p class="vcap">縮圖：{e(v["thumb"]["credit"])} · 點擊即在頁面內播放（youtube-nocookie）</p></div>
<div class="vtext"><span class="tag">{e(v["channel"])}</span><span class="date">{e(v["date"])}</span><h3>{e(v["title"])}</h3><p class="orig">{e(v["orig"])}</p><p>{e(v["summary"])}</p><div class="src"><a href="{e(v["url"])}" target="_blank" rel="noopener">在 YouTube 觀看 ↗</a></div></div></div>
<script>(function(){{var b=document.getElementById('yt');if(!b)return;b.querySelector('a').addEventListener('click',function(ev){{ev.preventDefault();var f=document.createElement('iframe');f.src='https://www.youtube-nocookie.com/embed/'+b.dataset.id+'?autoplay=1';f.title='YouTube video';f.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';f.allowFullscreen=true;b.innerHTML='';b.appendChild(f);}});}})();</script></section>''')
    # 04 caveats
    cv = "".join(f"<li>{e(c)}</li>" for c in d["caveats"])
    H.append(f'<section id="caveats"><div class="sec-head"><span class="num">04</span><h2>注意事項</h2><span class="en">Caveats</span></div><ul class="caveats">{cv}</ul></section>')
    li = "".join(f'<li><a href="{aibase}issues/{x["date"]}/">No.{x["issue_no"]:03d} · {x["date"]}</a> — {e(x["watch"][0]["model"])} 等 {len(x["watch"])} 個追蹤模型</li>' for x in all_issues)
    H.append(f'<section class="archive" id="archive"><div class="sec-head"><span class="num">∞</span><h2>往期</h2><span class="en">Archive</span></div><ul>{li}</ul></section>')
    H.append(f'''</main><footer><div class="wrap">AI Model Daily · 每日追蹤指定 AI 模型的更新與其他重要模型新聞。摘要為編輯整理，事實以原始來源為準；圖片取自官方或來源頁的分享圖（og:image），版權屬原權利人，均標示來源並連結原頁；不使用 AI 生成圖像代表真實產品。<br>Issue {d["issue_no"]:03d} · {date}</div></footer>
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
