# Skill-Flow Redesign Plan — Blindspot Audit, 2026-07-21

> Prioritized action plan from a blindspot deep dive with three parallel research tracks:
> (1) the skill-flow frontier across `mattpocock/skills`, `anthropics/skills`,
> `vercel-labs/agent-skills`, `obra/superpowers`, `chintanturakhia/onboarding-skills` and the
> skills.sh directory; (2) a per-agent capability map (Claude Code, Codex CLI, Gemini CLI,
> Cursor, GitHub Copilot CLI, opencode); (3) the Quarkus Agents MCP tool surface.
> Scope: restructure this repo from one umbrella skill into an explicit multi-skill flow —
> `setup-agentic-scaffolding` (prerequisites) + a project-creation skill + component
> scaffolding. Facts carry an as-of date of **2026-07-21** and rot at ecosystem speed.

## Target architecture

```text
/setup-agentic-scaffolding            user-invoked; run once per machine, revisit per project
      │  verifies toolchain (JDK 25/GraalVM, JBang) · registers Quarkus Agents MCP + context7
      │  · writes the conventions file into the user's project · verifies, never declares
      ▼
/scaffold-project                     hybrid (user- AND model-invoked) — the current
      │  quarkus-langchain4j-scaffolding RENAMED, keeping its full umbrella scope:
      │  · creation end-to-end: quarkus_create → git init/commit → quarkus_skills per
      │    extension → repo templates + package layout + deps → devui-testing_runTests
      │  · components on an existing project (§4–§10): AI service, tools, agents/
      │    workflows, RAG, MCP client/server, guardrails — auto-triggered by the model
      ▼
/audit-project                        user-invoked; EXISTING projects, two entry scenarios:
                                      (a) stack project → conformance report vs conventions;
                                      (b) plain Quarkus project adopting the stack → gap
                                      analysis, then hands off to setup Phase C + components
```

Each downstream skill opens with the canonical hard-dependency pointer
(*"prerequisites should already be configured — run `/setup-agentic-scaffolding` if not"*),
per the hard/soft dependency rule observed in `mattpocock/skills` ADR 0001.

## Design rules imported from the frontier

- **Invocation axis is the backbone.** Orchestrators (`setup`, `create`) ship
  `disable-model-invocation: true` (Claude) + `policy.allow_implicit_invocation: false` in
  `agents/openai.yaml` (Codex), with human-facing descriptions. The component skill stays
  model-invoked with rich triggers. A user-invoked skill may call model-invoked skills, never
  another user-invoked one.
- **Prompt-driven, not scripted:** Explore → Present findings leading with the recommended
  answer → Confirm a draft → Write. Never clobber user edits; update blocks in-place.
- **Idempotent phases + verification:** re-running skips what is already done ("already vs
  newly installed"); every install step ends with a real check (`claude mcp list`, tool
  probe), never a success claim. Persist progress state so the flow is resumable.
- **Skills reference each other in `/skill` prose**, never by file path across skill folders.
  Seed templates live inside the owning skill's folder.
- **One skill = one context window.** Keep the orchestrators thin; delegate. Documented
  deviation (D6): `scaffold-project` keeps the umbrella scope (creation + components) to
  minimize the number of skills the user faces; split it later only if it outgrows one
  context window — splitting is cheap, renaming is not.

## P0 — Design and authoring (blocks everything else)

### 1. Author `setup-agentic-scaffolding` *(high impact; the flow's entry point)* — ✅ done 2026-07-21

Phased, in the `onboarding-skills` mold:

- **Phase A — toolchain check (machine-level).** `command -v` for JDK/GraalVM 25, JBang,
  container runtime (the Quarkus MCP needs Java 21+, Docker/Podman, and Quarkus CLI or Maven
  or JBang). Report what is missing; install only what the user approves.
- **Phase B — MCP registration (per agent).** Detect the running agent, register
  `quarkus-agent` (`jbang quarkus-agent-mcp@quarkusio`) and `context7`
  (`npx -y @upstash/context7-mcp`) through that agent's mechanism (matrix below), then
  verify. **Restart handoff:** in Claude Code, Codex and Gemini CLI a newly registered MCP
  only loads next session — the skill must end with an explicit "restart, then re-run
  `/setup-agentic-scaffolding` to verify" step (idempotency makes the re-run cheap and turns
  it into the verification pass). Cursor needs a GUI enable; Copilot CLI and opencode are
  live immediately.
- **Phase C — conventions (project-level).** Copy the conventions file into the user's
  project root under the right name per agent (`CLAUDE.md` / `AGENTS.md` / `GEMINI.md` —
  see P1-6), seeded from templates inside the skill folder. Edit the existing file in-place
  when one exists; never create the second when the first is present.
