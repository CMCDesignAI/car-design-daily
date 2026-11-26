#!/usr/bin/env python3
"""Offline candidate cache for AI digest columns."""
import argparse
import copy
import hashlib
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
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

TAIPEI = ZoneInfo('Asia/Taipei')
DEFAULT_DIR = '/workspace/ai-digest/column_cache'
REPO_ROOT = Path('/workspace/car-design-daily').resolve()


def parse_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('date must be YYYY-MM-DD')
    return date.fromisoformat(value)


def today():
    return datetime.now(TAIPEI).date()


def read_json(path):
    with path.open(encoding='utf-8') as f:
        return json.load(f)


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.tmp-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
            f.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def cache_dir(args):
    path = Path(args.dir or os.environ.get('COLUMN_CACHE_DIR', DEFAULT_DIR)).expanduser().resolve()
    if path == REPO_ROOT or REPO_ROOT in path.parents:
        raise ValueError('cache directory must be outside the public repository')
    return path


def load_cache(root):
    path = root / 'cache.json'
    data = read_json(path) if path.exists() else {'entries': []}
    if not isinstance(data, dict) or not isinstance(data.get('entries'), list):
        raise ValueError('invalid cache.json: expected an entries list')
    return data


def safe_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise ValueError('id and creator_key must contain only letters, digits, underscores or hyphens')
    return value


def derive_id(record):
    url = record['permalink']
    parsed = urlparse(url)
    match = re.search(r'pfbid[A-Za-z0-9]+', url)
    video = parse_qs(parsed.query).get('v', [None])[0]
    if not video and (parsed.hostname or '').lower() in ('youtu.be', 'www.youtu.be'):
        video = parsed.path.strip('/').split('/')[0]
    if not video:
        video_match = re.search(r'/(?:videos?|shorts|embed)/([A-Za-z0-9_-]+)', parsed.path)
        video = video_match.group(1) if video_match else None
    slug = (match.group(0) if match else video or hashlib.sha1(url.encode()).hexdigest())[-8:]
    return safe_id('col-' + safe_id(record['creator_key']) + '-' + slug)


def convert_image(source, target):
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise ValueError('Pillow is required for image conversion') from exc
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original)
        image.thumbnail((1600, 1600))
        for quality in range(82, 49, -4):
            buffer = io.BytesIO()
            image.save(buffer, format='WEBP', quality=quality, method=6)
            if buffer.tell() < 300 * 1024:
                target.parent.mkdir(parents=True, exist_ok=True)
                fd, name = tempfile.mkstemp(prefix='.tmp-', dir=target.parent)
                try:
                    with os.fdopen(fd, 'wb') as f:
                        f.write(buffer.getvalue())
                    os.replace(name, target)
                finally:
                    if os.path.exists(name):
                        os.unlink(name)
                return
    raise ValueError('image cannot be reduced below 300 KB at quality 50')


def add(args, root):
    records = read_json(Path(args.file))
    if isinstance(records, dict):
        records = [records]
    if not isinstance(records, list):
        raise ValueError('input must be an object or a list of objects')
    data = load_cache(root)
    result = {'added': [], 'updated': [], 'errors': []}
    for index, record in enumerate(records):
        try:
            if not isinstance(record, dict):
                raise ValueError('record must be an object')
            for field in ('creator_key', 'platform', 'permalink', 'date', 'full_text', 'source'):
                if not isinstance(record.get(field), str) or not record[field].strip():
                    raise ValueError(f'{field} is required')
            safe_id(record['creator_key'])
            if parse_date(record['date']) > today():
                raise ValueError('post date is in the future')
            existing = next ( (e for e in data['entries'] if e['permalink'] == record['permalink']), None)
            ident = existing['id'] if existing else safe_id(record.get('id') or derive_id(record))
            if not existing and any(e['id'] == ident for e in data['entries']):
                raise ValueError(f'id already exists: {ident}')
            supplied_image = record.get('image')
            if supplied_image is not None and not isinstance(supplied_image, dict):
                raise ValueError('image must be an object or null')
            image = copy.deepcopy(existing.get('image')) if existing else None
            if record.get('image_path'):
                metadata = supplied_image or {}
                image = {key: metadata.get(key, '') for key in ('alt', 'credit', 'credit_url', 'src_url')}
                image['credit'] = image['credit'] or f"{record['platform']} 貼文附圖"
                image['file'] = f'img/{ident}.webp'
                convert_image(record['image_path'], root / image['file'])
            fields = {key: record.get(key, '') for key in ('source', 'creator_key', 'platform', 'permalink', 'date', 'orig', 'full_text', 'topic_hint', 'qualified_note')}
            if existing:
                # Omitted optional fields retain previously collected information.
                fields = {k: v for k, v in fields.items() if k in record}
                before = copy.deepcopy(existing)
                existing.update(fields)
                existing['image'] = image
                state = 'updated' if existing != before or record.get('image_path') else 'skipped'
            else:
                existing = {'id': ident, **fields, 'image': image,
                            'collected_at': datetime.now(TAIPEI).isoformat(),
                            'status': 'pending', 'used_date': None, 'reject_reason': None}
                data['entries'].append(existing)
                state = 'added'
            write_json(root / 'raw' / (ident + '.json'), record)
            if state != 'skipped':
                result[state].append(ident)
            else:
                result.setdefault('skipped', []).append(ident)
        except (ValueError, TypeError, OSError) as exc:
            result['errors'].append({'index': index, 'error': str(exc)})
    if result['added'] or result['updated']:
        write_json(root / 'cache.json', data)
    return result, bool(result['errors'])


