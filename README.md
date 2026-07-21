# Quarkus + LangChain4j + AI Stack
# Version: 0.12.1

## What this repository is

A small, opinionated, distribution-ready artifact for building AI and agent applications on the
Java stack of **Quarkus + LangChain4j**. It pairs drop-in always-on coding conventions
(`CLAUDE.md` for Claude, `AGENTS.md` for Codex and Bob) with three skills that set up the
prerequisites, scaffold new projects and components, and audit existing projects — all from
working templates. The conventions and templates reflect real-world Quarkus + LangChain4j
practice and a baseline of modern Java, so the guidance captures how these systems are actually
built rather than generic boilerplate.

## What's inside

```
.
├── README.md                 # This file
├── CLAUDE.md                 # Always-on project conventions (drop into your project root)
├── AGENTS.md                 # Codex/Bob equivalent of the always-on project conventions
├── CONTRIBUTING.md           # How to propose changes
├── CHANGELOG.md              # Release history
├── LICENSE                   # Apache-2.0
├── .gitignore
├── .claude-plugin/           # Claude installable-plugin + marketplace manifests
│   ├── plugin.json
│   └── marketplace.json
├── .codex-plugin/            # Codex plugin manifest
│   └── plugin.json
├── gemini-extension.json     # Gemini CLI extension manifest (declares the MCP servers)
├── .agents/
│   └── plugins/
│       └── marketplace.json  # Codex repo-local marketplace manifest
├── plugins/
│   └── quarkus-agentic-scaffolding/  # Codex marketplace wrapper; symlinks to .codex-plugin + skills
├── scripts/
│   └── install-bob-skill.sh  # Fallback: copy the skills into a project's (or global) .bob/skills/
├── docs/
│   └── VALIDATING-TEMPLATES.md   # How to verify the templates still build
└── skills/
    ├── setup-agentic-scaffolding/   # User-invoked: prerequisites (toolchain, MCP, conventions)
    │   ├── SKILL.md
    │   └── templates/
    │       ├── conventions-CLAUDE.md    # Byte-for-byte seed copy of root CLAUDE.md
    │       └── conventions-AGENTS.md    # Byte-for-byte seed copy of root AGENTS.md
    ├── scaffold-project/            # Create projects + add components (model-invoked umbrella)
    │   ├── SKILL.md
    │   └── templates/
    │       ├── pom.xml.template
    │       ├── application.properties.template
    │       ├── AiService.java.template
    │       ├── AiServiceTest.java.template
    │       ├── Agent.java.template
    │       ├── McpClient.java.template
    │       ├── McpServer.java.template
    │       ├── Tools.java.template
    │       ├── Guardrails.java.template
    │       └── RagSetup.java.template
    └── audit-project/               # User-invoked: audit an existing project vs the conventions
        └── SKILL.md
```

## Quick install — any skills-capable agent

