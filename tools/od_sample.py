#!/usr/bin/env python3
"""Track and capture public OverDrive samples; prepare small credited crops."""
import argparse
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
import re
import sys

try:
    from . import columns as c
except ImportError:
    import columns as c

STATE = c.ROOT / 'data/od_state.json'
SAMPLES = c.ROOT / 'data/od_samples'
MEDIA = 'https://downloadlibrary.overdrive.com/media/13569124'

def discover():
    raw = c.get(MEDIA).decode('utf-8', 'replace')
    records = {}
    def walk(obj):
        if isinstance(obj, dict):
            edition = str(obj.get('edition','')); m = re.match(r'\s*(\d+)', edition)
            media = str(obj.get('id',''))
            if m and media.isdigit():
                samples = list(c.values(obj,'href'))
                sample = next((s for s in samples if isinstance(s,str) and 'samples.overdrive.com/' in s and 'crid=' in s), None)
                if sample:
                    issue = int(m[1]); crid = re.search(r'crid=([\w-]+)',sample)[1]
                    records[issue] = dict(issue=issue,edition=edition,media_id=media,crid=crid,sample_url=sample,overdrive_url=f'https://downloadlibrary.overdrive.com/media/{media}')
            for v in obj.values(): walk(v)
        elif isinstance(obj,list):
            for v in obj: walk(v)
    # Decode complete embedded objects, including JS assignments and JSON script tags.
    decoder=json.JSONDecoder()
    for m in re.finditer(r'[\[{]',raw):
        try: obj,_=decoder.raw_decode(raw,m.start())
        except ValueError: continue
        walk(obj)
    # Fallback for fragments: use the nearest preceding numeric id, never a nested format id.
    for m in re.finditer(r'https://samples\.overdrive\.com/\?crid=([\w-]+)[^"<>\s]*',html.unescape(raw)):
        prefix=html.unescape(raw)[:m.start()]
        ids=list(re.finditer(r'"id"\s*:\s*"(\d+)"',prefix))
        if not ids: continue
        start=ids[-1].start(); edition=re.search(r'"edition"\s*:\s*"(\d+)[^"]*"',prefix[start:])
        if not edition: continue
        issue=int(edition[1])
        if issue in records: continue
        media=ids[-1][1]
        records[issue]=dict(issue=issue,edition=edition[1],media_id=media,crid=m[1],sample_url=m[0],overdrive_url=f'https://downloadlibrary.overdrive.com/media/{media}')
    if not records: raise RuntimeError('No issue/sample records found on the public media page')
    return records

def capture(issue,crid=None):
    state=c.load(STATE,{}); rec=state.get('issues',{}).get(str(issue),{})
    if not crid:
        if not rec: rec=discover().get(issue,{})
        crid=rec.get('crid')
    if not crid: raise ValueError(f'No public sample found for issue {issue}; supply --crid')
    if not re.fullmatch(r'[\da-fA-F]{8}(?:-[\da-fA-F]{4}){3}-[\da-fA-F]{12}',crid): raise ValueError('Invalid sample UUID')
    from playwright.sync_api import sync_playwright
    dest=SAMPLES/str(issue); dest.mkdir(parents=True,exist_ok=True)
    saved=[]; previous=None
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
        try:
            page=browser.new_page(viewport={'width':1600,'height':1100},user_agent=c.UA['User-Agent'])
            page.goto(f'https://samples.overdrive.com/?crid={crid}&.epub-sample.overdrive.com',wait_until='networkidle',timeout=60000)
            page.wait_for_timeout(6000)
            for i in range(1,17):
                data=page.screenshot(); digest=hashlib.sha256(data).digest()
                if digest==previous: break
                path=dest/f'page_{i:02}.png'; path.write_bytes(data); saved.append(str(path.resolve()))
                previous=digest
                page.keyboard.press('ArrowRight'); page.wait_for_timeout(3000)
        finally: browser.close()
    # Clear stale spreads from an older, longer capture only after successful capture.
    for path in dest.glob('page_*.png'):
        if str(path.resolve()) not in saved: path.unlink()
    if not saved: raise RuntimeError('Sample produced no screenshots')
    manifest=dict(issue=issue,crid=crid,pages=saved,captured=c.today())
    c.save(dest/'capture.json',manifest)
    print(f'Captured issue {issue}: {len(saved)} spreads in {dest}')
    return saved

