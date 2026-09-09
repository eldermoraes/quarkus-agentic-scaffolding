# Contributing

Thanks for helping improve this artifact. It is small on purpose, and every rule and template is
meant to be **evidence-backed** — derived from how real Quarkus + LangChain4j projects are built,
not from generic boilerplate. Contributions are expected to keep that bar.

## What lives where

- **`CLAUDE.md`** — *declarative* conventions (the rules generated code must follow). Always-on.
- **`AGENTS.md`** — the Codex and Bob equivalent of `CLAUDE.md`. Always-on for Codex and Bob.
- **`skills/`** — the three *procedural* skills, each a `SKILL.md` (some with `templates/`):
  `setup-agentic-scaffolding` (prerequisites), `scaffold-project` (create projects and add
  components; owns `templates/`), and `audit-project` (conformance/adoption review). Packaged
  as the plugin for Claude and Codex, and copied into Bob's `.bob/skills/` by
  `scripts/install-bob-skill.sh`.
- **`.claude-plugin/`** — `plugin.json` + `marketplace.json` (the Claude installable
  distribution).
- **`.codex-plugin/`** — `plugin.json` (the Codex plugin manifest).
- **`.agents/plugins/marketplace.json`** — repo-local Codex marketplace entry.
- **`plugins/quarkus-agentic-scaffolding/`** — Codex marketplace wrapper with symlinks to `.codex-plugin/`
  and `skills/`; do not put duplicate skill content here.
- **`scripts/install-bob-skill.sh`** — installs the skill into a project's (or global) `.bob/skills/`
  for Bob (whose marketplace is IBM-internal and distributes modes and MCP servers, not skills).
- **`scripts/uninstall-bob-skill.sh`** — the mirror of the installer: removes the three skills
  from a project's (or global) `.bob/skills/`, ownership-checked and safe to re-run. Behavior-tested
  by `ci/test-uninstall-bob-skill.sh`.

Keep the split clean: the skill says *how to lay things out*; `CLAUDE.md` and `AGENTS.md` say
*what the code must do*. Do not restate conventions inside the skill — cross-reference the
always-on files instead.

## Required tooling

The mandatory tooling in `CLAUDE.md` §1 and `AGENTS.md` §1 governs using the scaffolding in
Quarkus + LangChain4j applications. When maintaining this repository itself, apply the
requirements to the operation being performed:

- **Quarkus Agents MCP** is required for Quarkus project creation, extension selection,
  configuration, version verification, API lookup, and troubleshooting.
- **context7** is required for external library/framework API documentation lookup
  (LangChain4j included).
- Repository maintenance — inspecting diffs, editing prose, reviewing PRs, checking CI results,
  and merging approved changes — may proceed without an MCP that the operation does not use.
  A dependency bump still requires the relevant tool if its review needs an API or Quarkus
  version lookup.

If a required tool is unavailable, report and pause only the operation that needs it; continue
independent maintenance work. Confirm convention or template changes against the relevant tool
before encoding library/framework behavior. This maintenance scope does not relax the tooling
requirements for applications using the scaffolding.

## Proposing a change

1. **Open an issue** describing the change and the evidence behind it.
2. **Branch** from `main`.
3. Make the change in the right place (`CLAUDE.md` / `AGENTS.md` vs `SKILL.md` vs a template).
4. If you touch a template, **validate it still builds** — see
   [`docs/VALIDATING-TEMPLATES.md`](docs/VALIDATING-TEMPLATES.md).
5. **Record the change in `CHANGELOG.md` under a `## Unreleased` heading** at the top of the
   file, creating that section if it is not there. Do not pick a version number and do not touch
   the version headers: with concurrent PRs the next version is unknowable from a branch, so the
   bump is the maintainer's job at release time (see [Versioning](#versioning)).
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

This artifact uses semantic versioning. The canonical file inventory and seed mappings live in
`ci/versioning.py`; `ci/check-version-consistency.sh` checks their version agreement. Contributors
record changes under `## Unreleased` in `CHANGELOG.md`. At release time, the maintainer runs
`ci/bump-version.sh <major.minor.patch>` and renames the changelog section to that version in the
same commit. The command preserves file formatting and re-copies the root conventions into the
setup skill's seeds. It validates inputs before writing; it does not provide rollback for a
filesystem failure during writes. Review the diff and run the version and convention parity
checks before tagging.

The launch command for the Quarkus Agents MCP is hand-maintained in ~15 places, and
`ci/check-mcp-command-consistency.sh` couples them: every published registration must carry
`--java 21+` and the same pinned GAV version. `CHANGELOG.md` and `docs/` are exempt, because they
quote older commands as a record.

The `mcp-java-floor` quality job also starts the manifest's pinned runner with an exact
`jbang --java 21` request and requires a valid MCP initialization response. It clears Java/JBang
runtime overrides and bounds startup time. This checks startup compatibility on the advertised
minimum JDK, not every tool's runtime behavior. Run `python3 ci/check_mcp_java_floor.py` locally
with JBang installed; its offline failure-path tests run with
`python3 -m unittest discover -s ci -p 'test_*.py'`.

## License

By contributing, you agree your contributions are licensed under the project's
[Apache License 2.0](LICENSE).