[![Skills](https://skills.sh/b/eldermoraes/quarkus-agentic-scaffolding)](https://skills.sh)

The fastest install on any agent that supports the [Agent Skills](https://agentskills.io) format —
Claude Code, Codex, GitHub Copilot, Cursor, Windsurf, opencode, Amp, IBM Bob, and dozens more:

```
npx skills add eldermoraes/quarkus-agentic-scaffolding
```

The [skills.sh](https://www.skills.sh/) CLI detects your agents and installs all three skills
(`setup-agentic-scaffolding`, `scaffold-project`, `audit-project`) into each of them — IBM Bob
included, as a first-class agent. Two things it does **not** set up, which
`/setup-agentic-scaffolding` (below) handles for you: the always-on conventions file (`CLAUDE.md`
for Claude, `AGENTS.md` for everything else) that lands in your project root, and the required MCP
tooling (Quarkus Agents MCP + context7).

## The flow

Three skills, run in order the first time and revisited as needed:

- **`/setup-agentic-scaffolding`** — user-invoked; run once per machine, then re-visit per
  project. Verifies the toolchain (JDK 25 / GraalVM, JBang, a container runtime), registers the
  Quarkus Agents MCP + context7 for your agent, and drops the conventions file into your project.
- **`/scaffold-project`** — creates a new Quarkus + LangChain4j project end-to-end, and also
  auto-triggers when you ask to add a component (an AI service, tool, agent/workflow, RAG
  pipeline, MCP client or server, or guardrail) to an existing project.
- **`/audit-project`** — user-invoked; points at an *existing* project and reports how it
  conforms to (or is ready to adopt) the conventions, fixing findings only after you confirm.

**Two invocation forms.** How you installed the skills decides the slash-command name in Claude
Code: a **skills-CLI install** (the Quick install above) gives bare names —
`/setup-agentic-scaffolding`, `/scaffold-project`, `/audit-project`; a **plugin install** (the
per-agent sections below) namespaces them by the plugin id — `/quarkus-agentic-scaffolding:setup-agentic-scaffolding`,
`/quarkus-agentic-scaffolding:scaffold-project`, `/quarkus-agentic-scaffolding:audit-project`. Both refer to the same
skills; use whichever your install produced.

## How to use with Claude

**Install the skills (plugin).** Add this repository as a plugin marketplace and install it:

```
/plugin marketplace add eldermoraes/quarkus-agentic-scaffolding
/plugin install quarkus-agentic-scaffolding@eldermoraes
```

All three skills and the `scaffold-project` `templates/` are installed and auto-discovered. (Or
use the [Quick install](#quick-install--any-skills-capable-agent) above, which works for Claude
Code too.)

**Set up the prerequisites.** Run `/setup-agentic-scaffolding` (or
`/quarkus-agentic-scaffolding:setup-agentic-scaffolding` on a plugin install) — it verifies the toolchain,
registers the **Quarkus Agents MCP** and **context7** MCP servers, and drops `CLAUDE.md` into your
project root. `CLAUDE.md` §1 makes those two MCP servers non-negotiable for this stack, and the
setup skill is what puts them in place.

*Manual fallback,* if you would rather wire it by hand: install the Quarkus Agents MCP with
`/plugin marketplace add quarkusio/quarkus-agent-mcp` then `/plugin install quarkus-agent@quarkus-tools`;
add context7 with `claude mcp add context7 -- npx -y @upstash/context7-mcp` (append
`--api-key <KEY>` for higher rate limits); optionally install superpowers with
`/plugin marketplace add obra/superpowers-marketplace` then
`/plugin install superpowers@superpowers-marketplace`; and copy [`CLAUDE.md`](CLAUDE.md) into your
project root yourself (Claude only auto-loads it from a project root or `~/.claude/`, so no plugin
can ship it for you).

**Try it.** Open your project and use a trigger phrase such as *"scaffold a new Quarkus +
LangChain4j project"*, *"create a new AI service"*, or *"set up a new RAG pipeline"* —
`scaffold-project` produces the layout and starter files, and `CLAUDE.md` governs the conventions
of the code that follows. To review an existing project, run `/audit-project`.

## How to use with Codex

**Install the skills (plugin).** Add this repository as a Codex plugin marketplace, then install
the plugin from the plugins list:

```
codex plugin marketplace add eldermoraes/quarkus-agentic-scaffolding
```

Open Codex, run `/plugins`, select the `eldermoraes` marketplace, and install `quarkus-agentic-scaffolding`.
All three skills and the `scaffold-project` `templates/` are auto-discovered. (Codex also
auto-discovers skills placed under `.agents/skills/`, and the [Quick install](#quick-install--any-skills-capable-agent)
works for Codex too.)

**Set up the prerequisites.** Run `/setup-agentic-scaffolding` — it verifies the toolchain,
registers the **Quarkus Agents MCP** and **context7** MCP servers for Codex, and drops `AGENTS.md`
into your project root. `AGENTS.md` §1 makes those two MCP servers non-negotiable for this stack.

*Manual fallback:* add the Quarkus Agents MCP with `codex mcp add quarkus-agent -- jbang quarkus-agent-mcp@quarkusio`;
add context7 with `codex mcp add context7 -- npx -y @upstash/context7-mcp` (append `--api-key <KEY>`
for higher rate limits); install/enable the Superpowers plugin if you use it; and copy
[`AGENTS.md`](AGENTS.md) into your project root (Codex reads project instructions from the project
tree).

**Try it.** Use a trigger phrase such as *"scaffold a new Quarkus + LangChain4j project"* or
*"create a new AI service"*; `scaffold-project` produces the layout and starter files and
`AGENTS.md` governs the conventions. Run `/audit-project` to review an existing project.

## How to use with Bob

IBM Bob reads the same `AGENTS.md` that Codex does, so the conventions are shared. Bob is a
first-class agent in the skills CLI, so the [Quick install](#quick-install--any-skills-capable-agent)
(`npx skills add eldermoraes/quarkus-agentic-scaffolding`) installs all three skills into
`.bob/skills/` for you — that is the recommended path.

**Set up the prerequisites.** Run `/setup-agentic-scaffolding` — it verifies the toolchain,
registers the **Quarkus Agents MCP** and **context7** MCP servers for Bob (via `.bob/mcp.json`),
and drops `AGENTS.md` into your project root. If you already added `AGENTS.md` for Codex, the same
file serves Bob — there is no separate `BOB.md`.

*Manual fallback:* configure the MCP servers in `.bob/mcp.json` at your project root (or
`~/.bob/mcp_settings.json` for all projects), or from the **MCP** tab in the Bob UI:

```json
{
  "mcpServers": {
    "quarkus-agent": { "command": "jbang", "args": ["quarkus-agent-mcp@quarkusio"] },
    "context7":      { "command": "npx",   "args": ["-y", "@upstash/context7-mcp"] }
  }
}
```

(`jbang` must be on your PATH; append `--api-key` and `<KEY>` to context7's `args` for higher rate
limits.) If the skills CLI is unavailable, the repository's fallback helper installs all three
skills into `.bob/skills/` for you:

```
./scripts/install-bob-skill.sh                   # into <cwd>/.bob/skills/
./scripts/install-bob-skill.sh /path/to/project  # into that project's .bob/skills/
./scripts/install-bob-skill.sh --global          # into ~/.bob/skills/
```

Bob asks for approval before activating a skill the first time.

**Try it.** Use a trigger phrase such as *"scaffold a new Quarkus + LangChain4j project"*;
`scaffold-project` produces the layout and starter files and `AGENTS.md` governs the conventions.
Run `/audit-project` to review an existing project.

## What's in `CLAUDE.md` / `AGENTS.md` and why

`CLAUDE.md` (Claude) and `AGENTS.md` (Codex and Bob) are intentionally short and always-on. They
carry the same project conventions, expressed for the instruction surface each agent reads. Each
section earns its place:

- **§1 Required tooling (mandatory).** Makes `context7` and the **Quarkus Agents MCP** required,
  not optional: every Quarkus task goes through the Quarkus Agents MCP and every library lookup
  through `context7`, with `superpowers` skills used where applicable. If a required tool is
  missing, work stops rather than falling back to stale model memory.
- **§2 Java conventions.** Sets Java 25 as the *minimum*, makes **virtual threads** the default
  carrier for blocking work, prefers **Scoped Values** over `ThreadLocal`, gives a pragmatic
  stance on structured concurrency, and favors **records / sealed types / pattern matching**.
  These are the modern-Java habits that make AI code simpler and more debuggable.
- **§3 Quarkus conventions.** Platform BOMs over pinned versions, CDI-first wiring, Quarkus REST +
  OpenAPI, WebSockets Next for streaming, the `-parameters` flag, a dual JVM/native build,
  zero-code AI observability via Micrometer + OpenTelemetry, and turning off Dev Services when a
  real model endpoint is configured.
- **§4 LangChain4j conventions.** Declarative `@RegisterAiService` over manual wiring, declarative
  **agentic** composition for multi-agent workflows, typed structured output, named/right-sized
  models, a streaming pattern that keeps reactive types at the edge, declarative fault tolerance
  on AI-service methods, and **Easy RAG first**.
- **§5 Testing.** A minimal intended baseline (`@QuarkusTest` + REST-assured + native ITs),
  flagged as a target rather than an observed standard.
- **§6 Scope and overrides.** States that per-project deviations are allowed when documented
  inline — the conventions guide, they do not imprison.

## What the skills do and how they compose with the conventions

The three skills split along the **invocation axis**, and all defer to the always-on convention
file for the active agent rather than restating the rules — a single source of truth per agent:
scaffolding and setup in the skills, rules in `CLAUDE.md` or `AGENTS.md`.

- **`setup-agentic-scaffolding`** (user-invoked) prepares the environment the other two skills
  depend on: it checks the toolchain, registers the Quarkus Agents MCP + context7 for the agent
  you are running, and writes the conventions file (seeded from byte-for-byte copies inside the
  skill folder) into your project. It is the one skill that legitimately runs *before* the MCP
  exists — that is its job.
- **`scaffold-project`** (model-invoked umbrella) handles the *"create something new"* moments. It
  is deliberately a single skill covering **both** ends of creation: bootstrapping a new project
  end-to-end (delegating skeleton, BOMs, and the native profile to the Quarkus Agents MCP, then
  applying the repo's package layout, `application.properties` baseline, non-extension deps, and
  starter templates), **and** adding components to an existing project — an AI service, tool,
  agent/workflow, RAG pipeline, MCP client or server, or guardrail. Keeping creation and
  components together (owner decision) minimizes the number of skills you face; it stays
  model-invoked so component requests auto-trigger.
- **`audit-project`** (user-invoked) is read-only by default: it audits an existing project
  against §2–§5, the package layout, and the dependency/properties baseline, and reports
  prioritized findings with evidence and a suggested fix each — applying fixes only after you
  confirm, by handing off to `scaffold-project`'s component sections.

The split between skill and conventions is deliberate and non-overlapping:

- **The skills are procedural** — they tell the agent (Claude, Codex, or Bob) *how to set up,
  lay things out, and get them running*, and point at the Quarkus Agents MCP to actually create
  and run the project.
- **`CLAUDE.md` / `AGENTS.md` are declarative** — they state the conventions the resulting code
  must follow (`CLAUDE.md` for Claude, `AGENTS.md` for Codex and Bob).

For Codex distribution, `.agents/plugins/marketplace.json` points to `plugins/quarkus-agentic-scaffolding/`.
That directory is only a lightweight wrapper with symlinks back to `.codex-plugin/` and `skills/`,
so the Claude and Codex packages share the same skill content. Bob does not use a marketplace; its
skills are installed by the skills CLI (or `scripts/install-bob-skill.sh`) into `.bob/skills/`.

## Advanced — personal use (optional global install)

A power user who works *exclusively* in this stack can apply the conventions globally instead of
copying the file into each project:

- **Claude** — move the contents of `CLAUDE.md` into the global `~/.claude/CLAUDE.md`.
- **Codex** — move the contents of `AGENTS.md` into `~/.codex/AGENTS.md`.
- **Bob** — Bob has no global conventions file, but it loads global *rules* from `~/.bob/rules/`;
  drop the conventions there (for example `~/.bob/rules/quarkus-langchain4j.md`). Install the
  skills globally with `./scripts/install-bob-skill.sh --global` (into `~/.bob/skills/`), and put
  shared MCP servers in `~/.bob/mcp_settings.json`.

**Trade-off (stated explicitly):** the global files apply to **all** work on your machine or
agent profile. If you also work in other stacks (other languages, frameworks, or non-AI Java
projects), these Quarkus/LangChain4j-specific rules will bleed into unrelated work. For anyone who
mixes stacks, the per-project drop-in is recommended over the global install.

**Precedence and reverting.** A project-root convention file is read *in addition to* a global
one, and project guidance can override broader global rules. To undo a global install, delete the
global file (or remove just the Quarkus/LangChain4j section you pasted into it).

## Versioning and changelog

This artifact uses semantic versioning. `README.md`, `CLAUDE.md`, `AGENTS.md`, the three
`skills/*/SKILL.md` files (`setup-agentic-scaffolding`, `scaffold-project`, `audit-project`),
`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, and `gemini-extension.json` each carry
a matching version header — nine files, enforced in CI by `ci/check-version-consistency.sh`. See
[`CHANGELOG.md`](CHANGELOG.md) for release history.

## License

Licensed under the **Apache License 2.0**. See [`LICENSE`](LICENSE) for the full text.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to propose changes to the conventions, the skills,
and the templates — including how to keep new patterns evidence-backed, and how to confirm the
templates still build (see [`docs/VALIDATING-TEMPLATES.md`](docs/VALIDATING-TEMPLATES.md)).
