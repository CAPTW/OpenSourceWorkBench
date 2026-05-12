# Review Protocol

OSW review protects scope, architecture, safety, and test evidence before work
is merged to `develop`. Reviewers should prioritize defects and risks over
style. A change with clean formatting but weak scope control should not pass.

## Required Inputs

- Task Card or prompt anchor.
- Changed file list and diff summary.
- Relevant docs, especially `docs/00_north_star.md`,
  `docs/08_scope_guardrails.md`, and `docs/05_harness_engineering.md`.
- QA command output, including skipped checks and reasons.
- Generated artifact classification.
- Checkpoint commit hash for feature or amend work.

## Review Order

1. Scope guardrails and v0.1 non-goals.
2. Architecture boundaries, optional extras, and plugin contracts.
3. Data safety, preview behavior, subprocess behavior, and validation messages.
4. Tests, golden fixtures, reproducibility, and command evidence.
5. Documentation accuracy, roadmap mapping, and public-facing claims.
6. Maintainability, naming, comments, and local style.

## Severity Levels

| Severity | Meaning | Required action |
| --- | --- | --- |
| Critical | Violates safety, secrets, destructive Git rules, forbidden scope, or could corrupt user/project data. | Blocks merge regardless of score. |
| High | Breaks a promised workflow, architecture boundary, CLI contract, or required test path. | Blocks merge until fixed or explicitly descoped. |
| Medium | Causes confusing behavior, weak validation, missing focused tests, or incomplete docs for touched behavior. | Usually requires amend before merge. |
| Low | Local clarity, maintainability, naming, or minor documentation issue. | May be fixed now or tracked. |

## Score Table

Start from zero and award points only for demonstrated evidence.

| Category | Points | Evidence expected |
| --- | ---: | --- |
| Scope alignment | 20 | Diff matches the Task Card and avoids forbidden v0.1 claims or features. |
| Architecture fit | 20 | Boundaries, optional dependencies, plugin contracts, and GUI/solver separation are respected. |
| Tests and QA | 20 | Required commands pass or have valid local skip reasons; meaningful tests cover changed behavior. |
| Safety and data handling | 15 | No secrets, runtime junk, destructive Git behavior, unsafe subprocess use, or data-loss risk. |
| Documentation and user claims | 15 | Docs, README, roadmap, and validation claims are accurate and aligned. |
| Maintainability | 10 | The implementation is small, readable, typed where useful, and consistent with local patterns. |

Maximum score: 100.

## Merge Thresholds

- `90-100`: Merge possible if no Critical or High issues remain and required
  QA evidence is present.
- `80-89`: Minor amend path. Merge is possible only after all required fixes
  are completed and rerun evidence is recorded.
- `70-79`: Major amend required. Do not merge; create or continue an amend
  worktree.
- `<70`: Blocked. Rework the task scope or implementation before another
  review.

Any Critical issue blocks merge regardless of numeric score. The following also
block merge regardless of score:

- Native SolidWorks, CATIA, NX, Creo, or other commercial native CAD direct
  import support.
- Simulink or `.mlapp` support.
- Full OpenFOAM solver coverage claims or broad solver UI coverage claims.
- Industrial certification claims.
- GUI direct subprocess solver execution.
- Committed secrets, tokens, credentials, or obvious solver runtime artifacts.
- Dirty source or target worktree at merge time.

## Review Output Format

```text
Decision:
Score:
Checkpoint:
Critical issues:
High issues:
Medium issues:
Low issues:
Required fixes:
Allowed amend files:
Required rerun commands:
Generated/runtime artifact check:
Residual risks:
```

Findings should include file paths and line references when possible.

## Amend Requirements

An amend pass must:

- Start from the review checkpoint or clearly state why it cannot.
- Change only the allowed amend files unless the reviewer updates the ticket.
- Address all required fixes.
- Rerun the commands requested by review.
- Write an amend report that compares the checkpoint with the amend commit.

Amend work should not expand product scope.

## Merge Gate Handoff

The merge gate may proceed only when the review decision is `Merge possible` or
`Minor amend then merge possible`, score thresholds are met, required fixes are
closed, source and target worktrees are clean, and pre-merge QA passes or has a
valid skip reason. The default merge result is one squash commit on `develop`.
