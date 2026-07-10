# Evolution Plan — Frontier Audit, 2026-07-10

> Prioritized action plan produced by a frontier audit (web research across the Quarkus platform,
> quarkus-langchain4j, LangChain4j core, OpenJDK/GraalVM, the agent-skill distribution ecosystem,
> and CI/update-automation practice) against this repository at v0.7.0. Facts below carry an
> as-of date of **2026-07-10** and rot at ecosystem speed — re-verify before acting on an item
> months later. Sources are linked inline on load-bearing claims.

## Where the frontier moved since the v0.7.0 baseline

| Axis | v0.7.0 baseline (2026-06-08) | Frontier (2026-07-10) |
|---|---|---|
| Quarkus platform | 3.36.1 | **3.37.2** (2026-07-08); LTS streams: 3.33 (until 2027-03), next LTS 3.40 (Sept 2026) |
| quarkus-langchain4j | (platform-managed) | Standalone BOM **1.12.0** (tracks LangChain4j 1.17.2); platform 3.37.2 ships 1.11.2 (LC4j 1.16.2) |
| LangChain4j core | 1.14.1 / agentic beta24 | **1.17.2 / agentic 1.17.2-beta27** — still experimental, plus `@LoopAgent`, `@ConditionalAgent`, `@PlannerAgent`, `@ErrorHandler`, human-in-the-loop, guardrails module, A2A 1.0.0.Final |
| Java | 25 LTS floor (correct) | 26 is current GA; 27 GA 2026-09-14; **GraalVM ships no 26/27/28 releases** — native stays on the 25 baseline until JDK 29 (Sept 2027) |
| Distribution | self-hosted marketplace only | Official Anthropic plugin directory (submission form), skills.sh (`npx skills add`, 72+ agents), Gemini CLI gallery (topic-driven), AGENTS.md now a Linux Foundation (AAIF) standard |
| Repo visibility | — | **0 stars, no GitHub description, no topics, no homepage** (verified via GitHub API); already listed on jvmskills.com |

The three user-declared open questions — adoption, staying current with Quarkus/LangChain4j, and
staying current with OpenJDK — are each answered by concrete items below (P0-1..3, P1-7, and the
OpenJDK facts + P1-7 respectively).

---

## P0 — High impact, low effort (this week)

### 1. Fix the GitHub repo metadata *(minutes; adoption)* — ✅ done 2026-07-10 (description + 16 topics live; homepage pending skills.sh page existing)
The repo has no description, homepage, or topics — it is invisible to every discovery surface.
Competitors tag 14–20 topics (e.g. `b6k-dev/quarkus-skill`). Add: description, homepage
(README or future docs page), and topics such as `quarkus`, `langchain4j`, `claude-code`,
`claude-code-plugin`, `claude-skills`, `agent-skills`, `codex-skills`, `ai-agents`, `java`,
`scaffolding`. Topic population sizes (verified): `claude-code` 45k repos, `agent-skills` 9.1k,
`codex-skills` 696, `langchain4j` 330.

### 2. Document the `npx skills add` install path *(minutes; adoption)* — ✅ done 2026-07-10 (v0.8.0, commit 7baeeaa, install verified live)
Because the skill already lives under `skills/`, this works **today** with zero code changes:

```
npx skills add eldermoraes/quarkus-agentic-scaffolding
```

