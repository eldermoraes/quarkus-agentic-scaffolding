"""Run the skill-effectiveness eval: fixed tasks x {baseline, skill} x repetitions with `claude -p`.

Every run starts in an empty directory outside this repository. Both arms get the same prompt,
model, MCP servers and permissions; the skill arm additionally loads a plugin that contains only
the `scaffold-project` skill (with its templates) from the committed revision. With
`--with-claude-md`, both arms also find the repository's `CLAUDE.md` (and `AGENTS.md`, when
`CLAUDE.md` references it) from the same revision in their working directory, loaded through
`--setting-sources project`; without the flag no settings or memory files load. Raw transcripts,
generated projects and compile logs stay in the output directory; `summarize.py` aggregates them.
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import score  # noqa: E402

ARMS = ('baseline', 'skill')
PLUGIN_NAME = 'quarkus-agentic-scaffolding'
COMPILE = ['mvn', '-B', '-ntp', '-DskipTests', 'test-compile']
CONTEXT_FILE = 'CLAUDE.md'
# Tools are pre-approved so a headless run never waits on a prompt; edits are confined to the
# run directory by acceptEdits. Anything else is denied, identically in both arms.
ALLOWED_TOOLS = ['Read', 'Write', 'Edit', 'Glob', 'Grep', 'Skill', 'TodoWrite', 'WebSearch', 'WebFetch',
                 'mcp__quarkus-agent', 'mcp__context7',
                 'Bash(mvn:*)', 'Bash(./mvnw:*)', 'Bash(mvnw:*)', 'Bash(git:*)', 'Bash(ls:*)',
                 'Bash(mkdir:*)', 'Bash(cat:*)', 'Bash(find:*)', 'Bash(grep:*)', 'Bash(head:*)',
                 'Bash(tail:*)', 'Bash(cd:*)', 'Bash(pwd)', 'Bash(java:*)', 'Bash(jbang:*)',
                 'Bash(cp:*)', 'Bash(mv:*)', 'Bash(rm:*)', 'Bash(echo:*)', 'Bash(sed:*)', 'Bash(wc:*)']
RATE_LIMIT = re.compile(r'usage limit|rate limit|limit reached|limit will reset|\b429\b', re.I)
BUILD_COMMAND = re.compile(r'(?:^|[\s;&|/])(?:mvn|mvnw|gradle|gradlew|quarkus)\b')


def mcp_pins():
    """Read the published MCP pins from the README so the eval follows Renovate bumps."""
    readme = (REPO / 'README.md').read_text()
    quarkus = re.search(r'io\.quarkus:quarkus-agent-mcp:([0-9][^\s:`"]*):runner', readme).group(1)
    context7 = re.search(r'@upstash/context7-mcp@([0-9][^\s`"]*)', readme).group(1)
    return quarkus, context7


def load_tasks():
    spec = json.loads((HERE / 'tasks.json').read_text())
    for task in spec['tasks']:
        for name in spec['common_checks'] + task['checks'] + spec['generator_checks']:
            if name not in score.CHECKS:
                raise SystemExit(f'unknown check {name} in task {task["id"]}')
    return spec


def schedule(spec, task_ids, repetitions):
    """Deterministic order; the arm order alternates per repetition to spread drift evenly."""
    runs = []
    for repetition in range(1, repetitions + 1):
        for task in spec['tasks']:
            if task_ids and task['id'] not in task_ids:
                continue
            arms = ARMS if repetition % 2 else tuple(reversed(ARMS))
            for arm in arms:
                runs.append({'id': f"{task['id']}-r{repetition}-{arm}", 'task': task,
                             'repetition': repetition, 'arm': arm})
    return runs


def prompt_for(spec, task):
    return spec['preamble'].replace('{artifact}', task['artifact']) + '\n\nTask: ' + task['prompt']


def setting_sources(args):
    """'' loads no settings and no memory files; 'project' loads the CLAUDE.md placed in the run
    directory (the run directory has no .claude/ folder, so no project settings come with it)."""
    return 'project' if args.with_claude_md else ''


def claude_command(args, output, arm, prompt, resume=None):
    command = ['claude', '-p', prompt, '--model', args.model, '--output-format', 'stream-json',
               '--verbose', '--setting-sources', setting_sources(args), '--strict-mcp-config',
               '--mcp-config', str(output / 'mcp.json'), '--permission-mode', 'acceptEdits',
               '--allowedTools', ','.join(ALLOWED_TOOLS)]
    if arm == 'skill':
        command += ['--plugin-dir', str(output / 'plugin')]
    if resume:
        command += ['--resume', resume]
    return command


def clean_env(port):
    env = {k: v for k, v in os.environ.items()
           if not any(word in k.upper() for word in ('API_KEY', 'SECRET', 'TOKEN'))}
    env.pop('CLAUDECODE', None)
    env['QUARKUS_HTTP_PORT'] = str(port)       # parallel dev-mode instances must not share 8080
    env['QUARKUS_HTTP_TEST_PORT'] = '0'
    return env


def execute(command, cwd, log, timeout, env):
    """Run in a new process group; on timeout kill the whole group. Returns (exit, timed_out, secs)."""
    start = time.monotonic()
    with open(log, 'w') as out:
        try:
            process = subprocess.Popen(command, cwd=cwd, stdout=out, stderr=subprocess.STDOUT,
                                       stdin=subprocess.DEVNULL, env=env, start_new_session=True)
        except OSError as error:
            out.write(str(error))
            return 127, False, 0.0
        try:
            code, timed_out = process.wait(timeout=timeout), False
        except subprocess.TimeoutExpired:
            code, timed_out = None, True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        process.wait()
        return (process.returncode if code is None else code), timed_out, round(time.monotonic() - start, 1)


def reap(workdir):
    """Kill anything still running from the run directory (e.g. a dev mode started by the MCP)."""
    subprocess.run(['pkill', '-9', '-f', str(workdir)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def parse_transcript(path):
    info = {'init': None, 'result': None, 'tool_calls': 0, 'skill_invocations': [], 'build_commands': 0,
            'failed_build_commands': 0, 'failed_tool_calls': 0, 'quarkus_mcp_calls': 0, 'context7_calls': 0}
    pending = {}
    for line in Path(path).read_text(errors='replace').splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get('type') == 'system' and event.get('subtype') == 'init' and info['init'] is None:
            info['init'] = event
        elif event.get('type') == 'result':
            info['result'] = event
        message = event.get('message')
        content = message.get('content') if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get('type') == 'tool_use':
                info['tool_calls'] += 1
                name, data = block.get('name', ''), block.get('input') or {}
                build = name == 'Bash' and bool(BUILD_COMMAND.search(str(data.get('command', ''))))
                pending[block.get('id')] = build
                if name == 'Skill':
                    info['skill_invocations'].append(str(data.get('skill') or data.get('command') or data))
                if build:
                    info['build_commands'] += 1
                if name.startswith('mcp__quarkus-agent__'):
                    info['quarkus_mcp_calls'] += 1
                if name.startswith('mcp__context7__'):
                    info['context7_calls'] += 1
            elif block.get('type') == 'tool_result' and block.get('is_error'):
                info['failed_tool_calls'] += 1
                if pending.get(block.get('tool_use_id')):
                    info['failed_build_commands'] += 1
    return info


def isolation(arm, init):
    """Baseline must not see the skill; the skill arm must see it. Checked on the init event."""
    if init is None:
        return False, 'no init event'
    names = [str(n) for n in (init.get('skills') or []) + (init.get('slash_commands') or [])]
    names += [str(p.get('name', p)) if isinstance(p, dict) else str(p) for p in init.get('plugins') or []]
    found = any('scaffold' in n or 'quarkus-agentic' in n for n in names)
    if arm == 'baseline' and found:
        return False, 'scaffolding skill visible in baseline'
    if arm == 'skill' and not found:
        return False, 'scaffolding skill not loaded in skill arm'
    return True, None


def run_one(args, spec, output, run, port, stop):
    task, arm = run['task'], run['arm']
    folder = output / 'runs' / run['id']
    workdir = folder / 'work'
    workdir.mkdir(parents=True)
    context_files = sorted(p.name for p in (output / 'context').iterdir()) if args.with_claude_md else []
    for name in context_files:
        shutil.copyfile(output / 'context' / name, workdir / name)
    env = clean_env(port)
    record = {'run': run['id'], 'task': task['id'], 'repetition': run['repetition'], 'arm': arm,
              'model': args.model, 'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'with_claude_md': args.with_claude_md, 'context_files': context_files,
              'setting_sources': setting_sources(args)}
    if stop.is_set():
        record['status'] = 'not_run_rate_limited'
        return record
    prompt = prompt_for(spec, task)
    (folder / 'prompt.txt').write_text(prompt)
    print(f"start {run['id']}", flush=True)
    code, timed_out, secs = execute(claude_command(args, output, arm, prompt), workdir,
                                    folder / 'transcript.jsonl', args.timeout, env)
    reap(workdir)
    info = parse_transcript(folder / 'transcript.jsonl')
    result = info['result'] or {}
    ok, why = isolation(arm, info['init'])
    mcp_status = {s.get('name'): s.get('status') for s in (info['init'] or {}).get('mcp_servers', [])}
    rate_limited = bool(result.get('is_error')) and bool(RATE_LIMIT.search(str(result.get('result', ''))))
    if rate_limited:
        stop.set()
    project = score.find_project(workdir)
    names = spec['common_checks'] + task['checks']
    record.update({
        'status': 'rate_limited' if rate_limited else ('invalid_isolation' if not ok else 'completed'),
        'isolation_ok': ok, 'isolation_error': why, 'mcp_status': mcp_status,
        'agent_exit': code, 'agent_timed_out': timed_out, 'agent_seconds': secs,
        'agent_is_error': result.get('is_error'), 'agent_turns': result.get('num_turns'),
        'cost_usd_equivalent': result.get('total_cost_usd'), 'usage': result.get('usage'),
        'final_message': str(result.get('result', ''))[:2000],
        'tool_calls': info['tool_calls'], 'failed_tool_calls': info['failed_tool_calls'],
        'agent_build_commands': info['build_commands'], 'agent_failed_build_commands': info['failed_build_commands'],
        'skill_invocations': info['skill_invocations'], 'quarkus_mcp_calls': info['quarkus_mcp_calls'],
        'context7_calls': info['context7_calls'],
        'project_dir': str(project.relative_to(workdir)) if project else None,
        'java_files': score.java_file_count(project),
        'conformance': score.score(project, names),
        'generator': score.score(project, spec['generator_checks']),
    })
    # Metric 3: independent build attempts until green, at most 2. Attempt 1 compiles what the
    # agent left; on failure the same session is resumed once with the compiler output, then
    # attempt 2 compiles again. Conformance above is scored before any repair.
    attempts = []
    if project is not None and not rate_limited:
        compile_code, compile_timeout, compile_secs = execute(COMPILE, project, folder / 'compile-1.log', 300, env)
        attempts.append({'exit': compile_code, 'timed_out': compile_timeout, 'seconds': compile_secs})
        session = result.get('session_id') or (info['init'] or {}).get('session_id')
        if compile_code != 0 and session and not stop.is_set():
            tail = '\n'.join((folder / 'compile-1.log').read_text(errors='replace').splitlines()[-60:])
            repair = ('The acceptance check `mvn -B -ntp -DskipTests test-compile` failed in '
                      f'./{record["project_dir"]}. Fix the project so it passes. Compiler output (last lines):\n\n{tail}')
            rcode, rtimeout, rsecs = execute(claude_command(args, output, arm, repair, resume=session), workdir,
                                             folder / 'repair-transcript.jsonl', args.repair_timeout, env)
            reap(workdir)
            rinfo = parse_transcript(folder / 'repair-transcript.jsonl')
            rresult = rinfo['result'] or {}
            record['repair'] = {'exit': rcode, 'timed_out': rtimeout, 'seconds': rsecs,
                                'turns': rresult.get('num_turns'), 'cost_usd_equivalent': rresult.get('total_cost_usd'),
                                'is_error': rresult.get('is_error')}
            if rresult.get('is_error') and RATE_LIMIT.search(str(rresult.get('result', ''))):
                stop.set()
                record['status'] = 'rate_limited'
            project = score.find_project(workdir)
            if project is not None:
                c2, t2, s2 = execute(COMPILE, project, folder / 'compile-2.log', 300, env)
                attempts.append({'exit': c2, 'timed_out': t2, 'seconds': s2})
    record['compile_attempts'] = attempts
    record['compiles_first_attempt'] = bool(attempts) and attempts[0]['exit'] == 0
    record['compiles_within_two'] = any(a['exit'] == 0 for a in attempts)
    record['build_attempts_to_green'] = next((i + 1 for i, a in enumerate(attempts) if a['exit'] == 0), None)
    record['successful_generation'] = record['compiles_first_attempt'] and record['java_files'] > 0 \
        and not timed_out and record['status'] == 'completed'
    (folder / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
    print(f"done {run['id']}: compile@1={record['compiles_first_attempt']} "
          f"attempts={record['build_attempts_to_green']} "
          f"conformance={sum(record['conformance'].values())}/{len(names)} status={record['status']}", flush=True)
    return record


def snapshot(args, output):
    """Plugin with only scaffold-project, copied from the committed revision; optional context
    files (CLAUDE.md) from the same revision; MCP config."""
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    files = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', revision, '--',
                                     'skills/scaffold-project'], cwd=REPO, text=True).splitlines()
    hashes = {}
    for name in files:
        data = subprocess.check_output(['git', 'show', f'{revision}:{name}'], cwd=REPO)
        target = output / 'plugin' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    manifest = output / 'plugin' / '.claude-plugin' / 'plugin.json'
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({'name': PLUGIN_NAME, 'version': 'eval',
                                    'skills': ['./skills/scaffold-project']}, indent=2) + '\n')
    context = {}
    if args.with_claude_md:
        names = [CONTEXT_FILE]
        main_file = subprocess.check_output(['git', 'show', f'{revision}:{CONTEXT_FILE}'], cwd=REPO)
        if re.search(rb'AGENTS\.md', main_file):
            names.append('AGENTS.md')
        for name in names:
            data = subprocess.check_output(['git', 'show', f'{revision}:{name}'], cwd=REPO)
            target = output / 'context' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            context[name] = hashlib.sha256(data).hexdigest()
    quarkus, context7 = mcp_pins()
    (output / 'mcp.json').write_text(json.dumps({'mcpServers': {
        'quarkus-agent': {'command': 'jbang', 'args': ['--java', '21+', f'io.quarkus:quarkus-agent-mcp:{quarkus}:runner']},
        'context7': {'command': 'npx', 'args': ['-y', f'@upstash/context7-mcp@{context7}']}}}, indent=2) + '\n')
    return revision, hashes, context, quarkus, context7


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='new directory outside the repository')
    parser.add_argument('--tasks', default='', help='comma-separated task ids (default: all)')
    parser.add_argument('--repetitions', type=int, default=3)
    parser.add_argument('--parallel', type=int, default=3)
    parser.add_argument('--model', default='claude-sonnet-5-5')
    parser.add_argument('--timeout', type=int, default=900, help='seconds per agent run')
    parser.add_argument('--repair-timeout', type=int, default=600, help='seconds for the single repair turn')
    parser.add_argument('--with-claude-md', action='store_true',
                        help="copy the repository's CLAUDE.md (and AGENTS.md if it is referenced) into every "
                             'run directory, in both arms, and load it with --setting-sources project')
    parser.add_argument('--dry-run', action='store_true', help='print the plan and commands, run nothing')
    args = parser.parse_args()
    spec = load_tasks()
    runs = schedule(spec, set(filter(None, args.tasks.split(','))), args.repetitions)
    output = args.output.resolve()
    if args.dry_run:
        quarkus, context7 = mcp_pins()
        print(f'{len(runs)} runs, model {args.model}, parallel {args.parallel}, timeout {args.timeout}s; '
              f'MCP quarkus-agent-mcp {quarkus}, context7-mcp {context7}; '
              f"CLAUDE.md in run directory: {'yes' if args.with_claude_md else 'no'}")
        for run in runs:
            command = claude_command(args, output, run['arm'], prompt_for(spec, run['task']))
            print(f"\n[{run['id']}] cwd={output / 'runs' / run['id'] / 'work'}\n" + shlex.join(command))
        return
    if output == REPO or REPO in output.parents or output.exists():
        parser.error('output must be a new directory outside the repository')
    if subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', 'evals/effectiveness', 'skills/scaffold-project',
                       CONTEXT_FILE, 'AGENTS.md'],
                      cwd=REPO).returncode:
        parser.error('commit changes to the eval or the skill before collecting')
    if os.environ.get('ANTHROPIC_API_KEY'):
        print('note: ANTHROPIC_API_KEY is removed from every run; the subscription login is used', flush=True)
    output.mkdir(parents=True)
    revision, hashes, context, quarkus, context7 = snapshot(args, output)
    environment = {
        'date': datetime.date.today().isoformat(), 'source_commit': revision, 'skill_sha256': hashes,
        'with_claude_md': args.with_claude_md, 'context_files_sha256': context,
        'setting_sources': setting_sources(args),
        'model': args.model, 'claude_code': subprocess.check_output(['claude', '--version'], text=True).strip(),
        'java': subprocess.run(['java', '-version'], capture_output=True, text=True).stderr.splitlines()[0],
        'maven': subprocess.check_output(['mvn', '-v'], text=True).splitlines()[0],
        'quarkus_agent_mcp': quarkus, 'context7_mcp': context7, 'timeout_seconds': args.timeout,
        'repair_timeout_seconds': args.repair_timeout, 'parallel': args.parallel,
        'repetitions': args.repetitions, 'compile_command': COMPILE, 'allowed_tools': ALLOWED_TOOLS,
        'tasks_sha256': hashlib.sha256((HERE / 'tasks.json').read_bytes()).hexdigest(),
        'baseline_env': dict(line.split('=', 1) for line in (REPO / 'ci/baseline.env').read_text().splitlines()
                             if line and not line.startswith('#')),
    }
    (output / 'environment.json').write_text(json.dumps(environment, indent=2) + '\n')
    stop = threading.Event()
    ports = queue.Queue()
    for slot in range(args.parallel):
        ports.put(18080 + slot)
    lock = threading.Lock()
    records = []

    def worker(run):
        port = ports.get()
        try:
            record = run_one(args, spec, output, run, port, stop)
        except Exception as error:  # keep every scheduled run in the results
            record = {'run': run['id'], 'task': run['task']['id'], 'repetition': run['repetition'],
                      'arm': run['arm'], 'status': 'harness_error', 'error': repr(error)}
        finally:
            ports.put(port)
        with lock:
            records.append(record)
            records.sort(key=lambda r: r['run'])
            (output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')
        return record

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as pool:
        list(pool.map(worker, runs))
    if stop.is_set():
        print('stopped early: the subscription reported a usage/rate limit; partial results kept', flush=True)
        sys.exit(2)


if __name__ == '__main__':
    main()
