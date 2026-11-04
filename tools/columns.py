#!/usr/bin/env python3
"""Public design-column queue. Fetch, pick JSON writer stubs, commit usage, or status."""
import argparse
import collections
import datetime as dt
import email.utils
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
Q = ROOT / 'data/columns_queue.json'
LOG = ROOT / 'data/columns_log.json'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}
AD = 'Auto&Design'
KINDS = {'Meet the Designer': 'interview', 'Design Story': 'column', 'Concept': 'concept', 'Extra': 'analysis', 'News': 'news'}
FEEDS = {'': 'News', 'category/meet-the-designer-en-2': 'Meet the Designer', 'category/design-story-en': 'Design Story', 'category/newsstand': 'Design Story', 'category/concept-en': 'Concept', 'category/extra-en': 'Extra', 'category/news-en': 'News'}

def today(): return dt.datetime.now(ZoneInfo('Asia/Taipei')).date().isoformat()
def get(url):
    url = urllib.parse.quote(url, safe="%:/?&=+#@;,!$'()*[]")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15) as r:
        if r.status != 200: raise ValueError(f'HTTP {r.status}')
        return r.read()
def load(path, default):
    try: return json.loads(Path(path).read_text(encoding='utf-8'))
    except FileNotFoundError: return default

def save(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'); tmp.replace(path)

def text(value): return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', value or ''))).strip()
def migrate():
    if Q.exists(): return
    old = load(ROOT / 'data/autodesign_queue.json', {'items': {}})
    log = load(ROOT / 'data/autodesign_log.json', {'used': {}})
    used = {'ad-' + k.removeprefix('ad-'): v for k, v in log['used'].items()}
    items = {}
    for key, item in old['items'].items():
        x = dict(item); iid = 'ad-' + key.removeprefix('ad-')
        x.update(id=iid, source=AD, credit=AD, paywalled=False, kind=KINDS.get(x.get('column'), 'news'))
        x['used'] = x.get('used', False) or iid in used
        x['excerpt'] = text(x.get('excerpt'))[:600]; items[iid] = x
    save(Q, {'items': items})
    if not LOG.exists(): save(LOG, {'used': used})

class Page(HTMLParser):
    def __init__(self, raw):
        super().__init__(); self.meta = {}; self.links = []; self.scripts = []; self.script = None; self.feed(raw)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta': self.meta[a.get('property', a.get('name', ''))] = a.get('content', '')
        if tag == 'a' and a.get('href'): self.links.append(a['href'])
        if tag == 'script' and a.get('type') == 'application/ld+json': self.script = ''
    def handle_data(self, data):
        if self.script is not None: self.script += data
    def handle_endtag(self, tag):
        if tag == 'script' and self.script is not None:
            try: self.scripts.append(json.loads(self.script))
            except ValueError: pass
            self.script = None

class ArticleHTML(HTMLParser):
    """Collect visible paragraphs and images only within public article containers."""
    VOID = {'img', 'meta', 'link', 'br', 'hr', 'input', 'source', 'wbr', 'area', 'base', 'embed', 'param', 'track', 'col'}

    def __init__(self, raw, url):
        super().__init__(convert_charrefs=True)
        self.url = url; self.stack = []; self.paragraphs = []; self.images = []; self.p = None
        self.paywalled = False
        self.feed(raw); self.close()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        tokens = (a.get('class', '') + ' ' + a.get('id', '')).lower()
        active = (self.stack[-1][1] if self.stack else False) or tag in ('article', 'main') or 'entry-content' in tokens
        blocked = (self.stack[-1][2] if self.stack else False) or tag in ('nav', 'footer', 'header', 'script', 'style', 'noscript', 'aside', 'form') or bool(re.search(r'\b(?:paywall|subscription|related|social|share|advertisement|cookie|navigation)\b', tokens)) or 'hidden' in a or a.get('aria-hidden') == 'true' or bool(re.search(r'display\s*:\s*none', a.get('style', '')))
        if tag == 'meta' and a.get('itemprop') == 'isAccessibleForFree' and a.get('content', '').lower() == 'false': self.paywalled = True
        if active and not blocked:
            if tag == 'p': self.p = []
            if tag == 'img' or (tag == 'meta' and a.get('property') == 'og:image'):
                self.add_image(a)
        if tag not in self.VOID: self.stack.append((tag, active, blocked))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID: self.handle_endtag(tag)

    def add_image(self, a):
        for dim in ('width', 'height'):
            value = a.get(dim, '').strip().removesuffix('px')
            if value.isdigit() and int(value) < 200: return
        srcset = a.get('data-srcset') or a.get('srcset', '')
        candidates = [part.strip().split() for part in srcset.split(',') if part.strip()]
        src = (candidates[-1][0] if candidates else None) or a.get('data-src') or a.get('src') or a.get('content')
        if not src: return
        src = urllib.parse.urljoin(self.url, src)
        if urllib.parse.urlsplit(src).scheme not in ('http', 'https'): return
        if re.search(r'logo|icon|\.svg(?:[?#]|$)|tracking|pixel|spacer', src, re.I): return
        if src not in self.images: self.images.append(src)

    def handle_data(self, data):
        if self.p is not None and self.stack and self.stack[-1][1] and not self.stack[-1][2]: self.p.append(data)

    def handle_endtag(self, tag):
        if tag == 'p' and self.p is not None:
            value = re.sub(r'\s+', ' ', ''.join(self.p)).strip()
            if value: self.paragraphs.append(value)
            self.p = None
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]; break


