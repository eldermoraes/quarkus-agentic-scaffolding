# Scaffold skill pilot (retired)

The pilot ran 12 Codex executions (three component tasks, two repetitions, a baseline arm and an
arm that also read `scaffold-project`) to measure what the skill adds when the project
conventions are already supplied.

It is retired. Its only collection, on 2026-09-09, was inconclusive: documentation prerequisites
failed in every run and no attempt generated Java, so it says nothing about the skill's
effectiveness. The [effectiveness eval](../effectiveness/README.md) supersedes it and does not
use any of its files.

## Published results

The record stays in the repository, unchanged, under [`results/2026-09-09/`](results/2026-09-09/):
the [report](results/2026-09-09/REPORT.md), the raw metric records, the environment metadata and
the tool-failure audit. These files mention the pilot's runner, tasks and starter project, which
are no longer here.

Everything under `evals/` is a record of what a run used and produced. `renovate.json` lists
`evals/**` in `ignorePaths`, so dependency updates never rewrite published results or a build
file a future eval checks in.

## Getting the inputs back

The annotated tag `eval-pilot-2026-09-09` (commit `2237dd1`) holds the protocol as it was frozen
for the published run: this README, `run.py`, `tasks.json`, `starter/pom.xml` and the scorer's
test, `ci/test_eval_scoring.py`. It is the
`source_commit` recorded in `results/2026-09-09/environment.json`, and its `tasks.json` and starter
POM match the hashes recorded there and in `audit.json`.

```sh
git show eval-pilot-2026-09-09:evals/skill-pilot/run.py
git checkout eval-pilot-2026-09-09   # the whole tree as the pilot ran it
```

The documentation preflight (`preflight.py`, tested by `ci/test_eval_preflight.py`) and the input
snapshotting in `run.py` were added after the pilot and never ran in a published collection. The last revision with every
runnable file in its final form is `v0.25.0` (commit `969dea2`).
