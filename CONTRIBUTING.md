# Contributing

Thanks for helping improve this artifact. It is small on purpose, and every rule and template is
meant to be **evidence-backed** — derived from how real Quarkus + LangChain4j projects are built,
not from generic boilerplate. Contributions are expected to keep that bar.

## What lives where

- **`CLAUDE.md`** — *declarative* conventions (the rules generated code must follow). Always-on.
- **`AGENTS.md`** — the Codex and Bob equivalent of `CLAUDE.md`. Always-on for Codex and Bob.
- **`skills/quarkus-langchain4j-scaffolding/`** — the *procedural* scaffolding skill (`SKILL.md`)
  and its `templates/`. Packaged as the plugin for Claude and Codex, and copied into Bob's
  `.bob/skills/` by `scripts/install-bob-skill.sh`.
- **`.claude-plugin/`** — `plugin.json` + `marketplace.json` (the Claude installable
  distribution).
- **`.codex-plugin/`** — `plugin.json` (the Codex plugin manifest).
- **`.agents/plugins/marketplace.json`** — repo-local Codex marketplace entry.
- **`plugins/quarkus-agentic/`** — Codex marketplace wrapper with symlinks to `.codex-plugin/`
  and `skills/`; do not put duplicate skill content here.
- **`scripts/install-bob-skill.sh`** — installs the skill into a project's (or global) `.bob/skills/`
  for Bob (which has no plugin marketplace).

Keep the split clean: the skill says *how to lay things out*; `CLAUDE.md` and `AGENTS.md` say
*what the code must do*. Do not restate conventions inside the skill — cross-reference the
always-on files instead.

## Required tooling

The same tooling the stack mandates applies to contributors (see `CLAUDE.md` §1 or `AGENTS.md` §1):

- **Quarkus Agents MCP** for any Quarkus work (project creation, extensions, version checks, docs).
- **context7** for any external library/framework API lookup (LangChain4j included).

Do not change a convention or template from model memory or a generic web search — confirm it
against these tools first.

## Proposing a change

1. **Open an issue** describing the change and the evidence behind it.
2. **Branch** from `main`.
3. Make the change in the right place (`CLAUDE.md` / `AGENTS.md` vs `SKILL.md` vs a template).
4. If you touch a template, **validate it still builds** — see
   [`docs/VALIDATING-TEMPLATES.md`](docs/VALIDATING-TEMPLATES.md).
5. **Bump the version** (semver) in the version headers of `README.md`, `CLAUDE.md`,
   `AGENTS.md`, `SKILL.md`, `.claude-plugin/plugin.json`, and `.codex-plugin/plugin.json`, and add a
   `CHANGELOG.md` entry.
6. Open a PR that links the issue and summarizes the evidence.

### Evidence bar for conventions and templates

A change to a convention or a template should be backed by one of:

- an established pattern across real-world Quarkus + LangChain4j projects;
- official Quarkus / LangChain4j documentation confirmed via the Quarkus Agents MCP or context7; or
- a reproducible build/runtime result (e.g. the template fails to compile against the current
  platform, or a new extension supersedes an old pattern).

Taste-only or "this looks cleaner" changes to the conventions are unlikely to be accepted without
one of the above.

## Keeping changes grounded

Conventions and templates should reflect how real Quarkus + LangChain4j systems are actually built:

1. Prefer patterns that recur across multiple real-world projects over one-off choices from a
   single codebase.
2. Confirm any API or configuration against the Quarkus Agents MCP or context7 before encoding it.
3. Distill only the **recurring, defensible** patterns into `CLAUDE.md` / `AGENTS.md` and the
   templates; document any deliberate deviation inline (see `CLAUDE.md` §6 or `AGENTS.md` §6).
4. When a change is driven by a build or runtime result, capture that rationale in the
   `CHANGELOG.md` entry.

## Versioning

This artifact uses semantic versioning. Keep the version header identical across `README.md`,
`CLAUDE.md`, `AGENTS.md`, `SKILL.md`, `.claude-plugin/plugin.json`, and
`.codex-plugin/plugin.json`, and record every change in `CHANGELOG.md`.

## License

By contributing, you agree your contributions are licensed under the project's
[Apache License 2.0](LICENSE).
