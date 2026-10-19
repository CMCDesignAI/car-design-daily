#!/usr/bin/env python3
"""Combined one-point-perspective interior (door trims + dash) → assets/ip-combined-template.svg.
Used by tools/build.py (interior_html) for issues dated >= 2026-10-19; colours come from the same CSS
variables as the old door/dash pair, so each day's palette fills it. Re-run after geometry edits:
  python3 tools/gen_ip_combined.py
World: X right, Y up, Z forward (metres). Camera at (0, CY, 0), image plane vertical, so every
depth line converges on VP=(CX,H0). Fronto-parallel planes (constant Z) are pure scale+translate."""
import re, math, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=os.path.join(ROOT,'assets','ip-template.svg')
OUT=os.path.join(ROOT,'assets','ip-combined-template.svg')
W_,H_=1600,780; CX,H0=800,250; F=720; CY=1.30
VX=104   # side crop per edge (6.5%), view stays centred on the VP x=800
W=0.78                      # half cabin width (door inner plane)
ZF=1.55                     # dash rear face
ZW0,YW0=1.95,1.00           # windshield base
ZW1,YW1=1.15,1.50           # windshield top / roof
RY=1.50; BY=0.95            # roof, beltline (= dash top)
S=1.56/1260                 # dash-template unit -> metres (template x -30..1230 spans the cabin)
SEATX=-0.36                 # driver seat / wheel / cluster centreline
def P(X,Y,Z): return (CX+F*X/Z, H0-F*(Y-CY)/Z)
def d(pts,close=True): return "M"+" L".join(f"{x:.1f} {y:.1f}" for x,y in pts)+(" Z" if close else "")
def poly(pts3,close=True): return d([P(*p) for p in pts3],close)

# --- tiny path sampler (M L H V Q Z absolute) for 2-D template shapes ---
def sample(path,n=10):
    toks=re.findall(r'[MLHVQZ]|-?\d*\.?\d+',path); i=0; pts=[]; cur=(0,0); cmd=None
    def num():
        nonlocal i; v=float(toks[i]); i+=1; return v
    while i<len(toks):
        t=toks[i]
        if t in 'MLHVQZ': cmd=t; i+=1
        if cmd=='Z': continue
        if cmd in 'ML': cur=(num(),num()); pts.append(cur)
        elif cmd=='H': cur=(num(),cur[1]); pts.append(cur)
        elif cmd=='V': cur=(cur[0],num()); pts.append(cur)
        elif cmd=='Q':
            c=(num(),num()); e=(num(),num()); s0=cur
            for k in range(1,n+1):
                u=k/n; pts.append(((1-u)**2*s0[0]+2*u*(1-u)*c[0]+u*u*e[0],(1-u)**2*s0[1]+2*u*(1-u)*c[1]+u*u*e[1]))
            cur=e
    return pts
def rrect(x,y,w,h,r): return f"M{x+r} {y} H{x+w-r} Q{x+w} {y} {x+w} {y+r} V{y+h-r} Q{x+w} {y+h} {x+w-r} {y+h} H{x+r} Q{x} {y+h} {x} {y+h-r} V{y+r} Q{x} {y} {x+r} {y}Z"

# --- door: template (tx 20..690, ty 250..740) mapped onto side plane; template right = front ---
DZ0,DZ1=0.85,ZF
def door_map(side,inset=0.0):
    X=side*(W-inset)
    return lambda tx,ty:(X, BY-(ty-250)/490*(BY-0.05), DZ0+(tx-20)/670*(DZ1-DZ0))
def dshape(side,path,fills,inset=0.0,extra=''):
    m=door_map(side,inset); dd=poly([m(*q) for q in sample(path)])
    return "".join(f'<path d="{dd}" fill="{f}"{extra}/>' for f in fills)
def dstroke(side,path,stroke,inset=0.0,close=False):
    m=door_map(side,inset); dd=poly([m(*q) for q in sample(path)],close)
    return f'<path d="{dd}" {stroke} fill="none"/>'
ST='stroke="var(--stitch)" stroke-width="2.2" stroke-dasharray="6 4" stroke-linecap="round"'

