# Validating the templates

The templates in `skills/scaffold-project/templates/` are the product. As Quarkus
and LangChain4j evolve, two things can rot:

1. the **platform version** the templates were last built against (`ci/baseline.env`) falls
   behind, and
2. a **library API** the templates use (especially the LangChain4j *agentic* annotations) changes.

This page describes how to confirm the templates still produce a project that **compiles,
starts and answers requests**. Run it before shipping a release, and whenever you touch a template.

> Tooling note: per `CLAUDE.md` §1, do Quarkus work through the **Quarkus Agents MCP**, not raw
> Maven. The MCP procedure below is primary; the scripted boot test is for environments (e.g. CI)
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
   (`langchain4j-guardrails`, `langchain4j-embeddings-bge-small-en-v15-q`,
   `langchain4j-document-parser-apache-pdfbox`, and the test-scoped
   `quarkus-langchain4j-testing-evaluation-junit5`) still resolve via the BOM with no explicit
   `<version>`.

3. **Materialize the templates** into `src/main/java/org/acme/` and `src/main/resources/` (the
   same mapping `ci/build-from-templates.sh` applies; the templates import each other, so a
   partial set does not compile):
   - copy `AiService.java.template` → `ai/ChatAssistant.java`
   - copy `RestResource.java.template` → `rest/ChatResource.java`
   - copy `Tools.java.template` → `tools/TicketTools.java`
   - copy `Guardrails.java.template` → `guardrails/PromptInjectionGuard.java`
   - copy `McpClient.java.template` → `ai/TicketOpsAssistant.java`
   - copy `McpServer.java.template` → `mcp/TriageMcpServer.java`
   - copy `RagSetup.java.template` → `rag/RagAssistant.java`
   - copy `AiServiceTest.java.template` → `src/test/java/org/acme/ai/ChatAssistantTest.java`
   - copy `application.properties.template` → `resources/application.properties`
   - split `Agent.java.template` into its per-file sections (each block is headed by a
     `/* ===== File: <path> ===== */` marker) under `dto/`, `ai/`, `workflow/`, `web/`.

4. **Build/run via the MCP.** Start dev mode (`quarkus_start`) with a real Ollama endpoint reachable
   and an in-process embedding model on the classpath (`langchain4j-embeddings-bge-small-en-v15-q`)
   plus all four keys of the RAG block set (`quarkus.langchain4j.easy-rag.path-type=classpath`,
   `quarkus.langchain4j.easy-rag.path=rag` with a document in `src/main/resources/rag`,
   `quarkus.langchain4j.embedding-model.provider` and
   `%test.quarkus.langchain4j.easy-rag.ingestion-strategy=off`), so Easy RAG augmentation is
   satisfied. A clean start means augmentation **and** compilation succeeded.

