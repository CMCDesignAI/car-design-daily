"""Auto focal point for card images (frames are object-fit:cover).
focus_for(abs_path) -> "X% Y%" for CSS object-position so the detected car/main subject sits centred
in the visible part of a 16:9 frame (clamped to the image edges; whole car kept when it fits).
Detection: ultralytics YOLOv8n (COCO car/motorcycle/bus/truck/person fallback); no detection -> None (centre).
Results cached in tools/focus_cache.json keyed by repo-relative path + size + mtime, so it runs once per image.
Manual override: image.focus / more_images[].focus = "X% Y%" in data.json (build.py prefers it)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
CACHE_F = f"{HERE}/focus_cache.json"
_cache = None; _model = False; _dirty = False
VEH = {2, 3, 5, 7}

def _load():
    global _cache
    if _cache is None:
        try: _cache = json.load(open(CACHE_F, encoding="utf-8"))
        except Exception: _cache = {}
    return _cache

def save():
    if _dirty and _cache is not None:
        json.dump(_cache, open(CACHE_F, "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)

def _detect(p):
    """-> (box [x0,y0,x1,y1] normalised, img_w, img_h) or (None, w, h)."""
    global _model
    from PIL import Image
    w, h = Image.open(p).size
    if _model is False:
        try:
            from ultralytics import YOLO
            _model = YOLO(os.environ.get("FOCUS_MODEL", os.path.expanduser("~/.cache/focus/yolov8n.pt")))
        except Exception as ex:
            print("focus: detector unavailable:", ex); _model = None
    if _model is None: return None, w, h
    r = _model.predict(p, verbose=False, conf=0.25)[0]
    bx = [(b.xyxy[0].tolist(), int(b.cls), float(b.conf)) for b in r.boxes]
    for cls in (VEH, {0}):
        c = [x for x in bx if x[1] in cls]
        if c:
            area = lambda b: (b[0][2]-b[0][0])*(b[0][3]-b[0][1])
            big = max(area(x) for x in c)
            c = [x for x in c if area(x) >= 0.25 * big]   # main subject(s), drop tiny background cars
            x0 = min(x[0][0] for x in c); y0 = min(x[0][1] for x in c); x1 = max(x[0][2] for x in c); y1 = max(x[0][3] for x in c)
            return [x0/w, y0/h, x1/w, y1/h], w, h
    return None, w, h

def position(box, w, h, ratio=16/9):
    if not box: return None
    def axis(a0, a1, vis):   # vis = visible fraction of this axis
        if vis >= 0.999: return 50.0
        c = (a0 + a1) / 2; L = min(max(c - vis / 2, 0), 1 - vis)
        if a1 - a0 <= vis: L = min(max(L, a1 - vis), a0)   # keep whole subject if it fits
        return round(L / (1 - vis) * 100, 1)
    if w / h > ratio: return f"{axis(box[0], box[2], h*ratio/w)}% 50%"
    return f"50% {axis(box[1], box[3], (w/ratio)/h)}%"

def focus_for(p, ratio=16/9):
    global _dirty
    if not os.path.exists(p): return None
    st = os.stat(p); key = os.path.relpath(p, ROOT)
    c = _load(); sig = f"{st.st_size}:{int(st.st_mtime)}"
    e = c.get(key)
    if not e or e.get("sig") != sig:
        try: box, w, h = _detect(p)
        except Exception as ex: print("focus fail", key, ex); return None
        if box is None and _model is None: return None   # don't cache "no detector"
        e = c[key] = {"sig": sig, "box": [round(v, 4) for v in box] if box else None, "w": w, "h": h}; _dirty = True
    return position(e["box"], e["w"], e["h"], ratio)
