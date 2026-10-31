#!/usr/bin/env python3
"""Render static pages from issues/<date>/data.json.
Outputs: issues/<date>/index.html for every issue, root index.html (= latest issue), archive/index.html.
Usage: python3 tools/build.py [--site-url https://xxxx.flypod.page]"""
import json, os, glob, html, sys, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = ""
if "--site-url" in sys.argv: SITE = sys.argv[sys.argv.index("--site-url")+1].rstrip("/")
e = html.escape
# Seasonal decorations, one line per holiday: start/end inclusive (YYYY-MM-DD, Asia/Taipei),
# logo = (file in assets/, width, height), or logo_light + logo_dark for per-theme versions; section_suffix = emoji after numbered section titles or "".
SEASONAL = [
    dict(start="2026-10-31", end="2026-11-02", logo_light=("cdd-halloween2-light.webp", 1400, 538), logo_dark=("cdd-halloween2-dark.webp", 1400, 538), section_suffix="🎃"),  # Halloween
]
def seasonal(date):
    return next((x for x in SEASONAL if x["start"] <= date <= x["end"]), {})
def sec_suffix(date):
    sfx = seasonal(date).get("section_suffix")
    return f'<span class="sec-sfx" aria-hidden="true">{sfx}</span>' if sfx else ""
def taipei_today():
    """Build date in Asia/Taipei; override with CDD_BUILD_DATE=YYYY-MM-DD for testing."""
    import datetime
    return os.environ.get("CDD_BUILD_DATE") or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d")
def masthead_title(date, base):
    def img(lg, cls=""):
        fn, w, h = lg
        return f'<img{cls} src="{base}assets/{fn}" alt="Car Design Daily" width="{w}" height="{h}" decoding="async">'
    sx = seasonal(date)
    if sx.get("logo_light") and sx.get("logo_dark"):  # CSS shows the one matching the active theme (display:none hides the other from AT)
        return f'<h1 class="mast-logo">{img(sx["logo_light"], " class=\"lg-light\"")}{img(sx["logo_dark"], " class=\"lg-dark\"")}</h1>'
    if sx.get("logo"):
        return f'<h1 class="mast-logo">{img(sx["logo"])}</h1>'
    return '<h1>Car Design Daily</h1>'

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

CAR_PATHS={
 "suv":("M30 118 L40 78 L80 52 L210 48 L250 78 L282 86 L290 118 Z","M88 60 L200 57 L232 80 L82 82 Z","M214 82 L282 92"),
 "sport":("M18 120 L28 100 L110 72 L180 70 L250 92 L298 104 L300 120 Z","M118 78 L176 76 L214 94 L106 96 Z","M30 108 L298 112"),
 "ev":("M50 118 L56 80 L96 50 L196 50 L236 82 L262 92 L266 118 Z","M102 58 L190 58 L220 84 L96 84 Z","M60 100 L262 100")}
def car_svg(t,body,acc,win):
    b,w,l=CAR_PATHS[t]
    return (f'<svg viewBox="0 0 320 150" class="carsvg" role="img" aria-label="示意車型剪影"><ellipse cx="160" cy="132" rx="140" ry="7" fill="#0002"/>'
      f'<path d="{b}" fill="{body}" stroke="#0005"/><path d="{w}" fill="{win}" opacity=".85"/><path d="{l}" stroke="{acc}" stroke-width="5" fill="none"/>'
      f'<path d="M24 116 L300 116" stroke="{acc}" stroke-width="6"/>'
      + "".join(f'<circle cx="{x}" cy="120" r="19" fill="#1b1b1b"/><circle cx="{x}" cy="120" r="9" fill="{acc}"/>' for x in ((82,238) if t!="sport" else (78,248))) + '</svg>')
def apps_html(apps):
    if not apps: return ""
    ee=html.escape
    def sw(lab,n,hx,off): return f'<div class="asw"><i style="background:{hx}"></i><span><small>{lab}</small>{ee(n)}<code>{hx}{"（官方）" if off else "（示意色）"}</code></span></div>'
    out=[]
    for a in apps:
        win=a["interior"][0][1]
        sws=sw("車身",*a["body"])+sw("飾條",*a["accent"])+"".join(sw("內裝",*x) for x in a["interior"])
        src="".join(f'<a href="{ee(u)}" target="_blank" rel="noopener">{ee(n)} ↗</a>' for n,u in a["src"])
        out.append(f'<article class="app">{car_svg(a["type"],a["body"][1],a["accent"][1],win)}<h4>{ee(a["name"])}</h4><div class="asws">{sws}</div><p>{ee(a["why"])}</p><div class="src">來源：{src}</div></article>')
    return '<h4 class="apph">配色應用示例 · 依上方數據套用到車型（剪影與配色為示意）</h4><div class="apps">'+"".join(out)+'</div>'

IP_HL_MODE = "dark"   # interactive highlight style for the combined drawing: "glow" (halo outline) | "dark" (darken the rest)
TOOL_FROM = "2026-10-19"       # issues on/after this date drop the 內裝配色 module; the palette lives in the 小工具 page (tool/)
COMBINED_FROM = "2026-10-19"   # issues on/after this date use the single combined perspective drawing
# combined drawing colour rules: headliner is one of two fixed presets; carpet is fixed black (in the SVG);
# door main colour (door-upper) always = ip-upper
HEADLINER_PRESETS = {"light": ("#C8CBD0", "#DCDFE3"), "dark": ("#4A4E55", "#61666E")}
def headliner_preset(val):
    """'light'|'dark' (default light). Legacy hex values are normalised by luminance (check_cmf.py rejects them)."""
    if val in (None, ""): return "light"
    if val in HEADLINER_PRESETS: return val
    h = str(val).lstrip("#")
    try:
        r_, g_, b_ = (int(h[i:i+2], 16) for i in (0, 2, 4)); lum = .2126*r_ + .7152*g_ + .0722*b_
    except Exception:
        lum = 255
    k = "light" if lum >= 128 else "dark"
    print(f"[build] WARN interior headliner {val!r} not 'light'/'dark' -> using {k}", file=sys.stderr)
    return k

