"""Keep the Codex marketplace payload self-contained and installable."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
SKILLS = {'setup-agentic-scaffolding', 'scaffold-project', 'audit-project'}


class CodexDistributionTests(unittest.TestCase):
    def test_marketplace_payload_contains_the_root_plugin(self):
        manifest = json.loads((ROOT / '.codex-plugin/plugin.json').read_text())
        marketplace = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text())
        entry, = marketplace['plugins']
        self.assertEqual(entry['name'], manifest['name'])
        self.assertEqual(entry['source']['source'], 'local')
        source = (ROOT / entry['source']['path']).resolve()

        with tempfile.TemporaryDirectory() as directory:
            installed = Path(directory) / 'plugin'
            for name in ('.codex-plugin', 'skills', 'assets'):
                payload = source / name
                self.assertTrue(payload.resolve().is_relative_to(source), name)
                self.assertFalse(payload.is_symlink(), name)
                shutil.copytree(payload, installed / name, symlinks=False)
            self.assertEqual(
                json.loads((installed / '.codex-plugin/plugin.json').read_text()), manifest)
            for root in (ROOT, installed):
                with self.subTest(root=root):
                    icon = (root / manifest['interface']['composerIcon']).resolve()
                    self.assertTrue(icon.is_relative_to(root.resolve()))
                    self.assertLess(icon.stat().st_size, 50 * 1024)
                    svg = ET.parse(icon).getroot()
                    self.assertEqual(svg.tag, '{http://www.w3.org/2000/svg}svg')
                    self.assertEqual(svg.attrib['viewBox'], '0 0 512 512')
                    self.assertEqual(icon.read_bytes(),
                                     (ROOT / manifest['interface']['composerIcon']).read_bytes())
                    skills = (root / manifest['skills']).resolve()
                    self.assertTrue(skills.is_relative_to(root.resolve()))
                    self.assertEqual(
                        {p.name for p in skills.iterdir() if p.is_dir()}, SKILLS)
                    for name in SKILLS:
                        self.assertTrue((skills / name / 'SKILL.md').is_file())

            expected = {p.relative_to(ROOT / 'skills'): p.read_bytes()
                        for p in (ROOT / 'skills').rglob('*') if p.is_file()}
            actual = {p.relative_to(installed / 'skills'): p.read_bytes()
                      for p in (installed / 'skills').rglob('*') if p.is_file()}
            self.assertEqual(actual, expected)
            self.assertFalse(any(p.is_symlink() for p in installed.rglob('*')))

    @unittest.skipUnless(shutil.which('codex'), 'Codex CLI is needed for the install smoke test')
    def test_real_codex_install_contains_skills_and_icon(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            marketplace = directory / 'marketplace'
            for name in ('.agents/plugins', '.codex-plugin', 'skills', 'assets', 'plugins'):
                shutil.copytree(ROOT / name, marketplace / name, symlinks=True)
            home = directory / 'codex-home'
            home.mkdir()
            env = {**os.environ, 'CODEX_HOME': str(home)}

            def codex(*args):
                result = subprocess.run(
                    ['codex', 'plugin', *args, '--json'], env=env,
                    cwd=directory, capture_output=True, text=True, timeout=60)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)

            codex('marketplace', 'add', str(marketplace))
            result = codex('add', 'quarkus-agentic-scaffolding@eldermoraes')
            installed = Path(result['installedPath'])
            self.assertEqual(
                (installed / '.codex-plugin/plugin.json').read_bytes(),
                (ROOT / '.codex-plugin/plugin.json').read_bytes())
            self.assertEqual((installed / 'assets/icon.svg').read_bytes(),
                             (ROOT / 'assets/icon.svg').read_bytes())
            expected = {p.relative_to(ROOT / 'skills'): p.read_bytes()
                        for p in (ROOT / 'skills').rglob('*') if p.is_file()}
            actual = {p.relative_to(installed / 'skills'): p.read_bytes()
                      for p in (installed / 'skills').rglob('*') if p.is_file()}
            self.assertEqual(actual, expected)

    def test_external_actions_are_pinned_to_full_commits(self):
        uses = re.compile(r'^\s*(?:-\s+)?uses:\s+(\S+)', re.MULTILINE)
        found = 0
        for workflow in (ROOT / '.github').rglob('*.yml'):
            for reference in uses.findall(workflow.read_text()):
                if reference.startswith('./'):
                    continue
                with self.subTest(workflow=workflow.name, reference=reference):
                    self.assertRegex(reference, r'^[^@\s]+@[0-9a-f]{40}$')
                    found += 1
        self.assertGreater(found, 0)


if __name__ == '__main__':
    unittest.main()
