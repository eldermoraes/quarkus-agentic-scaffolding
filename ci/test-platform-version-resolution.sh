#!/usr/bin/env bash
# Fixture test for the "latest stable platform" resolution in ci/build-from-templates.sh.
#
# The weekly validate-templates run (schedule, no argument) used to take Maven's <latest>
# hint verbatim. On 2026-10-05 that hint was 4.0.0.Beta1, a Quarkus 4 pre-release whose
# platform has no langchain4j-mcp, and the run failed (#79). The script now reads every
# <version>, drops pre-releases and keeps the highest x.y.z. These fixtures pin that:
#   1. a pre-release at the top of the list (and in <latest>/<release>) is skipped;
#   2. ordering is numeric, not lexical (3.40.1 > 3.9.9, 3.10.0 > 3.9.0);
#   3. every pre-release qualifier is dropped, in any letter case;
#   4. metadata with no stable version at all fails loudly instead of printing nothing.
#
# Fixtures are fed through PLATFORM_METADATA_URL with a file:// URL, so no network is used.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

SCRIPT=ci/build-from-templates.sh
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
failures=0
pass() { echo "ok: $1"; }
fail() { echo "FAIL: $1" >&2; failures=$((failures + 1)); }

# write_metadata <file> <latest> <version>... — a minimal quarkus-bom maven-metadata.xml.
write_metadata() {
  local file="$1" latest="$2"; shift 2
  {
    echo '<?xml version="1.0" encoding="UTF-8"?>'
    echo '<metadata>'
    echo '  <groupId>io.quarkus.platform</groupId>'
    echo '  <artifactId>quarkus-bom</artifactId>'
    echo '  <versioning>'
    echo "    <latest>$latest</latest>"
    echo "    <release>$latest</release>"
    echo '    <versions>'
    local v; for v in "$@"; do echo "      <version>$v</version>"; done
    echo '    </versions>'
    echo '    <lastUpdated>20261005000000</lastUpdated>'
    echo '  </versioning>'
    echo '</metadata>'
  } >"$file"
}

# expect_resolves <fixture> <expected-version> <label>
expect_resolves() {
  local got
  if got="$(PLATFORM_METADATA_URL="file://$1" "$SCRIPT" --resolve-only 2>"$TMP/stderr")" \
     && [[ "$got" == "$2" ]]; then
    pass "$3: resolved $2"
  else
    fail "$3: expected $2, got '${got:-}' (stderr: $(cat "$TMP/stderr"))"
  fi
}

# expect_fails <fixture> <label>
expect_fails() {
  if PLATFORM_METADATA_URL="file://$1" "$SCRIPT" --resolve-only >"$TMP/stdout" 2>"$TMP/stderr"; then
    fail "$2: expected a non-zero exit, got '$(cat "$TMP/stdout")'"
  elif [[ -s "$TMP/stdout" ]]; then
    fail "$2: failed but still printed '$(cat "$TMP/stdout")'"
  else
    pass "$2: failed loudly ($(cat "$TMP/stderr"))"
  fi
}

# 1. The 2026-10-05 shape: Beta on top, also in <latest>/<release>.
write_metadata "$TMP/beta-on-top.xml" 4.0.0.Beta1 \
  3.38.3 3.39.0.CR1 3.39.1 3.39.5 3.40.0.CR1 3.40.1 4.0.0.Beta1
expect_resolves "$TMP/beta-on-top.xml" 3.40.1 "Beta at the top of the list"
if grep -q '4.0.0.Beta1; pre-release ignored' "$TMP/stderr"; then
  pass "Beta at the top of the list: log names the ignored pre-release"
else
  fail "Beta at the top of the list: log does not name the ignored pre-release: $(cat "$TMP/stderr")"
fi

# 2. Numeric ordering: a lexical sort would pick 3.9.9.
write_metadata "$TMP/numeric.xml" 3.40.1 3.9.0 3.9.9 3.10.0 3.40.1
expect_resolves "$TMP/numeric.xml" 3.40.1 "numeric, not lexical, ordering"

# 3. Every qualifier dropped, mixed case, stable buried in the middle.
write_metadata "$TMP/qualifiers.xml" 5.0.0-SNAPSHOT \
  3.40.1 4.0.0.Alpha2 4.0.0.beta3 4.0.0.CR1 4.0.0.rc2 4.0.0.M1 5.0.0-SNAPSHOT
expect_resolves "$TMP/qualifiers.xml" 3.40.1 "Alpha/Beta/CR/RC/M/SNAPSHOT all ignored"

# 4. No stable version: must fail, not print an empty version.
write_metadata "$TMP/no-stable.xml" 4.0.0.Beta1 4.0.0.Alpha1 4.0.0.Beta1
expect_fails "$TMP/no-stable.xml" "metadata without any stable version"

if [[ "$failures" == 0 ]]; then
  echo 'OK: latest-stable platform resolution behaves as documented on all fixtures'
else
  echo "FAIL: $failures assertion(s) failed" >&2
  exit 1
fi
