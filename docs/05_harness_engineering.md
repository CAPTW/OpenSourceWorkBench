# Harness Engineering

This document defines how Codex work should be run for OpenSolver Workbench
(OSW) v0.1. It is intentionally local-first: every feature starts from a clean
Git state, every risky step has a checkpoint, and every merge into `develop`
passes a review and QA gate. The harness exists to keep an educational and
research workbench from drifting into proprietary clone claims, unsafe solver
execution, or unreviewed generated artifacts.

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
  destructive recovery commands from Codex prompts unless the user explicitly
  requests the exact operation.

## End-to-End Codex Loop

1. Read the project anchor, current docs, and local Git state.
2. Convert the requested work into a bounded Task Card.
3. Start or confirm a clean `feature/osw-*` worktree from `develop`.
4. Implement only the allowed scope for that phase-step.
5. Run fast QA and record the evidence.
6. Create a local checkpoint commit before review.
7. Review against scope, architecture, tests, safety, and docs.
8. If required, create an `amend/osw-*` worktree from the review checkpoint.
9. Commit amend changes and compare against the review checkpoint.
10. Merge to `develop` only through the merge gate, normally as one squash
    commit.
11. Preserve reports under `.codex/reports/` for traceability.

## Agent Instruction Surfaces

### Root `AGENTS.md`

The root `AGENTS.md` is the repository-level contract. It should state:

- OSW mission and v0.1 non-goals.
- Architecture rules for plugins, project data models, optional dependencies,
  solver/importer boundaries, and GUI safety.
- Test rules for unit, integration, GUI, golden, and validation suites.
- Review rules, including evidence-first reporting and scope-drift blocking.
- Codex behavior: no push, no destructive Git, no secrets, and no feature work
  outside the active prompt.

### Directory AGENTS

Directory AGENTS files override only local concerns and must not conflict with
the root contract.

| Directory | Planned purpose |
| --- | --- |
| `src/osw/plugins/AGENTS.md` | Plugin metadata, entry points, capability declarations, and preview-first importer behavior. |
| `src/osw/solvers/AGENTS.md` | Solver adapter contracts, dry-run preparation, external execution boundaries, and result import expectations. |
| `src/osw/scripts/mscript/AGENTS.md` | MATLAB/Octave-compatible parsing and preview limits, excluding Simulink and proprietary toolbox compatibility. |
| `src/osw/gui/AGENTS.md` | GUI shell boundaries, preview behavior, and no direct solver subprocess execution. |
| `src/osw/mesh/AGENTS.md` | meshio/Gmsh-facing metadata, optional dependencies, and fixture discipline. |
| `src/osw/geometry/AGENTS.md` | Standard/exported geometry previews and no native commercial CAD import. |
| `src/osw/post/AGENTS.md` | ResultDataset/FigureDataset, visualization, report evidence, and no overclaims. |
| `tests/AGENTS.md` | Marker policy, no network in unit tests, no external solver execution by default, fixture size limits. |
| `tools/AGENTS.md` | Git and QA helper safety, non-destructive behavior, and clear exit codes. |
| `.codex/AGENTS.md` | Prompt catalog, report locations, and no secret-bearing MCP or connector output. |

## Skills

Skills are reusable local instructions, not product features. They live under
`.codex/skills/` and are used only when relevant to the active prompt.

| Skill | Responsibility |
| --- | --- |
| `architecture-review` | Review dependency direction, optional extras, plugin seams, and GUI/solver separation. |
| `plugin-contract` | Guide importer, solver, script, post-processing, and report plugin contracts. |
| `qa-review` | Run fast QA and summarize command evidence. |
| `amend-revise` | Isolate review fixes and compare against the checkpoint. |
| `scope-drift-recovery` | Stop and recover when work leaves v0.1 scope or the Task Card. |
| `git-worktree` | Start feature and amend worktrees safely from local branches. |
| `git-merge-gate` | Verify cleanliness, QA, review score, and squash merge readiness. |
| `dirty-worktree-recovery` | Preserve and classify dirty local changes before recovery. |

Each skill should include trigger conditions, required inputs, allowed files,
forbidden actions, command evidence, and output format.

## Hooks Plan

Tracked hooks are part of the harness but must remain conservative. They should
fail only on hard safety issues and should explain exactly what failed.

- `pre-commit`: run staged-file checks, secret-like pattern scans, generated
  artifact checks, and optional scope/architecture checkers if available.
- `pre-merge-commit`: run merge-gate checks before a merge commit or squash
  commit is finalized.
- Future hooks may check documentation links or prompt format, but should not
  require network access.

Hooks must not create secrets, add remotes, push, delete branches, delete
worktrees, or run external solvers.

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

## Sub-Agent Roles

Sub-agents may be useful for independent review or verification work when the
user explicitly asks for parallel agent work. They should receive bounded,
self-contained tasks with disjoint write scopes.

| Role | Output |
| --- | --- |
| Scope reviewer | Scope-drift findings against `docs/08_scope_guardrails.md`. |
| Architecture reviewer | Dependency, plugin, solver, importer, and GUI boundary findings. |
| QA verifier | Command results, reproduction notes, and test-gap summary. |
| Documentation reviewer | Claim accuracy, roadmap alignment, and decision-log coverage. |
| Security reviewer | Secret-like content, unsafe file handling, and subprocess risk findings. |
| Release gate reviewer | Release checklist status and blocker report. |

## Task Card Template

Every phase-step prompt should be reducible to this template:

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

The Task Card is the source of truth for diff scope. Anything outside it must
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
- The diff stays inside the Task Card.
- Fast or pre-merge QA passes, or skipped checks have valid local reasons.
- No runtime artifacts, generated junk, secrets, or forbidden claims are in the
  diff.

The default merge shape is a single squash commit on `develop`.

## Drift Recovery

Drift means the work has moved outside the Task Card, the v0.1 scope, or the
local Git safety rules. Recovery should preserve evidence before changing
anything.

1. Stop feature work and record the drift.
2. Run `git status --short` and classify files.
3. Save a rescue patch with `tools/git/rescue_dirty_worktree.py --write` when
   available.
4. Move unrelated ideas to a decision-log entry, risk item, or future Task Card.
5. Continue only with the allowed subset, or block and report the exact reason.

Do not use `git reset --hard`, `git clean`, branch deletion, or worktree
removal as drift recovery from Codex prompts.

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

## MCP Resource Plan

MCP resources should support traceability without becoming a hidden source of
truth. Planned resource categories:

- Prompt catalog entries for phase-step prompts and Git safety prompts.
- Report indexes for review, amend, merge, QA, and release evidence.
- Schema references for ProjectSchema, UnitSystem, MaterialDB, ResultDataset,
  and FigureDataset once implemented.
- Optional connector summaries for external issue trackers or documents, with
  secrets and credentials excluded.

Local repository files remain authoritative when MCP resources and local docs
conflict.

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
