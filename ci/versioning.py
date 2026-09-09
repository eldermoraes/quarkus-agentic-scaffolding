"""Canonical release inventory and formatting-preserving version updates."""
import argparse
import json
from pathlib import Path
import re
import sys

MARKDOWN = (
    'README.md', 'CLAUDE.md', 'AGENTS.md',
    'skills/setup-agentic-scaffolding/SKILL.md',
    'skills/scaffold-project/SKILL.md', 'skills/audit-project/SKILL.md',
)
JSON_FILES = ('.claude-plugin/plugin.json', '.codex-plugin/plugin.json', 'gemini-extension.json')
SEEDS = {f'{name}.md': f'skills/setup-agentic-scaffolding/templates/conventions-{name}.md'
         for name in ('CLAUDE', 'AGENTS')}
VERSION = r'(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)'


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def version_span(text, name):
    if name in MARKDOWN:
        matches = list(re.finditer(r'^# Version: ([^\r\n]*)', text, re.M))
        if len(matches) != 1:
            raise ValueError(f'{name}: expected exactly one version header')
        start, end = matches[0].span(1)
    else:
        data = json.loads(text, object_pairs_hook=unique_keys)
        if not isinstance(data, dict) or not isinstance(data.get('version'), str):
            raise ValueError(f'{name}: expected a top-level version string')
        # Walk top-level members so nested version fields remain untouched.
        decoder = json.JSONDecoder()
        position = text.index('{') + 1
        while True:
            position = re.compile(r'\s*').match(text, position).end()
            key, position = decoder.raw_decode(text, position)
            position = re.compile(r'\s*:\s*').match(text, position).end()
            value_start = position
            _, position = decoder.raw_decode(text, position)
            if key == 'version':
                start, end = value_start + 1, position - 1
                break
            position = re.compile(r'\s*,\s*').match(text, position).end()
    if not re.fullmatch(VERSION, text[start:end]):
        raise ValueError(f'{name}: invalid version {text[start:end]!r}')
    return start, end


def inventory(root):
    result = {}
    for name in (*MARKDOWN, *JSON_FILES):
        text = (root / name).read_bytes().decode('utf-8')
        start, end = version_span(text, name)
        result[name] = (text, start, end)
    return result


def check(root):
    files = inventory(root)
    versions = {text[start:end] for text, start, end in files.values()}
    if len(versions) != 1:
        raise ValueError(f'version mismatch: {sorted(versions)}')
    print(f'OK: version {versions.pop()} consistent across {len(files)} files')


def bump(root, version):
    if not re.fullmatch(VERSION, version):
        raise ValueError('new version must be numeric major.minor.patch without leading zeros')
    files = inventory(root)
    updates = {name: (text[:start] + version + text[end:]).encode('utf-8')
               for name, (text, start, end) in files.items()}
    for source, seed in SEEDS.items():
        # Validate destinations before writing; stale seeds are deliberately repaired.
        if not (root / seed).is_file():
            raise ValueError(f'missing seed file: {seed}')
        updates[seed] = updates[source]
    for name, content in updates.items():
        (root / name).write_bytes(content)
    print(f'Updated {len(updates)} files to {version}; update CHANGELOG.md before releasing')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('check', 'bump', 'seeds'))
    parser.add_argument('version', nargs='?')
    args = parser.parse_args()
    if (args.command == 'bump') != (args.version is not None):
        parser.error('only bump requires a version argument')
    root = Path(__file__).resolve().parent.parent
    try:
        if args.command == 'check':
            check(root)
        elif args.command == 'bump':
            bump(root, args.version)
        else:
            for source, seed in SEEDS.items():
                print(f'{source}|{seed}')
    except (OSError, ValueError) as error:
        sys.exit(f'FAIL: {error}')


if __name__ == '__main__':
    main()
