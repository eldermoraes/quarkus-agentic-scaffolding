# Changelog

All notable changes to this artifact are documented here. This project adheres to semantic
versioning.

## v0.13.1 — 2026-07-21
- **README fixes.** The skills.sh badge image now uses the `www.skills.sh` host directly (the
  apex-domain URL 308-redirects, which GitHub's image proxy does not follow, breaking the image)
  and links to the project's own skills.sh page instead of the site root. The "What's inside"
  repository tree moved below the usage sections so Quick install and The flow lead the page.

## v0.13.0 — 2026-07-21
- **Hard-stop MCP gate.** Closed the rationalization loophole where agents proceeded to scaffold
  manually when the Quarkus Agents MCP was down. Conventions §1 (`CLAUDE.md` / `AGENTS.md`) now
  require verifying the MCP is reachable (`quarkus_*` tools present + a cheap `quarkus_status`
  call) before any Quarkus task, and mandate an immediate STOP — report what is missing, point the
  user to `/setup-agentic-scaffolding` (and to restarting the session), and end the turn — with no
  fallback to the Quarkus CLI, Maven/Gradle archetypes, model memory, or web search. Added a
  matching "verify the MCP first" procedural gate at the top of the `scaffold-project` and
  `audit-project` skills. `/setup-agentic-scaffolding` remains the sole exception. Motivated by
  observed agent behavior of proceeding manually when the MCP is down.

## v0.12.1 — 2026-07-21
- **Grouped skill selection in the skills.sh installer.** `.claude-plugin/plugin.json` now declares
  the `skills` array explicitly, so `npx skills add` presents a selectable "Quarkus Agentic
  Scaffolding" group node that toggles all three skills at once (individual selection still
  works). No behavior change for Claude Code plugin installs, which already auto-discover
  `skills/`.

## v0.12.0 — 2026-07-21
- **Plugin machine id renamed `quarkus-agentic` → `quarkus-agentic-scaffolding`** so the repository
  name, install command, and plugin id all match. The human `displayName` ("Quarkus Agentic
  Scaffolding") is unchanged. Updated across every manifest (`.claude-plugin/plugin.json` +
  `marketplace.json`, `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`,
  `gemini-extension.json`), the `plugins/quarkus-agentic-scaffolding/` Codex wrapper directory, and
  all namespaced invocation forms (`/quarkus-agentic-scaffolding:<skill>`) in the README and skills.
- **Breaking for existing installs.** Because the id changed, a plugin installed under the old
  `quarkus-agentic` id must be reinstalled: uninstall the old id, then reinstall under
  `quarkus-agentic-scaffolding`. Skills and templates are otherwise unchanged.

## v0.11.0 — 2026-07-21
- **Restructured the single umbrella skill into an explicit three-skill flow** split along the
  invocation axis (see `docs/FLOW-REDESIGN-PLAN.md`):
  - **New `setup-agentic-scaffolding`** (user-invoked, `disable-model-invocation: true`) — the
    flow's entry point. Verifies the toolchain (JDK 25 / GraalVM, JBang, container runtime),
    registers the Quarkus Agents MCP + context7 for the running agent, and writes the conventions
    file into the user's project. Ships byte-for-byte seed copies of the root conventions
    (`templates/conventions-CLAUDE.md`, `templates/conventions-AGENTS.md`).
  - **`quarkus-langchain4j-scaffolding` renamed to `scaffold-project`** (model-invoked umbrella,
    owner decision D6 — creation + components stay one skill). Its creation path was reworked
    around the Quarkus Agents MCP surface: `quarkus_create` defaults (`noCode=true`,
    `noWrapper=false`), the mandatory extension-selection gate, a `git init`/commit step before
    `quarkus_skills`/`quarkus_start`, and `devui-testing_runTests` dev-mode verification.
  - **New `audit-project`** (user-invoked, `disable-model-invocation: true`) — read-only
    conformance/adoption audit of an existing project against the §2–§5 conventions, the package
    layout, and the dependency/properties baseline; applies fixes only on confirmation by handing
    off to `scaffold-project`'s component sections.
