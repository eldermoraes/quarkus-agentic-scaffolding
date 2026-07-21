---
name: setup-agentic-scaffolding
description: Set up the prerequisites for the Quarkus + LangChain4j agentic stack in the coding agent you are running — detect and (with approval) install the toolchain, register the Quarkus Agents MCP and context7 MCP servers, and write the conventions file into your project. User-invoked only, via /setup-agentic-scaffolding; it prepares the environment the /scaffold-project and /audit-project skills depend on.
disable-model-invocation: true
---

# Setup Agentic Scaffolding
# Version: 0.12.0

## 1. When to use this skill

Run this skill **once per machine** and **revisit once per project** to configure the prerequisites
for the Quarkus + LangChain4j agentic stack — before scaffolding or auditing any project. It is the
entry point of the flow:

- **Phase A — toolchain (machine-level):** JDK 25+/GraalVM, JBang, a container runtime, Maven or the
  Quarkus CLI.
- **Phase B — MCP registration (per agent):** the **Quarkus Agents MCP** and **context7**, wired
  through the mechanism of whichever agent is running.
- **Phase C — conventions (project-level):** the always-on conventions file (`CLAUDE.md` or
  `AGENTS.md`) copied into the user's project root.

This skill is **user-invoked only** (`disable-model-invocation: true`); it never triggers itself
from a task description.

## 2. Bootstrap license (read first)

The project conventions (`CLAUDE.md` / `AGENTS.md` §1) make the Quarkus Agents MCP mandatory for
every Quarkus task and tell the agent to **stop** if required tooling is missing. **That rule does
not apply to this skill.** Installing that tooling is precisely this skill's job, so it legitimately
operates **before and without** the Quarkus Agents MCP and context7. Do not stop or defer to the
MCP here — proceed with Phases A–C and register the MCP as part of the work.

## 3. How this skill works (process)

Every phase follows the same house pattern — never act blind, never clobber:

1. **Explore.** Detect current state with read-only probes (`command -v`, `mcp list`, file checks).
2. **Present findings, recommendation first.** Lead with the recommended action, then the evidence
   ("already installed vs missing"). Never claim something is installed without a probe backing it.
3. **Confirm.** Get explicit user approval before any install, registration, or file write.
4. **Write / Execute, then verify.** Run the step, then re-probe to prove it worked — never declare
   success from the command's exit alone.

The three phases are **idempotent**: re-running skips what is already done and only fills gaps. If a
step needs a restart to take effect (Phase B), the re-run **is** the verification pass.

## 4. Phase A — toolchain (machine-level)

The Quarkus Agents MCP needs Java 21+ to run (this stack targets Java 25+), plus a way to build and
run Quarkus: JBang (how the MCP itself launches), a container runtime for Dev Services, and Maven or
the Quarkus CLI. **Explore** each with a read-only probe, then **present** a status table before
touching anything.

| Tool | Probe | Why it is needed | If missing (present, then confirm) |
|---|---|---|---|
| JDK 25+ / GraalVM | `java -version` | Language baseline (§2); GraalVM adds native builds | Install a JDK 25 (Temurin/GraalVM); recommend GraalVM for native |
| JBang | `jbang --version` | Launches `quarkus-agent-mcp@quarkusio` and the MCP server | Install JBang (`curl -Ls https://sh.jbang.dev \| bash` or a package manager) |
| Container runtime | `docker version` / `podman version` | Quarkus Dev Services (model containers, stores) | Install Docker Desktop or Podman |
| Maven / Quarkus CLI | `mvn -version` / `quarkus --version` | Build tool (the generated project ships `mvnw`, so this is optional) | Optional — recommend the Quarkus CLI only if the user wants it |

Rules for Phase A:

- **Report "already installed vs missing" honestly.** Show the probe output; never fabricate a
  version or a success.
- **Install only what the user approves**, one tool at a time, and **re-probe** after each install
  to confirm.
- If a required tool cannot be installed in this environment, **stop and report it** rather than
  faking readiness — the downstream MCP work will fail without it.

## 5. Phase B — MCP registration (per agent)

Register two MCP servers through the running agent's own mechanism:

- **quarkus-agent** — command `jbang`, args `quarkus-agent-mcp@quarkusio`
- **context7** — command `npx`, args `-y @upstash/context7-mcp` (append `--api-key <KEY>` for higher
  rate limits)

**First detect which agent is running** (Claude Code, Codex CLI, Gemini CLI, Cursor, GitHub Copilot
CLI, opencode, or Bob), then use its row below. **Present the exact commands, confirm, execute, then
verify** with the listed check — never assume registration succeeded.

