from pathlib import Path
import subprocess
import tempfile
import unittest


class ScopeGuardTest(unittest.TestCase):
    def run_guard(self, changed_file=None, scope="-s project", missing_server=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ci").mkdir()
            (root / "skills/setup-agentic-scaffolding").mkdir(parents=True)
            guard = root / "ci/check-mcp-command-consistency.sh"
            guard.write_bytes(Path(__file__).with_name(guard.name).read_bytes())
            (root / "gemini-extension.json").write_text("{}")
            for name in ("README.md", "skills/setup-agentic-scaffolding/SKILL.md"):
                selected = scope if name == changed_file else "-s project"
                commands = f"gemini mcp add {selected} quarkus-agent jbang --java 21+ io.quarkus:quarkus-agent-mcp:1.2.6:runner\n"
                if not (missing_server and name == changed_file):
                    commands += f"gemini mcp add {selected} context7 npx -y @upstash/context7-mcp@4.0.6\n"
                commands += "Use `-s user` instead for all projects.\n"
                (root / name).write_text(commands)
            return subprocess.run(["bash", str(guard)], capture_output=True, text=True)

    def test_project_examples_and_user_alternative_pass(self):
        result = self.run_guard()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_scope_drift_and_missing_examples_fail_on_either_surface(self):
        for name in ("README.md", "skills/setup-agentic-scaffolding/SKILL.md"):
            for scope in ("", "-s user"):
                with self.subTest(name=name, scope=scope):
                    self.assertNotEqual(self.run_guard(name, scope).returncode, 0)
            with self.subTest(name=name, missing=True):
                self.assertNotEqual(self.run_guard(name, missing_server=True).returncode, 0)
