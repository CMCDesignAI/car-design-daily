#!/usr/bin/env python3
"""Render static pages from issues/<date>/data.json.
Outputs: issues/<date>/index.html for every issue, root index.html (= latest issue), archive/index.html.
Usage: python3 tools/build.py [--site-url https://xxxx.flypod.page]"""
import json, os, glob, html, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = ""
if "--site-url" in sys.argv: SITE = sys.argv[sys.argv.index("--site-url")+1].rstrip("/")
e = html.escape
WD = ["週一","週二","週三","週四","週五","週六","週日"]

SWITCH_JS = """<script>(function(){var n=document.querySelector('.modes');if(!n)return;var cur=n.getAttribute('data-mode');
var rm=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
function reset(){n.classList.add('still');n.setAttribute('data-pos',cur);void n.offsetWidth;n.classList.remove('still');}
var from=null;try{from=sessionStorage.getItem('cdd-switch-from');sessionStorage.removeItem('cdd-switch-from');}catch(_){}
if(from&&from!==cur&&!rm)n.classList.add('arrive');
window.addEventListener('pageshow',function(ev){if(ev.persisted)reset();});
function dest(a){var u=new URL(a.getAttribute('href'),location.href);if(u.protocol==='file:'&&u.pathname.slice(-1)==='/')u.pathname+='index.html';return u.href;}
Array.prototype.forEach.call(n.querySelectorAll('a[data-mode]'),function(a){a.addEventListener('click',function(ev){
 if(ev.defaultPrevented||ev.button!==0||ev.metaKey||ev.ctrlKey||ev.shiftKey||ev.altKey)return;
 var to=a.getAttribute('data-mode'),url=dest(a);ev.preventDefault();
 if(to===cur||rm){location.href=url;return;}
 try{sessionStorage.setItem('cdd-switch-from',cur);}catch(_){}
 n.setAttribute('data-pos',to);var done=false,go=function(){if(done)return;done=true;location.href=url;};
 n.querySelector('.mind').addEventListener('transitionend',function(e){if(e.propertyName==='transform')go();});setTimeout(go,520);});});})();</script>"""

WAKE_MARK = 'assets/wakelock.js'
WRITTEN = []   # every page written by write_page in this run

def write_page(path, html_text):
    """Shared writer for EVERY generated page (car + ai). Injects the wake-lock <script> into <head>
    with the right relative path, so redesigns of headers/footers can never drop it. DO NOT bypass."""
    rel = os.path.relpath(os.path.dirname(os.path.abspath(path)), ROOT)
    depth = 0 if rel == "." else rel.count(os.sep) + 1
    tag = f'<script src="{"../" * depth}{WAKE_MARK}" defer></script>'
    if WAKE_MARK not in html_text:
        assert "</head>" in html_text, f"no </head> in {path}"
        html_text = html_text.replace("</head>", tag + "</head>", 1)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(html_text)
    WRITTEN.append(path)

def check_wakelock():
    """Fail loudly (exit 2) if any page written in this run lacks the wake lock, or the JS file is gone."""
    bad = []
    for p in WRITTEN:
        if WAKE_MARK not in open(p, encoding="utf-8").read(): bad.append(os.path.relpath(p, ROOT))
    if not os.path.exists(f"{ROOT}/{WAKE_MARK}"): bad.append(WAKE_MARK + " (file missing)")
    if bad:
        sys.stderr.write("WAKE LOCK MISSING: " + ", ".join(bad) + "\n"); sys.exit(2)
    print("wakelock ok")

def switcher(root, mode):
    """Segmented section switcher shown on every page. root = relative path to site root.
    Plain links (work without JS); SWITCH_JS slides the frame (.mind) to the target, then navigates."""
    def a(m, href, en, zh):
        cur = ' aria-current="page" class="on"' if m == mode else ''
        return f'<a href="{href}" data-mode="{m}"{cur}><b>{en}</b><span>{zh}</span></a>'
    return (f'<nav class="modes" data-mode="{mode}" data-pos="{mode}" aria-label="切換日報"><i class="mind" aria-hidden="true"></i>'
            f'{a("car", root, "Car Design", "汽車設計")}{a("ai", root + "ai/", "AI Models", "AI 模型")}</nav>')

