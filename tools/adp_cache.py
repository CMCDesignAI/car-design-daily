#!/usr/bin/env python3
"""Offline cache and browser-read quota for Automotive Design Planet columns."""
import argparse
import copy
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tarfile
import tempfile
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from PIL import Image, ImageOps

TAIPEI = ZoneInfo('Asia/Taipei')
REPO = Path('/workspace/car-design-daily').resolve()
DEFAULT = '/workspace/ai-digest/source_cache/adp'
SOURCE = 'Automotive Design Planet'


def read(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.tmp-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False, indent=1)
            f.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)


def day(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('date must be YYYY-MM-DD')
    return date.fromisoformat(value)


def today(): return datetime.now(TAIPEI).date()
def cache(root): return read(root / 'cache.json', {'entries': []})


def quota(root, d):
    start = d - timedelta(days=6)
    reads = [r for r in read(root / 'reads.json', {'reads': []})['reads'] if start <= day(r['date']) <= d]
    return {'date': d.isoformat(), 'window_start': start.isoformat(), 'limit': 2,
            'used': len(reads), 'remaining': max(0, 2-len(reads)), 'reads': reads}


def rank(e):
    return (float(e.get('craft') or 0), e.get('date') or '')


def image_convert(src, dest):
    with Image.open(src) as original:
        im = ImageOps.exif_transpose(original)
        if im.mode != 'RGB':
            if 'A' in im.getbands():
                background = Image.new('RGB', im.size, 'white')
                background.paste(im, mask=im.getchannel('A'))
                im = background
            else: im = im.convert('RGB')
        im.thumbnail((960, 960))
        for quality in (85, 80, 75, 70, 65, 60, 55, 50):
            buf = io.BytesIO()
            im.save(buf, format='JPEG', quality=quality, optimize=True)
            if buf.tell() < 300 * 1024:
                dest.parent.mkdir(parents=True, exist_ok=True)
                fd, name = tempfile.mkstemp(prefix='.tmp-', dir=dest.parent)
                try:
                    with os.fdopen(fd, 'wb') as f: f.write(buf.getvalue())
                    os.replace(name, dest)
                finally:
                    if os.path.exists(name): os.unlink(name)
                return
    raise ValueError('image cannot be reduced below 300 KB at quality 50')


def add(root, path):
    record = read(Path(path), None)
    if isinstance(record, list) and len(record) == 1: record = record[0]
    if not isinstance(record, dict): raise ValueError('input must be an object or one-item list')
    for key in ('id', 'url', 'full_text'):
        if not isinstance(record.get(key), str) or not record[key].strip(): raise ValueError(f'{key} is required')
    if not re.fullmatch(r'adp-[A-Za-z0-9_-]+', record['id']): raise ValueError('invalid ADP id')
    if record.get('date'): day(record['date'])
    paths = record.get('image_paths', [])
    metadata = record.get('images', [])
    if not isinstance(paths, list) or len(paths) > 3 or not all(isinstance(p, str) and p for p in paths): raise ValueError('image_paths must be a list of at most 3 paths')
    if not isinstance(metadata, list) or len(metadata) > 3 or not all(isinstance(m, dict) for m in metadata): raise ValueError('images must be a list of at most 3 objects')
    if 'craft' in record and record['craft'] is not None: float(record['craft'])
    data = cache(root)
    matches = [e for e in data['entries'] if e['id'] == record['id'] or e['url'] == record['url']]
    if len(matches) > 1: raise ValueError('id and url match different entries')
    entry = matches[0] if matches else None
    ident = entry['id'] if entry else record['id']
    images = copy.deepcopy(entry.get('images', [])) if entry else []
    for i, src in enumerate(paths):
        filename = f'img/{ident}' + (f'-{i+1}' if i else '') + '.jpg'
        image_convert(src, root / filename)
        m = metadata[i] if i < len(metadata) else {}
        old = images[i] if i < len(images) else {}
        item = {k: m.get(k, old.get(k, '')) for k in ('alt', 'credit', 'credit_url', 'src_url')}
        item['file'] = filename
        if i < len(images): images[i] = item
        else: images.append(item)
    fields = ('url', 'title_en', 'date', 'full_text', 'excerpt', 'design_tag', 'craft', 'qualified_note')
    if entry:
        entry.update({k: record[k] for k in fields if k in record})
    else:
        entry = {'id': ident, 'source': SOURCE, **{k: record.get(k, '') for k in fields},
                 'collected_at': datetime.now(TAIPEI).isoformat(), 'status': 'pending', 'used_date': None, 'reject_reason': None}
        data['entries'].append(entry)
    entry['images'] = images
    write(root / 'raw' / (ident + '.json'), record)
    write(root / 'cache.json', data)
    reads = read(root / 'reads.json', {'reads': []})
    if not any(r['id'] in (ident, record['id']) for r in reads['reads']):
        now = datetime.now(TAIPEI)
        if quota(root, now.date())['remaining'] == 0: print('warning: ADP browser read exceeds rolling quota', file=sys.stderr)
        reads['reads'].append({'date': now.date().isoformat(), 'id': ident, 'url': record['url'], 'counted_at': now.isoformat()})
        write(root / 'reads.json', reads)
    return {'updated' if matches else 'added': ident, 'id': ident, 'quota': quota(root, today()), 'images': len(images)}


def used_data(repo):
    return (read(repo / 'data/columns_queue.json', {'items': {}})['items'],
            read(repo / 'data/columns_log.json', {'used': {}})['used'])


def next_item(root, args):
    q = quota(root, day(args.date) if args.date else today())
    if not q['remaining']: return {'ok': False, 'reason': 'quota', 'quota': q, 'item': None}
    items = read(Path(args.queue), {'items': {}})['items']
    used = read(Path(args.log), {'used': {}})['used']
    entries = cache(root)['entries']
    eligible = [x for x in items.values() if x.get('source') == SOURCE and x.get('needs_browser') and not x.get('used') and not x.get('removed') and x['id'] not in used and not any(e['id'] == x['id'] or e['url'] == x.get('url') for e in entries)]
    eligible.sort(key=rank, reverse=True)
    keys = ('id', 'url', 'title_en', 'date', 'craft', 'design_tag', 'excerpt', 'kind', 'column')
    return {'ok': bool(eligible), **({} if eligible else {'reason': 'empty'}), 'quota': q, 'item': {k: eligible[0].get(k) for k in keys} if eligible else None}


def pick(root, args):
    day(args.date)
    queue, used = used_data(Path(args.repo))
    pending = [e for e in cache(root)['entries'] if e['status'] == 'pending']
    entries = [e for e in pending if e['id'] not in used and not queue.get(e['id'], {}).get('used')]
    entries.sort(key=rank, reverse=True)
    result = copy.deepcopy(entries)
    for e in result:
        for img in e.get('images', []):
            path = (root / img['file']).resolve()
            if root not in path.parents: raise ValueError('image path is outside cache')
            img['abs_path'] = str(path)
            if args.copy_images:
                dest = Path(args.copy_images).expanduser().resolve()
                if dest == root or root in dest.parents: raise ValueError('copy destination must be outside cache')
                dest.mkdir(parents=True, exist_ok=True)
                img['issue_file'] = path.name
                shutil.copyfile(path, dest / path.name)
    return {'date': args.date, 'picked': result, 'stats': {'pending': len(pending), 'qualified': len(entries)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dir')
    sub = parser.add_subparsers(dest='command', required=True)
    def cmd(name):
        p = sub.add_parser(name); p.add_argument('--dir', default=argparse.SUPPRESS); return p
    p = cmd('quota'); p.add_argument('--date')
    p = cmd('next'); p.add_argument('--date'); p.add_argument('--queue', default=str(REPO / 'data/columns_queue.json')); p.add_argument('--log', default=str(REPO / 'data/columns_log.json'))
    p = cmd('add'); p.add_argument('file')
    p = cmd('pick'); p.add_argument('--date', required=True); p.add_argument('--repo', default=str(REPO)); p.add_argument('--copy-images')
    p = cmd('mark-used'); p.add_argument('ids', nargs='+'); p.add_argument('--date', required=True)
    p = cmd('reject'); p.add_argument('ids', nargs='+'); p.add_argument('--reason', required=True)
    cmd('status')
    p = cmd('export'); p.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        root = Path(args.dir or os.environ.get('ADP_CACHE_DIR', DEFAULT)).expanduser().resolve()
        if root == REPO or REPO in root.parents: raise ValueError('cache directory must be outside the public repository')
        if args.command == 'quota': result = quota(root, day(args.date) if args.date else today())
        elif args.command == 'next': result = next_item(root, args)
        elif args.command == 'add': result = add(root, args.file)
        elif args.command == 'pick': result = pick(root, args)
        elif args.command in ('mark-used', 'reject'):
            data = cache(root); lookup = {e['id']: e for e in data['entries']}
            if any(i not in lookup for i in args.ids): raise ValueError('unknown id')
            if args.command == 'mark-used': day(args.date)
            if args.command == 'reject' and not args.reason.strip(): raise ValueError('reason is required')
            for i in args.ids:
                if args.command == 'mark-used': lookup[i].update(status='used', used_date=args.date, reject_reason=None)
                else: lookup[i].update(status='rejected', reject_reason=args.reason)
            write(root / 'cache.json', data); result = {'updated': args.ids}
        elif args.command == 'status':
            entries = cache(root)['entries']; q = quota(root, today())
            result = {'counts': {s: sum(e['status'] == s for e in entries) for s in ('pending', 'used', 'rejected')}, 'quota': q, 'pending': [{k: e.get(k) for k in ('id', 'title_en', 'craft', 'date')} for e in entries if e['status'] == 'pending'], 'last_collected_at': max((e['collected_at'] for e in entries), default=None), 'remaining': q['remaining']}
        else:
            out = Path(args.out).expanduser().resolve()
            if out == root or root in out.parents: raise ValueError('export destination must be outside cache')
            with tarfile.open(out, 'w:gz') as tar: tar.add(root, arcname=root.name)
            result = {'out': str(out)}
        print(json.dumps(result, ensure_ascii=False)); return 0
    except (ValueError, TypeError, OSError, KeyError) as exc:
        print(str(exc), file=sys.stderr); print(json.dumps({'error': str(exc)}, ensure_ascii=False)); return 1


if __name__ == '__main__': sys.exit(main())
