# OSW-AUTO-027_OPENFOAM_DUCT_TEMPLATE Self Check

## Scope

- Added a prepare-only internal duct flow template generator.
- Added a duct SolverAdapterPlugin that writes case files and returns a command preview only.
- Added patch-name validation warnings with default patch fallback.
- Added a minimal residual parser interface for common OpenFOAM residual log lines.
- Added focused unit tests and golden duct case fixtures.

## Files

- `src/osw/solvers/openfoam/__init__.py`
- `src/osw/solvers/openfoam/adapter.py`
- `src/osw/solvers/openfoam/case_generator.py`
- `src/osw/solvers/openfoam/residuals.py`
- `tests/unit/test_openfoam_duct.py`
- `tests/golden/openfoam/duct/**`

## TDD Evidence

- Initial focused run failed with missing imports for `OpenFoamDuctTemplateAdapter`
  and `OpenFoamDuctConfig`.
- After implementation, the focused duct suite passed.

## Checks

- `pytest tests\\unit\\test_openfoam_duct.py tests\\golden\\openfoam\\duct -q`
  - Passed: 6 passed.
- `pytest tests\\unit\\test_openfoam_case_generator.py tests\\unit\\test_openfoam_adapter.py tests\\golden\\openfoam\\test_openfoam_cavity_golden.py -q`
  - Passed: 7 passed.
- `ruff check src tests`
  - Passed.
- `python tools\\qa\\run_fast_qa.py`
  - Passed: 155 passed, 1 skipped.
- `python tools\\qa\\check_scope_drift.py`
  - Passed.
- `python tools\\qa\\check_architecture_boundaries.py`
  - Passed.
- `python tools\\qa\\check_no_solver_artifacts_committed.py`
  - Passed.
- `python tools\\qa\\check_plugin_manifests.py`
  - Passed.

## Notes

- No GUI files were changed.
- No OpenFOAM executable is invoked.
- Duct support is limited to case preparation, patch validation, golden fixtures,
  and residual-log parsing structure.
