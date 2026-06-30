# OSW-AUTO-067 GUI Workflow Fix Queue Self-Check

## Scope

- Step: OSW-AUTO-067_GUI_WORKFLOW_FIX_QUEUE
- Branch: `feature/osw-p17-1-gui-workflow-glue`
- Worktree: `C:/Users/USER/source/repos/_worktrees/osw-p17-1-gui-workflow-glue`
- Base develop: `7b232f5003fcc8eb207846570499ffb3442d3197`
- Package version: `0.1.1`
- Source license metadata: `GPL-3.0-or-later`

## OSW-AUTO-066 Findings Addressed

- GUI Import now accepts file paths through `MainWindow.import_file()` and a real file dialog action.
- Imported geometry, mesh, `.m`, and `.mat` paths add visible Project Tree items.
- Selecting imported items updates Properties with type, path, status, summary, diagnostics, and metadata.
- Run/Generate calls `WorkbenchWorkflowSession.run_generate()` and records bounded prepare/generate results or optional dependency diagnostics.
- Table Viewer now displays metadata/result tables instead of a placeholder.
- Report export receives current project state, mesh info, result tables, figure placeholders, and warnings.

## Changed Flows

- Import: `src/osw/gui/workflow_service.py`, `src/osw/gui/main_window.py`
- Configure/Inspect: `src/osw/gui/properties_panel.py`, Project Tree selection handling
- Run/Generate: `WorkbenchWorkflowSession` prepare/diagnostic workflow service
- Result/Table/Report: `src/osw/gui/table_viewer.py`, `src/osw/gui/report_panel.py`
- Docs: release checklist, risk register, decision log, README, changelog

## Tests Added or Updated

- `tests/gui/test_import_workflow.py`
- `tests/gui/test_run_workflow.py`
- `tests/unit/test_gui_workflow_service.py`

## Architecture and Safety Evidence

- GUI Python modules do not import `subprocess`.
- `python tools/qa/check_architecture_boundaries.py`: PASS
- `python tools/qa/check_scope_drift.py`: PASS
- `python tools/qa/check_no_solver_artifacts_committed.py`: PASS
- `.m` import remains preview-first; tests assert marker file is not created.
- Runtime case/report artifacts are written to temp or external test-run paths, not the repo.

## Feature-Branch QA

- `python -m osw.cli --version`: PASS, `osw 0.1.1`
- `python -m osw.cli doctor`: PASS
- `python tools/qa/check_docs_links.py`: PASS
- `python tools/qa/check_duplicate_test_basenames.py`: PASS
- `ruff check src tests`: PASS
- `pytest tests/unit -q`: PASS, `276 passed, 3 skipped`
- `pytest tests/gui -q`: PASS in base environment with PySide6 unavailable, `14 skipped`
- `pytest -q`: PASS, `294 passed, 23 skipped`
- `pytest -q --import-mode=importlib`: PASS, `294 passed, 23 skipped`
- `python tools/qa/run_fast_qa.py`: PASS
- `python tools/qa/run_pre_merge_qa.py`: PASS
- `git diff --check`: PASS

## Isolated Source-Install Evidence

- Venv: `C:/Users/USER/source/repos/_venvs/osw-v011-gui-workflow-067`
- Install:
  - `python -m pip install -U pip`
  - `python -m pip install -e ".[gui,viz,mesh,mscript,chm]"`
  - `python -m pip install -e ".[dev]"`
- `python -m osw.cli --version`: PASS, `osw 0.1.1`
- `python -m osw.cli doctor`: PASS; PySide6, meshio, gmsh, pyvista, cantera, CoolProp, scipy, and hdf5storage available.
- `ruff --version`: `ruff 0.15.13`
- `ruff check src tests`: PASS
- Focused GUI workflow tests: PASS, `10 passed`
- `pytest -q`: PASS, `312 passed, 5 skipped, 2 warnings`
- `pytest -q --import-mode=importlib`: PASS, `312 passed, 5 skipped, 2 warnings`
- `python tools/qa/run_fast_qa.py`: PASS
- `python tools/qa/run_pre_merge_qa.py`: PASS
- External report: `C:/Users/USER/source/repos/_test_runs/osw-v0.1.1-gui-workflow-067/OSW-AUTO-067_SOURCE_INSTALL_RETEST.md`

## GUI Workflow Smoke

- Harness: `C:/Users/USER/source/repos/_test_runs/osw-v0.1.1-gui-workflow-067/gui_smoke.py`
- Runtime artifacts: `C:/Users/USER/source/repos/_test_runs/osw-v0.1.1-gui-workflow-067/runtime-artifacts`
- Result: PASS
- Verified:
  - geometry, M-script, and MAT imports add Project Tree items;
  - M-script preview did not execute code;
  - Run/Generate created prepare/diagnostic entries;
  - Gmsh generated external runtime mesh artifacts;
  - report export contains imported item and diagnostics.
- External report: `C:/Users/USER/source/repos/_test_runs/osw-v0.1.1-gui-workflow-067/OSW-AUTO-067_GUI_WORKFLOW_SMOKE.md`

## Tag Preservation

- `v0.1.1` object type: `tag`
- `v0.1.1` target: `7b232f5003fcc8eb207846570499ffb3442d3197`
- `v0.1.1-rc1` object type: `tag`
- `v0.1.1-rc1` target: `da1a2c9e2d27674dc4bb85a2800138170c4c4dec`
- `v0.1.0` object type: `tag`
- `v0.1.0` target: `da8728adf679314442755ed781c1dd57d1c6ed27`
- No tag was created, deleted, moved, overwritten, or retargeted.

## Release Implication

If merged, `develop` advances beyond local `v0.1.1` release evidence. Public publish remains blocked pending a new version/release decision.

## Push Status

No push occurred.

## Next Recommended Prompt

OSW-AUTO-068_INTERACTIVE_GUI_WORKFLOW_UAT_RETEST
