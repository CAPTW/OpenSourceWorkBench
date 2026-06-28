# Development Workflow

This document defines the local development workflow for OpenSolver Workbench
(OSW) v0.1. It is intentionally conservative: every feature starts from a clean
Git state, every risky step has a checkpoint, and every merge into `develop`
passes review and QA.

## Operating Principles

- Keep `develop` clean. Feature and amend work happens in sibling worktrees
  under `../_worktrees/`.
- Prefer small, reviewable phase-step changes over broad repository sweeps.
- Record evidence before claiming completion: command output, changed files,
  review decisions, and remaining risks.
- Keep unit tests network-free and solver-free. External solvers are optional
  integration concerns, never default smoke-test requirements.
- Treat scope guardrails as hard requirements. Native commercial CAD import,
  Simulink or `.mlapp`, full OpenFOAM UI coverage, industrial certification,
  and GUI direct subprocess solver execution are out of v0.1 scope.
- Do not push, force-push, delete branches, remove worktrees, or use
  destructive recovery commands unless the maintainer explicitly requests the
  exact operation.

## Reviewable Development Loop

1. Read the project anchor, current docs, and local Git state.
2. Convert the requested work into a bounded task card.
3. Start or confirm a clean `feature/osw-*` worktree from `develop`.
4. Implement only the allowed scope for that phase-step.
5. Run fast QA and record the evidence.
6. Create a local checkpoint commit before review.
7. Review against scope, architecture, tests, safety, and docs.
8. If required, create an `amend/osw-*` worktree from the review checkpoint.
9. Commit amend changes and compare against the review checkpoint.
10. Merge to `develop` only through the merge gate, normally as one squash
    commit.

## QA Script Plan

The QA layer should be simple enough to run frequently and strict enough to
catch drift before review.

| Script | Purpose |
| --- | --- |
| `tools/qa/run_fast_qa.py` | Run `python -m osw.cli --version`, `python -m osw.cli doctor`, `ruff check src tests`, and `pytest tests/unit -q` when safe. |
| `tools/qa/check_scope_drift.py` | Scan changed docs and code for out-of-scope claims or forbidden product directions. |
| `tools/qa/check_architecture_boundaries.py` | Check dependency boundaries, optional extras, plugin seams, and GUI/solver separation. |
| `tools/qa/check_plugin_manifests.py` | Check plugin manifest completeness when manifests exist. |
| `tools/qa/check_git_clean.py` | Report branch and dirty state for gate evidence. |
| `tools/qa/check_no_solver_artifacts_committed.py` | Detect solver/runtime artifact paths in staged or changed files. |
| `tools/qa/run_pre_merge_qa.py` | Combine fast QA, scope drift, architecture, and artifact checks for merge gate use. |

Missing optional external tools must be reported explicitly rather than treated
as hidden success.

## Task Card Template

Every phase-step should be reducible to this template:

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

The task card is the source of truth for diff scope. Anything outside it must
be stopped, parked, or deferred.

## Review, Amend, Merge Loop

Review is a gate, not a style pass. The reviewer scores the checkpoint and
lists required fixes, allowed amend files, and commands to rerun. Required
fixes are applied in an `amend/osw-*` branch or amend worktree created from
the review checkpoint. The amend report must compare changed files and command
results against that checkpoint.

Merge to `develop` is allowed only when:

- Review score and decision meet the thresholds in `docs/06_review_protocol.md`.
- Required fixes are complete or explicitly waived with a valid reason.
- Source and target worktrees are clean.
- The diff stays inside the task card.
- Fast or pre-merge QA passes, or skipped checks have valid local reasons.
- No runtime artifacts, generated junk, secrets, or forbidden claims are in the
  diff.

The default merge shape is a single squash commit on `develop`.

## Drift Recovery

Drift means the work has moved outside the task card, the v0.1 scope, or the
local Git safety rules. Recovery should preserve evidence before changing
anything.

1. Stop feature work and record the drift.
2. Run `git status --short` and classify files.
3. Save a rescue patch with `tools/git/rescue_dirty_worktree.py --write` when
   available.
4. Move unrelated ideas to a decision-log entry, risk item, or future task card.
5. Continue only with the allowed subset, or block and report the exact reason.

Do not use `git reset --hard`, `git clean`, branch deletion, or worktree
removal as drift recovery.

## Git Worktree Workflow

The canonical flow is:

```text
develop
  -> feature/osw-<phase-step>
      -> checkpoint before review
      -> optional amend/osw-<phase-step>-review-<n>
  -> squash merge back to develop after gate approval
```

Use `../_worktrees/osw-<phase-step>` for feature worktrees and
`../_worktrees/osw-amend-<phase-step>-review-<n>` for amend worktrees. Existing
branches and worktree paths must never be overwritten.

## Release Gate

The release gate is stricter than the merge gate. A v0.1 release candidate must
show:

- All release checklist items in `docs/10_release_checklist.md` are complete or
  explicitly deferred.
- Validation matrix entries are current and do not overclaim solver coverage.
- Examples are small, educational, and free of committed runtime junk.
- Package metadata, README, docs, license, and non-goals are aligned.
- Unit tests and selected integration/golden/validation checks pass in the
  documented environment.
- No public claim implies industrial certification or compatibility with
  forbidden native/proprietary workflows.
