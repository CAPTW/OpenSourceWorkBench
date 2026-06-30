# OSW-AUTO-030_CANTERA_REACTOR_PLUGIN Self Check

## Scope

- Added an optional Cantera 0D reactor SolverAdapterPlugin.
- Added explicit SI reactor inputs: `temperature_k`, `pressure_pa`,
  `end_time_s`, `time_step_s`, and gas composition.
- Added lazy Cantera loading so package import and unit tests do not require
  the optional dependency.
- Added friendly missing dependency and missing mechanism diagnostics.
- Added bounded in-process time integration for constant-volume 0D reactors.
- Added species/time `TablePreview` output and a temperature/time plot dataset
  placeholder for report integration.
- Added a plugin manifest and bounded example README.

## Files

- `src/osw/solvers/cantera/__init__.py`
- `src/osw/solvers/cantera/adapter.py`
- `src/osw/solvers/cantera/osw-plugin.json`
- `tests/unit/test_cantera_reactor_plugin.py`
- `tests/integration/test_cantera_optional.py`
- `examples/06_cantera_reactor/README.md`

## TDD Evidence

- Initial focused run failed with `ModuleNotFoundError: No module named
  'osw.solvers.cantera'`.
- After implementation, the expanded focused Cantera suite passed with real
  Cantera tests skipped locally because Cantera is not installed.

## Checks

- `pytest tests/unit/test_cantera_*.py tests/integration/test_cantera_optional.py -q`
  - Attempted exactly; Windows PowerShell passed the wildcard literally, so
    pytest reported `file or directory not found: tests/unit/test_cantera_*.py`.
- `$canteraTests = Get-ChildItem tests\\unit\\test_cantera_*.py | ForEach-Object { $_.FullName }; pytest $canteraTests tests\\integration\\test_cantera_optional.py -q`
  - Passed: 7 passed, 2 skipped.
- `ruff check src tests`
  - Passed.
- `python tools\\qa\\run_fast_qa.py`
  - Passed: 183 passed, 3 skipped.
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
- No external process execution was added.
- No full combustion CFD or process simulator bridge was added.
- Real Cantera numerical validation is optional and skipped when Cantera is not
  installed.

## Review Amend

- Added explicit v0.1 reactor bounds: maximum end time and maximum integration
  step count.
- Changed `prepare_case()` to return an invalid preview with warnings for
  malformed input instead of raising during preview.
- Rejected zero-sum gas compositions with an OSW input diagnostic.
- Added focused regression tests for each review-required behavior.

## Amend Checks

- `$canteraTests = Get-ChildItem tests\\unit\\test_cantera_*.py | ForEach-Object { $_.FullName }; pytest $canteraTests tests\\integration\\test_cantera_optional.py -q`
  - Passed: 11 passed, 2 skipped.
- `ruff check src tests`
  - Passed.
- `python tools\\qa\\run_fast_qa.py`
  - Passed: 187 passed, 3 skipped.
- `python tools\\qa\\check_scope_drift.py`
  - Passed.
- `python tools\\qa\\check_architecture_boundaries.py`
  - Passed.
- `python tools\\qa\\check_no_solver_artifacts_committed.py`
  - Passed.
- `python tools\\qa\\check_plugin_manifests.py`
  - Passed.