IP_HL_JS = """<script>(()=>{const m=document.currentScript.closest('.ipalette'),s=m&&m.querySelector('.intcombo svg');if(!s)return;const NS='http://www.w3.org/2000/svg',L=[...s.querySelectorAll('[data-v]')].filter(e=>!e.closest('defs,clipPath,pattern'));const A=[...s.querySelectorAll('path,rect,circle,ellipse')].filter(e=>!e.closest('defs,clipPath,pattern'));const B=[...m.querySelectorAll('[data-hl]')];let pin=null,ov=null;const hov=matchMedia('(hover:hover)');const dark=!!s.closest('.hl-dark');const show=k=>{if(ov){ov.remove();ov=null}B.forEach(b=>b.setAttribute('aria-pressed',String(pin!==null&&b.dataset.hl===pin)));if(dark){const v=k?k.split(' '):null;A.forEach(e=>e.classList.toggle('hl-dim',!!v&&!v.includes(e.dataset.v)));return}if(!k)return;const v=k.split(' '),inv=s.getScreenCTM().inverse(),seen=new Set();ov=document.createElementNS(NS,'g');ov.setAttribute('class','hl-ov');ov.setAttribute('pointer-events','none');ov.setAttribute('filter','url(#hlglow)');L.forEach(e=>{if(!v.includes(e.dataset.v))return;const t=inv.multiply(e.getScreenCTM()),c=e.cloneNode(false);['fill','stroke','stroke-width','stroke-dasharray','opacity','fill-opacity','stroke-opacity','class','data-v','transform','style','filter'].forEach(a=>c.removeAttribute(a));c.setAttribute('transform',`matrix(${t.a} ${t.b} ${t.c} ${t.d} ${t.e} ${t.f})`);const key=c.outerHTML;if(seen.has(key))return;seen.add(key);c.setAttribute('fill','none');c.setAttribute('stroke','#fff');c.setAttribute('stroke-width','2.5');c.setAttribute('stroke-linejoin','round');c.setAttribute('vector-effect','non-scaling-stroke');ov.appendChild(c)});s.appendChild(ov)};B.forEach(b=>{b.addEventListener('click',e=>{e.stopPropagation();pin=pin===b.dataset.hl?null:b.dataset.hl;show(pin)});b.addEventListener('mouseenter',()=>{if(hov.matches&&pin===null)show(b.dataset.hl)});b.addEventListener('mouseleave',()=>{if(pin===null)show(null)})});document.addEventListener('click',e=>{if(pin!==null&&!e.target.closest('[data-hl]')){pin=null;show(null)}});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&pin!==null){pin=null;show(null)}})})()</script>"""

INT_ALIAS = [("ip-lower","door-lower"),("door-upper","ip-upper"),("console","door-lower"),("seat","door-insert"),("steering","door-lower"),("headliner","door-insert"),("seat-bolster","seat"),("seat-center","seat"),("console-arm","armrest"),("accent-pod","ip-decor"),("accent-pod2","accent-pod")]
def tool_palette(b, date):
    """Resolved colour variables of one issue's interior palette for the 小工具 page (combined-drawing rules applied)."""
    v={pt[4]:pt[2] for pt in b["parts"]}; v.update({k:x for k,x in b.get("vars",{}).items() if k!="headliner"})
    for k,fb in INT_ALIAS: v.setdefault(k,v.get(fb,"#888888"))
    hv=b.get("vars",{}).get("headliner"); hk=hv if hv in HEADLINER_PRESETS else ("light" if not hv else None)
    if hk is None:
        h=str(hv).lstrip("#")
        try: r_,g_,b_=(int(h[i:i+2],16) for i in (0,2,4)); hk="light" if .2126*r_+.7152*g_+.0722*b_>=128 else "dark"
        except Exception: hk="light"
    v.pop("headliner",None); v["door-upper"]=v["ip-upper"]
    return {"date":date,"theme":b["theme"],"zh":b["zh"],"mood":b.get("mood",[]),"headliner":hk,
            "vars":{k:x.upper() for k,x in v.items() if isinstance(x,str) and x.startswith("#")},
            "names":{pt[4]:[pt[0],pt[1]] for pt in b["parts"]}}

def tool_page(al):
    pals=[tool_palette(d["color_data"]["interior"],d["date"]) for d in al if (d.get("color_data") or {}).get("interior")]
    os.makedirs(f"{ROOT}/tool", exist_ok=True); open(f"{ROOT}/tool/palettes.js","w",encoding="utf-8").write("/* generated by tools/build.py: daily interior palettes, newest first */\nwindow.CDD_PALETTES="+json.dumps(pals,ensure_ascii=False,separators=(",",":"))+";\n")
    svg=open(os.path.join(ROOT,"assets","ip-combined-template.svg"),encoding="utf-8").read()
    hl=json.dumps(HEADLINER_PRESETS)
    return f'''<!doctype html><html lang="zh-Hant-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>小工具 · 內裝配色 · Car Design Daily</title><meta name="description" content="內裝配色小工具：輸入情緒關鍵字產生配色，逐部位調色、換材質，即時套到車室透視插圖。純前端、離線可用。">
<meta name="theme-color" content="#111114">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Noto+Sans+TC:wght@400;600&family=Noto+Serif+TC:wght@600;700&family=Playfair+Display:ital,wght@0,700;0,800;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/style.css"><link rel="stylesheet" href="tool.css">
{theme_init("car")}</head>
<body class="mode-car tool-page">{topbar("../", "car", "../", '<nav class="nav"><a href="../#design">設計新聞</a><a href="../#cmf">色彩材質</a><a href="../#knowledge">汽車新知</a><a href="./" aria-current="page">小工具</a><a href="../archive/">往期</a></nav>')}
<main class="wrap">
<nav class="tswitch" aria-label="小工具"><a href="./" aria-current="page">內裝配色</a><a href="parts/">零件圖庫</a></nav>
<div class="tmast"><div class="kicker">Tools · Interior Colour Studio</div><h1>小工具 · 內裝配色</h1>
<p class="tlede">輸入情緒關鍵字產生配色組合，或從每日配色開始；把色票拖到部位上、輸入 HEX 或用色盤調整，再為每個部位換材質。插圖即時更新。全部在瀏覽器裡完成，不連伺服器、不用 AI。</p></div>
<div class="tstage"><div class="intcombo hl-dark" id="cab">{svg}</div>
<div class="tbar"><span id="curname" class="tcur"></span><span class="tsp"></span><div class="seg" role="group" aria-label="頂棚"><span>頂棚</span><button type="button" data-hd="light" aria-pressed="true">淺灰</button><button type="button" data-hd="dark" aria-pressed="false">深灰</button></div></div></div>
<div class="tgrid">
<section class="tcol" aria-labelledby="h-mood"><h2 id="h-mood">情緒關鍵字 <small>Mood</small></h2>
<div class="kwbox"><div class="kwchips" id="kwchips"></div><input id="kw" type="text" autocomplete="off" placeholder="例：戶外、深藍、寧靜、luxury…" aria-label="情緒關鍵字" aria-autocomplete="list" aria-controls="kwsug" role="combobox" aria-expanded="false"><ul id="kwsug" role="listbox" hidden></ul></div>
<div class="kwhint" id="kwhint"></div>
<div class="combos" id="combos"></div>
<h3>每日配色 <small>Daily presets</small></h3><div class="presets" id="presets"></div></section>
<section class="tcol" aria-labelledby="h-parts"><h2 id="h-parts">部位 <small>Parts</small></h2>
<p class="thelp">點部位或插圖選取（其餘變暗）；把色票拖到部位或插圖上即可換色，手機可先點色票再點部位。</p>
<ul class="parts" id="parts"></ul>
<p class="trule">固定規則：地毯固定深黑 <code>#141516</code>；頂棚只能淺灰 <code>{HEADLINER_PRESETS["light"][0]}</code> 或深灰 <code>{HEADLINER_PRESETS["dark"][0]}</code>；門板主色永遠跟隨上儀表板（ip-upper）。</p></section>
<section class="tcol" aria-labelledby="h-pick"><h2 id="h-pick">調色 <small>Colour &amp; Material</small></h2>
<div class="picker" id="picker"><div class="pk-head"><i id="pkchip"></i><b id="pkname">選一個部位</b></div>
<div class="sv" id="sv" role="slider" tabindex="0" aria-label="飽和度與明度"><div class="svk" id="svk"></div></div>
<div class="thue" id="hue" role="slider" tabindex="0" aria-label="色相" aria-valuemin="0" aria-valuemax="360"><div class="hk" id="hk"></div></div>
<div class="pk-row"><label>HEX <input id="hex" type="text" maxlength="7" spellcheck="false" autocomplete="off"></label><label>H <input id="ih" type="number" min="0" max="360"></label><label>S <input id="is" type="number" min="0" max="100"></label><label>L <input id="il" type="number" min="0" max="100"></label></div>
<label class="pk-mat">材質 <select id="mat"></select></label></div>
<h3>匯出 <small>Export</small></h3><div class="exp"><button type="button" id="cpjson">複製 JSON</button><button type="button" id="cphex">複製 HEX 清單</button><button type="button" id="cpurl">複製分享連結</button><button type="button" id="reset">重設為今日配色</button></div><p class="thelp" id="expmsg" aria-live="polite"></p></section>
</div>
<p class="note">插圖為程式繪製示意，不代表任何真實車款；顏色為螢幕示意，請以實體色卡為準。</p>
</main>
<script>(()=>{{const f=()=>{{const t=document.querySelector(".topbar");if(t)document.documentElement.style.setProperty("--tbh",t.offsetHeight+"px")}};f();addEventListener("resize",f)}})()</script><script>window.CDD_HEADLINER={hl};</script><script src="palettes.js"></script><script src="moods.js"></script><script src="interior.js"></script>
{theme_toggle("car")}</body></html>'''

