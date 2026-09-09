# Scaffold skill pilot

The fixed pilot uses three component tasks, two repetitions, and two arms (12 agent executions).
Both arms receive the same Quarkus MCP-generated POM and project conventions. The treatment arm
also receives `scaffold-project` and its templates, with an explicit instruction to read the skill.
This measures incremental skill assistance with conventions already supplied, not the whole package.

See the [2026-09-09 pilot report](results/2026-09-09/REPORT.md): the first collection was
inconclusive because documentation prerequisites failed. The report pins the original protocol.

## Protocol

- Codex `gpt-6-astra`, low reasoning, existing ChatGPT account quota; no API key billing.
- Fresh Git directory outside this repository for every attempt; no previous-run continuation.
  Current runs snapshot tracked inputs from one commit and record their hashes.
- Current runs probe Quarkus and Context7 documentation before invoking Codex. A failed probe
  records collection-not-started and spends no model executions. A successful probe cannot
  guarantee service availability or quota throughout collection.
- Host skill discovery and plugins disabled in both arms. Treatment reads the local skill explicitly.
  `codex debug prompt-input` confirmed the isolation flags remove the host skills catalog before runs.
- Both arms get Quarkus Agents MCP 1.2.6 with Java 21+ and Context7 4.0.6 without an API key.
  Quarkus documentation search may be unavailable without a container runtime; this environment
  limitation applies to both arms. No live model, container installation, or network inference test.
- The starter was generated through `quarkus_create` on Quarkus 3.39.2. Its compiler release was
  raised from the generated 17 to 25. Shared BOMs, compiler settings, dependencies and native
  profile are inherited infrastructure, excluded from compliance scoring.
- Each task runs baseline then skill in repetition one, skill then baseline in repetition two.
  Runs share the machine's dependency cache; elapsed time is descriptive, not a speed benchmark.
- Each agent attempt has a 15-minute deadline, followed by an independent four-minute
  `mvn -B -ntp -DskipTests test-compile`. No retries or best-of selection.
- Every scheduled attempt remains in the results, including errors and timeouts. Raw logs stay in
  the chosen external output directory. Never publish raw logs without inspecting for credentials.

## Frozen scoring

`tasks.json` contains exact prompts and eight applicable checks per task. `run.py` defines their
mechanical predicates. Each check has equal weight. These are source-presence checks, not proof of
semantic correctness or complete convention compliance. Java comments are excluded. A sample
RAG document is a nonempty file under a `docs` directory; embedding support is an added
`langchain4j-embeddings-*` dependency. XML and documentation alone do not satisfy Java predicates.

Report compilation separately from checklist totals; an empty starter compiling is not a completed
task. Successful generation requires an agent exit of zero, no timeout, generated Java sources,
and an independent compile exit of zero. Report each task and arm, with denominators retained.
The checklist maximum is 48 per arm (six runs × eight checks).

Record CLI-reported token usage when present and failed shell commands from events. These are
not “turns/errors until green”: that metric is unavailable here. Two repetitions per task support
only a descriptive pilot, without significance claims or generalization to other models or tasks.
Publish the observed result even if the difference is zero or negative.

## Reproduce

Use the pinned source revision listed with the results, Python 3, Codex CLI supporting
`skip_host_skill_discovery`, JDK 25, Maven, JBang and Node/npm. Authenticate Codex with the existing
ChatGPT account. With an authorized execution budget, run:

```sh
python3 evals/skill-pilot/run.py /tmp/new-skill-pilot-output
```

The output directory must not already exist. It contains exact prompts, generated projects,
private event/compile logs, environment metadata and machine-readable results. Inspect all
artifacts before copying a sanitized result into the repository.
