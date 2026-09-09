import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from check_mcp_java_floor import probe, runner_coordinate


class JavaFloorTest(unittest.TestCase):
    def command(self, response, wait=False):
        program = "import sys,time; sys.stdin.readline(); "
        program += f"print({json.dumps(json.dumps(response))}, flush=True); "
        if wait:
            program += "time.sleep(30)"
        return [sys.executable, "-u", "-c", program]

    def test_valid_initialize(self):
        info = {"name": "quarkus-agent", "version": "fixture"}
        result = {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": info}
        self.assertEqual(probe(self.command({"jsonrpc": "2.0", "id": 1, "result": result}, True), 2), info)

    def test_false_positive_responses_fail(self):
        for response in ({"jsonrpc": "2.0", "id": 1, "error": {"code": -1}},
                         {"jsonrpc": "2.0", "id": 1, "result": {}},
                         {"jsonrpc": "2.0", "id": 99, "result": {}}, ["not a response"]):
            with self.subTest(response=response), self.assertRaises(RuntimeError):
                probe(self.command(response), 1)

    def test_early_exit_reports_stderr(self):
        with self.assertRaisesRegex(RuntimeError, "fixture startup failure"):
            probe([sys.executable, "-c", "import sys; print('fixture startup failure', file=sys.stderr)"], 1)

    def test_timeout_cleans_up_child_process(self):
        with tempfile.TemporaryDirectory() as directory:
            pidfile = Path(directory) / "pid"
            script = ("import subprocess,sys,time; sys.stdin.readline(); "
                      "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
                      f"open({str(pidfile)!r},'w').write(str(child.pid)); time.sleep(30)")
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                probe([sys.executable, "-c", script], 0.5)
            # A killed child may briefly remain a zombie until the OS reaps it.
            result = subprocess.run(["ps", "-o", "stat=", "-p", pidfile.read_text()],
                                    capture_output=True, text=True)
            self.assertTrue(not result.stdout.strip() or result.stdout.strip().startswith("Z"))

    def test_coordinate_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.json"
            for coordinate, valid in (("io.quarkus:quarkus-agent-mcp:1.2.6:runner", True),
                                      ("https://example.com/code.java", False)):
                manifest.write_text(json.dumps({"mcpServers": {"quarkus-agent": {"args": [coordinate]}}}))
                if valid:
                    self.assertEqual(runner_coordinate(manifest), coordinate)
                else:
                    with self.assertRaises(ValueError):
                        runner_coordinate(manifest)
