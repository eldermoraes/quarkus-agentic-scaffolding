"""Documentation failures must stop collection before invoking a model."""
import json
import os
from pathlib import Path
import sys
import tempfile
import subprocess
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'evals/skill-pilot'))
from preflight import PreflightError, probe


class PreflightTests(unittest.TestCase):
    def command(self, result):
        script = '''import json,sys
for line in sys.stdin:
 request=json.loads(line)
 if 'id' not in request: continue
 result={} if request['id']==1 else json.loads(sys.argv[1])
 print(json.dumps({'jsonrpc':'2.0','id':request['id'],'result':result}),flush=True)
'''
        return [sys.executable, '-c', script, json.dumps(result)]

    def test_success(self):
        probe(self.command({'content': [{'type': 'text', 'text': 'Documentation found'}]}),
              'docs', {}, os.environ.copy(), timeout=2)

    def test_error_and_quota_are_blocking(self):
        for result in ({'isError': True, 'content': []},
                       {'content': [{'text': 'Monthly quota exceeded'}]},
                       {'content': [{'text': 'Documentation unavailable: Docker or Podman, neither available'}]}):
            with self.subTest(result=result), self.assertRaises(PreflightError):
                probe(self.command(result), 'docs', {}, os.environ.copy(), timeout=2)

    def test_exited_launcher_does_not_leave_child_holding_stdout(self):
        with tempfile.TemporaryDirectory() as directory:
            pid_file = Path(directory) / 'child.pid'
            script = "import subprocess,sys; from pathlib import Path; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); Path(sys.argv[1]).write_text(str(p.pid))"
            started = time.monotonic()
            with self.assertRaises(PreflightError):
                probe([sys.executable, '-c', script, str(pid_file)], 'docs', {},
                      os.environ.copy(), timeout=2)
            self.assertLess(time.monotonic() - started, 5)
            self.assertTrue(pid_file.exists(), 'child fixture must start before probe times out')
            pid = pid_file.read_text()
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                state = subprocess.run(['ps', '-o', 'stat=', '-p', pid], capture_output=True, text=True).stdout.strip()
                if not state or state.startswith('Z'):
                    break
                time.sleep(0.05)
            self.assertTrue(not state or state.startswith('Z'), f'child {pid} still running')


if __name__ == '__main__':
    unittest.main()
