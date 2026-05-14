# Review: OSW-AUTO-038_CI_CD

## Review Score

95/100

## Decision

Approve. Merge is possible with no required amend items.

## Scope Review

- The diff is limited to CI workflow configuration, local CI documentation,
  release checklist references, pytest marker metadata, optional integration
  test markers, focused workflow tests, and required Codex reports.
- No feature implementation, solver adapter implementation, GUI execution path,
  or external solver automation was introduced.
- No scope drift into Simulink, `.mlapp`, commercial native CAD import, full
  OpenFOAM UI, full solver coverage, or industrial certification claims was
  found.

## CI / Workflow Review

- `.github/workflows/ci.yml` defines a local-safe GitHub Actions workflow.
- The workflow installs only `.[dev]`, then runs CLI smoke, Ruff, unit tests,
  local-safe integration smoke, golden tests, validation tests, fast QA, scope
  drift, architecture boundary, and solver artifact checks.
- Optional external solver tests are disabled by default using
  `pytest tests/integration -q -m "not external_solver"`.
- Optional type checking is opt-in through `OSW_RUN_TYPE_CHECK=1`.
- Documentation link and license notice checks are present as placeholders,
  with clear skip behavior for the missing docs-link tool.

## Test / Marker Review

- `external_solver` and `optional_dependency` pytest markers are registered in
  `pyproject.toml`.
- Real `ccx` and GNU Octave integration tests are marked `external_solver`.
- Optional mesh/Chemistry integration tests are marked `optional_dependency` and
  remain skip-safe when optional Python extras are missing.
- Focused unit tests verify workflow parsing when PyYAML is available, expected
  CI commands, marker registration, and README documentation.

## Documentation Review

- README now documents local CI commands and the opt-in external solver
  integration command.
- Release checklist now references CI workflow presence, local-safe integration
  smoke, external-solver exclusion, and README command documentation.
- Wording distinguishes optional dependency availability from base workflow
  readiness and does not imply external solvers are installed by default.

## QA Evidence Review

- PyYAML workflow parse command: passed locally.
- `pytest tests/unit/test_ci_workflow.py -q`: `3 passed`.
- `pytest tests/integration -q -m "not external_solver"`:
  `4 passed, 3 skipped, 3 deselected`.
- `ruff check src tests`: passed.
- `pytest tests/unit -q`: `216 passed, 3 skipped`.
- `pytest tests/golden -q`: `10 passed`.
- `pytest tests/validation -q`: `4 passed`.
- `python tools/qa/run_fast_qa.py`: passed.
- `python tools/qa/check_scope_drift.py`: passed.
- `python tools/qa/check_architecture_boundaries.py`: passed.
- `python tools/qa/check_no_solver_artifacts_committed.py`: passed.
- `python tools/qa/check_plugin_manifests.py`: passed.
- `git diff --check`: passed.

## Required Amend Items

None.

## Low Findings

- Workflow syntax validation in CI is currently conditional on PyYAML being
  available. Local PyYAML validation passed, and focused tests cover this path
  when PyYAML is available. This is not a blocker, but a future CI hardening
  step could add a dedicated action lint or guaranteed YAML parser dependency.

## Hard Blocker Review

No hard blockers found. The change does not introduce default external solver
execution, mandatory heavy optional dependencies, secrets, generated runtime
artifacts, forbidden scope drift, destructive Git operations, or invalid
workflow YAML.

## Final Merge Recommendation

Squash merge `feature/osw-p12-1-ci-cd` into `develop` with the approved message
`ci: add local-safe GitHub Actions workflow` after pre-merge QA remains green.
