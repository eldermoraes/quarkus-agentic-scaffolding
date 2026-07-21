---
name: audit-project
description: Audit an existing Quarkus + LangChain4j project against this stack's agentic conventions — a read-only conformance or gap-analysis review. Use when the user asks to audit, review, check, assess, or validate a Quarkus project against the LangChain4j agentic conventions, or wants to know whether an existing project conforms to (or is ready to adopt) this stack. User-invoked only.
disable-model-invocation: true
---

# Audit a Quarkus + LangChain4j Project

# Version: 0.11.0

## 1. When to use this skill

Use this skill to **review an existing project** against the Quarkus + LangChain4j agentic
conventions and report where it conforms and where it drifts. It never creates or scaffolds — for
that, use `/scaffold-project`; to configure prerequisites, use `/setup-agentic-scaffolding`.

Invoke it as `/audit-project` (skills-CLI install) or `/quarkus-agentic:audit-project` (plugin
install) — both name the same skill.

**Required tooling (mandatory).** This skill needs the **Quarkus Agents MCP** (for version-matched
validation via `quarkus_skills` / `quarkus_searchDocs` with `projectDir`) and the project's
**conventions file** (`CLAUDE.md` / `AGENTS.md` / `GEMINI.md`) as the source of truth for the
checks. If either is missing, stop and tell the user to run `/setup-agentic-scaffolding` first,
then re-run this audit. Do not fall back to model memory or a generic web search.

## 2. Read-only contract

This audit **NEVER modifies the project**. It reads `pom.xml`, `application.properties`, and the
source tree, then reports findings. It does not edit files, add dependencies, run builds, or apply
any fix on its own.

Fixes are applied **only after explicit user confirmation**, and never by this skill directly:
hand off each confirmed fix to `/scaffold-project`'s component scaffolding (AI service, tools,
agents, RAG, MCP, guardrails) or, for the conventions file itself, to `/setup-agentic-scaffolding`
Phase C. The audit's job ends at a prioritized report plus that offer.

## 3. Two entry scenarios

Detect the scenario — do not ask when it is determinable from `pom.xml` and the source tree.

- **(a) Already on this stack** — the project imports `quarkus-langchain4j-bom` and uses
  `@RegisterAiService` (or related LangChain4j extensions). Produce a **conformance report**: every
  §2–§5 check below, scored against the current code.
- **(b) Plain Quarkus, adopting the stack** — a Quarkus project with no LangChain4j footprint.
  Produce a **gap analysis**: which conventions already hold (Java level, `-parameters`, native
  profile, BOM discipline) and which pieces are missing to adopt the stack. End the report pointing
  at `/setup-agentic-scaffolding` **Phase C** (to add the conventions file) and `/scaffold-project`
  (to add the missing AI service, agents, RAG, or MCP components).

If neither pattern is clear (e.g. not a Quarkus project at all), say so and stop.

## 4. Process

Follow **Explore → Audit → Report**. Stay read-only throughout.

1. **Explore.** Read `pom.xml` (BOMs, extensions, compiler config, profiles),
   `application.properties`, and the `src/main/java` tree (package layout, annotations). Confirm
   the conventions file is present. When the Quarkus Agents MCP is available, pass `projectDir` to
   `quarkus_skills` / `quarkus_searchDocs` so extension patterns and versions are validated against
   **this** project's platform version, not from memory.
2. **Audit.** Walk the check catalog (§5) area by area. For each check, record pass / fail /
   not-applicable with concrete evidence (`file:line`).
3. **Report.** Emit the prioritized findings in the §6 format.

## 5. Check catalog

Derived from the conventions file §2–§5. Each check cites the section it enforces. Mark a check
**N/A** when its precondition does not hold (e.g. native checks when there is no native profile).

### 5.1 Java (§2)

