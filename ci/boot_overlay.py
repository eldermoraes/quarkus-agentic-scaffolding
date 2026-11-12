#!/usr/bin/env python3
"""Boot overlay for the project ci/build-from-templates.sh generates from the templates.

Turns the materialized project into one that `mvn test` can start without a live model:

  1. checks that the Easy RAG extension is still in the pom (the boot test exercises ingestion
     and embedding-provider selection, so it must not be dropped);
  2. uncomments the template's RAG, MCP-client and MCP-server keys in application.properties,
     each at its first commented occurrence (the template's primary choice, not the
     alternatives listed after it), then sets the RAG block's test-profile
     ingestion-strategy back to on: the template skips ingestion in tests for continuous
     testing (#113), while the boot test runs in its own JVM and asserts on retrieval;
  3. copies the sample documents into the folder the uncommented easy-rag.path names (under
     src/main/resources when easy-rag.path-type is classpath);
  4. adds a %test override pointing the "ops" MCP client at the application's own MCP server
     on the Quarkus test port, so the client has a server to connect to;
  5. adds %test model ids that tell the default, "main" and "smaller" models apart (the
     template gives the default and "main" models the same id; a model id is fixed at build
     time, so the fake's test resource cannot override it);
  6. copies the CI test fixtures (fake Ollama + entry-service boot test) into src/test/java.

A key it must uncomment and cannot find fails the run and names the key: a template change
must not silently switch off part of the boot test.

Usage: boot_overlay.py <project-dir> <fixtures-dir>
  <fixtures-dir> holds java/ (test sources, copied as-is under src/test/java) and rag/
  (documents for Easy RAG).
"""
import pathlib
import re
import shutil
import sys

TEST_INGESTION_KEY = "%test.quarkus.langchain4j.easy-rag.ingestion-strategy"
# Keys the template ships commented out and the boot test needs active, in template order.
KEYS_TO_ENABLE = (
    "quarkus.langchain4j.easy-rag.path-type",
    "quarkus.langchain4j.easy-rag.path",
    "quarkus.langchain4j.embedding-model.provider",
    TEST_INGESTION_KEY,
    "quarkus.langchain4j.mcp.ops.transport-type",
    "quarkus.langchain4j.mcp.ops.url",
    "quarkus.mcp.server.http.root-path",
    "quarkus.mcp.server.support-langchain4j-annotations",
)
# Distinct model ids per configured model; FakeOllama.java names the same values.
TEST_MODEL_IDS = (
    ("quarkus.langchain4j.ollama.chat-model.model-id", "fake-default"),
    ("quarkus.langchain4j.ollama.main.chat-model.model-id", "fake-main"),
    ("quarkus.langchain4j.ollama.smaller.chat-model.model-id", "fake-smaller"),
)
EASY_RAG_ARTIFACT = "quarkus-langchain4j-easy-rag"
TEST_PORT = "${quarkus.http.test-port:8081}"


def fail(message):
    sys.exit(f"ERROR: {message}")


def enable_keys(text, keys):
    """Uncomment the first commented assignment of each key; an active one is left alone.

    Returns (new_text, values, missing): values maps each found key to its value.
    """
    lines = text.split("\n")
    values, missing = {}, []
    for key in keys:
        active = re.compile(rf"^{re.escape(key)}\s*=\s*(.*)$")
        commented = re.compile(rf"^#\s*{re.escape(key)}\s*=\s*(.*)$")
        hit = next((i for i, line in enumerate(lines) if active.match(line)), None)
        if hit is None:
            hit = next((i for i, line in enumerate(lines) if commented.match(line)), None)
            if hit is None:
                missing.append(key)
                continue
            lines[hit] = lines[hit].lstrip("#").lstrip()
        values[key] = active.match(lines[hit]).group(1).strip()
    return "\n".join(lines), values, missing


def main(argv):
    if len(argv) != 3:
        fail("usage: boot_overlay.py <project-dir> <fixtures-dir>")
    proj, fixtures = pathlib.Path(argv[1]), pathlib.Path(argv[2])

    pom = (proj / "pom.xml").read_text()
    if f"<artifactId>{EASY_RAG_ARTIFACT}</artifactId>" not in pom:
        fail(f"{EASY_RAG_ARTIFACT} is not in the generated pom.xml; the boot test needs Easy RAG")

    props_path = proj / "src/main/resources/application.properties"
    text, values, missing = enable_keys(props_path.read_text(), KEYS_TO_ENABLE)
    if missing:
        fail("application.properties has no line (commented or active) for "
             + ", ".join(missing)
             + "; the boot overlay must enable it. Update KEYS_TO_ENABLE in ci/boot_overlay.py "
               "together with the template.")

    # The template skips ingestion in the test profile so continuous testing inside the
    # dev-mode JVM does not load the embedding model's native library twice (#113). The boot
    # test runs under `mvn test` in a JVM of its own and asserts on retrieved passages, so it
    # turns ingestion back on, in place.
    template_line = f"\n{TEST_INGESTION_KEY}={values[TEST_INGESTION_KEY]}\n"
    if template_line not in text:
        fail(f"cannot turn ingestion back on: no line {template_line.strip()!r} in "
             f"{props_path} after enabling the keys")
    text = text.replace(template_line,
                        f"\n# Boot test: ingestion back on (see ci/boot_overlay.py).\n"
                        f"{TEST_INGESTION_KEY}=on\n", 1)
    values[TEST_INGESTION_KEY] = "on"

    mcp_root = values["quarkus.mcp.server.http.root-path"]
    text = text.rstrip("\n") + (
        "\n\n# --- Added by ci/boot_overlay.py (CI boot test only) ---\n"
        "# The MCP client talks to this application's own MCP server on the test port.\n"
        f"%test.quarkus.langchain4j.mcp.ops.url=http://localhost:{TEST_PORT}{mcp_root}\n"
        "# Distinct model ids, so a recorded request shows which configured model it reached.\n"
        + "".join(f"%test.{key}={value}\n" for key, value in TEST_MODEL_IDS))
    props_path.write_text(text)
    for key in KEYS_TO_ENABLE:
        print(f"enabled {key}={values[key]}")

    # A classpath path is relative to the resources root; a filesystem one, to the working
    # directory, which for `mvn test` is the project directory.
    rag_root = proj / "src/main/resources" if (
        values["quarkus.langchain4j.easy-rag.path-type"] == "classpath") else proj
    rag_dir = rag_root / values["quarkus.langchain4j.easy-rag.path"]
    rag_dir.mkdir(parents=True, exist_ok=True)
    docs = sorted((fixtures / "rag").glob("*"))
    if not docs:
        fail(f"no documents in {fixtures / 'rag'}")
    for doc in docs:
        shutil.copy(doc, rag_dir / doc.name)
        print(f"added RAG document {rag_dir.relative_to(proj) / doc.name}")

    test_root = proj / "src/test/java"
    sources = sorted((fixtures / "java").rglob("*.java"))
    if not sources:
        fail(f"no Java fixtures in {fixtures / 'java'}")
    for src in sources:
        dest = test_root / src.relative_to(fixtures / "java")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)
        print(f"added test fixture {dest.relative_to(proj)}")


if __name__ == "__main__":
    main(sys.argv)
