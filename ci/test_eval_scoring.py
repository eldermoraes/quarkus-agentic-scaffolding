"""Keep the pilot's mechanical rubric from awarding credit to unrelated text."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('pilot', Path(__file__).resolve().parent.parent / 'evals/skill-pilot/run.py')
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


class PilotScoringTests(unittest.TestCase):
    def test_score_domains_and_comments(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            java = root / 'src/main/java/org/acme/Service.java'
            java.parent.mkdir(parents=True)
            props = root / 'src/main/resources/application.properties'
            props.parent.mkdir(parents=True)
            props.write_text('# @RegisterAiService\nmodel.temperature=0\n')
            java.write_text('class Service {} // @RegisterAiService\n/* @InputGuardrails */\n')
            (root / 'pom.xml').write_text('<!-- <artifactId>langchain4j-embeddings-test</artifactId> -->')
            task = {'checks': ['ai_service', 'input_guardrail', 'zero_temperature', 'embedding_dependency']}
            self.assertEqual(pilot.score(root, task), {'ai_service': False, 'input_guardrail': False,
                                                      'zero_temperature': True, 'embedding_dependency': False})
            java.write_text('@RegisterAiService\n@InputGuardrails\ninterface Service {}')
            self.assertTrue(pilot.score(root, task)['ai_service'])
            self.assertTrue(pilot.score(root, task)['input_guardrail'])


if __name__ == '__main__':
    unittest.main()
