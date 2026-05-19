# OSW-AUTO-053 Final v0.1 Release Prep Self-Check

## Scope

- Step: `OSW-AUTO-053_FINAL_V0_1_RELEASE_PREP`
- Branch: `feature/osw-p15-1-final-v0-1-release-prep`
- Worktree: `C:/Users/USER/source/repos/_worktrees/osw-p15-1-final-v0-1-release-prep`
- Decision: `APPROVE_FINAL_PREP`
- Final package version prepared: `0.1.0`
- Final tag: `v0.1.0` remains absent and was not created.
- Pushes: no push performed.

## RC3 UAT Summary

External UAT evidence was available at
`C:/Users/USER/source/repos/_test_runs/osw-rc3-uat/OSW-AUTO-052_RC3_LOCAL_UAT_TEST_RUN_report.md`.

- OSW-AUTO-052 local RC3 UAT passed.
- P0 blockers: none.
- P1 blockers: none.
- P2 follow-ups: optional solver stacks missing locally, PySide6 missing so live GUI interaction was not automated, live external solver runs were not performed, and external URL freshness remains out of scope for the local-only docs checker.
- Demo smoke: CAD import and HTML report passed; mesh import, Gmsh, CalculiX, OpenFOAM, Cantera/CoolProp, and MATLAB/Octave workflows passed with optional dependencies missing where local stacks were unavailable.

## Tag Preservation Evidence

- `v0.1.0-rc1` object type: `tag`
- `v0.1.0-rc1` peeled target:
  `29c5c8bec8df30c7f7be72fc9be5e5409794968e`
- `v0.1.0-rc2` object type: `tag`
- `v0.1.0-rc2` peeled target:
  `684dc6138d4257564bbcdd176a9d5ed311a7316d`
- `v0.1.0-rc3` object type: `tag`
- `v0.1.0-rc3` peeled target:
  `dc7df75c53f0a4acb0a1ccf33d97c01ffdde4b16`
- `git tag --list "v0.1.0"` returned no final tag.

No RC tag was created, deleted, moved, recreated, overwritten, retargeted, or pushed.

## Implementation Summary

- Updated package metadata from `0.1.0rc3` to `0.1.0` in `pyproject.toml` and `src/osw/__init__.py`.
- Updated package smoke expectations to `0.1.0`.
- Extended `tools/qa/check_release_metadata.py` for final-prep validation:
  - repeatable prior RC allowances for rc1, rc2, and rc3;
  - `--forbid-final-tag`;
  - explicit future final-tag validation options;
  - continued rejection of unexpected `v0.1*` tags and lightweight tags when annotated tags are required.
- Added isolated release metadata tests for final-prep and final-tag validation behavior.
- Updated final release notes, README release-readiness wording, release checklist, risk register, decision log, and license/version plan.
- Did not change product features, solver adapters, GUI behavior, dependency versions, license metadata, release artifacts, or public announcement files.

## Version And License Evidence

- Source-isolated feature-worktree command: `$env:PYTHONPATH='src'; python -m osw.cli --version`
  - Result: `osw 0.1.0`
- Source-isolated feature-worktree doctor:
  - Result: version `0.1.0`, external solver execution disabled, optional PySide6/meshio/gmsh/pyvista/cantera/CoolProp/hdf5storage missing, matplotlib/scipy available.
- Raw `python -m osw.cli --version` in the feature worktree still reported `osw 0.1.0rc3` because the local editable install points at the main checkout until the squash merge updates `develop`. The source tree and release metadata checker both validate `0.1.0`; the raw command must be rechecked after merge on `develop`.
- Source license remains `GPL-3.0-or-later`.

## QA Results

- `python tools/qa/check_release_metadata.py --expected-version 0.1.0 --expected-source-license GPL-3.0-or-later --allowed-prior-rc-tag v0.1.0-rc1 --allowed-prior-rc-target 29c5c8bec8df30c7f7be72fc9be5e5409794968e --allowed-prior-rc-tag v0.1.0-rc2 --allowed-prior-rc-target 684dc6138d4257564bbcdd176a9d5ed311a7316d --allowed-prior-rc-tag v0.1.0-rc3 --allowed-prior-rc-target dc7df75c53f0a4acb0a1ccf33d97c01ffdde4b16 --forbid-final-tag`
  - PASS: release metadata aligned for `0.1.0`.
- `python tools/qa/check_release_metadata.py --forbid-release-tags`
  - Expected strict-mode failure: local `v0.1*` RC tags exist and strict pre-tag mode forbids release tags.
- `python tools/qa/check_docs_links.py`
  - PASS: 30 Markdown files checked, 59 local links checked, 0 external links skipped.
- `python tools/qa/check_duplicate_test_basenames.py`
  - PASS.
- `python tools/qa/check_scope_drift.py`
  - PASS.
- `python tools/qa/check_architecture_boundaries.py`
  - PASS.
- `python tools/qa/check_no_solver_artifacts_committed.py`
  - PASS.
- `ruff check src tests`
  - PASS.
- `python tools/qa/run_fast_qa.py`
  - PASS.
- `python tools/qa/run_pre_merge_qa.py`
  - PASS.
- `git diff --check`
  - PASS.

## Test Results

- `pytest tests/unit/test_release_metadata.py -q`
  - PASS: 20 passed.
- `pytest tests/unit/test_package_smoke.py -q`
  - PASS: 6 passed.
- `pytest tests/unit -q`
  - PASS: 258 passed, 3 skipped.
- `pytest tests/gui -q`
  - PASS: 10 skipped.
- `pytest -q --import-mode=importlib`
  - PASS: 276 passed, 19 skipped.
- `pytest tests/integration -q -m "not external_solver"`
  - PASS: 4 passed, 3 skipped, 3 deselected.
- `pytest tests/golden -q`
  - PASS: 10 passed.
- `pytest tests/validation -q`
  - PASS: 4 passed.
- `pytest -q`
  - PASS: 276 passed, 19 skipped.

## Final Release Prep Status

- Final package metadata is prepared as `0.1.0`.
- Final `v0.1.0` tag remains absent.
- Existing rc1, rc2, and rc3 local annotated tags are preserved.
- No push occurred.
- No product feature, solver adapter, GUI behavior, dependency-version, or license-metadata change was made.
- Next dedicated gate: `OSW-AUTO-054_FINAL_V0_1_LOCAL_TAG_GATE`.