def extract_article(raw, url):
    parsed = ArticleHTML(raw, url)
    metadata = Page(raw)
    paywalled = parsed.paywalled or any(v is False or str(v).lower() == 'false' for v in values(metadata.scripts, 'isAccessibleForFree'))
    return '\n\n'.join(parsed.paragraphs), parsed.images, paywalled


def values(obj, key):
    if isinstance(obj, dict):
        if key in obj: yield obj[key]
        for v in obj.values(): yield from values(v, key)
    elif isinstance(obj, list):
        for v in obj: yield from values(v, key)

def page(url): return Page(get(url).decode('utf-8', 'replace'))
def iso(value):
    if not value: return None
    if re.match(r'^\d{4}-\d{2}-\d{2}', str(value)): return str(value)[:10]
    return email.utils.parsedate_to_datetime(value).date().isoformat()
def item(source, prefix, url, title, date, kind, column, excerpt='', image=None, paywalled=False):
    slug = urllib.parse.urlsplit(url).path.rstrip('/').split('/')[-1]
    return dict(id=prefix + slug, source=source, credit=source, paywalled=paywalled, kind=kind, column=column,
                title_en=text(title), date=date, url=url, image=image, excerpt=text(excerpt)[:600], added=today(), used=False)

def disegno_keep(value):
    if re.search(r'car|automotive|vehicle|mobility|jaguar|transport|bmw|porsche|ferrari|volvo|polestar|renault', value, re.I): return True
    return bool(re.search(r'design studio', value, re.I) and re.search(r'mercedes|audi|bentley|rolls.royce|ford|lincoln|toyota|lexus|honda|acura|nissan|infiniti|mazda|hyundai|kia|genesis|peugeot|citro[eë]n|fiat|alfa romeo|lamborghini|maserati|aston martin|mclaren|lotus|tesla|buick|cadillac|chevrolet|gmc|rivian|lucid|volkswagen|skoda|seat|cupra|bugatti|suzuki|subaru|mitsubishi|land rover|range rover', value, re.I))

