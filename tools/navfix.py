"""Top-nav 小工具 dropdown (內裝配色 / 零件圖庫). Applied by build.write_page to every generated page,
and runnable standalone (python3 tools/navfix.py) to patch static pages. Idempotent.
Also removes the old duplicate pill row (nav.jump) and the per-tool pill switch (nav.tswitch)."""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = ('<script>(()=>{document.querySelectorAll(".ndrop>a").forEach(a=>a.addEventListener("click",e=>{'
      'const d=a.parentNode;if(matchMedia("(hover:none)").matches&&!d.classList.contains("open")){e.preventDefault();'
      'document.querySelectorAll(".ndrop.open").forEach(x=>x.classList.remove("open"));d.classList.add("open");a.setAttribute("aria-expanded","true")}}));'
      'document.addEventListener("click",e=>{if(!e.target.closest(".ndrop"))document.querySelectorAll(".ndrop.open").forEach(x=>{x.classList.remove("open");x.firstChild.setAttribute("aria-expanded","false")})})})()</script>')
TOOL_A = re.compile(r'<a href="([^"]*?)tool/"( aria-current="page")?>小工具</a>|<a href="\./"( aria-current="page")>小工具</a>|<a href="\.\./"( aria-current="page")?>小工具</a>')

def fix(html, path):
    rel = os.path.relpath(os.path.dirname(os.path.abspath(path)), ROOT)
    depth = 0 if rel == "." else rel.count(os.sep) + 1
    base = "../" * depth
    html = re.sub(r'<nav class="jump"[^>]*>.*?</nav>', '', html, flags=re.S)
    html = re.sub(r'<nav class="tswitch"[^>]*>.*?</nav>', '', html, flags=re.S)
    if 'class="ndrop"' not in html:
        here = rel.replace(os.sep, "/")
        cur_c = ' aria-current="page"' if here == "tool" else ''
        cur_p = ' aria-current="page"' if here == "tool/parts" else ''
        top_cur = ' aria-current="page"' if here.startswith("tool") else ''
        dd = (f'<span class="ndrop"><a href="{base}tool/"{top_cur} aria-haspopup="true" aria-expanded="false">小工具</a>'
              f'<span class="ndm" role="menu"><a href="{base}tool/" role="menuitem"{cur_c}>內裝配色</a>'
              f'<a href="{base}tool/parts/" role="menuitem"{cur_p}>零件圖庫</a></span></span>')
        html, n = TOOL_A.subn(dd, html, count=1)
        if n and "</body>" in html: html = html.replace("</body>", JS + "</body>", 1)
    return html

if __name__ == "__main__":
    for dp, dn, fn in os.walk(ROOT):
        if "/.git" in dp: continue
        for f in fn:
            if f.endswith(".html"):
                p = os.path.join(dp, f); s = open(p, encoding="utf-8").read(); t = fix(s, p)
                if t != s: open(p, "w", encoding="utf-8").write(t); print("patched", os.path.relpath(p, ROOT))
