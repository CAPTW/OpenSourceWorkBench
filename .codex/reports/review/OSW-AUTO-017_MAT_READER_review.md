# OSW-AUTO-017 MAT Reader Review

## Self-Check

Implemented a preview-only MATLAB MAT reader for `.mat` workflows.

Changed areas:

- `src/osw/scripts/mscript/mat_reader.py`
- `src/osw/post/table_model.py`
- `src/osw/scripts/mscript/__init__.py`
- `tests/unit/test_mat_reader.py`

Safety notes:

- The reader never executes MATLAB, Octave, or script code.
- MATLAB Engine and proprietary toolbox support were not added.
- SciPy remains optional and is loaded lazily.
- MAT v7.3 is detected as HDF5-backed and gives an explicit hdf5storage warning
  when the optional reader is unavailable.
- CSV export works from structured preview rows, not from generated runtime
  directories.

## Decision

Merge allowed.

## Score

95 / 100

## Category Scores

- Architecture Compliance: 18 / 18
- Test Coverage / Regression Safety: 18 / 18
- User Workflow Quality: 11 / 12
- Numerical / Validation Safety: 11 / 12
- Error Handling / Robustness: 10 / 10
- Security / Script Safety: 10 / 10
- Documentation: 4 / 5
- Scope Discipline: 5 / 5
- Git / Local Environment Safety: 9 / 10

## Findings

No hard blockers.

The implementation is scoped to previewing MAT data metadata and numeric table
exports. It avoids MATLAB Engine integration, proprietary toolbox claims,
Simulink, `.mlapp`, and GUI direct subprocess execution.

## Required Fixes

None.

## Checks Reviewed

- `pytest tests/unit/test_mat_reader.py -q`: passed.
- `ruff check src tests`: passed.
- `python tools/qa/run_fast_qa.py`: passed.
- `python tools/qa/check_scope_drift.py`: passed.
- `python tools/qa/check_architecture_boundaries.py`: passed.
- `python tools/qa/check_no_solver_artifacts_committed.py`: passed.

## Residual Risks

hdf5storage is not installed in this environment, so MAT v7.3 is covered by the
friendly unsupported/optional-dependency path rather than a real v7.3 load.
