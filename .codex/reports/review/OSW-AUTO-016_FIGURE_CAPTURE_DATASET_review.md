# OSW-AUTO-016 Figure Capture / FigureDataset Review

## Self-Check

Implemented a minimal FigureDataset and figure capture path for preview-first
MATLAB/Octave workflows.

Changed areas:

- Figure dataset records, serialization, image loading, and report placeholders.
- Workspace extraction for PNG/SVG outputs from explicit runner workspaces.
- Octave run-result figure capture helper.
- Optional Matplotlib PNG/SVG export bridge.
- Plot Viewer dataset listing with PySide6-safe imports.
- Curated `examples/08_mscript_figure` fixture for explicit PNG/SVG output.

Safety notes:

- `.m` import remains preview-first and does not execute code.
- Octave execution still goes through the reviewed backend runner and requires
  explicit `allow_execution=True`.
- GUI code does not launch subprocesses or call Octave.
- Matplotlib remains optional and guarded.

## Decision

Merge allowed.

## Score

94 / 100

## Category Scores

- Architecture Compliance: 18 / 18
- Test Coverage / Regression Safety: 18 / 18
- User Workflow Quality: 11 / 12
- Numerical / Validation Safety: 10 / 12
- Error Handling / Robustness: 9 / 10
- Security / Script Safety: 10 / 10
- Documentation: 4 / 5
- Scope Discipline: 5 / 5
- Git / Local Environment Safety: 9 / 10

## Findings

No hard blockers.

The implementation keeps figure capture bounded to PNG/SVG artifacts and
structured metadata. It avoids advanced MATLAB plot reconstruction, `.fig`
compatibility, Simulink, and GUI direct subprocess execution.

## Required Fixes

None.

## Checks Reviewed

- `pytest tests/unit/test_figure_dataset.py tests/integration/test_mscript_figure_capture_optional.py -q`: passed with optional PySide6 and Octave checks skipped.
- `pytest tests/unit/test_gui_shell_cli.py tests/unit/test_report_generator.py -q`: passed.
- `pytest tests/gui -q`: skipped cleanly because PySide6 is not installed.
- `ruff check src tests`: passed.
- `python tools/qa/run_fast_qa.py`: passed.
- `python tools/qa/check_scope_drift.py`: passed.
- `python tools/qa/check_architecture_boundaries.py`: passed.
- `python tools/qa/check_no_solver_artifacts_committed.py`: passed.
- `python tools/hooks/scan_mscript_safety.py examples/08_mscript_figure`: passed.

## Residual Risks

Real GNU Octave is optional in this environment, so the actual Octave plotting
integration was skipped. Matplotlib export was exercised because Matplotlib is
available locally.
