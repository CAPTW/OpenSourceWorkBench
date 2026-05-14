# Review: OSW-AUTO-033_PLUGIN_INSTALL_FOLDER_ZIP

Decision:
Approve after amend.

Score:
96/100

Checkpoint:
`2a21a77 checkpoint(033): Plugin Install from Folder/Zip before review`

Amend:
`amend/osw-p10-1-plugin-install-review-01`

## Initial Review Findings

Critical issues:
None.

High issues:
None after amend.

Medium issues fixed:

- Plugin Manager install refresh reloaded entry-point plugins, which could load
  installed package code during the install flow. Fixed by refreshing local
  manifests with `include_entry_points=False` and preserving already-discovered
  entry-point rows without reloading them.
- Installed plugin directory naming collapsed distinct valid ids such as
  `demo.a-b`, `demo.a_b`, and `demo.a.b`. Fixed by encoding the exact plugin id
  with URL-safe base64 for the install directory name.

Low issues:
None blocking.

## Scope Review

The diff stays within the approved plugin installer, Plugin Manager dialog,
focused tests, and required Codex reports. It does not add a remote plugin
store, network install path, solver adapter behavior, external execution, native
commercial CAD import, Simulink or `.mlapp` support, or industrial validation
claims.

## Architecture Review

The installer lives in `osw.plugins` and uses manifest and health contracts. GUI
code calls the installer service and does not run subprocesses or solver code.
Manifest validation reads only manifest files and does not import plugin module
entry points. Entry-point discovery remains existing inventory behavior, but is
not re-run as part of the install refresh.

## Checklist Completeness Review

Covered acceptance criteria:

- Valid folder installs.
- Valid zip installs.
- Invalid manifest rejected.
- Duplicate plugin id detected against installed and currently discovered ids.
- Zip traversal blocked before extraction.
- Plugin code is not executed during manifest validation.
- Dependency warnings are surfaced without making optional dependencies
  mandatory.
- Existing enable/disable persistence is retained through `PluginEnablementStore`.
- Plugin Manager exposes folder and zip install controls.

## Wording / Safety Review

No user-facing text claims external solver execution, remote install, native
commercial CAD support, full solver coverage, or certification. Install status
messages distinguish successful install from warnings and rejected installs.

## QA Evidence Review

Commands run:

- `pytest tests/unit/test_plugin_install.py tests/gui/test_plugin_manager*.py -q`
  failed before collection because PowerShell passed the wildcard literally to
  pytest.
- `pytest tests/unit/test_plugin_install.py tests/gui/test_plugin_manager_dialog.py -q`
  passed after explicit expansion: `9 passed, 1 skipped`.
- `ruff check src tests` passed.
- `pytest tests/unit -q` passed: `196 passed, 3 skipped`.
- `python tools/qa/run_fast_qa.py` passed.
- `python tools/qa/check_scope_drift.py` passed.
- `python tools/qa/check_architecture_boundaries.py` passed.
- `python tools/qa/check_no_solver_artifacts_committed.py` passed.

Skipped checks:

- PySide6 GUI test body skipped locally because PySide6 is an optional GUI extra
  and is not installed.

## Required Amend Items

None remaining.

## Generated / Runtime Artifact Check

`python tools/qa/check_no_solver_artifacts_committed.py` passed. The required
Codex reports are staged intentionally for this autopilot step.

## Final Merge Recommendation

Merge possible. Score is above 90 and no hard blockers remain.
