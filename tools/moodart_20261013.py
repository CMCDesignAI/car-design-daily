#!/usr/bin/env python3
"""Mood boards for 2026-10-13: Neo-Tokyo night delivery van / Desert rally pastel."""
import sys, os, subprocess, math, numpy as np
from PIL import Image, ImageFilter
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
TMP = "/tmp/moodart1013"; os.makedirs(TMP, exist_ok=True)
rng = np.random.default_rng(20261013)
def save(name, im):
    im.thumbnail((1400, 1400)); dst = f"{OUT}/{name}.webp"; im.save(dst, "WEBP", quality=80, method=6); print("ok", dst, os.path.getsize(dst))
def render(name, body, w, h, defs=""):
    p = f"{TMP}/{name}.svg"; open(p, "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{defs}</defs>{body}</svg>')
    png = f"{TMP}/{name}.png"
    subprocess.run(["google-chrome","--headless=new","--no-sandbox","--disable-gpu","--hide-scrollbars",f"--window-size={w},{h}",f"--screenshot={png}","file://"+p],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60)
    save(name, Image.open(png).convert("RGB").crop((0,0,w,h)))
def wheel(cx,cy,r,t,rim): return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{t}"/><circle cx="{cx}" cy="{cy}" r="{r*.6}" fill="{rim}"/><circle cx="{cx}" cy="{cy}" r="{r*.15}" fill="{t}"/>'
def texture(name, base, waves, streak, seed):
    W,H=1000,750; yy,xx=np.mgrid[0:H,0:W]; a=np.zeros((H,W,3),np.float32); a[:]=base
    w=waves*np.sin(xx/37+yy/61)+waves*.6*np.cos(xx/19-yy/43)
    for c in range(3): a[:,:,c]+=w*(.5+.2*c)+rng.normal(0,6,(H,W))
    for _ in range(14):
        y0=int(rng.integers(40,H-40)); x0=int(rng.integers(0,W-200))
        for t in range(200): a[min(H-1,y0+int(5*math.sin(t/15))), x0+t]=streak
    save(name, Image.fromarray(np.clip(a,0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.8)))
# A: Neo-Tokyo night delivery van
def A():
    W,H=1600,900
    d='<linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d0f1f"/><stop offset="1" stop-color="#2b1b3f"/></linearGradient>'
    b=f'<rect width="{W}" height="{H}" fill="url(#s)"/>'
    for i,(x,h) in enumerate([(0,520),(180,640),(330,480),(1180,600),(1350,700),(1480,540)]):
        b+=f'<rect x="{x}" y="{H-h}" width="160" height="{h}" fill="#151a2e"/>'
        for r in range(8): b+=f'<rect x="{x+20}" y="{H-h+30+r*55}" width="120" height="10" fill="{["#ff3d7f","#29e3ff","#ffd23f"][(i+r)%3]}" opacity=".55"/>'
    b+=f'<rect y="700" width="{W}" height="200" fill="#0a0c18"/><rect y="700" width="{W}" height="200" fill="#29e3ff" opacity=".06"/>'
    b+='<path d="M430,700 L430,430 Q430,380 480,380 L1050,380 Q1120,380 1140,440 L1180,560 L1180,700 Z" fill="#e8e6df"/>'
    b+='<path d="M1050,400 L1120,450 L1150,550 L1050,550 Z" fill="#151a2e"/>'
    b+='<rect x="430" y="600" width="750" height="14" fill="#ff3d7f"/><rect x="1160" y="560" width="20" height="40" fill="#29e3ff"/>'
    b+='<rect x="520" y="430" width="420" height="140" rx="6" fill="none" stroke="#151a2e" stroke-width="4"/>'
    b+=wheel(560,700,62,"#0a0c18","#3a3f55")+wheel(1060,700,62,"#0a0c18","#3a3f55")
    render("mb1-1",b,W,H,d)
    W,H=1000,750
    b=f'<rect width="{W}" height="{H}" fill="#151a2e"/>'
    for i in range(6): b+=f'<rect x="{80+i*145}" y="120" width="120" height="420" rx="8" fill="#e8e6df" opacity=".9"/><rect x="{80+i*145}" y="320" width="120" height="8" fill="#ff3d7f"/>'
    b+='<rect x="0" y="600" width="1000" height="150" fill="#0a0c18"/><path d="M0,600 L1000,600" stroke="#29e3ff" stroke-width="6"/>'
    render("mb1-2",b,W,H)
    b=f'<rect width="{W}" height="{H}" fill="#0d0f1f"/><path d="M100,600 Q100,200 500,180 Q900,200 900,600 Z" fill="#e8e6df"/>'
    b+='<rect x="200" y="380" width="600" height="40" rx="20" fill="#29e3ff"/><circle cx="500" cy="300" r="36" fill="#ff3d7f"/>'
    for i in range(9): b+=f'<rect x="{230+i*62}" y="460" width="40" height="80" rx="6" fill="#151a2e"/>'
    render("mb1-3",b,W,H)
    texture("mb1-4",[24,26,48],30,[255,61,127],1)
# B: Desert rally pastel
def B():
    W,H=1600,900
    d='<linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f6d7c3"/><stop offset="1" stop-color="#f2b896"/></linearGradient>'
    b=f'<rect width="{W}" height="{H}" fill="url(#s)"/><circle cx="1250" cy="230" r="90" fill="#fff4e0"/>'
    b+='<path d="M0,620 Q400,520 800,600 T1600,580 L1600,900 L0,900 Z" fill="#e8a87c"/><path d="M0,720 Q500,640 1000,720 T1600,700 L1600,900 L0,900 Z" fill="#d98a6a"/>'
    b+='<path d="M380,700 L420,560 L620,500 L1020,495 L1180,560 L1220,700 Z" fill="#9fd3c7"/>'
    b+='<path d="M620,500 L680,430 L960,428 L1020,495 Z" fill="#385170" opacity=".7"/>'
    b+='<rect x="600" y="400" width="380" height="26" rx="6" fill="#385170"/>'
    for x in (640,720,800,880): b+=f'<circle cx="{x+20}" cy="413" r="10" fill="#fff4e0"/>'
    b+='<rect x="420" y="600" width="780" height="18" fill="#f7cac9"/>'
    b+=wheel(520,700,70,"#3d3d3d","#fff4e0")+wheel(1080,700,70,"#3d3d3d","#fff4e0")
    b+='<ellipse cx="300" cy="720" rx="200" ry="40" fill="#f6d7c3" opacity=".7"/>'
    render("mb2-1",b,W,H,d)
    W,H=1000,750
    b=f'<rect width="{W}" height="{H}" fill="#f6d7c3"/>'
    for i,c in enumerate(["#9fd3c7","#f7cac9","#e8a87c","#385170","#fff4e0","#d98a6a"]): b+=f'<rect x="{60+i*150}" y="{140+(i%2)*60}" width="130" height="420" rx="65" fill="{c}"/>'
    render("mb2-2",b,W,H)
    b=f'<rect width="{W}" height="{H}" fill="#fff4e0"/><rect x="120" y="200" width="760" height="360" rx="40" fill="#9fd3c7"/>'
    for r in range(4):
        for c in range(8): b+=f'<circle cx="{190+c*90}" cy="{270+r*75}" r="18" fill="#385170" opacity=".8"/>'
    b+='<rect x="120" y="600" width="760" height="40" rx="20" fill="#f7cac9"/>'
    render("mb2-3",b,W,H)
    texture("mb2-4",[220,170,130],18,[159,211,199],2)
A(); B()
