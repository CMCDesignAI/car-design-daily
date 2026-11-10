#!/usr/bin/env python3
"""Digest static article HTML without executing JavaScript or logging in."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode

from bs4 import BeautifulSoup

UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36'
JUNK = re.compile(r'(?:^|[-_\s])(?:ads?|advert\w*|cookie\w*|related\w*|share\w*|social|sidebar|newsletter|comments?|navigation|menu)(?:$|[-_\s])', re.I)
IMAGE = re.compile(r'\.(?:jpe?g|png|webp|avif|gif)(?:[?#]|$)', re.I)
SKIP = re.compile(r'(?:^|[/_.-])(?:logos?|avatars?|sprites?|icons?|emoji|tracking|pixel|share|facebook|twitter|pinterest|google_preferred_source_badge)(?:[/_.-]|$)', re.I)


CONTENT = '.entry-content, .post-content, .article-content, .td-post-content, .elementor-widget-theme-post-content'


def compact(text):
    return ' '.join(text.split())


def walk(value):
    yield value
    if isinstance(value, dict):
        for child in value.values(): yield from walk(child)
    elif isinstance(value, list):
        for child in value: yield from walk(child)


def digest(raw, source, limit):
    soup = BeautifulSoup(raw, 'lxml')
    base = source if source.startswith(('http://','https://')) else Path(source).resolve().as_uri()
    if soup.base and soup.base.get('href'): base = urljoin(base, soup.base['href'])
    title = compact(soup.title.get_text(' ',strip=True)) if soup.title else ''
    if not title:
        tag = soup.find('meta', property='og:title')
        title = tag.get('content','') if tag else ''
    date = None
    for tag in soup.find_all('meta'):
        key = (tag.get('property') or tag.get('name') or tag.get('itemprop') or '').lower()
        if key in ('article:published_time','datepublished','parsely-pub-date','og:published_time','og:datepublished','og:date','date','pubdate','publishdate'):
            date = tag.get('content') or None
            if date: break
    blobs = []
    for script in soup.find_all('script'):
        try: obj = json.loads(script.string or script.get_text())
        except (ValueError, TypeError): continue
        blobs.append(obj)
        if not date:
            for value in walk(obj):
                if isinstance(value,dict):
                    found = value.get('datePublished') or value.get('dateCreated')
                    if isinstance(found,str): date = found; break
    facebook = []
    for a in soup.find_all('a',href=True):
        link = urljoin(base,a['href'])
        parts = urlsplit(link)
        if ((parts.hostname or '').lower() == 'facebook.com' or (parts.hostname or '').lower().endswith('.facebook.com')) and (re.search(r'/posts/pfbid[^/?#]+',parts.path) or any(k in ('story_fbid','pfbid') for k,v in parse_qsl(parts.query))):
            if link not in facebook: facebook.append(link)
    # Expand noscript before selecting/removing layout; lxml may already parse its children.
    for tag in list(soup.find_all('noscript')):
        if not tag.find('img'):
            tag.replace_with(BeautifulSoup(tag.get_text(), 'lxml'))
    for tag in list(soup.find_all(['nav','footer','header','aside','form','script','style','iframe','button','template'])):
        tag.decompose()
    for tag in list(soup.find_all(True)):
        if tag.attrs is None: continue
        # Theme layout classes such as has-sidebar / fusion-main-menu also
        # occur on body and wrappers around the entire public article.
        if tag.name in ('html','body','article','main') or tag.select_one('article, main, '+CONTENT):
            continue
        identity = str(tag.get('id',''))+' '+' '.join(tag.get('class',[]))
        if JUNK.search(identity) or tag.get('role') in ('navigation','banner','contentinfo'):
            tag.decompose()
    def score(tag):
        text = compact(tag.get_text(' ',strip=True))
        links = sum(len(a.get_text(' ',strip=True)) for a in tag.find_all('a'))
        return len(text)-links*.7
    # Prefer the prose container over the enclosing article, which may also
    # contain a headline, slideshow controls, breadcrumbs or related stories.
    candidates = soup.select(CONTENT) or soup.select('article') or soup.select('main, [role="main"]')
    if not candidates: candidates = soup.find_all(['section','div','body'])
    root = max(candidates,key=score) if candidates else soup
    text = compact(root.get_text(' ',strip=True))
    # Include the article's featured photo outside post-content, but keep
    # unrelated widgets outside the article out of the image scan.
    image_root = root.find_parent('article') or root
    images = []
    def add_image(value):
        if not isinstance(value,str): return
        value = value.strip().replace('\\/','/')
        if not value or value.startswith(('data:','blob:')): return
        url = urljoin(base,value)
        parts = urlsplit(url)
        if parts.scheme not in ('http','https','file') or not IMAGE.search(parts.path) or SKIP.search(parts.path): return
        query = [(k,v) for k,v in parse_qsl(parts.query,keep_blank_values=True)
                 if not (re.fullmatch(r'x\d+',k) and not v)]
        # Keep non-resize parameters (including signatures), and don't assume
        # width is disposable on signed/CDN URLs.
        sizing = {'w','h','width','height','resize','fit'}
        if query and all(k.lower() in sizing for k,v in query): query = []
        url = urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode(query),''))
        if url not in images: images.append(url)
    for img in image_root.find_all('img'):
        tiny = False
        for dim in ('width','height'):
            val = str(img.get(dim,''))
            if re.fullmatch(r'\d+(?:px)?',val) and int(val.removesuffix('px')) <= 32: tiny = True
        if tiny: continue
        for attr in ('src','data-src','data-original'): add_image(img.get(attr))
        for attr in ('srcset','data-srcset'):
            srcset = img.get(attr,'').strip()
            # Avada lazy placeholders contain commas inside a data URI. They
            # are not candidate URLs; the real src above remains usable.
            if srcset.startswith(('data:','blob:')): continue
            options = []
            for item in srcset.split(','):
                pieces = item.strip().split()
                if not pieces: continue
                try: weight = float(pieces[1].rstrip('wx')) if len(pieces)>1 else 1
                except ValueError: weight = 1
                options.append((weight,pieces[0]))
            if options: add_image(max(options,key=lambda pair:pair[0])[1])
    # JSON blobs can hold galleries omitted from the static article DOM.
    for obj in blobs:
        for value in walk(obj):
            if isinstance(value,str) and (value.startswith(('http://','https://','//','/'))):
                add_image(value)
    return dict(title=title,date=date,url=source,chars=min(len(text),limit),truncated=len(text)>limit,text=text[:limit],images=images,pfbid=facebook)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url_or_file')
    parser.add_argument('--chars',type=int,default=3000)
    parser.add_argument('--images-only',action='store_true',help='Only images and Facebook permalinks; JSON retains metadata with empty text.')
    parser.add_argument('--json',action='store_true')
    args = parser.parse_args()
    if args.chars < 0: parser.error('--chars must be nonnegative')
    try:
        if args.url_or_file.startswith(('http://','https://')):
            result = subprocess.run(['curl','-fsSL','-m','15','-A',UA,args.url_or_file],capture_output=True)
            if result.returncode: raise OSError(result.stderr.decode(errors='replace').strip() or 'curl failed')
            raw = result.stdout
        else: raw = Path(args.url_or_file).read_bytes()
        data = digest(raw,args.url_or_file,args.chars)
    except (OSError,ValueError) as exc:
        print(f'Error reading {args.url_or_file}: {exc}',file=sys.stderr)
        return 1
    if args.images_only: data.update(text='',chars=0,truncated=False)
    if args.json: print(json.dumps(data,ensure_ascii=False,indent=2))
    else:
        if not args.images_only:
            print(f"Title: {data['title']}\nDate: {data['date'] or ''}\nURL: {data['url']}\nText ({data['chars']} chars{' ; truncated' if data['truncated'] else ''}):\n{data['text']}\n")
        print('Images:\n'+'\n'.join(data['images']))
        if data['pfbid']: print('\nFacebook / pfbid:\n'+'\n'.join(data['pfbid']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
