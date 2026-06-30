# OSW-AUTO-062 Patch v0.1.1 Final Prep Self-Check

## Summary

- Step: OSW-AUTO-062_PATCH_V0_1_1_FINAL_PREP
- Decision: APPROVE_FINAL_V0_1_1_PREP_WITH_DOCS_ONLY_POST_RC_DELTA
- Base develop before implementation: `eeac576cc830cf75038127b1fb5d1c178b8b0d6e`
- Target package version: `0.1.1`
- Final tag target: `v0.1.1` remains pending and was not created.
- Push status: no push performed.

## Tag Preservation Evidence

- Historical `v0.1.0` remains an annotated tag at `da8728adf679314442755ed781c1dd57d1c6ed27`.
- Historical `v0.1.0-rc1` remains at `29c5c8bec8df30c7f7be72fc9be5e5409794968e`.
- Historical `v0.1.0-rc2` remains at `684dc6138d4257564bbcdd176a9d5ed311a7316d`.
- Historical `v0.1.0-rc3` remains at `dc7df75c53f0a4acb0a1ccf33d97c01ffdde4b16`.
- Prior patch RC `v0.1.1-rc1` remains an annotated tag at `da1a2c9e2d27674dc4bb85a2800138170c4c4dec`.
- `git tag --list "v0.1.1"` returned no final tag before this checkpoint.

## Version Metadata Evidence

- `pyproject.toml` package version changed from `0.1.1rc1` to `0.1.1`.
- `src/osw/__init__.py` now reports `__version__ = "0.1.1"`.
- `tests/unit/test_package_smoke.py` expects `0.1.1`.
- Feature-worktree CLI verification with the worktree source path reported `osw 0.1.1`.
- License metadata remains `GPL-3.0-or-later`.

## Release Metadata Evidence

The existing release metadata checker already supported the final-prep policy for:

- expected package version `0.1.1`;
- historical final tag allowance for `v0.1.0`;
- prior RC allowances for `v0.1.0-rc1`, `v0.1.0-rc2`, `v0.1.0-rc3`, and `v0.1.1-rc1`;
- forbidden final tag mode for `v0.1.1`;
- future expected annotated final tag validation.

Additional isolated tests were added for the v0.1.1 final-prep and final-tag policies, including wrong-target failures, forbidden final tag detection, lightweight final tag rejection, and unexpected tag rejection.

## Docs-Only Post-RC Delta Acceptance

OSW-AUTO-061A advanced `develop` beyond `v0.1.1-rc1` only for docs/readiness cleanup. This prompt records the maintainer acceptance of that docs-only post-RC delta and prepares final `0.1.1` metadata without moving or publishing `v0.1.1-rc1`.

## Files Changed

- `pyproject.toml`
- `src/osw/__init__.py`
- `tests/unit/test_package_smoke.py`
- `tests/unit/test_release_metadata.py`
- `CHANGELOG.md`
- `README.md`
- `docs/07_decision_log.md`
- `docs/09_risk_register.md`
- `docs/10_release_checklist.md`
- `docs/13_license_and_version_plan.md`

## Checks Run

- `python -m osw.cli --version`: PASS, `osw 0.1.1`
- `python -m osw.cli doctor`: PASS
- `python tools/qa/check_docs_links.py`: PASS
- `python tools/qa/check_duplicate_test_basenames.py`: PASS
- `python tools/qa/check_no_solver_artifacts_committed.py`: PASS
- `python tools/qa/check_release_metadata.py --expected-version 0.1.1 ... --forbid-final-tag v0.1.1`: PASS
- `ruff check src tests`: PASS
- `pytest tests/unit/test_release_metadata.py -q`: PASS, 36 passed
- `pytest tests/unit/test_package_smoke.py -q`: PASS, 6 passed
- `pytest tests/unit -q`: PASS, 274 passed, 3 skipped
- `pytest tests/gui -q`: PASS, 10 skipped
- `pytest -q --import-mode=importlib`: PASS, 292 passed, 19 skipped
- `pytest tests/integration -q -m "not external_solver"`: PASS, 4 passed, 3 skipped, 3 deselected
- `pytest tests/golden -q`: PASS, 10 passed
- `pytest tests/validation -q`: PASS, 4 passed
- `pytest -q`: PASS, 292 passed, 19 skipped
- `python tools/qa/check_scope_drift.py`: PASS
- `python tools/qa/check_architecture_boundaries.py`: PASS
- `python tools/qa/run_fast_qa.py`: PASS
- `python tools/qa/run_pre_merge_qa.py`: PASS
- `git diff --check`: PASS

## Isolated Source-Install Validation

- Venv: `C:/Users/USER/source/repos/_venvs/osw-v011-final-prep-062`
- Worktree: `C:/Users/USER/source/repos/_worktrees/osw-p16-5-patch-v0-1-1-final-prep`
- Install commands:
  - `python -m pip install -e ".[gui,viz,mesh,mscript,chm]"`: PASS
  - `python -m pip install -e ".[dev]"`: PASS
- `python -m osw.cli --version`: PASS, `osw 0.1.1`
- `ruff --version`: PASS, `ruff 0.15.13`
- `ruff check src tests`: PASS
- `pytest -q`: PASS, 306 passed, 5 skipped, 2 warnings
- `pytest -q --import-mode=importlib`: PASS, 306 passed, 5 skipped, 2 warnings
- `python tools/qa/run_fast_qa.py`: PASS
- `python tools/qa/run_pre_merge_qa.py`: PASS
- `python tools/qa/check_docs_links.py`: PASS
- `python tools/qa/check_duplicate_test_basenames.py`: PASS

## Residual Risks

- Optional external solver executables remain environment-specific.
- GUI live interaction depth remains environment-specific.
- External URL freshness is outside the local-only docs checker.
- Final local `v0.1.1` tag creation remains blocked until OSW-AUTO-063.
- Public push and public announcement remain blocked until explicit maintainer gates.

## Next Prompt

If this final-prep change merges and post-merge validation passes, run:

`OSW-AUTO-063_PATCH_V0_1_1_FINAL_LOCAL_TAG_GATE`
