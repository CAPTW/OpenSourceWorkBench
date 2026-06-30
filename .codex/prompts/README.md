# OSW Prompt Catalog

This directory is reserved for reusable Codex prompt templates. HE-00 documents
the catalog only; actual prompt files are created in later harness prompts.

## Prompt Families

| Family | Purpose |
| --- | --- |
| `GIT-*` | Local Git bootstrap, baseline, worktree, checkpoint, amend, and merge gates. |
| `INIT-*` | Repository skeleton and environment bootstrap. |
| `P<phase>.*` | Product, architecture, core model, GUI, solver, importer, report, and validation phase work. |
| `HE-*` | Harness engineering, agents, skills, hooks, QA scripts, and prompt infrastructure. |
| `REVIEW-*` | Independent review prompts that score checkpoint commits. |
| `RELEASE-*` | Release checklist and release gate prompts. |

## Required Prompt Sections

Every prompt should include:

- Role.
- Project anchor.
- Required reads.
- Task.
- Allowed files.
- Forbidden files.
- Safety rules.
- Implementation requirements.
- Acceptance criteria.
- QA commands.
- Output format.
- Post-anchor stopping rule.

## Report Paths

Prompts should write evidence to the matching report directory when requested:

- Worktree start: `.codex/reports/worktrees/`
- Pre-review checkpoint: `.codex/reports/review/`
- Amend loop: `.codex/reports/amend/`
- Merge gate: `.codex/reports/merge/`
- Release gate: `.codex/reports/release/`

Reports should summarize commands, changed files, pass/fail status, skipped
checks, and remaining risks. They must not include secrets, tokens, credentials,
or large generated runtime artifacts.

## Task Card Header

Reusable prompts should map to the Task Card shape in
`docs/05_harness_engineering.md`:

```text
Task ID:
Title:
Base branch:
Feature branch:
Worktree path:
Goal:
Allowed files:
Forbidden files:
Required reads:
Scope guardrails:
Implementation requirements:
Acceptance criteria:
QA commands:
Generated artifact policy:
Review checklist:
Checkpoint message:
Expected report path:
Rollback or recovery point:
```

## Maintenance Rules

- Keep prompt templates concise and explicit.
- Prefer local repository context over external state.
- Do not embed credentials, API keys, tokens, or personal paths.
- Do not instruct Codex to push, force-push, delete branches, delete worktrees,
  or use destructive recovery commands.
- Update `docs/07_decision_log.md` when a prompt establishes a durable process
  decision.
