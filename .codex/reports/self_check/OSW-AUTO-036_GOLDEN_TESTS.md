# Self-Check: OSW-AUTO-036_GOLDEN_TESTS

## Step ID

OSW-AUTO-036_GOLDEN_TESTS

## Branch / Worktree

- Branch: `feature/osw-p11-2-golden-tests`
- Worktree: `C:\Users\USER\source\repos\_worktrees\osw-p11-2-golden-tests`
- Base branch: `develop`

## Files Changed

- `docs/04_validation_matrix.md`
- `tests/AGENTS.md`
- `tests/golden/__init__.py`
- `tests/golden/conftest.py`
- `tests/golden/helpers.py`
- `tests/golden/test_golden_helpers.py`
- `tests/golden/calculix/test_calculix_cantilever_golden.py`
- `tests/golden/mesh/export_artifact_summary.json`
- `tests/golden/mesh/test_mesh_export_contract.py`
- `tests/golden/openfoam/test_openfoam_cavity_golden.py`
- `tests/golden/openfoam/duct/test_openfoam_duct_golden.py`
- `tests/golden/plugins/plugin_health_records.json`
- `tests/golden/plugins/test_plugin_manifest_health_golden.py`
- `tests/golden/report/required_sections.txt`
- `tests/golden/report/test_report_html_golden.py`
- `tests/golden/su2/test_su2_cfg_golden.py`
- `.codex/reports/self_check/OSW-AUTO-036_GOLDEN_TESTS.md`

## Scope Summary

Implemented a small golden comparison system for deterministic text and JSON
fixtures. Existing CalculiX, OpenFOAM, mesh, report, and SU2 golden tests now use
shared helpers for normalized comparisons and readable unified diffs. Added
fixtures for mesh export summary, report required sections, and plugin health
output from manifest validation data.

No product implementation, solver adapter, runner, GUI, dependency, or example
executable assets were changed.

## Golden Coverage Summary

- Generated CalculiX input deck comparison uses normalized text diffs.
- OpenFOAM cavity and duct case-file comparisons use normalized text diffs and
  path replacement hooks.
- Mesh export artifact summary is checked against a JSON fixture.
- Report required sections are checked against a text fixture and stable order.
- Plugin manifest health output is checked against a JSON fixture without
  executing plugin code.
- Helper tests cover path/timestamp normalization and readable diff output.

## Commands Run

- `git status --short`
- `git branch --show-current`
- `git worktree list`
- `git show-ref --verify --quiet refs/heads/develop`
- `pytest tests/golden -q`
- `ruff check tests/golden tests/AGENTS.md docs/04_validation_matrix.md`
- `ruff check src tests --fix`
- `pytest tests/unit -q`
- `ruff check src tests`
- `python tools/qa/run_fast_qa.py`
- `python tools/qa/check_scope_drift.py`
- `python tools/qa/check_architecture_boundaries.py`
- `python tools/qa/check_no_solver_artifacts_committed.py`
- `python tools/qa/check_plugin_manifests.py`
- `git diff --check`

## Command Results

- Preflight: base worktree clean, current branch `develop`, `develop` exists.
- Feature worktree created on `feature/osw-p11-2-golden-tests`.
- Initial `pytest tests/golden -q` failed because imports used
  `tests.golden.helpers` while `tests` is not a package. Fixed with a
  golden-suite `conftest.py` and local `helpers` imports.
- `ruff check tests/golden tests/AGENTS.md docs/04_validation_matrix.md` failed
  because Ruff was intentionally invoked against Markdown paths by mistake.
  Corrected by running the project Ruff command.
- `ruff check src tests --fix` passed after fixing import ordering.
- `pytest tests/golden -q` passed: `10 passed`.
- `pytest tests/unit -q` passed: `202 passed, 3 skipped`.
- `ruff check src tests` passed.
- `python tools/qa/run_fast_qa.py` passed, including CLI version, doctor, Ruff,
  and unit tests.
- `python tools/qa/check_scope_drift.py` passed.
- `python tools/qa/check_architecture_boundaries.py` passed.
- `python tools/qa/check_no_solver_artifacts_committed.py` passed.
- `python tools/qa/check_plugin_manifests.py` passed.
- `git diff --check` passed.

## Skipped Checks

No required checks were skipped.

## Remaining Risks

- Golden fixtures protect stable contracts and generated text/JSON structure;
  they do not prove external solver numerical validity.
- The helper intentionally normalizes timestamps when used, so tests must only
  apply it where timestamp volatility is expected.
- Plugin health golden output uses a deterministic missing dependency and
  missing executable fixture; it does not execute or validate real plugins.

## Merge Recommendation

Recommend review and merge if the review score is at least 90 with no hard
blockers. The diff is test/documentation scoped and all required checks pass.
