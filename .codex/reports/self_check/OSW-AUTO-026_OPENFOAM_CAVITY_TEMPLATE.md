# OSW-AUTO-026_OPENFOAM_CAVITY_TEMPLATE Self Check

## Scope

- Added a prepare-only OpenFOAM lid-driven cavity template generator.
- Added a SolverAdapterPlugin implementation that writes case files and returns a command preview.
- Added source templates and golden fixtures for the cavity case directory.
- Added focused unit and golden tests for generation, warnings, and adapter contract behavior.

## Files

- `src/osw/solvers/openfoam/__init__.py`
- `src/osw/solvers/openfoam/adapter.py`
- `src/osw/solvers/openfoam/case_generator.py`
- `src/osw/solvers/openfoam/osw-plugin.json`
- `src/osw/solvers/openfoam/templates/cavity/**`
- `tests/unit/test_openfoam_adapter.py`
- `tests/unit/test_openfoam_case_generator.py`
- `tests/golden/openfoam/**`

## TDD Evidence

- Initial focused run failed with `ModuleNotFoundError: No module named 'osw.solvers.openfoam'`.
- After implementation, focused tests passed.

## Checks

- `pytest tests\\unit\\test_openfoam_case_generator.py tests\\unit\\test_openfoam_adapter.py tests\\golden\\openfoam -q`
  - Passed: 7 passed.
- `pytest tests/unit/test_openfoam_*.py tests/golden/openfoam -q`
  - Failed locally because PowerShell/pytest treated the wildcard as a literal path.
- Resolved wildcard equivalent:
  - `$openfoamTests = Get-ChildItem -Path tests\\unit -Filter 'test_openfoam_*.py' | ForEach-Object { $_.FullName }`
  - `pytest @openfoamTests tests\\golden\\openfoam -q`
  - Passed: 7 passed.
- `ruff check src tests`
  - Passed.
- `python tools\\qa\\check_scope_drift.py`
  - Passed.
- `python tools\\qa\\check_architecture_boundaries.py`
  - Passed.
- `python tools\\qa\\check_no_solver_artifacts_committed.py`
  - Passed.
- `python tools\\qa\\check_plugin_manifests.py`
  - Passed.
- `python tools\\qa\\run_fast_qa.py`
  - Passed: 150 passed, 1 skipped.

## Notes

- No GUI solver internals were changed.
- No OpenFOAM executable is invoked.
- The adapter is limited to preparing a small cavity template and exposing a command preview.
