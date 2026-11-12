"""The opencode registration form (a `local` entry whose `command` is one array) is pinned and
bumped like every other published registration: the command consistency check counts it, and
Renovate's custom managers match both pins inside it."""
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SKILL = "skills/setup-agentic-scaffolding/SKILL.md"


def opencode_entry(java_pin=True):
    quarkus = ["jbang"] + (["--java", "21+"] if java_pin else []) + [
        "io.quarkus:quarkus-agent-mcp:1.2.6:runner"]
    return json.dumps({"mcp": {
        "quarkus-agent": {"type": "local", "command": quarkus},
        "context7": {"type": "local", "command": ["npx", "-y", "@upstash/context7-mcp@4.0.6"]},
    }}, indent=2)


class OpencodeFormTest(unittest.TestCase):
    def run_guard(self, java_pin):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ci").mkdir()
            (root / "skills/setup-agentic-scaffolding").mkdir(parents=True)
            guard = root / "ci/check-mcp-command-consistency.sh"
            guard.write_bytes((ROOT / "ci" / guard.name).read_bytes())
            (root / "gemini-extension.json").write_text("{}")
            gemini = ("gemini mcp add -s project quarkus-agent jbang --java 21+ "
                      "io.quarkus:quarkus-agent-mcp:1.2.6:runner\n"
                      "gemini mcp add -s project context7 npx -y @upstash/context7-mcp@4.0.6\n")
            (root / "README.md").write_text(gemini)
            (root / SKILL).write_text(gemini + "\n```json\n" + opencode_entry(java_pin) + "\n```\n")
            return subprocess.run(["bash", str(guard)], capture_output=True, text=True)

    def test_pinned_opencode_form_passes_and_is_counted(self):
        result = self.run_guard(java_pin=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        # Two Gemini commands plus the multi-line opencode array.
        self.assertIn("OK: 3 MCP registrations", result.stdout)

    def test_opencode_form_without_java_pin_fails(self):
        result = self.run_guard(java_pin=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing the `--java 21+` JDK pin", result.stderr)
        self.assertIn(SKILL, result.stderr)

    def test_renovate_bumps_both_pins_in_opencode_form(self):
        config = json.loads((ROOT / "renovate.json").read_text())
        entry = opencode_entry()
        found = {}
        for manager in config["customManagers"]:
            if not any(re.search(p.strip("/"), SKILL) for p in manager["managerFilePatterns"]):
                continue
            for pattern in manager["matchStrings"]:
                for match in re.finditer(pattern.replace("(?<", "(?P<"), entry):
                    found[manager.get("depNameTemplate")] = match.group("currentValue")
        self.assertEqual(found, {"io.quarkus:quarkus-agent-mcp": "1.2.6",
                                 "@upstash/context7-mcp": "4.0.6"})


if __name__ == "__main__":
    unittest.main()