| Check | Look for | Pass when |
|---|---|---|
| Language level | `maven.compiler.release` in `pom.xml` | ≥ 25 |
| Native baseline cap | `release` **and** a `native` profile | `release` = 25 (GraalVM JDK 25 line) |
| Virtual threads for blocking work | blocking I/O in `@Tool` / AI calls | `@RunOnVirtualThread` (not event loop, not raw platform pool) |
| Scoped Values over ThreadLocal | `ThreadLocal` for request/agent identity | `ScopedValue` used instead |
| Records / sealed / pattern matching | DTOs and closed hierarchies in `dto/` | records for DTOs, sealed types for event/result hierarchies |

### 5.2 Quarkus (§3)

| Check | Look for | Pass when |
|---|---|---|
| BOM imports, no pinned versions | `quarkus-bom` + `quarkus-langchain4j-bom` in `dependencyManagement` | both imported at one platform version; **no** `<version>` on extensions |
| `-parameters` retention | compiler config in `pom.xml` | `<parameters>true</parameters>` set |
| Native profile present | `<profile>` in `pom.xml` | a `native` profile exists |
| REST + OpenAPI surface | extensions | `quarkus-rest` + `quarkus-rest-jackson`; `quarkus-smallrye-openapi` present |
| Streaming via WebSockets Next | streaming transport | `quarkus-websockets-next` (no custom SSE/transport) |
| Observability extensions | extensions | `quarkus-micrometer-registry-prometheus` **and** `quarkus-opentelemetry` present |
| Dev Services disabled for real endpoint | a real Ollama URL is configured | `quarkus.langchain4j.devservices.enabled=false` |

### 5.3 LangChain4j (§4)

| Check | Look for | Pass when |
|---|---|---|
| Declarative AI services | AI-service classes | `@RegisterAiService` interfaces, **not** manual `ChatModel` wiring |
| Tools as CDI beans | tool dispatch | `@Tool` methods on `@ApplicationScoped` beans, **not** hand-rolled JSON function dispatch |
| Declarative agentic composition | multi-agent orchestration | `@Agent` + `@SequenceAgent` / `@ParallelAgent` / `@SupervisorAgent` / `@Output`, **no** hand-rolled executor glue |
| Upstream guardrail imports | guardrail beans | imports from `dev.langchain4j.guardrail` (the retired Quarkus-specific guardrail API is gone) |
| Reactive only at the edge | Mutiny usage | `Multi` / `Uni` only in `@WebSocket` edge beans; **none** inside engine/agent/tool logic |
| Declarative fault tolerance | retry/timeout logic on AI methods | MicroProfile `@Timeout` / `@Retry` / `@Fallback` on `@RegisterAiService` methods, **not** hand-rolled try/retry loops |
| Request/response logging (dev) | `application.properties` | `quarkus.langchain4j.log-requests=true` + `.log-responses=true` |

### 5.4 Testing (§5)

| Check | Look for | Pass when |
|---|---|---|
| Wiring smoke test | `src/test` | a `@QuarkusTest` that boots the container and asserts the AI service wires (no live model) |
| Quality graded, not string-matched | evaluation tests | AI quality graded via `quarkus-langchain4j-testing-evaluation-junit5` (semantic-similarity / AI-judge), not brittle string asserts |

## 6. Report format

Lead with the recommendation. Group findings by impact and give each one evidence, the convention
it violates, and a concrete fix.

- **High** — breaks a mandatory convention (pinned extension versions, manual `ChatModel` wiring,
  hand-rolled retry loops, Mutiny inside the engine, missing BOM import).
- **Medium** — drift that will bite later (missing native profile, no observability extensions,
  Dev Services left on against a real endpoint, `ThreadLocal` for agent identity).
- **Low** — polish (missing dev logging, DTOs that could be records, missing wiring smoke test).

Each finding:

```text
[HIGH] pom.xml:42 — langchain4j-ollama pins <version>1.0.0</version>
  Violates §3 (import the BOMs; do not pin extension versions).
  Fix: remove the <version>; let quarkus-langchain4j-bom manage it.
```

Close with a **summary count** (`3 high, 2 medium, 4 low`) and the offer to apply fixes via
`/scaffold-project` (components) or `/setup-agentic-scaffolding` Phase C (conventions file) **after
you confirm**. When nothing fails, say so plainly — "No conformance issues found against §2–§5" —
and stop; do not invent findings to fill the report.
