# Skill effectiveness eval

Does installing the `scaffold-project` skill change what a coding agent produces? This eval runs
five fixed tasks, each in two arms (baseline / with the skill) and three repetitions: 30 headless
`claude -p` runs, scored mechanically. Results live under [`results/`](results/).

## Arms

Both arms are identical except for one flag:

| | Baseline | Skill |
| --- | --- | --- |
| Starting point | empty directory outside the repository | same |
| Model | `claude-sonnet-5-5` (Claude Code CLI, subscription login, no API key) | same |
| MCP servers | Quarkus Agents MCP + context7, at the README pins (`--strict-mcp-config`) | same |
| Settings, user skills, plugins, `CLAUDE.md` | none (`--setting-sources ''`) | same |
| Permissions | `--permission-mode acceptEdits` + a fixed `--allowedTools` list | same |
| Skill | — | `--plugin-dir` with a plugin containing only `scaffold-project` and its templates, copied from the committed revision |

The exact command for every run is printed by `--dry-run`. In short:

```sh
claude -p "$PROMPT" --model claude-sonnet-5-5 --output-format stream-json --verbose \
  --setting-sources '' --strict-mcp-config --mcp-config mcp.json \
  --permission-mode acceptEdits --allowedTools "$ALLOWED" \
  [--plugin-dir plugin]          # skill arm only
```

`mcp.json` registers `jbang --java 21+ io.quarkus:quarkus-agent-mcp:<pin>:runner` and
`npx -y @upstash/context7-mcp@<pin>`, with the pins read from the top-level README.

**Isolation is asserted per run, not assumed.** The machine that collected the results has the
skill installed globally (plugin and skills CLI). An isolated `CLAUDE_CONFIG_DIR` was not usable
because the subscription login lives in the default configuration, so isolation comes from
`--setting-sources ''` (no user, project or local settings, so no user skills, plugins, or memory
files) and `--strict-mcp-config`. The runner reads each run's `init` event: a baseline run that
lists any `scaffold`/`quarkus-agentic` skill or plugin, or a skill run that does not list it, is
marked `invalid_isolation` and excluded from the aggregates (and still reported).

The skill is not named in the prompt. It triggers the way it does for a user, from its
description; how often it fired is reported (`skill_invoked`).

## Tasks

[`tasks.json`](tasks.json) holds a fixed preamble plus five task prompts, written as a user would
ask (what to build, not which conventions to follow):

1. `classifier`: LLM ticket classifier behind `POST /classify`.
2. `parallel`: two reviewer agents running in parallel, combined into one report.
3. `rag`: question answering over a local Markdown folder.
4. `mcp-server`: order-lookup operations exposed to remote MCP clients and to an LLM assistant.
5. `tools`: tool-calling support assistant with per-conversation memory.

The preamble is identical in both arms. It fixes only mechanical parameters (output directory
`./app`, `groupId`, `artifactId`, Ollama as provider) and tells the agent that no human will answer.
Both the skill and the Quarkus MCP ask the user to confirm extensions before generating a
project; headless, that would end the run with a question and no code. This is a deviation from
real use.

## Scoring

All scoring is mechanical ([`score.py`](score.py)); no human or LLM judgment.

1. **Compiles.** The runner runs `mvn -B -ntp -DskipTests test-compile` itself, in the produced
   project, after the agent exits (5-minute limit). This is the same definition of "compiles" that
   [`ci/build-from-templates.sh`](../../ci/build-from-templates.sh) applies to the templates; the
   script itself generates projects from templates, so it cannot score an agent's project.
2. **Convention checks.** Presence/absence predicates derived from the conventions in
   [`CLAUDE.md`](../../CLAUDE.md) / [`AGENTS.md`](../../AGENTS.md), equal weight, Java comments and
   commented-out properties excluded. Two bands, reported separately:
   - **Agent-decided** (headline): nine common checks for every task — `@RegisterAiService`, a
     named model, a record DTO, `@InputGuardrails`, delimited external text in the prompt, no
     manual `ChatModel`/`AiServices` wiring, a `@QuarkusTest`, `%dev` request logging, Dev
     Services disabled — plus four task-specific checks (13 per run). See `tasks.json`.
   - **Generator** (context only): dual BOM import, no version pins on Quarkus/LangChain4j
     dependencies, `maven.compiler.release` ≥ 25, `-parameters`, `native` profile. A project
     generator supplies most of these, so they are kept out of the delta.
3. **Build attempts to green, at most 2.** `claude -p` exposes no reliable per-turn "error until
   green" signal, so the metric is: attempt 1 is the independent compile above; if it fails, the
   same session is resumed once (`--resume`) with the last 60 lines of compiler output and a
   10-minute limit, then attempt 2 compiles again. Convention checks are scored before any
   repair. The transcript also yields agent turns and failed build commands the agent ran itself.

A check passing means the convention's marker is present, not that the code is semantically
right. Several checks can be satisfied in ways the regex misses (for example, a named model
configured only in properties); the predicates are the same for both arms.

## Reproduce

Requirements: Claude Code CLI logged in, JDK 25, Maven, JBang, Node/npm, Python 3. Commit any
change to `evals/effectiveness/` or `skills/scaffold-project/` first (the runner refuses dirty
inputs). Then:

```sh
python3 evals/effectiveness/run.py --dry-run /tmp/qas-eval          # print the 30 commands
python3 evals/effectiveness/run.py /tmp/qas-eval                    # collect (new directory)
python3 evals/effectiveness/summarize.py /tmp/qas-eval \
  --export evals/effectiveness/results/$(date +%F)                  # aggregate and export
```

Options: `--tasks classifier,rag`, `--repetitions 1`, `--parallel 3`, `--timeout 900` (seconds per
agent run), `--repair-timeout 600`. `ANTHROPIC_API_KEY` and other `*API_KEY*`/`*TOKEN*`/`*SECRET*`
variables are stripped from every run. If the subscription reports a usage or rate limit, the
runner stops scheduling, keeps the partial results, and exits with code 2.

The export copies every run's record (`runs/*.json`), the environment, `summary.json`,
`SUMMARY.md`, and `artifacts.tar.gz` (prompts, stream-json transcripts, compile logs, and the
generated sources without `target/`), after a scan for credential-like strings.
