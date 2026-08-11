#!/usr/bin/env bash
# Behavior test for scripts/uninstall-bob-skill.sh.
#
# A destructive script does not validate by reading. Every case runs in a temp directory,
# and the --global case overrides HOME, so the test can never touch the real ~/.bob.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
REPO="$PWD"
INSTALL="$REPO/scripts/install-bob-skill.sh"
UNINSTALL="$REPO/scripts/uninstall-bob-skill.sh"
SKILLS=(setup-agentic-scaffolding scaffold-project audit-project)

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
failures=0
pass() { echo "ok: $1"; }
fail() { echo "FAIL: $1" >&2; failures=$((failures + 1)); }
assert_exists()  { if [[ -e "$1" || -L "$1" ]]; then pass "$2"; else fail "$2"; fi; }
assert_absent()  { if [[ ! -e "$1" && ! -L "$1" ]]; then pass "$2"; else fail "$2"; fi; }
assert_grep()    { if grep -Fq "$2" "$1"; then pass "$3"; else fail "$3 (missing: $2)"; fi; }

# --- Case 1: install -> uninstall round trip, and the boundary holds ----------
P="$TMP/proj"
mkdir -p "$P"
"$INSTALL" "$P" >/dev/null
mkdir -p "$P/.bob/skills/my-own-skill"
printf -- '---\nname: my-own-skill\ndescription: mine\n---\n' \
  >"$P/.bob/skills/my-own-skill/SKILL.md"
printf '{"mcpServers":{}}\n' >"$P/.bob/mcp.json"
mkdir -p "$P/.bob/rules"
printf 'my rule\n' >"$P/.bob/rules/mine.md"
for s in "${SKILLS[@]}"; do assert_exists "$P/.bob/skills/$s" "case1: installed $s"; done

"$UNINSTALL" "$P" >"$TMP/out1" 2>&1
for s in "${SKILLS[@]}"; do
  assert_absent "$P/.bob/skills/$s" "case1: removed $s"
  assert_grep "$TMP/out1" "Removed '$s' from: $P/.bob/skills/$s" "case1: reported $s"
done
assert_exists "$P/.bob/skills/my-own-skill/SKILL.md" "case1: foreign skill survives"
assert_exists "$P/.bob/skills"    "case1: .bob/skills/ itself survives"
assert_exists "$P/.bob/mcp.json"  "case1: .bob/mcp.json survives (the MCP boundary)"
assert_exists "$P/.bob/rules/mine.md" "case1: .bob/rules/ survives"
assert_grep "$TMP/out1" "Start a new conversation in Bob" "case1: prints the reload hint"

# --- Case 2: re-running is a clean no-op -------------------------------------
if "$UNINSTALL" "$P" >"$TMP/out2" 2>&1; then
  pass "case2: re-run exits 0"
else
  fail "case2: re-run exits 0"
fi
if [[ "$(grep -c "not installed" "$TMP/out2")" == 3 ]]; then
  pass "case2: three 'not installed' lines"
else
  fail "case2: three 'not installed' lines"
fi

# --- Case 3: ownership check - a skill of the user's own, same directory name --
F="$TMP/foreign"
mkdir -p "$F/.bob/skills/audit-project"
printf -- '---\nname: my-audit-project\ndescription: not theirs\n---\nbody\n' \
  >"$F/.bob/skills/audit-project/SKILL.md"
cp "$F/.bob/skills/audit-project/SKILL.md" "$TMP/foreign-skill.orig"
"$UNINSTALL" "$F" >"$TMP/out3" 2>&1 || true
assert_exists "$F/.bob/skills/audit-project/SKILL.md" "case3: foreign audit-project survives"
if cmp -s "$F/.bob/skills/audit-project/SKILL.md" "$TMP/foreign-skill.orig"; then
  pass "case3: foreign SKILL.md byte-for-byte unchanged"
else
  fail "case3: foreign SKILL.md byte-for-byte unchanged"
fi
assert_grep "$TMP/out3" "not ours" "case3: warns that it is not ours"

# --- Case 4: no SKILL.md at all - unverifiable, so left alone ------------------
N="$TMP/nomanifest"
mkdir -p "$N/.bob/skills/scaffold-project/templates"
printf 'x\n' >"$N/.bob/skills/scaffold-project/templates/leftover.txt"
"$UNINSTALL" "$N" >"$TMP/out4" 2>&1 || true
assert_exists "$N/.bob/skills/scaffold-project/templates/leftover.txt" \
  "case4: directory without SKILL.md is left in place"

# --- Case 5: symlinked skill - unlink the link, never recurse into the target --
S="$TMP/symlinked"
mkdir -p "$S/.bob/skills" "$TMP/real-target"
printf -- '---\nname: scaffold-project\ndescription: real\n---\n' \
  >"$TMP/real-target/SKILL.md"
ln -s "$TMP/real-target" "$S/.bob/skills/scaffold-project"
"$UNINSTALL" "$S" >"$TMP/out5" 2>&1
assert_absent "$S/.bob/skills/scaffold-project" "case5: symlink removed"
assert_exists "$TMP/real-target/SKILL.md" "case5: symlink target untouched"
assert_grep "$TMP/out5" "its target was left alone" "case5: says the target survived"

# --- Case 6: --global, with HOME redirected so the real ~/.bob is never touched -
H="$TMP/home"
mkdir -p "$H"
HOME="$H" "$INSTALL" --global >/dev/null
for s in "${SKILLS[@]}"; do assert_exists "$H/.bob/skills/$s" "case6: global install $s"; done
# The global MCP registration Bob 2.0.0 actually reads. --global sets BASE="$HOME",
# so this file is inside the blast radius and the script promises to leave it alone.
mkdir -p "$H/.bob/settings"
printf '{"mcpServers":{}}\n' >"$H/.bob/settings/mcp.json"
HOME="$H" "$UNINSTALL" --global >"$TMP/out6" 2>&1
for s in "${SKILLS[@]}"; do assert_absent "$H/.bob/skills/$s" "case6: global remove $s"; done
assert_exists "$H/.bob/settings/mcp.json" \
  "case6: ~/.bob/settings/mcp.json survives (the global MCP boundary)"
assert_exists "$H/.bob/skills" "case6: ~/.bob/skills/ itself survives"

# --- Case 7: --help and a bad directory ---------------------------------------
if "$UNINSTALL" --help >"$TMP/out7" 2>&1; then
  pass "case7: --help exits 0"
else
  fail "case7: --help exits 0"
fi
if "$UNINSTALL" "$TMP/does-not-exist" >"$TMP/out8" 2>&1; then
  fail "case7: a missing target directory must fail"
else
  pass "case7: a missing target directory fails"
fi

if [[ "$failures" == 0 ]]; then
  echo "OK: uninstall-bob-skill.sh behaves ($(( ${#SKILLS[@]} )) skills, 7 cases)"
else
  echo "FAIL: $failures assertion(s) failed" >&2
  exit 1
fi