- **README rewritten around the flow.** Quick install (skills CLI) leads, now installing all three
  skills and covering IBM Bob as a first-class agent; added a **The flow** section
  (setup → scaffold → audit) and the skills.sh badge; collapsed the three near-duplicate per-agent
  prerequisite walkthroughs into a single `/setup-agentic-scaffolding` step plus a manual fallback
  each; documented both slash-command invocation forms (bare via skills-CLI installs,
  `/quarkus-agentic:<skill>` via plugin installs); fixed the stale "current version is 0.10.0"
  prose line.
- **CI gates extended.** `ci/check-version-consistency.sh` now covers all three `SKILL.md` files
  (nine versioned files total, up from seven); `ci/check-conventions-parity.sh` additionally
  verifies the two setup-skill seed copies are byte-for-byte identical to the root `CLAUDE.md` /
  `AGENTS.md`; `ci/build-from-templates.sh` and the validate-templates workflow point at
  `skills/scaffold-project/templates/`.
- **Distribution manifests** (`.claude-plugin/plugin.json` + `marketplace.json`,
  `.codex-plugin/plugin.json`, `gemini-extension.json`) describe the three-skill flow, with
  `scaffolding`, `setup`, `audit`, and `mcp` keywords; `gemini-extension.json` keeps
  `contextFileName: AGENTS.md`. `scripts/install-bob-skill.sh` now installs all three skills
  (same CLI shape) and is documented as a fallback, since `npx skills add` covers Bob natively.
- All version headers synchronized to 0.11.0.

## v0.10.1 — 2026-07-13
- Added a `displayName` of "Quarkus Agentic Scaffolding" to the plugin so the Claude Code UI
  shows a proper human-readable label instead of the prettified `quarkus-agentic` slug. The field
  is set in both `.claude-plugin/plugin.json` and the `.claude-plugin/marketplace.json` plugin
  entry (the marketplace entry wins for users installing from this marketplace, with `plugin.json`
  as the fallback), so installed users see the new name. The `name` identifier stays
  `quarkus-agentic`, so skill namespacing and install identity are unchanged. `displayName`
  requires Claude Code v2.1.143+ and falls back to `name` on older clients. This brings the Claude
  Code manifests to parity with the Codex manifest, which already carried the same display name.
- All version headers synchronized to 0.10.1.

## v0.10.0 — 2026-07-10
- Added MCP scaffolding in both directions: `McpClient.java.template` (an AI service consuming
  MCP tools via `@McpToolBox`, with `streamable-http`/`stdio` client config in
  `application.properties.template`) and `McpServer.java.template` (exposing the app's own
  `TicketTools` as an MCP server via `io.quarkiverse.mcp.server` `@Tool`, versioned by the
  platform member BOM `quarkus-mcp-server-bom` — no pins). SKILL.md gained MCP client (§6) and
  MCP server (§7) sections; the CI extension list now covers `langchain4j-mcp` and
  `mcp-server-http`.
- Conventions: CLAUDE.md/AGENTS.md now cover zero-code AI observability (Micrometer +
  OpenTelemetry auto-instrumentation, GenAI token-usage/cost metrics, per-tool spans) and
  declarative fault tolerance on AI-service methods (`@Timeout`/`@Retry`/`@Fallback`, with the
  `@Timeout` × tool-calling-loops caveat), plus the GraalVM native-baseline note (no GraalVM
  releases for JDK 26, 27, or 28 — native stays on the JDK 25 baseline until JDK 29).
  `application.properties.template` and `AiService.java.template` carry commented, opt-in
  examples for both.
- New CI gate: `ci/check-conventions-parity.sh` + a `conventions-parity` job in the quality
  workflow — CLAUDE.md and AGENTS.md are now diffed under typography normalization so a
  convention edit can no longer land on one side only (a pre-existing one-character drift was
  fixed in the process).
- Added `gemini-extension.json` so the repository can be listed in the Gemini CLI extensions
  gallery (declares the required Quarkus Agents MCP + context7 servers; `contextFileName`
  delivers `AGENTS.md`); it is now the seventh version-carrying file, enforced by the extended
  `ci/check-version-consistency.sh`.
