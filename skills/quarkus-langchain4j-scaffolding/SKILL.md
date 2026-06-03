---
name: quarkus-langchain4j-scaffolding
description: Scaffold and structure new Quarkus + LangChain4j projects, modules, AI services, agents, RAG pipelines, and embedding store setups. Use this whenever the user asks to create, scaffold, set up, bootstrap, initialize, start, generate, or kickstart a new Quarkus project, AI service, agent, RAG component, embedding store, or related module in this stack. Also use for generating baseline pom.xml, application.properties, project layout, or starter classes for Quarkus + LangChain4j work.
---

# Quarkus + LangChain4j Scaffolding
# Version: 0.3.0

## 1. When to use this skill

Use this skill when **creating something new** in a Quarkus + LangChain4j project:

- Create, scaffold, bootstrap, initialize, start, generate, or kickstart a new Quarkus +
  LangChain4j **project** or **module**.
- Add a new **AI service** (`@RegisterAiService` interface).
- Add a new **agent** or **multi-agent workflow** (declarative LangChain4j Agentic).
- Set up a **RAG** component or **embedding store**.
- Generate a baseline **`pom.xml`**, **`application.properties`**, **project layout**, or starter
  classes for this stack.

This skill covers *how to lay things out and get them running*. It does **not** restate coding
conventions — see §9.

**Required tooling (mandatory).** This skill must not scaffold without it. Create the project and
discover extensions through the **Quarkus Agents MCP** (`quarkus_create`, `quarkus_searchTools`),
and call `quarkus_skills` for each chosen extension **before** writing any code — never create a
Quarkus project or add an extension by hand. Use **context7** for every LangChain4j and other
library API lookup. If either tool is unavailable, stop and report it rather than guessing. These
are project prerequisites; see `CLAUDE.md` §1 or `AGENTS.md` §1.

## 2. Project layout convention

Single-module Quarkus application (no multi-module reactor by default). Organize one root
package into focused sub-packages:

```
src/main/java/<group>/<app>/
  ai/         # @RegisterAiService interfaces (AI services and agents)
  dto/        # records: inputs, reports, and event/step types
  workflow/   # agentic orchestrators + the streaming-bridge beans
  rest/       # JAX-RS resources (@Path)
  web/        # WebSocket endpoints (@WebSocket)
  rag/        # RagConfig producers (only when escalating beyond Easy RAG)
  memory/     # chat-memory store + provider (optional, persistent memory)
src/main/resources/
  application.properties
  rag/        # documents folder ingested by Easy RAG (quarkus.langchain4j.easy-rag.path)
```

Start with only the sub-packages a feature needs; add the rest as the project grows.

## 3. Dependency baseline

Start from `templates/pom.xml.template`. It pins Java 25 as the minimum, imports the `quarkus-bom`
and `quarkus-langchain4j-bom` platform BOMs, and includes the core extensions
(`quarkus-rest` + `quarkus-rest-jsonb`, `quarkus-arc`, `quarkus-smallrye-openapi`,
`quarkus-websockets-next`, `quarkus-langchain4j-ollama`), the test stack (`quarkus-junit` +
`rest-assured`), the `-parameters` compiler flag, and a `native` profile. The template marks
which dependencies to add for **agents** (`quarkus-langchain4j-agentic`) and for **RAG**
(`quarkus-langchain4j-easy-rag` + an in-process embedding model).

When creating the project through the Quarkus Agents MCP, pass the matching extensions to
`quarkus_create` and reconcile the generated `pom.xml` with the template.

## 4. AI service scaffolding

Use `templates/AiService.java.template`. It is a `@RegisterAiService` interface with
`@SystemMessage` / `@UserMessage` prompts and a typed return value, plus an optional
`@RegisterAiService(modelName = "…")` for selecting a named model. Pair it with a `rest/`
resource or a `web/` WebSocket endpoint to expose it.

## 5. Agent scaffolding

Use `templates/Agent.java.template`. It shows the full declarative agentic shape:

- individual `@Agent` AI services (sub-agents) returning records;
- an orchestrator interface using `@SequenceAgent` / `@ParallelAgent` (and the
  `@SupervisorAgent` + `@SupervisorRequest` variant for routing) with `@Output` assembling the
  result from the `AgenticScope`;
- an `@ApplicationScoped` streaming bridge that runs the blocking workflow on a virtual thread
  and emits progress over a Mutiny `Multi`;
- the `@WebSocket` endpoint that delegates to the bridge.

Requires the `quarkus-langchain4j-agentic` extension. Call `quarkus_skills` for it before writing
the workflow.

## 6. RAG pipeline scaffolding

Use `templates/RagSetup.java.template`. Default to **Easy RAG**: add `quarkus-langchain4j-easy-rag`
plus an in-process embedding model (`langchain4j-embeddings-all-minilm-l6-v2`), drop documents
into the folder referenced by `quarkus.langchain4j.easy-rag.path`, and let Quarkus ingest them on
startup — no retriever code required. The template also includes a commented, **opt-in** manual
path (a CDI-produced `EmbeddingStore` + `EmbeddingStoreContentRetriever` + `RetrievalAugmentor`)
to use **only when a project needs control Easy RAG does not provide**.

## 7. `application.properties` baseline

Use `templates/application.properties.template`. It configures the Ollama provider with a local
default model (cloud models shown as comments), a named `smaller` model for cheap subtasks,
generous timeouts, request/response logging, disabled Dev Services, and the Easy RAG documents
path.

## 8. After scaffolding

Run and verify through the Quarkus Agents MCP (start dev mode, run tests via the Dev MCP tools)
rather than invoking Maven directly.

## 9. Cross-reference

For coding conventions to apply once scaffolding is done — Java language level, virtual threads,
records/sealed/pattern matching, declarative AI services, streaming, RAG, testing — see the
project's `CLAUDE.md` (Claude) or `AGENTS.md` (Codex). This skill does not duplicate those
conventions.
