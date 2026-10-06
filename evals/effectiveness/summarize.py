"""Aggregate a collection's results.json into summary.json and SUMMARY.md, optionally exporting
the per-run records and an artifacts archive into the repository."""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score  # noqa: E402

ARMS = ('baseline', 'skill')
SKIP = {'target', '.git', 'node_modules', '.quarkus'}
SECRET = re.compile(r'(sk-ant-[\w-]{10,}|ghp_\w{20,}|github_pat_\w{20,}|AKIA[0-9A-Z]{16}|ctx7sk-[\w-]{10,})')


def valid(record):
    return record.get('status') == 'completed' and record.get('isolation_ok')


def mean(values, digits=2):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), digits) if values else None


def ratio(checks):
    return sum(checks.values()) / len(checks) if checks else 0.0


def cell(records):
    n = len(records)
    return {
        'n': n,
        'compile_first_attempt': sum(r['compiles_first_attempt'] for r in records),
        'compile_within_two': sum(r['compiles_within_two'] for r in records),
        'build_attempts': {'1': sum(r['build_attempts_to_green'] == 1 for r in records),
                           '2': sum(r['build_attempts_to_green'] == 2 for r in records),
                           'not_green': sum(r['build_attempts_to_green'] is None for r in records)},
        'conformance_pct': round(100 * mean([ratio(r['conformance']) for r in records], 6), 1) if n else None,
        'generator_pct': round(100 * mean([ratio(r['generator']) for r in records], 6), 1) if n else None,
        'mean_agent_turns': mean([r.get('agent_turns') for r in records]),
        'mean_failed_build_commands': mean([r.get('agent_failed_build_commands') for r in records]),
        'mean_agent_minutes': mean([(r.get('agent_seconds') or 0) / 60 for r in records]),
        'timeouts': sum(bool(r.get('agent_timed_out')) for r in records),
        'skill_invoked': sum(any('scaffold' in s for s in r.get('skill_invocations', [])) for r in records),
        'mean_quarkus_mcp_calls': mean([r.get('quarkus_mcp_calls') for r in records]),
    }


def summarize(records):
    used = [r for r in records if valid(r)]
    tasks = sorted({r['task'] for r in records}, key=lambda t: [r['task'] for r in records].index(t))
    summary = {'scheduled': len(records), 'valid': len(used),
               'excluded': [{'run': r['run'], 'status': r.get('status'), 'reason': r.get('isolation_error') or r.get('error')}
                            for r in records if not valid(r)],
               'by_task': {t: {a: cell([r for r in used if r['task'] == t and r['arm'] == a]) for a in ARMS} for t in tasks},
               'overall': {a: cell([r for r in used if r['arm'] == a]) for a in ARMS},
               'checks': {}}
    for arm in ARMS:
        rows = [r for r in used if r['arm'] == arm]
        names = sorted({k for r in rows for k in list(r['conformance']) + list(r['generator'])})
        summary['checks'][arm] = {k: [sum(bool({**r['conformance'], **r['generator']}.get(k)) for r in rows
                                          if k in r['conformance'] or k in r['generator']),
                                      sum(1 for r in rows if k in r['conformance'] or k in r['generator'])]
                                  for k in names}
    b, s = summary['overall']['baseline'], summary['overall']['skill']
    if b['n'] and s['n']:
        summary['delta'] = {
            'compile_first_attempt_pp': round(100 * (s['compile_first_attempt'] / s['n'] - b['compile_first_attempt'] / b['n']), 1),
            'compile_within_two_pp': round(100 * (s['compile_within_two'] / s['n'] - b['compile_within_two'] / b['n']), 1),
            'conformance_pp': round(s['conformance_pct'] - b['conformance_pct'], 1),
            'generator_pp': round(s['generator_pct'] - b['generator_pct'], 1)}
    return summary


