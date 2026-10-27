#!/usr/bin/env python3
"""Fail if any <img src> (local) in generated AI pages points to a missing file,
or any data.json image.file has a path prefix (must be a bare filename in img/)."""
import glob, json, os, re, sys
bad = []
for dj in glob.glob("ai/issues/*/data.json"):
    s = json.dumps(json.load(open(dj)), ensure_ascii=False)
    for f in re.findall(r'"file": "([^"]*)"', s):
        if "/" in f: bad.append(f"{dj}: image.file must be bare filename, got {f!r}")
for page in ["ai/index.html"] + glob.glob("ai/issues/*/index.html"):
    d = os.path.dirname(page)
    for src in re.findall(r'<img[^>]*?\ssrc="([^"]+)"', open(page).read()):
        if re.match(r'(https?:|data:|//)', src): continue
        if not os.path.isfile(os.path.normpath(os.path.join(d, src))): bad.append(f"{page}: missing {src}")
for b in bad: print("FAIL", b)
print(f"check_ai_img: {len(bad)} problem(s)"); sys.exit(1 if bad else 0)