def rss(url, source, prefix, label=None):
    root = ET.fromstring(get(url))
    for it in root.findall('./channel/item'):
        link = (it.findtext('link') or '').strip()
        title = text(it.findtext('title')); cats = [text(c.text) for c in it.findall('category')]
        body = it.findtext('{http://purl.org/rss/1.0/modules/content/}encoded') or it.findtext('description') or ''
        excerpt = text(body)[:600]; col = label or 'News'; kind = 'news'
        if source == AD:
            if title.upper().startswith('MEET THE DESIGNER'): col = 'Meet the Designer'
            elif col == 'News':
                for name in KINDS:
                    if name.upper() in [c.upper() for c in cats]: col = name; break
            kind = KINDS[col]
        elif source in ('Car Design TV', 'The Autopian', 'Wallpaper*', 'Disegno'):
            if source == 'Car Design TV':
                parts = urllib.parse.urlsplit(link)
                link = urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode([(k,v) for k,v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True) if not k.lower().startswith('utm_')])))
                kind = 'concept' if re.search(r'concept|vision', title, re.I) else 'analysis'
            else: kind = 'analysis'
            if source == 'The Autopian' and re.search(r'bicycle|tandem|car show', title, re.I): continue
            if source == 'Wallpaper*' and re.search(r'yacht|boat|bike|watch|review', title+' '+link, re.I): continue
            if source == 'Disegno' and not disegno_keep(title+' '+text(it.findtext('description'))+' '+link): continue
        elif source == 'Dezeen':
            kind = 'interview' if re.search(r'\binterview\b|["“][^"”]{8,}["”]\s*(?:says|said|explains|according)', title+' '+excerpt, re.I) else ('concept' if 'concept' in (title+' '+excerpt).lower() else 'news')
            col = kind.title()
        else:
            design = re.search(r'sketch|design|making', title, re.I)
            if 'Production Cars' in cats and not design: continue
            kind = 'making_of' if design else ('concept' if 'Concept Cars' in cats else 'news')
            col = 'Making-of' if kind == 'making_of' else kind.title()
        image = re.search(r'<img[^>]+src=[\'"]([^\'"]+)', body)
        yield item(source, prefix, link, title, iso(it.findtext('pubDate')), kind, col, excerpt, html.unescape(image[1]) if image else None)

MF = 'CAR STYLING / Motor-Fan'
HD = 'Honda Design'

def core77_title(title): return re.sub(r'\s+- Core77$', '', title).strip()
def core77_keep(title):
    return bool(re.search(r'car|auto|vehicle|\bEV\b|concept|dashboard|cockpit|seat|truck|SUV|pillar|aerodynamic|design', title, re.I)) and not re.search(r'bicycle|\bbike\b|lamp|desk', title, re.I)

def public_article(source, prefix, url):
    p = page(url); title = p.meta.get('og:title', '')
    date = iso(next(values(p.scripts, 'datePublished'), None) or p.meta.get('article:published_time') or p.meta.get('datePublished') or p.meta.get('date'))
    if source == MF:
        title = title.removesuffix(' | Motor Fan｜自動車情報のモーターファン')
        kind = 'concept' if 'コンセプト' in title else ('interview' if re.search(r'インタビュー|語る|デザイナー', title) else ('analysis' if re.search(r'スタイリング|インテリア|CMF|デザイン|解説|編', title) else 'news'))
        column = 'CAR STYLING'
    else:
        if not date:
            match = re.search(r'(?<!\d)(20\d{2})(0[1-9]|1[0-2])', urllib.parse.urlsplit(url).path)
            if match: date = f'{match[1]}-{match[2]}-01'
        kind = 'interview'; column = 'Honda Design Interview'
    x = item(source, prefix, url, title, date, kind, column, p.meta.get('og:description', ''), p.meta.get('og:image'))
    if source == MF: x['language'] = 'ja'
    return x


