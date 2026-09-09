# Agentic compensation: defer the default convention

Decision for [issue #48](https://github.com/eldermoraes/quarkus-agentic-scaffolding/issues/48),
2026-09-09: keep compensation out of the global §4 conventions and starter templates for now.
Current templates remain valid. Compensation may be appropriate for a specific application after
its integration and failure semantics are tested; it is not a universal requirement for every tool.

## Verified evidence

Context7 was queried first for upstream documentation. LangChain4j documents optional cross-agent
compensation via `compensateOnError`, with `@CompensateFor` connecting a tool to its compensator.
Successful tool calls with a compensator are processed in reverse order; missing compensators are
skipped. Compensation is best effort: one compensator failing does not prevent the remaining ones
from running. This is not guaranteed transactional rollback.
See [agent workflows](https://docs.langchain4j.dev/tutorials/agents#cross-agent-compensation) and
[tool compensation](https://docs.langchain4j.dev/tutorials/tools).

The local `langchain4j-agentic:1.19.0-beta29` binary exposes `compensateOnError()` on
`dev.langchain4j.agentic.declarative.ParallelAgent`, verified with `javap`.

However, inspection did **not** reproduce the issue's claim that Quarkus integration processors
reference `compensateOnError` and `CompensateFor`:

- The `quarkus-langchain4j-agentic-deployment` class archives for 1.13.0 and 1.13.1 contain neither
  literal, while `BeforeCall` is present.
- The 1.13.1 published sources for `AgenticProcessor.java` and `AgenticLangChain4jDotNames.java`
  also contain neither literal. The inspected
  [Maven Central source archive](https://repo.maven.apache.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-agentic-deployment/1.13.1/quarkus-langchain4j-agentic-deployment-1.13.1-sources.jar)
  has SHA-256 `97d6ad3cf59b3aaaadb30f1a210bd1a92dd4039dbfb709fb95f93c90bcb240fe`.
- The [Quarkiverse agentic guide](https://docs.quarkiverse.io/quarkus-langchain4j/dev/agentic.html)
  did not document compensation when checked on this date.

Absence of these symbols is not proof that runtime support is absent. It means the specific
integration evidence in the issue remains unverified. An upstream annotation compiling is also
insufficient evidence that a Quarkus-managed workflow enables its behavior.

## Adoption criteria

Reconsider a convention or opt-in template when the Quarkus integration is documented or a
minimal Quarkus-managed runtime test demonstrates all of these behaviors:

1. A successful externally visible tool action is followed by a workflow failure and its
   compensator executes.
2. Multiple successful tool calls are compensated in the expected reverse order.
3. A failing compensator does not prevent remaining compensators from running, and the failure
   is observable to operators.
4. The application defines idempotency and recovery behavior for retries, partial success and
   irreversible actions; it does not assume an annotation guarantees rollback.
5. JVM wiring is exercised, plus native wiring when the application targets a native binary.

This decision adds no compensation example that could imply unverified runtime guarantees.
`BeforeCall` and `writeStateIfAbsent` are separate capabilities and are not prerequisites for
closing this adoption decision.