- **Bootstrap license.** CLAUDE.md §1 mandates the Quarkus Agents MCP for all Quarkus work —
  but setup runs precisely when it is absent. The skill must state explicitly that it
  operates before/without the MCP (that is its job), so §1 does not deadlock it.

### 2. Rename the umbrella skill to `scaffold-project` *(high impact; decided 2026-07-21)* — ✅ done 2026-07-21

- **Rename, don't split** (owner decision, D6): `quarkus-langchain4j-scaffolding` becomes
  `scaffold-project`, keeping its full umbrella scope (creation + components) in one skill.
  Rationale: renames are expensive (install identity, directory listing) so do it now while
  the install base is ~zero (verified: absent from skills.sh search results for
  "quarkus"/"langchain4j"); a split into a separate component skill stays cheap to do later
  if the skill outgrows one context window — no name is being claimed that would break.
- **Invocation stance:** `scaffold-project` does NOT get `disable-model-invocation: true` —
  it must stay model-invoked so component requests ("add RAG", "create an AI service")
  keep auto-triggering; it is also the documented `/scaffold-project` step of the flow.
  Only `setup-agentic-scaffolding` and `audit-project` are user-invoked-only.
- Rework the renamed SKILL.md's creation path with the MCP-surface findings:
  - `quarkus_create` creates **and auto-starts dev mode**; required params `outputDir`,
    `noCode`, `noWrapper`. Recommended defaults: `noCode=true` (repo templates replace the
    codestart hello-world), `noWrapper=false` (keep `mvnw`) — both confirmed with the user.
  - Extension selection is a **mandatory user gate** (the tool's own contract: present the
    list with a recommended default and wait).
  - No `streams` param — resolve LTS vs latest up front and pass `quarkusVersion` (or omit
    for latest).
  - Post-create workaround: `git init && git add -A && git commit` before
    `quarkus_start`/`quarkus_skills` (MCP refuses non-git projects).
  - Delegate to the MCP: skeleton/BOMs/native profile (`quarkus_create`), per-extension
    patterns (`quarkus_skills`), verification (`devui-testing_runTests`,
    `devui-exceptions_getLastException`). Keep in the skill: sub-package layout,
    non-extension deps (embedding model, document parser), opinionated templates,
    `application.properties` baseline.

### 3. Author `audit-project` *(new scope, owner-requested 2026-07-21)* — ✅ done 2026-07-21

Read-only by default: audits an existing project against the conventions (§2–§5), the
package layout, the dependency/properties baseline, and reports prioritized findings with
evidence and a suggested fix each — applying fixes only after explicit confirmation, by
handing off to `scaffold-project`'s component sections. Serves both conformance checks on stack projects and
gap analysis for plain Quarkus projects adopting the stack (adoption path ends pointing at
setup Phase C for the conventions file). Uses `quarkus_skills`/`quarkus_searchDocs` with
`projectDir` for version-matched validation. Checks include: BOM imports without pinned
extension versions, `maven.compiler.release` ≥ 25 (25 when a native profile exists),
`-parameters`, native profile present, declarative `@RegisterAiService` over manual wiring,
tools as CDI beans, upstream guardrail imports, reactive types only at the edge,
observability extensions, Dev Services disabled when a real endpoint is configured, and the
§5 test baseline.

### 4. Sequence before the Anthropic directory submission *(ordering, zero effort)*

Issue #4 (submission kit) is still pending user action — land this restructure and the
renames **first**; renaming skills after directory listing costs a resubmission.

## P1 — Integration and parity

### 4. Sync every distribution surface *(medium effort, mechanical)* — ✅ done 2026-07-21

New/renamed skills must propagate to: `.claude-plugin/plugin.json` + `marketplace.json`,
`.codex-plugin/plugin.json` + `plugins/quarkus-agentic/` symlink wrapper +
`.agents/plugins/marketplace.json`, `gemini-extension.json`, per-skill `agents/openai.yaml`,
`scripts/install-bob-skill.sh` (pending D3), and CI:
`ci/check-version-consistency.sh` (new SKILL.md version headers) and the parity gate scope.

### 5. Rewrite the README around the flow *(high adoption impact)* — ✅ done 2026-07-21

Quick install (`npx skills add …`) → `/setup-agentic-scaffolding` → create skill. Collapse
the three near-duplicate per-agent prerequisite sections (~140 lines) into the setup skill's
content; add a short **Flow** section (router-in-prose, `ask-matt` style); add the skills.sh
badge; fix the stale "current version is 0.10.0" prose line.

**Document both invocation forms.** The two distribution channels produce different slash
names in Claude Code: a skills-CLI install is bare (`/setup-agentic-scaffolding`), a plugin
install is namespaced by the plugin id (`/quarkus-agentic:setup-agentic-scaffolding` — the
id stays `quarkus-agentic` by design; v0.10.1 added the human `displayName` instead of
renaming, to preserve install identity). Every skill mention in README/docs must show both
forms, or plugin users will conclude the skill did not install (observed in practice,
2026-07-21).

