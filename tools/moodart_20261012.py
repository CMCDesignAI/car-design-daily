#!/usr/bin/env python3
"""Mood boards for 2026-10-12: Cyber-organic biomorphic EV / Scandinavian calm interior."""
import sys, os, subprocess, math, numpy as np
from PIL import Image, ImageFilter, ImageDraw
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
TMP = "/tmp/moodart1012"; os.makedirs(TMP, exist_ok=True)
rng = np.random.default_rng(20261012)

def render_svg(name, svg, w, h):
    p = f"{TMP}/{name}.svg"; open(p, "w").write(svg); png = f"{TMP}/{name}.png"
    subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={w},{h}", f"--screenshot={png}", "file://" + p], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
    save(name, Image.open(png).convert("RGB").crop((0, 0, w, h)))
def save(name, im):
    im.thumbnail((1400, 1400)); dst = f"{OUT}/{name}.webp"; im.save(dst, "WEBP", quality=80, method=6)
    print("ok", dst, im.size, os.path.getsize(dst))
def wrap(w, h, body, defs=""):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{defs}</defs>{body}</svg>'
def wheel(cx, cy, r, tyre, rim, accent=None):
    s = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{tyre}"/><circle cx="{cx}" cy="{cy}" r="{r*.62}" fill="{rim}"/>'
    if accent:
        for i in range(6):
            a = math.radians(i*60-90)
            s += f'<line x1="{cx}" y1="{cy}" x2="{cx+r*.48*math.cos(a):.1f}" y2="{cy+r*.48*math.sin(a):.1f}" stroke="{accent}" stroke-width="2.5"/>'
    return s + f'<circle cx="{cx}" cy="{cy}" r="{r*.12}" fill="{tyre}"/>'

# ---------- A: Cyber-organic biomorphic EV ----------
def a_hero():
    W, H = 1600, 900
    d = '''<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b1c24"/><stop offset=".55" stop-color="#16353f"/><stop offset="1" stop-color="#1fa7a0"/></linearGradient>
    <linearGradient id="body" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1fa7a0"/><stop offset=".5" stop-color="#0e6e6a"/><stop offset="1" stop-color="#2a2f33"/></linearGradient>
    <linearGradient id="water" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0e2a33"/><stop offset="1" stop-color="#061018"/></linearGradient>
    <filter id="b"><feGaussianBlur stdDeviation="10"/></filter>'''
    b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
    # dock piles
    for x in (120, 220, 1380, 1480):
        b += f'<rect x="{x}" y="480" width="18" height="200" fill="#2a2f33" opacity=".8"/>'
    b += f'<rect y="640" width="{W}" height="260" fill="url(#water)"/>'
    b += '<ellipse cx="800" cy="700" rx="560" ry="24" fill="#000" opacity=".3" filter="url(#b)"/>'
    # biomorphic body: flowing organic coupe-crossover
    body = 'M160,690 C200,560 280,500 420,470 C560,440 720,430 900,445 C1080,460 1240,500 1320,580 L1340,700 L180,700 Z'
    b += f'<path d="{body}" fill="url(#body)"/>'
    # translucent shell overlay
    b += '<path d="M320,520 C480,470 700,460 920,480 C1100,495 1220,540 1280,600 L1260,620 C1180,560 1000,510 760,500 C520,490 360,530 300,580 Z" fill="#d7e8e4" opacity=".22"/>'
    # canopy
    b += '<path d="M480,500 C600,455 780,450 960,470 L940,540 C780,520 620,525 500,555 Z" fill="#0b1c24" opacity=".85"/>'
    b += '<path d="M500,510 C620,475 780,470 940,485 L925,525 C780,510 640,515 515,540 Z" fill="#6b5b95" opacity=".35"/>'
    # pulse light veins
    for pts in [
        'M240,620 C400,580 600,560 900,570 C1100,578 1240,610 1300,650',
        'M280,650 C450,615 700,600 1000,610',
    ]:
        b += f'<path d="{pts}" fill="none" stroke="#f08a5d" stroke-width="3" opacity=".85"/>'
    # exoskeleton arches
    b += '<path d="M360,700 Q360,520 420,500" fill="none" stroke="#d7e8e4" stroke-width="6" opacity=".5"/>'
    b += '<path d="M1120,700 Q1140,530 1080,510" fill="none" stroke="#d7e8e4" stroke-width="6" opacity=".5"/>'
    b += wheel(420, 700, 64, "#0b1c24", "#2a2f33", "#1fa7a0") + wheel(1120, 700, 68, "#0b1c24", "#2a2f33", "#1fa7a0")
    # no logo — abstract glow node instead
    b += '<circle cx="260" cy="600" r="10" fill="#f08a5d" opacity=".9"/>'
    render_svg("mb1-1", wrap(W, H, b, d), W, H)