def interior_html(b, date=""):
    if not b: return ""
    ee=html.escape; c=[x[2] for x in b["parts"]]
    v={pt[4]:pt[2] for pt in b["parts"]}; v.update(b.get("vars",{}))
    alias={}
    for k,fb in [("ip-lower","door-lower"),("door-upper","ip-upper"),("console","door-lower"),("seat","door-insert"),("steering","door-lower"),("headliner","door-insert"),("seat-bolster","seat"),("seat-center","seat"),("console-arm","armrest"),("accent-pod","ip-decor"),("accent-pod2","accent-pod")]:
        if k not in v: alias[k]=fb
        v.setdefault(k,v.get(fb,"#888"))
    rd=lambda f: open(os.path.join(ROOT,"assets",f),encoding="utf-8").read()
    style=";".join(f"--{k}:{x}" for k,x in v.items())
    if date >= COMBINED_FROM:
      vc=dict(v); vc["door-upper"]=vc.get("ip-upper",vc.get("door-upper")); alias["door-upper"]="ip-upper"
      hl=HEADLINER_PRESETS[headliner_preset(b.get("vars",{}).get("headliner"))]
      vc["headliner"],vc["headliner-hi"]=hl
      style=";".join(f"--{k}:{x}" for k,x in vc.items())
      svg=(f'<div class="intpair intcombo hl-{IP_HL_MODE}" style="{style}">'
         f'<figure><div class="intwrap">{rd("ip-combined-template.svg")}</div><figcaption>車室透視（門板・車窗・A/B 柱・方正儀表台・中控塔與平板螢幕・方形出風口・杯架點綴・方向盤・座椅・中央扶手）</figcaption></figure></div>')
    else:
     svg=(f'<div class="intpair" style="{style}">'
         f'<figure><div class="intwrap">{rd("door-template.svg")}</div><figcaption>前門板（上飾板・飾條・嵌飾・門把・扶手開關座・拉手凹槽・喇叭網・置物袋・縫線）</figcaption></figure>'
         f'<figure><div class="intwrap">{rd("ip-template.svg")}</div><figcaption>儀表板正視（方正儀表台・中控塔・方形出風口・杯架點綴・方向盤・座椅・中央扶手）</figcaption></figure></div>')
    evmap={}
    for it in b.get("evidence",[]):
        nm,_,src=it[0].partition("："); evmap[nm]=(src.split("（")[0] or it[0],it[1])
    def swc(p):
        pt,nm,hx,off=p[:4]; ev=(p[5]["src"],p[5]["url"]) if len(p)>5 and p[5] else evmap.get(nm)
        tag="（官方）" if off else "（示意色）"
        sub=f'<small class="evs">{ee(ev[0])}{tag}{" ↗"}</small>' if ev else f'<small class="evs">示意色</small>'
        inner=f'<i style="background:{hx}"></i><span>{ee(nm)}<br><code>{hx}</code><br><small>{ee(pt.split(" · ")[0])}</small>{sub}</span>'
        return f'<a class="sw swl" href="{ee(ev[1])}" target="_blank" rel="noopener">{inner}</a>' if ev else f'<div class="sw">{inner}</div>'
    combo = date >= COMBINED_FROM
    def grp(var):
        # the swatch's variable plus every variable that inherits it (fallbacks, door-upper = ip-upper)
        def root(k):
            seen=set()
            while k in alias and k not in seen: seen.add(k); k=alias[k]
            return k
        g=[var]+[k for k in alias if root(k)==var and k!=var]
        if var=="headliner": g.append("headliner-hi")
        return " ".join(g)
    def swc2(p):
        pt,nm,hx,off=p[:4]; ev=(p[5]["src"],p[5]["url"]) if len(p)>5 and p[5] else evmap.get(nm)
        tag="（官方）" if off else "（示意色）"
        src=f'<a class="evs" href="{ee(ev[1])}" target="_blank" rel="noopener">{ee(ev[0])}{tag} ↗</a>' if ev else '<small class="evs">示意色</small>'
        return (f'<div class="sw swh"><button type="button" class="swb" data-hl="{grp(p[4])}" aria-pressed="false" aria-label="在插圖中標示：{ee(nm)}（{ee(pt.split(" · ")[0])}）">'
                f'<i style="background:{hx}"></i><span>{ee(nm)}<br><code>{hx}</code><br><small>{ee(pt.split(" · ")[0])}</small></span></button>{src}</div>')
    if combo:
        pal="".join(swc2(p) for p in b["parts"])
        mt="".join(f'<li><button type="button" class="ipb" data-hl="{grp(p[4])}" aria-pressed="false"><b>{ee(p[0])}</b>：{ee(p[1])} <code>{p[2]}</code></button></li>' for p in b["parts"])
    else:
        pal="".join(swc(p) for p in b["parts"])
        mt="".join(f'<li><b>{ee(p[0])}</b>：{ee(p[1])} <code>{p[2]}</code></li>' for p in b["parts"])
    offi="、".join(x[1] for x in b["parts"] if x[3]) or "無"
    kw="".join(f'<span>{ee(k)}</span>' for k in b["mood"])
    return (f'<div class="cmod ipalette" id="palette"><div class="kicker">Daily Interior Palette</div><h3>內裝配色 · {ee(b["theme"])} <small>{ee(b["zh"])}｜{ee(b["intro"])}</small></h3>'
      f'{svg}<p class="note">插圖為程式繪製示意，不代表任何真實車款。</p>'
      f'<div class="irow"><div><h4>色票 Swatches · 來源</h4><div class="ipal">{pal}</div></div><div><h4>情緒 Mood</h4><div class="chips">{kw}</div><p style="margin:10px 0 0;line-height:1.7">{ee(b["mood_text"])}</p></div>'
      f'<div><h4>部位與材質 IP &amp; Door Trim</h4><ul class="iparts">{mt}</ul></div></div>'
      + (f'<p class="note inote">點色票或部位可在插圖中標示對應位置（再點一次或點空白處取消）；色票下方小字為流行色來源（點連結可開來源）。官方色值：{ee(offi)}；其餘為示意色，請以實體色卡為準。</p>'
         + IP_HL_JS if combo else
         f'<p class="note inote">色票下方小字為流行色來源（點色票可開來源）。官方色值：{ee(offi)}；其餘為示意色，請以實體色卡為準。</p>') + '</div>')