def history(repo, issue_date):
    rows = []
    log = repo / 'ai-columns-log.json'
    if log.exists():
        entries = read_json(log)
        if not isinstance(entries, list):
            raise ValueError('ai-columns-log.json must contain a list')
        rows.extend(entries)
    for path in (repo / 'ai' / 'issues').glob('*/data.json'):
        try:
            d = parse_date(path.parent.name)
        except ValueError:
            continue
        if issue_date - timedelta(days=30) <= d < issue_date:
            issue = read_json(path)
            rows.extend({**col, 'date': path.parent.name} for col in issue.get('columns', []))
    urls, keys = set(), set()
    for row in rows:
        try:
            d = parse_date(row.get('date'))
        except (ValueError, TypeError):
            continue
        if issue_date - timedelta(days=30) <= d < issue_date:
            if row.get('url'):
                urls.add(row['url'])
            if row.get('key') or row.get('id'):
                keys.add(row.get('key') or row['id'])
    return urls, keys


def pick(args, root):
    issue_date = parse_date(args.date)
    if args.window < 0 or args.max < 0 or args.per_creator < 0:
        raise ValueError('window and limits must be non-negative')
    entries = load_cache(root)['entries']
    urls, keys = history(Path(args.repo), issue_date)
    pending = [e for e in entries if e['status'] == 'pending']
    eligible, excluded, expired = [], [], []
    for e in pending:
        post = parse_date(e['date'])
        if post < issue_date - timedelta(days=args.window):
            expired.append(e['id'])
        elif post > issue_date:
            excluded.append({'id': e['id'], 'reason': 'post date is after issue date'})
        elif e['permalink'] in urls:
            excluded.append({'id': e['id'], 'reason': 'url used within 30 days'})
        elif e['id'] in keys:
            excluded.append({'id': e['id'], 'reason': 'key used within 30 days'})
        else:
            eligible.append(e)
    eligible.sort(key=lambda e: e['date'], reverse=True)
    picked, counts = [], {}
    for e in eligible:
        if counts.get(e['creator_key'], 0) >= args.per_creator:
            excluded.append({'id': e['id'], 'reason': 'per-creator limit'})
        elif len(picked) >= args.max:
            excluded.append({'id': e['id'], 'reason': 'maximum limit'})
        else:
            item = copy.deepcopy(e)
            if item.get('image'):
                image_path = (root / item['image']['file']).resolve()
                if root not in image_path.parents:
                    raise ValueError('image path is outside cache')
                item['image']['abs_path'] = str(image_path)
                if args.copy_images:
                    dest = Path(args.copy_images).expanduser().resolve()
                    if dest == root or root in dest.parents:
                        raise ValueError('image copy destination must be outside the cache directory')
                    dest.mkdir(parents=True, exist_ok=True)
                    filename = safe_id(item['id']) + '.webp'
                    shutil.copyfile(image_path, dest / filename)
                    item['image']['issue_file'] = filename
            picked.append(item)
            counts[e['creator_key']] = counts.get(e['creator_key'], 0) + 1
    return {'date': args.date, 'picked': picked, 'excluded': excluded, 'expired_pending': expired,
            'stats': {'pending': len(pending), 'qualified': len(eligible)}}, False