5. **Run the tests through the Dev MCP**, as `scaffold-project` §12 prescribes:
   `quarkus_callTool` `devui-testing_runTests` with dev mode up. The dev log must show Easy RAG
   ingesting at startup (the dev-mode JVM has then loaded the embedding model's native library),
   and the run must report `ChatAssistantTest#aiServiceIsWired()` passing. A failure reading
   `Native Library … already loaded in another classloader` means the test profile loaded the
   embedding model a second time inside that JVM (#113). PR CI cannot run this step (no MCP
   there), so it is part of the pre-release validation together with the scripted boot test
   below.

## Scripted boot test (JDK 25, no Ollama)

`ci/build-from-templates.sh` reconstructs the project and boots it with a fake model, so it needs
neither the MCP nor a live Ollama:

```
ci/build-from-templates.sh 3.40.1.2          # boot test against a given platform
ci/build-from-templates.sh                   # boot test against the latest stable platform
ci/build-from-templates.sh --compile-only    # quick check: stop after mvn test-compile
```

It needs Maven, python3 and a JDK 25. What it does:

1. Generates the project with the quarkus-maven-plugin (the extension list above, `-DnoCode`) and
   materializes every template, as in step 3.
2. Injects the non-extension dependencies from `pom.xml.template`. Easy RAG and the in-process
   embedding model stay in.
3. Applies the boot overlay (`ci/boot_overlay.py`): uncomments the template's RAG keys
   (`easy-rag.path-type`, `easy-rag.path`, `embedding-model.provider`, and the test-profile
   `ingestion-strategy`, which
   it then sets back to `on`: the template skips ingestion in tests so continuous testing works,
   while this test runs in its own JVM and asserts on retrieved passages), the `ops` MCP client
   keys and the MCP server `root-path`, points the `ops` client at the application's own MCP
   server on the test port, gives the default, `main` and `smaller` models distinct `%test` model
   ids (`fake-default`, `fake-main`, `fake-smaller`; a model id is fixed at build time, so the
   test resource cannot set it), adds a sample document to the RAG folder and copies the test
   fixtures into `src/test/java`. A key it
   must uncomment and cannot find stops the run with the key's name, so a template change cannot
   silently switch off part of the test.
4. Runs `mvn -B -ntp test`.
5. Packages the project (`mvn package -DskipTests`) and starts
   `java -jar target/quarkus-app/quarkus-run.jar` from an empty temporary directory, as a
   container image does, on `QUARKUS_HTTP_PORT` (default 8080). It passes once the started
   process is alive, its own log says it listens on that port, the port answers (each poll
   times out after 5 s) and the log shows Easy RAG's `Ingested N files` with N > 0. A port
   another process already holds fails the step with a message saying so, since an answer from
   that process would prove nothing. The process is stopped (SIGTERM, then SIGKILL after 10 s)
   and its directory removed on every exit, an interrupted run included. A documents path
   resolved against the working directory fails here (#151). No model is called at startup,
   and the MCP client does not connect at startup (the packaged application started with its
   URL pointing at a closed port), so the URL needs no override. Measured on 2026-11-12 (platform 3.40.1.2): the step adds about
   8 seconds on a quiet machine (whole script 27 s against 19 s without it), and up to 55
   under heavy load (package 26–39 s, start 9–16 s).

The fixtures live in `ci/fixtures/boot-test/`. They are **CI fixtures, not shipped templates**:
the `scaffold-project` skill never copies them into a user's project.

- `FakeOllama` is a `QuarkusTestResource` that serves the Ollama chat API from a JDK `HttpServer`
  and points the default, `main` and `smaller` models at it. It answers plain text, or a JSON
  object filling every property of the schema a record-returning service sends (an `enum`
  property gets its first value), and records every request. Its recording API — `requests()`,
  `userTurns(request)`, `schemaProperties(request)`, `reset()`, `answerNextWith(...)` and
  `answerNextFor(schemaProperties, ...)`, which aims answers at one agent's requests — is the
  seam for regression tests on model routing, retrieval scoping, output validation and request
  isolation, so keep it stable.
- `EntryServicesBootTest` drives the chat REST endpoint, the triage bridge, the RAG assistant and
  the MCP-client assistant: ordinary input must produce a recorded model request, and input
  carrying reserved delimiter markup must be rejected with no model request. It also checks that
  each triage agent's request names the model the agent declares, at that model's temperature,
  and that only the RAG assistant's request carries the sample document's text. With the fake
  answering `{}` or null fields once, the triage asks again and reports DONE with a complete
  report; answering `{}` every time, it reports ERROR; answering a complete object with one field
  no record declares, it reports DONE without asking again; each agent's JSON schema lists every
  field as required; the priority agent's schema lists `LOW`, `MEDIUM` and `HIGH` for the level;
  with the fake answering another level once, the triage asks again and reports DONE, and
  answering it every time, ERROR; the triage WebSocket sends the level as a plain string; and of
  two tickets triaged in sequence, the second's requests carry no text of the first, the
  Synthesizer's no raw ticket.

The generated pom carries no REST Assured (`-DnoCode` adds no test dependencies beyond
`quarkus-junit`), so the fixtures call the endpoint with the JDK `HttpClient`.

**What a green run proves.** Against the platform it ran on: every template compiles; Quarkus
augmentation and startup succeed with Easy RAG ingesting a document through the in-process
embedding model, the MCP server and the MCP client connected to it; the packaged application
starts from another working directory and ingests its documents; the `ChatAssistantTest` wiring
smoke test passes; each entry service passes ordinary input to the model and rejects reserved
delimiter markup before any model call; each triage agent reaches the model it names;
retrieved content reaches the RAG assistant only; an incomplete structured answer is asked
again and, if it stays incomplete, reported as an error, while an extra field is accepted; a
priority level outside the three allowed values is treated like an incomplete answer; and one
triage's ticket does not reach the model requests of the next. It does **not** prove anything
about answer quality or a real model's behavior (tool calling, structured output from a live
model): the fake answers with fixed text.

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
  (`langchain4j-embeddings-bge-small-en-v15-q`, `langchain4j-document-parser-apache-pdfbox`) resolve
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
**not** available in CI, so CI generates the project with the Maven plugin (it cannot call `quarkus_create`)
and the MCP procedure above stays the source of truth.

**Boot test in CI.** `.github/workflows/validate-templates.yml` runs the **scripted boot test**
above (`ci/build-from-templates.sh`, without `--compile-only`) on three occasions:

- on every **pull request**, whatever files it changes, and on every **push to `main`** that
  touches `skills/`, `ci/`, `.github/actions/` or the workflow itself, against the versions pinned
  in `ci/baseline.env`, so builds stay reproducible. The job is named `boot`, and that name is the
  status check to require on `main`; pull requests carry no paths filter because a required check
  that never starts blocks the pull request;
- on **manual runs** (`workflow_dispatch`), against the live latest platform as below;
- on a **weekly cron (Mondays, 05:00 UTC)**, against the **live latest stable** Quarkus platform
  (the highest purely numeric version in Maven Central's metadata, platform respins such as
  `3.40.1.1` included; Alpha/Beta/CR pre-releases are skipped), so a
  new release that breaks the templates is caught even when nothing in the repo changed.

A failing scheduled run opens a tracking issue (labeled `build failed`), or comments on the
existing one; the next green scheduled run closes it automatically. The `boot` job, which builds
and runs the generated project with Maven, holds a token that can only read the repository
(`contents: read`, and its checkout does not keep the token in the git config); a separate
`boot-report` job, which runs only on scheduled runs, holds `issues: write` to open or close the
issue. Pull requests, pushes, manual runs and cancelled runs never touch the issue.

**Release watching (Renovate).** `renovate.json` watches the entries in `ci/baseline.env` and
opens a PR for each new release (`dependencyDashboardApproval` is `false`); the repo's
**Dependency Dashboard** issue lists what is open or pending. It tracks the Quarkus platform (`quarkus-bom`, via Maven Central), the
`quarkus-langchain4j` BOM, and new OpenJDK GA releases (via the `java-version` datasource), plus
the pinned MCP versions in the setup skill, the README and `gemini-extension.json`. Merging the PR
is what turns a noticed release into a bump; independently, the weekly cron above catches breakage
whether or not anyone has merged it.

> **Activation is a user action.** Renovate only runs once the **Mend Renovate GitHub App** is
> installed on the repository. Until then `renovate.json` sits inert and no Dependency Dashboard
> appears.

Treat CI as a backstop, not a replacement: a green run means the generated project starts and its
entry services handle requests against a fake model (see "What a green run proves" above). Whether
a live model behaves as the templates expect still needs the MCP procedure with a real Ollama, which
remains the source of truth.
