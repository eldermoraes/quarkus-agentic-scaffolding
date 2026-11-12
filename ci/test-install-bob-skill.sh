#!/usr/bin/env bash
# Behavior test for scripts/install-bob-skill.sh.
#
# The installer replaces files, so every case runs in a temp directory, and the --global case
# overrides HOME, so the test can never touch the real ~/.bob or this checkout's own .bob/.
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
assert_absent() { if [[ ! -e "$1" && ! -L "$1" ]]; then pass "$2"; else fail "$2"; fi; }
assert_grep()   { if grep -Fq "$2" "$1"; then pass "$3"; else fail "$3 (missing: $2)"; fi; }
assert_same()   { if diff -r "$1" "$2" >/dev/null 2>&1; then pass "$3"; else fail "$3"; fi; }
# run_install <outfile> <args...> — records the exit status in $status without tripping set -e.
run_install() { local out="$1"; shift; status=0; "$INSTALL" "$@" >"$out" 2>&1 || status=$?; }
assert_status() {
  if [[ "$1" == zero && "$status" == 0 ]] || [[ "$1" == nonzero && "$status" != 0 ]]; then
    pass "$2"
  else
    fail "$2 (exit $status)"
  fi
}
# Our skill is installed at $1 exactly as shipped: SKILL.md plus templates/ and references/.
assert_ours() {
  local dest="$1" src="$REPO/skills/$2" label="$3" support
  if cmp -s "$src/SKILL.md" "$dest/SKILL.md"; then pass "$label: SKILL.md is ours"; else fail "$label: SKILL.md is ours"; fi
  for support in templates references; do
    if [[ -d "$src/$support" ]]; then assert_same "$src/$support" "$dest/$support" "$label: $support/ matches the source"; fi
  done
}

# --- Case 1: fresh install ----------------------------------------------------
P="$TMP/proj"
mkdir -p "$P"
run_install "$TMP/out1" "$P"
assert_status zero "case1: fresh install exits 0"
for s in "${SKILLS[@]}"; do
  assert_ours "$P/.bob/skills/$s" "$s" "case1 $s"
  assert_grep "$TMP/out1" "Installed '$s' into: $P/.bob/skills/$s" "case1: reported $s"
done

# --- Case 2: re-run refreshes our own install, stale supporting files go -------
printf 'obsolete\n' >"$P/.bob/skills/scaffold-project/templates/obsolete.txt"
mkdir -p "$P/.bob/skills/audit-project/references"
printf 'obsolete\n' >"$P/.bob/skills/audit-project/references/obsolete.md"
# A refreshed install whose SKILL.md still declares our name, but with an old body.
sed 's/^description:.*/description: an older release/' \
  "$REPO/skills/setup-agentic-scaffolding/SKILL.md" >"$P/.bob/skills/setup-agentic-scaffolding/SKILL.md"
printf -- '---\nname: scaffold-project\ndescription: old\n---\nold body\n' \
  >"$P/.bob/skills/scaffold-project/SKILL.md"
run_install "$TMP/out2" "$P"
assert_status zero "case2: refresh exits 0"
for s in "${SKILLS[@]}"; do assert_ours "$P/.bob/skills/$s" "$s" "case2 $s"; done
assert_absent "$P/.bob/skills/scaffold-project/templates/obsolete.txt" "case2: stale template removed"
assert_absent "$P/.bob/skills/audit-project/references/obsolete.md" "case2: stale reference removed"

# --- Case 3: a skill of the user's own in a directory with our name ------------
F="$TMP/foreign"
mkdir -p "$F/.bob/skills/audit-project/templates" "$F/.bob/skills/audit-project/references"
printf -- '---\nname: my-audit-project\ndescription: mine\n---\nmy body\n' \
  >"$F/.bob/skills/audit-project/SKILL.md"
printf 'my template\n' >"$F/.bob/skills/audit-project/templates/mine.txt"
printf 'my reference\n' >"$F/.bob/skills/audit-project/references/mine.md"
cp -R "$F/.bob/skills/audit-project" "$TMP/foreign.orig"
run_install "$TMP/out3" "$F"
assert_status nonzero "case3: exits non-zero when a skill was skipped"
assert_same "$TMP/foreign.orig" "$F/.bob/skills/audit-project" "case3: foreign skill byte-for-byte unchanged"
assert_grep "$TMP/out3" "Skipped 'audit-project'" "case3: names the skipped skill"
assert_grep "$TMP/out3" "my-audit-project" "case3: says what the directory declares"
for s in setup-agentic-scaffolding scaffold-project; do
  assert_ours "$F/.bob/skills/$s" "$s" "case3 $s still installed"
done
assert_grep "$TMP/out3" "Installed 'scaffold-project' into:" "case3: reports the others"

# --- Case 4: a directory without SKILL.md -------------------------------------
N="$TMP/nomanifest"
mkdir -p "$N/.bob/skills/scaffold-project/templates"
printf 'x\n' >"$N/.bob/skills/scaffold-project/templates/leftover.txt"
cp -R "$N/.bob/skills/scaffold-project" "$TMP/nomanifest.orig"
run_install "$TMP/out4" "$N"
assert_status nonzero "case4: exits non-zero"
assert_same "$TMP/nomanifest.orig" "$N/.bob/skills/scaffold-project" "case4: directory left as it was"
assert_absent "$N/.bob/skills/scaffold-project/SKILL.md" "case4: no SKILL.md written into it"
assert_grep "$TMP/out4" "Skipped 'scaffold-project'" "case4: names the skipped skill"
for s in setup-agentic-scaffolding audit-project; do
  assert_ours "$N/.bob/skills/$s" "$s" "case4 $s still installed"
