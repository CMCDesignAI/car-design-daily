import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from datetime import timedelta
from unittest.mock import patch

from PIL import Image
from tools import adp_cache, columns


class ADPCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name); self.root = self.base / 'cache'; self.repo = self.base / 'repo'
        (self.repo / 'data').mkdir(parents=True)
        self.queue = self.repo / 'data/columns_queue.json'; self.log = self.repo / 'data/columns_log.json'
        self.queue.write_text('{"items": {}}'); self.log.write_text('{"used": {}}')
        self.env = {**os.environ, 'ADP_CACHE_DIR': str(self.root)}

    def tearDown(self): self.tmp.cleanup()

    def run_cmd(self, *args):
        p = subprocess.run([sys.executable, 'tools/adp_cache.py', *args], env=self.env, text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout), p.stderr

    def add(self, ident, **fields):
        record = {'id': ident, 'url': 'https://example.com/' + ident, 'full_text': 'Full design story', 'date': '2024-01-01', **fields}
        path = self.base / 'record.json'; path.write_text(json.dumps(record))
        return self.run_cmd('add', str(path))

    def test_quota_idempotency_and_overage(self):
        self.assertEqual(self.run_cmd('quota')[0]['remaining'], 2)
        self.add('adp-one'); self.add('adp-one')
        self.assertEqual(self.run_cmd('quota')[0]['used'], 1)
        self.add('adp-two')
        result, _ = self.run_cmd('next', '--queue', str(self.queue), '--log', str(self.log))
        self.assertEqual(result['reason'], 'quota')
        result, stderr = self.add('adp-three')
        self.assertEqual(result['quota']['remaining'], 0); self.assertIn('warning', stderr)
        self.assertEqual(len(json.loads((self.root / 'cache.json').read_text())['entries']), 3)

    def test_rolling_window(self):
        old = (adp_cache.today() - timedelta(days=8)).isoformat()
        adp_cache.write(self.root / 'reads.json', {'reads': [{'date': old, 'id': 'adp-old'}]})
        self.assertEqual(self.run_cmd('quota')[0]['remaining'], 2)

    def test_next_ranking_and_exclusions(self):
        def item(i, craft, date='2024-01-01', **kw):
            return {'id': 'adp-'+i, 'url': 'https://example.com/adp-'+i, 'source': adp_cache.SOURCE, 'needs_browser': True, 'craft': craft, 'date': date, **kw}
        items = [item('old', 4), item('new', 4, '2024-02-01'), item('used', 99, used=True), item('removed', 99, removed=True), item('logged', 99), item('cached', 99)]
        self.queue.write_text(json.dumps({'items': {x['id']: x for x in items}})); self.log.write_text(json.dumps({'used': {'adp-logged': '2024-01-01'}}))
        self.add('adp-cached')
        result, _ = self.run_cmd('next', '--queue', str(self.queue), '--log', str(self.log))
        self.assertEqual(result['item']['id'], 'adp-new')

    def test_images_pick_status_export(self):
        png = self.base / 'test.png'; Image.new('RGB', (100, 50), 'red').save(png)
        self.add('adp-one', image_paths=[str(png)] * 3)
        result, _ = self.run_cmd('pick', '--date', '2026-01-01', '--repo', str(self.repo), '--copy-images', str(self.base / 'out'))
        self.assertEqual(len(result['picked'][0]['images']), 3)
        with Image.open(self.root / 'img/adp-one.jpg') as image:
            self.assertEqual(image.format, 'JPEG')
        archive = self.base / 'cache.tgz'; self.run_cmd('export', '--out', str(archive))
        with tarfile.open(archive) as tar: self.assertIn('cache/reads.json', tar.getnames())
        self.run_cmd('mark-used', 'adp-one', '--date', '2026-01-01')
        self.assertEqual(self.run_cmd('pick', '--date', '2026-01-01', '--repo', str(self.repo))[0]['picked'], [])

    def test_columns_pick_requires_cache(self):
        item = {'id': 'adp-one', 'url': 'https://example.com/adp-one', 'source': adp_cache.SOURCE, 'needs_browser': True, 'title_en': 'Design story', 'date': '2024-01-01', 'kind': 'interview', 'column': 'Design Story', 'craft_ok': True, 'craft': 5}
        self.queue.write_text(json.dumps({'items': {item['id']: item}}))
        with patch.object(columns, 'Q', self.queue), patch.object(columns, 'LOG', self.log), patch.object(columns, 'migrate'), patch.dict(os.environ, {'ADP_CACHE_DIR': str(self.root)}), patch.object(columns, 'get', side_effect=AssertionError('network')):
            with contextlib.redirect_stdout(io.StringIO()) as out: columns.pick('2026-01-01', 1, '', None, True)
            self.assertEqual(json.loads(out.getvalue()), [])
            self.add('adp-one')
            with contextlib.redirect_stdout(io.StringIO()) as out: columns.pick('2026-01-01', 1, '', None, True)
            result = json.loads(out.getvalue())[0]
            self.assertEqual(result['body'], 'Full design story'); self.assertIsNone(result['browser_task'])


if __name__ == '__main__': unittest.main()
