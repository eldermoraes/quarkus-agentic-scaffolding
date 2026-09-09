# Anthropic community submission kit

Prepared 2026-09-09 for [issue #4](https://github.com/eldermoraes/quarkus-agentic-scaffolding/issues/4).
**Not submitted.** The Console URL was opened in a browser and displayed login, not submission
fields. The values below come from repository manifests; field names/category are inferred until
an authenticated form is inspected. This replaces the obsolete v0.8.0 single-skill worksheet.

## Destination and completion

Use the [Console submission form](https://platform.claude.com/plugins/submit) for an individual
author. Anthropic's [submission documentation](https://code.claude.com/docs/en/plugins#submit-your-plugin-to-the-community-marketplace)
identifies this as review for `claude-community`. The separate `claude-plugins-official` marketplace
is curated by Anthropic and has no application process. Submission does not guarantee acceptance.

Authenticate, match the live fields to the values below, inspect any required declarations, and
submit only when those declarations are accurate. Record the actual receipt or submission ID in
issue #4; keep the issue open until that exists. If accepted, verify the plugin appears in the
[community catalog](https://github.com/anthropics/claude-plugins-community) before claiming it is
installable there.

## Values for the live form

| Meaning | Value |
| --- | --- |
| Plugin identifier | `quarkus-agentic-scaffolding` |
| Display name | Quarkus Agentic Scaffolding |
| Repository/homepage | `https://github.com/eldermoraes/quarkus-agentic-scaffolding` |
| Marketplace | `eldermoraes` |
| Plugin manifest | `.claude-plugin/plugin.json` |
| Marketplace manifest | `.claude-plugin/marketplace.json` |
| Author | Elder Moraes |
| Public maintainer contact | `elder.moraes@gmail.com` |
| License | `Apache-2.0` |
| Suggested category, if offered | Developer Tools |
| Keywords | quarkus, langchain4j, ai, agents, rag, mcp, scaffolding, setup, audit, java |
| Version | Read `version` from `.claude-plugin/plugin.json` at submission time |
| Review commit, if requested | Resolve the current release tag to its commit at submission time |

Short description:

> Setup, scaffold and audit Quarkus + LangChain4j agentic Java applications using shared
> conventions and build-checked templates.

Long description:

> Quarkus Agentic Scaffolding provides three skills: setup-agentic-scaffolding prepares toolchain,
> MCP registration and project conventions; scaffold-project creates projects and adds AI services,
> workflows, RAG and MCP components; audit-project reviews conformance. Project creation and
> Quarkus work use the external Quarkus Agents MCP, and library documentation uses Context7.
> Templates are checked by CI against the configured Quarkus platform; generated application
> behavior still needs project-specific review and tests. The setup skill copies conventions into
> the project so they are loaded as project context.

## Scope statement for reviewers

The Claude manifests declare three skill directories and no hooks, MCP servers, LSP servers,
background monitors or telemetry components. Their absence is a statement about inspected plugin
declarations, not a claim about the host agent or third-party services.

Invoked skills can perform actions: setup probes prerequisites, proposes tool installation,
registers external MCP configuration with the user's approval, and writes project conventions;
scaffolding creates files and uses external tooling; auditing is read-only by default. MCP tools,
package downloads, documentation queries and builds can use the network. Generated applications
may call model providers according to their own configuration.

The repository also contains installation/uninstallation helpers, CI/check/release scripts and
an opt-in evaluation runner. These are not a single copy-only executable and are not automatically
run by a Claude manifest declaration. Bob's fallback installer refreshes skill supporting files.
The separate Gemini extension declares the two external MCP servers; that is a different
installation route. Review the repository rather than assuming every distribution loads the same
components. Do not claim that external tools are telemetry-free or that this repository never
performs network requests.

## Validation record

Validated on 2026-09-09 with Claude Code `2.1.266`:

```sh
claude plugin validate .claude-plugin/marketplace.json
claude plugin validate .claude-plugin/plugin.json
```

Marketplace validation passes without warnings after adding its optional description. Plugin
validation passes with one warning: root `CLAUDE.md` is not automatically loaded as project
context. This is expected for this package: setup ships convention seeds and copies them into the
user's project. The submission must not suggest that installing the plugin alone loads those
conventions. Re-run both checks against the exact version being submitted.
