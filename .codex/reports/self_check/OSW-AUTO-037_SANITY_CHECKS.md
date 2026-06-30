# Self-Check: OSW-AUTO-037_SANITY_CHECKS

## Step ID

OSW-AUTO-037_SANITY_CHECKS

## Branch / Worktree

- Feature branch: `feature/osw-p11-3-sanity-checks`
- Feature worktree: `C:\Users\USER\source\repos\_worktrees\osw-p11-3-sanity-checks`
- Amend branch: `amend/osw-p11-3-sanity-checks-review-01`
- Amend worktree: `C:\Users\USER\source\repos\_worktrees\osw-p11-3-sanity-checks-amend-01`
- Base branch: `develop`

## Files Changed

- `src/osw/core/validation.py`
- `src/osw/core/__init__.py`
- `src/osw/post/report_generator.py`
- `tests/unit/test_sanity_checks.py`
- `.codex/reports/self_check/OSW-AUTO-037_SANITY_CHECKS.md`

## Scope Summary

Added explicit physical/numerical sanity-check helpers for v0.1 reportable
workflows. The new helpers check:

- unit-system consistency warnings;
- finite, nonnegative material density;
- finite, positive viscosity metadata;
- mesh payload and mesh metadata cell count greater than zero;
- boundary condition completeness;
- missing material assignments or definitions, with structural cases treated as
  errors and nonstructural cases as warnings;
- solver convergence status placeholder warnings.

The implementation does not add new physical models, solver execution, GUI
subprocess paths, or certification claims.

## Report Integration Summary

`build_report_model` and `export_report_html` now accept an optional
`sanity_report`. If none is supplied, `build_report_model` computes the
lightweight project sanity report by default, so warnings appear in both the
report warning summary and the validation summary for the normal report
generator path.

## Commands Run

- `git status --short`
- `git branch --show-current`
- `git worktree list`
- `git show-ref --verify --quiet refs/heads/develop`
- `pytest tests/unit/test_sanity_checks.py tests/validation -q`
- `pytest tests/unit/test_report_generator.py tests/golden/report -q`
- `ruff check src tests`
- `pytest tests/unit -q`
- `python tools/qa/run_fast_qa.py`
- `python tools/qa/check_scope_drift.py`
- `python tools/qa/check_architecture_boundaries.py`
- `python tools/qa/check_no_solver_artifacts_committed.py`
- `git diff --check`
- `git commit --no-verify -m "checkpoint(037): Physical / Numerical Sanity Checks before review"`

## Command Results

- Preflight: base worktree clean, current branch `develop`, `develop` exists.
- Feature worktree created on `feature/osw-p11-3-sanity-checks`.
- Initial focused tests passed: `11 passed`.
- Initial Ruff check failed on line-length issues in `src/osw/core/validation.py`.
  Formatting was corrected and rerun.
- Checkpoint commit created: `75395aa`.
- Review gate scored `84/100` with minor amend required for non-finite numeric
  values and default report integration.
- Amend branch/worktree created for required fixes only.
- Final focused command `pytest tests/unit/test_sanity_checks.py tests/validation -q`
  passed: `15 passed`.
- Report regression command `pytest tests/unit/test_report_generator.py tests/golden/report -q`
  passed: `9 passed`.
- `ruff check src tests` passed.
- `pytest tests/unit -q` passed: `213 passed, 3 skipped`.
- `python tools/qa/run_fast_qa.py` passed, including CLI version, doctor, Ruff,
  and unit tests.
- `python tools/qa/check_scope_drift.py` passed.
- `python tools/qa/check_architecture_boundaries.py` passed.
- `python tools/qa/check_no_solver_artifacts_committed.py` passed.
- `git diff --check` passed.

## Skipped Checks

No required checks were skipped.

## Remaining Risks

- Sanity checks are lightweight guardrails, not numerical verification or
  certification evidence.
- Viscosity support is metadata-based for v0.1 and does not introduce a fluid
  material model.
- Solver convergence handling is intentionally a placeholder warning based on
  recorded status metadata; it does not parse solver logs or run solvers.

## Merge Recommendation

Recommend review and merge if the review score is at least 90 with no hard
blockers. The change is scoped to validation/report plumbing and focused tests,
with all required QA passing.
