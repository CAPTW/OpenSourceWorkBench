# OSW-AUTO-028_SU2_BASIC_ADAPTER Self Check

## Scope

- Added a prepare-only SU2 SolverAdapterPlugin for basic `.cfg` generation.
- Added a small SU2 simulation config model and deterministic config writer.
- Added `.su2` mesh handoff by filename/reference only; no mesh conversion or
  solver execution is performed by the adapter.
- Added a backend SU2 runner wrapper that reuses `ExternalCommandRunner` and
  augments missing executable diagnostics for `SU2_CFD`.
- Added a minimal residual parser for SU2 history CSV and simple console table
  logs.
- Added focused unit tests and a golden SU2 config fixture.

## Files

- `src/osw/solvers/su2/__init__.py`
- `src/osw/solvers/su2/adapter.py`
- `src/osw/solvers/su2/config.py`
- `src/osw/solvers/su2/residuals.py`
- `src/osw/solvers/su2/runner.py`
- `src/osw/solvers/su2/osw-plugin.json`
- `tests/unit/test_su2_adapter.py`
- `tests/unit/test_su2_config.py`
- `tests/unit/test_su2_residuals.py`
- `tests/unit/test_su2_runner.py`
- `tests/golden/su2/basic_euler.cfg`
- `tests/golden/su2/test_su2_cfg_golden.py`

## TDD Evidence

- Initial focused run failed with `ModuleNotFoundError: No module named
  'osw.solvers.su2'`.
- After implementation, the focused SU2 suite passed.

## Checks

- `pytest tests/unit/test_su2_*.py tests/golden/su2 -q`
  - Attempted exactly; Windows PowerShell passed the wildcard literally, so
    pytest reported `file or directory not found: tests/unit/test_su2_*.py`.
- `$su2Tests = Get-ChildItem tests\\unit\\test_su2_*.py | ForEach-Object { $_.FullName }; pytest $su2Tests tests\\golden\\su2 -q`
  - Passed: 10 passed.
- `pytest tests/unit/test_su2_config.py tests/unit/test_su2_adapter.py tests/unit/test_su2_residuals.py tests/unit/test_su2_runner.py tests/golden/su2 -q`
  - Passed: 10 passed.
- `ruff check src tests`
  - Passed.
- `python tools\\qa\\run_fast_qa.py`
  - Passed: 164 passed, 1 skipped.
- `python tools\\qa\\check_scope_drift.py`
  - Passed.
- `python tools\\qa\\check_architecture_boundaries.py`
  - Passed.
- `python tools\\qa\\check_no_solver_artifacts_committed.py`
  - Passed.

## Notes

- No GUI files were changed.
- No OpenFOAM files were changed.
- The SU2 adapter prepares config artifacts and command previews only.
- Advanced SU2 workflows, optimization, and broad solver coverage remain parked.

## Review Amend

- Added validation that rejects newline/control/config-syntax injection in SU2
  mesh references, convergence filenames, and marker names.
- Added an explicit `reference_frame="su2_nondimensional"` assumption for SU2
  reference length/area/origin values.
- Changed config writing to validate and generate text before creating the
  output directory.
- Changed missing executable diagnostics to name the configured executable.

## Amend Checks

- `$su2Tests = Get-ChildItem tests\\unit\\test_su2_*.py | ForEach-Object { $_.FullName }; pytest $su2Tests tests\\golden\\su2 -q`
  - Passed: 15 passed.
- `ruff check src tests`
  - Passed.
- `python tools\\qa\\run_fast_qa.py`
  - Passed: 169 passed, 1 skipped.
- `python tools\\qa\\check_scope_drift.py`
  - Passed.
- `python tools\\qa\\check_architecture_boundaries.py`
  - Passed.
- `python tools\\qa\\check_no_solver_artifacts_committed.py`
  - Passed.
- `python tools\\qa\\check_plugin_manifests.py`
  - Passed.

## Second Review Amend

- Removed the remaining hard-coded `SU2_CFD` install guidance from the custom
  executable missing diagnostic.
- Extended the runner test to assert a custom executable diagnostic does not
  say `install SU2_CFD on PATH`.

## Second Amend Checks

- `pytest tests\\unit\\test_su2_runner.py -q`
  - Passed: 1 passed.
- `ruff check src\\osw\\solvers\\su2\\runner.py tests\\unit\\test_su2_runner.py`
  - Passed.
