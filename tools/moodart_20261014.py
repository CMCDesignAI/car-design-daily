#!/usr/bin/env python3
"""Mood boards for 2026-10-14: Monaco Riviera grand tourer / Kyoto craft & washi interior."""
import sys, os, subprocess, math, numpy as np
from PIL import Image, ImageFilter
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
TMP = "/tmp/moodart1014"; os.makedirs(TMP, exist_ok=True)
rng = np.random.default_rng(20261014)
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
# A: Monaco Riviera grand tourer
def A():
    W,H=1600,900
    d='<linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f4d9b0"/><stop offset=".55" stop-color="#9cc7d8"/><stop offset="1" stop-color="#1f5f8b"/></linearGradient>'
    b=f'<rect width="{W}" height="{H}" fill="url(#s)"/><circle cx="1300" cy="200" r="80" fill="#fff3dc" opacity=".9"/>'
    b+='<path d="M0,470 Q200,380 420,430 Q600,330 820,420 L820,520 L0,560 Z" fill="#c98f6b" opacity=".7"/>'
    for i in range(7): b+=f'<rect x="{60+i*90}" y="{430-i%3*20}" width="70" height="{90+i%3*20}" fill="{["#f2e6d0","#e9b98f","#f5d8c8"][i%3]}"/>'
    b+=f'<rect y="560" width="{W}" height="140" fill="#1f5f8b"/><rect y="700" width="{W}" height="200" fill="#d8cbb4"/>'
    b+='<path d="M300,760 L330,660 Q360,610 470,600 L700,590 Q790,520 960,515 Q1090,520 1160,590 L1300,610 Q1360,625 1365,700 L1370,760 Z" fill="#7a1f2b"/>'
    b+='<path d="M720,592 Q800,532 960,528 Q1070,532 1130,590 Z" fill="#20303f" opacity=".85"/>'
    b+='<path d="M330,690 L1365,690" stroke="#c9a96e" stroke-width="5"/>'
    b+=wheel(480,760,62,"#1a1a1a","#c9a96e")+wheel(1180,760,62,"#1a1a1a","#c9a96e")
    render("mb1-1",b,W,H,d)
    W,H=1000,750
    b=f'<rect width="{W}" height="{H}" fill="#f2e6d0"/>'
    for i,c in enumerate(["#7a1f2b","#1f5f8b","#c9a96e","#f2e6d0","#e9b98f","#20303f"]): b+=f'<rect x="{70+i*145}" y="140" width="120" height="470" rx="10" fill="{c}" stroke="#20303f" stroke-width="2"/>'
    render("mb1-2",b,W,H)
    b=f'<rect width="{W}" height="{H}" fill="#e9b98f"/>'
    for r in range(6): b+=f'<rect x="120" y="{120+r*85}" width="760" height="70" rx="30" fill="#7a1f2b"/><path d="M140,{155+r*85} L860,{155+r*85}" stroke="#f2e6d0" stroke-width="2" stroke-dasharray="8 8"/>'
    b+='<circle cx="500" cy="380" r="90" fill="none" stroke="#c9a96e" stroke-width="14"/>'
    render("mb1-3",b,W,H)
    texture("mb1-4",[120,30,42],22,[201,169,110],1)
# B: Kyoto craft & washi interior
def B():
    W,H=1600,900
    b=f'<rect width="{W}" height="{H}" fill="#efe6d6"/>'
    for i in range(17): b+=f'<line x1="{i*100}" y1="0" x2="{i*100}" y2="560" stroke="#8a6a4a" stroke-width="6"/>'
    for j in range(6): b+=f'<line x1="0" y1="{j*100}" x2="{W}" y2="{j*100}" stroke="#8a6a4a" stroke-width="4"/>'
    b+='<rect y="560" width="1600" height="340" fill="#c8b48a"/>'
    for i in range(8): b+=f'<rect x="{i*200}" y="560" width="200" height="340" fill="none" stroke="#3e5641" stroke-width="5"/>'
    b+='<path d="M380,720 Q380,560 520,540 L1080,540 Q1220,560 1220,720 Z" fill="#f7f1e3" stroke="#3e5641" stroke-width="5"/>'
    b+='<rect x="440" y="610" width="720" height="38" rx="19" fill="#a33b2a"/>'
    b+='<path d="M560,540 Q800,470 1040,540" fill="none" stroke="#8a6a4a" stroke-width="10"/>'
    render("mb2-1",b,W,H)
    W,H=1000,750
    b=f'<rect width="{W}" height="{H}" fill="#f7f1e3"/>'
    for i in range(40): b+=f'<path d="M0,{20+i*18} Q500,{10+i*18+(i%3)*8} 1000,{20+i*18}" stroke="#d6c9ae" stroke-width="2" fill="none"/>'
    b+='<rect x="140" y="160" width="300" height="420" fill="#efe6d6" stroke="#8a6a4a" stroke-width="10"/><rect x="560" y="160" width="300" height="420" fill="#efe6d6" stroke="#8a6a4a" stroke-width="10"/>'
    for k in range(3): b+=f'<line x1="{140+(k+1)*75}" y1="160" x2="{140+(k+1)*75}" y2="580" stroke="#8a6a4a" stroke-width="5"/><line x1="{560+(k+1)*75}" y1="160" x2="{560+(k+1)*75}" y2="580" stroke="#8a6a4a" stroke-width="5"/>'
    render("mb2-2",b,W,H)
    b=f'<rect width="{W}" height="{H}" fill="#3e5641"/>'
    for r in range(10):
        for c in range(14): b+=f'<rect x="{40+c*68}" y="{40+r*68}" width="58" height="58" fill="{["#c8b48a","#a33b2a","#efe6d6"][(r+c)%3]}" opacity=".85"/>'
    render("mb2-3",b,W,H)
    texture("mb2-4",[232,222,200],10,[138,106,74],2)
A(); B()
