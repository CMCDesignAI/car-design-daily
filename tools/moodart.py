#!/usr/bin/env python3
"""Procedural mood-board artwork (original, fictional, logo-free)."""
import sys, os, subprocess, math, numpy as np
from PIL import Image, ImageDraw, ImageFilter
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
TMP = "/tmp/moodart"; os.makedirs(TMP, exist_ok=True)
rng = np.random.default_rng(20261016)

def render_svg(name, svg, w, h):
    p = f"{TMP}/{name}.svg"; open(p, "w").write(svg)
    png = f"{TMP}/{name}.png"
    subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={w},{h}", f"--screenshot={png}", "file://" + p],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    im = Image.open(png).convert("RGB").crop((0, 0, w, h))
    save(name, im)

def save(name, im):
    im.thumbnail((1400, 1400))
    dst = f"{OUT}/{name}.webp"; im.save(dst, "WEBP", quality=82, method=6)
    print("ok", dst, im.size, os.path.getsize(dst))

def svg_wrap(w, h, body, defs=""):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{defs}</defs>{body}</svg>'

def wheel(cx, cy, r, rim="#5A6B78", tyre="#2A2A28"):
    s = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{tyre}"/>'
    s += f'<circle cx="{cx}" cy="{cy}" r="{r*0.62}" fill="{rim}"/>'
    s += f'<circle cx="{cx}" cy="{cy}" r="{r*0.22}" fill="#d9d9d9"/>'
    for i in range(8):
        a = math.radians(i*45)
        s += f'<line x1="{cx}" y1="{cy}" x2="{cx+r*0.55*math.cos(a)}" y2="{cy+r*0.55*math.sin(a)}" stroke="#c4a574" stroke-width="3"/>'
    return s

# ---- Theme A: Industrial workwear utility pickup ----
def a_hero():
    W, H = 1600, 900
    defs = '''<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#B8C0C8"/><stop offset="1" stop-color="#8A9298"/></linearGradient>
    <linearGradient id="cab" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#D4C4A0"/><stop offset="1" stop-color="#A89060"/></linearGradient>
    <linearGradient id="bed" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6A7A88"/><stop offset="1" stop-color="#4A5A68"/></linearGradient>
    <pattern id="conc" width="40" height="40" patternUnits="userSpaceOnUse"><rect width="40" height="40" fill="#9A9A94"/><circle cx="8" cy="12" r="1.2" fill="#888"/><circle cx="28" cy="30" r="1" fill="#7a7a74"/></pattern>'''
    b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
    # scaffolding
    for x in [80, 200, 1400, 1520]:
        b += f'<rect x="{x}" y="120" width="14" height="520" fill="#5A5A55"/>'
        b += f'<rect x="{x-40}" y="200" width="90" height="8" fill="#E8C12A"/>'
    b += f'<rect y="640" width="{W}" height="260" fill="url(#conc)"/>'
    # pickup body
    b += '<ellipse cx="800" cy="700" rx="520" ry="24" fill="#000" opacity=".18"/>'
    b += '<path d="M280,620 L280,420 L420,360 L700,360 L720,400 L720,620 Z" fill="url(#cab)"/>'
    b += '<path d="M720,400 L1280,400 L1320,440 L1320,620 L720,620 Z" fill="url(#bed)"/>'
    b += '<rect x="300" y="400" width="380" height="120" fill="#6A8FA8" opacity=".55"/>'
    b += '<rect x="280" y="500" width="40" height="120" fill="#E8C12A"/>'  # safety stripe
    b += '<rect x="1280" y="500" width="40" height="120" fill="#E8C12A"/>'
    b += wheel(420, 620, 78) + wheel(1100, 620, 78)
    b += '<rect x="760" y="430" width="400" height="14" fill="#C4A574"/>'
    render_svg("mb1-1", svg_wrap(W, H, b, defs), W, H)

