# Quarkus + LangChain4j + AI Stack
# Version: 0.20.1

## What this repository is

A small, opinionated, distribution-ready artifact for building AI and agent applications on the
Java stack of **Quarkus + LangChain4j**. It pairs drop-in always-on coding conventions
(`CLAUDE.md` for Claude, `AGENTS.md` for Codex and Bob) with three skills that set up the
prerequisites, scaffold new projects and components, and audit existing projects — all from
working templates. The conventions and templates reflect real-world Quarkus + LangChain4j
practice and a baseline of modern Java, so the guidance captures how these systems are actually
built rather than generic boilerplate.

## Quick install — any skills-capable agent

[![Skills](https://www.skills.sh/b/eldermoraes/quarkus-agentic-scaffolding)](https://www.skills.sh/eldermoraes/quarkus-agentic-scaffolding)

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

*Manual fallback,* if you would rather wire it by hand: register the Quarkus Agents MCP with the
pinned command
`claude mcp add -s user quarkus-agent -- jbang --java 21+ io.quarkus:quarkus-agent-mcp:1.2.5:runner`;
add context7 with `claude mcp add -s user context7 -- npx -y @upstash/context7-mcp@4.0.3` (for higher rate limits
`export CONTEXT7_API_KEY=…` in your shell — the server picks it up from the environment, so no key
belongs on the command line); optionally install superpowers with
`/plugin marketplace add obra/superpowers-marketplace` then
`/plugin install superpowers@superpowers-marketplace`; and copy [`CLAUDE.md`](CLAUDE.md) into your
project root yourself (Claude only auto-loads it from a project root or `~/.claude/`, so no plugin
can ship it for you).

Quarkus also ships the server as a Claude plugin — `/plugin marketplace add
quarkusio/quarkus-agent-mcp` then `/plugin install quarkus-agent@quarkus-tools`. Two things to know
before you pick that route over the command above. It launches `jbang quarkus-agent-mcp@quarkusio`,
and that alias resolves `io.quarkus:quarkus-agent-mcp:RELEASE:runner`, so what runs is whatever was
newest when the server started — two machines set up a week apart run different code. And it passes
no `--java`: the alias *does* declare `java-version: 21+`, but JBang 0.125.x ignores that for a GAV
script-ref, so the server runs on JBang's default JDK 17 and dies with `UnsupportedClassVersionError`
unless whatever launched it happens to export a JDK 21+ `JAVA_HOME`. Use one route or the other, not
both — the plugin's server and a `claude mcp add` entry are both named `quarkus-agent`, so uninstall
the plugin (`/plugin uninstall quarkus-agent@quarkus-tools`) before registering by hand.

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

*Manual fallback:* add the Quarkus Agents MCP with `codex mcp add quarkus-agent -- jbang --java 21+ io.quarkus:quarkus-agent-mcp:1.2.5:runner`;
add context7 with `codex mcp add context7 -- npx -y @upstash/context7-mcp@4.0.3` (for higher rate limits
`export CONTEXT7_API_KEY=…` in your shell — the server picks it up from the environment, so no key
belongs on the command line); install/enable the Superpowers plugin if you use it; and copy
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
registers the **Quarkus Agents MCP** and **context7** MCP servers for Bob, and drops `AGENTS.md`
into your project root. If you already added `AGENTS.md` for Codex, the same file serves Bob — there
is no separate `BOB.md`.

*Manual fallback:* register both servers with Bob's own CLI (Bob 2.0.0), which writes the file Bob
actually reads:

```
bob mcp add -s global quarkus-agent jbang -- --java 21+ io.quarkus:quarkus-agent-mcp:1.2.5:runner
bob mcp add -s global context7 npx -- -y @upstash/context7-mcp@4.0.3
bob mcp list
```

The `--` is required: without it Bob parses `--java` as one of its own options and exits with
`error: unknown option '--java'`. The `-s global` above is deliberate: Bob's own default is
`-s workspace`, so dropping the flag does not mean "no scope" — it registers in the current project,
and at that scope the file must already exist or the command dies with `ENOENT … .bob/mcp.json`.
Seed it **only if it is missing** — `>` truncates, and an existing file holds registrations worth
keeping:

```
[ -f .bob/mcp.json ] || { mkdir -p .bob && printf '{"mcpServers":{}}\n' > .bob/mcp.json; }
```

At global scope Bob creates the file and its directory for you. On a name that is already registered, `add` refuses
(`Error: MCP server "quarkus-agent" already exists`) — to *replace* a stale entry use
`bob mcp add-json -s global quarkus-agent '{"command":"jbang","args":["--java","21+","io.quarkus:quarkus-agent-mcp:1.2.5:runner"]}'`,
which overwrites in place. Read what `bob mcp list` prints, not just the name: an entry from an older
setup shows its own command (an unpinned `jbang quarkus-agent-mcp@quarkusio`, say) and is exactly the
case `add-json` is for.

To write the JSON by hand instead, the global file is `~/.bob/settings/mcp.json` and the project
file is `<project>/.bob/mcp.json` (a same-named server at project scope overrides global). Older
Bob docs name `mcp_settings.json` in that same settings directory; Bob 2.0.0 treats it as legacy and
migrates it **only when `mcp.json` does not yet exist**, so on a machine that already has `mcp.json`
anything written to the legacy name is silently ignored. That cuts both ways, so **look before you
register**: if `~/.bob/settings/mcp_settings.json` exists and `mcp.json` does not, start Bob once and
let it migrate (it says so — *"your global MCP configuration has been migrated to mcp.json"*) before
running any `bob mcp add`. Adding first creates `mcp.json` yourself, and the migration then never
runs — your old servers stay in the legacy file, unread. If you set Bob up with a version of this
guide before v0.18.0, also look for `~/.bob/mcp.json` and `~/.bob/mcp_settings.json` — one directory
above `settings/`, which is where we used to point you; Bob reads neither, so a registration sitting
there has never loaded. Contents either way:

```json
{
  "mcpServers": {
    "quarkus-agent": { "command": "jbang", "args": ["--java", "21+", "io.quarkus:quarkus-agent-mcp:1.2.5:runner"] },
    "context7":      { "command": "npx",   "args": ["-y", "@upstash/context7-mcp@4.0.3"] }
  }
}
```

(`jbang` must be on the PATH of whatever *starts* Bob — install it with a package manager, e.g.
`sdk install jbang` or `brew install jbang`. A GUI-launched client gets a minimal PATH that contains
none of the usual install locations, so if the server fails with `spawn jbang ENOENT`, put the
absolute path from `command -v jbang` in `command` and keep the args as they are. `--java 21+` is not
optional: the MCP server is compiled for Java 21, and JBang
resolves its own JDK — it falls back to its default, currently 17, whenever the process that spawned
it hands over no `JAVA_HOME`, which is exactly what Bob and other GUI-launched clients do. For higher
rate limits `export CONTEXT7_API_KEY=…` in your environment rather than writing a literal key into
the file; the server reads it from there.) If the skills CLI is
unavailable, the repository's fallback helper installs all three
skills into `.bob/skills/` for you:

```
# Pick one — the three forms are alternatives, not a sequence; uncomment the one you want
./scripts/install-bob-skill.sh                     # into <cwd>/.bob/skills/
# ./scripts/install-bob-skill.sh /path/to/project  # into that project's .bob/skills/
# ./scripts/install-bob-skill.sh --global          # into ~/.bob/skills/
```

Bob asks for approval before activating a skill — once per conversation, not once ever; the setting
is a single global toggle rather than a per-skill grant. Two things to know while you are here: a
skill's `description` front-matter field is load-bearing (Bob ignores a skill without one), and
skills are only available in Bob's **Advanced** mode.

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
  confirm, by handing off to `scaffold-project`'s component sections. Platform upgrades (an EOL
  Quarkus line, an unsupported Java release, pre-BOM LangChain4j) have no such handoff: they stay
  your own step.

The split between skill and conventions is deliberate and non-overlapping:

- **The skills are procedural** — they tell the agent (Claude, Codex, or Bob) *how to set up,
  lay things out, and get them running*, and point at the Quarkus Agents MCP to actually create
  and run the project.
- **`CLAUDE.md` / `AGENTS.md` are declarative** — they state the conventions the resulting code
  must follow (`CLAUDE.md` for Claude, `AGENTS.md` for Codex and Bob).

For Codex distribution, `.agents/plugins/marketplace.json` points to `plugins/quarkus-agentic-scaffolding/`.
That directory is only a lightweight wrapper with symlinks back to `.codex-plugin/` and `skills/`,
so the Claude and Codex packages share the same skill content. Bob has a marketplace, but it
distributes modes and MCP servers rather than skills (and is IBM-internal), so there is no
marketplace channel for skills: Bob's are installed by the skills CLI (or
`scripts/install-bob-skill.sh`) into `.bob/skills/`.

