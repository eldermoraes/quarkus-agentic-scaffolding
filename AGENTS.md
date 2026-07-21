# Quarkus + LangChain4j + AI Stack - Project Conventions
# Version: 0.12.1

These conventions apply whenever Codex or Bob writes, reviews, or configures code in a Quarkus +
LangChain4j project. They are always-on. Procedural scaffolding steps and starter code live in
the `scaffold-project` skill and its templates, not here.

---

## 1. Required tooling (mandatory)

These tools are prerequisites for this project, not suggestions. Do not work around their absence:
if a required tool is unavailable, stop and report it rather than falling back to model memory or a
generic web search.

- **Quarkus Agents MCP - required for every Quarkus task.** Project creation, extension selection,
  configuration, version checks, API usage, and troubleshooting MUST go through the Quarkus Agents
  MCP. Never create a Quarkus project or add an extension by hand, and never answer a Quarkus
  question from model memory before consulting it.
- **context7 - required for external library and framework documentation.** Before relying on
  memory or web search for any library or framework API - LangChain4j included - you MUST look it
  up with `context7` first.
- **superpowers skills - use whenever applicable.** Invoke the relevant `superpowers` skill
  capabilities for the task at hand.

---

## 2. Java conventions

- **Java 25 is the minimum language level**, not a ceiling. Compile with
  `maven.compiler.release` set to at least 25 and adopt newer language levels freely. Document
  any project that must pin an older level and explain why (see section 6). One cap applies to
  native targets: GraalVM ships no releases for JDK 26, 27, or 28, so native-image stays on the
  JDK 25 baseline (with quarterly updates) until JDK 29 lands (September 2027) - projects that
  build a native binary keep `maven.compiler.release` at 25 until then
  ([GraalVM release-train announcement](https://medium.com/graalvm/accelerating-the-graalvm-release-train-26b0d7cff2ab)).
- **Default to Virtual Threads for I/O-bound and blocking concurrent work.** Platform threads
  are acceptable only when the runtime or a critical dependency forbids virtual threads (for
  example, a JDBC driver that pins the carrier). When a blocking AI or tool call must run inside
  a reactive endpoint, run it on a virtual thread rather than on the event loop.
- **Use Scoped Values in place of `ThreadLocal`** for request- or agent-scoped identity that
  must survive virtual-thread continuations, avoiding the leakage and inheritance pitfalls of
  `ThreadLocal`.
- **Structured concurrency for related subtasks.** For fan-out across related concurrent
  subtasks, prefer declarative parallelism (LangChain4j `@ParallelAgent` / `@ParallelMapperAgent`,
  see section 4) or explicit virtual-thread fan-out (`Thread.startVirtualThread(...)` or an
  `Executors.newVirtualThreadPerTaskExecutor()`), instead of ad-hoc executor coordination.
  `StructuredTaskScope` is the preferred structured-concurrency primitive where the project can
  enable it; note it is a Java preview feature (requires `--enable-preview`) with GraalVM
  native-image considerations, so adopt it only when the preview flag and the native target
  allow.
- **Prefer records, sealed types, and pattern matching where they clarify intent.** Use records
  for DTOs and value objects (they also minimize the GraalVM reflection surface), sealed
  interfaces for closed hierarchies such as event or result types, and pattern-matching `switch`
  over those hierarchies so the compiler enforces exhaustiveness.

---

## 3. Quarkus conventions

- **Import the platform BOMs; do not pin extension versions.** Import `quarkus-bom` and
  `quarkus-langchain4j-bom` at the same platform version and let the BOMs manage every extension
  and LangChain4j version.
- **CDI-first.** Use `quarkus-arc` and standard CDI (`@ApplicationScoped`, `@Inject`,
  `@Produces`) for wiring. Produce framework objects (retrieval augmentors, memory providers,
  embedding stores) from `@ApplicationScoped` producer beans.
- **REST and API surface.** Use `quarkus-rest` (Quarkus REST) with `quarkus-rest-jackson` for JSON
  (Jackson is the Quarkus default serializer), and expose `quarkus-smallrye-openapi` so endpoints
  are documented and explorable.
- **Streaming uses WebSockets Next.** For token or progress streaming, use
  `quarkus-websockets-next` rather than rolling a custom transport (see section 4 for the
  streaming pattern).
- **Observability comes from platform extensions, not code.** Add
  `quarkus-micrometer-registry-prometheus` (metrics, scraped at `/q/metrics`) and
  `quarkus-opentelemetry` (traces) and AI services are instrumented automatically: per-method
  timers and counters (`langchain4j.aiservices.*`), GenAI-semconv token usage
  (`gen_ai.client.token.usage`, tagged by operation and token type), one span per AI-service
  call (`langchain4j.aiservices.<Interface>.<method>`) and per tool call
  (`langchain4j.tools.<tool>`). Register a CDI `CostEstimator` bean
  (`io.quarkiverse.langchain4j.cost`) to emit `gen_ai.client.estimated_cost`. Prompt and
  completion text reaches spans only when explicitly enabled
  (`quarkus.langchain4j.tracing.include-prompt` / `.include-completion`) - treat those as
  dev-only, since they record user content.
- **Enable parameter-name retention.** Configure the compiler with `-parameters` (Maven:
  `<parameters>true</parameters>`), which REST and AI-service binding rely on.
- **Build for both JVM and native.** Keep a `native` Maven profile so the project can produce a
  GraalVM native binary alongside the JVM build, and gate native integration tests in that
  profile. Native builds compile against the GraalVM JDK 25 line until JDK 29 (September 2027) -
  see section 2 - so a project with a native profile does not raise the language level above 25.
- **Disable Dev Services when an external model endpoint is configured.** When the project points
  at a real Ollama endpoint (local or cloud), disable LangChain4j Dev Services
  (`quarkus.langchain4j.devservices.enabled=false`) so a container is not started implicitly.

---

## 4. LangChain4j conventions

- **Declarative AI services are the default.** Define AI services as CDI-managed interfaces
  annotated with `@RegisterAiService` (the Quarkus form of LangChain4j's declarative service),
  using `@SystemMessage` / `@UserMessage` for prompts and `@MemoryId` for per-conversation
  memory. Prefer this over manual `ChatModel` wiring unless there is a documented reason.
- **Tools are CDI beans.** Expose actions to a model with `@Tool` methods on `@ApplicationScoped`
  beans, wired via `@RegisterAiService(tools = ...)` or `@ToolBox` - never hand-rolled JSON
  function dispatch. Tool methods doing I/O follow the section 2 virtual-thread rules.
- **Multi-agent workflows are composed declaratively.** Build agentic workflows from
  `@RegisterAiService` agents annotated with `@Agent(name, description, outputKey)` and orchestrate
  them with the LangChain4j Agentic annotations - `@SequenceAgent`, `@ParallelAgent`,
  `@ParallelMapperAgent`, and `@SupervisorAgent` (+ `@SupervisorRequest`) - assembling results
  with `@Output` over the `AgenticScope`. Use the `quarkus-langchain4j-agentic` extension. Avoid
  hand-rolled executor or coordination glue between AI services.
- **Structured output via typed return values.** Have services return records or enums to get
  structured results, and set `temperature=0` for classification and other deterministic tasks.
- **Name and right-size models.** Configure models by name (`@RegisterAiService(modelName = "...")`
  on services, `@ModelName("...")` on injected models) and use a small, fast, low-temperature model
  for cheap subtasks (classification, query rewriting) and a larger model for the primary task.
- **Streaming pattern: reactive only at the edge.** Stream over `quarkus-websockets-next`
  (`@WebSocket`, `@OnTextMessage` returning a Mutiny `Multi`, `@OnError`). Keep the agent and
  engine logic free of reactive types: have the WebSocket delegate to an `@ApplicationScoped`
  orchestrator that runs the blocking pipeline on a virtual thread
  (`Multi.createFrom().emitter(...)` + `Thread.startVirtualThread(...)`) and emits progress.
  Mutiny appears only at the channel edge, never inside the engine.
- **Guardrails wrap AI services declaratively.** Validate prompts/responses with
  `@InputGuardrails` / `@OutputGuardrails` beans implementing the upstream
  `dev.langchain4j.guardrail` interfaces (the Quarkus-specific guardrail API was retired in favor
  of upstream); tune retries with `quarkus.langchain4j.guardrails.max-retries`.
- **Fault tolerance is declarative on AI-service methods.** With
  `quarkus-smallrye-fault-tolerance`, put MicroProfile `@Timeout`, `@Retry`, and `@Fallback`
  (`org.eclipse.microprofile.faulttolerance`) directly on `@RegisterAiService` methods, with the
  fallback as a `default` method on the same interface - never hand-rolled try/retry loops
  around AI calls. Size `@Timeout` generously on tool-calling methods: a single invocation may
  span several model/tool round-trips before it returns.
- **RAG starts simple with Easy RAG.** For retrieval-augmented generation, start with the
  `quarkus-langchain4j-easy-rag` extension plus an in-process embedding model: point
  `quarkus.langchain4j.easy-rag.path` at a documents folder and let it ingest on startup. Move to
  a hand-built `RetrievalAugmentor` (a CDI-produced `EmbeddingStore` + `EmbeddingStoreContentRetriever`)
  only when a project needs control Easy RAG does not provide.
- **Enable request/response logging.** Set `quarkus.langchain4j.log-requests=true` and
  `quarkus.langchain4j.log-responses=true` so prompts and model output are observable during
  development.

---

## 5. Testing

No test suite is mandated, so treat this as the intended baseline rather than an observed standard.
Apply it when adding tests:

- Use `@QuarkusTest` (artifact `io.quarkus:quarkus-junit`) for integration-style tests and
  `io.rest-assured:rest-assured` to exercise HTTP endpoints.
- Run native integration tests through `maven-failsafe-plugin` inside the `native` profile.
- Keep model interactions deterministic in tests (`temperature=0`, fixed prompts) or mock the
  model so tests do not depend on live inference.
- Grade model *quality* with the evaluation framework
  (`quarkus-langchain4j-testing-evaluation-junit5` + semantic-similarity / AI-judge strategies)
  rather than brittle string asserts; keep the scaffolded `@QuarkusTest` wiring smoke test green
  without a live model.

---

## 6. Scope and overrides

These conventions apply to projects in this Quarkus + LangChain4j stack. A per-project addition
or override is allowed when justified - for example, pinning a fixed older Java version, choosing
platform threads for a pinning dependency, or selecting a different model provider - and must be
documented inline near the override so the deviation and its reason stay visible.
