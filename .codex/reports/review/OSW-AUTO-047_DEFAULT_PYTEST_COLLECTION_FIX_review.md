# OSW-AUTO-047 Review

Decision: Merge possible

Score: 96/100

Checkpoint: `f1b24ad` (`checkpoint(047): Default pytest collection fix before review`)

## Critical Issues

None.

## High Issues

None.

## Medium Issues

None.

## Low Issues

- The release checklist uses generic report-evidence wording that marks the
  review report path as `PASS`. This is acceptable once this report is staged
  and included in the feature branch before merge.

## Review Evidence

- The default pytest failure was reproduced before the feature worktree:
  duplicate basename import mismatch between
  `tests/gui/test_plugin_manager_dialog.py` and
  `tests/unit/test_plugin_manager_dialog.py`.
- The fix directly renames the colliding test files to
  `tests/gui/test_plugin_manager_dialog_gui.py` and
  `tests/unit/test_plugin_manager_dialog_unit.py`.
- Both original test files are preserved as 100% renames, so their coverage is
  retained.
- `tools/qa/check_duplicate_test_basenames.py` scans paths under `tests/`
  without importing test modules, using network access, or mutating state.
- `tools/qa/run_fast_qa.py` now runs the duplicate-basename guard, and
  `tools/qa/run_pre_merge_qa.py` inherits it through the fast QA runner.
- Product source, package version metadata, license metadata, docs-link checker
  implementation, and release tags are untouched.

## Required Fixes

None.

## QA Evidence

Passed on the feature branch:

- `python -m osw.cli --version`
- `python -m osw.cli doctor`
- `python tools/qa/check_release_metadata.py --expected-version 0.1.0rc2 --expected-source-license GPL-3.0-or-later --allowed-prior-rc-tag v0.1.0-rc1 --allowed-prior-rc-target 29c5c8bec8df30c7f7be72fc9be5e5409794968e --expected-rc-tag v0.1.0-rc2 --expected-rc-target 684dc6138d4257564bbcdd176a9d5ed311a7316d --require-annotated-rc-tag`
- `python tools/qa/check_duplicate_test_basenames.py`
- `pytest tests/unit/test_duplicate_test_basenames.py -q`
- `pytest tests/gui/test_plugin_manager_dialog_gui.py tests/unit/test_plugin_manager_dialog_unit.py -q`
- `pytest tests/unit -q`
- `pytest tests/gui -q`
- `pytest -q --import-mode=importlib`
- `pytest tests/integration -q -m "not external_solver"`
- `pytest tests/golden -q`
- `pytest tests/validation -q`
- `pytest -q`
- `ruff check src tests`
- `python tools/qa/check_scope_drift.py`
- `python tools/qa/check_architecture_boundaries.py`
- `python tools/qa/check_no_solver_artifacts_committed.py`
- `python tools/qa/run_fast_qa.py`
- `python tools/qa/run_pre_merge_qa.py`
- `git diff --check`

Skipped:

- `python tools/qa/check_docs_links.py`: tool is absent. This remains the
  separate P2 docs-link checker follow-up and was not implemented here.

## Tag And Environment Safety

- `v0.1.0-rc1` remains an annotated tag pointing to
  `29c5c8bec8df30c7f7be72fc9be5e5409794968e`.
- `v0.1.0-rc2` remains an annotated tag pointing to
  `684dc6138d4257564bbcdd176a9d5ed311a7316d`.
- Final `v0.1.0` tag is absent.
- No tag was created, deleted, moved, overwritten, retargeted, or pushed.
- No branch push or remote change occurred.

## Generated/Runtime Artifact Check

`python tools/qa/check_no_solver_artifacts_committed.py` passed. The only
`.codex` files are prompt-required text reports.

## Residual Risks

- Once merged, this hardening commit advances `develop` beyond local rc2.
  `v0.1.0-rc2` remains historical local feedback evidence and must not be
  pushed as the current RC. A later RC3 tag gate is required for any current
  pushable RC.
- Docs link checker remains a separate P2 follow-up.
