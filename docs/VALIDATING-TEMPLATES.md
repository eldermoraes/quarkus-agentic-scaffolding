# Validating the templates

The templates in `skills/scaffold-project/templates/` are the product. As Quarkus
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
     extensions = "rest,rest-jackson,smallrye-openapi,websockets-next,langchain4j-ollama,langchain4j-agentic,langchain4j-easy-rag,langchain4j-mcp,mcp-server-http",
     noCode = true, noWrapper = false
   )
   ```

2. **Reconcile dependencies.** `pom.xml.template` no longer pins a platform version — `quarkus_create`
   owns the shell. Instead, confirm the generated `pom.xml` imports both `quarkus-bom` and
   `quarkus-langchain4j-bom` under `io.quarkus.platform`, and that the extension list above still
   resolves. Then confirm the **non-extension** deps in `pom.xml.template`
   (`langchain4j-embeddings-all-minilm-l6-v2`, `langchain4j-document-parser-apache-pdfbox`) still
   resolve via the BOM with no explicit `<version>`.

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

- **0.10.0 (2026-07-10):** platform `3.37.2`, `maven.compiler.release` 25.
  `ci/build-from-templates.sh 3.37.2` reconstructed the full template set — 19 `.java` files plus
  `application.properties` (20 materialized entries), now including the MCP pair
  (`TicketOpsAssistant` from McpClient, `TriageMcpServer` from McpServer) — and ran
  `mvn test-compile` to `BUILD SUCCESS`. The generated pom imported `quarkus-mcp-server-bom`
  (member BOM, no version pins) alongside `quarkus-bom` and `quarkus-langchain4j-bom`; the three
  non-extension dependencies injected and resolved. Quality gates at the same state: version
  consistency across 7 files (including `gemini-extension.json`), conventions parity, shellcheck,
  actionlint, markdownlint — all green.
- **0.9.0 (2026-07-10):** platform `3.37.2`, `maven.compiler.release` 25. `ci/build-from-templates.sh`
  reconstructed the full template set — 17 `.java` files plus `application.properties`
  (18 materialized entries) from the AiService, AiServiceTest, Agent (multi-file), Tools,
  Guardrails, and RagSetup templates — and ran `mvn test-compile`: 16 main sources compiled to
  `target/classes` and the `ChatAssistantTest` wiring smoke test compiled to `target/test-classes`
  (`BUILD SUCCESS`, `javac [... release 25]`). Confirms the agentic API, WebSockets Next, Mutiny,
  the `@Tool` and guardrail (`dev.langchain4j.guardrail`) imports, and the three injected
  non-extension deps — embedding model, PDF parser, and the test-scoped
  `quarkus-langchain4j-testing-evaluation-junit5` — all resolve on the platform BOM with no explicit
  `<version>`.
- **0.6.0 (2026-06-03):** platform `3.36.1`. After slimming `pom.xml.template` to a dependency
  reference: regenerated the shell via `quarkus_create` (core + agents + RAG — all extensions
  resolved) and confirmed the two non-extension deps now listed in the template
  (`langchain4j-embeddings-all-minilm-l6-v2`, `langchain4j-document-parser-apache-pdfbox`) resolve
  via `quarkus-langchain4j-bom` with **no** `<version>` (1.14.1-beta24). `BUILD SUCCESS`.
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

## Automated validation

Two mechanisms run these drift checks for you. Both are **backstops** — the Quarkus Agents MCP is
**not** available in CI, so CI reconstructs the project statically (it cannot call `quarkus_create`)
and the MCP procedure above stays the source of truth.

**Static compile in CI.** `ci/build-from-templates.sh` scripts the **static fallback** above — it
reconstructs a project from `templates/` and compiles it — and `.github/workflows/validate-templates.yml`
runs that script two ways:

- on every **push and pull request**, against the versions pinned in `ci/baseline.env`, so builds
  stay reproducible, and
- on a **weekly cron (Mondays, 05:00 UTC)**, against the **live latest** Quarkus platform, so a new
  release that breaks the templates is caught even when nothing in the repo changed.

A failing scheduled run opens a tracking issue (labeled `build failed`), or comments on the
existing one; close it manually once a later run is green.

**Release watching (Renovate).** `renovate.json` watches the entries in `ci/baseline.env` and
surfaces new releases on the repo's **Dependency Dashboard** issue for approval — it raises no
automatic PRs. It tracks the Quarkus platform (`quarkus-bom`, via Maven Central), the
`quarkus-langchain4j` BOM, and new OpenJDK GA releases (via the `java-version` datasource). Ticking a
dashboard checkbox is what turns a noticed release into a bump; independently, the weekly cron above
catches breakage whether or not anyone has ticked it.

> **Activation is a user action.** Renovate only runs once the **Mend Renovate GitHub App** is
> installed on the repository. Until then `renovate.json` sits inert and no Dependency Dashboard
> appears.

Treat CI as a backstop, not a replacement: a green run means the Java still **compiles**, not that a
full Quarkus augmentation (Easy RAG, model wiring) succeeds — that requires the MCP procedure, which
remains the source of truth.
