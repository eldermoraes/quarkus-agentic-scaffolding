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
# A re-run refreshes our own install: SKILL.md is replaced, and templates/ and references/ are
# replaced as a whole, so files a newer release dropped do not linger.
#
# Two guards, the same as uninstall-bob-skill.sh, because 'audit-project' is a generic enough
# name to collide with a skill you wrote yourself:
#   1. Ownership — an existing directory is only refreshed when its SKILL.md front matter
#      declares the same name. Anything else (different name, no name, no SKILL.md) is left in
#      place with a warning. Residual: a skill of your own that is *also* named audit-project is
#      indistinguishable from ours and will be refreshed over.
#   2. Symlinks — a symlinked skill directory is skipped, never written through, so a link into
#      your own checkout does not have the checkout overwritten.
# The other skills are still installed; the script exits 1 when anything was skipped.
#
set -euo pipefail

SKILL_NAMES=(setup-agentic-scaffolding scaffold-project audit-project)

usage() {
  cat <<'EOF'
install-bob-skill.sh — install this repository's skills into IBM Bob.

Installs setup-agentic-scaffolding, scaffold-project, and audit-project. This is a
fallback: `npx skills add eldermoraes/quarkus-agentic-scaffolding` already covers Bob.
Re-running refreshes them. An existing directory with one of these names is replaced only
when its SKILL.md declares that name; any other directory, or a symlink, is left untouched
with a warning, the rest are still installed, and the script exits 1.

Usage:
  install-bob-skill.sh                    into ./.bob/skills/         (current directory)
  install-bob-skill.sh /path/to/project   into that project's .bob/skills/
  install-bob-skill.sh --global           into ~/.bob/skills/
EOF
}

# BEGIN ownership rule — kept identical in install-bob-skill.sh and uninstall-bob-skill.sh
# (ci/test-install-bob-skill.sh compares the two copies). Each script carries its own copy so it
# still runs on its own. Prints the name that $1/SKILL.md declares in its front matter, or
# nothing when there is no readable SKILL.md. Reading through a symlink is fine: read-only.
declared_skill_name() {
  if [[ -f "$1/SKILL.md" && -r "$1/SKILL.md" ]]; then
    awk '/^name:/ {
      sub(/^name:[[:space:]]*/, ""); sub(/[[:space:]]+$/, ""); print; exit
    }' "$1/SKILL.md" | tr -d '\r'
  fi
}
# END ownership rule

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

SKIPPED=0
for SKILL_NAME in "${SKILL_NAMES[@]}"; do
  SRC="$SKILLS_ROOT/$SKILL_NAME"
  if [[ ! -f "$SRC/SKILL.md" ]]; then
    echo "error: skill source not found at $SRC" >&2
    exit 1
  fi

  DEST="$BASE/.bob/skills/$SKILL_NAME"

  if [[ -L "$DEST" ]]; then
    echo "Skipped '$SKILL_NAME': $DEST is a symlink — not written through, left in place" >&2
    SKIPPED=$((SKIPPED + 1))
    continue
  fi
  if [[ -e "$DEST" ]]; then
    DECLARED="$(declared_skill_name "$DEST")"
    if [[ "$DECLARED" != "$SKILL_NAME" ]]; then
      echo "Skipped '$SKILL_NAME': SKILL.md declares '${DECLARED:-<none>}', not ours — left in place: $DEST" >&2
      SKIPPED=$((SKIPPED + 1))
      continue
    fi
  fi

  # Bob reads SKILL.md plus its supporting files; agents/openai.yaml is Codex/OpenAI-specific
  # metadata and is intentionally not copied. SKILL.md is removed first so that a symlinked
  # SKILL.md inside our own directory is replaced, not written through.
  mkdir -p "$DEST"
  rm -f -- "$DEST/SKILL.md"
  cp "$SRC/SKILL.md" "$DEST/SKILL.md"
  for support in templates references; do
    rm -rf -- "${DEST:?}/${support:?}"
    if [[ -d "$SRC/$support" ]]; then
      cp -R "$SRC/$support" "$DEST/$support"
    fi
  done

  echo "Installed '$SKILL_NAME' into: $DEST"
done

echo "Open the project in Bob and try: \"scaffold a new Quarkus + LangChain4j project\""

if [[ "$SKIPPED" -gt 0 ]]; then
  echo "error: skipped $SKIPPED skill(s) whose directory is not ours (see above); rename or move it aside, then re-run" >&2
  exit 1
fi
