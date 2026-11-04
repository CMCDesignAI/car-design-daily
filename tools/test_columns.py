"""Offline regressions for selection, migration, public teasers, and sample preparation."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import columns as c
import od_sample as od


def entry(iid, source=c.AD, kind='column', date='2026-11-01', **extra):
    x = c.item(source, '', 'https://example.com/' + iid, iid, date, kind,
               {'column': 'Design Story', 'interview': 'Meet the Designer'}.get(kind, kind.title()))
    x.update(extra)
    return x


class SelectionTests(unittest.TestCase):
    def test_tiers_oldest_first_and_core77_fallback(self):
        items = [entry('core', 'Core77', 'analysis', '2026-01-01'),
                 entry('cdn', 'Car Design News', 'interview'),
                 entry('new'), entry('old', date='2026-10-01')]
        self.assertEqual([x['id'] for x in c.select(items, {}, '2026-11-04', 8)], ['old', 'cdn'])  # A&D max 1/day
        self.assertEqual(c.select(items, {'old': 'D', 'new': 'D', 'cdn': 'D'}, '2026-11-04')[0]['id'], 'core')

    def test_samples_due_one_per_day_and_second_is_column(self):
        items = [entry('sample1', kind='issue_sample', due='2026-11-04'),
                 entry('sample2', kind='issue_sample', due='2026-11-04'),
                 entry('future', kind='issue_sample', due='2026-11-07'), entry('column'), entry('tv', 'Car Design TV', 'analysis')]
        self.assertEqual([x['id'] for x in c.select(items, {}, '2026-11-04')], ['sample1', 'tv'])
        self.assertEqual([x['id'] for x in c.select(items, {'sample1': '2026-11-04'}, '2026-11-04', 3)], ['tv'])

    def test_core77_fallback_after_daily_sample_already_used(self):
        items = [entry('used-sample', kind='issue_sample'), entry('due-sample', kind='issue_sample'),
                 entry('core', 'Core77', 'analysis')]
        self.assertEqual([x['id'] for x in c.select(items, {'used-sample': '2026-11-04'}, '2026-11-04', 2)], ['core'])

    def test_back_issue_expires_after_12_months(self):
        old = entry('old', kind='issue_sample', due='2026-11-01', back_issue=True, release_date='2025-11-07')
        self.assertEqual([x['id'] for x in c.select([old], {}, '2026-11-07')], ['old'])
        self.assertEqual(c.select([old], {}, '2026-11-08'), [])

    def test_exclusion_uses_excerpt_and_usage(self):
        items = [entry('excluded', excerpt='Electric BATTERY materials'), entry('used', used=True), entry('okay')]
        self.assertEqual([x['id'] for x in c.select(items, {}, '2026-11-04', 3, 'battery')], ['okay'])

    def test_auto_two_triggers_and_date_window(self):
        for trigger in [entry('interview', kind='interview')]:
            self.assertEqual(len(c.select([trigger, entry('other', 'Car Design TV', 'analysis')], {}, '2026-11-04')), 2)
        self.assertEqual(len(c.select([entry(str(i)) for i in range(3)], {}, '2026-11-04')), 1)  # A&D max 1/day, no force-fill
        self.assertEqual(len(c.select([entry('old-interview', kind='interview', date='2026-10-01'), entry('one')], {}, '2026-11-04')), 1)


class SourceTests(unittest.TestCase):
    fixtures = Path(__file__).parent / 'fixtures/columns'

    def test_new_rss_sources(self):
        with patch.object(c, 'get', return_value=(self.fixtures/'feeds.xml').read_bytes()):
            tv = list(c.rss('fixture', 'Car Design TV', 'cdtv-', 'Design Analysis'))
            self.assertEqual(tv[0]['url'], 'https://example.com/car?keep=yes')
            self.assertEqual(tv[0]['kind'], 'concept')
            self.assertEqual(tv[1]['kind'], 'analysis')
            ap = list(c.rss('fixture', 'The Autopian', 'ap-', 'Damn Good Design (Adrian Clarke)'))
            self.assertEqual([x['id'] for x in ap], ['ap-car', 'ap-lamp'])
            wp = list(c.rss('fixture', 'Wallpaper*', 'wp-', 'Transportation'))
            self.assertEqual([x['id'] for x in wp], ['wp-car', 'wp-bicycle', 'wp-lamp'])
            dg = list(c.rss('fixture', 'Disegno', 'dg-', 'Disegno'))
            self.assertEqual([x['id'] for x in dg], ['dg-car', 'dg-review'])
            self.assertEqual(dg[0]['excerpt'], 'Public automotive teaser')
            self.assertEqual(dg[0]['date'], '2026-11-01')

    def test_public_article_metadata_and_honda_slug_date(self):
        with patch.object(c, 'get', return_value=(self.fixtures/'article.html').read_bytes()):
            x = c.public_article(c.MF, 'mf-', 'https://motor-fan.jp/article/123/')
        self.assertEqual(x['id'], 'mf-123')
        self.assertEqual(x['kind'], 'interview')
        self.assertEqual(x['language'], 'ja')
        self.assertNotIn('Motor Fan', x['title_en'])
        self.assertEqual(x['excerpt'], 'Public teaser')
        self.assertEqual(x['date'], '2026-11-01')
        with patch.object(c, 'get', return_value=(self.fixtures/'honda.html').read_bytes()):
            x = c.public_article(c.HD, 'hd-', 'https://global.honda/jp/design/interview/202602crv/')
        self.assertEqual(x['date'], '2026-02-01')
        self.assertEqual(x['column'], 'Honda Design Interview')

    def test_disegno_brand_design_studios(self):
        self.assertTrue(c.disegno_keep('Inside the Mercedes-Benz design studio'))
        self.assertTrue(c.disegno_keep('Transportation design'))
        self.assertFalse(c.disegno_keep('Inside a furniture design studio'))

    def test_new_priorities_do_not_trigger_auto_two(self):
        for source in (c.MF, c.HD):
            x = entry('new', source, 'interview')
            self.assertEqual(c.tier(x), 2)
            self.assertEqual(len(c.select([x, entry('other')], {}, '2026-11-04')), 1)
        self.assertEqual(c.select([entry('removed', removed=True)], {}, '2026-11-04'), [])



class FileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.stack = contextlib.ExitStack()
        for name, val in [('ROOT', self.root), ('Q', self.root/'data/columns_queue.json'), ('LOG', self.root/'data/columns_log.json')]:
            self.stack.enter_context(patch.object(c, name, val))
        self.stack.enter_context(patch.object(od, 'SAMPLES', self.root/'samples'))
        self.stack.enter_context(patch.object(od, 'STATE', self.root/'state.json'))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))

    def tearDown(self):
        self.stack.close(); self.tmp.cleanup()

    def test_migrate_preserves_usage_and_commit_full_id(self):
        old = entry('a-long-id', kind='interview')
        c.save(self.root/'data/autodesign_queue.json', {'items': {'a-long-id': old}})
        c.save(self.root/'data/autodesign_log.json', {'used': {'a-long-id': '2026-11-01'}})
        c.migrate(); c.migrate()
        x = c.load(c.Q, {})['items']['ad-a-long-id']
        self.assertTrue(x['used']); self.assertEqual(x['source'], c.AD)
        c.commit('2026-11-04', ['ad-a-long-id'])
        self.assertEqual(c.load(c.LOG, {})['used']['ad-a-long-id'], '2026-11-04')

    def test_enqueue_crops_and_writer_metadata(self):
        from PIL import Image
        page = od.SAMPLES/'280/page_01.png'; page.parent.mkdir(parents=True)
        Image.new('RGB', (1600, 1100), 'white').save(page)
        crop = od.crop(280, '01', (0, 0, 1300, 500), 'detail')
        with Image.open(crop) as im: self.assertEqual(max(im.size), 1200)
        with self.assertRaisesRegex(ValueError, '45%'): od.crop(280, '01', (0, 0, 1600, 800), 'large')
        rec = dict(issue=280, overdrive_url='https://example.com/280')
        c.save(od.STATE, {'issues': {'280': rec}, 'last_issue': 280})
        with self.assertRaisesRegex(ValueError, 'notes'): od.add_section(280, 'T', [1], 'short', [str(crop)], '2026-11-04')
        notes = 'Key point read from the spread about microcar proportions and retro references. ' * 4
        od.add_section(280, 'Quadricycle planet', [1], notes, [str(crop), str(crop)], '2026-11-04')
        od.add_section(280, 'Pianeta quadriciclo', [1], notes, [str(crop)])
        q = c.load(c.Q, {})['items']
        self.assertEqual([x['due'] for x in q.values()], ['2026-11-04', '2026-11-07'])
        output = io.StringIO()
        with contextlib.redirect_stdout(output): c.pick('2026-11-04', 1, '', str(self.root/'img'))
        picked = json.loads(output.getvalue())[0]
        self.assertEqual(picked['sample_pages'], [1])
        self.assertEqual(picked['image']['credit'], 'Auto&Design No.280, via OverDrive sample')
        self.assertTrue((self.root/'img'/picked['image2']['file']).exists())

    def test_public_body_skip_and_three_downloads(self):
        paragraph = 'The designer explains proportions, clay process and recycled materials. ' * 20
        fixture = ('<nav><p>navigation</p></nav><meta property="og:image" content="/outside.jpg">'
                   '<main><article class="entry-content"><p>' + paragraph + '<b>Design quote.</b></p>'
                   '<footer><p>footer noise</p></footer><script>private()</script>'
                   '<img src="/logo.png"><img src="/tiny.jpg" width="100">'
                   '<img src="/vector.svg"><img src="/fallback.jpg" srcset="/small.jpg 300w, /large.jpg 1200w">'
                   + ''.join(f'<img src="/photo{i}.jpg">' for i in range(4)) + '</article></main>')
        body, images, paywall = c.extract_article(fixture, 'https://example.com/story')
        self.assertIn('Design quote.', body)
        self.assertNotIn('navigation', body); self.assertNotIn('footer noise', body)
        self.assertFalse(paywall)
        self.assertEqual(images[0], 'https://example.com/large.jpg')
        self.assertEqual(len(images), 5)
        rows = [entry('a-short'), entry('b-paid'), entry('c-good'), entry('cdn', 'Car Design News', 'interview')]
        c.save(c.Q, {'items': {x['id']: x for x in rows}})
        visited = []
        def fake_get(url):
            visited.append(url)
            if url.endswith('a-short'): return b'<article><p>Teaser only</p></article>'
            if url.endswith('b-paid'): return ('<script type="application/ld+json">{"isAccessibleForFree":false}</script>' + fixture).encode()
            if url.endswith('c-good'): return fixture.encode()
            if url.endswith('cdn'): self.fail('CDN should never be fetched')
            return b'image bytes'
        output = io.StringIO()
        with patch.object(c, 'get', side_effect=fake_get), contextlib.redirect_stdout(output):
            c.pick('2026-11-04', 4, '', str(self.root/'img'))
        result = json.loads(output.getvalue())
        self.assertEqual(len(result), 1)
        picked = result[0]
        self.assertEqual(picked['body'], body)
        self.assertEqual(len(picked['images']), 5)
        self.assertEqual(len(picked['more_images']), 1)
        self.assertEqual(len(list((self.root/'img').iterdir())), 3)
        self.assertEqual(picked['image2']['file'], 'c-good-2.jpg')
        queue = c.load(c.Q, {})['items']
        self.assertEqual(queue['a-short']['skipped_reason'], 'body_too_short')
        self.assertEqual(queue['b-paid']['skipped_reason'], 'paywalled')
        self.assertEqual(queue['cdn']['skipped_reason'], 'paywalled')
        self.assertGreater(c.tier(rows[-1]), c.tier(entry('core', 'Core77', 'analysis')))

    def test_seed_and_backfill(self):
        rec = dict(issue=280, crid='x', overdrive_url='https://example.com/280')
        with patch.object(od, 'discover', return_value={280:rec}), patch.object(od, 'capture', return_value=['page']) as cap:
            od.check('2026-11-04', seed=True)
            cap.assert_not_called(); self.assertFalse(c.Q.exists())
            self.assertEqual(c.load(od.STATE, {})['last_issue'], 280)
            od.check('2026-11-04', seed=True, backfill=True)
            cap.assert_called_once(); self.assertIn('280', c.load(od.STATE,{})['pending_sections'])

    def test_new_homepages_limit_duplicates_and_failure_isolation(self):
        mf_home = c.Page(''.join(f'<a href="/article/{i}/">article</a>' for i in range(20)))
        honda_home = c.Page('<a href="/jp/design/interview/202610crv/">Honda</a>')
        article = c.Page((SourceTests.fixtures/'article.html').read_text())
        honda = c.Page((SourceTests.fixtures/'honda.html').read_text())
        visited = []
        def fake_page(url):
            visited.append(url)
            if url == 'https://motor-fan.jp/publisher/carstyling-jp/': return mf_home
            if url == 'https://global.honda/jp/design/': return honda_home
            if '/article/' in url: return article
            if '/design/interview/' in url: return honda
            raise RuntimeError('non-200 source')
        with patch.object(c, 'rss', side_effect=RuntimeError('non-200 feed')), patch.object(c, 'page', side_effect=fake_page), patch.object(c, 'today', return_value='2026-11-04'), contextlib.redirect_stderr(io.StringIO()):
            c.fetch(75)
            self.assertEqual(sum('/article/' in url for url in visited), 15)
            items = c.load(c.Q, {})['items']
            self.assertEqual(len(items), 16)
            self.assertEqual(items['hd-202610crv']['date'], '2026-10-01')
            visited.clear()
            c.fetch(75)
            self.assertEqual(sum('/article/' in url for url in visited), 5)
            self.assertFalse(any('/design/interview/' in url for url in visited))

    def test_core77_existing_cleanup(self):
        c.save(c.Q, {'items': {x['id']: x for x in [entry('lamp', 'Core77', 'analysis', title_en='Lamp design - Core77'), entry('car', 'Core77', 'analysis', title_en='Car design - Core77')]}})
        with patch.object(c, 'rss', side_effect=RuntimeError('offline')), patch.object(c, 'page', side_effect=RuntimeError('offline')), contextlib.redirect_stderr(io.StringIO()):
            c.fetch(75)
        items = c.load(c.Q, {})['items']
        self.assertTrue(items['lamp']['removed'])
        self.assertEqual(items['car']['title_en'], 'Car design')

    def test_cdn_teaser_only_paywall_and_failure_isolation(self):
        home = c.Page('<a href="/designers/smith-talks/123">x</a><a href="/cars/person-appointed/124">x</a>')
        article = c.Page('<meta property="og:title" content="Smith talks"><meta property="og:description" content="Public teaser"><script type="application/ld+json">{"datePublished":"2026-11-01","isAccessibleForFree":false,"articleBody":"PRIVATE BODY"}</script>')
        def fake_page(url):
            if url == 'https://www.cardesignnews.com/': return home
            if '/designers/' in url: return article
            raise RuntimeError('source unavailable')
        with patch.object(c, 'rss', side_effect=RuntimeError('feed unavailable')), patch.object(c, 'page', side_effect=fake_page), patch.object(c, 'today', return_value='2026-11-04'), contextlib.redirect_stderr(io.StringIO()): c.fetch(75)
        items = list(c.load(c.Q,{})['items'].values())
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['excerpt'], 'Public teaser')
        self.assertTrue(items[0]['paywalled']); self.assertEqual(items[0]['kind'], 'interview')


if __name__ == '__main__': unittest.main()