def fetch(days):
    migrate(); q = load(Q, {'items': {}}); cut = (dt.date.fromisoformat(today()) - dt.timedelta(days=days)).isoformat(); count = 0
    for x in q['items'].values():
        if x['source'] == 'Core77':
            x['title_en'] = core77_title(x['title_en'])
            if not core77_keep(x['title_en']): x['removed'] = True
    def add(x):
        nonlocal count
        if not x['date'] or x['date'] < cut or (x['kind'] == 'news' and x['source'] != AD): return
        old = q['items'].get(x['id'])
        if old:
            if x['source'] == AD and list(KINDS).index(x['column']) < list(KINDS).index(old['column']): old.update(column=x['column'], kind=x['kind'])
        else: q['items'][x['id']] = x; count += 1
    jobs = [(AD, f'https://autodesignmagazine.com/en/{path+"/" if path else ""}feed/', 'ad-', col) for path,col in FEEDS.items()]
    jobs += [('Dezeen','https://www.dezeen.com/tag/cars/feed/','dz-',None), ('Car Body Design','https://www.carbodydesign.com/feed/','cbd-',None)]
    jobs += [('Car Design TV', 'https://www.cardesigntv.com/feed/', 'cdtv-', 'Design Analysis'),
             ('The Autopian', 'https://www.theautopian.com/category/damn-good-design/feed/', 'ap-', 'Damn Good Design (Adrian Clarke)'),
             ('Wallpaper*', 'https://www.wallpaper.com/feeds/tag/transportation', 'wp-', 'Transportation'),
             ('Disegno', 'https://disegnojournal.com/newsfeed?format=rss', 'dg-', 'Disegno')]
    for source, url, prefix, label in jobs:
        for p in range(1, 6 if source == AD else 2):
            try:
                batch = list(rss(url + (f'?paged={p}' if p > 1 else ''), source, prefix, label))
                for x in batch: add(x)
                if not batch or min(x['date'] for x in batch if x['date']) < cut or len(batch) < 10: break
            except Exception as e: print(f'{source}: {e}', file=sys.stderr); break
    for source, base, pattern, prefix, limit in [
        ('Car Design News','https://www.cardesignnews.com/',r'/(?:cars|cmf|designers|interiors|lighting|ux)/[^/?#]+/\d+/?$', 'cdn-',25),
        ('Core77','https://www.core77.com/transportation',r'/posts/\d+/[^/?#]+/?$', 'c77-',25)]:
        try: links = list(dict.fromkeys(urllib.parse.urljoin(base, urllib.parse.urlsplit(u).path) for u in page(base).links if re.search(pattern, urllib.parse.urlsplit(u).path) and urllib.parse.urlsplit(urllib.parse.urljoin(base,u)).netloc == urllib.parse.urlsplit(base).netloc))
        except Exception as e: print(f'{source}: {e}', file=sys.stderr); continue
        new = 0
        for url in links:
            if any(x['url'].rstrip('/') == url.rstrip('/') for x in q['items'].values()): continue
            if new >= limit: break
            new += 1
            try:
                p = page(url); title = p.meta.get('og:title',''); slug = urllib.parse.urlsplit(url).path
                if source == 'Car Design News' and re.search(r'joins|appointed|to-lead|retires|passed-away', slug+' '+title, re.I): continue
                if source == 'Core77':
                    title = core77_title(title)
                    if not core77_keep(title): continue
                date = iso(next(values(p.scripts,'datePublished'), None) or p.meta.get('article:published_time'))
                if not date and source != 'Core77': continue
                kind = 'interview' if source == 'Car Design News' and re.search(r'/designers/|on-|vp-|head-of-design|talks', slug+' '+title, re.I) else 'analysis'
                free = next(values(p.scripts,'isAccessibleForFree'), True)
                add(item(source,prefix,url,title,date or today(),kind,kind.title(),p.meta.get('og:description') or p.meta.get('description',''),p.meta.get('og:image'),free is False or str(free).lower() == 'false'))
            except Exception as e: print(f'{source} {url}: {e}', file=sys.stderr)
    for source, base, pattern, prefix, limit in [
        (MF, 'https://motor-fan.jp/publisher/carstyling-jp/', r'^/article/\d+/?$', 'mf-', 15),
        (HD, 'https://global.honda/jp/design/', r'/design/interview/', 'hd-', None)]:
        try:
            links = list(dict.fromkeys(urllib.parse.urljoin(base, urllib.parse.urlsplit(u).path) for u in page(base).links if re.search(pattern, urllib.parse.urlsplit(u).path) and urllib.parse.urlsplit(urllib.parse.urljoin(base,u)).netloc == urllib.parse.urlsplit(base).netloc))
        except Exception as e: print(f'{source}: {e}', file=sys.stderr); continue
        new = [url for url in links if not any(x['url'].rstrip('/') == url.rstrip('/') for x in q['items'].values())]
        for url in new[:limit]:
            try: add(public_article(source, prefix, url))
            except Exception as e: print(f'{source} {url}: {e}', file=sys.stderr)
    save(Q,q); return count

def expired(x,date):
    # zley: back-issue sample cards only while the issue is within 12 months of release.
    if x.get('kind')!='issue_sample' or not x.get('back_issue') or not x.get('release_date'): return False
    d=dt.date.fromisoformat(date); r=dt.date.fromisoformat(x['release_date'][:10])
    try: cutoff=d.replace(year=d.year-1)
    except ValueError: cutoff=d.replace(year=d.year-1,day=28)
    return r<cutoff