def door(side):
    o=[f'<g class="door door-{"l" if side<0 else "r"}">']
    shell="M20 250 H680 L690 600 Q680 730 600 740 H90 Q30 730 20 640Z"
    o.append(dshape(side,shell,["var(--door-lower)","url(#stipple)","url(#topLight)"]))
    up="M20 250 H690 V330 H20Z"
    o.append(dshape(side,up,["var(--door-upper)","url(#stipple)","url(#topLight)"]))
    o.append(dshape(side,"M20 330 H690 V344 H20Z",["var(--ip-decor)","url(#brushed)"]))
    ins="M70 360 Q72 350 84 350 H560 Q600 352 604 380 L600 470 Q596 486 580 486 H90 Q72 486 70 470Z"
    o.append(dshape(side,ins,["var(--door-insert)","url(#denim)","url(#topLight)"]))
    o.append(dstroke(side,"M86 364 H580 Q590 366 590 380 L586 466 Q584 474 576 474 H94 Q84 474 84 464Z",ST,close=True))
    # inner handle recess + lever
    o.append(dshape(side,rrect(440,372,110,46,10),["#000"],extra=' fill-opacity=".35"'))
    o.append(dshape(side,rrect(452,380,80,28,8),["var(--ip-decor)","url(#brushed)"]))
    o.append(dshape(side,rrect(530,384,14,20,3),["#c33"],extra=' fill-opacity=".7"'))
    # pull cup, speaker, map pocket
    o.append(dshape(side,"M120 560 Q300 548 470 560 L460 640 Q300 652 130 640Z",["#000"],extra=' fill-opacity=".30"'))
    o.append(dshape(side,"M90 650 H600 L596 720 Q340 732 96 720Z",["var(--door-lower)","url(#stipple)","url(#topLight)"]))
    o.append(dshape(side,"M100 660 H590 L586 708 Q340 718 104 708Z",["#000"],extra=' fill-opacity=".22"'))
    o.append(dstroke(side,"M90 650 H600",'stroke="#000" stroke-opacity=".45" stroke-width="4"'))
    o.append(dshape(side,rrect(500,570,140,66,14),["var(--ip-decor)"]))
    o.append(dshape(side,rrect(506,576,128,54,10),["var(--door-lower)","url(#perf)"]))
    # armrest: vertical face sits 7 cm proud of the door; top face carries the window switches
    AI=0.07; m0=door_map(side,0); m1=door_map(side,AI)
    ay=492; za,zb=60,638
    top=[m0(za,ay),m0(zb,ay),m1(zb-6,ay),m1(za+6,ay)]
    o.append("".join(f'<path d="{poly(top)}" fill="{f}"/>' for f in ["var(--armrest)","url(#grain)"]))
    o.append(f'<path d="{poly(top)}" fill="#fff" fill-opacity=".10"/>')
    face="M60 492 H610 Q640 494 638 520 L630 548 H80 Q56 548 58 520Z"
    o.append(dshape(side,face,["var(--armrest)","url(#grain)","url(#topLight)"],inset=AI))
    o.append(dstroke(side,"M76 504 H604",ST,inset=AI))
    # switch pack on armrest top (in X–Z plane)
    def sw(z0,z1,i0,i1,fill,extra=''):
        mm=lambda tx,ins:door_map(side,ins)(tx,ay)
        q=[mm(z0,i0),mm(z1,i0),mm(z1,i1),mm(z0,i1)]
        return f'<path d="{poly(q)}" fill="{fill}"{extra}/>'
    o.append(sw(440,590,0.012,0.058,"#1a1a1a"))
    for k in range(4): o.append(sw(452+34*k,478+34*k,0.02,0.05,"#3a3a3a"))
    # beltline cap (top of door roll) – lines up with the dash top
    cap=[door_map(side,0)(20,250),door_map(side,0)(690,250),door_map(side,0.05)(690,250),door_map(side,0.05)(20,250)]
    o.append(f'<path d="{poly(cap)}" fill="var(--door-upper)"/><path d="{poly(cap)}" fill="#fff" fill-opacity=".14"/>')
    o.append('</g>')
    return "".join(o)

