---
name: quarkus-langchain4j-scaffolding
description: Scaffold and structure new Quarkus + LangChain4j projects, modules, AI services, agents, RAG pipelines, MCP clients and servers (Model Context Protocol), and embedding store setups. Use this whenever the user asks to create, scaffold, set up, bootstrap, initialize, start, generate, or kickstart a new Quarkus project, AI service, agent, RAG component, MCP client or server integration, embedding store, or related module in this stack. Also use for generating baseline pom.xml, application.properties, project layout, or starter classes for Quarkus + LangChain4j work.
---

# Quarkus + LangChain4j Scaffolding
# Version: 0.10.1

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
conventions — see §14.

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
  tools/      # @Tool CDI beans the AI services can call
  guardrails/ # input/output guardrails (optional)
  mcp/        # MCP server features (@Tool/@Prompt/@Resource offered to remote MCP clients)
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

Create the project with `quarkus_create` and let it generate the shell. The generated `pom.xml`
already imports the `quarkus-bom` and `quarkus-langchain4j-bom` platform BOMs, sets Java 25, enables
the `-parameters` compiler flag, adds a `native` profile, and pulls in the test stack
(`quarkus-junit` + `rest-assured`) — all at the current platform version. Do not hand-maintain any
of that: `quarkus_create` (the same codestart generator behind code.quarkus.io) keeps it up to date.

Pass these extensions to `quarkus_create`:

- core: `rest`, `rest-jackson`, `smallrye-openapi`, `websockets-next`, `langchain4j-ollama`
- agents: add `langchain4j-agentic`
- RAG: add `langchain4j-easy-rag`
- MCP client: add `langchain4j-mcp`
- MCP server: add `mcp-server-http` (io.quarkiverse.mcp; use `mcp-server-stdio` for a subprocess server)
- observability (optional): add `micrometer-registry-prometheus` and `opentelemetry`
- fault tolerance (optional): add `smallrye-fault-tolerance`

(`quarkus-arc` comes in automatically.) Then add the **non-extension** dependencies listed in
`templates/pom.xml.template` — the `dev.langchain4j` embedding model (required by Easy RAG) and,
for PDFs, the document parser — since project generators add only Quarkus extensions, not those.

## 4. AI service scaffolding

Use `templates/AiService.java.template`. It is a `@RegisterAiService` interface with
`@SystemMessage` / `@UserMessage` prompts and a typed return value, plus an optional
`@RegisterAiService(modelName = "…")` for selecting a named model. Pair it with a `rest/`
resource or a `web/` WebSocket endpoint to expose it.

## 5. Tool scaffolding

Use `templates/Tools.java.template`. Tools are plain `@ApplicationScoped` CDI beans with
`@Tool`-annotated methods the model may call. Wire them globally with
`@RegisterAiService(tools = TicketTools.class)` or per method with `@ToolBox(TicketTools.class)`.
Tools run blocking by default; keep blocking I/O (DB, REST) off the event loop by annotating the
method `@RunOnVirtualThread`. Validate a tool's arguments or results with tool-level guardrails —
see §10.

## 6. MCP client scaffolding (consume remote MCP tools)

Use `templates/McpClient.java.template`. An AI service can take its tools from one or more MCP
servers: annotate the service method with `@McpToolBox("name")`
(`io.quarkiverse.langchain4j.mcp.runtime`) — or `@McpToolBox` with no name to activate every
configured client — and declare each named client in `application.properties`
(`quarkus.langchain4j.mcp.<name>.transport-type` + `.url`; prefer `streamable-http`, or
`stdio` + `.command` for a local subprocess server). Requires the `langchain4j-mcp` extension (the
platform BOM manages its version). Local `@Tool` beans (§5) and MCP toolboxes combine freely on
the same service. Each client adds a readiness health check; disable with
`quarkus.langchain4j.mcp.health.enabled=false` when the remote server is optional at startup.

## 7. MCP server scaffolding (expose your app as an MCP server)