def enqueue(rec,date,pages):
    c.migrate(); q=c.load(c.Q,{'items':{}}); issue=rec['issue']
    for part,label in enumerate(('cover+contents','editorial','first feature'),1):
        iid=f'od-{issue}-p{part}'; due=(dt.date.fromisoformat(date)+dt.timedelta(days=(part-1)*3)).isoformat()
        if iid in q['items']: continue
        q['items'][iid]=dict(id=iid,source=c.AD,credit=f'Auto&Design No.{issue}, via OverDrive sample',paywalled=False,kind='issue_sample',column=f'新刊 No.{issue}',title_en=f'Auto&Design No.{issue}: {label}',date=date,due=due,url=rec['overdrive_url'],overdrive_url=rec['overdrive_url'],image=None,excerpt='',added=c.today(),used=False,issue_no=issue,part=part,sample_pages=pages)
    c.save(c.Q,q)

def check(date,seed=False,backfill=False):
    records=discover(); newest=max(records); state=c.load(STATE,{}); last=int(state.get('last_issue',0))
    state.setdefault('issues',{}).update({str(k):v for k,v in records.items()})
    state['checked']=date
    if seed and not backfill:
        state['last_issue']=max(last,newest); c.save(STATE,state)
        print(f'Seeded current issue {newest}; no queue entries created'); return
    targets=[newest] if backfill else sorted(k for k in records if k>last)
    for issue in targets:
        print(f'New issue {issue}: {records[issue]["overdrive_url"]}',flush=True)
        pages=capture(issue,records[issue]['crid'])
        enqueue(records[issue],date,pages)
        state['last_issue']=max(int(state.get('last_issue',0)),issue); c.save(STATE,state)
    c.save(STATE,state)
    if not targets: print(f'No new issue (latest {newest}, last_issue {last})')

def crop(issue,page,box,out):
    from PIL import Image
    if Path(out).name!=out or out in ('','.','..'): raise ValueError('--out must be a filename')
    page_number=int(page)
    if page_number<1: raise ValueError('--page must be positive')
    src=SAMPLES/str(issue)/f'page_{page_number:02}.png'
    with Image.open(src) as im:
        x,y,w,h=box
        if min(x,y)<0 or min(w,h)<=0 or x+w>im.width or y+h>im.height: raise ValueError('Crop must fit inside the page')
        if w*h>im.width*im.height*.45: raise ValueError('Crop exceeds 45% of page area')
        small=im.crop((x,y,x+w,y+h)).convert('RGB'); small.thumbnail((1200,1200))
        dest=src.parent/'crops'/(Path(out).stem+'.jpg'); dest.parent.mkdir(parents=True,exist_ok=True)
        small.save(dest,quality=82)
    print(dest.resolve()); return dest

def set_crops(iid,crop1,crop2=None):
    c.migrate(); q=c.load(c.Q,{'items':{}})
    if iid not in q['items'] or q['items'][iid]['kind']!='issue_sample': raise ValueError(f'Unknown issue sample {iid}')
    for key,path in [('crop1',crop1),('crop2',crop2)]:
        if path:
            p=Path(path).resolve()
            if not p.is_file(): raise ValueError(f'Crop does not exist: {p}')
            q['items'][iid][key]=str(p)
    c.save(c.Q,q); print(f'Updated {iid}')

def main():
    ap=argparse.ArgumentParser(description=__doc__); sub=ap.add_subparsers(dest='cmd',required=True)
    ck=sub.add_parser('check'); ck.add_argument('--date',default=c.today()); ck.add_argument('--seed-current',action='store_true'); ck.add_argument('--backfill',action='store_true')
    cp=sub.add_parser('capture'); cp.add_argument('--issue',type=int,required=True); cp.add_argument('--crid')
    cr=sub.add_parser('crop'); cr.add_argument('--issue',type=int,required=True); cr.add_argument('--page',required=True); cr.add_argument('--box',required=True); cr.add_argument('--out',required=True)
    st=sub.add_parser('set'); st.add_argument('--id',required=True); st.add_argument('--crop1',required=True); st.add_argument('--crop2')
    a=ap.parse_args()
    try:
        if a.cmd=='check': dt.date.fromisoformat(a.date); check(a.date,a.seed_current,a.backfill)
        elif a.cmd=='capture': capture(a.issue,a.crid)
        elif a.cmd=='crop':
            box=tuple(int(x) for x in a.box.split(','))
            if len(box)!=4: raise ValueError('--box requires x,y,w,h')
            crop(a.issue,a.page,box,a.out)
        else: set_crops(a.id,a.crop1,a.crop2)
    except Exception as e: print(f'Error: {e}',file=sys.stderr); return 1
    return 0

if __name__=='__main__': sys.exit(main())
