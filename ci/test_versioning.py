"""Release updates preserve content and fail validation before changing files."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import versioning


class VersioningTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in versioning.MARKDOWN:
            self.write(name, b'# Title\r\n# Version: 1.2.3\r\nOther 1.2.3 text\r\n')
        for name in versioning.JSON_FILES:
            self.write(name, b'{\r\n "nested": {"version":"9.9.9"}, "version" : "1.2.3", "other": true\r\n}\r\n')
        for seed in versioning.SEEDS.values():
            self.write(seed, b'stale seed')

    def write(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob('*') if path.is_file()}

    def test_bump_preserves_content_and_copies_seeds(self):
        before = self.snapshot()
        versioning.bump(self.root, '2.0.0')
        after = self.snapshot()
        for name in versioning.MARKDOWN:
            self.assertEqual(after[name], before[name].replace(b'# Version: 1.2.3', b'# Version: 2.0.0'))
        for name in versioning.JSON_FILES:
            self.assertEqual(after[name], before[name].replace(b'"1.2.3"', b'"2.0.0"'))
        for source, seed in versioning.SEEDS.items():
            self.assertEqual(after[seed], after[source])

    def test_invalid_versions_do_not_write(self):
        for version in ('v2.0.0', '2.0', '01.2.3', '2.0.0-beta', '2.0.0\n'):
            with self.subTest(version=version):
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    versioning.bump(self.root, version)
                self.assertEqual(before, self.snapshot())

    def test_bad_sources_do_not_write(self):
        name = versioning.JSON_FILES[-1]
        original = (self.root / name).read_bytes()
        for malformed in (b'{"version":"1.2.3","version":"1.2.3"}',
                          b'{"nested":{"version":"1.2.3"}}', b'{', b'{"version":12}'):
            with self.subTest(malformed=malformed):
                self.write(name, malformed)
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    versioning.bump(self.root, '2.0.0')
                self.assertEqual(before, self.snapshot())
        self.write(name, original)
        for missing in (name, next(iter(versioning.SEEDS.values()))):
            path = self.root / missing
            data = path.read_bytes()
            path.unlink()
            before = self.snapshot()
            with self.assertRaises((ValueError, OSError)):
                versioning.bump(self.root, '2.0.0')
            self.assertEqual(before, self.snapshot())
            path.write_bytes(data)

    def test_header_count_and_version_mismatch(self):
        name = versioning.MARKDOWN[0]
        for contents in (b'# Version: 1.2.3\n# Version: 1.2.3\n', b'No header', b'# Version: broken'):
            self.write(name, contents)
            before = self.snapshot()
            with self.assertRaises(ValueError):
                versioning.bump(self.root, '2.0.0')
            self.assertEqual(before, self.snapshot())
        self.write(name, b'# Version: 2.0.0\n')
        with self.assertRaises(ValueError):
            versioning.check(self.root)

    def test_checker_count_comes_from_inventory(self):
        self.write('extra.md', b'# Version: 1.2.3\n')
        with patch.object(versioning, 'MARKDOWN', (*versioning.MARKDOWN, 'extra.md')):
            output = StringIO()
            with redirect_stdout(output):
                versioning.check(self.root)
            self.assertEqual(output.getvalue(), 'OK: version 1.2.3 consistent across 10 files\n')


if __name__ == '__main__':
    unittest.main()
