# OSW-AUTO-029_COOLPROP_PROPERTY_PLUGIN Self Check

## Scope

- Added an optional CoolProp property model plugin for CHM v0.1.
- Added explicit SI state inputs: `fluid`, `pressure_pa`, `temperature_k`, and
  selected output properties.
- Added lazy CoolProp loading so package import and unit tests do not require
  the optional dependency.
- Added friendly missing dependency diagnostics.
- Added point calculation, sweep table generation, CSV export through
  `TablePreview`, and a plot dataset placeholder in reportable output.
- Added a plugin manifest under the CoolProp adapter package.

## Files

- `src/osw/solvers/coolprop/__init__.py`
- `src/osw/solvers/coolprop/property_plugin.py`
- `src/osw/solvers/coolprop/osw-plugin.json`
- `tests/unit/test_coolprop_property_plugin.py`

## TDD Evidence

- Initial focused run failed with `ModuleNotFoundError: No module named
  'osw.solvers.coolprop'`.
- After implementation, the focused CoolProp suite passed with the real
  CoolProp check skipped locally because CoolProp is not installed.

## Checks

- `pytest tests/unit/test_coolprop_*.py -q`
  - Attempted exactly; Windows PowerShell passed the wildcard literally, so
    pytest reported `file or directory not found: tests/unit/test_coolprop_*.py`.
- `$coolpropTests = Get-ChildItem tests\\unit\\test_coolprop_*.py | ForEach-Object { $_.FullName }; pytest $coolpropTests -q`
  - Passed: 5 passed, 1 skipped.
- `pytest tests\\unit\\test_coolprop_property_plugin.py -q`
  - Passed: 5 passed, 1 skipped.
- `ruff check src tests`
  - Passed.
- `python tools\\qa\\run_fast_qa.py`
  - Passed: 174 passed, 2 skipped.
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
- No DWSIM bridge or process flowsheet simulator behavior was added.
- Real CoolProp numerical validation is optional and skipped when CoolProp is
  not installed.

## Review Amend

- Added plugin contract metadata in both the Python metadata surface and
  `osw-plugin.json`: entry point, adapter class, preview requirement, mutation
  and execution flags, dependency behavior, safety flags, and limitations.
- Replaced the placeholder CoolProp example README with a bounded SI-unit
  property point and sweep-table demo description.
- Added regression tests for the contract metadata and example documentation.

## Amend Checks

- `$coolpropTests = Get-ChildItem tests\\unit\\test_coolprop_*.py | ForEach-Object { $_.FullName }; pytest $coolpropTests -q`
  - Passed: 7 passed, 1 skipped.
- `ruff check src tests`
  - Passed.
- `python tools\\qa\\run_fast_qa.py`
  - Passed: 176 passed, 2 skipped.
- `python tools\\qa\\check_scope_drift.py`
  - Passed.
- `python tools\\qa\\check_architecture_boundaries.py`
  - Passed.
- `python tools\\qa\\check_no_solver_artifacts_committed.py`
  - Passed.
- `python tools\\qa\\check_plugin_manifests.py`
  - Passed.
