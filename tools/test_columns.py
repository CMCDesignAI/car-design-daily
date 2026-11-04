"""Offline regressions for selection, migration, public teasers, and sample preparation."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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
        self.assertEqual([x['id'] for x in c.select(items, {}, '2026-11-04', 8)], ['old', 'new', 'cdn'])
        self.assertEqual(c.select(items, {'old': 'D', 'new': 'D', 'cdn': 'D'}, '2026-11-04')[0]['id'], 'core')

    def test_samples_due_one_per_day_and_second_is_column(self):
        items = [entry('sample1', kind='issue_sample', due='2026-11-04'),
                 entry('sample2', kind='issue_sample', due='2026-11-04'),
                 entry('future', kind='issue_sample', due='2026-11-07'), entry('column')]
        self.assertEqual([x['id'] for x in c.select(items, {}, '2026-11-04')], ['sample1', 'column'])
        self.assertEqual([x['id'] for x in c.select(items, {'sample1': '2026-11-04'}, '2026-11-04', 3)], ['column'])

    def test_core77_fallback_after_daily_sample_already_used(self):
        items = [entry('used-sample', kind='issue_sample'), entry('due-sample', kind='issue_sample'),
                 entry('core', 'Core77', 'analysis')]
        self.assertEqual([x['id'] for x in c.select(items, {'used-sample': '2026-11-04'}, '2026-11-04', 2)], ['core'])

    def test_exclusion_uses_excerpt_and_usage(self):
        items = [entry('excluded', excerpt='Electric BATTERY materials'), entry('used', used=True), entry('okay')]
        self.assertEqual([x['id'] for x in c.select(items, {}, '2026-11-04', 3, 'battery')], ['okay'])

    def test_auto_two_triggers_and_date_window(self):
        for trigger in [entry('interview', kind='interview'), entry('cdn', 'Car Design News', 'interview')]:
            self.assertEqual(len(c.select([trigger, entry('other')], {}, '2026-11-04')), 2)
        self.assertEqual(len(c.select([entry(str(i)) for i in range(3)], {}, '2026-11-04')), 2)
        self.assertEqual(len(c.select([entry('old-interview', kind='interview', date='2026-10-01'), entry('one')], {}, '2026-11-04')), 1)


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
        od.enqueue(rec, '2026-11-04', [str(page)]); od.enqueue(rec, '2026-11-04', [str(page)])
        q = c.load(c.Q, {})['items']
        self.assertEqual(len(q), 3)
        self.assertEqual([x['due'] for x in q.values()], ['2026-11-04', '2026-11-07', '2026-11-10'])
        od.set_crops('od-280-p1', str(crop), str(crop))
        output = io.StringIO()
        with contextlib.redirect_stdout(output): c.pick('2026-11-04', 1, '', str(self.root/'img'))
        picked = json.loads(output.getvalue())[0]
        self.assertEqual(picked['sample_pages'], [str(page)])
        self.assertEqual(picked['image']['credit'], 'Auto&Design No.280, via OverDrive sample')
        self.assertTrue((self.root/'img'/picked['image2']['file']).exists())

    def test_seed_and_backfill(self):
        rec = dict(issue=280, crid='x', overdrive_url='https://example.com/280')
        with patch.object(od, 'discover', return_value={280:rec}), patch.object(od, 'capture', return_value=['page']) as cap:
            od.check('2026-11-04', seed=True)
            cap.assert_not_called(); self.assertFalse(c.Q.exists())
            self.assertEqual(c.load(od.STATE, {})['last_issue'], 280)
            od.check('2026-11-04', seed=True, backfill=True)
            cap.assert_called_once(); self.assertEqual(len(c.load(c.Q,{})['items']), 3)

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
