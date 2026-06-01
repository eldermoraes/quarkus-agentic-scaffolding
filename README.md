# Quarkus + LangChain4j + AI Stack
# Version: 0.2.0

## What this repository is

A small, opinionated, distribution-ready artifact for building AI and agent applications on the
Java stack of **Quarkus + LangChain4j**. It pairs a drop-in `CLAUDE.md` of always-on coding
conventions with a Claude skill that scaffolds new projects, AI services, agents, and RAG
pipelines from working templates. The conventions and templates reflect real-world Quarkus +
LangChain4j practice and a baseline of modern Java, so the guidance captures how these systems are
actually built rather than generic boilerplate.

## What's inside

```
.
├── README.md                 # This file
├── CLAUDE.md                 # Always-on project conventions (drop into your project root)
├── CONTRIBUTING.md           # How to propose changes
├── CHANGELOG.md              # Release history
├── LICENSE                   # Apache-2.0
├── .gitignore
├── .claude-plugin/           # Installable-plugin + marketplace manifests
│   ├── plugin.json
│   └── marketplace.json
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

## How to use

**Prerequisites (required).** This stack depends on two MCP tools that must be available in your
Claude environment — they are mandatory, not optional (see `CLAUDE.md` §1):

- **Quarkus Agents MCP** — all Quarkus work goes through it. Install the official plugin:
  ```
  /plugin marketplace add quarkusio/quarkus-agent-mcp
  /plugin install quarkus-agent@quarkus-tools
  ```
- **context7** — all library/framework documentation lookups go through it:
  ```
  claude mcp add context7 -- npx -y @upstash/context7-mcp
  ```
  (Append `--api-key <KEY>` for higher rate limits.)

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

## What's in `CLAUDE.md` and why

`CLAUDE.md` is intentionally short and always-on. Each section earns its place:

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

## What the skill does and how it composes with `CLAUDE.md`

The `quarkus-langchain4j-scaffolding` skill handles the *"create something new"* moments:
new project, AI service, agent/workflow, or RAG component. It provides a project layout, a
dependency baseline, an `application.properties` baseline, and starter classes via the files in
`templates/`.

The split is deliberate and non-overlapping:

- **The skill is procedural** — it tells Claude *how to lay things out and get them running*, and
  it points at the Quarkus Agents MCP to actually create and run the project.
- **`CLAUDE.md` is declarative** — it states the conventions the resulting code must follow.

The skill explicitly defers to `CLAUDE.md` for conventions and does not restate them, so there is
a single source of truth: scaffolding in the skill, rules in `CLAUDE.md`.

## Advanced — personal use (optional global install)

A power user who works *exclusively* in this stack can move the contents of `CLAUDE.md` into the
global `~/.claude/CLAUDE.md` so the conventions apply to every project without copying the file
each time.

**Trade-off (stated explicitly):** the global file applies to **all** Claude Code work on your
machine. If you also work in other stacks (other languages, frameworks, or non-AI Java projects),
these Quarkus/LangChain4j-specific rules will bleed into unrelated work. For anyone who mixes
stacks, the per-project drop-in is recommended over the global install.

**Precedence and reverting.** A project-root `CLAUDE.md` is read *in addition to* a global
`~/.claude/CLAUDE.md`, and the project file takes precedence where guidance conflicts — so a
project can always override the global rules. Use `/memory` in a session to see and edit which
files are active. To undo a global install, delete `~/.claude/CLAUDE.md` (or remove just the
Quarkus/LangChain4j section you pasted into it).

## Versioning and changelog

This artifact uses semantic versioning. The current version is **0.2.0**; `CLAUDE.md`, `SKILL.md`,
`.claude-plugin/plugin.json`, and this `README.md` each carry a matching version header. See
[`CHANGELOG.md`](CHANGELOG.md) for release history.

## License

Licensed under the **Apache License 2.0**. See [`LICENSE`](LICENSE) for the full text.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to propose changes to the conventions, the skill,
and the templates — including how to keep new patterns evidence-backed, and how to confirm the
templates still build (see [`docs/VALIDATING-TEMPLATES.md`](docs/VALIDATING-TEMPLATES.md)).
