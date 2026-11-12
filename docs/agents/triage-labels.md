# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual label strings used in this repo's issue tracker.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

`/triage` also uses two category roles. They map to labels of the same name:

| Label in mattpocock/skills | Label in our tracker | Meaning                             |
| -------------------------- | -------------------- | ----------------------------------- |
| `bug`                      | `bug`                | Something is broken                 |
| `enhancement`              | `enhancement`        | New feature or improvement          |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from this table.

All seven labels exist in `eldermoraes/quarkus-agentic-scaffolding` (`gh label list`), so apply
them; do not create new ones. In this repo `ready-for-agent` also means the ticket has its
`/to-spec` spec (see [`issue-tracker.md`](issue-tracker.md#labels)). The other labels in the
repo, such as `documentation`, are not triage roles.
