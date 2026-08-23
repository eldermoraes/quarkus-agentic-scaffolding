#!/usr/bin/env bash
# Fixture test for the managed-block removal procedure published in README.md's
# "Uninstall" section.
#
# A one-liner that deletes a region of the user's own CLAUDE.md does not validate by
# reading. The earlier design used `sed -i` with a count-based precheck; three inputs
# passed that precheck and still destroyed user-authored lines (see the spec, Finding 1).
# Every one of those inputs is a fixture here.
#
# Three properties are asserted:
#   1. The precheck says OK-SAFE-TO-REMOVE only for one complete, in-order marker pair.
#   2. On every input the precheck REFUSES, running the removal anyway leaves the file
#      byte-for-byte identical - so a user who ignores the precheck is still safe.
#   3. Group D pins the accepted residual: a marker quoted at column 0 counts as real to
#      both commands, so the precheck cannot tell a genuine pair from a quoted one. Those
#      fixtures record shipped behavior, not bugs (see the spec, Finding 1, "Residual").
#
# Plus a drift guard: README.md must still publish these exact commands.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

BEGIN_MARKER='<!-- BEGIN quarkus-agentic-scaffolding conventions (managed block; do not edit inside. Re-run /setup-agentic-scaffolding to update.) -->'
END_MARKER='<!-- END quarkus-agentic-scaffolding conventions -->'

# --- The two published commands, defined once. ---------------------------------
AWK_PROG='/^<!-- BEGIN quarkus-agentic-scaffolding conventions/{b++;bl=NR}
     /^<!-- END quarkus-agentic-scaffolding conventions/{e++;el=NR}
     END{printf "BEGIN=%d END=%d beginLine=%d endLine=%d -> %s\n", b,e,bl,el,
         (b==1 && e==1 && bl<el) ? "OK-SAFE-TO-REMOVE" : "REFUSE - remove the block by hand"}'
PERL_SUB='s/^<!-- BEGIN quarkus-agentic-scaffolding conventions.*?^<!-- END quarkus-agentic-scaffolding conventions -->[ \t]*\r?\n?//msg'

