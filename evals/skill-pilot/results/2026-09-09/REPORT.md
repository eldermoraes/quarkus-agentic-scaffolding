# Pilot result: inconclusive

All 12 authorized Codex executions completed, but none generated Java. Five attempts stopped
because Quarkus documentation search required unavailable Docker/Podman; seven stopped after
Context7 returned “Monthly quota exceeded.” These are prerequisite failures, so the pilot does
not estimate the skill's effectiveness. A zero observed difference here is not evidence of parity.

| Task | Baseline successful generation | With skill successful generation |
| --- | --- | --- |
| Classifier | 0/2 | 0/2 |
| Parallel workflow | 0/2 | 0/2 |
| Easy RAG | 0/2 | 0/2 |
| Total | 0/6 | 0/6 |

Both arms scored 0/48 on the frozen presence checklist because no implementation was produced.
The independent compiler passed all 12 unchanged starters; **that is not successful generation**.
No attempt timed out. No attempts were retried, replaced, or excluded.

## Evidence

- Frozen protocol/scorer revision: `2237dd1e7e4f73e93bedade13e49abbc434813a4`.
- [Raw metric records](results.json), [environment metadata](environment.json), and
  [sanitized tool-failure/input audit](audit.json) preserve every attempt.
- Each treatment run read the supplied skill; no baseline run read it. All output POM hashes
  match, and all runs have zero Java files. Sources/conventions stayed unchanged during collection.
- `infrastructure_error` in the frozen runner only detects process-start failures (exit 127);
  it does not identify documentation-service failures. The separately published audit classifies
  those from actual MCP responses without rewriting the original metric records.
- CLI-reported tokens: baseline 563,635 input (416,000 cached) and 2,649 output; treatment
  982,635 input (792,320 cached) and 3,772 output. These are observed cumulative usage counters,
  not dollar costs or distinct context lengths. Existing ChatGPT quota was used.
- Raw event logs remain local because they can contain environment details and tool output.
  No generated Java artifact exists to publish.

## What changes before another collection

Connectivity alone was an insufficient preflight. The runner now exercises both documentation
capabilities before starting any model execution, records a failed preflight as **collection not
started**, and snapshots tracked inputs from one commit with hashes. These safeguards were added
**after** this pilot; they do not retroactively change its protocol or results. Restore the required
documentation services and obtain a new execution budget before collecting another sample.

Issue #6 remains open: the reproducible harness and this failed pilot are published, but a valid
comparison still requires functioning prerequisites. No effectiveness badge or positive claim is
supported by these results.
