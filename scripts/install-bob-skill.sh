#!/usr/bin/env bash
#
# install-bob-skill.sh — install the quarkus-langchain4j-scaffolding skill into IBM Bob.
#
# IBM Bob discovers skills under .bob/skills/ (per project) or ~/.bob/skills/ (global).
# This copies the skill's SKILL.md and templates/ into the chosen location.
#
set -euo pipefail

SKILL_NAME="quarkus-langchain4j-scaffolding"

usage() {
  cat <<'EOF'
install-bob-skill.sh — install the quarkus-langchain4j-scaffolding skill into IBM Bob.

Usage:
  install-bob-skill.sh                    into ./.bob/skills/         (current directory)
  install-bob-skill.sh /path/to/project   into that project's .bob/skills/
  install-bob-skill.sh --global           into ~/.bob/skills/
EOF
}

# Resolve the skill source relative to this script, so it works from any working directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/../skills/$SKILL_NAME"

if [[ ! -f "$SRC/SKILL.md" ]]; then
  echo "error: skill source not found at $SRC" >&2
  exit 1
fi

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

DEST="$BASE/.bob/skills/$SKILL_NAME"

# Bob reads SKILL.md plus its supporting files; agents/openai.yaml is Codex/OpenAI-specific
# metadata and is intentionally not copied.
mkdir -p "$DEST"
cp "$SRC/SKILL.md" "$DEST/SKILL.md"
rm -rf "$DEST/templates"
cp -R "$SRC/templates" "$DEST/templates"

echo "Installed '$SKILL_NAME' into: $DEST"
echo "Open the project in Bob and try: \"scaffold a new Quarkus + LangChain4j project\""
