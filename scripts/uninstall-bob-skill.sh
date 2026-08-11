#!/usr/bin/env bash
#
# uninstall-bob-skill.sh — remove this repository's skills from IBM Bob.
#
# The mirror of install-bob-skill.sh. Bob has no manifest, registry, per-skill approval
# record, or CLI/UI command for removing a skill: it discovers skills by scanning
# .bob/skills/ (per project) or ~/.bob/skills/ (global), and the Skills tab reflects the
# filesystem rather than recording it. Deleting the directory IS the uninstall.
#
# Boundary — this removes the three skill directories and nothing else. .bob/ also holds
# the MCP registration (mcp.json at a project's .bob/, or settings/mcp.json under ~/.bob/ —
# the Quarkus Agents MCP + context7 servers, which are shared with the rest of your work and
# must survive), plus rules/, custom_modes.yaml, settings/, hooks/, and commands/. None are
# touched, and neither is .bob/skills/ itself, where your own skills live.
#
# Two guards, because 'audit-project' is a generic enough name to collide with a skill you
# wrote yourself:
#   1. Ownership — only remove a directory whose SKILL.md front matter declares the same
#      name we installed. Anything else (different name, no name, no SKILL.md) is left in
#      place with a warning. Residual: a skill of your own that is *also* named
#      audit-project is indistinguishable from ours and will be removed.
#   2. Symlinks — unlink a symlinked path instead of recursing through it, so a link into
#      your own checkout does not take the checkout with it.
#
set -euo pipefail

SKILL_NAMES=(setup-agentic-scaffolding scaffold-project audit-project)

usage() {
  cat <<'EOF'
uninstall-bob-skill.sh — remove this repository's skills from IBM Bob.

Removes setup-agentic-scaffolding, scaffold-project, and audit-project from .bob/skills/.
Leaves your MCP registration (.bob/mcp.json in a project, ~/.bob/settings/mcp.json with
--global — the Quarkus Agents MCP + context7 servers), .bob/rules/, and every other skill
alone. Safe to re-run.

Usage:
  uninstall-bob-skill.sh                    from ./.bob/skills/         (current directory)
  uninstall-bob-skill.sh /path/to/project   from that project's .bob/skills/
  uninstall-bob-skill.sh --global           from ~/.bob/skills/
EOF
}

case "${1:-}" in
  -h|--help) usage; exit 0 ;;
  --global)  BASE="$HOME" ;;
  "")        BASE="$PWD" ;;
  *)
    BASE="$1"
    if [[ ! -d "$BASE" ]]; then
      echo "error: target directory does not exist: $BASE" >&2
      exit 1
    fi
    ;;
esac

for SKILL_NAME in "${SKILL_NAMES[@]}"; do
  DEST="$BASE/.bob/skills/$SKILL_NAME"

  if [[ ! -e "$DEST" && ! -L "$DEST" ]]; then
    echo "Skipped '$SKILL_NAME': not installed"
    continue
  fi

  # Ownership check. Reading through a symlink is fine - this is read-only.
  DECLARED=""
  if [[ -f "$DEST/SKILL.md" ]]; then
    DECLARED="$(awk '/^name:/ {
      sub(/^name:[[:space:]]*/, ""); sub(/[[:space:]]+$/, ""); print; exit
    }' "$DEST/SKILL.md" | tr -d '\r')"
  fi
  if [[ "$DECLARED" != "$SKILL_NAME" ]]; then
    echo "Skipped '$SKILL_NAME': SKILL.md declares '${DECLARED:-<none>}', not ours — left in place" >&2
    continue
  fi

  if [[ -L "$DEST" ]]; then
    rm -- "$DEST"
    echo "Removed '$SKILL_NAME' (symlink) from: $DEST — its target was left alone"
  else
    rm -rf -- "$DEST"
    echo "Removed '$SKILL_NAME' from: $DEST"
  fi
done

echo "Start a new conversation in Bob — skills load once per conversation."