| Agent | Register quarkus-agent + context7 | Verify | Live this session? |
|---|---|---|---|
| Claude Code | `claude mcp add -s user quarkus-agent -- jbang quarkus-agent-mcp@quarkusio` · `claude mcp add -s user context7 -- npx -y @upstash/context7-mcp` | `claude mcp list` | No — restart |
| Codex CLI | `codex mcp add quarkus-agent -- jbang quarkus-agent-mcp@quarkusio` · `codex mcp add context7 -- npx -y @upstash/context7-mcp` | `codex mcp list` | No — restart; sandbox may block network |
| Gemini CLI | `gemini mcp add quarkus-agent jbang quarkus-agent-mcp@quarkusio` · `gemini mcp add context7 npx -y @upstash/context7-mcp` — **or** install this repo's Gemini extension, which already declares both servers | `gemini mcp list` | No — restart |
| Cursor | Write `.cursor/mcp.json` with both servers (`mcpServers` map, same command/args) | Settings → MCP shows both; user **toggles them on** | GUI enable |
| GitHub Copilot CLI | `copilot mcp add quarkus-agent -- jbang quarkus-agent-mcp@quarkusio` · `copilot mcp add context7 -- npx -y @upstash/context7-mcp` | `copilot mcp list` | **Yes** — live immediately |
| opencode | Write `opencode.json` `mcp` key with both servers | `/mcp` in session | **Yes** — hot reload |
| Bob (D3) | Write `.bob/mcp.json` (project) or `~/.bob/mcp_settings.json` (global) with both servers | MCP tab in the Bob UI lists both | Reload in UI |

The `.cursor/mcp.json`, `opencode.json`, and `.bob/mcp.json` map has the same shape everywhere:

```json
{
  "mcpServers": {
    "quarkus-agent": { "command": "jbang", "args": ["quarkus-agent-mcp@quarkusio"] },
    "context7":      { "command": "npx",   "args": ["-y", "@upstash/context7-mcp"] }
  }
}
```

(opencode uses the top-level `mcp` key rather than `mcpServers`; keep the two server entries the
same. `jbang` must be on PATH — that is Phase A's job.)

### 5.1 Restart handoff

In **Claude Code, Codex CLI, and Gemini CLI** a newly registered MCP server only loads on the **next
session**. After registering and verifying it appears in the `mcp list` output, end with this
explicit handoff:

> Registration is written but the MCP loads next session. **Restart your agent, then re-run
> `/setup-agentic-scaffolding`.** The re-run is idempotent — it will skip everything already done and
> confirm the Quarkus Agents MCP and context7 are now live. That re-run **is** the verification pass.

**Cursor** needs a one-time GUI toggle (Settings → MCP). **Copilot CLI** and **opencode** pick the
servers up immediately (opencode hot-reloads), so no restart is required for those two.

## 6. Superpowers (detect and guide — never auto-install)

`superpowers` skills are used wherever applicable in this stack, but they are a **third-party
plugin** — this skill **detects** them and **presents install commands for the user to run**; it
**never auto-installs** them (decision D2).

- **Detect:** check whether superpowers skills are already available to the running agent.
- **If absent, present** the install path (the user runs it), e.g. for Claude Code:

  ```text
  /plugin marketplace add obra/superpowers-marketplace
  /plugin install superpowers@superpowers-marketplace
  ```

  For other agents, point the user at the superpowers marketplace for their agent. Do not run these
  for the user.

## 7. Phase C — conventions (project-level)

Copy the always-on conventions file into the **user's project root**, under the name the running
agent reads:

| Agent | Conventions file in project root | Seed template (inside this skill) |
|---|---|---|
| Claude Code | `CLAUDE.md` | `templates/conventions-CLAUDE.md` |
| Codex CLI, GitHub Copilot CLI, opencode, Bob | `AGENTS.md` | `templates/conventions-AGENTS.md` |
| Gemini CLI | `AGENTS.md` (this repo's Gemini extension sets `contextFileName: AGENTS.md`) | `templates/conventions-AGENTS.md` |
| Cursor | `AGENTS.md` (fallback the agent reads) | `templates/conventions-AGENTS.md` |

The seed templates `templates/conventions-CLAUDE.md` and `templates/conventions-AGENTS.md` are
**byte-for-byte mirrors of this repository's root `CLAUDE.md` and `AGENTS.md`**. They ship inside the
skill folder so a skills-CLI install (`npx skills add …`, which copies only the skill folder) can
still deliver them.

Rules for Phase C:

- **No file present:** copy the right template to the project root under the right name. Confirm the
  path first.
- **A conventions file already exists:** **do not clobber it.** Present a draft merge (the stack's
  §1–§6 sections added or updated), keep every line of the user's own content, and **edit in place**
  after the user approves the draft.
- If both `CLAUDE.md` and `AGENTS.md` could apply, write the one for the **running agent**; do not
  create the second when the first is present.

## 8. Where the flow goes next

Setup is done once Phases A–C verify green. Continue with:

- **`/scaffold-project`** — create a new Quarkus + LangChain4j project (or add an AI service, agent,
  RAG, MCP client/server component to an existing one).
- **`/audit-project`** — check an existing project against the stack conventions, or run a gap
  analysis on a plain Quarkus project adopting the stack.

Both skills open assuming these prerequisites are configured — if they are not, they point back here.

## 9. Invocation forms

This skill is reachable under two slash names depending on how it was installed:

- **Skills-CLI install** (`npx skills add …`): bare — `/setup-agentic-scaffolding`.
- **Plugin install** (Claude Code marketplace): namespaced by the plugin id —
  `/quarkus-agentic-scaffolding:setup-agentic-scaffolding`.

Both invoke the same skill; plugin users who do not see the bare name should use the namespaced form.