- All version headers synchronized to 0.10.0.

## v0.9.0 — 2026-07-10
- Added a real CI backstop: `ci/build-from-templates.sh` reconstructs a project from the
  templates by convention and compiles it; the `validate-templates` workflow runs it on PRs
  (against `ci/baseline.env`) and weekly against the live latest platform, opening or updating a
  tracking issue on scheduled failures (closed manually once a later run is green); the `quality`
  workflow adds version-consistency, shellcheck, actionlint, and markdownlint gates; scheduled
  link checking via lychee.
- Added `renovate.json` + `ci/baseline.env`: Renovate watches Quarkus platform, the
  quarkus-langchain4j BOM, and new OpenJDK GA releases (java-version datasource) on the
  Dependency Dashboard (approval mode — no automatic PRs). Activation requires installing the
  Mend Renovate app.
- Closed template capability gaps: `Tools.java.template` (@Tool CDI beans + wiring),
  `Guardrails.java.template` (upstream input/output guardrails), `AiServiceTest.java.template`
  (@QuarkusTest wiring smoke test + commented model-dependent and eval examples), and commented
  loop/conditional/error-handler/human-in-the-loop variants in `Agent.java.template`;
  `pom.xml.template` gained the test-scoped `quarkus-langchain4j-testing-evaluation-junit5`
  dependency (version managed by the platform BOM); SKILL.md gained tool/guardrail/test-scaffolding
  sections and the layout gained `tools/` and `guardrails/`; CLAUDE.md/AGENTS.md §4–§5 now cover
  tools, guardrails, and the eval framework.
- All version headers synchronized to 0.9.0.

## v0.8.0 — 2026-07-10
- Documented a universal install path via the skills.sh CLI (`npx skills add
  eldermoraes/quarkus-agentic-scaffolding`), which detects and installs the scaffolding skill into
  any Agent Skills-compatible agent (Claude Code, Codex, Copilot, Cursor, Windsurf, opencode, and
  others). Verified end-to-end against the live CLI. The conventions files and the required MCP
  tooling remain per-agent manual steps, as before.
- All version headers synchronized to 0.8.0.

## v0.7.0 — 2026-06-08
- **Fixed Bob support, which had been modeled on a non-existent CLI.** Removed the hallucinated
  `bob plugin marketplace add` / `bob plugin add` and `bob mcp add` commands (IBM Bob has no plugin
  CLI or marketplace), and removed `BOB.md` and `.bob-plugin/`. Verified against `bob.ibm.com/docs`:
  Bob reads the same `AGENTS.md` as Codex, discovers skills under `.bob/skills/`, and configures MCP
  servers via `.bob/mcp.json` (or the MCP tab in the UI). Added `scripts/install-bob-skill.sh` to
  copy the skill into a project's (or global `~/.bob/skills/`) skills directory, and documented the
  Quarkus Agents MCP + context7 setup as a `.bob/mcp.json` entry
  (`jbang quarkus-agent-mcp@quarkusio`, `npx -y @upstash/context7-mcp`). The Quarkus Agents MCP is a
  standalone MCP server whose docs list IBM Bob as a supported client.
- **Fixed the Codex setup commands.** Replaced the non-existent `codex plugin add` with installing
  the plugin from the `/plugins` list after `codex plugin marketplace add`, and switched the Quarkus
  Agents MCP from a (non-existent) Codex plugin to
  `codex mcp add quarkus-agent -- jbang quarkus-agent-mcp@quarkusio`. Added a "Try it" step for parity.
- `AGENTS.md` is now the shared conventions file for both Codex and Bob; `README.md` and
  `CONTRIBUTING.md` updated to drop `BOB.md` / `.bob-plugin/` and reflect the per-agent install paths.
- All version headers synchronized to 0.7.0.