def markdown(summary, environment):
    lines = ['# Skill effectiveness eval: results', '',
             f"Date {environment.get('date')}, model `{environment.get('model')}`, {environment.get('claude_code')}, "
             f"source commit `{environment.get('source_commit', '')[:12]}`. "
             f"{summary['valid']} valid of {summary['scheduled']} scheduled runs. "
             f"Repository CLAUDE.md in both arms' run directory: "
             f"{'yes (' + ', '.join(environment.get('context_files_sha256') or {}) + ')' if environment.get('with_claude_md') else 'no'}.", '',
             '| Task | Arm | n | Compiles (attempt 1) | Compiles (within 2) | Convention checks (agent-decided) | Generator checks | Mean turns | Mean failed build cmds | Mean minutes |',
             '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    def row(name, arm, c):
        return (f"| {name} | {arm} | {c['n']} | {c['compile_first_attempt']}/{c['n']} | {c['compile_within_two']}/{c['n']} | "
                f"{c['conformance_pct']}% | {c['generator_pct']}% | {c['mean_agent_turns']} | "
                f"{c['mean_failed_build_commands']} | {c['mean_agent_minutes']} |")
    present = [arm for arm in ARMS if summary['overall'][arm]['n']]  # --arms may run one arm only
    for task, arms in summary['by_task'].items():
        for arm in present:
            lines.append(row(task, arm, arms[arm]))
    for arm in present:
        lines.append(row('**All tasks**', arm, summary['overall'][arm]))
    if 'delta' in summary:
        d = summary['delta']
        lines += ['', f"Delta (skill minus baseline): compile at attempt 1 {d['compile_first_attempt_pp']:+} pp, "
                      f"compile within two attempts {d['compile_within_two_pp']:+} pp, agent-decided convention checks "
                      f"{d['conformance_pp']:+} pp, generator checks {d['generator_pp']:+} pp."]
    lines += ['', '## Per-check pass counts', '', '| Check | Baseline | Skill |', '| --- | --- | --- |']
    names = sorted(set(summary['checks'].get('baseline', {})) | set(summary['checks'].get('skill', {})))
    for name in names:
        b = summary['checks'].get('baseline', {}).get(name, [0, 0])
        s = summary['checks'].get('skill', {}).get(name, [0, 0])
        lines.append(f'| `{name}` | {b[0]}/{b[1]} | {s[0]}/{s[1]} |')
    skill = summary['overall']['skill']
    lines += ['', f"The skill arm invoked `scaffold-project` in {skill['skill_invoked']}/{skill['n']} runs.",
              f"Excluded runs: {len(summary['excluded'])}" + (': ' + ', '.join(f"{e['run']} ({e['status']})" for e in summary['excluded']) if summary['excluded'] else '.')]
    return '\n'.join(lines) + '\n'


def export(output, dest):
    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'runs').mkdir(exist_ok=True)
    for name in ('results.json', 'environment.json'):
        shutil.copyfile(output / name, dest / name)
    for result in sorted((output / 'runs').glob('*/result.json')):
        shutil.copyfile(result, dest / 'runs' / f'{result.parent.name}.json')
    with tarfile.open(dest / 'artifacts.tar.gz', 'w:gz') as archive:
        for path in sorted((output / 'runs').rglob('*')):
            rel = path.relative_to(output / 'runs')
            if not path.is_file() or SKIP.intersection(rel.parts) or path.suffix in ('.jar', '.class'):
                continue
            text = path.read_bytes()
            if SECRET.search(text.decode('utf-8', errors='ignore')):
                raise SystemExit(f'refusing to export {rel}: credential-like string')
            archive.add(path, arcname=str(Path('runs') / rel))


def rescore(output, records):
    """Recompute the convention checks from the projects kept in a local collection directory."""
    spec = json.loads((Path(__file__).resolve().parent / 'tasks.json').read_text())
    tasks = {t['id']: t for t in spec['tasks']}
    for record in records:
        workdir = output / 'runs' / record['run'] / 'work'
        if record.get('status') == 'harness_error' or not workdir.is_dir():
            continue
        project = score.find_project(workdir)
        record['conformance'] = score.score(project, spec['common_checks'] + tasks[record['task']]['checks'])
        record['generator'] = score.score(project, spec['generator_checks'])
        record['rescored'] = True
        (output / 'runs' / record['run'] / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
    (output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='collection directory written by run.py')
    parser.add_argument('--export', type=Path, help='repository results directory to populate')
    parser.add_argument('--rescore', action='store_true',
                        help='recompute convention checks with the current score.py before summarizing')
    args = parser.parse_args()
    records = json.loads((args.output / 'results.json').read_text())
    if args.rescore:
        rescore(args.output, records)
    environment = json.loads((args.output / 'environment.json').read_text())
    summary = summarize(records)
    target = args.export or args.output
    if args.export:
        export(args.output, args.export)
    (target / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    (target / 'SUMMARY.md').write_text(markdown(summary, environment))
    print(markdown(summary, environment))


if __name__ == '__main__':
    main()
