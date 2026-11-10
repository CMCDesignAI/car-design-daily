#!/usr/bin/env python3
"""Compact image review sheets; crop coordinates are original, right/bottom exclusive."""
import argparse
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit, unquote

from PIL import Image, ImageDraw

UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36'


def positive(value):
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError('must be positive')
    return value


def margins(im, original):
    """Require essentially solid full edge lines; stop at first visible content.

    Work on a bounded preview, ignore <=2 original pixels, and never remove
    more than 20% per side. Conservative on skies and pale photographic detail.
    """
    sample = im.copy()
    sample.thumbnail((600, 600))
    w, h = sample.size
    px = sample.load()
    bounds = [0, 0, w, h]
    for side in range(4):
        length, depth = (h, w) if side % 2 == 0 else (w, h)
        def line(d):
            if side == 0: return [px[d, y] for y in range(length)]
            if side == 2: return [px[w-1-d, y] for y in range(length)]
            if side == 1: return [px[x, d] for x in range(length)]
            return [px[x, h-1-d] for x in range(length)]
        edge = line(0)
        color = tuple(sum(p[c] for p in edge)/length for c in range(3))
        def solid(row):
            return sum(max(abs(p[c]-color[c]) for c in range(3)) <= 6 for p in row) / length >= .9999
        if not solid(edge):
            continue
        inset = 0
        for d in range(1, max(2, int(depth*.2))):
            if not solid(line(d)): break
            inset = d + 1
        else:
            continue  # no distinct interior: flat image/sky, not a clear border
        if inset * original[side % 2] / depth <= 2:
            continue
        inset = max(0, inset-2)  # leave a small safety rim around fine detail
        if side == 0: bounds[0] = inset
        elif side == 1: bounds[1] = inset
        elif side == 2: bounds[2] = w-inset
        else: bounds[3] = h-inset
    bbox = [round(bounds[i] * original[i % 2] / (w if i % 2 == 0 else h)) for i in range(4)]
    return bbox if bbox != [0, 0, *original] else None


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog='16 inputs per page: --out, then stem_p2.jpg, stem_p3.jpg. Sheets <=1600px wide, <300KB. Failed inputs retain cells.')
    parser.add_argument('--out', required=True)
    parser.add_argument('--cols', type=positive, default=4)
    parser.add_argument('--thumb', type=positive, default=320)
    parser.add_argument('--check-edges', action='store_true')
    parser.add_argument('inputs', nargs='+')
    args = parser.parse_args()
    cols = min(args.cols, 16, len(args.inputs))
    thumb = min(args.thumb, max(1, 1600//cols-16))
    cw, ch = thumb+16, thumb+70
    records, written = [], []
    try:
        with tempfile.TemporaryDirectory(prefix='contact_sheet_') as tmp:
            for start in range(0, len(args.inputs), 16):
                batch = args.inputs[start:start+16]
                sheet = Image.new('RGB', (cols*cw, math.ceil(len(batch)/cols)*ch), '#eeeeee')
                draw = ImageDraw.Draw(sheet)
                for j, source in enumerate(batch):
                    rec = dict(index=start+j+1, path=source, size=None, kb=None, suggested_bbox=None, has_margin=False)
                    x, y = (j % cols)*cw+8, (j//cols)*ch+8
                    name = unquote(urlsplit(source).path.split('/')[-1]) if source.startswith(('http://','https://')) else Path(source).name
                    try:
                        path = Path(source)
                        remote = source.startswith(('http://','https://'))
                        if remote:
                            path = Path(tmp)/'download'
                            result = subprocess.run(['curl','-fsSL','-m','15','-A',UA,'-o',str(path),source], capture_output=True)
                            if result.returncode: raise ValueError('download failed: '+result.stderr.decode(errors='replace').strip()[-140:])
                        rec['kb'] = round(path.stat().st_size/1024, 2)
                        try:
                            with Image.open(path) as original:
                                rec['size'] = list(original.size)
                                # JPEG decoder reduces allocation before RGB conversion.
                                original.draft('RGB', (max(600,thumb), max(600,thumb)))
                                original.thumbnail((max(600,thumb), max(600,thumb)))
                                im = original.convert('RGB')
                        finally:
                            if remote: path.unlink(missing_ok=True)
                        if args.check_edges:
                            rec['suggested_bbox'] = margins(im, rec['size'])
                            rec['has_margin'] = rec['suggested_bbox'] is not None
                        im.thumbnail((thumb,thumb))
                        ix, iy = x+(thumb-im.width)//2, y+(thumb-im.height)//2
                        sheet.paste(im,(ix,iy))
                        if rec['has_margin']:
                            b = rec['suggested_bbox']; w,h = rec['size']
                            box = (ix+round(b[0]*im.width/w), iy+round(b[1]*im.height/h), ix+min(im.width-1,round(b[2]*im.width/w)), iy+min(im.height-1,round(b[3]*im.height/h)))
                            draw.rectangle(box, outline='#ff00aa', width=3)
                        info = f"{rec['size'][0]}x{rec['size'][1]} | {rec['kb']} KB"
                    except Exception as exc:
                        rec['error'] = str(exc)
                        draw.text((x,y+thumb//2), 'FAIL: '+str(exc)[:38], fill='red')
                        info = 'FAIL'
                    label = f"{rec['index']}. {name}"
                    # Pillow's default font is not guaranteed to cover arbitrary filenames.
                    label = label.encode('ascii','replace').decode()
                    draw.text((x,y+thumb+5), label[:max(3,thumb//6)], fill='black')
                    draw.text((x,y+thumb+23),info,fill='black')
                    records.append(rec)
                out = Path(args.out) if start == 0 else Path(args.out).with_name(Path(args.out).stem+f'_p{start//16+1}.jpg')
                for quality in range(85, 9, -5):
                    buffer = io.BytesIO()
                    sheet.save(buffer, 'JPEG', quality=quality, optimize=True)
                    if buffer.tell() < 300*1024: break
                while buffer.tell() >= 300*1024:
                    sheet = sheet.resize((max(1,sheet.width*9//10), max(1,sheet.height*9//10)))
                    buffer = io.BytesIO(); sheet.save(buffer,'JPEG',quality=20,optimize=True)
                out.write_bytes(buffer.getvalue())
                written.append(f'{out}: {sheet.width}x{sheet.height}, {buffer.tell()/1024:.1f} KB ({len(batch)} inputs)')
        print('\n'.join(written), file=sys.stderr if args.check_edges else sys.stdout)
        if args.check_edges: print(json.dumps(records,ensure_ascii=False,indent=2))
    except OSError as exc:
        print(f'Error writing sheet: {exc}',file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
