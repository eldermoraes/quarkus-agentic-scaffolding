#!/usr/bin/env bash
# Fails unless CLAUDE.md and AGENTS.md carry identical conventions once their
# known, legitimate presentation differences are normalized away.
#
# The two files are hand-synced twins: CLAUDE.md speaks to Claude, AGENTS.md to
# Codex/Bob (and any AGENTS.md-standard reader). Their only allowed differences
# are the drift classes below; any other divergence means a conventions edit
# landed in one file only, and this gate fails with the offending diff.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# --- Known drift classes 1-3: one sed -E substitution per class. -------------
# Applied to BOTH files after unwrapping. To admit a NEW legitimate difference,
# append a rule here with a comment naming the drift class it normalizes.
SED_RULES=(
  # class 1 (typography): em dash "—" (CLAUDE.md) vs plain hyphen "-" (AGENTS.md)
  's/—/-/g'
  # class 1 (typography): ellipsis "…" (CLAUDE.md) vs "..." (AGENTS.md)
  's/…/.../g'
  # class 2 (cross-references): "§4" (CLAUDE.md) vs "section 4" (AGENTS.md)
  's/§([0-9]+)/section \1/g'
  # class 3 (audience): the preamble names its reader differently per file;
  # both wordings collapse to the same canonical token.
  's/whenever code is written, reviewed, or configured in/whenever <READER-CLAUSE> in/'
  's/whenever Codex or Bob writes, reviews, or configures code in/whenever <READER-CLAUSE> in/'
)

# --- Drift class 4 (line wrapping): unwrap hard-wrapped blocks. ---------------
# A block starts at a blank line, heading, horizontal rule, or list item; any
# other line is a continuation and is joined to its block with a single space,
# so the two files may wrap the same sentence at different columns.
unwrap() {
  awk '
    function flush() { if (buf != "") print buf; buf = "" }
    { sub(/[[:space:]]+$/, "") }                       # strip trailing ws/CR
    /^[[:space:]]*$/              { flush(); print ""; next }
    /^(#|---|- |\* |> |[0-9]+\. )/ { flush(); buf = $0; next }
    { line = $0; sub(/^[[:space:]]+/, "", line)
      buf = (buf == "" ? line : buf " " line) }
    END { flush() }
  '
}

normalize() {
  local sed_script
  sed_script="$(printf '%s;' "${SED_RULES[@]}")"
  unwrap <"$1" | sed -E "$sed_script"
}

if diff_output="$(diff -u \
    --label 'CLAUDE.md (normalized)' <(normalize CLAUDE.md) \
    --label 'AGENTS.md (normalized)' <(normalize AGENTS.md))"; then
  echo "OK: CLAUDE.md and AGENTS.md conventions are in parity"
else
  {
    echo 'FAIL: CLAUDE.md and AGENTS.md have diverged beyond the known drift'
    echo '      classes (typography, section references, audience preamble,'
    echo '      line wrapping). Apply the same conventions edit to BOTH files,'
    echo '      or extend SED_RULES in this script for a new legitimate class.'
    echo
    echo "$diff_output"
  } >&2
  exit 1
fi

# --- Seed-copy parity: the setup skill ships byte-for-byte copies of the root -
# conventions files (it drops them into the user's project in Phase C). These are
# plain copies, not normalized twins, so a plain diff must match exactly.
seed_fail=0
while IFS='|' read -r root seed; do
  if seed_diff="$(diff -u "$root" "$seed")"; then
    echo "OK: $seed is identical to $root"
  else
    {
      echo "FAIL: $seed has drifted from $root — re-copy the root file over the"
      echo '      seed after any conventions edit or version bump.'
      echo
      echo "$seed_diff"
    } >&2
    seed_fail=1
  fi
done <<'SEEDS'
CLAUDE.md|skills/setup-agentic-scaffolding/templates/conventions-CLAUDE.md
AGENTS.md|skills/setup-agentic-scaffolding/templates/conventions-AGENTS.md
SEEDS
[[ "$seed_fail" == 0 ]] || exit 1