def topbar(root, mode, brand_href, nav_html=""):
    brand = ('CAR DESIGN <span>DAILY</span>' if mode == "car" else 'AI MODEL <span>DAILY</span>')
    return (f'<header class="topbar"><div class="wrap"><a class="brand" href="{brand_href}">{brand}</a>'
            f'{switcher(root, mode)}{nav_html}<button class="toggle" id="tg" aria-label="切換深淺色">◐<span class="tl"> 深／淺</span></button></div></header>')

def theme_init(mode):
    key = "cdd-theme-ai" if mode == "ai" else "cdd-theme"
    dflt = "'dark'" if mode == "ai" else "null"
    return f"<script>(function(){{var t=localStorage.getItem('{key}')||{dflt};if(t)document.documentElement.setAttribute('data-theme',t);}})();</script>"

def theme_toggle(mode):
    key = "cdd-theme-ai" if mode == "ai" else "cdd-theme"
    return SWITCH_JS + ("<script>document.getElementById('tg').onclick=function(){var r=document.documentElement,c=r.getAttribute('data-theme');"
            "var dark=c?c==='dark':matchMedia('(prefers-color-scheme: dark)').matches;var n=dark?'light':'dark';"
            f"r.setAttribute('data-theme',n);localStorage.setItem('{key}',n);}};</script>")

def issues():
    out = []
    for p in sorted(glob.glob(f"{ROOT}/issues/*/data.json"), reverse=True):
        out.append(json.load(open(p, encoding="utf-8")))
    return out

def term_text(t):
    """Term body; optional t["source"] = [[name, url], ...] rendered as a small 出處 line."""
    if not t.get("source"):
        return f'<p>{e(t["body"])}</p>'
    src = "、".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(n)} ↗</a>' for n, u in t["source"])
    return f'<div><p>{e(t["body"])}</p><p class="tsrc">出處：{src}</p></div>'

def term_diagram(d, all_issues):
    """Per-issue term illustration: issues/<date>/<term.diagram> (inline SVG, class="diagram").
    Fails the build if missing, or if the same SVG is reused for a different term."""
    t = d["term"]; date = d["date"]
    fn = t.get("diagram")
    if not fn:
        sys.exit(f"[build] ERROR {date}: term.diagram missing — draw a new illustration for '{t['name']}' (issues/{date}/term.svg)")
    path = f"{ROOT}/issues/{date}/{fn}"
    if not os.path.exists(path):
        sys.exit(f"[build] ERROR {date}: term illustration not found: {path}")
    svg = open(path, encoding="utf-8").read().strip()
    if 'class="diagram"' not in svg:
        sys.exit(f"[build] ERROR {date}: {path} must be an <svg class=\"diagram\"> element")
    for o in all_issues:
        if o["date"] == date or "diagram" not in o.get("term", {}): continue
        op = f"{ROOT}/issues/{o['date']}/{o['term']['diagram']}"
        if os.path.exists(op) and open(op, encoding="utf-8").read().strip() == svg and o["term"]["name"] != t["name"]:
            sys.exit(f"[build] ERROR {date}: term '{t['name']}' reuses the illustration of {o['date']} ('{o['term']['name']}'). Draw a new one.")
    return svg


