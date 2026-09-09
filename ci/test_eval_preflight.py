"""Documentation failures must stop collection before invoking a model."""
import json
import os
from pathlib import Path
import sys
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


if __name__ == '__main__':
    unittest.main()