def tier(x):
    s,k=x['source'],x['kind']
    if s == 'Car Design News': return 98
    if k == 'issue_sample': return 0 if not x.get('back_issue') else 3
    return {
        (AD, 'interview'): 1, (AD, 'column'): 1,
        (MF, 'analysis'): 2,
        (MF, 'interview'): 2, (HD, 'interview'): 2,
        (AD, 'concept'): 4, (AD, 'analysis'): 4,
        ('The Autopian', 'analysis'): 3, ('Car Design TV', 'analysis'): 3,
        ('Car Body Design', 'making_of'): 5, ('Car Body Design', 'concept'): 5,
        ('Car Design TV', 'concept'): 5, (MF, 'concept'): 5,
        ('Dezeen', 'interview'): 6, ('Dezeen', 'concept'): 6,
        ('Wallpaper*', 'analysis'): 6, ('Disegno', 'analysis'): 6,
        (AD, 'news'): 7, ('Core77', 'analysis'): 8,
    }.get((s,k),99)


def select(items, used, date, n=None, exclude=''):
    ex = [s.strip().lower() for s in (exclude or '').split(',') if s.strip()]
    pool = [x for x in items if not x.get('removed') and not x.get('used') and x['id'] not in used and x['date'] <= date and not any(k in (x['title_en']+' '+x.get('excerpt','')).lower() for k in ex) and (x['kind'] != 'issue_sample' or x.get('due',x['date']) <= date) and tier(x)<99 and not expired(x,date)]
    if n is None:
        start = (dt.date.fromisoformat(date)-dt.timedelta(days=7)).isoformat()
        fresh = [x for x in pool if start <= x['date'] <= date]
        batches = collections.Counter(x['date'] for x in fresh if x['source']==AD and x['column']=='Design Story')
        n = 2 if any((x['source']==AD and x['column']=='Meet the Designer') for x in fresh) or any(v>=3 for v in batches.values()) or any(x['kind']=='issue_sample' and x.get('due')==date for x in pool) else 1
    sample_used = any(x['kind']=='issue_sample' and used.get(x['id'])==date for x in items)
    if sample_used: pool = [x for x in pool if x['kind'] != 'issue_sample']
    pool.sort(key=lambda x:(tier(x),x.get('due',x['date']),x['id']))
    result = []
    ad_used = any(used.get(x['id'])==date and x['source']==AD for x in items)
    for x in pool:
        if len(result)>=n: break
        if x['kind']=='issue_sample':
            if sample_used: continue
            sample_used=True
        if x['source']=='Core77' and any(y['source']!='Core77' for y in pool): continue
        # zley pacing: Auto&Design (issue samples + web columns combined) max 1 card per day.
        if x['source']==AD:
            if ad_used: continue
            ad_used=True
        result.append(x)
    return result

