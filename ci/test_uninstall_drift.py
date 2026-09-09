"""The README guard must catch changes beyond the former AWK fragments."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class UninstallDriftTests(unittest.TestCase):
    def check_readme(self, transform, success):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'ci').mkdir()
            script = root / 'ci/test-conventions-block-removal.sh'
            shutil.copyfile(ROOT / 'ci/test-conventions-block-removal.sh', script)
            (root / 'README.md').write_text(transform((ROOT / 'README.md').read_text()))
            result = subprocess.run(['bash', str(script)], capture_output=True, text=True)
            self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)

    def test_indentation_is_allowed(self):
        self.check_readme(lambda text: text.replace('     END{printf', '         END{printf'), True)

    def test_semantic_drift_is_rejected(self):
        for old, new in [('b,e,bl,el,', 'e,b,bl,el,'),
                         ('REFUSE - remove the block by hand', 'REFUSE - continue anyway')]:
            with self.subTest(old=old):
                self.check_readme(lambda text: text.replace(old, new), False)

    def test_missing_or_duplicate_program_is_rejected(self):
        self.check_readme(lambda text: text.replace("awk '", "gawk '"), False)
        self.check_readme(lambda text: text + '\n' + text, False)


if __name__ == '__main__':
    unittest.main()
