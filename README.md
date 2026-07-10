# Quarkus + LangChain4j + AI Stack
# Version: 0.8.0

## What this repository is

A small, opinionated, distribution-ready artifact for building AI and agent applications on the
Java stack of **Quarkus + LangChain4j**. It pairs drop-in always-on coding conventions
(`CLAUDE.md` for Claude, `AGENTS.md` for Codex and Bob) with a reusable skill that
scaffolds new projects, AI services, agents, and RAG pipelines from working templates. The
conventions and templates reflect real-world Quarkus + LangChain4j practice and a baseline of
modern Java, so the guidance captures how these systems are actually built rather than generic
boilerplate.

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
├── .agents/
│   └── plugins/
│       └── marketplace.json  # Codex repo-local marketplace manifest
├── plugins/
│   └── quarkus-agentic/      # Codex marketplace wrapper; symlinks to .codex-plugin + skills
├── scripts/
│   └── install-bob-skill.sh  # Copy the skill into a project's (or global) .bob/skills/
├── docs/
│   └── VALIDATING-TEMPLATES.md   # How to verify the templates still build
└── skills/
    └── quarkus-langchain4j-scaffolding/
        ├── SKILL.md           # The scaffolding skill
        └── templates/
            ├── pom.xml.template
            ├── application.properties.template
            ├── AiService.java.template
            ├── Agent.java.template
            └── RagSetup.java.template