BPF0,BPF1=0.85,0.86   # B-pillar front edge Z at beltline / roof (raked so it leans toward the VP)
BPR0,BPR1=0.68,0.69   # B-pillar rear edge
CARPET='#141516'   # fixed deep-black carpet (floor + kick panels), never palette-driven
def carpet(pts):
    dd=poly(pts)
    return f'<path d="{dd}" fill="{CARPET}"/><path d="{dd}" fill="url(#weave)" opacity=".5"/>'
TRIM=["var(--headliner)","url(#weave)"]
def trim(pts,shade=".12"):
    dd=poly(pts); return "".join(f'<path d="{dd}" fill="{f}"/>' for f in TRIM)+f'<path d="{dd}" fill="#000" fill-opacity="{shade}"/>'
WT=1.455  # side-window top at the B-pillar (rear corner)
WTF,ZTF=1.49,1.19   # side-window top at the A-pillar (front corner): the frame line is a near-horizontal roofline on screen
def sidewall(side):
    X=side*W; o=[]
    wall=[(X,0,0.2),(X,RY,0.2),(X,RY,ZW1),(X,YW0,ZW0),(X,0,ZW0)]
    o.append(trim(wall))                                   # one continuous trim surface: rail, B- and A-pillar side
    o.append(carpet([(X,0,DZ0),(X,0,ZW0),(X,0.80,ZW0),(X,0.80,DZ0)]))
    fz=[(X,0.45,DZ1-0.01),(X,0.45,ZW0),(X,YW0,ZW0),(X,BY,DZ1-0.01)]
    o.append("".join(f'<path d="{poly(fz)}" fill="{f}"/>' for f in ["var(--door-upper)","url(#stipple)","url(#topLight)"]))
    o.append(f'<path d="{poly(fz)}" fill="#000" fill-opacity=".10"/>')
    lw=[(X,0,0.2),(X,BY,0.2),(X,BY,DZ0+0.02),(X,0,DZ0+0.02)]
    o.append("".join(f'<path d="{poly(lw)}" fill="{f}"/>' for f in ["var(--door-upper)","url(#stipple)","url(#topLight)"]))
    o.append(f'<path d="{poly(lw)}" fill="#000" fill-opacity=".18"/>')
    o.append(f'<path d="{poly([(X,BY,DZ0-0.004),(X,0,DZ0-0.004)],False)}" stroke="#000" stroke-opacity=".6" stroke-width="5"/>')
    # front side glass: top frame along WT (recedes to the VP), straight down the B-pillar front edge,
    # front edge parallel to the A-pillar
    zt=BPF0+(BPF1-BPF0)*(WT-BY)/(RY-BY)
    glass=[(X,BY+.01,BPF0),(X,BY+.01,1.86),(X,WTF,ZTF),(X,WT,zt)]
    gid=f'sideglass{"L" if side<0 else "R"}'
    o.append(f'<clipPath id="{gid}"><path d="{poly(glass)}"/></clipPath>')
    o.append(f'<path d="{poly(glass)}" fill="url(#sky)"/>')
    o.append(f'<path d="{poly([(X,1.0,1.28),(X,1.0,1.42),(X,1.42,1.12),(X,1.42,1.00)])}" fill="#fff" fill-opacity=".35"/>')
    o.append(f'<g clip-path="url(#{gid})">{wing_mirror(side)}</g>')
    # black triangular sail panel at the window's front-lower corner (part of the frame, not glass)
    sail=[(X,BY+.01,1.86),(X,BY+.01,1.655),(X,1.12,1.655),(X,1.12,1.86-0.67*(1.12-BY-0.01)/(WTF-BY-0.01))]
    o.append(f'<path d="{poly(sail)}" fill="#121315"/>')
    # clean seals: top frame, B-pillar edge, A-pillar edge
    o.append(f'<path d="{poly([(X,BY+.01,BPF0),(X,WT,zt),(X,WTF,ZTF),(X,BY+.01,1.86)],False)}" stroke="#2b2f36" stroke-opacity=".75" stroke-width="4" fill="none" stroke-linejoin="round"/>')
    o.append(f'<path d="{poly([(X,BY+0.004,BPR0),(X,BY+0.004,1.80)],False)}" stroke="var(--door-upper)" stroke-width="6"/>')
    # B-pillar shading only (same trim material), plus belt adjuster
    bp=[(X,BY,BPR0),(X,BY,BPF0),(X,WT,zt),(X,RY,BPF1),(X,RY,BPR1)]
    o.append(f'<path d="{poly(bp)}" fill="#000" fill-opacity=".05"/>')
    o.append(f'<path d="{poly([(X,1.22,BPF1-0.075),(X,1.22,BPF1-0.045),(X,1.30,BPF1-0.04),(X,1.30,BPF1-0.07)])}" fill="#2a2b2e"/>')
    return "".join(o)

