# OSW-AUTO-070 Patch v0.1.2 RC1 Prep Self-Check

## Step

- Step ID: `OSW-AUTO-070_PATCH_V0_1_2_RC1_PREP`
- Branch: `feature/osw-p17-3-patch-v0-1-2-rc1-prep`
- Worktree: `C:/Users/USER/source/repos/_worktrees/osw-p17-3-patch-v0-1-2-rc1-prep`
- Base develop before implementation: `8711c190a99db4bae02cd0e40363c102f8696be2`
- Target package version: `0.1.2rc1`
- Target local RC tag: `v0.1.2-rc1`

## Historical Tags

- `v0.1.1`: annotated tag, target `7b232f5003fcc8eb207846570499ffb3442d3197`.
- `v0.1.1-rc1`: annotated tag, target `da1a2c9e2d27674dc4bb85a2800138170c4c4dec`.
- `v0.1.0`: annotated tag, target `da8728adf679314442755ed781c1dd57d1c6ed27`.
- `v0.1.0-rc1`: target `29c5c8bec8df30c7f7be72fc9be5e5409794968e`.
- `v0.1.0-rc2`: target `684dc6138d4257564bbcdd176a9d5ed311a7316d`.
- `v0.1.0-rc3`: target `dc7df75c53f0a4acb0a1ccf33d97c01ffdde4b16`.
- No existing historical tag was moved, recreated, deleted, retargeted, or pushed.
- Final `v0.1.2` tag was not created.

## Changes

- Updated package metadata and static package version to `0.1.2rc1`.
- Updated package smoke expectations for CLI/package version.
- Added release metadata unit tests for:
  - `0.1.2rc1` metadata with multiple historical final tags;
  - historical `v0.1.1` wrong-target failure;
  - prior `v0.1.1-rc1` allowed/wrong-target behavior;
  - forbidden final `v0.1.2`;
  - expected annotated `v0.1.2-rc1`;
  - wrong-target and lightweight current RC failures;
  - unexpected `v0.1.2*` tag rejection.
- Updated README, CHANGELOG, decision log, risk register, release checklist, and license/version plan for the `0.1.2rc1` recovery candidate.

## OSW-AUTO-068 Evidence Summary

- OSW-AUTO-068 status: `PASS_WITH_LIMITATIONS`.
- No P0/P1 blockers were reported.
- GUI workflow improved over OSW-AUTO-066: STL/VTU/`.m`/`.mat` imports created visible project items; selection updated properties; Run/Generate routed through workflow services; report export included imported state and diagnostics.
- Remaining risks are P2/P3: external solver live runs, manual desktop CUA depth, Cantera deprecation warning, external URL freshness, and packaging smoke.

## Feature-Branch QA

Passed:

- `python -m osw.cli --version`: `osw 0.1.2rc1`.
- `python -m osw.cli doctor`.
- `python tools/qa/check_docs_links.py`.
- `python tools/qa/check_duplicate_test_basenames.py`.
- `python tools/qa/check_no_solver_artifacts_committed.py`.
- `python tools/qa/check_scope_drift.py`.
- `python tools/qa/check_architecture_boundaries.py`.
- `python tools/qa/check_release_metadata.py --expected-version 0.1.2rc1 ... --forbid-final-tag v0.1.2`.
- `ruff check src tests`.
- `pytest tests/unit/test_release_metadata.py -q`: 44 passed.
- `pytest tests/unit/test_package_smoke.py -q`: 6 passed.
- `pytest tests/unit -q`: 284 passed, 3 skipped.
- `pytest tests/gui -q`: 14 skipped in the base environment because PySide6 is not installed there.
- `pytest tests/integration -q -m "not external_solver"`: 4 passed, 3 skipped, 3 deselected.
- `pytest tests/golden -q`: 10 passed.
- `pytest tests/validation -q`: 4 passed.
- `pytest -q`: 302 passed, 23 skipped.
- `pytest -q --import-mode=importlib`: 302 passed, 23 skipped.
- `python tools/qa/run_fast_qa.py`.
- `python tools/qa/run_pre_merge_qa.py`.
- `git diff --check`.

## Source-Install Validation

- Venv: `C:/Users/USER/source/repos/_venvs/osw-v012rc1-source-run-070`.
- Report: `C:/Users/USER/source/repos/_test_runs/osw-v0.1.2-rc1-source-run-070/OSW-AUTO-070_PATCH_V0_1_2_RC1_SOURCE_INSTALL_RETEST.md`.
- Install commands:
  - `python -m pip install -U pip`.
  - `python -m pip install -e ".[gui,viz,mesh,mscript,chm]"`.
  - `python -m pip install -e ".[dev]"`.
- Results:
  - `python -m osw.cli --version`: `osw 0.1.2rc1`.
  - `python -m osw.cli doctor`: PySide6, meshio, gmsh, PyVista, Matplotlib, Cantera, CoolProp, SciPy, and hdf5storage available.
  - `ruff --version`: `ruff 0.15.13`.
  - `ruff check src tests`: PASS.
  - `pytest -q`: PASS.
  - `pytest -q --import-mode=importlib`: PASS.
  - `python tools/qa/run_fast_qa.py`: PASS.
  - `python tools/qa/run_pre_merge_qa.py`: PASS.
  - Docs link checker and duplicate basename checker: PASS.

## GUI Workflow Smoke

- Report: `C:/Users/USER/source/repos/_test_runs/osw-v0.1.2-rc1-source-run-070/OSW-AUTO-070_PATCH_V0_1_2_RC1_GUI_WORKFLOW_SMOKE.md`.
- Runtime artifact directory: `C:/Users/USER/source/repos/_test_runs/osw-v0.1.2-rc1-source-run-070/runtime-artifacts`.
- Screenshot directory: `C:/Users/USER/source/repos/_test_runs/osw-v0.1.2-rc1-source-run-070/screenshots`.
- Results:
  - `python -m osw.cli gui --help`: PASS.
  - `pytest tests/gui -q`: 14 passed in the full-extras venv.
  - `pytest tests/gui/test_import_workflow.py -q`: 2 passed.
  - `pytest tests/gui/test_run_workflow.py -q`: 2 passed.
  - `pytest tests/gui/test_report_panel.py -q`: 1 passed.
  - `pytest tests/unit/test_mscript_safety_scan.py -q`: 4 passed.
  - `pytest tests/unit/test_report_generator.py -q`: 8 passed.
  - `python tools/qa/check_architecture_boundaries.py`: PASS.
  - GUI subprocess scan found only the local `src/osw/gui/AGENTS.md` policy text.

## Release Implication

- `v0.1.1` remains historical local-only final evidence and must not be published as current.
- `0.1.2rc1` / `v0.1.2-rc1` is the next local patch candidate.
- Local `v0.1.2-rc1` tag creation remains pending post-merge checks.
- Final `v0.1.2`, public push, release artifacts, and public announcement remain blocked.

## Push Status

No push was performed.