def hmi_cards(items, img):
    """介面與 HMI cards (0–2), rendered as ordinary cards inside the 色彩與材質 card grid.
    item: {id, kind: case|inspiration, brand, tag, title, date, points[], image{file,alt,credit,credit_url}, sources[[name,url]]}"""
    e = html.escape; out = []
    for x in [x for x in (items or []) if x][:2]:
        im = x["image"]; insp = x.get("kind") == "inspiration"
        lab = "靈感參考" if insp else "介面與 HMI"
        pts = "".join(f'<li>{e(p)}</li>' for p in x["points"])
        src = "".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(n)} ↗</a>' for n, u in x["sources"])
        out.append(f'<article class="cmf-card hmi-card{" insp" if insp else ""}" id="{e(x["id"])}"><figure class="news-img"><div class="ratio"><img src="{img}{e(im["file"])}" alt="{e(im["alt"])}" loading="lazy" decoding="async"></div>'
                   f'<figcaption>圖片來源：<a href="{e(im["credit_url"])}" target="_blank" rel="noopener">{e(im["credit"])}</a></figcaption></figure>'
                   f'<div class="cbody"><span class="tag">{lab} · {e(x["brand"])} · {e(x["tag"])}</span><span class="date">{e(x["date"])}</span><h3>{e(x["title"])}</h3><ul class="cpts">{pts}</ul><div class="src">來源：{src}</div></div></article>')
    return out

