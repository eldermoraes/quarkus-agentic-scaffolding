#!/usr/bin/env bash
# Fails unless every external action a workflow or local composite action uses is pinned to a
# full 40-character commit SHA, followed by a `# vX.Y.Z` comment naming the version it is.
#
# Why this gate exists: a tag such as `@v7` is a movable pointer. Whoever controls the action's
# repository can point it at new code, and the next run executes that code with the workflow's
# token. A commit SHA cannot move. Renovate (`helpers:pinGitHubActionDigests` in renovate.json)
# keeps the pins and their version comments current, so pinning does not mean going stale.
#
# Local actions (`uses: ./...`) live in this repository and are reviewed with it, so they are
# not pinned; their own `uses:` lines are scanned like any workflow's.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

python3 - <<'PY'
import glob, re, sys

FILES = sorted(glob.glob(".github/workflows/*.y*ml") + glob.glob(".github/actions/**/action.y*ml", recursive=True))
USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(?P<ref>[^\s#]+)\s*(?:#\s*(?P<comment>.*))?$")
PINNED = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")
VERSION = re.compile(r"^v?\d+\.\d+\.\d+$")

bad, total = [], 0
for path in FILES:
    for lineno, line in enumerate(open(path, encoding="utf-8"), 1):
        m = USES.match(line)
        if not m:
            continue
        ref = m.group("ref").strip("'\"")
        if ref.startswith("./"):
            continue
        total += 1
        if ref.startswith("docker://"):
            if "@sha256:" not in ref:
                bad.append((path, lineno, line.strip(), "docker image not pinned by sha256 digest"))
            continue
        if not PINNED.match(ref):
            bad.append((path, lineno, line.strip(), "not pinned to a 40-character commit SHA"))
        elif not VERSION.match((m.group("comment") or "").strip()):
            bad.append((path, lineno, line.strip(), "missing the `# vX.Y.Z` version comment"))

if bad:
    print("FAIL: external actions must be pinned as `uses: owner/repo@<40-char sha> # vX.Y.Z`.",
          file=sys.stderr)
    for path, lineno, line, why in bad:
        print(f"  {path}:{lineno}: {line}  ({why})", file=sys.stderr)
    sys.exit(1)
if total == 0:
    print("FAIL: no external action found at all — did the workflows move?", file=sys.stderr)
    sys.exit(1)
print(f"OK: {total} external action references, all pinned to a commit SHA with a version comment")
PY
