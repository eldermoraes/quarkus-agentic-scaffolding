"""Keep the effectiveness eval's mechanical rubric honest: markers count only in live code."""
from pathlib import Path
import sys
import tempfile
import unittest

EVAL = Path(__file__).resolve().parent.parent / 'evals/effectiveness'
sys.path.insert(0, str(EVAL))
import run  # noqa: E402
import score  # noqa: E402
import summarize  # noqa: E402

POM = '''<project><dependencyManagement><dependencies>
<dependency><groupId>io.quarkus.platform</groupId><artifactId>${quarkus.platform.artifact-id}</artifactId><version>3.40.1</version><scope>import</scope></dependency>
<dependency><groupId>io.quarkus.platform</groupId><artifactId>quarkus-langchain4j-bom</artifactId><version>3.40.1</version><scope>import</scope></dependency>
</dependencies></dependencyManagement>
<properties><maven.compiler.release>25</maven.compiler.release><quarkus.platform.artifact-id>quarkus-bom</quarkus.platform.artifact-id></properties>
<dependencies><dependency><groupId>io.quarkiverse.langchain4j</groupId><artifactId>quarkus-langchain4j-easy-rag</artifactId></dependency>
<dependency><groupId>dev.langchain4j</groupId><artifactId>langchain4j-embeddings-bge-small-en-v15-q</artifactId></dependency></dependencies>
<build><plugins><plugin><artifactId>maven-compiler-plugin</artifactId><version>3.16.0</version>
<configuration><parameters>true</parameters></configuration></plugin></plugins></build>
<profiles><profile><id>native</id></profile></profiles></project>'''

SERVICE = '''package org.acme.ai;
// @InputGuardrails in a comment earns nothing
/* @Timeout @Fallback */
@RegisterAiService(modelName = "classifier", tools = OrderTools.class)
public interface Classifier {
    @UserMessage("""
        Classify the ticket. <ticket>{text}</ticket>
        """)
    Category classify(String text);
}
enum Category { BILLING, TECHNICAL, OTHER }
record Request(String text) {}
'''


class EffectivenessScoringTests(unittest.TestCase):
    def project(self, root, java=SERVICE, props='', pom=POM):
        (root / 'app/src/main/java/org/acme/ai').mkdir(parents=True)
        (root / 'app/src/main/resources/rag').mkdir(parents=True)
        (root / 'app/src/main/java/org/acme/ai/Classifier.java').write_text(java)
        (root / 'app/src/main/resources/application.properties').write_text(props)
        (root / 'app/pom.xml').write_text(pom)
        return score.find_project(root)

    def test_live_markers_count_and_comments_do_not(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(Path(directory), props=(
                '# quarkus.langchain4j.devservices.enabled=false\n'
                'quarkus.langchain4j.ollama.classifier.chat-model.temperature=0\n'
                '%dev.quarkus.langchain4j.log-requests=true\n'))
            result = score.score(project, ['ai_service', 'named_model', 'llm_tools_wired', 'delimited_input',
                                           'enum_result', 'record_dto', 'input_guardrail', 'fault_tolerance',
                                           'devservices_off', 'zero_temperature', 'dev_logging', 'no_manual_wiring'])
            self.assertEqual(result, {'ai_service': True, 'named_model': True, 'llm_tools_wired': True,
                                      'delimited_input': True, 'enum_result': True, 'record_dto': True,
                                      'input_guardrail': False, 'fault_tolerance': False,
                                      'devservices_off': False, 'zero_temperature': True,
                                      'dev_logging': True, 'no_manual_wiring': True})

    def test_generator_band_and_rag_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = self.project(root, props='quarkus.langchain4j.easy-rag.path=src/main/resources/rag\n')
            names = ['dual_bom', 'no_extension_version_pins', 'java_release_25', 'parameters_flag',
                     'native_profile', 'easy_rag_extension', 'easy_rag_path', 'embedding_dependency',
                     'sample_document']
            result = score.score(project, names)
            self.assertEqual(result['sample_document'], False)
            (root / 'app/src/main/resources/rag/guide.md').write_text('# Guide\n')
            self.assertTrue(all(score.score(project, names).values()))
            (root / 'app/docs').mkdir()
            (root / 'app/docs/a.md').write_text('# A\n')
            (root / 'app/src/main/resources/application.properties').write_text(
                'quarkus.langchain4j.easy-rag.path=${DOCS_PATH:docs}\n')
            (root / 'app/src/main/resources/rag/guide.md').unlink()
            self.assertTrue(score.score(project, ['sample_document'])['sample_document'])
            pinned = POM.replace('langchain4j-easy-rag</artifactId>', 'langchain4j-easy-rag</artifactId><version>1.0</version>')
            (root / 'app/pom.xml').write_text(pinned)
            self.assertFalse(score.score(project, ['no_extension_version_pins'])['no_extension_version_pins'])

    def test_manual_wiring_and_missing_project(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(Path(directory), java=SERVICE + 'class X { ChatModel model; }\n')
            self.assertFalse(score.score(project, ['no_manual_wiring'])['no_manual_wiring'])
        self.assertEqual(score.score(None, ['ai_service']), {'ai_service': False})

    def test_tasks_reference_known_checks_and_schedule_is_balanced(self):
        spec = run.load_tasks()
        runs = run.schedule(spec, set(), 3)
        self.assertEqual(len(runs), 30)
        self.assertEqual(sum(r['arm'] == 'skill' for r in runs), 15)
        self.assertEqual([r['arm'] for r in runs[:2]], ['baseline', 'skill'])
        self.assertEqual([r['arm'] for r in runs[10:12]], ['skill', 'baseline'])

    def test_isolation_assertion(self):
        init = {'skills': ['simplify'], 'plugins': [{'name': 'cc-plugin-telemetry'}]}
        self.assertTrue(run.isolation('baseline', init)[0])
        self.assertFalse(run.isolation('skill', init)[0])
        init['skills'].append('quarkus-agentic-scaffolding:scaffold-project')
        self.assertFalse(run.isolation('baseline', init)[0])
        self.assertTrue(run.isolation('skill', init)[0])

    def test_summary_excludes_invalid_runs(self):
        base = {'compiles_first_attempt': True, 'compiles_within_two': True, 'build_attempts_to_green': 1,
                'conformance': {'a': True, 'b': False}, 'generator': {'g': True}, 'agent_seconds': 60}
        records = [dict(base, run='t-r1-baseline', task='t', arm='baseline', status='completed', isolation_ok=True),
                   dict(base, run='t-r1-skill', task='t', arm='skill', status='completed', isolation_ok=True,
                        conformance={'a': True, 'b': True}),
                   dict(base, run='t-r2-skill', task='t', arm='skill', status='invalid_isolation', isolation_ok=False)]
        summary = summarize.summarize(records)
        self.assertEqual(summary['valid'], 2)
        self.assertEqual(summary['delta']['conformance_pp'], 50.0)
        self.assertEqual(summary['overall']['skill']['n'], 1)


    def test_claude_md_option_changes_only_setting_sources(self):
        from types import SimpleNamespace
        output = Path('/tmp/eval-out')
        for flag, sources in ((False, ''), (True, 'project')):
            args = SimpleNamespace(model='m', with_claude_md=flag)
            for arm in run.ARMS:
                command = run.claude_command(args, output, arm, 'p')
                self.assertEqual(command[command.index('--setting-sources') + 1], sources)
                self.assertEqual('--plugin-dir' in command, arm == 'skill')


if __name__ == '__main__':
    unittest.main()