def wing_mirror(side):
    # original rounded-rect mirror (housing + rounded-rect glass), top edge trimmed with a small chamfer
    # at the top inner/front corner; glass faces rearward (Z plane)
    xi,xo=W+0.07,W+0.25; y0,y1=0.99,1.15; zr,zf=1.64,1.73
    def outline(x0,x1,ya,yb,r,ch,z):
        # rounded corners except the top-inner corner, which is cut by a chamfer of size ch
        pts=[]
        def arc(cx_,cy_,a0):
            for k in range(7):
                a=math.radians(a0+15*k); pts.append((cx_+r*math.cos(a),cy_+r*math.sin(a)))
        arc(x1-r,ya+r,270)            # bottom-outer
        arc(x1-r,yb-r-0.008,0)        # top-outer (top trimmed slightly lower)
        pts.append((x0+ch,yb-0.008)); pts.append((x0,yb-0.008-ch*0.8))   # chamfer at top-inner
        arc(x0+r,ya+r,180)            # bottom-inner
        return [(side*x,y,z) for x,y in pts]
    o=[]
    # thick, filled stalk from the sail panel; bottom flush with the housing bottom (Y=y0)
    xa,xb=side*(W-0.01),side*(xi+0.04); ya=y0+0.10
    st_top=[(xa,ya,zr),(xb,ya,zr),(xb,ya,zr+0.07),(xa,ya,zr+0.07)]
    st_rear=[(xa,y0,zr),(xb,y0,zr),(xb,ya,zr),(xa,ya,zr)]
    o.append(f'<path d="{poly(st_top)}" fill="#2a2c30" stroke="#2a2c30" stroke-width="1"/>')
    o.append(f'<path d="{poly(st_rear)}" fill="#141517" stroke="#141517" stroke-width="1"/>')
    # housing depth: top + inner side faces between rear and front outlines
    R=outline(xi,xo,y0,y1,0.035,0.045,zr); Fz=outline(xi,xo,y0,y1,0.035,0.045,zf)
    for i in range(len(R)):
        j=(i+1)%len(R); q=[R[i],R[j],Fz[j],Fz[i]]
        o.append(f'<path d="{poly(q)}" fill="#1c1d20" stroke="#1c1d20" stroke-width="1"/>')
    o.append("".join(f'<path d="{poly(R)}" fill="{f}"/>' for f in ["#141517","url(#topLight)"]))
    G=outline(xi+0.015,xo-0.012,y0+0.014,y1-0.012,0.025,0.035,zr-0.002)
    o.append(f'<path d="{poly(G)}" fill="#c3ccd2"/><path d="{poly(G)}" fill="url(#sky)" opacity=".6"/>')
    o.append(f'<path d="{poly([(side*(xi+0.05),y0+0.02,zr-0.003),(side*(xi+0.09),y1-0.03,zr-0.003)],False)}" stroke="#fff" stroke-opacity=".7" stroke-width="5"/>')
    return "".join(o)