precheck()     { awk "$AWK_PROG" "$1"; }
remove_block() { perl -i -0777 -pe "$PERL_SUB" "$1"; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
failures=0
pass() { echo "ok: $1"; }
fail() { echo "FAIL: $1" >&2; failures=$((failures + 1)); }

expect_verdict() { # expect_verdict <file> <OK-SAFE-TO-REMOVE|REFUSE> <label>
  local got
  got="$(precheck "$1")"
  if [[ "$got" == *"$2"* ]]; then
    pass "$3: precheck -> $2"
  else
    fail "$3: precheck expected $2, got: $got"
  fi
}
assert_unchanged() { # assert_unchanged <file> <saved-copy> <label>
  if cmp -s "$1" "$2"; then
    pass "$3: byte-for-byte unchanged"
  else
    fail "$3: THE FILE WAS MODIFIED - this is the bug the fixture exists to catch"
    diff -u "$2" "$1" >&2 || true
  fi
}
assert_has()  { if grep -Fq "$2" "$1"; then pass "$3"; else fail "$3"; fi; }
assert_lacks() { if grep -Fq "$2" "$1"; then fail "$3"; else pass "$3"; fi; }

mk_block() { # mk_block <file> - append a well-formed managed block
  {
    printf '%s\n' "$BEGIN_MARKER"
    printf '\n# Quarkus + LangChain4j + AI Stack - Project Conventions\n\nrule one\nrule two\n\n'
    printf '%s\n' "$END_MARKER"
  } >>"$1"
}

# ============================================================================
# Group A - a complete, in-order pair: precheck passes and the block goes away
# ============================================================================

# A1: user content on both sides of the block.
f="$TMP/a1.md"
printf '# My own notes\n\nKEEP-ONE\n\n' >"$f"
mk_block "$f"
printf '\n## More of mine\n\nKEEP-TWO\n' >>"$f"
expect_verdict "$f" 'OK-SAFE-TO-REMOVE' 'A1 well-formed'
remove_block "$f"
assert_has  "$f" 'KEEP-ONE' 'A1: user content before the block survives'
assert_has  "$f" 'KEEP-TWO' 'A1: user content after the block survives'
assert_lacks "$f" 'BEGIN quarkus-agentic-scaffolding' 'A1: BEGIN marker gone'
assert_lacks "$f" 'END quarkus-agentic-scaffolding'   'A1: END marker gone'
assert_lacks "$f" 'rule one' 'A1: block body gone'

# A2: nothing but the block - reduces to exactly 0 bytes.
f="$TMP/a2.md"
: >"$f"
mk_block "$f"
expect_verdict "$f" 'OK-SAFE-TO-REMOVE' 'A2 only-the-block'
remove_block "$f"
if [[ ! -s "$f" ]]; then
  pass "A2: file is empty, so the documented \`rm\` step applies"
else
  fail "A2: expected 0 bytes, got $(wc -c <"$f") - contents: $(cat "$f")"
fi

# A3: a blank line on each side - leaves whitespace only, which is why the documented
# test is `grep -q '[^[:space:]]'` and not `[ -s ]`.
f="$TMP/a3.md"
printf '\n' >"$f"
mk_block "$f"
printf '\n' >>"$f"
expect_verdict "$f" 'OK-SAFE-TO-REMOVE' 'A3 blank-line padded'
remove_block "$f"
if [[ -s "$f" ]] && ! grep -q '[^[:space:]]' "$f"; then
  pass 'A3: non-empty but whitespace-only, and the published grep test catches it'
else
  fail "A3: expected a whitespace-only non-empty file, got $(wc -c <"$f") bytes"
fi

# A4: CRLF line endings - this is what the \r? in the regex is for.
f="$TMP/a4.md"
{
  printf 'KEEP-CRLF\r\n\r\n'
  printf '%s\r\n' "$BEGIN_MARKER"
  printf 'rule one\r\n'
  printf '%s\r\n' "$END_MARKER"
  printf '\r\nTAIL-CRLF\r\n'
} >"$f"
expect_verdict "$f" 'OK-SAFE-TO-REMOVE' 'A4 CRLF'
remove_block "$f"
assert_has   "$f" 'KEEP-CRLF' 'A4: user content survives'
assert_has   "$f" 'TAIL-CRLF' 'A4: trailing user content survives'
assert_lacks "$f" 'BEGIN quarkus-agentic-scaffolding' 'A4: block removed despite CRLF'

# A5: the END marker is the last line, with no trailing newline - what the \n? is for.
f="$TMP/a5.md"
printf 'KEEP-NONL\n\n%s\nrule one\n%s' "$BEGIN_MARKER" "$END_MARKER" >"$f"
expect_verdict "$f" 'OK-SAFE-TO-REMOVE' 'A5 no trailing newline'
remove_block "$f"
assert_has   "$f" 'KEEP-NONL' 'A5: user content survives'
assert_lacks "$f" 'END quarkus-agentic-scaffolding' 'A5: block removed without a final newline'

# ============================================================================
# Group B - malformed: precheck REFUSES, and the removal is a no-op anyway.
# Every one of these was destroyed by the `sed` procedure this replaced.
# ============================================================================

run_group_b() { # run_group_b <label> <file>
  local label="$1" f="$2" saved="$2.orig"
  cp "$f" "$saved"
  expect_verdict "$f" 'REFUSE' "$label"
  remove_block "$f"
  assert_unchanged "$f" "$saved" "$label"
}

# B1: BEGIN with no END. `sed` deleted from BEGIN to end of file.
f="$TMP/b1.md"
printf 'KEEP\n\n%s\nrule one\n\nMORE-OF-MINE\n' "$BEGIN_MARKER" >"$f"
run_group_b 'B1 BEGIN with no END' "$f"

# B2: a stray END on its own.
f="$TMP/b2.md"
printf 'KEEP\n\n%s\n\nMORE-OF-MINE\n' "$END_MARKER" >"$f"
run_group_b 'B2 stray END' "$f"

# B3: END before BEGIN. Passes even a strict BEGIN==1 && END==1 check - only the
# line-number comparison catches it. `sed` ran the range to end of file.
f="$TMP/b3.md"
printf 'KEEP\n\n%s\n\nMIDDLE-OF-MINE\n\n%s\n\nTAIL-OF-MINE\n' "$END_MARKER" "$BEGIN_MARKER" >"$f"
run_group_b 'B3 out-of-order markers' "$f"

# B4: both markers on one line. `grep -c` counted 1; `sed` never tested the closing
# regex against the line it opened on, so the range ran to end of file.
f="$TMP/b4.md"
printf 'KEEP\n\n%s filler %s\n\nMORE-OF-MINE\n' "$BEGIN_MARKER" "$END_MARKER" >"$f"
run_group_b 'B4 both markers on one line' "$f"

# B5: the user writes *about* the markers, mid-sentence. `grep -c` counted 2 and `sed`
# opened a range on the prose.
f="$TMP/b5.md"
printf "KEEP\n\nThe \`%s\` and \`%s\` pair delimits generated text.\n\nMORE-OF-MINE\n" \
  "$BEGIN_MARKER" "$END_MARKER" >"$f"
run_group_b 'B5 prose mention of both markers' "$f"

# B6: prose mention of BEGIN plus a real END at column 0.
f="$TMP/b6.md"
printf "KEEP\n\nI removed the \`%s\` line by hand.\n\n%s\n\nMORE-OF-MINE\n" \
  "$BEGIN_MARKER" "$END_MARKER" >"$f"
run_group_b 'B6 prose BEGIN plus a real END' "$f"

# ============================================================================
# Group C - two complete blocks. The precheck refuses on count, deliberately, so a
# human eyeballs a duplicated block. The removal is NOT run: perl's /g would happily
# remove both, which is safe content-wise but is not what the published procedure does.
# ============================================================================
f="$TMP/c1.md"
printf 'KEEP\n\n' >"$f"
mk_block "$f"
printf '\nMIDDLE-OF-MINE\n\n' >>"$f"
mk_block "$f"
expect_verdict "$f" 'REFUSE' 'C1 two complete blocks'

# ============================================================================
# Group D - the accepted residual, pinned as documented behavior. See the spec
# (2026-08-10-uninstall-design.md, Finding 1, "Residual"). Neither awk nor perl has any
# notion of a fenced code block, so a marker quoted at column 0 is column 0 to both: the
# precheck proves only that a column-0 marker pair exists IN ORDER, never that the pair
# is genuine. D1 quotes both markers, and the deletion happens to stay inside the fence.
# D2 and D3 are the sharp cases: a MIXED pair - one real marker, one quoted - deletes
# everything between the two matched lines, so the damage is NOT bounded to the quoted
# region. The mitigation is process, not pattern: the mandatory backup in step 1 and the
# published "read the diff before you trust it" warning. These three fixtures are a
# record of shipped behavior, not bug reports - do not "fix" the awk/perl commands to
# make them fail, those commands are published as validated against primary sources.
# ============================================================================
f="$TMP/d1.md"
{
  printf 'KEEP-BEFORE\n\nHere is what the block looks like:\n\n```markdown\n'
  printf '%s\n' "$BEGIN_MARKER"
  printf 'quoted example\n'
  printf '%s\n' "$END_MARKER"
  printf '```\n\nKEEP-AFTER\n'
} >"$f"
expect_verdict "$f" 'OK-SAFE-TO-REMOVE' 'D1 fenced quote (ACCEPTED residual)'
remove_block "$f"
assert_has "$f" 'KEEP-BEFORE' 'D1: content outside the fence survives'
assert_has "$f" 'KEEP-AFTER'  'D1: content after the fence survives'
if grep -Fq 'quoted example' "$f"; then
  fail 'D1: unexpected - the quoted region survived; re-check the spec residual note'
else
  pass 'D1: the quoted region was removed (documented residual)'
fi

# D2: MIXED pair - a real BEGIN whose END was deleted by hand, plus a column-0 END quoted
# inside a fence much further down. The precheck sees one BEGIN and one END in order and
# passes, and the removal takes every line between them, the user's own section included.
# This is the accepted residual, asserted here so the behavior cannot change unnoticed.
f="$TMP/d2.md"
{
  printf 'MY-HEADER\n\n'
  printf '%s\n' "$BEGIN_MARKER"
  printf '\nconventions body\n\n'
  printf '## MY OWN SECTION\n\nMY-PRECIOUS-NOTES\n\n'
  printf '```markdown\n'
  printf '%s\n' "$END_MARKER"
  printf '```\n\nMY-TAIL\n'
} >"$f"
expect_verdict "$f" 'OK-SAFE-TO-REMOVE' 'D2 mixed pair, real BEGIN + quoted END (ACCEPTED residual)'
remove_block "$f"
assert_has   "$f" 'MY-HEADER' 'D2: content above the real BEGIN survives'
assert_has   "$f" 'MY-TAIL'   'D2: content below the quoted END survives'
assert_lacks "$f" 'MY-PRECIOUS-NOTES' \
  'D2: user content between the two markers IS deleted - accepted, and not bounded to the fence'

# D3: the symmetric MIXED pair - a column-0 BEGIN quoted inside a fence, plus a real END
# further down. Same verdict, same unbounded deletion.
f="$TMP/d3.md"
{
  printf 'MY-HEADER\n\nHere is the opening marker:\n\n```markdown\n'
  printf '%s\n' "$BEGIN_MARKER"
  printf '```\n\n## MY OWN SECTION\n\nMY-PRECIOUS-NOTES\n\n'
  printf '%s\n' "$END_MARKER"
  printf '\nMY-TAIL\n'
} >"$f"
expect_verdict "$f" 'OK-SAFE-TO-REMOVE' 'D3 mixed pair, quoted BEGIN + real END (ACCEPTED residual)'
remove_block "$f"
assert_has   "$f" 'MY-HEADER' 'D3: content above the fence survives'
assert_has   "$f" 'MY-TAIL'   'D3: content below the real END survives'
assert_lacks "$f" 'MY-PRECIOUS-NOTES' \
  'D3: user content between the two markers IS deleted - accepted, and not bounded to the fence'

# ============================================================================
# Drift guard - README.md must publish these exact commands.
# ============================================================================
if grep -Fq "perl -i -0777 -pe '$PERL_SUB'" README.md; then
  pass 'README publishes the validated perl command verbatim'
else
  fail 'README no longer publishes the validated perl command - it drifted from this test'
fi
for frag in 'b++;bl=NR' 'e++;el=NR' 'b==1 && e==1 && bl<el' 'OK-SAFE-TO-REMOVE' \
            "grep -q '[^[:space:]]'"; do
  if grep -Fq "$frag" README.md; then
    pass "README still carries the precheck fragment: $frag"
  else
    fail "README lost the precheck fragment: $frag"
  fi
done
if grep -Eq "sed -i.*(BEGIN|END) quarkus-agentic-scaffolding" README.md; then
  fail 'README publishes a sed -i procedure for the managed block - see spec Finding 1'
else
  pass 'README publishes no sed -i procedure for the managed block'
fi
if grep -Eq 'npx skills remove (-g )?--all|skills remove --all' README.md; then
  fail "README publishes \`npx skills remove --all\` - it removes unrelated skills"
else
  pass "README does not publish \`npx skills remove --all\`"
fi

if [[ "$failures" == 0 ]]; then
  echo 'OK: managed-block removal behaves as documented on all 15 fixtures, and README matches'
else
  echo "FAIL: $failures assertion(s) failed" >&2
  exit 1
fi
