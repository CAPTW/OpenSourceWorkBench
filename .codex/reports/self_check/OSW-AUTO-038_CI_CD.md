# Self-Check: OSW-AUTO-038_CI_CD

## Step ID

OSW-AUTO-038_CI_CD

## Branch / Worktree

- Branch: `feature/osw-p12-1-ci-cd`
- Worktree: `C:\Users\USER\source\repos\_worktrees\osw-p12-1-ci-cd`
- Base branch: `develop`

## Files Changed

- `.github/workflows/ci.yml`
- `README.md`
- `docs/10_release_checklist.md`
- `pyproject.toml`
- `tests/integration/test_calculix_runner_optional.py`
- `tests/integration/test_cantera_optional.py`
- `tests/integration/test_gmsh_adapter_optional.py`
- `tests/integration/test_mesh_import_meshio.py`
- `tests/integration/test_mscript_figure_capture_optional.py`
- `tests/integration/test_octave_runner_optional.py`
- `tests/unit/test_ci_workflow.py`
- `.codex/reports/self_check/OSW-AUTO-038_CI_CD.md`

## Scope Summary

Added a local-safe GitHub Actions workflow for OSW v0.1 CI. The workflow installs
only the base development extra, runs lint, unit tests, integration smoke with
external-solver tests excluded, golden tests, validation tests, OSW QA checks,
and placeholder docs/license/type-check steps. It does not install or execute
external solvers by default.

## CI Coverage Summary

- Lint: `ruff check src tests`
- Optional type check: opt-in only with `OSW_RUN_TYPE_CHECK=1`
- Unit tests: `pytest tests/unit -q`
- Integration smoke: `pytest tests/integration -q -m "not external_solver"`
- Golden tests: `pytest tests/golden -q`
- Validation tests: `pytest tests/validation -q`
- QA gates: fast QA, scope drift, architecture boundaries, solver artifact scan
- Placeholders: docs link check if tool is present; license metadata check

## Commands Run

- `git status --short`
- `git branch --show-current`
- `git worktree list`
- `git show-ref --verify --quiet refs/heads/develop`
- `python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('.github/workflows/ci.yml').read_text())"`
- `pytest tests/unit/test_ci_workflow.py -q`
- `pytest tests/integration -q -m "not external_solver"`
- `ruff check src tests`
- `pytest tests/unit -q`
- `pytest tests/golden -q`
- `pytest tests/validation -q`
- `python tools/qa/run_fast_qa.py`
- `python tools/qa/check_scope_drift.py`
- `python tools/qa/check_architecture_boundaries.py`
- `python tools/qa/check_no_solver_artifacts_committed.py`
- `python tools/qa/check_plugin_manifests.py`
- `git diff --check`
- Local license metadata check through `pyproject.toml`

## Command Results

- Preflight: base worktree clean, current branch `develop`, `develop` exists.
- Feature worktree created on `feature/osw-p12-1-ci-cd`.
- PyYAML workflow parse: passed.
- Focused CI workflow tests: `3 passed`.
- Local-safe integration smoke: `4 passed, 3 skipped, 3 deselected`.
- `ruff check src tests`: passed after import ordering fix in
  `tests/unit/test_ci_workflow.py`.
- `pytest tests/unit -q`: `216 passed, 3 skipped`.
- `pytest tests/golden -q`: `10 passed`.
- `pytest tests/validation -q`: `4 passed`.
- `python tools/qa/run_fast_qa.py`: passed, including CLI smoke, Ruff, and unit tests.
- `python tools/qa/check_scope_drift.py`: passed.
- `python tools/qa/check_architecture_boundaries.py`: passed.
- `python tools/qa/check_no_solver_artifacts_committed.py`: passed.
- `python tools/qa/check_plugin_manifests.py`: passed.
- `git diff --check`: passed.
- Local license metadata check: passed.

## Skipped Checks

- `tools/qa/check_docs_links.py`: skipped because the tool is not present.
- Local markdown link/content check: skipped because no project command exists
  for this in `tools/qa`.
- Optional external solver tests: excluded from default CI and local smoke by
  `-m "not external_solver"`.
- Optional type check: disabled by default; workflow runs it only when
  `OSW_RUN_TYPE_CHECK=1`.

## Remaining Risks

- GitHub Actions was validated locally by YAML parsing and command-level tests;
  it was not executed on GitHub from this environment.
- Docs link and license notice checks are placeholders until dedicated project
  tools exist.
- Optional solver and heavy optional dependency tests remain local opt-in and
  are not release blockers for the base CI path.

## Merge Recommendation

Recommend review and merge if the review score is at least 90 with no hard
blockers. The change is limited to CI workflow, local command documentation,
pytest marker metadata, optional integration test markers, and focused workflow
tests.