def a_cockpit():
    W, H = 1000, 750
    d = '''<linearGradient id="dash" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#16353f"/><stop offset="1" stop-color="#0b1c24"/></linearGradient>
    <linearGradient id="mem" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#1fa7a0"/><stop offset="1" stop-color="#6b5b95"/></linearGradient>'''
    b = f'<rect width="{W}" height="{H}" fill="#0b1c24"/>'
    b += '<path d="M0,60 L1000,40 L1000,260 L0,300 Z" fill="#1a3340"/>'
    b += '<path d="M0,280 L1000,250 L1000,480 L0,520 Z" fill="url(#dash)"/>'
    # organic membrane cluster
    b += '<ellipse cx="500" cy="360" rx="220" ry="70" fill="#d7e8e4" opacity=".15"/>'
    b += '<ellipse cx="500" cy="360" rx="180" ry="48" fill="none" stroke="url(#mem)" stroke-width="4"/>'
    for i in range(7):
        x = 350 + i*50
        b += f'<circle cx="{x}" cy="360" r="6" fill="#f08a5d" opacity=".8"/>'
    # translucent steering yoke
    b += '<path d="M350,560 Q500,500 650,560 Q620,640 500,660 Q380,640 350,560 Z" fill="none" stroke="#1fa7a0" stroke-width="14"/>'
    b += '<path d="M420,600 L580,600" stroke="#d7e8e4" stroke-width="6" opacity=".5"/>'
    # side organic vents
    for x in (120, 820):
        b += f'<path d="M{x},320 C{x+40},300 {x+60},400 {x+20},480" fill="none" stroke="#6b5b95" stroke-width="8" opacity=".6"/>'
    render_svg("mb1-2", wrap(W, H, b, d), W, H)

def a_detail():
    W, H = 1000, 750
    d = '''<radialGradient id="g" cx=".5" cy=".4" r=".6"><stop offset="0" stop-color="#1fa7a0"/><stop offset="1" stop-color="#0b1c24"/></radialGradient>'''
    b = f'<rect width="{W}" height="{H}" fill="url(#g)"/>'
    # shell seams
    for i in range(6):
        y = 120 + i*90
        b += f'<path d="M80,{y} C300,{y-40} 700,{y+40} 920,{y}" fill="none" stroke="#d7e8e4" stroke-width="3" opacity=".45"/>'
    # light ducts
    for i in range(5):
        x = 180 + i*140
        b += f'<rect x="{x}" y="280" width="18" height="220" rx="9" fill="#f08a5d" opacity=".55"/>'
    # honeycomb vents
    for row in range(4):
        for col in range(6):
            x = 220 + col*90 + (row%2)*45; y = 520 + row*40
            b += f'<polygon points="{x},{y-14} {x+16},{y-7} {x+16},{y+7} {x},{y+14} {x-16},{y+7} {x-16},{y-7}" fill="none" stroke="#2a2f33" stroke-width="2"/>'
    render_svg("mb1-3", wrap(W, H, b, d), W, H)

