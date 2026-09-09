"""Bob's fallback installation includes and refreshes on-demand instructions."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class BobReferenceTests(unittest.TestCase):
    def test_install_and_refresh_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            command = ['bash', str(ROOT / 'scripts/install-bob-skill.sh'), directory]
            subprocess.run(command, check=True, capture_output=True)
            source = ROOT / 'skills/setup-agentic-scaffolding/references/bob-mcp.md'
            installed = Path(directory) / '.bob/skills/setup-agentic-scaffolding/references/bob-mcp.md'
            self.assertEqual(installed.read_bytes(), source.read_bytes())
            installed.write_text('stale instructions')
            stale = installed.parent / 'obsolete.md'
            stale.write_text('obsolete')
            subprocess.run(command, check=True, capture_output=True)
            self.assertEqual(installed.read_bytes(), source.read_bytes())
            self.assertFalse(stale.exists())


if __name__ == '__main__':
    unittest.main()