## Advanced — personal use (optional global install)

A power user who works *exclusively* in this stack can apply the conventions globally instead of
copying the file into each project:

- **Claude** — move the contents of `CLAUDE.md` into the global `~/.claude/CLAUDE.md`.
- **Codex** — move the contents of `AGENTS.md` into `~/.codex/AGENTS.md`.
- **Bob** — move the contents of `AGENTS.md` into `~/.bob/AGENTS.md`, Bob's documented global
  context file. (Bob also loads global *rules* from `~/.bob/rules/`, so
  `~/.bob/rules/quarkus-langchain4j.md` works too if you would rather keep them separate from your
  general context.) Install the skills globally with `./scripts/install-bob-skill.sh --global`
  (into `~/.bob/skills/`), and add the shared MCP servers with the `bob mcp add -s global` commands
  from [How to use with Bob](#how-to-use-with-bob) — not by hand in the **MCP** tab, which is how a
  registration ends up without the `--java 21+` pin.

**Trade-off (stated explicitly):** the global files apply to **all** work on your machine or
agent profile. If you also work in other stacks (other languages, frameworks, or non-AI Java
projects), these Quarkus/LangChain4j-specific rules will bleed into unrelated work. For anyone who
mixes stacks, the per-project drop-in is recommended over the global install.

**Precedence.** A project-root convention file is read *in addition to* a global one, and project
guidance can override broader global rules. To undo a global install, see
[Uninstall](#uninstall) — the same managed-block procedure applies to `~/.claude/CLAUDE.md`,
`~/.codex/AGENTS.md`, and `~/.bob/AGENTS.md` or `~/.bob/rules/<your-file>.md`.

## Uninstall

Removes **this artifact only**. Everything it helped you set up is shared with the rest of your
work and stays: **JDK 25 / GraalVM**, **JBang**, your container runtime, the **Quarkus Agents MCP**
and **context7** MCP servers, `superpowers`, and every project `/scaffold-project` generated. No
step below touches them — that is deliberate. If you also want the two MCP servers gone, remove
them with your agent's own MCP commands; nothing here does it for you.

| Removed | Where it lives |
|---|---|
| The three skills, per agent | `.claude/skills/`, `.agents/skills/`, `.bob/skills/`, … project and global |
| Plugin + marketplace (Claude) | `quarkus-agentic-scaffolding@eldermoraes` |
| Plugin + marketplace (Codex) | `quarkus-agentic-scaffolding@eldermoraes` |
| Extension (Gemini CLI) | `quarkus-agentic-scaffolding` |
| The managed conventions block | `CLAUDE.md` / `AGENTS.md` in your project root |
| The global conventions, if you did the [Advanced](#advanced--personal-use-optional-global-install) install | `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `~/.bob/AGENTS.md` or `~/.bob/rules/<your-file>.md` |

The MCP config files `/setup-agentic-scaffolding` may have written are **kept**: `.cursor/mcp.json`,
`opencode.json`, and Bob's `.bob/mcp.json` (project) or `~/.bob/settings/mcp.json` (global).
Deleting them would remove exactly what this boundary protects — and for the two Bob files that is
not even the whole story: `bob mcp add` merges into whatever is already there, so a global
`~/.bob/settings/mcp.json` typically holds servers that have nothing to do with this artifact
(possibly with credentials in them). If you do want our two servers gone, remove them **by entry**,
never by file: `bob mcp remove -s global quarkus-agent` and `bob mcp remove -s global context7`
(`-s workspace` for a project file), then `bob mcp list` to confirm what remains.

### 1. The skills

Use the path you installed with — or all of them, if you are not sure. Every command here is
safe to run when nothing is installed.

**Skills CLI** (the [Quick install](#quick-install--any-skills-capable-agent)) — name the three
skills:

```
npx skills remove setup-agentic-scaffolding scaffold-project audit-project -y
npx skills remove -g setup-agentic-scaffolding scaffold-project audit-project -y
npx skills list
npx skills list -g
```

The first line covers the current project, the second your global install. Removal deletes real
files, not just symlinks. Omitting `-a/--agents` is intentional: the CLI then cleans the skills out
of *every* agent it knows about, including ghost symlinks left by an agent it no longer detects.

> **Do not use `--all` here.** It removes **every** skill from your agents, including skills that
> have nothing to do with this repository — and, contrary to its own `--help`, it does not imply
> `-y`. Name the three skills.

**Claude Code** — uninstall the plugin, then drop the marketplace:

```
/plugin uninstall quarkus-agentic-scaffolding@eldermoraes
/plugin marketplace remove eldermoraes
/reload-plugins
```

> Removing a marketplace in Claude Code **uninstalls every plugin installed from it** and deletes
> its cached clone. That is harmless here — this marketplace ships one plugin — but if you added
> other plugins from `eldermoraes`, they go with it.

Verify with `claude plugin list`. Your MCP servers live in `~/.claude.json` under `mcpServers`,
which is untouched by any of this.

**Codex** — remove the plugin **first**, then the marketplace:

```
codex plugin remove quarkus-agentic-scaffolding@eldermoraes
codex plugin marketplace remove eldermoraes
codex plugin list
```

> Codex behaves the opposite way from Claude: removing the marketplace does **not** uninstall
> anything. It drops `[marketplaces.eldermoraes]` from `~/.codex/config.toml` and deletes the
> Codex-managed marketplace directory, which leaves any other plugin from that marketplace
> **orphaned** — its cache and config survive, its source does not. Remove the plugins first.

`codex plugin remove` has no `rm` or `uninstall` alias, and marketplace removal is CLI-only (there
is no `/plugins` equivalent). Your MCP servers stay in `[mcp_servers.*]` in `config.toml`.

**Bob** — Bob has no command for this: a skill is a directory it scans for, so removing the
directory is the whole uninstall.

```
# Pick one — the three forms are alternatives, not a sequence; uncomment the one you want
./scripts/uninstall-bob-skill.sh                     # from <cwd>/.bob/skills/
# ./scripts/uninstall-bob-skill.sh /path/to/project  # from that project's .bob/skills/
# ./scripts/uninstall-bob-skill.sh --global          # from ~/.bob/skills/
ls .bob/skills/                                      # verify; and: ls ~/.bob/skills/
```

Nothing named `setup-agentic-scaffolding`, `scaffold-project`, or `audit-project` should be left in
that listing — a directory Bob does not see is a skill Bob does not load. `ls` answering `No such
file or directory` is a pass too: it means this project never had a local `.bob/skills/`, which is
exactly what you should see if you only ever installed with `--global`.

It removes only the three skills it installed, and only after reading each `SKILL.md`'s front-matter
`name`: a directory that declares a different name — or declares none, or has no `SKILL.md` at all —
is skipped with a warning rather than deleted. What the check cannot do is tell two identical
declarations apart, so a skill of your own that *also* declares `name: audit-project` is
indistinguishable from ours and **will** be removed. Move it aside before you run this. A symlinked
skill is unlinked, not recursed into. Your MCP registration (`.bob/mcp.json` in a project,
`~/.bob/settings/mcp.json` globally), `.bob/rules/`, and every other skill in `.bob/skills/` are
left alone. Re-running it is a clean no-op. Skills load once per conversation, so
**start a new conversation** in Bob afterwards.

**Gemini CLI** — if you installed the extension, uninstalling it takes the two MCP servers it
declares with it, so add them back at user scope:

```
gemini extensions uninstall quarkus-agentic-scaffolding
gemini mcp add -s user quarkus-agent jbang --java 21+ io.quarkus:quarkus-agent-mcp:1.2.5:runner
gemini mcp add -s user context7 npx -y @upstash/context7-mcp@4.0.3
gemini extensions list
gemini mcp list
```

Order matters — uninstall first, then re-add. A `settings.json` registration takes precedence over
an extension-declared server of the same name, so re-adding *before* uninstalling would silently
shadow the extension's pinned versions. `gemini mcp add` defaults to `--scope project`, hence
`-s user`. In `gemini mcp list`, an entry labelled `(from quarkus-agentic-scaffolding)` is still
coming from the extension; after a successful uninstall and re-add, both servers appear without
that label. Restart the session.

### 2. The conventions file

The file in your project root is **yours**. `/setup-agentic-scaffolding` only owns the region
between its two markers:

```text
<!-- BEGIN quarkus-agentic-scaffolding conventions … -->
…
<!-- END quarkus-agentic-scaffolding conventions -->
```

Removing that region is the uninstall. Deleting the file is optional, and only safe when nothing
else is in it. Run these from your project root, on `CLAUDE.md` (Claude) or `AGENTS.md` (Codex,
Bob, Gemini, Cursor, opencode). For the [Advanced](#advanced--personal-use-optional-global-install)
install, substitute the global path — `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, or
`~/.bob/AGENTS.md` (or `~/.bob/rules/<your-file>.md`, if you used a rules file instead).

**Run these one fence at a time, and do not paste the section as a whole.** Each of the five steps
below is conditional on what the step before it printed, so a single paste would run the removal
without you having read the precheck, and then hand the original file straight back.

Steps 1 and 2 are the safe pair — a copy and a report, neither of which changes `CLAUDE.md`:

```bash
# 1. Back up, without clobbering an existing .bak
cp CLAUDE.md "CLAUDE.md.backup-$(date +%Y%m%d-%H%M%S)"

# 2. Precheck — proceed ONLY on OK-SAFE-TO-REMOVE
awk '/^<!-- BEGIN quarkus-agentic-scaffolding conventions/{b++;bl=NR}
     /^<!-- END quarkus-agentic-scaffolding conventions/{e++;el=NR}
     END{printf "BEGIN=%d END=%d beginLine=%d endLine=%d -> %s\n", b,e,bl,el,
         (b==1 && e==1 && bl<el) ? "OK-SAFE-TO-REMOVE" : "REFUSE - remove the block by hand"}' CLAUDE.md
```

Read that line before going on. Run step 3 **only** if it printed `OK-SAFE-TO-REMOVE`; on `REFUSE`,
stop here and edit the file by hand.

```bash
# 3. Remove — changes nothing unless a complete, in-order pair exists
perl -i -0777 -pe 's/^<!-- BEGIN quarkus-agentic-scaffolding conventions.*?^<!-- END quarkus-agentic-scaffolding conventions -->[ \t]*\r?\n?//msg' CLAUDE.md
```

Now compare what is left against the backup:

```bash
# 4. Inspect what the removal changed
diff "$(ls -t CLAUDE.md.backup-* | head -1)" CLAUDE.md
```

Deleting the file itself is optional, and the line below does it only if no content is left. Run it
**only** once the diff has shown you that nothing of yours was inside the deleted region and that
nothing but whitespace remains:

```bash
# 4b. Drop the file itself only if nothing but whitespace is left
grep -q '[^[:space:]]' CLAUDE.md || rm CLAUDE.md
```

**Read the diff before you trust it.** A large deletion is the expected result, so its size tells
you nothing about whether it went right. What you are checking for is *your own writing* in the
deleted lines. If you see any, step 5 is the recovery — it puts the original file back verbatim,
managed block included, and you then remove the block by hand:

```bash
# 5. Restore, if the diff shows anything you wrote
cp "$(ls -t CLAUDE.md.backup-* | head -1)" CLAUDE.md
```

**Keep the backup** until you have restarted your agent and confirmed it still behaves. There is
deliberately no `rm` step for it.

**On `REFUSE`, do not run step 3** — edit the file by hand instead. `REFUSE` means the markers are
missing, duplicated, out of order, or on the same line, and no automated edit can tell a real block
from a passage where you wrote *about* the markers. Step 3 is built to change nothing in that case,
but the point of the precheck is that you never find out the hard way. The reverse does not hold:
`OK-SAFE-TO-REMOVE` says a marker pair exists *in order*, not that the pair is genuine — a marker
quoted at column 0, say inside a fenced code block where you documented your own agent setup, counts
as real to both commands, and step 3 then takes everything between it and its partner. That is why
step 1's backup is not optional and why the diff has to be read.

Two more things worth knowing:

- **If `CLAUDE.md` is a symlink,** in-place editing replaces it with a regular file and breaks the
  link. Edit the target instead.
- **`CLAUDE.md` is often not in git.** Do not count on `git checkout` to undo this — that is what
  the backup in step 1 is for.

Step 4 uses `grep -q '[^[:space:]]'` rather than a size test on purpose: a file containing only the
block reduces to exactly 0 bytes, but a block with a blank line on each side leaves a 2-byte
whitespace-only file. Interior blank lines double up after removal; that is cosmetic, and yours to
tidy.

### 3. Verify

```bash
npx skills list          # and: npx skills list -g
claude plugin list
codex plugin list
gemini extensions list
gemini mcp list
grep -rIn 'quarkus-agentic-scaffolding' . --exclude-dir=.git
```

None of the first five should mention `quarkus-agentic-scaffolding`, and `gemini mcp list` should
show `quarkus-agent` and `context7` **without** a `(from …)` label. The `grep` should return
nothing but your own backups. Restart your agent — most of them read skills, plugins, and
instruction files once at startup.

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
│   ├── install-bob-skill.sh    # Fallback: copy the skills into a project's (or global) .bob/skills/
│   └── uninstall-bob-skill.sh  # The mirror: remove them again (see Uninstall)
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