def a_material():
    W, H = 1000, 750
    arr = np.zeros((H, W, 3), dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    base = np.array([14, 40, 45], dtype=np.float32)
    arr[:] = base
    # iridescent waves
    wave = 40*np.sin(xx/40 + yy/70) + 25*np.cos(xx/25 - yy/55)
    arr[:,:,0] += 10 + 0.4*wave
    arr[:,:,1] += 50 + 0.8*wave
    arr[:,:,2] += 45 + 0.5*wave
    # wet carbon noise
    noise = rng.normal(0, 8, (H, W))
    arr[:,:,0] += noise*0.3; arr[:,:,1] += noise*0.2; arr[:,:,2] += noise*0.25
    # pulse streaks
    for _ in range(18):
        y0 = int(rng.integers(50, H-50)); x0 = int(rng.integers(0, W))
        for t in range(120):
            x = min(W-1, x0+t); y = min(H-1, max(0, y0+int(8*math.sin(t/12))))
            arr[y, x] = [240, 138, 93]
    im = Image.fromarray(np.clip(arr,0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    save("mb1-4", im)

# ---------- B: Scandinavian calm interior ----------
def b_hero():
    W, H = 1600, 900
    d = '''<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c9d6d5"/><stop offset=".5" stop-color="#f4f1ea"/><stop offset="1" stop-color="#d2b48c"/></linearGradient>
    <linearGradient id="body" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f4f1ea"/><stop offset="1" stop-color="#d8d2c6"/></linearGradient>
    <linearGradient id="road" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a8a29a"/><stop offset="1" stop-color="#6e6860"/></linearGradient>'''
    b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
    # pine trunks
    for x,hgt in [(100,420),(220,500),(1360,460),(1480,520)]:
        b += f'<rect x="{x}" y="{560-hgt}" width="28" height="{hgt}" fill="#3e4a3c" opacity=".85"/>'
        b += f'<ellipse cx="{x+14}" cy="{560-hgt}" rx="60" ry="40" fill="#3e4a3c" opacity=".5"/>'
    b += f'<rect y="620" width="{W}" height="280" fill="url(#road)"/>'
    # calm wagon silhouette
    body='M200,690 L240,560 L420,500 L980,495 L1180,520 L1240,600 L1260,690 Z'
    b += f'<path d="{body}" fill="url(#body)"/>'
    b += '<path d="M420,500 L500,430 L900,428 L980,495 Z" fill="#3e4a3c" opacity=".55"/>'  # glass
    b += '<path d="M440,495 L520,445 L880,443 L960,492" fill="none" stroke="#c9d6d5" stroke-width="3"/>'
    b += '<path d="M240,580 L1180,560" stroke="#a8a29a" stroke-width="4" fill="none"/>'  # belt
    # slim info strip hint on dash through glass
    b += '<rect x="560" y="470" width="220" height="8" rx="2" fill="#c9d6d5" opacity=".8"/>'
    b += wheel(400, 690, 58, "#2a2a2a", "#c4a484") + wheel(1080, 690, 60, "#2a2a2a", "#c4a484")
    # no logos
    render_svg("mb2-1", wrap(W, H, b, d), W, H)

def b_cockpit():
    W, H = 1000, 750
    d = '''<linearGradient id="wood" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e2c9a0"/><stop offset="1" stop-color="#d2b48c"/></linearGradient>'''
    b = f'<rect width="{W}" height="{H}" fill="#f4f1ea"/>'
    # large side light
    b += '<rect x="0" y="40" width="1000" height="220" fill="#c9d6d5" opacity=".55"/>'
    b += '<path d="M0,240 L1000,220 L1000,360 L0,390 Z" fill="url(#wood)"/>'
    # slim info ribbon instead of screen wall
    b += '<rect x="120" y="280" width="760" height="28" rx="6" fill="#3e4a3c" opacity=".75"/>'
    b += '<rect x="140" y="288" width="200" height="12" rx="3" fill="#c9d6d5"/>'
    # wool seats
    b += '<ellipse cx="320" cy="560" rx="110" ry="130" fill="#a8a29a"/>'
    b += '<ellipse cx="680" cy="560" rx="110" ry="130" fill="#a8a29a"/>'
    b += '<rect x="230" y="520" width="180" height="160" rx="20" fill="#b7b1a8"/>'
    b += '<rect x="590" y="520" width="180" height="160" rx="20" fill="#b7b1a8"/>'
    # wood wheel
    b += '<circle cx="500" cy="520" r="70" fill="none" stroke="#c4a484" stroke-width="14"/>'
    b += '<circle cx="500" cy="520" r="70" fill="none" stroke="#3e4a3c" stroke-width="3"/>'
    b += '<rect x="470" y="500" width="60" height="40" rx="4" fill="#d2b48c"/>'
    render_svg("mb2-2", wrap(W, H, b, d), W, H)

def b_detail():
    W, H = 1000, 750
    b = f'<rect width="{W}" height="{H}" fill="#f4f1ea"/>'
    # wood knobs
    for i,x in enumerate((220,500,780)):
        b += f'<circle cx="{x}" cy="280" r="70" fill="#d2b48c"/>'
        b += f'<circle cx="{x}" cy="280" r="50" fill="#e2c9a0"/>'
        b += f'<rect x="{x-6}" y="230" width="12" height="40" fill="#3e4a3c"/>'
    # woven door panel
    for row in range(10):
        for col in range(16):
            x=80+col*52; y=420+row*28
            colr = "#a8a29a" if (row+col)%2==0 else "#c4a484"
            b += f'<rect x="{x}" y="{y}" width="48" height="24" fill="{colr}" opacity=".7"/>'
    # hidden vent slits
    for x in (150,400,650,850):
        b += f'<rect x="{x}" y="360" width="80" height="6" rx="2" fill="#3e4a3c" opacity=".4"/>'
    render_svg("mb2-3", wrap(W, H, b), W, H)

def b_material():
    W, H = 1000, 750
    arr = np.zeros((H, W, 3), dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    # oak rings left half
    cx, cy = 280, 375
    dist = np.sqrt((xx-cx)**2 + (yy-cy)**2)
    rings = (np.sin(dist/12)*20 + 180).clip(0,255)
    arr[:,:,0] = rings*0.85; arr[:,:,1] = rings*0.7; arr[:,:,2] = rings*0.45
    # wool texture right half
    noise = rng.normal(0, 18, (H, W))
    wool = 168 + noise
    mask = xx > 500
    for c, base in enumerate([168,162,154]):
        arr[:,:,c] = np.where(mask, base+noise*0.6, arr[:,:,c])
    # soft vignette seam
    seam = np.exp(-((xx-500)**2)/(2*40**2))
    for c in range(3):
        arr[:,:,c] = arr[:,:,c]*(1-0.15*seam) + 244*0.15*seam
    im = Image.fromarray(np.clip(arr,0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    save("mb2-4", im)

if __name__ == "__main__":
    a_hero(); a_cockpit(); a_detail(); a_material()
    b_hero(); b_cockpit(); b_detail(); b_material()
    print("moodart 2026-10-12 done")