def change_status(args, root):
    data = load_cache(root)
    lookup = {e['id']: e for e in data['entries']}
    missing = [ident for ident in args.ids if ident not in lookup]
    if missing:
        raise ValueError('unknown id(s): ' + ', '.join(missing))
    if args.command == 'mark-used':
        parse_date(args.date)
    for ident in args.ids:
        entry = lookup[ident]
        if args.command == 'mark-used':
            entry.update(status='used', used_date=args.date, reject_reason=None)
        else:
            entry.update(status='rejected', reject_reason=args.reason)
    write_json(root / 'cache.json', data)
    return {'updated': args.ids}, False


def status(args, root):
    entries = [e for e in load_cache(root)['entries'] if (not args.source or e['source'] == args.source) and (not args.creator or e['creator_key'] == args.creator)]
    counts = {s: sum(e['status'] == s for e in entries) for s in ('pending', 'used', 'rejected')}
    grouped = {}
    for e in entries:
        key = (e['source'], e['creator_key'])
        group = grouped.setdefault(key, {'source': key[0], 'creator_key': key[1], 'last_collected_at': e['collected_at']})
        group['last_collected_at'] = max(group['last_collected_at'], e['collected_at'])
    newest = max((parse_date(e['date']) for e in entries), default=None)
    pending = [{'id': e['id'], 'date': e['date'], 'topic_hint': e.get('topic_hint', ''), 'age_days': (today() - parse_date(e['date'])).days} for e in entries if e['status'] == 'pending']
    return {'counts': counts, 'newest_post_date': newest.isoformat() if newest else None,
            'last_collected': list(grouped.values()), 'pending': pending,
            'suggested_since': ((newest - timedelta(days=1)) if newest else (today() - timedelta(days=5))).isoformat()}, False


class JsonParser(argparse.ArgumentParser):
    def error(self, message):
        print(message, file=sys.stderr)
        print(json.dumps({'error': message}, ensure_ascii=False))
        self.exit(2)


def main():
    parser = JsonParser(description=__doc__)
    parser.add_argument('--dir', help='cache directory')
    sub = parser.add_subparsers(dest='command', required=True)
    def command(name):
        p = sub.add_parser(name)
        p.add_argument('--dir', default=argparse.SUPPRESS, help='cache directory')
        return p
    p = command('add'); p.add_argument('file')
    p = command('pick'); p.add_argument('--date', required=True); p.add_argument('--window', type=int, default=7); p.add_argument('--max', type=int, default=6); p.add_argument('--per-creator', type=int, default=2); p.add_argument('--repo', default=str(REPO_ROOT)); p.add_argument('--copy-images')
    p = command('mark-used'); p.add_argument('ids', nargs='+'); p.add_argument('--date', required=True)
    p = command('reject'); p.add_argument('ids', nargs='+'); p.add_argument('--reason', required=True)
    p = command('status'); p.add_argument('--source'); p.add_argument('--creator')
    p = command('export'); p.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        root = cache_dir(args)
        if args.command == 'add':
            result, error = add(args, root)
        elif args.command == 'pick':
            result, error = pick(args, root)
        elif args.command in ('mark-used', 'reject'):
            result, error = change_status(args, root)
        elif args.command == 'status':
            result, error = status(args, root)
        else:
            out = Path(args.out).expanduser().resolve()
            if out == root or root in out.parents:
                raise ValueError('export destination must be outside the cache directory')
            if not root.is_dir():
                raise ValueError('cache directory does not exist')
            with tarfile.open(out, 'w:gz') as tar:
                tar.add(root, arcname=root.name)
            result, error = {'out': str(out)}, False
        if error:
            for item in result.get('errors', []):
                print(f"record {item['index']}: {item['error']}", file=sys.stderr)
        print(json.dumps(result, ensure_ascii=False))
        return int(error)
    except (ValueError, TypeError, OSError, json.JSONDecodeError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        print(json.dumps({'error': str(exc)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
