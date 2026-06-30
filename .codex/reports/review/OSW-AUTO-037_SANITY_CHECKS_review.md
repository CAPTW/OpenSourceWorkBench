# Review: OSW-AUTO-037_SANITY_CHECKS

## Review Score

95/100

## Decision

Approve after minor amend. The initial review scored 84/100 and required two
fixes. The amend branch resolves the required issues and introduces no hard
blockers.

## Scope Review

- Changes stay within the allowed validation, report generator, and focused
  test surfaces.
- No new physical models, solver execution, GUI subprocess paths, or
  certification claims were introduced.
- No Simulink, `.mlapp`, commercial native CAD, full OpenFOAM UI, or industrial
  validation scope drift was found.

## Docs / Report Review

- Report generator integration now computes lightweight project sanity messages
  by default when no explicit `sanity_report` is supplied.
- Sanity warnings are merged into the normal validation summary and report
  warning summary.
- Existing report and golden report tests remain stable.

## Checklist Completeness Review

- Negative density fails.
- Non-finite density fails.
- Nonpositive and non-finite viscosity fail.
- Zero mesh cells fail for both payload and reference metadata paths.
- Non-finite mesh metadata cell counts fail.
- Missing material assignments fail for structural domains and warn for
  nonstructural domains.
- Boundary condition completeness and solver convergence placeholders are
  surfaced as reportable validation messages.

## Wording / Safety Review

- Warnings describe lightweight sanity checks and avoid certification claims.
- Solver convergence handling is explicitly a recorded-status placeholder, not
  a solver log parser or runtime execution path.
- Optional report integration does not auto-run solvers or scripts.

## QA Evidence Review

- `pytest tests/unit/test_sanity_checks.py tests/validation -q`: passed,
  `15 passed`.
- `pytest tests/unit/test_report_generator.py tests/golden/report -q`: passed,
  `9 passed`.
- `ruff check src tests`: passed.
- `pytest tests/unit -q`: passed, `213 passed, 3 skipped`.
- `python tools/qa/run_fast_qa.py`: passed.
- `python tools/qa/check_scope_drift.py`: passed.
- `python tools/qa/check_architecture_boundaries.py`: passed.
- `python tools/qa/check_no_solver_artifacts_committed.py`: passed.
- `git diff --check`: passed.

## Required Amend Items

- Required: reject `NaN`/`inf` density and viscosity values.
  Status: complete with focused tests.
- Required: make sanity warnings appear through the normal report generator path
  instead of only by manually supplying `sanity_report`.
  Status: complete with focused report test and report/golden regression check.

## Hard Blocker Review

No hard blockers found. The change does not add GUI direct solver subprocess
execution, `.m` auto-run behavior, secrets, solver runtime artifacts, scope
drift, untested runner/parser changes, or destructive git operations.

## Final Merge Recommendation

Merge the amend branch into `develop` using the configured squash message after
the amend commit is created and pre-merge QA remains green.
