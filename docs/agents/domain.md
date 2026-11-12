# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

This repo is **single-context**. It has no `CONTEXT.md`, no `CONTEXT-MAP.md` and no `docs/adr/`:
its domain language and its decisions live in the files below.

## Before exploring, read these

- **`CLAUDE.md`** (and its twin **`AGENTS.md`**): the conventions this artifact ships to
  Quarkus + LangChain4j projects. They are the product, and they name its concepts (AI service,
  tool, agent, guardrail, named model, Easy RAG). Section 6 holds the maintenance override for
  this repo.
- **`CONTRIBUTING.md`**, section "What lives where": what each file and directory is for, and the
  rule that conventions belong in `CLAUDE.md` / `AGENTS.md` while the skills say how to lay
  things out.
- **`README.md`**: what the artifact is, the three skills (`setup-agentic-scaffolding`,
  `scaffold-project`, `audit-project`), install and uninstall per agent, and the file tree.
- **`CHANGELOG.md`**: the decision record. Each entry states what changed and the evidence
  behind it; read the entries that touch the area you work in.
- **`docs/`**: `AGENTIC-COMPENSATION.md` is a decision record (why compensation is not a default
  convention); `EVOLUTION-PLAN.md` and `FLOW-REDESIGN-PLAN.md` are dated audit plans whose facts
  carry an as-of date; `VALIDATING-TEMPLATES.md` says how to check that the templates still build
  and start.

If `CONTEXT.md` or `docs/adr/` appear later, read them too. Do not flag their absence; the
`/domain-modeling` skill creates them when a term or decision is actually resolved.

## File structure

```
/
├── CLAUDE.md, AGENTS.md        ← conventions (the product's vocabulary)
├── README.md, CONTRIBUTING.md
├── CHANGELOG.md                ← decision record
├── docs/                       ← decision record and dated plans
└── skills/                     ← the three skills and their templates
```

## Use the conventions' vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as `CLAUDE.md` uses it. Don't drift to synonyms.

## Flag decision conflicts

If your output contradicts a decision recorded in `CHANGELOG.md` or `docs/AGENTIC-COMPENSATION.md`, surface it explicitly rather than silently overriding:

> _Contradicts the decision in `docs/AGENTIC-COMPENSATION.md`, but worth reopening because…_