Use `templates/McpServer.java.template`. Annotate business methods with `@Tool` / `@ToolArg`
from `io.quarkiverse.mcp.server` (plus `@Prompt` / `@Resource` for reusable prompts and data)
to offer them to any MCP client over Streamable HTTP at `/mcp`
(`quarkus.mcp.server.http.root-path`). Requires the `mcp-server-http` extension
(`io.quarkiverse.mcp`, managed by the platform's `quarkus-mcp-server-bom` — no version pin);
use `mcp-server-stdio` instead when a desktop client spawns the app as a subprocess. Do not
confuse the two `@Tool` annotations: `io.quarkiverse.mcp.server.Tool` offers a method to remote
MCP clients, while `dev.langchain4j.agent.tool.Tool` (§5) offers it to your own model — the
template delegates to the `TicketTools` bean so one implementation backs both. Enable
`quarkus.mcp.server.traffic-logging.enabled=true` to watch the JSON-RPC exchanges in dev.

## 8. Agent scaffolding

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

## 9. RAG pipeline scaffolding

Use `templates/RagSetup.java.template`. Default to **Easy RAG**: add `quarkus-langchain4j-easy-rag`
plus an in-process embedding model (`langchain4j-embeddings-all-minilm-l6-v2`), drop documents
into the folder referenced by `quarkus.langchain4j.easy-rag.path`, and let Quarkus ingest them on
startup — no retriever code required. The template also includes a commented, **opt-in** manual
path (a CDI-produced `EmbeddingStore` + `EmbeddingStoreContentRetriever` + `RetrievalAugmentor`)
to use **only when a project needs control Easy RAG does not provide**.

## 10. Guardrails

Use `templates/Guardrails.java.template`. Guardrails are `@ApplicationScoped` CDI beans that
validate an AI service's inputs (`InputGuardrail`) and outputs (`OutputGuardrail`); attach them
with `@InputGuardrails(…)` / `@OutputGuardrails(…)` on the AI-service method or interface. Use the
upstream `dev.langchain4j.guardrail` API — the Quarkus-specific guardrail API was removed. An
output guardrail can force the model to answer again with `reprompt(…)`; cap attempts with
`quarkus.langchain4j.guardrails.max-retries` (default 3, 0 disables).

## 11. `application.properties` baseline

Use `templates/application.properties.template`. It configures the Ollama provider with a local
default model (cloud models shown as comments), a named `smaller` model for cheap subtasks,
generous timeouts, request/response logging, disabled Dev Services, and the Easy RAG documents
path. A commented MCP client block declares the named `ops` client used in §6. A commented MCP
server block sets the Streamable HTTP path and traffic logging for §7. A commented observability
block wires OTLP trace export and dev-only prompt/completion capture.

## 12. After scaffolding

Run and verify through the Quarkus Agents MCP (start dev mode, run tests via the Dev MCP tools)
rather than invoking Maven directly.

## 13. Test scaffolding

Use `templates/AiServiceTest.java.template`. Its active content is a `@QuarkusTest` wiring smoke
test (`ChatAssistantTest`) that injects the `ChatAssistant` AI service and asserts it is non-null:
booting Quarkus builds the CDI container and the AI-service proxy, so a green test proves wiring
and augmentation succeeded **without calling the model and without a running Ollama** — only
`quarkus-junit` is needed. The template also carries commented, opt-in examples: a model-dependent
test (live Ollama, `temperature=0`) and an **AI-quality evaluation** example (`Scorer` /
`@EvaluationTest` with semantic-similarity or AI-judge strategies), backed by
`quarkus-langchain4j-testing-evaluation-junit5` — already listed, test-scoped, in
`templates/pom.xml.template` (the platform BOM manages its version).

## 14. Cross-reference

For coding conventions to apply once scaffolding is done — Java language level, virtual threads,
records/sealed/pattern matching, declarative AI services, streaming, RAG, testing — see the
project's `CLAUDE.md` (Claude) or `AGENTS.md` (Codex). This skill does not duplicate those
conventions.
