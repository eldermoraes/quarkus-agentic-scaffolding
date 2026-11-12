# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues in
[`eldermoraes/quarkus-agentic-scaffolding`](https://github.com/eldermoraes/quarkus-agentic-scaffolding/issues).
Use the `gh` CLI for all operations.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> -R eldermoraes/quarkus-agentic-scaffolding --json number,title,body,labels,comments`. Use `--json`: with its output piped, plain `gh issue view <number> --comments` prints the comments only, without the issue body.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

A clone can carry more than one remote and no `gh` default repository, so add
`-R eldermoraes/quarkus-agentic-scaffolding` to every command above (or run `gh repo set-default`
once) instead of relying on `gh` to infer the repo from `git remote -v`.

## Labels

Labels in use (`gh label list`). [`triage-labels.md`](triage-labels.md) maps the triage roles
of `/triage` to them.

- `needs-triage`: not yet looked at by a maintainer.
- `needs-info`: waiting on the reporter for more information.
- `ready-for-human`: specified; needs a human to do or decide it.
- `ready-for-agent`: specified and ready for an agent to pick up: the ticket has its `/to-spec`
  spec. A ticket filed without a spec does not carry it.
- `bug`, `enhancement`, `documentation`: the category of the change.
- `ecosystem`: opened by a scheduled workflow when an upstream release needs review.
- `build failed`: opened and closed by a scheduled workflow that tracks a failing template build
  or link check.
- GitHub's defaults: `duplicate`, `good first issue`, `help wanted`, `invalid`, `question`,
  `wontfix` (also the triage role for work that will not be done).

## Tickets and specs

A ticket body follows the `/to-tickets` issue template: `## What to build`,
`## Acceptance criteria`, `## Blocked by`. Its `/to-spec` spec, when it has one, is posted as the
**first comment** on the same issue (it starts with `# Spec`), so the read command above returns
the ticket in `body` and the spec in `comments[0].body`.

## Security and privacy findings

Never file a security or privacy finding as a public issue. [`SECURITY.md`](../../SECURITY.md)
asks for vulnerabilities to be reported privately through a GitHub security advisory; this repo
handles privacy findings the same way. The maintainer's practice is a draft advisory whose
description holds the ticket and its spec. A public ticket that depends on it refers to it only as
"a private security advisory".

## Pull requests

A pull request links its issue with `Closes #<number>` and follows
[`CONTRIBUTING.md`](../../CONTRIBUTING.md): the change is recorded in `CHANGELOG.md` under
`## Unreleased`, and no version is bumped.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; `/triage` reads this flag.)_

When set to `yes`, PRs run through the same labels and states as issues, using the `gh pr` equivalents:

- **Read a PR**: `gh pr view <number> --comments` and `gh pr diff <number>` for the diff.
- **List external PRs for triage**: `gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments` then keep only `authorAssociation` of `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, or `NONE` (drop `OWNER`/`MEMBER`/`COLLABORATOR`).
- **Comment / label / close**: `gh pr comment`, `gh pr edit --add-label`/`--remove-label`, `gh pr close`.

GitHub shares one number space across issues and PRs, so a bare `#42` may be either: resolve with `gh pr view 42` and fall back to `gh issue view 42`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> -R eldermoraes/quarkus-agentic-scaffolding --json number,title,body,labels,comments`.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets.

- **Map**: a single issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body. `gh issue create --label wayfinder:map`.
- **Child ticket**: an issue linked to the map as a GitHub sub-issue (`gh api` on the sub-issues endpoint). Where sub-issues aren't enabled, add the child to a task list in the map body and put `Part of #<map>` at the top of the child body. Labels: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Once claimed, the ticket is assigned to the driving dev.
- **Blocking**: GitHub's **native issue dependencies**, the canonical, UI-visible representation. Add an edge with `gh api --method POST repos/eldermoraes/quarkus-agentic-scaffolding/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`, where `<blocker-db-id>` is the blocker's numeric **database id** (`gh api repos/eldermoraes/quarkus-agentic-scaffolding/issues/<n> --jq .id`, _not_ the `#number` or `node_id`). GitHub reports `issue_dependencies_summary.blocked_by` (open blockers only, the live gate). Where dependencies aren't available, fall back to a `Blocked by: #<n>, #<n>` line at the top of the child body. A ticket is unblocked when every blocker is closed.
- **Frontier query**: list the map's open children (`gh issue list --state open`, scoped to the map's sub-issues / task list), drop any with an open blocker (`issue_dependencies_summary.blocked_by > 0`, or an open issue in the `Blocked by` line) or an assignee; first in map order wins.
- **Claim**: `gh issue edit <n> --add-assignee @me`, the session's first write.
- **Resolve**: `gh issue comment <n> --body "<answer>"`, then `gh issue close <n>`, then append a context pointer (gist + link) to the map's Decisions-so-far.

The `wayfinder:*` labels do not exist in this repo yet.
