#!/usr/bin/env bash
# Fails if any scaffold template names an agent-specific conventions file.
#
# Templates are copied as-is into projects whose conventions file may be
# CLAUDE.md (Claude) or AGENTS.md (Codex, Bob), so a comment that points at one
# of them is wrong for the other. Templates refer to "the project conventions"
# plus "section N", which reads correctly against both files.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if hits=$(grep -rnE 'CLAUDE\.md|AGENTS\.md' skills/scaffold-project/templates/); then
  echo "Templates must not name CLAUDE.md or AGENTS.md; write \"project conventions section N\" instead:" >&2
  echo "$hits" >&2
  exit 1
fi
echo "ok: no template names an agent-specific conventions file"