def page(d, base, all_issues, is_root):
    date = d["date"]; y, m, dd = date.split("-")
    img = f"{base}issues/{date}/img/" if is_root else "img/"
    css = f"{base}assets/style.css"
    title = f"Car Design Daily · {y}.{m}.{dd}"
    desc = d["lede"]
    lead = d["design_news"][0].get("image")
    ogimg = (f"{SITE}/issues/{date}/img/{lead['file']}" if lead else f"{SITE}/issues/{date}/img/{d['moodboards'][0]['images'][0][0]}.webp") if SITE else ""
    canon = (f"{SITE}/issues/{date}/" if SITE else "")
    H = []
    H.append(f'''<!doctype html><html lang="zh-Hant-TW"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<meta property="og:type" content="article"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
{f'<meta property="og:image" content="{ogimg}"><meta name="twitter:card" content="summary_large_image">' if ogimg else ''}
{f'<link rel="canonical" href="{canon}">' if canon else ''}
<meta name="theme-color" content="#111114">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Noto+Sans+TC:wght@400;600&family=Noto+Serif+TC:wght@600;700&family=Playfair+Display:ital,wght@0,700;0,800;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{css}">
{theme_init("car")}
</head><body class="mode-car">
{topbar(base, "car", base, f'<nav class="nav">{'<a href="#breaking">特報</a>' if d.get("breaking") else ''}<a href="#design">設計新聞</a>{'<a href="#cmf">色彩材質</a>' if d.get("cmf") else ''}<a href="#knowledge">汽車新知</a><a href="#mood">情緒板</a><a href="{base}archive/">往期</a></nav>')}
<main class="wrap">
<div class="mast"><div class="kicker">Issue No. {d['issue_no']:03d} · Global Car Design Digest</div>
<h1>Car Design Daily</h1>
<div class="meta"><span><b>{y} 年 {int(m)} 月 {int(dd)} 日</b> {d['weekday']}</span><span>設計新聞 {len(d['design_news'])} 則</span>{f"<span>色彩與材質 {len(d['cmf'])} 則</span>" if d.get('cmf') else ''}<span>汽車新知 {len(d['knowledge'])} 則</span><span>情緒板 {len(d['moodboards'])} 組</span></div>
<p class="lede">{e(d['lede'])}</p></div>''')
    # breaking news (optional; issues without "breaking" render exactly as before)
    bk = d.get("breaking")
    if bk:
        im = bk.get("image"); v = bk.get("video") or {}
        fig = (f'<figure class="news-img"><div class="ratio"><img src="{img}{e(im["file"])}" alt="{e(im["alt"])}" loading="eager" decoding="async" width="1600" height="900"></div>'
               f'<figcaption>圖片來源：<a href="{e(im["credit_url"])}" target="_blank" rel="noopener">{e(im["credit"])}</a></figcaption></figure>') if im else ""
        vlink = f'<p class="bk-vlink">▶ <a href="{e(v["url"])}" target="_blank" rel="noopener">{e(v.get("title","觀看影片"))} ↗</a></p>' if v.get("url") else ""
        if v.get("type") == "youtube":
            vid = f'<div class="bk-video"><div class="ratio"><iframe src="https://www.youtube-nocookie.com/embed/{e(v["id"])}" title="{e(v.get("title",""))}" allow="accelerometer; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>{vlink}</div>'
        elif v.get("mp4"):
            poster = f' poster="{img}{e(im["file"])}"' if im else ""
            vid = f'<div class="bk-video"><div class="ratio"><video controls playsinline preload="metadata"{poster} title="{e(v.get("title",""))}"><source src="{e(v["mp4"])}" type="video/mp4"></video></div>{vlink}</div>'
        elif v.get("url"):
            vid = (f'<div class="bk-video"><blockquote class="twitter-tweet" data-theme="dark" data-dnt="true" data-conversation="none"><a href="{e(v["url"])}">{e(v.get("title",""))}</a></blockquote>{vlink}</div>'
                   '<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>')
        else:
            vid = ""
        if vid:
            fig = ""  # video takes the hero position; no duplicate still image
        pts = "".join(f'<li>{e(x)}</li>' for x in bk["points"])
        src = "".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(n)} ↗</a>' for n, u in bk["sources"])
        H.append(f'<section id="breaking" class="breaking"><div class="bk-label">{e(bk.get("label","新車特報"))} · Breaking</div><article class="story bk-card">{vid}{fig}<div class="shead"><span class="tag">{e(bk["brand"])}</span><span class="date">{e(bk["date"])}</span><h3>{e(bk["title"])}</h3><ul class="cpts">{pts}</ul></div><div class="src">來源：{src}</div></article></section>')
    # design news
    H.append('<section id="design"><div class="sec-head"><span class="num">01</span><h2>設計新聞</h2><span class="en">Design News</span></div><div class="news">')
    for i, s in enumerate(d["design_news"]):
        an = "".join(f'<li><b>{e(k)}</b><span>{e(v)}</span></li>' for k, v in s["analysis"])
        src = "".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(n)} ↗</a>' for n, u in s["sources"])
        im = s.get("image")
        fig = (f'<figure class="news-img"><div class="ratio"><img src="{img}{e(im["file"])}" alt="{e(im["alt"])}" loading="{"eager" if i == 0 else "lazy"}" decoding="async" width="1600" height="900"></div>'
               f'<figcaption>圖片來源：<a href="{e(im["credit_url"])}" target="_blank" rel="noopener">{e(im["credit"])}</a></figcaption></figure>') if im else ""
        head = f'<div class="shead"><span class="tag">{e(s["brand"])} · {e(s["tag"])}</span><span class="date">{e(s["date"])}</span><h3>{e(s["title"])}</h3><p class="orig">{e(s["orig"])}</p><p class="sum">{e(s["summary"])}</p>'
        if i == 0:
            H.append(f'<article class="story feature" id="{s["id"]}">{fig}{head}<div class="src">來源：{src}</div></div><div class="fan"><p class="alabel">設計解析 Design Notes</p><ul class="analysis">{an}</ul></div></article>')
        else:
            H.append(f'<article class="story" id="{s["id"]}">{fig}{head}</div><p class="alabel">設計解析 Design Notes</p><ul class="analysis">{an}</ul><div class="src">來源：{src}</div></article>')
    H.append('</div></section>')
    # colour & material (optional; issues without "cmf" render exactly as before)
    cmf = d.get("cmf") or []
    n_k, n_m = ("03", "04") if cmf else ("02", "03")
    if cmf:
        H.append('<section id="cmf"><div class="sec-head"><span class="num">02</span><h2>色彩與材質</h2><span class="en">Colour &amp; Material</span></div><div class="cmf">')
        for c in cmf:
            im = c.get("image")
            fig = (f'<figure class="news-img"><div class="ratio"><img src="{img}{e(im["file"])}" alt="{e(im["alt"])}" loading="lazy" decoding="async" width="1600" height="900"></div>'
                   f'<figcaption>圖片來源：<a href="{e(im["credit_url"])}" target="_blank" rel="noopener">{e(im["credit"])}</a></figcaption></figure>') if im else ""
            pts = "".join(f'<li>{e(x)}</li>' for x in c["points"])
            src = "".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(n)} ↗</a>' for n, u in c["sources"])
            H.append(f'<article class="cmf-card" id="{e(c["id"])}">{fig}<div class="cbody"><span class="tag">{e(c["car"])} · {e(c["tag"])}</span><h3>{e(c["title"])}</h3><ul class="cpts">{pts}</ul><div class="src">來源：{src}</div></div></article>')
        H.append('</div></section>')
    # knowledge
    H.append(f'<section id="knowledge"><div class="sec-head"><span class="num">{n_k}</span><h2>汽車新知</h2><span class="en">Industry &amp; Tech</span></div><div class="kgrid">')
    for k in d["knowledge"]:
        src = "".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(n)} ↗</a>' for n, u in k["sources"])
        H.append(f'<article class="k"><span class="tag">{e(k["tag"])}</span><span class="date" style="font-size:12px;color:var(--muted);margin-left:8px">{e(k["date"])}</span><h3>{e(k["title"])}</h3><p>{e(k["summary"])}</p><div class="src">{src}</div></article>')
    t = d["term"]
    H.append(f'</div><div class="term"><div><div class="lab">今日設計名詞 · Term of the Day</div><h3>{e(t["name"])}</h3><div class="zh">{e(t["zh"])}</div>{term_diagram(d, all_issues)}</div>{term_text(t)}</div></section>')
    # mood boards
    H.append(f'<section id="mood"><div class="sec-head"><span class="num">{n_m}</span><h2>情緒板</h2><span class="en">Mood Boards</span></div>')
    H.append('<p class="note">情緒板裡的車輛都是原創虛構的概念設計，不代表任何真實車款或品牌。圖像為程式生成的插畫和材質紋理，主題每期隨機抽選。</p>')
    for b in d["moodboards"]:
        figs = "".join(f'<figure class="tile{" hero" if h else ""}"><img src="{img}{n}.webp" alt="{e(c)}" loading="lazy" decoding="async"><figcaption>{e(c)}</figcaption></figure>' for n, c, h in b["images"])
        pal = "".join(f'<div class="sw"><i style="background:{hx}"></i><span>{e(nm)}<br><code>{hx}</code></span></div>' for nm, hx in b["palette"])
        kw = "".join(f'<span>{e(k)}</span>' for k in b["keywords"])
        mt = "".join(f'<li>{e(x)}</li>' for x in b["materials"])
        H.append(f'<div class="board"><div class="board-head"><div><div class="kicker">Random Theme</div><h3>{e(b["theme"])}</h3><div class="zh">{e(b["zh"])}</div></div><p>{e(b["intro"])}</p></div><div class="mgrid">{figs}</div><div class="bwrap"><div class="palette">{pal}</div><div class="bmeta"><div><h4>關鍵字 Keywords</h4><div class="chips">{kw}</div></div><div><h4>材質筆記 Material Notes</h4><ul>{mt}</ul></div></div></div></div>')
    H.append('</section>')
    # archive
    li = "".join(f'<li><a href="{base}issues/{x["date"]}/">No.{x["issue_no"]:03d} · {x["date"]}</a> — {e(x["design_news"][0]["title"])}</li>' for x in all_issues)
    H.append(f'<section class="archive" id="archive"><div class="sec-head"><span class="num">∞</span><h2>往期</h2><span class="en">Archive</span></div><ul>{li}</ul></section>')
    H.append(f'''</main><footer><div class="wrap">Car Design Daily · 每日整理全球汽車設計新聞、產業新知與隨機情緒板。內容摘要與分析為編輯整理，事實以原始來源為準；新聞圖片取自車廠官方新聞室／原報導，版權屬原權利人，均標示來源並連結原頁。<br>Issue {d["issue_no"]:03d} · {date}</div></footer>
{theme_toggle("car")}
</body></html>''')
    return "\n".join(H)

def archive_page(all_issues):
    li = "".join(f'<li><a href="../issues/{x["date"]}/">No.{x["issue_no"]:03d} · {x["date"]} {x["weekday"]}</a> — {e(x["design_news"][0]["title"])}</li>' for x in all_issues)
    return f'''<!doctype html><html lang="zh-Hant-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>往期 · Car Design Daily</title><link rel="stylesheet" href="../assets/style.css">
{theme_init("car")}</head>
<body class="mode-car">{topbar("../", "car", "../")}
<main class="wrap"><section class="archive"><div class="sec-head"><span class="num">∞</span><h2>往期</h2><span class="en">Archive</span></div><ul>{li}</ul></section></main>{theme_toggle("car")}</body></html>'''

if __name__ == "__main__":
    al = issues()
    for d in al:
        write_page(f"{ROOT}/issues/{d['date']}/index.html", page(d, "../../", al, False))
    write_page(f"{ROOT}/index.html", page(al[0], "./", al, True))
    os.makedirs(f"{ROOT}/archive", exist_ok=True)
    write_page(f"{ROOT}/archive/index.html", archive_page(al))
    check_wakelock()
    print("built", [d["date"] for d in al])