## v0.6.0 — 2026-06-03
- Slimmed `pom.xml.template` from a full pom to a dependency reference. The project shell (platform
  BOMs, build plugins, the `-parameters` flag, the `native` profile, the test stack, version pins) is
  generated up to date by `quarkus_create` — the same codestart generator behind code.quarkus.io — so
  hand-maintaining it only caused drift (see v0.5.0). The template now keeps only what generators do
  not provide: the curated extension list and the non-extension `dev.langchain4j` deps (embedding
  model, PDF parser). Updated `SKILL.md` §3 and the `VALIDATING-TEMPLATES.md` reconcile step to match.
- All version headers synchronized to 0.6.0.

## v0.5.0 — 2026-06-03
- Switched the generated REST JSON serializer from JSON-B to Jackson
  (`quarkus-rest-jsonb` → `quarkus-rest-jackson`): `pom.xml.template`, the §3 REST convention in
  `CLAUDE.md` / `AGENTS.md` / `BOB.md`, the `SKILL.md` dependency baseline, and the
  `docs/VALIDATING-TEMPLATES.md` extension list. Jackson is the Quarkus default JSON serializer,
  confirmed via the Quarkus Agents MCP against the `rest-json` guide. The Java templates use plain
  records (no JSON-B annotations), so no code changes were required.
- Reconciled the `pom.xml.template` platform baseline `3.36.0` → `3.36.1` to match the current
  Quarkus platform (verified via `quarkus_create`); all 14 template files compile against it.
- All version headers synchronized to 0.5.0.

## v0.4.0 — 2026-06-03
- Added native Bob support alongside the existing Claude and Codex support: `BOB.md`,
  `.bob-plugin/plugin.json`, and Bob-specific plugin metadata for the scaffolding skill.
- README: documented Bob prerequisites, plugin installation, and the relationship between
  `BOB.md`, `CLAUDE.md`, `AGENTS.md`, and the shared scaffolding skill.
- CONTRIBUTING: updated ownership and versioning guidance to include Bob in the list of supported
  agents.
- All version headers synchronized to 0.4.0 across `README.md`, `CLAUDE.md`, `AGENTS.md`,
  `BOB.md`, `SKILL.md`, and all plugin manifests.


## v0.3.0 — 2026-06-03
- Added native Codex support alongside the existing Claude support: `AGENTS.md`,
  `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`, a non-duplicating
  `plugins/quarkus-agentic/` marketplace wrapper, and Codex app metadata for the scaffolding
  skill.
- README: documented Codex prerequisites, plugin installation, and the relationship between
  `AGENTS.md`, `CLAUDE.md`, and the shared scaffolding skill.
- CONTRIBUTING: updated ownership and versioning guidance so future changes keep Claude and Codex
  surfaces in sync.

## v0.2.0 — 2026-06-01
- Packaged as an installable Claude Code **plugin**: added `.claude-plugin/plugin.json` and
  `.claude-plugin/marketplace.json` (the repository is both the marketplace and the plugin). The
  `CLAUDE.md` conventions remain a per-project drop-in, since a plugin cannot deliver them.
- README: replaced the manual skill-zip upload with plugin install (`/plugin marketplace add` +
  `/plugin install`); added exact install commands for the required Quarkus Agents MCP and
  context7; documented `CLAUDE.md` precedence and how to revert a global install.
- Refreshed the Quarkus platform baseline in `pom.xml.template` from `3.35.3` to `3.36.0` (verified
  current via the Quarkus Agents MCP) and clarified that the pinned version is a reference baseline.
- Verified all templates compile against Quarkus `3.36.0` (Java 25), including the LangChain4j
  agentic API; added `docs/VALIDATING-TEMPLATES.md` describing the procedure.
- Added `CONTRIBUTING.md` (replacing the README placeholder).

## v0.1.0 — 2026-06-01
- Initial release.
- `CLAUDE.md` baseline conventions distilled from real-world Quarkus + LangChain4j practice,
  combined with a modern-Java baseline.
- `quarkus-langchain4j-scaffolding` skill with templates for project setup
  (`pom.xml`, `application.properties`), AI services, agents, and RAG pipelines.
- Licensed under Apache-2.0.