def wsp(X,t): return (X, YW0+(YW1-YW0)*t, ZW0+(ZW1-ZW0)*t)   # point on windshield plane
def apillar(side):
    o=[]; a,b=side*W,side*(W-0.11)
    band=[wsp(a,0),wsp(a,1),wsp(b,1),wsp(b,0)]
    o.append("".join(f'<path d="{poly(band)}" fill="{f}"/>' for f in ["var(--headliner)","url(#weave)"]))
    o.append(f'<path d="{poly(band)}" fill="#000" fill-opacity=".06"/>')
    o.append(f'<path d="{poly([wsp(b,0),wsp(b,1)],False)}" stroke="#000" stroke-opacity=".25" stroke-width="2"/>')
    # grab handle on the pillar
    def gp(dx,t): return P(*wsp(side*(W-0.055)+dx,t))
    pts=[gp(0,.62),gp(-side*0.035,.66),gp(-side*0.04,.86),gp(0,.9)]
    o.append(f'<path d="{d(pts,False)}" stroke="#000" stroke-opacity=".22" stroke-width="17" fill="none" stroke-linecap="round" stroke-linejoin="round" transform="translate(2 3)"/><path d="{d(pts,False)}" stroke="var(--headliner-hi)" stroke-width="14" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
    o.append(f'<path d="{d(pts,False)}" stroke="#fff" stroke-opacity=".6" stroke-width="3" fill="none" stroke-linecap="round" transform="translate(-1 -2)"/>')
    return "".join(o)

def wheel():
    # wheel plane at Z=1.33, centre on the driver-seat centreline (X=SEATX)
    ZS=1.40; cx,cy=P(SEATX,0.80,ZS); k=F*0.175/128/ZS   # rim radius 0.175 m
    col=[P(SEATX-0.035,0.76,ZS),P(SEATX+0.035,0.76,ZS),P(SEATX+0.05,0.70,ZF-0.02),P(SEATX-0.05,0.70,ZF-0.02)]
    g=[f'<path d="{d(col)}" fill="#1a1b1d"/>']
    g.append(f'<g id="steering" transform="translate({cx:.1f} {cy:.1f}) scale({k:.4f})">')
    g.append('<circle r="128" fill="none" stroke="var(--steering)" stroke-width="36"/>'
             '<circle r="128" fill="none" stroke="url(#perf)" stroke-width="36" opacity=".30"/>'
             '<circle cy="-5" r="131" fill="none" stroke="#fff" stroke-opacity=".12" stroke-width="7"/>'
             '<path d="M-128 0 A128 128 0 0 1 128 0" stroke="var(--stitch)" stroke-width="2.6" stroke-dasharray="6 4" fill="none" stroke-linecap="round"/>')
    # horizontal spokes with button pads
    for sx in (-1,1):
        g.append(f'<path d="M{sx*112} -16 L{sx*44} -24 L{sx*44} 26 L{sx*112} 20Z" fill="var(--steering)"/>'
                 f'<path d="M{sx*112} -16 L{sx*44} -24 L{sx*44} 26 L{sx*112} 20Z" fill="url(#topLight)"/>')
        for r_ in range(2):
            for c_ in range(2):
                x0=sx*(56+c_*22)-(9 if sx>0 else 9); g.append(f'<rect x="{x0-0:.0f}" y="{-14+r_*18}" width="17" height="13" rx="3" fill="#3a3d42"/>')
        g.append(f'<circle cx="{sx*100}" cy="2" r="5" fill="#4a4d52"/>')
    # broad dark lower spoke
    g.append('<path d="M-46 30 L46 30 L36 92 Q30 118 0 120 Q-30 118 -36 92Z" fill="#17181a"/>'
             '<path d="M-46 30 L46 30 L36 92 Q30 118 0 120 Q-30 118 -36 92Z" fill="url(#stipple)"/>')
    # wide shield / trapezoid airbag hub with emblem
    hub="M-60 -40 Q0 -50 60 -40 Q66 -38 64 -30 L52 30 Q46 54 0 60 Q-46 54 -52 30 L-64 -30 Q-66 -38 -60 -40Z"
    g.append(f'<path d="{hub}" fill="var(--steering)"/><path d="{hub}" fill="url(#topLight)"/><path d="{hub}" fill="none" stroke="#000" stroke-opacity=".35" stroke-width="2"/>')
    # (no emblem: plain hub)
    g.append('</g>')
    return "".join(g)

def seat(side):
    # seat CUSHION only (no backrest): horizontal plane Y=YC seen from above.
    # Front edge = rounded arch (parabola + rounded corners); sides run along Z so they converge on the VP.
    cx=side*abs(SEATX); YC=0.60; ZN=0.35
    def arch(hw,zf,a,r):
        pts=[]
        for k in range(41):
            u=-hw+2*hw*k/40; z=zf-a*(u/hw)**2; e=abs(u)-(hw-r)
            if e>0: z-=r-math.sqrt(max(r*r-e*e,0))
            pts.append((u,z))
        return pts
    def shape(hw,zf,a,r):
        f=arch(hw,zf,a,r); return [(-hw,ZN)]+f+[(hw,ZN)]
    w3=lambda pts,y=YC:[(cx+u,y,z) for u,z in pts]
    o=['<g class="seat cushion">']
    # inner side face (toward the console) – the only side the centre camera can see
    xi=cx-side*0.25
    sf=[(xi,YC,ZN),(xi,YC,0.97),(xi,0.30,0.97),(xi,0.30,ZN)]
    o.append(f'<path d="{poly(sf)}" fill="var(--seat-bolster)"/><path d="{poly(sf)}" fill="#000" fill-opacity=".45"/>')
    OUT=shape(0.25,1.11,0.07,0.07)
    o.append("".join(f'<path d="{poly(w3(OUT))}" fill="{f}"/>' for f in ["var(--seat-bolster)","url(#denim)","url(#pillow)"]))
    # piping along the outer arch
    o.append(f'<path d="{poly(w3(arch(0.235,1.10,0.07,0.06)),False)}" {ST} fill="none"/>')
    # bolster/insert seam shadow, then the centre insert (concentric contour)
    o.append(f'<path d="{poly(w3(shape(0.150,1.040,0.05,0.05)))}" fill="#000" fill-opacity=".35"/>')
    INS=shape(0.140,1.035,0.05,0.05)
    o.append("".join(f'<path d="{poly(w3(INS))}" fill="{f}"/>' for f in ["var(--seat-center)","url(#grain)","url(#pillow)"]))
    o.append(f'<path d="{poly(w3(shape(0.125,1.022,0.045,0.04)),False)}" {ST} fill="none"/>')
    # lengthwise channels: twin stitch lines along Z (they converge on the VP)
    for u in (-0.07,-0.02,0.02,0.07):
        zf=1.022-0.045*(u/0.125)**2-0.01
        o.append(f'<path d="{poly([(cx+u,YC,ZN),(cx+u,YC,zf)],False)}" {ST}/>')
    for u in (-0.045,0.045):
        zf=1.022-0.045*(u/0.125)**2-0.01
        o.append(f'<path d="{poly([(cx+u,YC,ZN),(cx+u,YC,zf)],False)}" stroke="#000" stroke-opacity=".30" stroke-width="3"/>')
    # outer bolster crown line
    for u in (-0.20,0.20):
        zf=1.11-0.07*(u/0.25)**2-0.03
        o.append(f'<path d="{poly([(cx+u,YC,ZN),(cx+u,YC,zf)],False)}" stroke="#fff" stroke-opacity=".10" stroke-width="5"/>')
    o.append('</g>')
    return "".join(o)

def console():
    o=[]
    # lower console (tunnel) top face, front meets the stack
    t=[(-0.10,0.48,0.95),(0.10,0.48,0.95),(0.10,0.50,1.52),(-0.10,0.50,1.52)]
    o.append("".join(f'<path d="{poly(t)}" fill="{f}"/>' for f in ["var(--console)","url(#stipple)"]))
    o.append(f'<path d="{poly(t)}" fill="#fff" fill-opacity=".06"/>')
    br=[(-0.10,0.50,1.52),(0.10,0.50,1.52),(0.10,0.60,1.52),(-0.10,0.60,1.52)]
    o.append("".join(f'<path d="{poly(br)}" fill="{f}"/>' for f in ["var(--console)","url(#topLight)"]))
    # cup holders + handbrake lever
    for zc in (1.44,1.28):
        c=P(0,0.48,zc); rx=F*0.045/zc; ry=rx*0.38
        o.append(f'<ellipse cx="{c[0]:.1f}" cy="{c[1]:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="#0c0d0e"/>')
    a=P(0.055,0.49,1.02); b=P(0.055,0.56,1.10)
    o.append(f'<path d="M{a[0]:.1f} {a[1]:.1f} L{b[0]:.1f} {b[1]:.1f}" stroke="#2a2c2f" stroke-width="20" stroke-linecap="round"/>'
             f'<path d="M{a[0]:.1f} {a[1]:.1f} L{b[0]:.1f} {b[1]:.1f}" stroke="#fff" stroke-opacity=".15" stroke-width="3" stroke-linecap="round"/>')
    # armrest box top
    at=[(-0.09,0.66,0.75),(0.09,0.66,0.75),(0.09,0.66,0.97),(-0.09,0.66,0.97)]
    rf=[(-0.09,0.66,0.75),(0.09,0.66,0.75),(0.09,0.30,0.75),(-0.09,0.30,0.75)]
    o.append("".join(f'<path d="{poly(at)}" fill="{f}"/>' for f in ["var(--console-arm)","url(#weave)","url(#pillow)"]))
    st=[(-0.075,0.66,0.75),(-0.075,0.66,0.95),(0.075,0.66,0.95),(0.075,0.66,0.75)]
    o.append(f'<path d="{poly(st,False)}" {ST} fill="none"/>')
    o.append("".join(f'<path d="{poly(rf)}" fill="{f}"/>' for f in ["var(--console)","url(#stipple)","url(#topLight)"]))
    return "".join(o)

def dash_face(tpl):
    # fronto-parallel plane Z=ZF: uniform scale of the existing dash template
    k=F*S/ZF; x0=CX-600*k; y0=P(0,BY,ZF)[1]-250*k
    body=tpl[tpl.index('<!-- upper dash'):tpl.index('<!-- steering')]
    # tablet screen on top of the stack (template coords, stack centred on x=600)
    tab=('<g id="tablet"><rect x="486" y="196" width="228" height="128" rx="10" fill="#111214"/>'
         '<rect x="496" y="206" width="208" height="108" rx="5" fill="url(#screen)"/>'
         '<path d="M520 290 Q600 236 680 290" stroke="#6fb6ff" stroke-opacity=".7" stroke-width="5" fill="none"/>'
         '<rect x="562" y="232" width="76" height="16" rx="3" fill="#fff" fill-opacity=".25"/>'
         '<g fill="#6fb6ff" fill-opacity=".45"><rect x="512" y="296" width="20" height="10" rx="2"/><rect x="540" y="296" width="20" height="10" rx="2"/><rect x="640" y="296" width="20" height="10" rx="2"/><rect x="668" y="296" width="20" height="10" rx="2"/></g></g>')
    # brighter cluster graphics
    cx_=600+SEATX/S-260
    body=body.replace('<g id="cluster" transform="translate(-160 0)">',f'<g id="cluster" transform="translate({cx_-160:.1f} 0)">')
    clu=(f'<g transform="translate({cx_-160:.1f} 0)"><rect x="330" y="276" width="180" height="44" rx="6" fill="#0b1a2a" fill-opacity=".6"/>'
         '<path d="M344 312 A26 26 0 0 1 396 312" stroke="#7fc4ff" stroke-width="4" fill="none"/><path d="M444 312 A26 26 0 0 1 496 312" stroke="#7fc4ff" stroke-opacity=".8" stroke-width="4" fill="none"/>'
         '<rect x="404" y="286" width="32" height="14" rx="2" fill="#bfe3ff" fill-opacity=".55"/></g>')
    return f'<g id="dash" transform="matrix({k:.4f} 0 0 {k:.4f} {x0:.1f} {y0:.1f})">{body}{clu}{tab}</g>'

def frit():
    a=W-0.11; b=0.04; tt=0.935
    def U(inset_side,inset_top,mz=True):
        ai=a-inset_side; ti=tt-inset_top
        pts=[wsp(-ai,0),wsp(-ai,ti)]
        if mz: pts+= [wsp(-0.17+inset_side,ti),wsp(-0.12+inset_side,0.74-inset_top),wsp(0.12-inset_side,0.74-inset_top),wsp(0.17-inset_side,ti)]
        pts+=[wsp(ai,ti),wsp(ai,0)]
        return pts
    outer=[wsp(-a,0),wsp(-a,1.02),wsp(a,1.02),wsp(a,0)]
    band=outer+U(b,0)[::-1]
    o=[f'<path d="{poly(band)}" fill="#0c0d0e"/>']
    dots=U(b,0)+U(b+0.028,0.05)[::-1]
    o.append(f'<path d="{poly(dots)}" fill="url(#fritdots)"/>')
    return "".join(o)

def build():
    tpl=open(SRC,encoding='utf-8').read()
    defs=tpl[tpl.index('<defs>'):tpl.index('</defs>')+7].replace('</defs>','<pattern id="fritdots" width="5" height="5" patternUnits="userSpaceOnUse"><circle cx="2.5" cy="2.5" r="1.3" fill="#0c0d0e"/></pattern></defs>')
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VX} 0 {W_-2*VX} {H_}" class="intsvg" role="img" aria-label="車室透視配色示意（程式繪製）：門板、車窗、A/B 柱、儀表台、中控塔、方向盤、座椅與中央扶手">',defs]
    o.append(f'<rect width="{W_}" height="{H_}" fill="url(#sky)"/>')
    # outside hint: horizon band through the windshield
    o.append(f'<rect y="{H0+50}" width="{W_}" height="160" fill="#b9c0c4" opacity=".35"/>')
    o.append(frit())
    # roof / headliner
    roof=[(-W,RY,0.15),(W,RY,0.15),(W,RY,ZW1),(-W,RY,ZW1)]
    o.append("".join(f'<path d="{poly(roof)}" fill="{f}"/>' for f in ["var(--headliner)","url(#weave)"]))
    o.append(f'<path d="{poly(roof)}" fill="#000" fill-opacity=".06"/>')
    m=P(0,1.47,ZW1+0.02); mw=F*0.13/(ZW1+.02); mh=F*0.05/(ZW1+.02)
    o.append(f'<path d="M{m[0]:.1f} {m[1]-mh:.1f} V{m[1]:.1f}" stroke="#2a2a2a" stroke-width="6"/><rect x="{m[0]-mw:.1f}" y="{m[1]:.1f}" width="{2*mw:.1f}" height="{mh:.1f}" rx="10" fill="#2a2a2a"/>')
    for s in (-1,1): o.append(sidewall(s))
    # floor (carpet) + firewall / footwells
    fl=[(-W,0,0.25),(W,0,0.25),(W,0,ZW0),(-W,0,ZW0)]
    o.append(carpet(fl))
    fw=[(-W,0,ZW0),(W,0,ZW0),(W,0.75,ZW0),(-W,0.75,ZW0)]
    o.append(f'<path d="{poly(fw)}" fill="#0f1011"/><path d="{poly(fw)}" fill="url(#weave)" opacity=".5"/>')
    for i,dx in enumerate((-0.13,0.0,0.13)):   # pedals on driver side
        X=SEATX+dx*0.8; w=0.03 if i else 0.05
        o.append(f'<path d="{poly([(X-w,0.16,1.88),(X+w,0.16,1.88),(X+w,0.33,1.86),(X-w,0.33,1.86)])}" fill="#1c1d1f" stroke="#3a3c40" stroke-width="1.5"/>')
    for s in (-1,1): o.append(door(s))
    # dash top surface: face top edge -> windshield base
    top=[(-W,BY,ZF),(W,BY,ZF),(W,YW0,ZW0),(-W,YW0,ZW0)]
    o.append("".join(f'<path d="{poly(top)}" fill="{f}"/>' for f in ["var(--ip-upper)","url(#stipple)"]))
    o.append(f'<path d="{poly(top)}" fill="#000" fill-opacity=".18"/>')
    for s in (-1,1): o.append(apillar(s))
    for s_ in (-1,1):
        kp=[(s_*W,0.63,1.60),(s_*0.10,0.63,1.60),(s_*0.10,0.50,1.60),(s_*0.25,0.47,1.60),(s_*(W-0.05),0.47,1.60),(s_*W,0.52,1.60)]
        o.append("".join(f'<path d="{poly(kp)}" fill="{f}"/>' for f in ["var(--ip-lower)","url(#stipple)","url(#topLight)"]))
        o.append(f'<path d="{poly(kp)}" fill="#000" fill-opacity=".25"/>')
    o.append(dash_face(tpl))
    o.append(console())
    o.append(wheel())
    for s in (-1,1): o.append(seat(s))
    o.append(f'<rect x="{VX}" width="{W_-2*VX}" height="{H_}" fill="url(#vig)"/></svg>')
    open(OUT,'w',encoding='utf-8').write("\n".join(o))
    print("VP",(CX,H0),"seatX",round(SEATX,3),"wheel",[round(v,1) for v in P(SEATX,0.84,1.33)])
build()