### 6. Decide the Gemini conventions story *(small)* — ✅ done 2026-07-21

`gemini-extension.json` already sets `contextFileName: AGENTS.md` and declares both MCP
servers — for Gemini-via-extension, prerequisites are self-serve today. Decide: keep
`AGENTS.md` as the Gemini context file (document it), or ship `GEMINI.md`; either way the
setup skill's Phase C table and the parity gate must reflect the choice.

## P2 — Discovery and quality

### 7. Optimize for skills.sh discovery *(small, compounding)* — ✅ done 2026-07-21

Search matches on skill `name` + `description`: keep **quarkus, langchain4j, agentic, MCP**
present in the description of every skill (and in the create skill's name if D1 allows).
Leaderboard ranks by installs; badge + topic placement compound.

### 8. Realign the eval (issue #6) *(after the split)*

The eval design predates the split; re-scope it to the new flow (setup + create + component
skills measured separately or end-to-end).

### 9. Simplify the Bob path *(decided 2026-07-21)* — ✅ done 2026-07-21

Bob gets a branch in setup Phases B/C (`.bob/mcp.json` + `AGENTS.md`). Correction over the
initial research: the skills CLI **does** support IBM Bob as a first-class agent
(`bob` in `vercel-labs/skills` `src/agents.ts`, installing to `.bob/skills` /
`~/.bob/skills`, verified in source and by a live install) — so `npx skills add` covers Bob
too, and `scripts/install-bob-skill.sh` can be demoted to a documented fallback.

## Per-agent automation matrix (reference, as of 2026-07-21)

| Agent | MCP registration | Conventions file | Live same session? |
|---|---|---|---|
| Claude Code | `claude mcp add -s user …` (bash, automatable) | `CLAUDE.md` | No — restart |
| Codex CLI | `codex mcp add …` / `~/.codex/config.toml` | `AGENTS.md` | No — restart; sandbox may block network |
| Gemini CLI | `gemini mcp add` / `.gemini/settings.json`; or the extension (already ships MCPs) | `GEMINI.md` (ext. sets `AGENTS.md`) | No — restart |
| Cursor | write `.cursor/mcp.json` | `.cursor/rules/*.mdc` or `AGENTS.md` | GUI enable |
| Copilot CLI | `copilot mcp add` / `~/.copilot/mcp-config.json` | `AGENTS.md` | **Yes** |
| opencode | write `opencode.json` (`mcp` key) | `AGENTS.md` | **Yes** (hot-reload) |

## Decisions (owner, 2026-07-21)

| # | Decision | Outcome |
|---|---|---|
| D1 | Creation-skill name | **`scaffold-project`** (revised 2026-07-21, superseding `new-project`) — carries the repo's "scaffolding" brand, stays generic across project types (agents, MCP server/client, plain AI service), and is verified unclaimed as an exact name on skills.sh (closest: `project-scaffold`, `project-scaffolder`, both low-install). Spelled with **c** — "Skaffold" with k is Google's Kubernetes tool. "quarkus"/"langchain4j" carried by the description. |
| D6 | Rename vs. split | **Rename the existing umbrella skill** (`quarkus-langchain4j-scaffolding` → `scaffold-project`) and keep creation + components together — no separate `scaffold-component`. Owner's UX priority: fewest skills facing the user. Install-base cost measured ~zero; split remains a cheap later refactor. `scaffold-project` stays model-invocable (hybrid). |
| D2 | Superpowers in setup | **Check + guide** — the setup detects it and presents install commands; never auto-installs third-party plugins. |
| D3 | Bob support level | **Include in setup** (Phase B/C branch). skills.sh covers Bob (see P2-9 correction); `install-bob-skill.sh` becomes a fallback. |
| D4 | Audit-skill scope | **`audit-project`** added (P0-3): read-only conformance/adoption audit, fixes only on confirmation. |
| D5 | Setup state file location & name | Open — decide while authoring P0-1 (`docs/agents/` block vs. dotfile). |

## Prompt-brief addition for this repo

> The repo is now a multi-skill flow, split along the invocation axis: `setup-agentic-scaffolding`
> and `audit-project` are user-invoked orchestrators (`disable-model-invocation: true`);
> `scaffold-project` (the renamed umbrella skill) is hybrid — the `/scaffold-project` creation
> step of the flow AND model-invoked component scaffolding on existing projects, kept as one
> skill by owner decision D6. Skills reference each other in `/skill` prose with hard-dependency pointers, keep
> seed templates in their own folder, and follow Explore → Present (recommendation first) →
> Confirm → Write. Any new/renamed skill must propagate to all distribution manifests and the
> version-consistency + parity CI gates.
