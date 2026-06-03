# Changelog

All notable changes to this artifact are documented here. This project adheres to semantic
versioning.

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
