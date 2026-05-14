# Self-Check: OSW-AUTO-033_PLUGIN_INSTALL_FOLDER_ZIP

## Step ID

OSW-AUTO-033_PLUGIN_INSTALL_FOLDER_ZIP

## Branch / Worktree

- Branch: `feature/osw-p10-1-plugin-install`
- Worktree: `C:\Users\USER\source\repos\_worktrees\osw-p10-1-plugin-install`
- Base branch: `develop`

## Files Changed

- `src/osw/plugins/installer.py`
- `src/osw/plugins/__init__.py`
- `src/osw/gui/plugin_manager_dialog.py`
- `tests/unit/test_plugin_install.py`
- `tests/gui/test_plugin_manager_dialog.py`
- `.codex/reports/self_check/OSW-AUTO-033_PLUGIN_INSTALL_FOLDER_ZIP.md`

## Scope Summary

Implemented a local-only plugin install MVP for folder and zip sources. The
installer validates only plugin manifest files, copies valid local plugin
packages into a managed install root, reports dependency health messages, detects
duplicate plugin ids, rejects invalid manifests, and prevents zip path traversal.

The GUI Plugin Manager now exposes folder/zip install actions and refreshes the
manifest inventory after install. It continues to persist enable/disable state
through the existing `PluginEnablementStore`.

No remote plugin store, network install, plugin code execution during validation,
solver adapter changes, or external solver execution were added.

## Coverage Summary

- Valid folder install covered.
- Valid zip install covered.
- Invalid manifest rejection covered.
- Duplicate plugin id detection covered for installed plugins and externally
  discovered ids.
- Missing dependency warning covered without blocking install.
- Zip path traversal rejection covered.
- Plugin code non-execution during manifest validation covered with a sentinel
  file test.
- GUI integration covered by optional PySide6 smoke test for install controls.

## Commands Run

- `git status --short`
- `git branch --show-current`
- `git worktree list`
- `git show-ref --verify --quiet refs/heads/develop`
- `pytest tests/unit/test_plugin_install.py tests/gui/test_plugin_manager*.py -q`
- `pytest tests/unit/test_plugin_install.py tests/gui/test_plugin_manager_dialog.py -q`
- `ruff check src tests`
- `pytest tests/unit -q`
- `python tools/qa/run_fast_qa.py`
- `python tools/qa/check_scope_drift.py`
- `python tools/qa/check_architecture_boundaries.py`
- `python tools/qa/check_no_solver_artifacts_committed.py`

## Command Results

- Preflight: base worktree clean, current branch `develop`, `develop` exists.
- Feature worktree created on `feature/osw-p10-1-plugin-install`.
- Requested focused pytest command with literal wildcard:
  `pytest tests/unit/test_plugin_install.py tests/gui/test_plugin_manager*.py -q`
  failed before collection because PowerShell passed the wildcard literally to
  pytest: `file or directory not found: tests/gui/test_plugin_manager*.py`.
- Expanded focused pytest:
  `pytest tests/unit/test_plugin_install.py tests/gui/test_plugin_manager_dialog.py -q`
  passed: `7 passed, 1 skipped`.
- `ruff check src tests` passed.
- `pytest tests/unit -q` passed: `194 passed, 3 skipped`.
- `python tools/qa/run_fast_qa.py` passed, including CLI smoke, doctor, Ruff,
  and unit tests.
- `python tools/qa/check_scope_drift.py` passed.
- `python tools/qa/check_architecture_boundaries.py` passed.
- `python tools/qa/check_no_solver_artifacts_committed.py` passed.

## Skipped Checks

- `tests/gui/test_plugin_manager_dialog.py` skipped locally because PySide6 is
  an optional GUI extra and is not installed in this environment.
- `tools/qa/check_docs_links.py` is not present; not required for this
  implementation step and not created.

## Remaining Risks

- The installer is intentionally local-only and does not verify plugin package
  signatures.
- Zip install supports a single manifest per archive for v0.1; multi-plugin
  bundles are rejected.
- GUI install dialogs were not exercised interactively because PySide6 is not
  installed locally; non-GUI model and installer behavior are unit-tested.

## Amend Review-01 Update

Initial review scored 86/100 and required two fixes before merge:

- Prevent Plugin Manager install refresh from reloading entry-point plugins,
  because entry-point loading can import package code during the install flow.
- Make installed plugin directory naming collision-resistant for distinct valid
  plugin ids such as `demo.a-b`, `demo.a_b`, and `demo.a.b`.

Amend branch:
`amend/osw-p10-1-plugin-install-review-01`

Amend worktree:
`C:\Users\USER\source\repos\_worktrees\osw-p10-1-plugin-install-amend-01`

Amend command results:

- Focused expanded pytest:
  `pytest tests/unit/test_plugin_install.py tests/gui/test_plugin_manager_dialog.py -q`
  passed: `9 passed, 1 skipped`.
- `ruff check src tests` passed.
- `pytest tests/unit -q` passed: `196 passed, 3 skipped`.
- `python tools/qa/run_fast_qa.py` passed.
- `python tools/qa/check_scope_drift.py` passed.
- `python tools/qa/check_architecture_boundaries.py` passed.
- `python tools/qa/check_no_solver_artifacts_committed.py` passed.

## Merge Recommendation

Recommend merge after amended review. The change stays within the plugin install
and Plugin Manager scope and has focused regression coverage for the review
fixes.
