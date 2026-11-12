#!/usr/bin/env bash
#
# install-bob-skill.sh — install this repository's skills into IBM Bob.
#
# This is a documented fallback. `npx skills add eldermoraes/quarkus-agentic-scaffolding`
# already covers IBM Bob as a first-class agent (it installs into .bob/skills/ or
# ~/.bob/skills/), so prefer that. Use this script when you cannot run the skills CLI.
#
# IBM Bob discovers skills under .bob/skills/ (per project) or ~/.bob/skills/ (global).
# This copies each skill's SKILL.md and its templates/ and references/ (when present) into the chosen
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
# shellcheck source=scripts/bob-skill-common.sh
source "$SCRIPT_DIR/bob-skill-common.sh"

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

SKIPPED=0
for SKILL_NAME in "${SKILL_NAMES[@]}"; do
  SRC="$SKILLS_ROOT/$SKILL_NAME"
  if [[ ! -f "$SRC/SKILL.md" ]]; then
    echo "error: skill source not found at $SRC" >&2
    exit 1
  fi

  DEST="$BASE/.bob/skills/$SKILL_NAME"

  # Refuse before mkdir, cp or stale-support cleanup can change a user's files.
  if bob_skill_has_symlink "$DEST" || [[ -L "$DEST/SKILL.md" ]]; then
    echo "Skipped '$SKILL_NAME': target or manifest uses a symlink — left in place" >&2
    SKIPPED=1
    continue
  fi
  if [[ -e "$DEST" ]]; then
    DECLARED=""
    if [[ -d "$DEST" ]]; then
      # A read error is a refusal for this skill, not permission to overwrite it.
      if ! DECLARED="$(bob_skill_declared_name "$DEST/SKILL.md")"; then
        echo "Skipped '$SKILL_NAME': cannot read SKILL.md — left in place" >&2
        SKIPPED=1
        continue
      fi
    fi
    if [[ "$DECLARED" != "$SKILL_NAME" ]]; then
      echo "Skipped '$SKILL_NAME': SKILL.md declares '${DECLARED:-<none>}', not ours — left in place" >&2
      SKIPPED=1
      continue
    fi
  fi

  # Bob reads SKILL.md plus its supporting files; agents/openai.yaml is Codex/OpenAI-specific
  # metadata and is intentionally not copied.
  mkdir -p "$DEST"
  cp "$SRC/SKILL.md" "$DEST/SKILL.md"
  for support in templates references; do
    rm -rf "${DEST:?}/${support:?}"
    if [[ -d "$SRC/$support" ]]; then
      cp -R "$SRC/$support" "$DEST/$support"
    fi
  done

  echo "Installed '$SKILL_NAME' into: $DEST"
done

echo "Open the project in Bob and try: \"scaffold a new Quarkus + LangChain4j project\""

exit "$SKIPPED"
