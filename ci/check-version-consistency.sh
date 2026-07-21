#!/usr/bin/env bash
# Fails unless the nine versioned files carry one identical version.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
md_versions="$(grep -hoE '^# Version: [0-9]+\.[0-9]+\.[0-9]+' \
  README.md CLAUDE.md AGENTS.md \
  skills/setup-agentic-scaffolding/SKILL.md \
  skills/scaffold-project/SKILL.md \
  skills/audit-project/SKILL.md \
  | awk '{print $3}')"
json_versions="$(python3 -c '
import json
for f in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", "gemini-extension.json"):
    print(json.load(open(f))["version"])')"
all="$(printf '%s\n%s\n' "$md_versions" "$json_versions")"
count_files="$(printf '%s\n' "$all" | wc -l | tr -d ' ')"
count_unique="$(printf '%s\n' "$all" | sort -u | wc -l | tr -d ' ')"
if [[ "$count_files" != "9" || "$count_unique" != "1" ]]; then
  echo "FAIL: expected 9 identical version headers, got $count_files entries / $count_unique distinct:" >&2
  printf '%s\n' "$all" >&2
  exit 1
fi
echo "OK: version $(printf '%s\n' "$all" | head -1) consistent across 9 files"