```

## Quick install — any skills-capable agent

The fastest install on any agent that supports the [Agent Skills](https://agentskills.io) format —
Claude Code, Codex, GitHub Copilot, Cursor, Windsurf, opencode, Amp, and dozens more:

```
npx skills add eldermoraes/quarkus-agentic-scaffolding
```

The [skills.sh](https://www.skills.sh/) CLI detects your agents and installs the
`quarkus-langchain4j-scaffolding` skill for each of them. Two things it does **not** set up, which
the per-agent sections below cover: the always-on conventions file (`CLAUDE.md` for Claude,
`AGENTS.md` for everything else) that you copy into your project root, and the required MCP
tooling (Quarkus Agents MCP + context7).

## How to use with Claude

**Prerequisites (required).** `CLAUDE.md` §1 makes three pieces of tooling non-negotiable for this
stack. Make them available in your Claude environment:

- **Quarkus Agents MCP** (mandatory) — all Quarkus work goes through it. Install the official plugin:
  ```
  /plugin marketplace add quarkusio/quarkus-agent-mcp
  /plugin install quarkus-agent@quarkus-tools
  ```
- **context7** (mandatory) — all library/framework documentation lookups go through it:
  ```
  claude mcp add context7 -- npx -y @upstash/context7-mcp
  ```
  (Append `--api-key <KEY>` for higher rate limits.)
- **superpowers skills** — invoked wherever applicable to the task. Install the plugin:
  ```
  /plugin marketplace add obra/superpowers-marketplace
  /plugin install superpowers@superpowers-marketplace
  ```

Set up both pieces — the conventions and the skill — then test it. They install differently: the
skill ships as a plugin, but `CLAUDE.md` must live in your project (a plugin cannot deliver it).

1. **Add the conventions.** Copy [`CLAUDE.md`](CLAUDE.md) to the root of your Quarkus +
   LangChain4j project. Claude Code and Cowork read it automatically and apply it whenever they
   write or review code in that project. This step is manual *by design* — Claude only auto-loads
   `CLAUDE.md` from a project root (or `~/.claude/`), so no plugin can ship it for you.

2. **Install the skill (plugin).** Add this repository as a plugin marketplace and install it:
   ```
   /plugin marketplace add eldermoraes/quarkus-agentic-scaffolding
   /plugin install quarkus-agentic@eldermoraes
   ```
   The `quarkus-langchain4j-scaffolding` skill and its `templates/` are installed and
   auto-discovered.

3. **Try it.** Open your project in Claude Code or Cowork and use a trigger phrase such as
   *"scaffold a new Quarkus + LangChain4j project"*, *"create a new AI service"*,
   *"scaffold a new agent"*, or *"set up a new RAG pipeline"*. The skill produces the layout and
   starter files; `CLAUDE.md` governs the conventions of the code that follows.

## How to use with Codex

**Prerequisites (required).** `AGENTS.md` §1 mirrors the same non-negotiable stack requirements for
Codex. Make them available in your Codex environment:

- **Quarkus Agents MCP** (mandatory) — all Quarkus work goes through it. It is a standalone MCP
  server; add it to Codex with JBang:
  ```
  codex mcp add quarkus-agent -- jbang quarkus-agent-mcp@quarkusio
  ```
- **context7** (mandatory) — all library/framework documentation lookups go through it:
  ```
  codex mcp add context7 -- npx -y @upstash/context7-mcp
  ```
  (Append `--api-key <KEY>` for higher rate limits.)
- **superpowers skills** — invoked wherever applicable to the task. Install or enable the
  Superpowers plugin in your Codex environment.

Set up both pieces — the conventions and the skill — then test it. They install differently: the
skill ships as a plugin, but `AGENTS.md` must live in your project because Codex reads project
instructions from the project tree.

1. **Add the conventions.** Copy [`AGENTS.md`](AGENTS.md) to the root of your Quarkus +
   LangChain4j project. Codex reads it automatically before it starts work in that project.

2. **Install the skill (plugin).** Add this repository as a Codex plugin marketplace, then install
   the plugin from the plugins list:
   ```
   codex plugin marketplace add eldermoraes/quarkus-agentic-scaffolding
   ```
   Open Codex and run `/plugins`, select the `eldermoraes` marketplace, and install
   `quarkus-agentic`. The `quarkus-langchain4j-scaffolding` skill and its `templates/` are then
   auto-discovered. (Alternatively, Codex auto-discovers skills placed under `.agents/skills/`, so
   you can drop the skill there instead of installing the plugin.)

3. **Try it.** Open your project in Codex and use a trigger phrase such as
   *"scaffold a new Quarkus + LangChain4j project"*, *"create a new AI service"*,
   *"scaffold a new agent"*, or *"set up a new RAG pipeline"*. The skill produces the layout and
   starter files; `AGENTS.md` governs the conventions of the code that follows.

## How to use with Bob

**Prerequisites (required).** `AGENTS.md` §1 makes the same stack tooling non-negotiable. Bob reads
the same `AGENTS.md` that Codex does, so the conventions are shared. Make the tooling available in
your Bob environment:

- **Quarkus Agents MCP** (mandatory) — all Quarkus work goes through it. It is a standalone MCP
  server, and IBM Bob is a supported client. Configure it in `.bob/mcp.json` at your project root
  (or `~/.bob/mcp_settings.json` for all projects), alongside context7:
  ```json
  {
    "mcpServers": {
      "quarkus-agent": { "command": "jbang", "args": ["quarkus-agent-mcp@quarkusio"] },
      "context7":      { "command": "npx",   "args": ["-y", "@upstash/context7-mcp"] }
    }
  }
  ```
  You can also add these from the **MCP** tab in the Bob UI. (`jbang` must be on your PATH; for
  higher context7 rate limits, append `--api-key` and `<KEY>` to its `args`.)
- **superpowers skills** (optional) — Bob has no Superpowers plugin; if you use those skills, copy
  them into `.bob/skills/` (project) or `~/.bob/skills/` (global) like any other Bob skill.

Set up both pieces — the conventions and the skill — then test it.

1. **Add the conventions.** Copy [`AGENTS.md`](AGENTS.md) to the root of your Quarkus +
   LangChain4j project. Bob automatically applies `AGENTS.md` to new conversations. If you already
   added `AGENTS.md` for Codex, the same file serves Bob — there is no separate `BOB.md`.

2. **Install the skill.** Bob has no plugin marketplace; skills are files under `.bob/skills/`. Run
   the helper from this repository:
   ```
   ./scripts/install-bob-skill.sh                 # into <cwd>/.bob/skills/
   ./scripts/install-bob-skill.sh /path/to/project  # into that project's .bob/skills/
   ./scripts/install-bob-skill.sh --global         # into ~/.bob/skills/
   ```
   Or copy `skills/quarkus-langchain4j-scaffolding/` into
   `.bob/skills/quarkus-langchain4j-scaffolding/` yourself. Bob asks for approval before activating
   a skill the first time.

3. **Try it.** Open your project in Bob and use a trigger phrase such as
   *"scaffold a new Quarkus + LangChain4j project"*, *"create a new AI service"*,
   *"scaffold a new agent"*, or *"set up a new RAG pipeline"*. The skill produces the layout and
   starter files; `AGENTS.md` governs the conventions of the code that follows.


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
  OpenAPI, WebSockets Next for streaming, the `-parameters` flag, a dual JVM/native build, and
  turning off Dev Services when a real model endpoint is configured.
- **§4 LangChain4j conventions.** Declarative `@RegisterAiService` over manual wiring, declarative
  **agentic** composition for multi-agent workflows, typed structured output, named/right-sized
  models, a streaming pattern that keeps reactive types at the edge, and **Easy RAG first**.
- **§5 Testing.** A minimal intended baseline (`@QuarkusTest` + REST-assured + native ITs),
  flagged as a target rather than an observed standard.
- **§6 Scope and overrides.** States that per-project deviations are allowed when documented
  inline — the conventions guide, they do not imprison.

## What the skill does and how it composes with the conventions

The `quarkus-langchain4j-scaffolding` skill handles the *"create something new"* moments:
new project, AI service, agent/workflow, or RAG component. It provides a project layout, a
dependency baseline, an `application.properties` baseline, and starter classes via the files in
`templates/`.

The split is deliberate and non-overlapping:

- **The skill is procedural** — it tells the agent (Claude, Codex, or Bob) *how to lay things out
  and get them running*, and it points at the Quarkus Agents MCP to actually create and run the
  project.
- **`CLAUDE.md` / `AGENTS.md` are declarative** — they state the conventions the resulting code
  must follow (`CLAUDE.md` for Claude, `AGENTS.md` for Codex and Bob).

The skill explicitly defers to the always-on convention file for the active agent and does not
restate those conventions, so there is a single source of truth per agent: scaffolding in the
skill, rules in `CLAUDE.md` or `AGENTS.md`.

For Codex distribution, `.agents/plugins/marketplace.json` points to `plugins/quarkus-agentic/`.
That directory is only a lightweight wrapper with symlinks back to `.codex-plugin/` and `skills/`,
so the Claude and Codex packages share the same skill content. Bob does not use a marketplace; its
skill is installed straight into `.bob/skills/` by `scripts/install-bob-skill.sh`.

## Advanced — personal use (optional global install)

A power user who works *exclusively* in this stack can apply the conventions globally instead of
copying the file into each project:

- **Claude** — move the contents of `CLAUDE.md` into the global `~/.claude/CLAUDE.md`.
- **Codex** — move the contents of `AGENTS.md` into `~/.codex/AGENTS.md`.
- **Bob** — Bob has no global conventions file, but it loads global *rules* from `~/.bob/rules/`;
  drop the conventions there (for example `~/.bob/rules/quarkus-langchain4j.md`). Install the skill
  globally with `./scripts/install-bob-skill.sh --global` (into `~/.bob/skills/`), and put shared
  MCP servers in `~/.bob/mcp_settings.json`.

**Trade-off (stated explicitly):** the global files apply to **all** work on your machine or
agent profile. If you also work in other stacks (other languages, frameworks, or non-AI Java
projects), these Quarkus/LangChain4j-specific rules will bleed into unrelated work. For anyone who
mixes stacks, the per-project drop-in is recommended over the global install.

**Precedence and reverting.** A project-root convention file is read *in addition to* a global
one, and project guidance can override broader global rules. To undo a global install, delete the
global file (or remove just the Quarkus/LangChain4j section you pasted into it).

## Versioning and changelog

This artifact uses semantic versioning. The current version is **0.8.0**; `CLAUDE.md`,
`AGENTS.md`, `SKILL.md`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, and this
`README.md` each carry a matching version header. See [`CHANGELOG.md`](CHANGELOG.md) for release
history.

## License

Licensed under the **Apache License 2.0**. See [`LICENSE`](LICENSE) for the full text.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to propose changes to the conventions, the skill,
and the templates — including how to keep new patterns evidence-backed, and how to confirm the
templates still build (see [`docs/VALIDATING-TEMPLATES.md`](docs/VALIDATING-TEMPLATES.md)).