def pick(date,n,exclude,imgdir,dry_run=False):
    migrate(); q=load(Q,{'items':{}}); used=load(LOG,{'used':{}})['used']; out=[]
    candidates=list(q['items'].values())
    target=n if n is not None else len(select(candidates,used,date,None,exclude))
    # Re-select after rejection so a short teaser never consumes a daily slot.
    while len(out) < target:
        batch=select(candidates,used,date,1,exclude)
        if not batch: break
        x=batch[0]; candidates=[y for y in candidates if y['id'] != x['id']]
        body=''; images=[]; reason=None
        if x.get('paywalled') or x['source']=='Car Design News':
            x['paywalled']=True; reason='paywalled'
        elif x['kind']=='issue_sample':
            body=x.get('notes',''); 
            if not (x.get('crops') or x.get('crop1')): reason='no_crops'
            elif len(body)<200: reason='no_notes'
        else:
            try:
                body,images,paywalled=extract_article(get(x['url']).decode('utf-8','replace'),x['url'])
                if paywalled: x['paywalled']=True; reason='paywalled'
                elif len(body)<800: reason='body_too_short'
            except Exception as e:
                reason='fetch_failed'
                print(f"article {x['id']}: {e}",file=sys.stderr)
        if reason:
            x['skipped_reason']=reason
            continue
        x.pop('skipped_reason',None)
        if x['source']==AD: candidates=[y for y in candidates if y['source']!=AD]
        o={k:x.get(k) for k in ('id','source','credit','kind','column','date','url','paywalled','excerpt')}
        o.update(orig=x['title_en'],title='',summary='',body=body[:12000],images=images,image=None,image2=None,more_images=[])
        if x['kind']=='issue_sample':
            o.update({k:x.get(k) for k in ('issue_no','part','sample_pages','section','language')})
            candidates=[y for y in candidates if y['kind']!='issue_sample']
        if imgdir:
            Path(imgdir).mkdir(parents=True,exist_ok=True)
            sources=(x.get('crops') or [x.get('crop1'),x.get('crop2')]) if x['kind']=='issue_sample' else images
            downloaded=[]
            for src in sources:
                if not src: continue
                if len(downloaded)>=3: break
                try:
                    if x['kind']=='issue_sample':
                        ext=Path(src).suffix; data=Path(src).read_bytes(); credit=f"Auto&Design No.{x['issue_no']}, via OverDrive sample"; credit_url=x['overdrive_url']
                    else:
                        ext=Path(urllib.parse.urlsplit(src).path).suffix.lower(); data=get(src); credit=x['credit']; credit_url=x['url']
                    if ext.lower() not in ('.jpg','.jpeg','.png','.webp','.gif'): ext='.jpg'
                    slot=len(downloaded)+1
                    name=x['id'][:50]+(f'-{slot}' if slot>1 else '')+ext
                    (Path(imgdir)/name).write_bytes(data)
                    downloaded.append(dict(file=name,alt=x['title_en'],credit=credit,credit_url=credit_url))
                except Exception as e: print(f"image {x['id']}: {e}",file=sys.stderr)
            if downloaded: o['image']=downloaded[0]
            if len(downloaded)>1: o['image2']=downloaded[1]
            o['more_images']=downloaded[2:]
        out.append(o)
    if not dry_run: save(Q,q)
    for o in out:
        if not re.fullmatch(r"[\x00-\u024f’‘“”–—…· ]*", o.get('orig') or ''):
            print(f"NOTE {o['id']}: orig title is not English; build.py hides it (add orig_title_zh only for a needed term with 中文註解). Write title/summary in 繁中, no kana.", file=sys.stderr)
    print(json.dumps(out,ensure_ascii=False,indent=2))

def commit(date,ids):
    migrate(); q=load(Q,{'items':{}}); log=load(LOG,{'used':{}})
    for iid in ids:
        matches=[k for k in q['items'] if k==iid or k[:53]==iid or ('ad-'+k.removeprefix('ad-')[:50])==iid]
        if len(matches)!=1: raise ValueError(f'Unknown or ambiguous id: {iid}')
        key=matches[0]; log['used'][key]=date; q['items'][key]['used']=True
    save(LOG,log); save(Q,q); print('logged',ids)

def status():
    migrate(); q=load(Q,{'items':{}}); used=load(LOG,{'used':{}})['used']
    left=[x for x in q['items'].values() if not x.get('removed') and not x.get('used') and x['id'] not in used]
    print(json.dumps(dict(unused=len(left),by_source=dict(collections.Counter(x['source'] for x in left)),by_kind=dict(collections.Counter(x['kind'] for x in left)),used=len(used),weeks_at_1_per_day=round(len(left)/7,1)),ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('cmd',choices=['fetch','pick','commit','status']); ap.add_argument('--date'); ap.add_argument('--days',type=int,default=14); ap.add_argument('--n',type=int); ap.add_argument('--exclude',default=''); ap.add_argument('--img-dir'); ap.add_argument('--ids',default='')
    ap.add_argument('--dry-run',action='store_true',help='do not persist queue changes (pick still fetches public HTML)')
    a=ap.parse_args()
    if a.cmd in ('pick','commit'):
        if not a.date: ap.error('--date is required')
        dt.date.fromisoformat(a.date)
    if a.cmd == 'commit' and not a.ids.strip(): ap.error('--ids is required')
    if a.n is not None and a.n<1: ap.error('--n must be positive')
    if a.cmd=='fetch': print('new',fetch(a.days)); status()
    elif a.cmd=='pick': pick(a.date,a.n,a.exclude,a.img_dir,a.dry_run)
    elif a.cmd=='commit': commit(a.date,[x.strip() for x in a.ids.split(',') if x.strip()])
    else: status()

if __name__=='__main__': main()