def a_swatch():
    W, H = 1200, 900
    cols = [("#C4A574","Khaki"),("#E8C12A","Safety Y"),("#9A9A94","Concrete"),
            ("#5A6B78","Steel"),("#2A2A28","Rubber"),("#E8DFC8","Canvas")]
    b = f'<rect width="{W}" height="{H}" fill="#E8DFC8"/>'
    for i,(c,n) in enumerate(cols):
        x, y = 60 + (i%3)*380, 80 + (i//3)*400
        b += f'<rect x="{x}" y="{y}" width="340" height="320" rx="18" fill="{c}"/>'
        b += f'<text x="{x+170}" y="{y+290}" fill="{"#fff" if i in (1,3,4) else "#222"}" font-size="28" text-anchor="middle" font-family="sans-serif">{n}</text>'
    render_svg("mb1-2", svg_wrap(W, H, b), W, H)

def a_interior():
    W, H = 1200, 900
    defs = '''<linearGradient id="dash" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5A6B78"/><stop offset="1" stop-color="#3A4A58"/></linearGradient>'''
    b = f'<rect width="{W}" height="{H}" fill="#C4A574"/>'
    b += '<path d="M80,200 L1120,160 L1120,500 L80,540 Z" fill="url(#dash)"/>'
    b += '<rect x="200" y="240" width="280" height="140" rx="8" fill="#2A2A28"/>'
    b += '<circle cx="700" cy="320" r="50" fill="none" stroke="#E8C12A" stroke-width="8"/>'
    b += '<rect x="150" y="560" width="400" height="280" rx="20" fill="#A89060"/>'
    b += '<rect x="650" y="560" width="400" height="280" rx="20" fill="#A89060"/>'
    b += '<rect x="180" y="600" width="340" height="40" fill="#E8C12A"/>'
    render_svg("mb1-3", svg_wrap(W, H, b, defs), W, H)

def steel_tex(name, w=1000, h=750):
    arr = rng.normal(110, 18, (h, w)).astype(np.float32)
    for y in range(h):
        arr[y] += math.sin(y*0.15)*8 + (y%7)*0.4
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    im = Image.fromarray(arr, 'L').convert('RGB')
    # add yellow stripe
    d = ImageDraw.Draw(im)
    d.rectangle([0, h//2-20, w, h//2+20], fill=(232, 193, 42))
    save(name, im)

# ---- Theme B: Brutalist off-roader ----
def b_hero():
    W, H = 1600, 900
    defs = '''<linearGradient id="sky2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#D0D4D8"/><stop offset="1" stop-color="#A8B0B8"/></linearGradient>
    <linearGradient id="blk" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#B8B5AE"/><stop offset="1" stop-color="#8A8780"/></linearGradient>'''
    b = f'<rect width="{W}" height="{H}" fill="url(#sky2)"/>'
    # block buildings
    b += '<rect x="40" y="180" width="220" height="420" fill="#9A9890"/>'
    b += '<rect x="280" y="260" width="160" height="340" fill="#7A7870"/>'
    b += '<rect x="1360" y="200" width="200" height="400" fill="#A8A59E"/>'
    b += f'<rect y="680" width="{W}" height="220" fill="#5A6B4A"/>'
    # brutalist vehicle: stacked boxes
    b += '<ellipse cx="820" cy="720" rx="480" ry="22" fill="#000" opacity=".2"/>'
    b += '<rect x="420" y="480" width="820" height="220" fill="url(#blk)"/>'
    b += '<rect x="500" y="320" width="520" height="180" fill="#A8A59E"/>'
    b += '<rect x="560" y="360" width="90" height="70" fill="#3A3A38"/>'  # small window
    b += '<rect x="780" y="360" width="90" height="70" fill="#3A3A38"/>'
    b += '<rect x="1000" y="360" width="70" height="70" fill="#3A3A38"/>'
    b += '<rect x="420" y="620" width="120" height="80" fill="#8B5A3C"/>'
    b += '<rect x="1120" y="620" width="120" height="80" fill="#8B5A3C"/>'
    b += wheel(560, 700, 90, rim="#3A3A38", tyre="#1E1E1C") + wheel(1100, 700, 90, rim="#3A3A38", tyre="#1E1E1C")
    # bolt heads
    for x in range(450, 1200, 80):
        b += f'<circle cx="{x}" cy="500" r="6" fill="#5A5850"/>'
    render_svg("mb2-1", svg_wrap(W, H, b, defs), W, H)

def b_swatch():
    W, H = 1200, 900
    cols = [("#B8B5AE","Concrete"),("#8B5A3C","Rust"),("#3A3A38","Charcoal"),
            ("#5A6B4A","Moss"),("#D0D4D8","Sky Grey"),("#1E1E1C","Shadow")]
    b = f'<rect width="{W}" height="{H}" fill="#D0D4D8"/>'
    for i,(c,n) in enumerate(cols):
        x, y = 60 + (i%3)*380, 80 + (i//3)*400
        b += f'<rect x="{x}" y="{y}" width="340" height="320" rx="4" fill="{c}"/>'
        b += f'<text x="{x+170}" y="{y+290}" fill="{"#fff" if i>=2 else "#222"}" font-size="28" text-anchor="middle" font-family="sans-serif">{n}</text>'
    render_svg("mb2-2", svg_wrap(W, H, b), W, H)

def b_detail():
    W, H = 1200, 900
    b = f'<rect width="{W}" height="{H}" fill="#B8B5AE"/>'
    b += '<polygon points="100,800 400,200 700,800" fill="#9A9890"/>'
    b += '<polygon points="500,800 850,150 1150,800" fill="#8A8780"/>'
    b += '<rect x="520" y="320" width="80" height="100" fill="#1E1E1C"/>'
    b += '<rect x="700" y="400" width="60" height="80" fill="#1E1E1C"/>'
    b += '<circle cx="300" cy="500" r="18" fill="#5A5850"/>'
    b += '<circle cx="900" cy="450" r="18" fill="#5A5850"/>'
    b += '<rect x="0" y="780" width="1200" height="120" fill="#8B5A3C"/>'
    render_svg("mb2-3", svg_wrap(W, H, b), W, H)

def concrete_tex(name, w=1000, h=750):
    arr = rng.normal(170, 22, (h, w)).astype(np.float32)
    noise = rng.random((h, w))
    arr[noise < 0.02] -= 40
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    im = Image.fromarray(arr, 'L').convert('RGB')
    # rust patch
    d = ImageDraw.Draw(im)
    d.ellipse([w//3, h//3, w//3+200, h//3+120], fill=(139, 90, 60))
    im = im.filter(ImageFilter.GaussianBlur(1.2))
    save(name, im)

if __name__ == "__main__":
    a_hero(); a_swatch(); a_interior(); steel_tex("mb1-4")
    b_hero(); b_swatch(); b_detail(); concrete_tex("mb2-4")