def make_thumb(src, dst, w=480, h=270):
    """Cached 16:9 JPG thumbnail for archive rows. Returns True if dst exists after the call."""
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src): return True
    try:
        from PIL import Image
        im = Image.open(src).convert("RGB"); r = w / h
        iw, ih = im.size
        if iw / ih > r: nw = int(ih * r); im = im.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
        else: nh = int(iw / r); im = im.crop((0, (ih - nh) // 2, iw, (ih - nh) // 2 + nh))
        im.resize((w, h), Image.LANCZOS).save(dst, "JPEG", quality=80, optimize=True, progressive=True); return True
    except Exception as ex:
        print("thumb skipped:", src, ex); return False

def archive_rows(rows, full):
    """rows: [(href, thumb_href|None, no, date, weekday, headline)] newest first. full=True → archive page list with thumbs."""
    e = html.escape
    if not full:
        return "".join(f'<li><a href="{h}">No.{no:03d} · {dt}</a> — {e(hl)}</li>' for h, _, no, dt, wd, hl in rows)
    out = []; idx = {}; years = set(); months = set()
    for r in rows:
        h, th, no, dt, wd, hl = r[:6]; kw = r[6] if len(r) > 6 else ""
        idx[dt] = (hl + " " + kw).lower(); years.add(dt[:4]); months.add(dt[5:7])
        im = f'<img src="{th}" alt="" loading="lazy" decoding="async" width="480" height="270">' if th else ''
        out.append(f'<li data-date="{dt}"><a class="arow" href="{h}"><span class="athumb">{im}</span><span class="atext"><span class="ameta">No.{no:03d} · {dt} {e(wd)}</span><span class="ahl">{e(hl)}</span></span></a></li>')
    yo = "".join(f'<option value="{y}">{y} 年</option>' for y in sorted(years, reverse=True))
    mo = "".join(f'<option value="{m}">{int(m)} 月</option>' for m in sorted(months))
    js = json.dumps(idx, ensure_ascii=False).replace("</", "<\\/")
    return (f'<div class="afilter"><select id="af-y" aria-label="年份"><option value="">全部年份</option>{yo}</select>'
            f'<select id="af-m" aria-label="月份"><option value="">全部月份</option>{mo}</select>'
            f'<input id="af-q" type="search" placeholder="搜尋標題、品牌、新聞…" aria-label="關鍵字搜尋"><span id="af-n" class="af-n"></span></div>'
            f'<ol class="alist">{"".join(out)}</ol><p class="aempty" id="af-empty" hidden>沒有符合條件的期數。</p>'
            f'<script type="application/json" id="af-idx">{js}</script>'
            '<script>(()=>{const I=JSON.parse(document.getElementById("af-idx").textContent),y=document.getElementById("af-y"),m=document.getElementById("af-m"),q=document.getElementById("af-q"),n=document.getElementById("af-n"),E=document.getElementById("af-empty"),L=[...document.querySelectorAll(".alist li")];'
            'const f=()=>{const t=q.value.trim().toLowerCase().split(/\\s+/).filter(Boolean);let c=0;L.forEach(li=>{const d=li.dataset.date,ok=(!y.value||d.slice(0,4)==y.value)&&(!m.value||d.slice(5,7)==m.value)&&t.every(w=>(I[d]||"").includes(w));li.hidden=!ok;c+=ok});E.hidden=c>0;n.textContent=(y.value||m.value||t.length)?`${c} 期`:"";};'
            '[y,m].forEach(x=>x.addEventListener("change",f));q.addEventListener("input",f);f();})()</script>')

def cover_src(d, base_dir):
    """Lead image of a car issue: breaking image, else first design-news image."""
    for im in [(d.get("breaking") or {}).get("image")] + [n.get("image") for n in d.get("design_news", [])]:
        if im and im.get("file") and os.path.exists(f"{base_dir}/img/{im['file']}"): return f"{base_dir}/img/{im['file']}"
    return None

def thumb_for(d, base_dir):
    src = cover_src(d, base_dir) if not isinstance(d, str) else d
    if not src: return None
    return "thumb.jpg" if make_thumb(src, f"{base_dir}/thumb.jpg") else None

WAKE_MARK = 'assets/wakelock.js'
WRITTEN = []   # every page written by write_page in this run

GAL_MAX = 5
def gallery(item, img, eager=False, pre="", cls="news-img"):
    """Card figure. item["image"] = first image; optional item["more_images"] = extra verified article-body
    images (same keys). Up to GAL_MAX total -> swipe/arrow carousel; one image -> plain figure (no arrows)."""
    im = item.get("image") if item else None
    if not im: return ""
    ims = ([im] + list(item.get("more_images") or []))[:GAL_MAX]
    cap = lambda x: f'圖片來源：<a href="{e(x["credit_url"])}" target="_blank" rel="noopener">{e(x["credit"])}</a>'
    tag = lambda x, k: f'<img src="{img}{e(x["file"])}" alt="{e(x["alt"])}" loading="{"eager" if (eager and k == 0) else "lazy"}" decoding="async" width="1600" height="900">'
    if len(ims) == 1:
        return f'<figure class="{cls}"><div class="ratio">{tag(im, 0)}</div><figcaption>{pre}{cap(im)}</figcaption></figure>'
    slides = "".join(f'<div class="gs" data-cap="{e(cap(x))}">{tag(x, k)}</div>' for k, x in enumerate(ims))
    dots = "".join(f'<i{" class=on" if k == 0 else ""}></i>' for k in range(len(ims)))
    return (f'<figure class="{cls} gal"><div class="ratio"><div class="gtrack">{slides}</div>'
            f'<button class="gbtn gp" type="button" aria-label="上一張">‹</button><button class="gbtn gn" type="button" aria-label="下一張">›</button>'
            f'<span class="gcount">1/{len(ims)}</span><span class="gdots">{dots}</span></div><figcaption>{pre}<span class="gcap">{cap(ims[0])}</span></figcaption></figure>')

GAL_JS = ("<script>(()=>{const go=(t,d)=>{const s=t.children,w=s[0].getBoundingClientRect().width||t.clientWidth,k=Math.max(0,Math.min(s.length-1,Math.round(t.scrollLeft/w)+d));t.scrollTo({left:s[k].offsetLeft-s[0].offsetLeft,behavior:'smooth'})};"
 "document.addEventListener('click',ev=>{const b=ev.target.closest('.gbtn');if(!b)return;const t=b.parentNode.querySelector('.gtrack');go(t,b.classList.contains('gn')?1:-1)});"
 "const up=t=>{const f=t.closest('.gal'),s=[...t.children],k=Math.round(t.scrollLeft/Math.max(1,s[0].getBoundingClientRect().width));"
 "f.querySelector('.gcount').textContent=(k+1)+'/'+s.length;f.querySelectorAll('.gdots i').forEach((d,j)=>d.classList.toggle('on',j===k));"
 "const c=f.querySelector('.gcap');if(c&&s[k])c.innerHTML=s[k].dataset.cap};"
 "document.querySelectorAll('.gtrack').forEach(t=>{let r;t.addEventListener('scroll',()=>{cancelAnimationFrame(r);r=requestAnimationFrame(()=>up(t))},{passive:true})})})()</script>")

VCAR_JS = ("<script>(()=>{const w=document.querySelector('.vcar');if(!w)return;const L=JSON.parse(w.dataset.v),fr=w.querySelector('iframe'),cnt=w.querySelector('.gcount'),cap=w.querySelector('.vcap');"
 "let i=0,p=null,ready=false,started=false;"
 "const show=(k,play)=>{i=(k+L.length)%L.length;cnt.textContent=(i+1)+'/'+L.length;cap.innerHTML=L[i].cap;w.dataset.i=i;"
 "if(ready){play?p.loadVideoById(L[i].id):p.cueVideoById(L[i].id)}else{fr.src='https://www.youtube-nocookie.com/embed/'+L[i].id+'?enablejsapi=1&playsinline=1&rel=0'+(play?'&autoplay=1':'')}};"
 "w.querySelector('.gp').addEventListener('click',()=>show(i-1,started));w.querySelector('.gn').addEventListener('click',()=>show(i+1,started));"
 "window.__vcar={show,get i(){return i},get ready(){return ready},get p(){return p}};"
 "const prev=window.onYouTubeIframeAPIReady;window.onYouTubeIframeAPIReady=()=>{prev&&prev();p=new YT.Player(fr,{events:{onReady:()=>{ready=true},onStateChange:ev=>{"
 "if(ev.data===YT.PlayerState.PLAYING)started=true;if(ev.data===YT.PlayerState.ENDED){if(i<L.length-1)show(i+1,true);else show(0,false)}}}})};"
 "const s=document.createElement('script');s.src='https://www.youtube.com/iframe_api';s.async=true;document.head.appendChild(s)})()</script>")

FOCUS_FROM = "2026-10-25"   # framing applies from this issue on (zley: no backfill)
FOCUS = {}   # abs img path -> manual "X% Y%" from data.json image.focus / more_images[].focus
def collect_focus(d, base_dir):
    def walk(o):
        if isinstance(o, dict):
            if o.get("file") and o.get("focus"): FOCUS[os.path.abspath(f"{base_dir}/img/{o['file']}")] = o["focus"]
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(d)

_FOC_RE = re.compile(r'(class="(?:ratio|gs)"[^>]*>)<img src="([^"]+)"(?![^>]*object-position)')
def apply_focus(html_text, path):
    """Centre the car in every 16:9 card/carousel frame: manual focus, else auto-detected (tools/focus.py)."""
    import focus as _f
    d0 = os.path.dirname(os.path.abspath(path))
    def sub(m):
        src = html.unescape(m.group(2))
        if "://" in src: return m.group(0)
        ap = os.path.abspath(os.path.join(d0, src))
        mm = re.search(r"issues/(\d{4}-\d{2}-\d{2})/img/", ap)
        if not mm or mm.group(1) < FOCUS_FROM: return m.group(0)   # old issues left as published
        pos = FOCUS.get(ap) or _f.focus_for(ap)
        return m.group(0) + (f' style="object-position:{pos}"' if pos and pos != "50% 50%" else "")
    return _FOC_RE.sub(sub, html_text)

def write_page(path, html_text):
    """Shared writer for EVERY generated page (car + ai). Injects the wake-lock <script> into <head>
    with the right relative path, so redesigns of headers/footers can never drop it. DO NOT bypass."""
    rel = os.path.relpath(os.path.dirname(os.path.abspath(path)), ROOT)
    depth = 0 if rel == "." else rel.count(os.sep) + 1
    tag = f'<script src="{"../" * depth}{WAKE_MARK}" defer></script>'
    if WAKE_MARK not in html_text:
        assert "</head>" in html_text, f"no </head> in {path}"
        html_text = html_text.replace("</head>", tag + "</head>", 1)
    if 'class="gtrack"' in html_text and "</body>" in html_text:
        html_text = html_text.replace("</body>", GAL_JS + "</body>", 1)
    html_text = apply_focus(html_text, path)
    from navfix import fix as _navfix   # 小工具 dropdown; drops old jump/tswitch pill rows
    html_text = _navfix(html_text, path)
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

CF_BEACON = '<!-- Cloudflare Web Analytics --><script type=\'module\' src=\'https://static.cloudflareinsights.com/beacon.min.js\' data-cf-beacon=\'{"token": "7dab43c8e146429d9735e6e3996de4c5"}\'></script><!-- End Cloudflare Web Analytics -->'

def theme_toggle(mode):
    key = "cdd-theme-ai" if mode == "ai" else "cdd-theme"
    return SWITCH_JS + ("<script>document.getElementById('tg').onclick=function(){var r=document.documentElement,c=r.getAttribute('data-theme');"
            "var dark=c?c==='dark':matchMedia('(prefers-color-scheme: dark)').matches;var n=dark?'light':'dark';"
            f"r.setAttribute('data-theme',n);localStorage.setItem('{key}',n);}};</script>") + CF_BEACON

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
    deco = taipei_today() if is_root else date; SFX = sec_suffix(deco)
    desc = d["lede"]
    lead = d["design_news"][0].get("image")
    ogimg = (f"{SITE}/issues/{date}/img/{lead['file']}" if lead else (f"{SITE}/issues/{date}/img/{d['moodboards'][0]['images'][0][0]}.webp" if d.get('moodboards') else "")) if SITE else ""
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
{topbar(base, "car", base, f'<nav class="nav">{'<a href="#breaking">特報</a>' if d.get("breaking") else ''}<a href="#design">設計新聞</a>{'<a href="#cmf">色彩材質</a>' if d.get("cmf") else ''}<a href="#knowledge">汽車新知</a>{'' if d.get("color_data") else '<a href="#mood">情緒板</a>'}<a href="{base}tool/">小工具</a><a href="{base}archive/">往期</a></nav>')}
<main class="wrap">
<div class="mast"><div class="kicker">Issue No. {d['issue_no']:03d} · Global Car Design Digest</div>
{masthead_title(deco, base)}
<div class="meta"><span><b>{y} 年 {int(m)} 月 {int(dd)} 日</b> {d['weekday']}</span><span>設計新聞 {len(d['design_news'])} 則</span>{f"<span>色彩與材質 {len(d['cmf'])} 則</span>" if d.get('cmf') else ''}{f"<span>介面設計 {len(d['hmi'])} 則</span>" if d.get('hmi') else ''}<span>汽車新知 {len(d['knowledge'])} 則</span>{'' if d.get('color_data') else f"<span>情緒板 {len(d['moodboards'])} 組</span>"}{f'<span class="parts-added"><a href="{base}tool/parts/" style="color:inherit">零件圖庫新增 {d["parts_added"]} 台</a></span>' if d.get('parts_added') else ''}</div>
<p class="lede">{e(d['lede'])}</p></div>''')
    links = [("design","設計新聞",True),("cmf","色彩與材質",bool(d.get("cmf"))),("knowledge","汽車新知",True),("mood","情緒板",not d.get("color_data"))]
    H.append('<nav class="jump" aria-label="本期段落">' + "".join(f'<a href="#{a}">{t}</a>' for a, t, ok in links if ok) + f'<a class="jtool" href="{base}tool/">小工具 ↗</a>' + '</nav><script>(()=>{const f=()=>{const t=document.querySelector(".topbar");if(t)document.documentElement.style.setProperty("--tbh",t.offsetHeight+"px")};f();addEventListener("resize",f)})()</script>')
    # breaking news (optional; issues without "breaking" render exactly as before)
    bk = d.get("breaking")
    if bk:
        cards = []
        for bk in [bk] + list(d.get("breaking_more") or []):  # optional extra cards (same fields) in the same section
            im = bk.get("image"); v = bk.get("video") or {}
            fig = (f'<figure class="news-img"><div class="ratio"><img src="{img}{e(im["file"])}" alt="{e(im["alt"])}" loading="eager" decoding="async" width="1600" height="900"></div>'
                   f'<figcaption>圖片來源：<a href="{e(im["credit_url"])}" target="_blank" rel="noopener">{e(im["credit"])}</a></figcaption></figure>') if im else ""
            if im and bk.get("more_images"):
                fig = gallery(bk, img, eager=not v, cls="news-img bk-inline" if v else "news-img")   # photos carousel (kept under the video when more_images is given)
            vlink = f'<p class="bk-vlink">▶ <a href="{e(v["url"])}" target="_blank" rel="noopener">{e(v.get("title","觀看影片"))} ↗</a>{f' · <a href="{e(v["x_url"])}" target="_blank" rel="noopener">{e(v.get("x_title","X 影片"))} ↗</a>' if v.get("x_url") else ""}</p>' if v.get("url") else ""
            if v.get("type") == "youtube_list":   # official per-car videos: arrows + 1/N, auto-advance on ENDED (YouTube IFrame API)
                its = v["items"]; f0 = its[0]
                vcap = lambda x: f'<a href="{e(x["url"])}" target="_blank" rel="noopener">{e(x["car"])}｜{e(x["title"])} ↗</a>'
                data = e(json.dumps([{"id": x["id"], "cap": vcap(x)} for x in its], ensure_ascii=False))
                live = f' <span class="vlive">· <a href="{e(v["live_url"])}" target="_blank" rel="noopener">{e(v.get("live_title","完整直播"))} ↗</a></span>' if v.get("live_url") else ""
                vid = (f'<div class="bk-video vcar" data-v="{data}"><div class="ratio"><iframe id="vcar-yt" src="https://www.youtube-nocookie.com/embed/{e(f0["id"])}?enablejsapi=1&amp;playsinline=1&amp;rel=0" title="{e(f0["car"])}｜{e(f0["title"])}" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
                       f'<button class="gbtn gp vbtn" type="button" aria-label="上一段影片">‹</button><button class="gbtn gn vbtn" type="button" aria-label="下一段影片">›</button><span class="gcount">1/{len(its)}</span></div>'
                       f'<p class="bk-vlink">▶ <span class="vcap">{vcap(f0)}</span>{live}</p></div>' + VCAR_JS)
            elif v.get("type") == "youtube":
                vid = f'<div class="bk-video"><div class="ratio"><iframe src="https://www.youtube-nocookie.com/embed/{e(v["id"])}{f"?start={int(v['start'])}" if v.get("start") else ""}" title="{e(v.get("title",""))}" allow="accelerometer; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>{vlink}</div>'
            elif v.get("mp4"):
                poster = f' poster="{img}{e(im["file"])}"' if im else ""
                vid = f'<div class="bk-video"><div class="ratio"><video controls playsinline preload="metadata"{poster} title="{e(v.get("title",""))}"><source src="{e(v["mp4"])}" type="video/mp4"></video></div>{vlink}</div>'
            elif v.get("url"):
                vid = (f'<div class="bk-video"><blockquote class="twitter-tweet" data-theme="dark" data-dnt="true" data-conversation="none"><a href="{e(v["url"])}">{e(v.get("title",""))}</a></blockquote>{vlink}</div>'
                       '<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>')
            else:
                vid = ""
            if vid and not bk.get("more_images"):
                fig = ""  # video takes the hero position; no duplicate still image
            pts = "".join(f'<li>{e(x)}</li>' for x in bk["points"])
            src = "".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(n)} ↗</a>' for n, u in bk["sources"])
            cards.append(f'<article class="story bk-card">{vid}{fig}<div class="shead"><span class="tag">{e(bk["brand"])}</span><span class="date">{e(bk["date"])}</span><h3>{e(bk["title"])}</h3><ul class="cpts">{pts}</ul></div><div class="src">來源：{src}</div></article>')
        bk0 = d["breaking"]
        if bk0.get("cars"):  # multi-car launch: hero video card + regular design-news style cards (3-col grid)
            cc = []
            for j, s in enumerate(bk0["cars"]):
                an = "".join(f'<li><b>{e(k)}</b><span>{e(v)}</span></li>' for k, v in s["analysis"])
                csrc = "".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(n)} ↗</a>' for n, u in s["sources"])
                cfig = gallery(s, img, eager=False)
                cc.append(f'<article class="story" id="{e(s["id"])}">{cfig}<div class="shead"><span class="tag">{e(s["brand"])} · {e(s["tag"])}</span><span class="date">{e(s["date"])}</span><h3>{e(s["title"])}</h3><p class="orig">{e(s["orig"])}</p><p class="sum">{e(s["summary"])}</p></div><p class="alabel">設計解析 Design Notes</p><ul class="analysis">{an}</ul><div class="src">來源：{csrc}</div></article>')
            cards = [cards[0], f'<div class="news bk-cars">{"".join(cc)}</div>']
        H.append(f'<section id="breaking" class="breaking"><div class="bk-label">{e(bk0.get("label","新車特報"))} · Breaking{SFX}</div>{"".join(cards)}</section>')
    # design news
    # 今日 3 重點 + jump nav
    H.append(f'<section id="design"><div class="sec-head"><span class="num">01</span><h2>設計新聞{SFX}</h2><span class="en">Design News</span></div><div class="news">')
    for i, s in enumerate(d["design_news"]):
        an = "".join(f'<li><b>{e(k)}</b><span>{e(v)}</span></li>' for k, v in s["analysis"])
        src = "".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(n)} ↗</a>' for n, u in s["sources"])
        im = s.get("image")
        fig = gallery(s, img, eager=(i == 0))
        head = f'<div class="shead"><span class="tag">{e(s["brand"])} · {e(s["tag"])}</span><span class="date">{e(s["date"])}</span><h3>{e(s["title"])}</h3><p class="orig">{e(s["orig"])}</p><p class="sum">{e(s["summary"])}</p>'
        if i == 0:
            H.append(f'<article class="story feature" id="{s["id"]}">{fig}{head}<div class="src">來源：{src}</div></div><div class="fan"><p class="alabel">設計解析 Design Notes</p><ul class="analysis">{an}</ul></div></article>')
        else:
            H.append(f'<article class="story" id="{s["id"]}">{fig}{head}</div><p class="alabel">設計解析 Design Notes</p><ul class="analysis">{an}</ul><div class="src">來源：{src}</div></article>')
    H.append('</div></section>')
    # colour & material (optional; issues without "cmf" render exactly as before)
    cmf = d.get("cmf") or []
    n_k, n_m = ("03", "04") if cmf else ("02", "03")  # new issues have no 04 (mood merged into cmf)
    def cdata_block(cd, H):
            # cd = color_data.release: only on days a new annual colour / colour report is published
            L=lambda n,u:f'<a href="{e(u)}" target="_blank" rel="noopener">{e(n)} ↗</a>'
            hs="".join(f'<a class="hue" href="{e(u)}" target="_blank" rel="noopener"><i style="background:{hx}"></i><b>{e(nm)}</b><span>{e(org)}</span><code>{e(code)}</code><small>{hx}{"（官方）" if off else "（示意色）"}</small></a>' for org,nm,code,hx,off,u in cd.get("hues",[]))
            cards=[]
            if cd.get("pop"):
                p=cd["pop"]; bars="".join(f'<div class="bar"><span>{e(n)}</span><div><i style="width:{v/max(x[2] for x in p["rows"])*100:.0f}%;background:{c}"></i></div><b>{v}%</b></div>' for n,c,v in p["rows"])
                cards.append(f'<div class="ccard"><h4>{e(p["title"])}</h4>{bars}'+(f'<p class="note">{e(p["note"])}</p>' if p.get("note") else "")+f'<div class="src">來源：{L(*p["src"])}</div></div>')
            if cd.get("dirs"):
                dr="".join(f'<li>{e(x)}</li>' for x in cd["dirs"]["items"]); cards.append(f'<div class="ccard"><h4>{e(cd["dirs"]["title"])}</h4><ul>{dr}</ul><div class="src">來源：{L(*cd["dirs"]["src"])}</div></div>')
            if cd.get("mat"):
                mt="".join(f'<li><b>{e(a)}</b>：{L(b,u)}</li>' for a,b,u in cd["mat"]["items"]); cards.append(f'<div class="ccard"><h4>{e(cd["mat"]["title"])}</h4><ul>{mt}</ul></div>')
            pts="".join(f'<li>{e(x)}</li>' for x in cd.get("points",[]))
            src="".join(L(n,u) for n,u in cd.get("sources",[]))
            H.append(f'<div class="cdata"><div class="kicker">{"Data-backed Colour Board" if cd.get("title","")=="年度色彩與數據" else "New Colour Release · "+e(cd.get("date",""))}</div><h3>{e(cd.get("title","年度色彩與數據"))}</h3>'
                     +(f'<ul class="cpts">{pts}</ul>' if pts else "")+(f'<div class="hues">{hs}</div><p class="note">只有標「官方」的色值是官方公布；其餘官方沒公布 HEX，色塊為示意，請以實體色卡為準。</p>' if hs else "")
                     +(f'<div class="cgrid">{"".join(cards)}</div>' if cards else "")+(f'<div class="src">來源：{src}</div>' if src else "")+'</div>')
    if cmf:
        H.append(f'<section id="cmf"><div class="sec-head"><span class="num">02</span><h2>色彩與材質{SFX}</h2><span class="en">Colour &amp; Material</span></div>')
        if (d.get("color_data") or {}).get("release"): cdata_block(d["color_data"]["release"], H)
        modular = any(x.get("kind") for x in cmf)
        def cmf_card(c, span):
            im = c.get("image"); sw0 = c.get("swatch")
            # material photo first; swatch (if any) becomes a small chip in the caption
            swc = (f'<span class="swchip" title="{e(sw0["label"])}"><i style="background:{e(sw0["hex"])}"></i><code>{e(sw0["hex"])}</code></span>') if (im and sw0) else ""
            fig = gallery(c, img, pre=swc)
            sw = c.get("swatch")
            if sw and not im: fig = f'<figure class="news-img"><div class="ratio" style="background:{e(sw["hex"])}"></div><figcaption>{e(sw["label"])} <code>{e(sw["hex"])}</code></figcaption></figure>'
            pts = "".join(f'<li>{e(x)}</li>' for x in c["points"]) + (f'<li class="fb">⚠ {e(c["note"])}</li>' if c.get("note") else "")
            src = "".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(n)} ↗</a>' for n, u in c["sources"])
            cls = f" s{span}" if span else ""
            return f'<article class="cmf-card{cls}" id="{e(c["id"])}">{fig}<div class="cbody"><span class="tag">{ {"car":"車型","trend":"趨勢","paint":"塗料","material":"材質"}.get(c.get("kind","car"),"")} · {e(c["car"])} · {e(c["tag"])}</span><h3>{e(c["title"])}</h3><ul class="cpts">{pts}</ul><div class="src">來源：{src}</div></div></article>'
        if not modular:
            H.append('<div class="cmf">' + "".join(cmf_card(c, 0) for c in cmf) + '</div>')
        else:
            cars = [c for c in cmf if c.get("kind") == "car"]; rest = [c for c in cmf if c.get("kind") != "car"]
            hm = hmi_cards(d.get("hmi"), img)
            sp = lambda n: {1: 6, 2: 3}.get(n, 2)  # one row per category: 1 full / 2 halves / 3 thirds
            cells = [cmf_card(c, sp(len(cars))) for c in cars]
            cells += [cmf_card(c, sp(len(rest))) for c in rest]
            cells += [h.replace('<article class="cmf-card hmi-card', f'<article class="cmf-card s{sp(len(hm))} hmi-card', 1) for h in hm]
            H.append('<div class="cmod"><div class="kicker">Colour · Material · Interface</div><h3>色彩・材質・介面動態</h3>'
                     f'<div class="cmf cmfx">{"".join(cells)}</div></div>')
        if d.get("color_data") and date < TOOL_FROM: H.append(interior_html(d["color_data"].get("interior"), date))
        H.append('</section>')
    # knowledge
    H.append(f'<section id="knowledge"><div class="sec-head"><span class="num">{n_k}</span><h2>汽車新知{SFX}</h2><span class="en">Industry &amp; Tech</span></div><div class="kgrid">')
    for k in d["knowledge"]:
        src = "".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(n)} ↗</a>' for n, u in k["sources"])
        H.append(f'<article class="k"><span class="tag">{e(k["tag"])}</span><span class="date" style="font-size:12px;color:var(--muted);margin-left:8px">{e(k["date"])}</span><h3>{e(k["title"])}</h3><p>{e(k["summary"])}</p><div class="src">{src}</div></article>')
    t = d["term"]
    H.append(f'</div><div class="term"><div><div class="lab">今日設計名詞 · Term of the Day</div><h3>{e(t["name"])}</h3><div class="zh">{e(t["zh"])}</div>{term_diagram(d, all_issues)}</div>{term_text(t)}</div></section>')
    # mood boards (legacy issues only; issues with color_data merge colour data into 色彩與材質)
    cd = d.get("color_data")
    if not cd:
      H.append(f'<section id="mood"><div class="sec-head"><span class="num">{n_m}</span><h2>情緒板{SFX}</h2><span class="en">Mood Boards</span></div>')
    if not cd:
        H.append('<p class="note">情緒板裡的車輛都是原創虛構的概念設計，不代表任何真實車款或品牌。圖像為程式生成的插畫和材質紋理，主題每期隨機抽選。</p>')
        for b in d["moodboards"]:
            figs = "".join(f'<figure class="tile{" hero" if h else ""}"><img src="{img}{n}.webp" alt="{e(c)}" loading="lazy" decoding="async"><figcaption>{e(c)}</figcaption></figure>' for n, c, h in b["images"])
            pal = "".join(f'<div class="sw"><i style="background:{hx}"></i><span>{e(nm)}<br><code>{hx}</code></span></div>' for nm, hx in b["palette"])
            kw = "".join(f'<span>{e(k)}</span>' for k in b["keywords"])
            mt = "".join(f'<li>{e(x)}</li>' for x in b["materials"])
            H.append(f'<div class="board"><div class="board-head"><div><div class="kicker">Random Theme</div><h3>{e(b["theme"])}</h3><div class="zh">{e(b["zh"])}</div></div><p>{e(b["intro"])}</p></div><div class="mgrid">{figs}</div><div class="bwrap"><div class="palette">{pal}</div><div class="bmeta"><div><h4>關鍵字 Keywords</h4><div class="chips">{kw}</div></div><div><h4>材質筆記 Material Notes</h4><ul>{mt}</ul></div></div></div></div>')
    if not cd: H.append('</section>')
    # archive
    prev = [x for x in all_issues if x["date"] < date][:7]
    li = archive_rows([(f'{base}issues/{x["date"]}/', None, x["issue_no"], x["date"], x["weekday"], x["design_news"][0]["title"]) for x in prev], False)
    if prev: H.append(f'<section class="archive" id="archive"><div class="sec-head"><span class="num">∞</span><h2>往期</h2><span class="en">Archive</span><a class="amore" href="{base}archive/">全部往期 →</a></div><ul>{li}</ul></section>')
    H.append(f'''</main><footer><div class="wrap">Car Design Daily · 每日整理全球汽車設計新聞、產業新知與隨機情緒板。內容摘要與分析為編輯整理，事實以原始來源為準；新聞圖片取自車廠官方新聞室／原報導，版權屬原權利人，均標示來源並連結原頁。<br>Issue {d["issue_no"]:03d} · {date}</div></footer>
{theme_toggle("car")}
</body></html>''')
    return "\n".join(H)

def archive_page(all_issues):
    rows = []
    for x in all_issues:
        th = thumb_for(x, f"{ROOT}/issues/{x['date']}")
        kw = " ".join([n.get("brand","") + " " + n.get("title","") for n in x.get("design_news", [])] + [c.get("car","") + " " + c.get("title","") for c in x.get("cmf") or []] + [h.get("brand","") + " " + h.get("title","") for h in x.get("hmi") or []] + [k.get("title","") for k in x.get("knowledge", [])] + [(x.get("breaking") or {}).get("title","")] + [m.get("title","") for m in x.get("breaking_more") or []])
        rows.append((f'../issues/{x["date"]}/', f'../issues/{x["date"]}/{th}' if th else None, x["issue_no"], x["date"], x["weekday"], x["design_news"][0]["title"], kw))
    li = archive_rows(rows, True)
    return f'''<!doctype html><html lang="zh-Hant-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>往期 · Car Design Daily</title><link rel="stylesheet" href="../assets/style.css">
{theme_init("car")}</head>
<body class="mode-car">{topbar("../", "car", "../")}
<main class="wrap"><section class="archive full"><div class="sec-head"><span class="num">∞</span><h2>往期</h2><span class="en">Archive</span></div>{li}</section></main>{theme_toggle("car")}</body></html>'''

if __name__ == "__main__":
    al = issues()
    for d in al: collect_focus(d, f"{ROOT}/issues/{d['date']}")
    for d in al:
        write_page(f"{ROOT}/issues/{d['date']}/index.html", page(d, "../../", al, False))
    write_page(f"{ROOT}/index.html", page(al[0], "./", al, True))
    os.makedirs(f"{ROOT}/archive", exist_ok=True)
    write_page(f"{ROOT}/archive/index.html", archive_page(al))
    os.makedirs(f"{ROOT}/tool", exist_ok=True)
    write_page(f"{ROOT}/tool/index.html", tool_page(al))
    import focus as _f; _f.save()
    check_wakelock()
    print("built", [d["date"] for d in al])
