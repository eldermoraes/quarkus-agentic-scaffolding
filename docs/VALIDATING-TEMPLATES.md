# Validating the templates

The templates in `skills/quarkus-langchain4j-scaffolding/templates/` are the product. As Quarkus
and LangChain4j evolve, two things can rot:

1. the pinned **platform version** in `pom.xml.template` falls behind, and
2. a **library API** the templates use (especially the LangChain4j *agentic* annotations) changes.

This page describes how to confirm the templates still produce a **compiling** project. Run it
before shipping a release, and whenever you touch a template.

> Tooling note: per `CLAUDE.md` §1, do Quarkus work through the **Quarkus Agents MCP**, not raw
> Maven. The MCP procedure below is primary; the static fallback is for environments (e.g. CI)
> where the MCP and a live Ollama are not available.

## Primary procedure (Quarkus Agents MCP)

1. **Create a throwaway project** with the template's extensions:

   ```
   quarkus_create(
     outputDir = "/tmp", artifactId = "ql4j-validate",
     extensions = "rest,rest-jackson,smallrye-openapi,websockets-next,langchain4j-ollama,langchain4j-agentic,langchain4j-easy-rag",
     noCode = true, noWrapper = false
   )
   ```

2. **Reconcile the version.** Read `quarkus.platform.version` from the generated `pom.xml`. If it is
   newer than the value in `pom.xml.template`, update the template (it is a reference baseline only).
   Also confirm the generated pom still imports `quarkus-langchain4j-bom` under
   `io.quarkus.platform` at the platform version — the template assumes this.

3. **Materialize the templates** into `src/main/java/org/acme/` and `src/main/resources/`:
   - copy `AiService.java.template` → `ai/ChatAssistant.java`
   - copy `RagSetup.java.template` → `rag/RagAssistant.java`
   - copy `application.properties.template` → `resources/application.properties`
   - split `Agent.java.template` into its per-file sections (each block is headed by a
     `/* ===== File: <path> ===== */` marker) under `dto/`, `ai/`, `workflow/`, `web/`.

4. **Build/run via the MCP.** Start dev mode (`quarkus_start`) with a real Ollama endpoint reachable
   and an in-process embedding model on the classpath (`langchain4j-embeddings-all-minilm-l6-v2`)
   plus `quarkus.langchain4j.easy-rag.path` set, so Easy RAG augmentation is satisfied. A clean
   start means augmentation **and** compilation succeeded.

## Static fallback (JDK 25, no Ollama)

When you only need to know *"does the template Java still compile against the current extensions?"*
— which is what catches agentic-API drift — a plain compile is enough and needs no Ollama:

1. Generate the project as above and materialize the templates.
2. Remove the `quarkus-langchain4j-easy-rag` dependency from the throwaway pom (it would otherwise
   require an embedding model and a configured path at *augmentation*; `RagAssistant` compiles
   without it). The easy-rag coordinate itself is already validated by `quarkus_create` resolving it.
3. Compile with a JDK 25:

   ```
   JAVA_HOME=/path/to/jdk-25 ./mvnw -B -ntp -DskipTests compile
   ```

   `BUILD SUCCESS` with `javac [... release 25]` over all source files means every import and
   annotation the templates use still resolves.

## Last validated

- **0.5.0 (2026-06-03):** platform `3.36.1`, `maven.compiler.release` 25. Generated a throwaway
  project with the `rest-jackson` extension list and compiled all 14 materialized template files
  (`BUILD SUCCESS`, `javac [... release 25]`) — confirms `quarkus-rest-jackson` resolves on the
  platform BOM and the agentic API (`@SequenceAgent` / `@ParallelAgent` / `@Output`, `AgenticScope`),
  WebSockets Next, and Mutiny imports still resolve. Template baseline bumped `3.36.0` → `3.36.1` to
  match the freshly generated pom.
- **0.2.0 (2026-06-01):** platform `3.36.0`, `maven.compiler.release` 25. All template files
  compiled (`BUILD SUCCESS`); the agentic API (`dev.langchain4j.agentic.*`, `@SequenceAgent` /
  `@ParallelAgent` / `@Output`, `AgenticScope`), WebSockets Next, and Mutiny imports all resolved.
  The generated pom confirmed the `quarkus-langchain4j-bom` strategy. Template version bumped
  `3.35.3` → `3.36.0` to match.

## Optional: CI (best-effort static check)

CI can run the **static fallback** to catch drift automatically, but note that the Quarkus Agents
MCP is **not** available in CI — so CI reconstructs the project statically (it cannot call
`quarkus_create`), and the MCP procedure above stays the source of truth. A minimal GitHub Actions
job:

```yaml
# .github/workflows/validate-templates.yml
name: validate-templates
on: [push, pull_request]
jobs:
  compile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: graalvm, java-version: '25' }
      # Reconstruct a project from templates/, then `mvn -B -DskipTests compile`.
      # Keep the reconstruction script alongside this workflow; update it when the
      # template set changes so a new/renamed template can't silently escape the check.
      - run: ./ci/build-from-templates.sh
```

Treat CI as a backstop, not a replacement: a green run means the Java still compiles, not that a
full Quarkus augmentation (Easy RAG, model wiring) succeeds — that requires the MCP procedure.
