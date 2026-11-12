#!/usr/bin/env bash
# Fixture test for ci/boot_overlay.py, the step of ci/build-from-templates.sh that turns the
# project generated from the templates into one `mvn test` can boot (#114). No Maven: the
# overlay runs on a minimal project holding the real application.properties.template.
#   1. on the shipped template it enables the RAG, MCP-client and MCP-server keys, each at its
#      first (primary) occurrence, leaving the commented alternatives alone;
#   2. it points the "ops" MCP client at the app's own MCP server on the test port, gives the
#      default, "main" and "smaller" models distinct %test model ids, and turns the template's
#      test-profile Easy RAG ingestion (off, #113) back on for the boot test;
#   3. it adds the RAG documents under the configured easy-rag.path (on the classpath, i.e.
#      under src/main/resources, when easy-rag.path-type is classpath) and the Java fixtures
#      under src/test/java;
#   4. a key it must enable that the template no longer has fails the run, naming the key;
#   5. a pom without Easy RAG fails the run;
#   6. build-from-templates.sh rejects an unknown option before generating anything.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

OVERLAY=ci/boot_overlay.py
TEMPLATE=skills/scaffold-project/templates/application.properties.template
FIXTURES=ci/fixtures/boot-test
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
failures=0
pass() { echo "ok: $1"; }
fail() { echo "FAIL: $1" >&2; failures=$((failures + 1)); }

# new_project <dir> [pom-artifact] — a generated-project stand-in with the template's properties.
new_project() {
  local dir="$1" artifact="${2:-quarkus-langchain4j-easy-rag}"
  mkdir -p "$dir/src/main/resources"
  cp "$TEMPLATE" "$dir/src/main/resources/application.properties"
  printf '<project><dependencies><dependency><groupId>io.quarkiverse.langchain4j</groupId><artifactId>%s</artifactId></dependency></dependencies></project>\n' \
    "$artifact" >"$dir/pom.xml"
}

# has_line <file> <exact line> <label>
has_line() {
  if grep -qxF -- "$2" "$1"; then pass "$3"; else fail "$3: no line '$2' in $1"; fi
}

# 1-3. The shipped template.
P="$TMP/ok"
new_project "$P"
if python3 "$OVERLAY" "$P" "$FIXTURES" >"$TMP/out" 2>&1; then
  pass "overlay applies to the shipped template"
else
  fail "overlay failed on the shipped template: $(cat "$TMP/out")"
fi
PROPS="$P/src/main/resources/application.properties"
has_line "$PROPS" 'quarkus.langchain4j.easy-rag.path=rag' "easy-rag.path enabled"
# Classpath-relative, so the packaged application finds its documents wherever it starts (#151).
has_line "$PROPS" 'quarkus.langchain4j.easy-rag.path-type=classpath' "easy-rag.path-type classpath enabled"
has_line "$PROPS" 'quarkus.langchain4j.embedding-model.provider=dev.langchain4j.model.embedding.onnx.bgesmallenv15q.BgeSmallEnV15QuantizedEmbeddingModel' \
  "in-process embedding provider enabled"
has_line "$PROPS" '# quarkus.langchain4j.embedding-model.provider=ollama' "Ollama embedding alternative stays commented"
has_line "$PROPS" 'quarkus.langchain4j.mcp.ops.transport-type=streamable-http' "MCP client transport enabled"
has_line "$PROPS" '# quarkus.langchain4j.mcp.ops.transport-type=stdio' "stdio alternative stays commented"
has_line "$PROPS" 'quarkus.mcp.server.http.root-path=/mcp' "MCP server root-path enabled"
# The ${...} is a Quarkus property expression, matched literally, so no shell expansion.
# shellcheck disable=SC2016
has_line "$PROPS" '%test.quarkus.langchain4j.mcp.ops.url=http://localhost:${quarkus.http.test-port:8081}/mcp' \
  "MCP client points at the app's own server on the test port"
has_line "$PROPS" '%test.quarkus.langchain4j.ollama.chat-model.model-id=fake-default' "default model gets its own test id"
has_line "$PROPS" '%test.quarkus.langchain4j.ollama.main.chat-model.model-id=fake-main' "main model gets its own test id"
has_line "$PROPS" '%test.quarkus.langchain4j.ollama.smaller.chat-model.model-id=fake-smaller' "smaller model gets its own test id"
# The template turns ingestion off in the test profile (#113); the boot test needs it on.
has_line "$PROPS" '%test.quarkus.langchain4j.easy-rag.ingestion-strategy=on' \
  "boot test re-enables Easy RAG ingestion in the test profile"
if grep -qE '^(# *)?%test\.quarkus\.langchain4j\.easy-rag\.ingestion-strategy=off' "$PROPS"; then
  fail "the template's test-profile ingestion-strategy=off line survived the overlay"
else
  pass "no test-profile ingestion-strategy=off line left"
fi
active="$(grep -cE '^quarkus\.langchain4j\.embedding-model\.provider=' "$PROPS" || true)"
if [[ "$active" == 1 ]]; then
  pass "exactly one embedding provider active"
else
  fail "expected one active embedding provider, found $active"
fi
for f in src/main/resources/rag/refund-policy.md \
         src/test/java/org/acme/boot/FakeOllama.java \
         src/test/java/org/acme/boot/EntryServicesBootTest.java; do
  if [[ -s "$P/$f" ]]; then pass "fixture copied: $f"; else fail "fixture missing: $f"; fi
done

# 4. A key the overlay must enable disappears from the template.
for key in quarkus.mcp.server.http.root-path %test.quarkus.langchain4j.easy-rag.ingestion-strategy; do
  P="$TMP/missing-key"
  rm -rf "$P"
  new_project "$P"
  grep -vF "$key" "$TEMPLATE" >"$P/src/main/resources/application.properties"
  if python3 "$OVERLAY" "$P" "$FIXTURES" >"$TMP/out" 2>&1; then
    fail "missing key $key: overlay succeeded"
  elif grep -qF "$key" "$TMP/out"; then
    pass "missing key $key: failed loudly, naming the key"
  else
    fail "missing key $key: failed without naming the key: $(cat "$TMP/out")"
  fi
done

# 5. Easy RAG removed from the pom.
P="$TMP/no-easy-rag"
new_project "$P" quarkus-langchain4j-ollama
if python3 "$OVERLAY" "$P" "$FIXTURES" >"$TMP/out" 2>&1; then
  fail "pom without Easy RAG: overlay succeeded"
elif grep -q 'quarkus-langchain4j-easy-rag' "$TMP/out"; then
  pass "pom without Easy RAG: failed loudly"
else
  fail "pom without Easy RAG: unexpected output: $(cat "$TMP/out")"
fi

# 6. Unknown option: exits 2 without calling Maven.
rc=0
ci/build-from-templates.sh --bogus >"$TMP/out" 2>&1 || rc=$?
if [[ "$rc" == 2 ]] && grep -q 'unknown option --bogus' "$TMP/out"; then
  pass "unknown option rejected before generating anything"
else
  fail "unknown option: exit $rc, output: $(cat "$TMP/out")"
fi

if [[ "$failures" == 0 ]]; then
  echo 'OK: the boot overlay behaves as documented on all fixtures'
else
  echo "FAIL: $failures assertion(s) failed" >&2
  exit 1
fi
