# Changelog

All notable changes to this artifact are documented here. This project adheres to semantic
versioning.

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
