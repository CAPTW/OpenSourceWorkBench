# OSW-AUTO-047 Default Pytest Collection Fix Self-Check

## Scope

This step fixes the default `pytest -q` collection import mismatch caused by
duplicate test module basenames. It does not change product source code,
package version metadata, license metadata, release tags, or docs-link checker
behavior.

## Original Failure

Reproduced from `develop` before creating the feature worktree:

```text
ERROR collecting tests/unit/test_plugin_manager_dialog.py
import file mismatch:
imported module 'test_plugin_manager_dialog' has this __file__ attribute:
  C:\Users\USER\source\repos\Workbench\tests\gui\test_plugin_manager_dialog.py
which is not the same as the test file we want to collect:
  C:\Users\USER\source\repos\Workbench\tests\unit\test_plugin_manager_dialog.py
```

## Implementation

- Renamed `tests/gui/test_plugin_manager_dialog.py` to
  `tests/gui/test_plugin_manager_dialog_gui.py`.
- Renamed `tests/unit/test_plugin_manager_dialog.py` to
  `tests/unit/test_plugin_manager_dialog_unit.py`.
- Added `tools/qa/check_duplicate_test_basenames.py` to scan `tests/**/*.py`
  without importing test modules and fail on duplicate basenames.
- Added `tests/unit/test_duplicate_test_basenames.py` for duplicate, unique,
  nested-path reporting, and `__init__.py` ignore behavior.
- Added the duplicate-basename check to `tools/qa/run_fast_qa.py`; pre-merge QA
  picks it up through the fast QA runner.
- Updated release checklist, risk register, and decision log to mark the known
  default pytest collection issue resolved and keep docs-link checking as a
  separate P2 follow-up.

## Feature Branch QA

Passed:

- `python -m osw.cli --version`: `osw 0.1.0rc2`
- `python -m osw.cli doctor`
- `python tools/qa/check_release_metadata.py --expected-version 0.1.0rc2 --expected-source-license GPL-3.0-or-later --allowed-prior-rc-tag v0.1.0-rc1 --allowed-prior-rc-target 29c5c8bec8df30c7f7be72fc9be5e5409794968e --expected-rc-tag v0.1.0-rc2 --expected-rc-target 684dc6138d4257564bbcdd176a9d5ed311a7316d --require-annotated-rc-tag`
- `python tools/qa/check_duplicate_test_basenames.py`
- `pytest tests/unit/test_duplicate_test_basenames.py -q`: `4 passed`
- `pytest tests/gui/test_plugin_manager_dialog_gui.py tests/unit/test_plugin_manager_dialog_unit.py -q`: `5 passed, 1 skipped`
- `pytest tests/unit -q`: `230 passed, 3 skipped`
- `pytest tests/gui -q`: `10 skipped`
- `pytest -q --import-mode=importlib`: `248 passed, 19 skipped`
- `pytest tests/integration -q -m "not external_solver"`:
  `4 passed, 3 skipped, 3 deselected`
- `pytest tests/golden -q`: `10 passed`
- `pytest tests/validation -q`: `4 passed`
- `pytest -q`: `248 passed, 19 skipped`
- `ruff check src tests`
- `python tools/qa/check_scope_drift.py`
- `python tools/qa/check_architecture_boundaries.py`
- `python tools/qa/check_no_solver_artifacts_committed.py`
- `python tools/qa/run_fast_qa.py`
- `python tools/qa/run_pre_merge_qa.py`
- `git diff --check`

Skipped:

- `python tools/qa/check_docs_links.py`: tool is absent. This remains the
  existing separate P2 follow-up and was not implemented here.

## Tag Preservation Evidence

Before review:

- `v0.1.0-rc1` object type: `tag`
- `v0.1.0-rc1` peeled commit:
  `29c5c8bec8df30c7f7be72fc9be5e5409794968e`
- `v0.1.0-rc2` object type: `tag`
- `v0.1.0-rc2` peeled commit:
  `684dc6138d4257564bbcdd176a9d5ed311a7316d`
- `v0.1.0`: absent

No tag was created, deleted, moved, overwritten, retargeted, or pushed.

## Remaining Risks

- `tools/qa/check_docs_links.py` remains absent and should be handled by
  `OSW-AUTO-048_DOCS_LINK_CHECKER_IMPLEMENTATION`.
- After this prompt merges, local `v0.1.0-rc2` remains historical feedback
  evidence and no longer represents current `develop`; a later RC3 tag gate is
  required if a current pushable RC is needed.
