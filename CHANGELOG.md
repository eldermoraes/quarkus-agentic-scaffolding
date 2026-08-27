# Changelog

All notable changes to this artifact are documented here. This project adheres to semantic
versioning.

## v0.21.0 — 2026-08-27
- **Baseline moved to the Quarkus 3.39 line.** `ci/baseline.env` goes to platform `3.39.1`
  (from `3.38.3`, Renovate PR #35). Nothing required a corrective change: the templates compile
  green against 3.39.1 in the CI compile job and in a local `ci/build-from-templates.sh 3.39.1`
  run.
- **`ci/test-uninstall-bob-skill.sh` now pins the dangling-symlink and bare-invocation
  branches.** Case 8 pins the conservative choice for a symlink whose target is gone: ownership
  cannot be verified through a broken link, so the uninstaller leaves it in place and warns.
  Case 9 pins that a bare invocation (no argument) operates on `$PWD`, exercised from an isolated
  subshell. Three assertion gaps in cases 4, 6, and 7 are closed — 49 assertions across 9 cases,
  `scripts/uninstall-bob-skill.sh` itself untouched. (#16, PR #41)
- **The idempotent re-run's repair path now covers `context7`, not just `quarkus-agent`.** The
  v0.18.0 stored-command verification rule stated the repair only for `quarkus-agent` — yet
  `context7` is the more frequent stale entry, since Renovate bumps its pin and every
  already-configured machine then holds the previous version, dead-ending `add` on
  `already exists`. The setup skill's §5 verification paragraph now names both pinned strings and
  both `claude mcp remove` forms, §5.1 and the README's *How to use with Bob* carry one
  `bob mcp add-json` example per server, and the Renovate custom managers already track the new
  occurrences. (#20, PR #39 by @matheusandre1)
- **Bob's `-s global` MCP registration is now a stated choice, not a silent default.** The setup
  skill's §5 Bob row and §5.1, and the README's *How to use with Bob*, register with `-s global` —
  which writes `~/.bob/settings/mcp.json` and applies to every workspace on the machine — without
  saying so, while the equivalent decision for the conventions file carries an explicit trade-off
  paragraph. All three spots now state the machine-wide scope and why it is the default (the MCPs
  are tools, not conventions, and re-registering per project is friction), and offer `-s workspace`
  to users who mix stacks — with the ENOENT seeding caveat §5.1 already documents. (#19, PR #38
  by @matheusandre1)
- **Pasting a whole Bob fence now runs nothing — all three forms are commented.** The v0.20.1
  "Pick one" comment left the first form active, so uncommenting `--global` and pasting the block
  still ran the `<cwd>` form as well. Both fences (install and uninstall, keeping the symmetry
  issue #17 asked for) now comment every form, so "uncomment the one you want" applies to each of
  them; the uninstall fence's read-only `ls` verify line stays active.

## v0.20.1 — 2026-08-26
- **The README no longer presents `-s workspace` as opt-in on `bob mcp add`.** Workspace scope is
  Bob's own default, so dropping the `-s global` flag from the published command registers in the
  current project — and dies with `ENOENT … .bob/mcp.json` when that file is missing. The
  paragraph now states the default the way the setup skill's §5.1 always has. (#25, PR #32 by
  @matheusandre1)
- **The five consistency nits deferred from the v0.17.0 reviews are closed.** The Bob install and
  uninstall fences mark their three forms as alternatives, not a sequence; the conventions-removal
  recipe's optional file drop got its own `# 4b.` comment; fixture D1's label now matches D2/D3
  (`ACCEPTED residual`); `CONTRIBUTING.md` carries the IBM-internal qualifier the README already
  had; and the Gemini CLI row states that `gemini mcp add` defaults to `--scope project`. (#17,
  PR #33 by @matheusandre1)
- **Contributors no longer have to guess the next version.** `CONTRIBUTING.md` step 5 asked every
  PR to bump the version headers and name its own changelog section — unknowable from a branch,
  and two concurrent PRs would conflict on all nine headers. External changes are now recorded
  under a `## Unreleased` heading in this file (created when absent), and the maintainer renames
  that section and bumps the headers in the release commit.

## v0.20.0 — 2026-08-21
- **Security-audit hardening: the skills' instruction text now states its trust posture
  explicitly, and the one remaining download-and-execute path is gone.** Driven by the skills.sh
  audit results (Snyk agent-scan and Gen Agent Trust Hub flagged all three skills at Warn);
  the goal is zero risk indicators per skill.
  - *Setup: no installer scripts, ever.* The JBang last-resort install no longer downloads an
    installer script at all — not even as the reviewed three-step flow v0.18.0 introduced. The
    rule is phase-wide: package managers are the only install path the skill performs for every
    tool in the Phase A table, and on a machine without one the user installs that tool
    themselves per its official documentation (manual/archive instructions preferred) and the
    skill re-probes once, checking `~/.jbang/bin/jbang` directly as well as the PATH. The Phase A
    rule, the toolchain table rows, and `SECURITY.md` were rewritten accordingly; `SECURITY.md`
    also discloses that the approved `jbang jdk install 21` gets no verification beyond jbang's
    own.
  - *Setup: registration is configuration, not execution.* §5 now states that the skill never
    runs `jbang`/`npx` itself — it writes the pinned command into the agent's MCP config and the
    agent runtime resolves the artifact from its official registry when it first starts the
    server, which on Copilot CLI, opencode, Bob, and a `claude mcp list` health check is
    immediately after the write. `jbang jdk install 21` is labeled an external JDK download
    needing explicit approval, config file registrations are read-modify-write with an approved
    diff, `CONTEXT7_API_KEY` presence is checked with `test -n` (never echoed), and Phase C
    documents that the conventions templates are static, versioned content the skill never
    injects runtime text into.
  - *Scaffold: the agent example is an internal support-console workflow.* The templates and §8
    dropped the earlier framing of the ticket as adversarial free text of unknown origin: an
    operator or application code submits a customer-authored ticket, which stays guarded
    (PromptInjectionGuard, `<ticket>` delimiting, edge validation). The `TriageSocket` javadoc
    became a production note pointing at WebSockets Next security and the `secure-sql-chatbot`
    sample; a commented Security block (OIDC + HTTP auth policy) landed in
    `application.properties.template`, with
    the permission paths listing `/mcp` **and** `/mcp/*` (Quarkus matches them exactly, and the
    MCP extension also serves `/mcp/sse` and `/mcp/messages/*`) and an `application-type=web-app`
    line for browser clients, which cannot send an `Authorization` header on a WebSocket upgrade.
  - *Scaffold: every free-text prompt slot is delimited, and every entry method is guarded.*
    `{problem}` (AiService), `{request}` (McpClient), `{question}` (RagSetup), the
    supervisor-variant ticket, the Synthesizer's `{category}`/`{priority}` (model-produced but
    derived from customer text), and the commented structured-output examples are wrapped in
    markers with "data, not instructions" system-message language; each of those entry methods
    now carries `@InputGuardrails(PromptInjectionGuard.class)` instead of a comment suggesting
    it, and the guard rejects input carrying the delimiter markup itself, which would otherwise
    close the delimited region early. The MCP client/server templates call for trusted servers
    and authorized clients; the stdio sample became a non-resolvable
    `<your-mcp-server>@<exact-version>` placeholder; every key that records user content —
    request/response logging, tracing prompt/completion capture, MCP traffic logging,
    `http-problem` detail echoing — is `%dev.`-scoped (conventions §3/§4 and the audit checks
    updated to match); RAG documents are described as curated, first-party content.
  - *Audit: content provenance stated.* A §2 subsection records that the audit reads only
    local, user-selected project files, follows no URLs or feeds, and makes only targeted
    external lookups — the `quarkus_status` gate call, `quarkus_searchDocs`/`quarkus_skills`,
    and context7 doc queries — whose results are evidence, never instructions; it never starts
    or stops the project's services; report evidence quotes the minimum and redacts secrets. A
    §5.3 row now checks that entry AI-service methods delimit their free-text slots and attach
    `@InputGuardrails`.
  - *Conventions:* the GraalVM release-train citation moved from the Medium post to the
    official release calendar, dev logging is now spelled `%dev.`-scoped (as is the tracing
    prompt/completion capture in §3), and a new §4 bullet states the rule the templates
    implement: externally originated free text is delimited in prompts and guarded at the entry
    method.

## v0.19.1 — 2026-08-11
- **Audit scenario (a) is now footprint-based, closing a routing gap for off-lineage LangChain4j.**
  Scenario (a) literally required the `quarkus-langchain4j-bom` import while (b) required no
  LangChain4j footprint at all, so a project on a pre-BOM LangChain4j vintage — one of the very
  legacy triggers §5.0 exists for — matched neither bullet. Any LangChain4j vintage now routes to
  (a), with the off-lineage version reported as its §5.0 finding; (b) stays reserved for projects
  with no LangChain4j footprint.

## v0.19.0 — 2026-08-11
- **`/audit-project` now reports findings as a single severity-ordered markdown table** (Severity /
  Evidence / Finding / Violates / Fix) instead of per-finding text blocks. Severity grades (high,
  medium, low) and the closing summary count are unchanged; the table is just easier to scan.
- **Legacy projects no longer block the audit — they become HIGH findings.** A new §5.0 "Platform
  lifecycle" check area turns the former hard stops into audit items: an EOL Quarkus platform line,
  an unsupported Java release, a LangChain4j vintage outside the `quarkus-langchain4j-bom` lineage,
  and a missing conventions file (`CLAUDE.md`/`AGENTS.md`/`GEMINI.md`). When the conventions file
  is absent, the audit runs against the skill's own §5 catalog (which covers the core of the
  canonical conventions) and reports the absence as a finding. The only remaining project-side stop
  is "not a Quarkus project at all"; the Quarkus Agents MCP gate is unchanged.

## v0.18.0 — 2026-08-10
- **Every published Quarkus Agents MCP registration now pins the JDK: `jbang --java 21+
  io.quarkus:quarkus-agent-mcp:1.2.5:runner`.** The old command shipped no JDK hint, and §5 of the
  setup skill justified that by saying the missing `java-version: 21+` was "moot here, because
  Phase A already requires JDK 25+". That reasoning was the bug: Phase A proves the *machine* has a
  JDK 25, but JBang resolves its own JDK and falls back to its default — 17 on JBang 0.125.x —
  whenever the spawning process exports no `JAVA_HOME` (GUI- and IDE-launched agents typically do
  not) or points below 21. The server is compiled for Java 21, so it died at boot with
  `UnsupportedClassVersionError: … class file version 65.0 … up to 61.0`, the client retried and
  gave up, and it read as "the MCP is broken". Verified by MCP `initialize` handshake against 1.2.5:
  the old command **fails** with no `JAVA_HOME` and passes with `JAVA_HOME=25` — so a
  terminal-launched agent was passing by accident of its environment; `--java 21+` passes in both.
  The `quarkus-agent-mcp@quarkusio` alias is not an escape hatch: it *does* declare
  `java-version: 21+`, but JBang 0.125.x ignores that for a GAV `script-ref` and fails identically
  (also verified). `21+` is a floor rather than a pin, so a machine already on 25 reuses it instead
  of downloading JDK 21. Touches all five `mcp add` rows, the args line in §5, and the JSON snippet
  in the setup skill, the Claude/Codex/Gemini/Bob commands and both snippets in `README.md`, and
  `gemini-extension.json` — 16 occurrences, now coupled by a gate (below) rather than by hand. The
  Renovate pin still resolves — its `matchStrings` anchor on the GAV, which the flag precedes.
- **Bob's global MCP file was documented at a path Bob never reads.** We published
  `~/.bob/mcp.json` (with a hedge toward `mcp_settings.json`); Bob 2.0.0's own constants are
  `MCP_WORKSPACE_FILENAME = "mcp.json"` (→ `<project>/.bob/mcp.json`, correct), `MCP_GLOBAL_FILENAME
  = "mcp.json"` in the global settings directory (→ **`~/.bob/settings/mcp.json`**), and
  `MCP_LEGACY_GLOBAL_FILENAME = "mcp_settings.json"`, which Bob migrates **only when `mcp.json` does
  not yet exist**. So on any machine that already has `mcp.json`, a registration written to the
  legacy name is silently ignored — the setup reports success and Bob never loads the server. New
  §5.1 in the setup skill documents the two real paths, the legacy trap, and the precedence rules,
  and `README.md`'s uninstall boundary now names the global file it keeps.
- **Bob registration switches from hand-written JSON to `bob mcp add` (Bob 2.0.0), verified against
  the CLI.** `bob mcp add -s global <name> jbang -- --java 21+ <GAV>` writes
  `~/.bob/settings/mcp.json`, creating the file and directory when missing, and `bob mcp list` is a
  real verification in the same style as the other agent rows. Two behaviors that cost a run if you
  do not know them, both reproduced in a scratch workspace: the `--` separator is **mandatory**
  (without it Bob parses the server's flag as its own and exits `error: unknown option '--java'`),
  and `-s workspace` does **not** create `.bob/mcp.json` — it exits `Fatal error: ENOENT`. Bob also
  watches the file and restarts the servers whose entry changed (`Restarting changed servers` in
  `~/.bob/logs/shell/`), so its "Live this session?" cell moves from "Reload in UI" to yes.
- **`bob mcp add` cannot repair a stale entry; `add-json` can.** Verified: on a name that already
  exists, `add` exits 1 with `Error: MCP server "…" already exists in …` and leaves the old entry
  intact — so an idempotent re-run could not have replaced an unpinned registration through the route
  this release recommends. §5.1 and the README now document
  `bob mcp add-json -s <scope> quarkus-agent '{…}'`, which overwrites in place, with a
  confirm-before-overwrite rule.
- **Registrations written by earlier releases of this skill sit one directory above where Bob looks.**
  Before v0.18.0 we pointed agents at `~/.bob/mcp.json` / `~/.bob/mcp_settings.json`; Bob reads
  neither and migrates neither (its legacy migration only ever looks inside the settings directory),
  so a machine set up by an earlier run can hold a registration that has never loaded. Both the skill
  and the README now name those two orphan paths as things to check, not just the settings directory.
- **`scripts/uninstall-bob-skill.sh`'s boundary comment and `--help` named the wrong files.** They
  listed a `settings.json` file where Bob 2.0.0 has a `settings/` directory, and named only
  `.bob/mcp.json` as the MCP registration the uninstall must not touch — which under `--global` is
  now `~/.bob/settings/mcp.json`. Both scopes are spelled out, in the script and in the README's Bob
  uninstall paragraph. Behavior unchanged: the script never touched those files.
- **New gate: `ci/check-mcp-command-consistency.sh`.** The command is hand-maintained in 16 places;
  the version gate couples the *version* and Renovate the *GAV*, but nothing coupled the *command*,
  so `--java 21+` could be present in one artifact and missing in another with every check green —
  a class of drift this repo has already hit (`9fdb9d2`). The script normalizes each published
  surface (markdown, CLI, JSON args, `add-json` payload) and fails unless every occurrence is
  preceded by the pin and carries the same version. Wired into `quality.yml`; `CHANGELOG.md` and
  `docs/` are exempt, since they quote older commands as a record. Proven to fail on a
  single unpinned copy before being committed.
- **Verification now reads the stored command, not the server's name.** Every Verify cell checked
  only that something called `quarkus-agent` was listed — which an unpinned entry from an earlier
  release or from the upstream Claude plugin satisfies, so no existing install was ever repaired and
  all of them were reported verified. §5 requires comparing the printed command to the canonical
  string and treating a mismatch as a repair (replace the entry: `add-json` for Bob, remove + re-add
  elsewhere), and reporting both strings.
- **`jbang` itself may be unreachable, which no JDK flag can fix.** A GUI- or IDE-launched client
  starts from launchd/systemd with a minimal PATH (`launchctl getenv PATH` is empty on macOS →
  `/usr/bin:/bin:/usr/sbin:/sbin`), where none of SDKMAN, Homebrew, or the upstream installer put
  `jbang`; the symptom is `spawn jbang ENOENT`. "`jbang` must be on PATH — that is Phase A's job"
  was the same category error this release fixes for `JAVA_HOME`: Phase A probes the login shell,
  not the spawn environment. Both files now say to register the absolute path from
  `command -v jbang` when a client fails that way.
- **Phase A installs a 21+ JDK for JBang instead of letting the first handshake do it.** With no
  JBang-managed 21+ and no visible `JAVA_HOME`, `--java 21+` makes JBang download a JDK *inside* MCP
  startup: `initialize` times out and reads as "the MCP is broken" on first run. Phase A now checks
  `jbang jdk list` and offers `jbang jdk install 21` in the foreground.
- **Bob's route no longer hard-depends on the `bob` binary**, and its handoff is honest. §5.1 probes
  `command -v bob` and keeps a hand-write path (read-modify-write, both real paths, verified in the
  UI's MCP tab) for IDE-only machines. And while Bob restarts changed *servers* by itself, it loads
  skills and the conventions file once per conversation — §5.2 now closes a Bob run by telling the
  user to start a new conversation before `/scaffold-project`.
- **The upstream Claude plugin carries the same JDK trap, and the README now says so** — with the
  right reason. `quarkus-agent@quarkus-tools` launches `jbang quarkus-agent-mcp@quarkusio`: the
  alias *does* declare `java-version: 21+` and JBang 0.125.x ignores it for a GAV `script-ref`, and
  `RELEASE` resolution means two machines run different code. The Claude manual fallback leads with
  the pinned `claude mcp add` (both servers at `-s user`), and the plugin is presented as the
  alternative with the name-collision warning the repo already gives for Gemini.
- **`ci/test-uninstall-bob-skill.sh` now covers the `--global` half of the MCP boundary.** Case 6
  redirects `HOME` but never fixtured `~/.bob/settings/mcp.json`, so the file this release promises
  to preserve under `--global` — where `BASE="$HOME"` — was asserted nowhere. Two asserts close it.

## v0.17.0 — 2026-08-10
- **Documented how to uninstall this artifact — and only this artifact.** New `## Uninstall`
  section in `README.md`, placed after *Advanced — personal use* because it depends on what that
  section describes. One removal block per install path (skills CLI, Claude plugin, Codex plugin,
  Bob, Gemini extension), each with its verification command, then the managed-block procedure for
  the conventions file and a verify sweep. The boundary is the feature: JDK 25 / GraalVM, JBang, the
  container runtime, the **Quarkus Agents MCP**, **context7**, `superpowers`, and every project
  `/scaffold-project` generated all survive. `.cursor/mcp.json`, `opencode.json`, and `.bob/mcp.json`
  are kept for the same reason — their entire content is the two MCP servers the boundary protects.
  The *Advanced* section's "Precedence and reverting" paragraph loses its reverting half and
  cross-references the new section, so undo lives in one place.
- **Every published command was validated against primary sources** — `--help` output, CLI source,
  and official docs — by six read-only subagents before publication. Three findings changed what
  shipped:
  - *The `sed` procedure was destructive and is gone.* A count-based precheck
    (`grep -c …`, expect 2) does not gate the dangerous cases: a user writing *about* the markers,
    markers out of order, and both markers on one line all pass it, and `sed` then deletes
    user-authored lines — to end of file in two of the three. Counts cannot fix it (they carry no
    ordering, and `grep -c` counts lines, not occurrences). Published instead: an `awk` precheck
    that anchors on `^<!--` and compares line numbers, plus a `perl -0777 -i -pe` substitution that
    *requires* both markers, so an incomplete or out-of-order pair leaves the file byte-for-byte
    untouched. `\r?` for CRLF, `\n?` for a block whose `END` is the last line without a trailing
    newline.
  - *The skills-CLI command was simply broken.* `npx skills remove -s A B C -a '*' -y` removes
    nothing: `remove` has no `-s/--skill` (it exists on `add`) and never expands `'*'`, so it exits
    1 with `Invalid agents: *`. Published: positional skill names and no `-a`, which cleans every
    known agent including ghost symlinks. The `--all` warning was corrected too — contrary to its
    own `--help`, `--all` does not imply `-y`, and removal deletes real files.
  - *`gemini mcp add` defaults to `--scope project`.* The re-add commands pass `-s user`, and run
    *after* the uninstall, because a `settings.json` registration shadows an extension-declared
    server of the same name.
- **`scripts/uninstall-bob-skill.sh`** — the mirror of `install-bob-skill.sh`, because Bob has no
  manifest, registry, or command for removing a skill; deleting the directory is the whole
  uninstall. Ownership-checked against each `SKILL.md`'s front-matter `name` — a directory that
  declares a different name, declares none, or has no `SKILL.md` is skipped with a warning rather
  than deleted; the residual, stated in the script's header and in the README, is that a skill of
  your own that *also* declares `name: audit-project` is indistinguishable from ours and will be
  removed, so move it aside first. Symlink-safe (unlinks rather than recursing into the target),
  idempotent, and scoped to the three skill directories — `.bob/mcp.json`, `.bob/rules/`, and your
  other skills are never touched.
- **Two behavior tests, because a destructive script and a destructive one-liner do not validate by
  reading.** `ci/test-uninstall-bob-skill.sh` covers the install/uninstall round trip, idempotency,
  the ownership and symlink guards, and `--global` with `HOME` redirected into a temp directory.
  `ci/test-conventions-block-removal.sh` runs the published commands over 15 fixtures — including
  every input the old `sed` procedure destroyed — and asserts that each refusal leaves the file
  byte-for-byte identical, plus a drift guard that fails if `README.md` stops publishing the exact
  validated commands. Three of the fixtures pin the accepted residual instead: a marker quoted at
  column 0 is column 0 to `awk` and `perl` alike, so a quoted pair — or a mixed real/quoted pair,
  whose deletion spans everything between the two lines — reaches `OK-SAFE-TO-REMOVE`. The mandatory
  backup and the "read the diff before you trust it" warning are the mitigation. Both tests run in a
  new `behavior-tests` job in the quality workflow.
- **Corrected five pre-existing claims** the validation surfaced (details and sources in the
  commit): `~/.bob/AGENTS.md` *is* Bob's documented global context file; Bob's marketplace exists
  but carries modes and MCP servers rather than skills; the global MCP path is documented
  inconsistently by IBM's own two doc sets, so both names appear and the UI's **Edit Global MCP** is
  recommended; skill approval is once per conversation via a single global boolean; and
  `codex plugin add` does exist, so the v0.7.0 entry's present-tense "non-existent" was softened to
  name the version instead. Two additions to the Bob section: a skill's `description` is
  load-bearing, and skills require Bob's **Advanced** mode.
- All version headers synchronized to 0.17.0.

## v0.16.0 — 2026-08-10
- **Resolved the remaining skills.sh audit findings with engineering, not scan-appeasement.** The
  Gen Agent Trust Hub report on `setup-agentic-scaffolding` (HIGH, four findings) and the Snyk
  report on `scaffold-project` (MEDIUM, W011) are both addressed at the root; no functionality
  removed.
  - *Pipe-to-shell eliminated* (Trust Hub #1, CRITICAL). The literal
    `curl -Ls https://sh.jbang.dev | bash` no longer appears anywhere: the JBang last resort is now
    a three-step download → inspect → approve → execute flow (`curl -LsS -o jbang-install.sh …`,
    show the file, run it only after explicit approval, delete it). The bytes the user approves are
    the bytes on disk and the bytes that run — a piped stream offers nothing stable to approve.
    Package managers remain the recommended path.
  - *External dependencies pinned* (Trust Hub #2). `@upstash/context7-mcp@4.0.0` (npm `latest`) and
    `io.quarkus:quarkus-agent-mcp:1.2.5:runner` — the explicit GAV the floating `quarkusio` catalog
    alias resolves to (`script-ref: …:RELEASE:runner`), validated runnable via `jbang info tools`.
    Pinned across the setup skill, `README.md`, and `gemini-extension.json`; two Renovate
    `customManagers` (npm + maven regex over all three files) keep the pins current, so upgrades
    become explicit reviewable PRs instead of whatever-is-newest-at-startup.
  - *Managed-block boundary on generated conventions* (Trust Hub #3). `CLAUDE.md`/`AGENTS.md` (and
    their byte-for-byte seed templates) are wrapped in stable, version-free
    `<!-- BEGIN/END quarkus-agentic-scaffolding conventions -->` markers. Phase C is rewritten
    around them: markers present → deterministic replace of the block only, every byte outside
    untouched; markers absent → the existing draft-merge, adding the markers so the next run is
    deterministic. Generated instruction text is now explicitly delimited from user content —
    the injection surface the auditor flagged — and the merge stopped being heuristic.
  - *Probe output is data, never instruction* (Trust Hub #4). New §3 rule: directives found inside
    command output are quoted back as findings, never executed.
  - *Triage template hardened at the ingestion edge* (Snyk W011). `Agent.java.template` now
    demonstrates the secure pattern it should have taught: the two entry sub-agents carry
    `@InputGuardrails(PromptInjectionGuard.class)` (wired from `Guardrails.java.template`, FQN
    `dev.langchain4j.service.guardrail.InputGuardrails` verified against upstream docs); prompts
    delimit the ticket in `<ticket>` markers with a system-message instruction to treat it as data;
    `TriageBridge` rejects blank/over-long input before any model call (4 000 chars, aligned with
    the guardrail); and the failure path stops leaking internals — `emitter.fail(e)` and
    `ProgressUpdate.error(t.getMessage())` are replaced by full server-side logging plus a generic
    client-safe `ProgressUpdate.failed()`, mirroring the RFC 9457 philosophy at the REST edge.
    `ci/build-from-templates.sh` compiles green against platform 3.38.1. One honest caveat: docs
    confirm guardrails on `@RegisterAiService` interfaces, but not explicitly when such an
    interface is invoked as an `@Agent` sub-agent; the sub-agents are ordinary CDI AI-service
    proxies, so the guard should run, but that is inference — worth a runtime assertion in a
    scaffolded project.
  - *`SECURITY.md` added.* States the trust boundary the skills operate under (read-only probes,
    approval before any mutation, no piped installers, pinned sources, no plaintext secrets,
    managed blocks, secure-by-default templates) and routes vulnerability reports to private
    GitHub security advisories.

## v0.15.0 — 2026-08-10
- **Refreshed the model defaults** (EVOLUTION-PLAN item 4). Chat goes from `llama3.2` /
  `llama3.2:1b` to **`qwen3:4b`** and **`qwen3:1.7b`** (the `smaller` named model): qwen3 is what
  the official quarkus-langchain4j Ollama guide uses, and its tool-calling is markedly better —
  which is precisely what the tool and agent templates exercise. The in-process embedding model
  goes from `langchain4j-embeddings-all-minilm-l6-v2` to
  **`langchain4j-embeddings-bge-small-en-v15-q`**, upstream Easy RAG's recommendation, with a
  better MTEB score at a similar footprint. Both artifacts stay managed by
  `quarkus-langchain4j-bom` (no version pin); a local build against platform 3.38.1 resolved the
  new one at 1.17.2-beta27 and compiled green. Touches `application.properties.template`,
  `pom.xml.template`, `RagSetup.java.template`, the `scaffold-project` RAG section, and
  `docs/VALIDATING-TEMPLATES.md`.
- **Checked and kept `model-id`.** The Ollama guide appears to show `chat-model.model-name`, which
  looked like a wrong key in our templates. It is not: `"model-name"` in the reference is the
  *placeholder for a named configuration*, and the config model generated by
  `quarkus-langchain4j-ollama` 1.12.2 lists `chat-model.model-id` as the real property, with no
  `chat-model.model-name` alongside it. No change — recorded so the question is not re-opened.

## v0.14.0 — 2026-08-10
- **Baseline moved to the Quarkus 3.38 line** (issue #11). `ci/baseline.env` goes to platform
  `3.38.1`, `quarkus-langchain4j-bom` `1.12.2`, and JDK `25.0.4+7.0.LTS`. Nothing in 3.38 required
  a corrective change: all six items in the 3.38 migration guide have zero surface in this
  repository, and the weekly cron had already built the templates against 3.38.1 successfully
  before the bump. The `QUARKUS_LANGCHAIN4J_BOM_VERSION` comment now spells out that the line is a
  release watcher and not what a build resolves — it read `1.12.0` while platform 3.37.2 actually
  shipped `1.11.2`.
- **`@Skills` in the conventions and templates.** The 3.38 line carries quarkus-langchain4j
  `1.12.x`, which introduces the `@Skills` annotation (`io.quarkiverse.langchain4j.skills`;
  verified present in `quarkus-langchain4j-skills` 1.12.2 and absent in 1.11.2 — the artifact
  itself already existed, only the annotation is new). A service annotated with `@Skills` gets an
  `activate_skill` tool plus a system message advertising the available skills, so reusable
  instructions live in `SKILL.md` files instead of an ever-growing `@SystemMessage`. Added to the
  extension menu, to `AiService.java.template` and `application.properties.template` as commented
  blocks, and as a §4 convention. The extension is `status:preview`, which the text says plainly;
  it stays out of the CI extension list for that reason.
- **`quarkus-http-problem` in the extension menu** (issue #10). Errors escaping a REST resource
  become RFC 9457 `application/problem+json` instead of a raw 500 with a stack trace — relevant
  here because a model timeout, a dead inference endpoint, or a throwing tool would otherwise leak
  prompts and internal names. Added as optional-recommended, with a §3 convention and a commented
  configuration block.

  Correcting the issue's premise: the extension **is** in `io.quarkus.platform:quarkus-bom` from
  3.38.0 (0 occurrences in the 3.37.2 BOM, 2 in 3.38.0 and 3.38.1 on Maven Central), so it needs
  **no** explicit `<version>` and is *not* the exception to the "no version pins" convention that
  the issue anticipated. The extension's own README still states the opposite; the BOM is
  authoritative. Its current version is 3.38.1, not the 3.33.2 recorded when the issue was filed.

## v0.13.3 — 2026-08-10
- **Hardened the two credible findings from the skills.sh security audits.** Both Gen Agent Trust
  Hub and Snyk rated `setup-agentic-scaffolding` HIGH, on two counts worth acting on:
  - *Piped installer.* Phase A led with `curl -Ls https://sh.jbang.dev | bash` as a way to install
    JBang. Package managers (SDKMAN, Homebrew, Chocolatey/Scoop) are now the documented path, and a
    new Phase A rule forbids piping a downloaded script into a shell on the agent's own initiative —
    the one-liner is a last resort, named as the trade-off it is, and only after the user approves
    that specific command.
  - *Credential handling.* Phase B told the agent to append `--api-key <KEY>` for context7, which
    puts a secret into a command and a config file verbatim. The stdio server already falls back to
    the `CONTEXT7_API_KEY` environment variable when the flag is absent, so the skill now registers
    context7 with no key argument at all and tells the user to export the key. Added a blanket
    "never handle a secret in plaintext" rule covering chat, config writes, and verification output.
    `README.md`'s three manual-fallback snippets were updated to match.

  The other two findings (prompt-injection surface from writing the conventions file;
  command-execution from `java -version` / `docker version` probes) describe what the skill is for
  and were left alone.

## v0.13.2 — 2026-08-10
- **Fixed the dead Quarkus LTS link.** The scheduled link check caught a 404 on
  `https://quarkus.io/blog/quarkus-lts-releases/`, referenced by the `scaffold-project` skill
  where it tells the agent to pick the current LTS instead of hardcoding a version. Replaced with
  [`https://quarkus.io/releases/`](https://quarkus.io/releases/), which lists the active LTS lines
  and their support windows — a better fit for the "don't hardcode a number that will rot"
  instruction than the 2023 policy announcement post.

## v0.13.1 — 2026-07-21
- **README fixes.** The skills.sh badge image now uses the `www.skills.sh` host directly (the
  apex-domain URL 308-redirects, which GitHub's image proxy does not follow, breaking the image)
  and links to the project's own skills.sh page instead of the site root. The "What's inside"
  repository tree moved below the usage sections so Quick install and The flow lead the page.

## v0.13.0 — 2026-07-21
- **Hard-stop MCP gate.** Closed the rationalization loophole where agents proceeded to scaffold
  manually when the Quarkus Agents MCP was down. Conventions §1 (`CLAUDE.md` / `AGENTS.md`) now
  require verifying the MCP is reachable (`quarkus_*` tools present + a cheap `quarkus_status`
  call) before any Quarkus task, and mandate an immediate STOP — report what is missing, point the
  user to `/setup-agentic-scaffolding` (and to restarting the session), and end the turn — with no
  fallback to the Quarkus CLI, Maven/Gradle archetypes, model memory, or web search. Added a
  matching "verify the MCP first" procedural gate at the top of the `scaffold-project` and
  `audit-project` skills. `/setup-agentic-scaffolding` remains the sole exception. Motivated by
  observed agent behavior of proceeding manually when the MCP is down.

## v0.12.1 — 2026-07-21
- **Grouped skill selection in the skills.sh installer.** `.claude-plugin/plugin.json` now declares
  the `skills` array explicitly, so `npx skills add` presents a selectable "Quarkus Agentic
  Scaffolding" group node that toggles all three skills at once (individual selection still
  works). No behavior change for Claude Code plugin installs, which already auto-discover
  `skills/`.

## v0.12.0 — 2026-07-21
- **Plugin machine id renamed `quarkus-agentic` → `quarkus-agentic-scaffolding`** so the repository
  name, install command, and plugin id all match. The human `displayName` ("Quarkus Agentic
  Scaffolding") is unchanged. Updated across every manifest (`.claude-plugin/plugin.json` +
  `marketplace.json`, `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`,
  `gemini-extension.json`), the `plugins/quarkus-agentic-scaffolding/` Codex wrapper directory, and
  all namespaced invocation forms (`/quarkus-agentic-scaffolding:<skill>`) in the README and skills.
- **Breaking for existing installs.** Because the id changed, a plugin installed under the old
  `quarkus-agentic` id must be reinstalled: uninstall the old id, then reinstall under
  `quarkus-agentic-scaffolding`. Skills and templates are otherwise unchanged.

## v0.11.0 — 2026-07-21
- **Restructured the single umbrella skill into an explicit three-skill flow** split along the
  invocation axis (see `docs/FLOW-REDESIGN-PLAN.md`):
  - **New `setup-agentic-scaffolding`** (user-invoked, `disable-model-invocation: true`) — the
    flow's entry point. Verifies the toolchain (JDK 25 / GraalVM, JBang, container runtime),
    registers the Quarkus Agents MCP + context7 for the running agent, and writes the conventions
    file into the user's project. Ships byte-for-byte seed copies of the root conventions
    (`templates/conventions-CLAUDE.md`, `templates/conventions-AGENTS.md`).
  - **`quarkus-langchain4j-scaffolding` renamed to `scaffold-project`** (model-invoked umbrella,
    owner decision D6 — creation + components stay one skill). Its creation path was reworked
    around the Quarkus Agents MCP surface: `quarkus_create` defaults (`noCode=true`,
    `noWrapper=false`), the mandatory extension-selection gate, a `git init`/commit step before
    `quarkus_skills`/`quarkus_start`, and `devui-testing_runTests` dev-mode verification.
  - **New `audit-project`** (user-invoked, `disable-model-invocation: true`) — read-only
    conformance/adoption audit of an existing project against the §2–§5 conventions, the package
    layout, and the dependency/properties baseline; applies fixes only on confirmation by handing
    off to `scaffold-project`'s component sections.
- **README rewritten around the flow.** Quick install (skills CLI) leads, now installing all three
  skills and covering IBM Bob as a first-class agent; added a **The flow** section
  (setup → scaffold → audit) and the skills.sh badge; collapsed the three near-duplicate per-agent
  prerequisite walkthroughs into a single `/setup-agentic-scaffolding` step plus a manual fallback
  each; documented both slash-command invocation forms (bare via skills-CLI installs,
  `/quarkus-agentic:<skill>` via plugin installs); fixed the stale "current version is 0.10.0"
  prose line.
- **CI gates extended.** `ci/check-version-consistency.sh` now covers all three `SKILL.md` files
  (nine versioned files total, up from seven); `ci/check-conventions-parity.sh` additionally
  verifies the two setup-skill seed copies are byte-for-byte identical to the root `CLAUDE.md` /
  `AGENTS.md`; `ci/build-from-templates.sh` and the validate-templates workflow point at
  `skills/scaffold-project/templates/`.
- **Distribution manifests** (`.claude-plugin/plugin.json` + `marketplace.json`,
  `.codex-plugin/plugin.json`, `gemini-extension.json`) describe the three-skill flow, with
  `scaffolding`, `setup`, `audit`, and `mcp` keywords; `gemini-extension.json` keeps
  `contextFileName: AGENTS.md`. `scripts/install-bob-skill.sh` now installs all three skills
  (same CLI shape) and is documented as a fallback, since `npx skills add` covers Bob natively.
- All version headers synchronized to 0.11.0.

## v0.10.1 — 2026-07-13
- Added a `displayName` of "Quarkus Agentic Scaffolding" to the plugin so the Claude Code UI
  shows a proper human-readable label instead of the prettified `quarkus-agentic` slug. The field
  is set in both `.claude-plugin/plugin.json` and the `.claude-plugin/marketplace.json` plugin
  entry (the marketplace entry wins for users installing from this marketplace, with `plugin.json`
  as the fallback), so installed users see the new name. The `name` identifier stays
  `quarkus-agentic`, so skill namespacing and install identity are unchanged. `displayName`
  requires Claude Code v2.1.143+ and falls back to `name` on older clients. This brings the Claude
  Code manifests to parity with the Codex manifest, which already carried the same display name.
- All version headers synchronized to 0.10.1.

## v0.10.0 — 2026-07-10
- Added MCP scaffolding in both directions: `McpClient.java.template` (an AI service consuming
  MCP tools via `@McpToolBox`, with `streamable-http`/`stdio` client config in
  `application.properties.template`) and `McpServer.java.template` (exposing the app's own
  `TicketTools` as an MCP server via `io.quarkiverse.mcp.server` `@Tool`, versioned by the
  platform member BOM `quarkus-mcp-server-bom` — no pins). SKILL.md gained MCP client (§6) and
  MCP server (§7) sections; the CI extension list now covers `langchain4j-mcp` and
  `mcp-server-http`.
- Conventions: CLAUDE.md/AGENTS.md now cover zero-code AI observability (Micrometer +
  OpenTelemetry auto-instrumentation, GenAI token-usage/cost metrics, per-tool spans) and
  declarative fault tolerance on AI-service methods (`@Timeout`/`@Retry`/`@Fallback`, with the
  `@Timeout` × tool-calling-loops caveat), plus the GraalVM native-baseline note (no GraalVM
  releases for JDK 26, 27, or 28 — native stays on the JDK 25 baseline until JDK 29).
  `application.properties.template` and `AiService.java.template` carry commented, opt-in
  examples for both.
- New CI gate: `ci/check-conventions-parity.sh` + a `conventions-parity` job in the quality
  workflow — CLAUDE.md and AGENTS.md are now diffed under typography normalization so a
  convention edit can no longer land on one side only (a pre-existing one-character drift was
  fixed in the process).
- Added `gemini-extension.json` so the repository can be listed in the Gemini CLI extensions
  gallery (declares the required Quarkus Agents MCP + context7 servers; `contextFileName`
  delivers `AGENTS.md`); it is now the seventh version-carrying file, enforced by the extended
  `ci/check-version-consistency.sh`.
- All version headers synchronized to 0.10.0.

## v0.9.0 — 2026-07-10
- Added a real CI backstop: `ci/build-from-templates.sh` reconstructs a project from the
  templates by convention and compiles it; the `validate-templates` workflow runs it on PRs
  (against `ci/baseline.env`) and weekly against the live latest platform, opening or updating a
  tracking issue on scheduled failures (closed manually once a later run is green); the `quality`
  workflow adds version-consistency, shellcheck, actionlint, and markdownlint gates; scheduled
  link checking via lychee.
- Added `renovate.json` + `ci/baseline.env`: Renovate watches Quarkus platform, the
  quarkus-langchain4j BOM, and new OpenJDK GA releases (java-version datasource) on the
  Dependency Dashboard (approval mode — no automatic PRs). Activation requires installing the
  Mend Renovate app.
- Closed template capability gaps: `Tools.java.template` (@Tool CDI beans + wiring),
  `Guardrails.java.template` (upstream input/output guardrails), `AiServiceTest.java.template`
  (@QuarkusTest wiring smoke test + commented model-dependent and eval examples), and commented
  loop/conditional/error-handler/human-in-the-loop variants in `Agent.java.template`;
  `pom.xml.template` gained the test-scoped `quarkus-langchain4j-testing-evaluation-junit5`
  dependency (version managed by the platform BOM); SKILL.md gained tool/guardrail/test-scaffolding
  sections and the layout gained `tools/` and `guardrails/`; CLAUDE.md/AGENTS.md §4–§5 now cover
  tools, guardrails, and the eval framework.
- All version headers synchronized to 0.9.0.

## v0.8.0 — 2026-07-10
- Documented a universal install path via the skills.sh CLI (`npx skills add
  eldermoraes/quarkus-agentic-scaffolding`), which detects and installs the scaffolding skill into
  any Agent Skills-compatible agent (Claude Code, Codex, Copilot, Cursor, Windsurf, opencode, and
  others). Verified end-to-end against the live CLI. The conventions files and the required MCP
  tooling remain per-agent manual steps, as before.
- All version headers synchronized to 0.8.0.

## v0.7.0 — 2026-06-08
- **Fixed Bob support, which had been modeled on a non-existent CLI.** Removed the hallucinated
  `bob plugin marketplace add` / `bob plugin add` and `bob mcp add` commands (IBM Bob has no plugin
  CLI or marketplace), and removed `BOB.md` and `.bob-plugin/`. Verified against `bob.ibm.com/docs`:
  Bob reads the same `AGENTS.md` as Codex, discovers skills under `.bob/skills/`, and configures MCP
  servers via `.bob/mcp.json` (or the MCP tab in the UI). Added `scripts/install-bob-skill.sh` to
  copy the skill into a project's (or global `~/.bob/skills/`) skills directory, and documented the
  Quarkus Agents MCP + context7 setup as a `.bob/mcp.json` entry
  (`jbang quarkus-agent-mcp@quarkusio`, `npx -y @upstash/context7-mcp`). The Quarkus Agents MCP is a
  standalone MCP server whose docs list IBM Bob as a supported client.
- **Fixed the Codex setup commands.** Replaced `codex plugin add`, which was not available in the
  Codex version targeted at the time, with installing the plugin from the `/plugins` list after
  `codex plugin marketplace add`, and switched the Quarkus Agents MCP from a (non-existent) Codex
  plugin to `codex mcp add quarkus-agent -- jbang quarkus-agent-mcp@quarkusio`. Added a "Try it"
  step for parity.
- `AGENTS.md` is now the shared conventions file for both Codex and Bob; `README.md` and
  `CONTRIBUTING.md` updated to drop `BOB.md` / `.bob-plugin/` and reflect the per-agent install paths.
- All version headers synchronized to 0.7.0.

## v0.6.0 — 2026-06-03
- Slimmed `pom.xml.template` from a full pom to a dependency reference. The project shell (platform
  BOMs, build plugins, the `-parameters` flag, the `native` profile, the test stack, version pins) is
  generated up to date by `quarkus_create` — the same codestart generator behind code.quarkus.io — so
  hand-maintaining it only caused drift (see v0.5.0). The template now keeps only what generators do
  not provide: the curated extension list and the non-extension `dev.langchain4j` deps (embedding
  model, PDF parser). Updated `SKILL.md` §3 and the `VALIDATING-TEMPLATES.md` reconcile step to match.
- All version headers synchronized to 0.6.0.

## v0.5.0 — 2026-06-03
- Switched the generated REST JSON serializer from JSON-B to Jackson
  (`quarkus-rest-jsonb` → `quarkus-rest-jackson`): `pom.xml.template`, the §3 REST convention in
  `CLAUDE.md` / `AGENTS.md` / `BOB.md`, the `SKILL.md` dependency baseline, and the
  `docs/VALIDATING-TEMPLATES.md` extension list. Jackson is the Quarkus default JSON serializer,
  confirmed via the Quarkus Agents MCP against the `rest-json` guide. The Java templates use plain
  records (no JSON-B annotations), so no code changes were required.
- Reconciled the `pom.xml.template` platform baseline `3.36.0` → `3.36.1` to match the current
  Quarkus platform (verified via `quarkus_create`); all 14 template files compile against it.
- All version headers synchronized to 0.5.0.

## v0.4.0 — 2026-06-03
- Added native Bob support alongside the existing Claude and Codex support: `BOB.md`,
  `.bob-plugin/plugin.json`, and Bob-specific plugin metadata for the scaffolding skill.
- README: documented Bob prerequisites, plugin installation, and the relationship between
  `BOB.md`, `CLAUDE.md`, `AGENTS.md`, and the shared scaffolding skill.
- CONTRIBUTING: updated ownership and versioning guidance to include Bob in the list of supported
  agents.
- All version headers synchronized to 0.4.0 across `README.md`, `CLAUDE.md`, `AGENTS.md`,
  `BOB.md`, `SKILL.md`, and all plugin manifests.


## v0.3.0 — 2026-06-03
- Added native Codex support alongside the existing Claude support: `AGENTS.md`,
  `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`, a non-duplicating
  `plugins/quarkus-agentic/` marketplace wrapper, and Codex app metadata for the scaffolding
  skill.
- README: documented Codex prerequisites, plugin installation, and the relationship between
  `AGENTS.md`, `CLAUDE.md`, and the shared scaffolding skill.
- CONTRIBUTING: updated ownership and versioning guidance so future changes keep Claude and Codex
  surfaces in sync.

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
