#!/usr/bin/env python3
"""Prepare a masthead logo PNG (transparent background) for tools/build.py.
Trims the transparent margin (glyph left edge = image left edge), measures the cap height of the
leading "C", and writes assets/<name>.webp at 2x resolution, sized so the lettering matches the
default logo. Prints the tuple to paste into SEASONAL / DEFAULT_LOGO in tools/build.py.
Usage: python3 tools/mklogo.py SRC.png cdd-xmas-light-v1 [--dark]
  --dark  = cream/light lettering (dark theme); default = black lettering (light theme)."""
import sys, os
import numpy as np
from PIL import Image
REF = 6.869  # width / "C" cap height of cdd-default-dark-v1 (the widest default) -> k = 1.0
def glyph_mask(a, dark):
    r, g, b, al = [a[..., i].astype(int) for i in range(4)]
    mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b)
    return (al > 128) & (mn > 170) & ((mx - mn) < 60) if dark else (al > 128) & (mx < 90)
def main():
    src, name = sys.argv[1], sys.argv[2]; dark = "--dark" in sys.argv
    im = Image.open(src).convert("RGBA"); a = np.array(im)
    ys, xs = np.nonzero(a[..., 3] > 24); x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    m = glyph_mask(a, dark); cols = np.nonzero(m.sum(0) >= 3)[0]; gx0, gx1 = cols.min(), cols.max() + 1
    strip = m[:, gx0:gx0 + int(.06 * (gx1 - gx0))].sum(1) >= 1; rows = np.nonzero(strip)[0]; t = e = rows[0]
    while e + 1 < len(strip) and strip[e + 1]: e += 1
    cap = e + 1 - t; k = round(min(1.0, (x1 - x0) / cap / REF), 4)
    if gx0 - x0 > 6: print(f"warning: something sits {gx0 - x0}px left of the glyphs; lettering won't be flush with the date line", file=sys.stderr)
    out = im.crop((x0, y0, x1, y1)); W = round(1440 * k); H = round(out.height * W / out.width)
    out = out.resize((W, H), Image.LANCZOS)
    dst = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", name + ".webp")
    out.save(dst, "WEBP", quality=90, method=6)
    print(f'("{name}.webp", {W}, {H}, {k})  # cap {cap}px, {os.path.getsize(dst)//1024} KB')
main()
