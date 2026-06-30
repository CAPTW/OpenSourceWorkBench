# OSW-AUTO-069 Release Version Recovery Decision Self-Check

## Step

OSW-AUTO-069_RELEASE_VERSION_RECOVERY_DECISION_AFTER_GUI_FIX

## Decision

Selected safe patch recovery path: `0.1.2rc1` / `v0.1.2-rc1` -> `0.1.2` /
`v0.1.2`.

No package version bump, tag creation, tag movement, release artifact build, or
push is performed in this prompt.

## Current State Evidence

- Current develop before implementation:
  `a12812dab77e1d968223a30859a8fa91e2ef0e1d`
- Package version before and after this prompt: `0.1.1`
- Source license metadata: `GPL-3.0-or-later`
- Historical `v0.1.1` tag: annotated tag at
  `7b232f5003fcc8eb207846570499ffb3442d3197`
- Historical `v0.1.1-rc1` tag: annotated tag at
  `da1a2c9e2d27674dc4bb85a2800138170c4c4dec`
- Historical `v0.1.0` tag: annotated tag at
  `da8728adf679314442755ed781c1dd57d1c6ed27`
- Historical `v0.1.0-rc1`, `v0.1.0-rc2`, `v0.1.0-rc3` targets:
  `29c5c8bec8df30c7f7be72fc9be5e5409794968e`,
  `684dc6138d4257564bbcdd176a9d5ed311a7316d`, and
  `dc7df75c53f0a4acb0a1ccf33d97c01ffdde4b16`.

## OSW-AUTO-068 Evidence Summary

OSW-AUTO-068 returned `PASS_WITH_LIMITATIONS` with no P0/P1 blockers. It
verified that OSW-AUTO-067 improved the GUI from a credible shell into a usable
v0.1.x workflow:

- STL, VTU, `.m`, and `.mat` imports created visible project items.
- Properties updated with type, status, path, and diagnostics.
- Run/Generate created CalculiX, OpenFOAM, Gmsh, CHM, and M-script prepare or
  diagnostic items.
- Table Viewer, FigureDataset, report output, and diagnostics were populated.
- Demo 01, 02, 06, and 08 passed; Demos 03, 04, 05, and 07 passed with optional
  dependency missing where external executables were not installed.

Remaining P2 follow-ups: live external solver executables, manual Computer Use
depth, Cantera deprecation warning, packaging smoke, and external URL freshness.

## Docs Changed

- `docs/07_decision_log.md`: added ADR-0023 selecting the `v0.1.2` patch path.
- `docs/09_risk_register.md`: lowered GUI workflow glue risk after OSW-AUTO-068
  and kept remaining limitations as P2 follow-ups.
- `docs/10_release_checklist.md`: recorded the OSW-AUTO-068 result, blocked
  public `v0.1.1` publish, and added next `0.1.2rc1` candidate routing.
- `docs/13_license_and_version_plan.md`: recorded historical `v0.1.1`, current
  develop ahead of it, and the planned `0.1.2rc1` -> `0.1.2` path.
- `CHANGELOG.md`: added a narrow unreleased planning note without claiming
  `0.1.2` exists.

## Checks Run

- `python -m osw.cli --version`: PASS (`osw 0.1.1`)
- `python -m osw.cli doctor`: PASS with optional heavy extras missing in the
  base checkout and source-install evidence available from OSW-AUTO-067/068.
- `python tools/qa/check_docs_links.py`: PASS
- `python tools/qa/check_duplicate_test_basenames.py`: PASS
- `python tools/qa/check_release_metadata.py ... --expected-final-tag v0.1.1`:
  PASS
- `ruff check src tests`: PASS
- `pytest -q`: PASS (`294 passed, 23 skipped`)
- `pytest -q --import-mode=importlib`: PASS (`294 passed, 23 skipped`)
- `python tools/qa/run_fast_qa.py`: PASS
- `python tools/qa/run_pre_merge_qa.py`: PASS
- `python tools/qa/check_scope_drift.py`: PASS
- `python tools/qa/check_architecture_boundaries.py`: PASS
- `python tools/qa/check_no_solver_artifacts_committed.py`: PASS
- `git diff --check`: PASS

## Tag And Push Safety

- No tag was created.
- No tag was deleted.
- No tag was moved, retargeted, recreated, or overwritten.
- No push occurred.
- Public publish of historical `v0.1.1` remains blocked.

## Next Prompt

OSW-AUTO-070_PATCH_V0_1_2_RC1_PREP
