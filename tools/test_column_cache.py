import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

SCRIPT = Path(__file__).with_name('column_cache.py')


class CacheTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.cache = self.base / 'cache'
        self.repo = self.base / 'repo'
        self.repo.mkdir()
        self.env = dict(os.environ, COLUMN_CACHE_DIR=str(self.cache))
        self.date = datetime.now(ZoneInfo('Asia/Taipei')).date()
        self.input = self.base / 'input.json'

    def cli(self, *args, success=True):
        p = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], env=self.env, text=True, capture_output=True)
        self.assertEqual(p.returncode == 0, success, p.stderr + p.stdout)
        return json.loads(p.stdout)

    def record(self, ident, days=0, creator='alice', **kw):
        return dict(id=ident, creator_key=creator, source='facebook', platform='Facebook', permalink='https://example.org/' + ident, date=str(self.date - timedelta(days=days)), full_text='original text', **kw)

    def add(self, records):
        self.input.write_text(json.dumps(records), encoding='utf-8')
        return self.cli('add', self.input)

    def pick(self, *args):
        return self.cli('pick', '--date', self.date, '--repo', self.repo, *args)

    def test_add_idempotency_and_status(self):
        r = self.record('col-a')
        self.assertEqual(self.add(r)['added'], ['col-a'])
        self.cli('mark-used', 'col-a', '--date', self.date)
        r['full_text'] = 'updated'
        self.assertEqual(self.add(r)['updated'], ['col-a'])
        self.assertEqual(self.add(r)['skipped'], ['col-a'])
        data = json.loads((self.cache / 'cache.json').read_text())['entries'][0]
        self.assertEqual((data['status'], data['used_date'], data['full_text']), ('used', str(self.date), 'updated'))
        self.assertEqual(json.loads((self.cache / 'raw/col-a.json').read_text()), r)
        self.assertEqual(self.pick()['picked'], [])

    def test_window_dedupe_and_caps(self):
        records = [self.record('col-url'), self.record('col-key', 1), self.record('col-issue', 2), self.record('col-one', 3), self.record('col-two', 4), self.record('col-three', 5), self.record('col-old', 8)]
        self.add(records)
        log = [{'date': str(self.date - timedelta(days=30)), 'url': records[0]['permalink']}, {'date': str(self.date - timedelta(days=1)), 'key': 'col-key'}]
        (self.repo / 'ai-columns-log.json').write_text(json.dumps(log))
        issue = self.repo / 'ai/issues' / str(self.date - timedelta(days=2))
        issue.mkdir(parents=True)
        (issue / 'data.json').write_text(json.dumps({'columns': [{'id': 'col-issue'}]}))
        result = self.pick()
        self.assertEqual([e['id'] for e in result['picked']], ['col-one', 'col-two'])
        self.assertEqual(result['expired_pending'], ['col-old'])
        self.assertEqual(len(result['excluded']), 4)
        self.assertEqual(result['stats'], {'pending': 7, 'qualified': 3})
        self.cli('mark-used', 'col-one', '--date', self.date)
        self.assertNotIn('col-one', [e['id'] for e in self.pick()['picked']])

    def test_image_and_export(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow is optional')
        image = self.base / 'input.png'
        Image.new('RGB', (2000, 1000), 'red').save(image)
        self.add(self.record('col-img', image_path=str(image)))
        webp = self.cache / 'img/col-img.webp'
        with Image.open(webp) as im:
            self.assertEqual(im.size, (1600, 800))
        picked = self.pick('--copy-images', self.base / 'issue-img')['picked'][0]
        self.assertEqual(picked['image']['abs_path'], str(webp))
        self.assertEqual(picked['image']['issue_file'], 'col-img.webp')
        self.assertTrue((self.base / 'issue-img/col-img.webp').exists())
        archive = self.base / 'backup.tgz'
        self.cli('export', '--out', archive)
        with tarfile.open(archive) as tar:
            self.assertIn('cache/raw/col-img.json', tar.getnames())
            self.assertIn('cache/img/col-img.webp', tar.getnames())


if __name__ == '__main__':
    unittest.main()