done

# --- Case 5: symlinked skill directories are never written through ------------
# The target declares our own name, so this proves the link alone is reason to skip.
S="$TMP/symlinked"
mkdir -p "$S/.bob/skills" "$TMP/real-target/templates"
printf -- '---\nname: setup-agentic-scaffolding\ndescription: a checkout\n---\n' \
  >"$TMP/real-target/SKILL.md"
printf 'keep\n' >"$TMP/real-target/templates/keep.txt"
cp -R "$TMP/real-target" "$TMP/real-target.orig"
ln -s "$TMP/real-target" "$S/.bob/skills/setup-agentic-scaffolding"
# $TMP/dangling-target-must-not-exist is never created: a dangling link is not written through either.
ln -s "$TMP/dangling-target-must-not-exist" "$S/.bob/skills/audit-project"
run_install "$TMP/out5" "$S"
assert_status nonzero "case5: exits non-zero"
assert_same "$TMP/real-target.orig" "$TMP/real-target" "case5: symlink target unchanged"
if [[ -L "$S/.bob/skills/setup-agentic-scaffolding" ]]; then pass "case5: link kept"; else fail "case5: link kept"; fi
if [[ -L "$S/.bob/skills/audit-project" ]]; then pass "case5: dangling link kept"; else fail "case5: dangling link kept"; fi
assert_absent "$TMP/dangling-target-must-not-exist" "case5: dangling link not followed"
assert_grep "$TMP/out5" "Skipped 'setup-agentic-scaffolding'" "case5: names the linked skill"
assert_grep "$TMP/out5" "Skipped 'audit-project'" "case5: names the dangling link"
assert_ours "$S/.bob/skills/scaffold-project" scaffold-project "case5 scaffold-project still installed"

# --- Case 6: --global, with HOME redirected so the real ~/.bob is never touched -
H="$TMP/home"
mkdir -p "$H/.bob/skills/audit-project" "$H/.bob/settings"
printf -- '---\nname: other\ndescription: mine\n---\n' >"$H/.bob/skills/audit-project/SKILL.md"
printf '{"mcpServers":{}}\n' >"$H/.bob/settings/mcp.json"
cp -R "$H/.bob" "$TMP/home-bob.orig"
status=0; HOME="$H" "$INSTALL" --global >"$TMP/out6" 2>&1 || status=$?
assert_status nonzero "case6: global run with a foreign skill exits non-zero"
assert_same "$TMP/home-bob.orig/skills/audit-project" "$H/.bob/skills/audit-project" "case6: foreign global skill unchanged"
assert_same "$TMP/home-bob.orig/settings" "$H/.bob/settings" "case6: ~/.bob/settings/ untouched"
for s in setup-agentic-scaffolding scaffold-project; do
  assert_ours "$H/.bob/skills/$s" "$s" "case6 global $s"
done

# --- Case 7: bare invocation uses $PWD ----------------------------------------
# The outer $PWD is the repo root. Never call "$INSTALL" with no arguments outside this
# subshell, or it would write into the checkout's own .bob/skills/.
mkdir -p "$TMP/bare"
status=0; ( cd "$TMP/bare" && "$INSTALL" ) >"$TMP/out7" 2>&1 || status=$?
assert_status zero "case7: bare invocation exits 0"
for s in "${SKILLS[@]}"; do assert_ours "$TMP/bare/.bob/skills/$s" "$s" "case7 $s"; done

# --- Case 8: --help and a missing target directory -----------------------------
run_install "$TMP/out8" --help
assert_status zero "case8: --help exits 0"
assert_grep "$TMP/out8" "install-bob-skill.sh" "case8: --help prints usage text"
run_install "$TMP/out8b" "$TMP/does-not-exist"
assert_status nonzero "case8: a missing target directory fails"
assert_absent "$TMP/does-not-exist" "case8: the missing directory is not created"

# --- Case 10: a SKILL.md that cannot be read is "no readable declaration" -------
# Skipped like any other skill we cannot prove is ours; the run must not abort on it.
U="$TMP/unreadable"
mkdir -p "$U/.bob/skills/audit-project"
printf -- '---\nname: audit-project\n---\n' >"$U/.bob/skills/audit-project/SKILL.md"
chmod 000 "$U/.bob/skills/audit-project/SKILL.md"
if [[ -r "$U/.bob/skills/audit-project/SKILL.md" ]]; then
  pass "case10: skipped (this user can read any file, e.g. root)"
else
  run_install "$TMP/out10" "$U"
  assert_status nonzero "case10: exits non-zero"
  assert_grep "$TMP/out10" "Skipped 'audit-project'" "case10: names the skipped skill"
  for s in setup-agentic-scaffolding scaffold-project; do
    assert_ours "$U/.bob/skills/$s" "$s" "case10 $s still installed"
  done
fi
chmod 644 "$U/.bob/skills/audit-project/SKILL.md"

# --- Case 9: the ownership rule is the same text in both scripts ---------------
# Each script carries its own copy so it runs on its own; this keeps the copies identical.
rule() { awk '/^# BEGIN ownership rule/ {on=1} on {print} /^# END ownership rule/ {exit}' "$1"; }
if [[ -n "$(rule "$INSTALL")" && "$(rule "$INSTALL")" == "$(rule "$UNINSTALL")" ]]; then
  pass "case9: install and uninstall share the ownership rule"
else
  fail "case9: install and uninstall share the ownership rule"
fi

if [[ "$failures" == 0 ]]; then
  echo "OK: install-bob-skill.sh behaves (${#SKILLS[@]} skills, 10 cases)"
else
  echo "FAIL: $failures assertion(s) failed" >&2
  exit 1
fi
