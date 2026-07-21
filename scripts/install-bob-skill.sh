#!/usr/bin/env bash
#
# install-bob-skill.sh — install this repository's skills into IBM Bob.
#
# This is a documented fallback. `npx skills add eldermoraes/quarkus-agentic-scaffolding`
# already covers IBM Bob as a first-class agent (it installs into .bob/skills/ or
# ~/.bob/skills/), so prefer that. Use this script when you cannot run the skills CLI.
#
# IBM Bob discovers skills under .bob/skills/ (per project) or ~/.bob/skills/ (global).
# This copies each skill's SKILL.md and its templates/ (when present) into the chosen
# location. All three skills are installed: setup-agentic-scaffolding, scaffold-project,
# and audit-project.
#
set -euo pipefail

SKILL_NAMES=(setup-agentic-scaffolding scaffold-project audit-project)

usage() {
  cat <<'EOF'
install-bob-skill.sh — install this repository's skills into IBM Bob.

Installs setup-agentic-scaffolding, scaffold-project, and audit-project. This is a
fallback: `npx skills add eldermoraes/quarkus-agentic-scaffolding` already covers Bob.

Usage:
  install-bob-skill.sh                    into ./.bob/skills/         (current directory)
  install-bob-skill.sh /path/to/project   into that project's .bob/skills/
  install-bob-skill.sh --global           into ~/.bob/skills/
EOF
}

# Resolve the skills source relative to this script, so it works from any working directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_ROOT="$SCRIPT_DIR/../skills"

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
  SRC="$SKILLS_ROOT/$SKILL_NAME"
  if [[ ! -f "$SRC/SKILL.md" ]]; then
    echo "error: skill source not found at $SRC" >&2
    exit 1
  fi

  DEST="$BASE/.bob/skills/$SKILL_NAME"

  # Bob reads SKILL.md plus its supporting files; agents/openai.yaml is Codex/OpenAI-specific
  # metadata and is intentionally not copied.
  mkdir -p "$DEST"
  cp "$SRC/SKILL.md" "$DEST/SKILL.md"
  rm -rf "$DEST/templates"
  if [[ -d "$SRC/templates" ]]; then
    cp -R "$SRC/templates" "$DEST/templates"
  fi

  echo "Installed '$SKILL_NAME' into: $DEST"
done

echo "Open the project in Bob and try: \"scaffold a new Quarkus + LangChain4j project\""
