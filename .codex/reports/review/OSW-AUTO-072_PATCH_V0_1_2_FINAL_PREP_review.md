# OSW-AUTO-072 Patch v0.1.2 Final Prep Review

Step ID: OSW-AUTO-072_PATCH_V0_1_2_FINAL_PREP

Review date: 2026-05-21

Reviewer stance: release-prep gate review.

## Decision

Score: 94 / 100

Decision: PASS. The branch is acceptable to squash merge into `develop` after pre-merge QA.

## Scope Review

- The change is release-prep only: package metadata, release documentation, release metadata tests, and evidence reports.
- No solver adapter behavior was changed.
- No GUI behavior was changed.
- No product feature implementation was added.
- No public announcement, release artifact, external solver binary, or generated runtime artifact was staged.

## Version And License Review

- `pyproject.toml` now declares `version = "0.1.2"`.
- `src/osw/__init__.py` now declares `__version__ = "0.1.2"`.
- `tests/unit/test_package_smoke.py` expects `0.1.2`.
- License metadata remains `GPL-3.0-or-later`.
- CLI version check reports `osw 0.1.2` after reinstalling the editable checkout.

## Tag Preservation Review

- `v0.1.2-rc1` remains an annotated tag pointing to `28b30c1f79d4c62d160629e96fc1fcefa2382ebe`.
- `v0.1.1` remains an annotated tag pointing to `7b232f5003fcc8eb207846570499ffb3442d3197`.
- `v0.1.1-rc1` remains unchanged at `da1a2c9e2d27674dc4bb85a2800138170c4c4dec`.
- `v0.1.0` remains an annotated tag pointing to `da8728adf679314442755ed781c1dd57d1c6ed27`.
- `v0.1.0-rc1`, `v0.1.0-rc2`, and `v0.1.0-rc3` remain unchanged.
- `v0.1.2` final tag is absent and was not created.
- No push was performed.

## Release Metadata Checker Review

The existing checker already supports the required final-prep policy. The branch adds isolated tests for:

- `0.1.2` final metadata with historical `v0.1.0` and `v0.1.1` final tags.
- prior `v0.1.2-rc1` allowance with an exact target.
- wrong-target failures for historical final and prior RC tags.
- `--forbid-final-tag v0.1.2`.
- expected annotated `v0.1.2` final tag validation for the later tag gate.
- lightweight final-tag rejection when annotated tags are required.
- unexpected `v0.1.2-*` release-tag rejection.

## QA Evidence Reviewed

- `python tools/qa/check_release_metadata.py ... --expected-version 0.1.2 ... --forbid-final-tag v0.1.2`: PASS.
- `pytest tests/unit/test_release_metadata.py -q`: 51 passed.
- `pytest tests/unit/test_package_smoke.py -q`: 6 passed.
- `python -m osw.cli --version`: `osw 0.1.2`.
- `python -m osw.cli doctor`: PASS.
- `python tools/qa/check_docs_links.py`: PASS.
- `python tools/qa/check_duplicate_test_basenames.py`: PASS.
- `python tools/qa/check_no_solver_artifacts_committed.py`: PASS.
- `ruff check src tests`: PASS.
- `pytest tests/unit -q`: 291 passed, 3 skipped.
- `pytest tests/gui -q`: base env skipped cleanly when PySide6 was unavailable; isolated venv passed 14 tests.
- `pytest -q --import-mode=importlib`: 309 passed, 23 skipped.
- `pytest tests/integration -q -m "not external_solver"`: 4 passed, 3 skipped, 3 deselected.
- `pytest tests/golden -q`: 10 passed.
- `pytest tests/validation -q`: 4 passed.
- `pytest -q`: 309 passed, 23 skipped in base env; 327 passed, 5 skipped, 2 warnings in isolated venv.
- `python tools/qa/run_fast_qa.py`: PASS.
- `python tools/qa/run_pre_merge_qa.py`: PASS.
- `python tools/qa/check_scope_drift.py`: PASS.
- `python tools/qa/check_architecture_boundaries.py`: PASS.
- `git diff --check`: PASS.

## Source Install Evidence

External report:

`C:/Users/USER/source/repos/_test_runs/osw-v0.1.2-final-prep-072/OSW-AUTO-072_PATCH_V0_1_2_FINAL_PREP_SOURCE_INSTALL_RETEST.md`

Reviewed result: PASS. The isolated venv installed the final-prep editable checkout with GUI/viz/mesh/mscript/chm and dev extras, reported `osw 0.1.2`, passed ruff, default pytest, importlib pytest, fast QA, pre-merge QA, docs link check, and duplicate basename check.

## GUI Workflow Evidence

External report:

`C:/Users/USER/source/repos/_test_runs/osw-v0.1.2-final-prep-072/OSW-AUTO-072_PATCH_V0_1_2_FINAL_PREP_GUI_WORKFLOW_SMOKE.md`

Reviewed result: PASS. The compact GUI workflow smoke verified import/project tree/properties, run/generate service diagnostics, table/plot/report state, `.m` preview-first behavior, and no GUI direct solver subprocess implementation.

## Findings

No P0 findings.

No P1 findings.

P2 follow-ups remain:

- Optional external solver live runs are environment-specific.
- Manual desktop CUA depth remains separate from the QTest GUI harness.
- Cantera 3.2 deprecation warning remains a follow-up.
- Packaging smoke remains separate.
- External URL freshness remains outside the local docs checker.

## Merge Recommendation

Proceed with pre-merge QA, then squash merge into `develop` using:

`chore(release): prepare final v0.1.2 metadata`

Do not create `v0.1.2` in this prompt. Final local tag creation belongs to OSW-AUTO-073.