The [skills.sh](https://www.skills.sh/) CLI ([vercel-labs/skills](https://github.com/vercel-labs/skills))
installs into 72+ agents (Claude Code, Cursor, Codex, Copilot, Windsurf, Goose, Amp, opencode,
Zed…). GitHub Copilot also reads `.claude/skills` natively
([docs](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)). The skills.sh
leaderboard ranks purely by install telemetry, so every documented install compounds visibility.
Add this as the first install option in the README, keeping `/plugin marketplace add` for Claude
and the Codex/Bob paths as-is.

### 3. Submit to the official Anthropic plugin directory *(one form; adoption)* — ⏳ pending user action: submission kit ready in [issue #4](https://github.com/eldermoraes/quarkus-agentic-scaffolding/issues/4)
Anthropic now runs a curated directory ([claude.com/plugins](https://claude.com/plugins),
[anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official)) plus a
community tier ([anthropics/claude-plugins-community](https://github.com/anthropics/claude-plugins-community))
surfaced in Claude Code's `/plugin` Discover tab. Submission is via the form at
**clau.de/plugin-directory-submission** (direct PRs are auto-closed). This is the single
highest-surface listing available for the Claude side.

### 4. Refresh the model defaults *(small template edit)*
- **Chat:** the official quarkus-langchain4j Ollama guide now uses **`qwen3:1.7b`**
  ([guide](https://docs.quarkiverse.io/quarkus-langchain4j/dev/guide-ollama.html)); qwen3 has
  strong tool-calling, which matters for the agent templates. `llama3.2` is still the extension's
  literal config default but is dated as a recommendation. Suggested: `qwen3:4b` default,
  `qwen3:1.7b` as the `smaller` named model (replacing `llama3.2` / `llama3.2:1b`).
- **Embeddings:** upstream Easy RAG's recommended in-process model is
  **bge-small-en-v1.5 quantized** (`langchain4j-embeddings-bge-small-en-v15-q`, ~24 MB, better
  MTEB score), not `all-minilm-l6-v2`
  ([LangChain4j RAG tutorial](https://docs.langchain4j.dev/tutorials/rag/)). Swap it in
  `pom.xml.template` and the RAG docs.
- `quarkus.langchain4j.timeout` is confirmed a **valid global key** (Duration, default 10s;
  per-provider keys override) — the template's 120s stays, no change needed.

### 5. Align the streaming convention with current docs *(CLAUDE.md/AGENTS.md §3–4 edit)*
Current quarkus-langchain4j docs present **SSE (`Multi<String>` from a plain quarkus-rest
endpoint) as the simple streaming default**, with `quarkus-websockets-next` recommended **for
stateful chat** (`@SessionScoped` AI service; connection ID becomes the memory ID)
([streamed responses](https://docs.quarkiverse.io/quarkus-langchain4j/dev/guide-streamed-responses.html),
[websockets](https://docs.quarkiverse.io/quarkus-langchain4j/dev/websockets.html)).
The conventions currently mandate websockets-next only. Soften to: SSE for simple token
streaming, websockets-next for stateful/conversational streaming — keeping the
virtual-thread-bridge pattern for agentic progress streaming.

---

## P1 — High impact, medium effort (next 2–4 weeks)

### 6. Materialize the CI backstop *(robustness — the plan already exists in prose)* — ✅ done 2026-07-10 (v0.9.0: ci/build-from-templates.sh + validate-templates/quality workflows)
`docs/VALIDATING-TEMPLATES.md` describes a workflow that was never created. Reference
architecture exists in this exact ecosystem:

- **Nightly/weekly cron compile against the latest platform** — the
  [quarkus-quickstarts daily workflow](https://github.com/quarkusio/quarkus-quickstarts/blob/development/.github/workflows/daily-aarch64-development.yml)
  and [spring-io/start.spring.io verification.yml](https://github.com/spring-io/start.spring.io/blob/main/.github/workflows/verification.yml)
  patterns: reconstruct a project from `templates/` (the static-fallback procedure), `mvn -B compile`
  on Temurin/GraalVM 25 with `check-latest: true`.
- **Failure toggles a tracking issue** — the
  [quarkus-ecosystem-ci](https://github.com/quarkusio/quarkus-ecosystem-ci) model (issue open =
  broken against latest, closed = healthy); [`jayqi/failed-build-issue-action`](https://github.com/marketplace/actions/failed-build-issue)
  dedupes nightly failures into one issue.
- **Cheap quality gates in the same PR workflow:** a ~10-line version-header consistency check
  (`grep -rhoE 'Version: [0-9.]+' <files> | sort -u | wc -l` must equal 1 — directly de-risks the
  6-file manual version sync), `shellcheck scripts/*.sh`, `markdownlint-cli2`, `lychee` link check
  on cron (not per-PR), `actionlint` once workflows exist.
- Write `ci/build-from-templates.sh` so the reconstruction is scripted, not re-derived by hand.

### 7. Add Renovate as the release watcher *(answers "how do I stay current?")* — ✅ done 2026-07-10 (v0.9.0: renovate.json + ci/baseline.env; ⏳ activation = install the Mend Renovate App)
Renovate — not Dependabot, which has no custom managers — can watch every axis this project
cares about, inside non-pom files (regex `customManagers`,
[docs](https://docs.renovatebot.com/modules/manager/regex/)):

- **Quarkus platform:** `maven` datasource on `io.quarkus.platform:quarkus-bom`.
  Note: quarkusio/quarkus-platform publishes **no GitHub releases** (verified — API 404s), so the
  Maven datasource is the correct source.
- **quarkus-langchain4j:** `github-releases` on `quarkiverse/quarkus-langchain4j` (or maven on its BOM).
- **OpenJDK:** the dedicated [`java-version` datasource](https://docs.renovatebot.com/modules/datasource/java-version/)
  (Adoptium-backed) detects new JDK GAs — this is the OpenJDK-tracking answer. For a
  hand-rolled check instead: `curl https://api.adoptium.net/v3/info/available_releases` returns
  `most_recent_feature_release` / `most_recent_lts` directly (live-verified).
- Use [`dependencyDashboardApproval`](https://docs.renovatebot.com/key-concepts/dashboard/) for
  issue-first notification instead of automatic PRs, since a "new platform version" here means
  "re-run validation and maybe touch docs", not "bump a lockfile".

OpenJDK cadence facts for the policy: 2 releases/year (Mar/Sept); LTS every 2 years — 25 (2025) →
**29 (Sept 2027)**; JDK 26 is current GA; 27 GA 2026-09-14 (compact object headers and G1 become
defaults). Java-25-as-floor stays correct — reinforced by GraalVM (see P2-17).

### 8. Close the biggest capability gaps in the skill/templates *(new capabilities, phase 1)* — ✅ done 2026-07-10 (v0.9.0: Tools/Guardrails/AiServiceTest templates + agentic variants + conventions §4–§5)
In order of glaringness for a kit whose pitch is "agentic AI apps":

1. **`@Tool` / function calling — the largest gap.** The templates ship agents with no tools.
   Add a `ToolBelt`-style section to the templates: `@Tool` on a CDI bean, wired via
   `@ToolBox(...)`/`@RegisterAiService(tools = ...)`; note `@RunOnVirtualThread`/blocking rules and
   the new tool-level guardrails (`@ToolInputGuardrails`/`@ToolOutputGuardrails`)
   ([function calling docs](https://docs.quarkiverse.io/quarkus-langchain4j/dev/function-calling.html)).
2. **Guardrails.** `@InputGuardrails`/`@OutputGuardrails` on AI services; the Quarkus-specific
   implementation was **removed in favor of upstream `dev.langchain4j.guardrail`** — use upstream
   imports in templates; `quarkus.langchain4j.guardrails.max-retries` defaults to 3
   ([docs](https://docs.quarkiverse.io/quarkus-langchain4j/dev/guardrails.html)).
3. **A generated test.** The scaffolding produces zero tests while CLAUDE.md §5 mandates a
   baseline. quarkus-langchain4j now ships a dedicated eval framework:
   `quarkus-langchain4j-testing-evaluation-junit5` + `-semantic-similarity` + `-ai-judge`
   (`Scorer`, `@EvaluationTest(minScore=…)`, YAML samples —
   [testing docs](https://docs.quarkiverse.io/quarkus-langchain4j/dev/testing.html)). Template a
   basic `@QuarkusTest` + one eval-style test, and add the framework to CLAUDE.md §5.
4. **New agentic annotations.** `Agent.java.template` covers Sequence/Parallel/Supervisor;
   the module (still experimental, now beta27) added `@LoopAgent`, `@ConditionalAgent` +
   `@ActivationCondition`, `@ErrorHandler` (declarative retry/recover), `@HumanInTheLoop`, and
   `@PlannerAgent` ([agentic docs](https://docs.quarkiverse.io/quarkus-langchain4j/dev/agentic.html)).
   Add Loop + Conditional + ErrorHandler as commented variants alongside the existing Supervisor
   variant.

### 9. Re-validate and re-baseline *(robustness)*
Re-run the VALIDATING-TEMPLATES procedure against platform 3.37.2 / quarkus-langchain4j 1.12.0.
Two behavioral notes to check: 1.11.0 switched agents to **deployment-time generation** (guards
against arbitrary reflection) and renamed token-usage metric attributes; 1.12.0 added build-time
validation of misconfigured agentic setups. Also decide and document the version stance: the kit
correctly does not pin (quarkus_create resolves the platform), but the docs should name the LTS
option (3.33 now, 3.40 from Sept 2026) for users who want stability, per
[Quarkus LTS policy](https://quarkus.io/blog/lts-releases/).

---

## P2 — Strategic (1–2 months)

### 10. MCP templates — client and server *(new capabilities, phase 2)*
Both directions are first-class now and squarely on-theme:
- **Client:** `quarkus-langchain4j-mcp`, `@McpToolBox("name")` on AI services, `streamable-http`
  transport recommended ([MCP docs](https://docs.quarkiverse.io/quarkus-langchain4j/dev/mcp.html)).
- **Server:** `io.quarkiverse.mcp:quarkus-mcp-server-*` to expose a Quarkus app as an MCP server
  ([docs](https://docs.quarkiverse.io/quarkus-mcp-server/dev/index.html)).
A "make my agent use MCP tools" and "expose my service as an MCP server" scaffold each would be
a differentiator no comparable kit has. Watch also: the new `@Skills` annotation/extension in
quarkus-langchain4j 1.12.0, and A2A (`@A2AClientAgent`, protocol 1.0.0.Final — still beta).

### 11. Observability + fault-tolerance conventions *(new capabilities)*
Both are now automatic/annotation-level in the extension and absent from the kit:
`quarkus-micrometer` + `quarkus-opentelemetry` give AI-service metrics, OTel GenAI-semconv token
usage, and per-tool spans with zero code ([observability docs](https://docs.quarkiverse.io/quarkus-langchain4j/dev/observability.html));
`@Timeout`/`@Retry`/`@Fallback` work directly on AI-service methods (caveat: `@Timeout` × long
tool-calling loops — [fault-tolerance guide](https://docs.quarkiverse.io/quarkus-langchain4j/dev/guide-fault-tolerance.html)).
One §-worth of conventions each plus a few template lines.

### 12. Community distribution campaign *(adoption — leverage the author's standing)*
Sequenced so social proof accumulates:
1. PR to [langchain4j-community-resources](https://github.com/langchain4j/langchain4j-community-resources)
   (explicitly open to shared resources — trivially accepted).
2. After ~10 stars: awesome-list PRs ([travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills)
   requires social proof; [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code)
   takes issue submissions).
3. Quarkus channels: guest post on quarkus.io (PR to quarkusio.github.io; AI-assisted OK, fully
   AI-written not), Quarkus Insights episode, Red Hat Developer article (author page exists).
4. foojay.io article (precedent: BoxLang launched its skills ecosystem there) + JUG/conference
   talks with `npx skills add …` as the live demo hook.

Benchmarks: Spring analogues sit at 144–159 stars driven by author audience
(`rrezartprebreza/spring-boot-skills`, `sivaprasadreddy/sivalabs-agent-skills`); the ceiling
pattern (vercel-labs/agent-skills, ~29k stars) is vendor blog + one-line install + leaderboard.
Also: the skill is already on [jvmskills.com](https://jvmskills.com/) — engage the curator; their
eval badges ("96% vs 70%") are the emerging quality signal (see 13).

### 13. Publish an eval for the skill *(quality signal)*
SkillsBench ([arxiv 2602.12670](https://arxiv.org/html/2602.12670v1)) found curated skills add
+16pp average but many skills add nothing — publishable evidence of effectiveness is becoming the
differentiator (jvmskills badges). Design a small fixed-task eval (scaffold X with vs. without the
skill; compile + convention-compliance as the rubric) and publish the numbers in the README.

### 14. Gemini CLI listing *(adoption, cheap)*
The Gemini gallery ([geminicli.com/extensions](https://geminicli.com/extensions/)) lists any
public repo with a `gemini-extension.json` and the GitHub topic `gemini-cli-extension` — no review
([releasing docs](https://geminicli.com/docs/extensions/releasing/)). The manifest can declare the
two MCP servers this stack requires. Cheapest official-gallery listing of the three vendors.

### 15. Agentic maintenance automation *(after #6/#7 are in place)*
Phase 2 of "stay current": a scheduled agent run that executes this repo's own validation
procedure and proposes fixes. Options, in maturity order:
[claude-code-action on cron](https://code.claude.com/docs/en/github-actions) (automation mode;
default output is a fix branch + prefilled-PR link), Anthropic Routines
([scheduled tasks docs](https://code.claude.com/docs/en/scheduled-tasks)), GitHub Agentic
Workflows ([gh-aw](https://github.com/github/gh-aw), technical preview, safe-outputs mediate PR
creation). The deterministic CI (#6) stays the source of truth; the agent consumes its failures.

### 16. CLAUDE.md × AGENTS.md parity gate *(robustness)*
The two files are hand-synced twins whose only diffs are typographic (— vs -, § vs "section") plus
the preamble. Add a CI check that normalizes those and diffs the rest, so a convention edit can't
land in one file only. Context: AGENTS.md is now a Linux Foundation (AAIF) standard read by
Codex, Cursor, Copilot, Windsurf, Zed, Junie et al. ([agents.md](https://agents.md/)); Claude Code
remains the CLAUDE.md holdout, so both files stay necessary.

### 17. Conventions touch-ups from the OpenJDK/GraalVM audit *(small edits)*
- §2 is accurate today (Scoped Values final via JEP 506; StructuredTaskScope still preview — 6th
  round in 26, 7th in 27, **API breaking each round**, no finalization targeted).
- Add one load-bearing note: **GraalVM ships no releases for JDK 26–28** — native-image is pinned
  to the 25 baseline until JDK 29 (Sept 2027)
  ([GraalVM release-train post](https://medium.com/graalvm/accelerating-the-graalvm-release-train-26b0d7cff2ab)).
  This both reinforces Java 25 as the floor and caps "adopt newer language levels freely" for
  native targets — worth one sentence in §2 and §3.
- Watch list (not yet conventions): compact object headers + G1 default in 27 (free wins),
  JEP 500 final-field warnings in 26 (frameworks may warn), Valhalla value classes preview in 28.

---

## Reusable prompt-brief for working on this repo with an agent

> This repo is a distribution artifact (conventions + skill + templates) for Quarkus +
> LangChain4j — the product is markdown and templates, not an app. Always: (1) verify any
> Quarkus/LangChain4j claim against the Quarkus Agents MCP / context7 before editing a convention
> or template — never from model memory; (2) treat versions as volatile — check Maven Central
> (`io.quarkus.platform:quarkus-bom`, `io.quarkiverse.langchain4j:quarkus-langchain4j-bom`) and
> note that the LangChain4j agentic module is beta and churns; (3) keep the declarative/procedural
> split — conventions in CLAUDE.md/AGENTS.md (kept in parity), scaffolding in SKILL.md, and never
> restate one in the other; (4) any template change requires the VALIDATING-TEMPLATES procedure
> and a synchronized version-header bump across README, CLAUDE.md, AGENTS.md, SKILL.md, and both
> plugin.json files; (5) evidence bar per CONTRIBUTING.md — recurring real-world pattern, official
> docs, or a reproducible build result.

## Sources
Full research trails (five parallel investigations, 2026-07-09/10) covered: Quarkus platform &
quarkus-langchain4j releases and capability docs; LangChain4j core releases and Maven Central
metadata; OpenJDK JEP index / release cadence / GraalVM release-train announcement; the
Claude/Codex/Gemini/skills.sh distribution ecosystem incl. verified GitHub API checks of this
repo's metadata; and CI/Renovate/Adoptium-API patterns with live-verified endpoints. Key URLs are
inline above.
