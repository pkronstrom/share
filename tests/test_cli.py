import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / 'quick-share'


class SharingTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(CLI.exists(), 'Sharing CLI does not exist yet')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'repo'
        self.root.mkdir()
        self.source = Path(self.tmp.name) / 'Example.html'
        self.source.write_text('<!doctype html><html><head><title>Example</title></head><body>Hello</body></html>')
        self.env = {**os.environ, 'QUICK_SHARE_REPO': str(self.root)}
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        (self.root / 'README.md').write_text('Fixture')
        self.git('add', 'README.md')
        self.git('commit', '-m', 'Initial')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, text=True, capture_output=True).stdout

    def cli(self, *args, success=True):
        result = subprocess.run([str(CLI), *map(str, args)], env=self.env, text=True, capture_output=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        return result

    def test_publish_and_list_then_unshare(self):
        result = self.cli('publish', self.source, '--no-push')
        self.assertTrue((self.root / 'cards/example/index.html').is_file())
        self.assertTrue(result['url'].endswith('/cards/example/'))
        self.assertEqual(self.cli('list')['shares'][0]['name'], 'example')
        self.assertEqual(self.git('status', '--porcelain'), '')
        self.cli('unshare', 'example', '--no-push')
        self.assertFalse((self.root / 'cards/example').exists())
        self.assertEqual(self.cli('list')['shares'], [])
        self.assertEqual(self.cli('unshare', 'example', '--no-push')['status'], 'already_absent')

    def test_retry_is_noop_and_updates_need_replace(self):
        self.cli('publish', self.source, '--no-push')
        head = self.git('rev-parse', 'HEAD')
        self.assertEqual(self.cli('publish', self.source, '--no-push')['status'], 'unchanged')
        self.assertEqual(head, self.git('rev-parse', 'HEAD'))
        self.source.write_text('Updated')
        self.cli('publish', self.source, '--no-push', success=False)
        self.cli('publish', self.source, '--replace', '--no-push')
        self.assertIn('Updated', (self.root / 'cards/example/index.html').read_text())

    def test_invalid_name_and_missing_file_leave_repo_unchanged(self):
        for bad in ('../escape', '.', '-bad', 'a/b'):
            self.cli('publish', self.source, '--name', bad, '--no-push', success=False)
        self.cli('publish', self.source.with_name('missing.html'), '--no-push', success=False)
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_dry_run_does_not_publish_or_remove(self):
        self.assertEqual(self.cli('publish', self.source, '--dry-run')['status'], 'dry_run')
        self.assertFalse((self.root / 'cards/example').exists())
        self.cli('publish', self.source, '--no-push')
        self.cli('unshare', 'example', '--dry-run')
        self.assertTrue((self.root / 'cards/example/index.html').is_file())

    def test_preserves_other_work_and_can_share_binary(self):
        (self.root / 'unrelated.txt').write_text('Keep')
        self.cli('publish', self.source, '--no-push', success=False)
        self.assertEqual((self.root / 'unrelated.txt').read_text(), 'Keep')
        (self.root / 'unrelated.txt').unlink()
        binary = self.source.with_name('model.glb')
        binary.write_bytes(bytes(range(256)))
        self.cli('publish', binary, '--no-push')
        self.assertEqual((self.root / 'cards/model/model.glb').read_bytes(), binary.read_bytes())


if __name__ == '__main__':
    unittest.main()
