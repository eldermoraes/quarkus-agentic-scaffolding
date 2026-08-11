#!/usr/bin/env bash
# Fails unless every published Quarkus Agents MCP registration carries the JDK pin
# and the same pinned version.
#
# Why this gate exists: the launch command is hand-maintained in ~15 places across
# README.md, the setup skill, and gemini-extension.json. check-version-consistency.sh
# couples the artifact *version* across files and Renovate couples the *GAV*, but
# nothing coupled the *command* — so `--java 21+` could be present in one copy and
# missing in another with every other gate green. It has to be present in all of
# them: JBang otherwise falls back to its default JDK (17 on 0.125.x) whenever the
# process that spawns the server exports no JAVA_HOME, and the server needs 21.
#
# Historical files are out of scope on purpose: CHANGELOG.md and docs/ quote the old,
# unpinned command as a record of what was fixed.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

python3 - <<'PY'
import glob, re, sys

FILES = ["README.md", "gemini-extension.json"] + sorted(glob.glob("skills/*/SKILL.md"))
GAV = re.compile(r"io\.quarkus:quarkus-agent-mcp:([0-9][^\s\"'`,\]]*):runner")
# Flatten the punctuation that separates a JSON args array or a wrapped line, so a
# markdown command, a JSON "args" list, and a quoted add-json payload all normalize
# to the same token stream: ... --java 21+ io.quarkus:quarkus-agent-mcp:X:runner ...
NOISE = re.compile(r"[\s\"',\[\]`]+")
PINNED = re.compile(r"--java 21\+ $")

unpinned, versions, total = [], set(), 0
for path in FILES:
    flat = NOISE.sub(" ", open(path, encoding="utf-8").read())
    for m in GAV.finditer(flat):
        total += 1
        versions.add(m.group(1))
        if not PINNED.search(flat[max(0, m.start() - 30):m.start()]):
            unpinned.append((path, flat[max(0, m.start() - 60):m.end()].strip()))

fail = False
if unpinned:
    fail = True
    print("FAIL: a published registration is missing the `--java 21+` JDK pin.", file=sys.stderr)
    print("      Every occurrence must read `jbang --java 21+ io.quarkus:...:runner`", file=sys.stderr)
    print("      (or the JSON equivalent). Occurrences found without it:\n", file=sys.stderr)
    for path, ctx in unpinned:
        print(f"  {path}: …{ctx}", file=sys.stderr)
if len(versions) > 1:
    fail = True
    print(f"\nFAIL: the pinned GAV version differs across files: {sorted(versions)}", file=sys.stderr)
    print("      Renovate bumps them together; a partial bump is drift.", file=sys.stderr)
if total == 0:
    fail = True
    print("FAIL: no Quarkus Agents MCP registration found at all — did a file move?", file=sys.stderr)
if fail:
    sys.exit(1)
print(f"OK: {total} MCP registrations, all pinned to --java 21+ at version {versions.pop()}")
PY
