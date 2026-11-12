"""Protect user-owned Bob skills using only synthetic temporary project/home trees."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ('setup-agentic-scaffolding', 'scaffold-project', 'audit-project')


class BobInstallOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='bob install ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / 'project with spaces'
        self.project.mkdir()
        self.home = self.root / 'home'
        self.home.mkdir()
        self.skills = self.project / '.bob/skills'

    def run_install(self, *args, cwd=None):
        return subprocess.run(
            ['bash', str(ROOT / 'scripts/install-bob-skill.sh'), *map(str, args)],
            cwd=cwd or self.project, env={**os.environ, 'HOME': str(self.home)},
            capture_output=True, text=True, timeout=15,
        )

    def make_skill(self, target, name):
        target.mkdir(parents=True)
        (target / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: synthetic\n---\n')
        for part in ('templates', 'references'):
            (target / part).mkdir()
            (target / part / 'mine.txt').write_text(f'my {part}\n')

    def snapshot(self, root):
        return {str(p.relative_to(root)): ('link', os.readlink(p)) if p.is_symlink()
                else ('dir',) if p.is_dir() else ('file', p.read_bytes())
                for p in root.rglob('*')}

    def assert_refused(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Skipped', result.stderr)

    def test_foreign_skill_is_unchanged_and_later_skills_install(self):
        target = self.skills / SKILLS[0]
        self.make_skill(target, 'my-own-skill')
        before = self.snapshot(target)
        result = self.run_install(self.project)
        self.assert_refused(result)
        self.assertEqual(before, self.snapshot(target))
        for name in SKILLS[1:]:
            self.assertEqual((self.skills / name / 'SKILL.md').read_bytes(),
                             (ROOT / 'skills' / name / 'SKILL.md').read_bytes())

    def test_missing_manifest_and_plain_file_are_left_alone(self):
        target = self.skills / SKILLS[0]
        target.mkdir(parents=True)
        (target / 'mine.txt').write_text('keep me')
        plain = self.skills / SKILLS[1]
        plain.write_text('not a skill directory')
        result = self.run_install()
        self.assert_refused(result)
        self.assertEqual(self.snapshot(target), {'mine.txt': ('file', b'keep me')})
        self.assertEqual(plain.read_text(), 'not a skill directory')
        self.assertTrue((self.skills / SKILLS[2] / 'SKILL.md').is_file())

    def test_own_refresh_removes_stale_support_but_preserves_other_files(self):
        self.assertEqual(self.run_install().returncode, 0)
        target = self.skills / SKILLS[0]
        (target / 'personal-note.txt').write_text('keep me')
        for part in ('templates', 'references'):
            (target / part).mkdir(exist_ok=True)
            (target / part / 'stale.txt').write_text('obsolete')
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((target / 'personal-note.txt').read_text(), 'keep me')
        for part in ('templates', 'references'):
            self.assertFalse((target / part / 'stale.txt').exists())
        self.assertEqual((target / 'SKILL.md').read_bytes(),
                         (ROOT / 'skills' / SKILLS[0] / 'SKILL.md').read_bytes())

    def test_symlinked_skill_and_broken_link_are_not_followed_or_replaced(self):
        outside = self.root / 'checkout'
        self.make_skill(outside, SKILLS[0])
        before = self.snapshot(outside)
        self.skills.mkdir(parents=True)
        target = self.skills / SKILLS[0]
        target.symlink_to(outside, target_is_directory=True)
        broken = self.skills / SKILLS[1]
        broken.symlink_to(self.root / 'absent')
        self.assert_refused(self.run_install())
        self.assertEqual(before, self.snapshot(outside))
        self.assertTrue(target.is_symlink())
        self.assertTrue(broken.is_symlink())
        self.assertTrue((self.skills / SKILLS[2] / 'SKILL.md').is_file())

    def test_symlinked_manifest_is_not_overwritten(self):
        target = self.skills / SKILLS[0]
        target.mkdir(parents=True)
        outside = self.root / 'own-manifest.md'
        outside.write_text(f'---\nname: {SKILLS[0]}\n---\nprivate synthetic text\n')
        before = outside.read_bytes()
        (target / 'SKILL.md').symlink_to(outside)
        self.assert_refused(self.run_install())
        self.assertEqual(outside.read_bytes(), before)
        self.assertTrue((target / 'SKILL.md').is_symlink())
        self.assertTrue((self.skills / SKILLS[2] / 'SKILL.md').is_file())

    def test_symlinked_ancestors_do_not_redirect_installation(self):
        for parent in ('.bob', '.bob/skills'):
            with self.subTest(parent=parent):
                project = self.root / parent.replace('/', '-')
                project.mkdir()
                outside = self.root / (project.name + '-outside')
                outside.mkdir()
                (outside / 'sentinel').write_text('keep me')
                link = project / parent
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(outside, target_is_directory=True)
                before = self.snapshot(outside)
                self.assert_refused(self.run_install(project))
                self.assertEqual(before, self.snapshot(outside))
                self.assertTrue(link.is_symlink())

    def test_global_install_uses_redirected_home_and_preserves_foreign_skill(self):
        target = self.home / '.bob/skills' / SKILLS[0]
        self.make_skill(target, 'my-synthetic-global-skill')
        before = self.snapshot(target)
        self.assert_refused(self.run_install('--global'))
        self.assertEqual(before, self.snapshot(target))
        self.assertTrue((self.home / '.bob/skills' / SKILLS[2] / 'SKILL.md').is_file())
        self.assertFalse(self.skills.exists())

    def test_unreadable_manifest_is_left_unchanged_and_later_skills_install(self):
        target = self.skills / SKILLS[0]
        self.make_skill(target, SKILLS[0])
        manifest = target / 'SKILL.md'
        before = manifest.read_bytes()
        manifest.chmod(0)
        try:
            self.assertFalse(os.access(manifest, os.R_OK), 'test requires an unprivileged user')
            result = self.run_install()
            self.assert_refused(result)
        finally:
            manifest.chmod(0o600)
        self.assertEqual(manifest.read_bytes(), before)
        self.assertEqual((target / 'templates/mine.txt').read_text(), 'my templates\n')
        self.assertTrue((self.skills / SKILLS[2] / 'SKILL.md').is_file())

    def test_crlf_declaration_keeps_the_uninstaller_ownership_rule(self):
        target = self.skills / SKILLS[0]
        target.mkdir(parents=True)
        (target / 'SKILL.md').write_bytes(f'---\r\nname: {SKILLS[0]}  \r\n---\r\n'.encode())
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
