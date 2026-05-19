# OSW-AUTO-060 Patch v0.1.1 RC1 Prep Self-Check

## Decision And Target

- Step: OSW-AUTO-060_PATCH_V0_1_1_RC1_PREP
- Decision: APPROVE_PATCH_RC1_PREP_AND_LOCAL_TAG
- Base `develop` before implementation: `70488a3635d3d8eae3f81f7a5a9b133056981649`
- Target package version: `0.1.1rc1`
- Target local RC tag: `v0.1.1-rc1`
- Later final package/tag: `0.1.1` / `v0.1.1`
- Source license: `GPL-3.0-or-later`

## Historical Tag Preservation

- Historical final `v0.1.0`: annotated tag object `tag`, peeled target `da8728adf679314442755ed781c1dd57d1c6ed27`
- Historical rc1 `v0.1.0-rc1`: annotated tag object `tag`, peeled target `29c5c8bec8df30c7f7be72fc9be5e5409794968e`
- Historical rc2 `v0.1.0-rc2`: annotated tag object `tag`, peeled target `684dc6138d4257564bbcdd176a9d5ed311a7316d`
- Historical rc3 `v0.1.0-rc3`: annotated tag object `tag`, peeled target `dc7df75c53f0a4acb0a1ccf33d97c01ffdde4b16`
- `v0.1.1*` tags were absent before this feature work.
- No existing tag was created, deleted, moved, retargeted, recreated, overwritten, or pushed during feature-branch implementation.

## Version And Metadata Evidence

- `pyproject.toml` version: `0.1.1rc1`
- `src/osw/__init__.py` version: `0.1.1rc1`
- Package smoke expected version: `0.1.1rc1`
- Feature-worktree CLI with local `src` on `PYTHONPATH`: `osw 0.1.1rc1`
- Release metadata checker supports:
  - `--allowed-historical-final-tag v0.1.0`
  - `--allowed-historical-final-target da8728adf679314442755ed781c1dd57d1c6ed27`
  - `--forbid-final-tag v0.1.1`
  - expected `v0.1.1-rc1` annotated tag validation after tag creation
- Release metadata command passed for `0.1.1rc1` before tag creation.

## Documentation Evidence

- `CHANGELOG.md` adds `0.1.1rc1` release-candidate notes.
- `README.md` release status now identifies `0.1.1rc1` as the current patch RC package version and keeps `v0.1.0` historical.
- `docs/07_decision_log.md` adds the OSW-AUTO-060 patch RC1 decision.
- `docs/09_risk_register.md` adds patch RC1 tag-gate bypass risk.
- `docs/10_release_checklist.md` identifies `v0.1.1-rc1` as the current local candidate and keeps final `v0.1.1` blocked.
- `docs/13_license_and_version_plan.md` records `0.1.1rc1`, historical `v0.1.0`, and final `v0.1.1` deferral.

## Feature-Branch QA Results

- `python -m osw.cli --version`: passed with `PYTHONPATH=src`, `osw 0.1.1rc1`
- `python -m osw.cli doctor`: passed with `PYTHONPATH=src`
- `python tools/qa/check_docs_links.py`: passed, 30 Markdown files and 59 local links checked
- `python tools/qa/check_duplicate_test_basenames.py`: passed
- `python tools/qa/check_no_solver_artifacts_committed.py`: passed
- `python tools/qa/check_release_metadata.py --expected-version 0.1.1rc1 ... --allowed-historical-final-tag v0.1.0 ... --forbid-final-tag v0.1.1`: passed
- `ruff check src tests`: passed
- `pytest tests/unit/test_release_metadata.py -q`: passed, 29 passed
- `pytest tests/unit/test_package_smoke.py -q`: passed, 6 passed
- `pytest tests/unit -q`: passed, 267 passed, 3 skipped
- `pytest tests/gui -q`: passed, 10 skipped
- `pytest -q --import-mode=importlib`: passed, 285 passed, 19 skipped
- `pytest tests/integration -q -m "not external_solver"`: passed, 4 passed, 3 skipped, 3 deselected
- `pytest tests/golden -q`: passed, 10 passed
- `pytest tests/validation -q`: passed, 4 passed
- `pytest -q`: passed, 285 passed, 19 skipped
- `python tools/qa/check_scope_drift.py`: passed
- `python tools/qa/check_architecture_boundaries.py`: passed
- `python tools/qa/run_fast_qa.py`: passed, unit subrun 267 passed, 3 skipped
- `python tools/qa/run_pre_merge_qa.py`: passed, unit subrun 267 passed, 3 skipped
- `git diff --check`: passed

## Isolated Source-Install Validation From Feature Worktree

- Venv: `C:/Users/USER/source/repos/_venvs/osw-v011rc1-source-run-060`
- Install command: `python -m pip install -e ".[gui,viz,mesh,mscript,chm]"`, then `python -m pip install -e ".[dev]"`
- Installed package: `open-solver-workbench-0.1.1rc1`
- CLI version: `osw 0.1.1rc1`
- Doctor: passed; PySide6, meshio, gmsh, pyvista, matplotlib, cantera, CoolProp, scipy, and hdf5storage available
- Ruff version/result: `ruff 0.15.13`, passed
- Default pytest: passed, 299 passed, 5 skipped, 2 warnings
- Importlib pytest: passed, 299 passed, 5 skipped, 2 warnings
- Fast QA: passed, unit subrun 267 passed, 3 skipped
- Pre-merge QA: passed, unit subrun 267 passed, 3 skipped
- Docs link checker: passed
- Duplicate basename checker: passed
- Worktree status: only intentional tracked release-prep changes

## Safety Confirmations

- Historical `v0.1.0` was not moved, deleted, retargeted, recreated, overwritten, pushed, or recommended for current publication.
- Historical rc1/rc2/rc3 tags were preserved.
- Final `v0.1.1` tag was not created.
- No push occurred.
- No release artifacts, external solver binaries, generated solver runtime outputs, product features, solver adapter behavior, or GUI behavior changes were introduced.

## Next Gate

After review, squash merge to `develop`, rerun post-merge QA and fresh source-install validation from current `develop`, then create local annotated `v0.1.1-rc1` only if all criteria pass.
