"""Run the fixed twelve-attempt Codex pilot; raw logs stay outside the repository."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

from preflight import check as check_documentation

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
PATTERNS = {
    'ai_service': r'@RegisterAiService\b',
    'enum': r'\benum\s+\w+',
    'record': r'\brecord\s+\w+',
    'named_model': r'modelName\s*=\s*"[^"\n]+"',
    'zero_temperature': r'(?m)^\s*[^#\n]*temperature\s*=\s*0(?:\.0)?\s*$',
    'input_guardrail': r'@InputGuardrails\b',
    'delimited_input': r'<([a-zA-Z]+)>[\s\S]*?</\1>',
    'virtual_threads': r'@RunOnVirtualThread\b|Thread\.startVirtualThread\s*\(',
    'fault_tolerance': r'@Timeout\b[\s\S]*@Fallback\b|@Fallback\b[\s\S]*@Timeout\b',
    'parallel_agent': r'@ParallelAgent\b|@ParallelMapperAgent\b',
    'agent_annotation': r'@Agent\s*\(',
    'agentic_scope': r'\bAgenticScope\b',
    'easy_rag_path': r'(?m)^\s*quarkus\.langchain4j\.easy-rag\.path\s*=\s*\S+',
    'embedding_dependency': r'<artifactId>\s*langchain4j-embeddings-[^<]+</artifactId>',
}


def score(project, task):
    java = '\n'.join(path.read_text() for path in sorted(project.glob('src/main/java/**/*.java')))
    # Mechanical presence checks, not semantic correctness claims. Exclude Java comments.
    java = re.sub(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/',
                  lambda match: '' if match[0].startswith(('//', '/*')) else match[0],
                  java, flags=re.S)
    props = '\n'.join(path.read_text() for path in project.glob('src/main/resources/*.properties'))
    results = {}
    for item in task['checks']:
        if item == 'sample_document':
            results[item] = any(p.is_file() and p.stat().st_size for p in project.glob('**/docs/*'))
        elif item == 'embedding_dependency':
            results[item] = bool(re.search(PATTERNS[item], re.sub(r'<!--.*?-->', '', (project / 'pom.xml').read_text(), flags=re.S)))
        else:
            results[item] = bool(re.search(PATTERNS[item], props if item in ('zero_temperature', 'easy_rag_path') else java))
    return results


def execute(command, cwd, stdout, stderr, timeout, env):
    with stdout.open('w') as out, stderr.open('w') as err:
        try:
            process = subprocess.Popen(command, cwd=cwd, stdout=out, stderr=err,
                                       env=env, start_new_session=True)
        except OSError as error:
            err.write(str(error))
            return 127, False
        try:
            return process.wait(timeout=timeout), False
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            return process.returncode, True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='New directory outside the repository')
    parser.add_argument('--timeout', type=int, default=900)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == REPO or REPO in output.parents or output.exists():
        parser.error('output must be a new directory outside the repository')
    tracked_roots = ['evals/skill-pilot', 'skills/scaffold-project', 'AGENTS.md']
    if subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', *tracked_roots], cwd=REPO).returncode:
        parser.error('commit changes to pilot inputs before collecting')
    output.mkdir(parents=True)
    # Copy only tracked bytes from the recorded revision, never mutable working-tree inputs.
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', revision, '--',
                                     *tracked_roots], cwd=REPO, text=True).splitlines()
    snapshot = output / 'inputs'
    hashes = {}
    for name in paths:
        data = subprocess.check_output(['git', 'show', f'{revision}:{name}'], cwd=REPO)
        destination = snapshot / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    pilot_inputs = snapshot / 'evals/skill-pilot'
    tasks = json.loads((pilot_inputs / 'tasks.json').read_text())
    env = os.environ.copy()
    for name in list(env):
        if any(word in name.upper() for word in ('API_KEY', 'SECRET', 'TOKEN')):
            env.pop(name)
    common = ['--enable', 'skip_host_skill_discovery', '--disable', 'plugins',
              '-c', 'model="gpt-6-astra"', '-c', 'model_reasoning_effort="low"',
              '-c', 'approval_policy="never"', '-c', 'forced_login_method="chatgpt"',
              '-c', 'mcp_servers.quarkus-agent.command="jbang"',
              '-c', 'mcp_servers.quarkus-agent.args=["--java","21+","io.quarkus:quarkus-agent-mcp:1.2.6:runner"]',
              '-c', 'mcp_servers.context7.command="npx"',
              '-c', 'mcp_servers.context7.args=["-y","@upstash/context7-mcp@4.0.6"]']
    metadata = {'model': 'gpt-6-astra', 'reasoning': 'low', 'timeout_seconds': args.timeout,
                'codex': subprocess.check_output(['codex', '--version'], text=True).strip(),
                'source_commit': revision, 'input_sha256': hashes,
                'tasks_sha256': hashlib.sha256((HERE / 'tasks.json').read_bytes()).hexdigest(),
                'compile_command': ['mvn', '-B', '-ntp', '-DskipTests', 'test-compile']}
    (output / 'environment.json').write_text(json.dumps(metadata, indent=2)+'\n')
    try:
        check_documentation(pilot_inputs / 'starter', env)
    except (OSError, RuntimeError) as error:
        (output / 'preflight.json').write_text(json.dumps({'collection_started': False,
                                                        'error': str(error)}, indent=2)+'\n')
        parser.exit(1, f'Collection not started: {error}\n')
    (output / 'preflight.json').write_text('{"collection_started": true}\n')
    results = []
    for task in tasks:
        for repetition in (1, 2):
            arms = ('baseline', 'skill') if repetition == 1 else ('skill', 'baseline')
            for arm in arms:
                run_id = f"{task['id']}-{repetition}-{arm}"
                run = output / run_id
                project = run / 'project'
                shutil.copytree(pilot_inputs / 'starter', project, ignore=shutil.ignore_patterns('target', '.git'))
                shutil.copyfile(snapshot / 'AGENTS.md', project / 'AGENTS.md')
                subprocess.run(['git', 'init', '-q'], cwd=project, check=True)
                if arm == 'skill':
                    shutil.copytree(snapshot / 'skills/scaffold-project', project / '.agents/skills/scaffold-project')
                treatment = ('Read .agents/skills/scaffold-project/SKILL.md and apply it; its templates are available.'
                             if arm == 'skill' else 'No scaffolding skill is supplied. Work without external skills or templates.')
                prompt = ("Implement the following component in the supplied project. This is a controlled maintenance evaluation. "
                          "Use only this project, the supplied conventions, and the two MCP servers for framework documentation. "
                          "Do not access other skills, other evaluation runs, or this repository's source outside this project. "
                          "Superpowers is disabled by the maintainer for this run. All project edits and checks are authorized. "
                          "Do not install tools, start containers or a live model, commit, push, or publish anything. "
                          "Check Quarkus MCP reachability and use Context7 for external APIs. "
                          "The supplied POM is fixed starter infrastructure; add dependencies only when needed. "
                          + treatment + '\n\n' + task['prompt'])
                (run / 'prompt.txt').write_text(prompt)
                start = time.monotonic()
                print(f'Starting {run_id}', flush=True)
                code, timed_out = execute(['codex', 'exec', '--ignore-user-config', '--ephemeral',
                                           '--json', '--sandbox', 'danger-full-access', *common, prompt],
                                          project, run / 'events.jsonl', run / 'stderr.log', args.timeout, env)
                compile_code, compile_timeout = execute(metadata['compile_command'], project,
                                                       run / 'compile.log', run / 'compile-stderr.log', 240, env)
                usage = None
                errors = 0
                for line in (run / 'events.jsonl').read_text().splitlines():
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if event.get('type') == 'turn.completed':
                        usage = event.get('usage')
                    item = event.get('item', {})
                    if item.get('type') == 'command_execution' and item.get('exit_code') not in (None, 0):
                        errors += 1
                scoring_error = None
                try:
                    checks = score(project, task)
                except (OSError, UnicodeError, ValueError) as error:
                    checks = {item: False for item in task['checks']}
                    scoring_error = type(error).__name__
                generated_java = any(project.glob('src/main/java/**/*.java'))
                result = {'run': run_id, 'task': task['id'], 'repetition': repetition, 'arm': arm,
                          'agent_exit': code, 'timed_out': timed_out, 'compile_exit': compile_code,
                          'compile_timed_out': compile_timeout,
                          'generated_java': generated_java,
                          'successful_generation': code == 0 and not timed_out and generated_java and compile_code == 0,
                          'scoring_error': scoring_error,
                          'infrastructure_error': code == 127 or compile_code == 127,
                          'elapsed_seconds': round(time.monotonic()-start,1),
                          'checks': checks, 'usage': usage, 'failed_shell_commands': errors}
                results.append(result)
                (output / 'results.json').write_text(json.dumps(results, indent=2)+'\n')
                print(f"Finished {run_id}: compile={compile_code}, checks={sum(result['checks'].values())}/8", flush=True)


if __name__ == '__main__':
    main()
