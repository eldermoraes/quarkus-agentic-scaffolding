# Bob MCP registration

Bob 2.0.0 ships `bob mcp add|add-json|list|remove`, so prefer the CLI over hand-writing JSON — it
writes the file Bob actually reads and `bob mcp list` is a real verification. Four things to know:
three the CLI enforces, one Bob's loader does.

- **Probe for the legacy file BEFORE the first `add` — this ordering is load-bearing.** Bob migrates
  `~/.bob/settings/mcp_settings.json` into `mcp.json` **only when `mcp.json` does not yet exist**.
  `bob mcp add -s global` creates `mcp.json`, so registering first blocks that migration
  permanently: on a machine whose global config still lives in the legacy file, our two servers land
  in a fresh `mcp.json` and **every other server the user configured silently stops loading**. So:
  if the legacy file exists and `mcp.json` does not, have the user start Bob once and let it migrate
  (it announces *"your global MCP configuration has been migrated to mcp.json"*), confirm the
  servers survived, and only then register. Never resolve this by copying files around yourself
  without showing the user both files first.
- **`--` before the server's own arguments is mandatory.** `bob mcp add … jbang --java 21+ <GAV>`
  fails with `error: unknown option '--java'`, because Bob parses the flag as its own. With the
  separator (`… jbang -- --java 21+ <GAV>`) the arguments land verbatim in the entry's `args`.
- **`add` never updates an existing entry — `add-json` does.** On a name that is already registered,
  `bob mcp add` exits 1 with `Error: MCP server "…" already exists in …` and leaves the old entry
  untouched, so an idempotent re-run cannot repair a stale registration through it — neither an
  unpinned `quarkus-agent` command nor the `context7` entry every version bump leaves behind. Use
  `bob mcp add-json`, which overwrites in place — still the CLI, so the file Bob reads stays the
  one being written. One form per server:
  `bob mcp add-json -s <scope> quarkus-agent '{"command":"jbang","args":["--java","21+","io.quarkus:quarkus-agent-mcp:1.2.6:runner"]}'`
  · `bob mcp add-json -s <scope> context7 '{"command":"npx","args":["-y","@upstash/context7-mcp@4.0.7"]}'`.
  Show the user the current entry and confirm before overwriting; `bob mcp remove` then `add`
  works too, but loses the entry if the add fails.
- **`-s global` is a scope decision — state it, never make it silently.** It writes
  `~/.bob/settings/mcp.json` (creating file and directory if needed) and registers the servers for
  **every workspace on the machine**, not just this project. That is this skill's default because
  the servers are tools, not conventions — they change nothing in projects that never call them —
  and re-registering per project is friction; but tell the user that is the scope they are getting,
  and offer `-s workspace` to anyone who mixes stacks and wants the registration confined to the
  current project. `-s workspace` (Bob's own default) writes `<project>/.bob/mcp.json` but does
  **not** create it — it exits with `Fatal error: ENOENT … .bob/mcp.json`. Seed it **only when it
  is missing**, because `>` truncates and an existing file holds the user's other servers:
  `[ -f .bob/mcp.json ] || { mkdir -p .bob && printf '{"mcpServers":{}}\n' > .bob/mcp.json; }`. At
  workspace scope the verify column reads `workspace`, and the legacy-migration probe in the first
  bullet still applies before any *global* add.
- **Never write `mcp_settings.json` yourself** (Bob's loader, not the CLI). A registration written
  there on a machine that already has `mcp.json` is silently ignored — it looks registered and Bob
  never loads it. Check `~/.bob/mcp.json` and `~/.bob/mcp_settings.json` too: one directory **above**
  the settings directory, where releases of this skill before v0.18.0 told agents to write. Bob reads
  neither and migrates neither, so a machine set up by an earlier run may hold a registration there
  that has never loaded. If you find one, report it and register through the CLI instead.

A same-named server at workspace scope overrides global, and a deeper `.bob/mcp.json` overrides a
shallower one in the same workspace. When something still fails to start, Bob's own log is the
evidence: `~/.bob/logs/shell/` — a `UnsupportedClassVersionError` there is the JDK trap from [setup §5](../SKILL.md#5-phase-b--mcp-registration-per-agent).

**No `bob` on PATH?** Probe with `command -v bob` before you plan the registration: a Bob-IDE-only
machine has no CLI, and the whole route above is unavailable. Then hand-write the file — global
`~/.bob/settings/mcp.json`, project `<project>/.bob/mcp.json` — read-modify-write so the user's
other servers survive, with the entries from [setup §5](../SKILL.md#5-phase-b--mcp-registration-per-agent) including `--java 21+`. Verify in the UI's **MCP**
tab, which lists what Bob actually loaded; that is the one verification that needs no binary.
Every rule above still applies: not the legacy name, not a truncating write, and Bob reloads
changed servers on its own.

