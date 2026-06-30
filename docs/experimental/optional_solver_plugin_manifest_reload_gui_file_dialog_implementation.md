# Optional Solver Plugin Manifest Reload GUI File Dialog Implementation

## 1. Status

Experimental reload GUI file-dialog preview is implemented.

The implemented panel is
`OptionalSolverPluginManifestReloadFileDialogPanel` in
`src/osw/gui/dialogs/optional_solver_plugin_manifest_reload_file_dialog_panel.py`.
It is a reader-first, review-only wrapper around
`OptionalSolverPluginManifestReloadFileReader`,
`OptionalSolverPluginManifestReloadViewModel.from_payload_mapping`, and
`OptionalSolverPluginManifestReloadPanel`.

The implementation adds an explicit file-dialog action, but no native dialog on
construction. It adds no default reload path, no background reload, no directory
scan, no network fetch, no plugin package import, no CLI subprocess, no runtime
reload acceptance, no ProjectSchema mutation, no discovery/validation/solver
execution, no automatic activation, no trust restoration, no issue/release/tag/
asset mutation, no version bump, and no validation-pass/fail, issue-closure,
bundled-solver, or certification claim.

Downstream guardrail phrase: no native dialog on construction.

Downstream guardrail phrase: no directory scan.

Downstream guardrail phrase: no validation execution.

Downstream guardrail phrase: no solver execution.

Downstream guardrail phrase: no automatic activation.

Downstream guardrail phrase: no trust restoration.

## 2. Purpose

This gate implements the OSW-EXP-116 GUI file-dialog design as an outer
chooser/controller for reload preview. The existing OSW-EXP-109 reload panel
remains pure view-model rendering. File selection and reader invocation are
isolated in the wrapper.

The wrapper previews one user-selected state-writer UX state file. It never
accepts that state as trusted runtime state.

## 3. Public GUI Surface

The panel exposes:

- `open_file_dialog()` for explicit file-dialog action;
- `load_selected_file(path)` for testable explicit-path loading without a native
  dialog;
- `clear_preview()` for widget-local reset;
- `reader_status_text()`, `reader_diagnostics_text()`, `action_state_text()`,
  `safety_text()`, `selected_file_text()`, and `summary_text()` for focused GUI
  assertions;
- `preview_summary_text()` and `preview_diagnostics_text()` from the embedded
  reload review panel;
- `has_view_model_preview()` and `last_reader_result()` for test-only state
  inspection.

The package lazy export now exposes
`OptionalSolverPluginManifestReloadFileDialogPanel` from `osw.gui.dialogs`.

## 4. Dependency Injection

The constructor accepts injectable file picker, reader, request factory, and
view-model factory callables. Focused GUI tests use those injections to verify
that construction opens no native dialog, performs no file read, invokes no CLI
bridge, and creates no output files.

The default picker is only called by `open_file_dialog()`. The default reader
request uses the conservative OSW-EXP-113 reader defaults and a GUI caller
context.

## 5. Reader-First Flow

The GUI flow is:

1. User invokes the explicit file-dialog action.
2. The picker returns one selected path or no path.
3. cancelled selection is non-error and reads no file.
4. A selected path is passed to
   `OptionalSolverPluginManifestReloadFileReader.read(...)`.
5. Reader diagnostics render before the reload review panel is updated.
6. reader blockers suppress view-model construction.
7. Only reader `safe_mapping` output feeds
   `OptionalSolverPluginManifestReloadViewModel.from_payload_mapping(...)`.
8. The existing `OptionalSolverPluginManifestReloadPanel` renders the resulting
   view-model for review only.

Reader-blocked states do not synthesize a partial view-model. A blocked
follow-up read updates reader diagnostics but preserves the prior successful
preview until the user clears it or previews another valid file.

## 6. Cancellation And Error Behavior

Cancellation performs no file read, no state parse, no runtime reload, and no
ProjectSchema mutation. It is displayed as an informational GUI diagnostic and
preserves any prior preview.

Injected file picker, reader, or view-model construction failures are converted
to internal GUI diagnostics. The diagnostic text avoids raw path and secret
display and never claims validation failure.

## 7. Redaction And Privacy

Selected-file display uses the reader redacted target display. The GUI does not
render raw absolute target paths by default. Reader diagnostics remain the
source of redaction, secret-like-value, unsafe-claim, stale-source, conflict,
schema, and payload-kind decisions.

File dialog filters are hints only. They are not trust signals.

## 8. Relationships

- Reload file reader: the GUI is a thin consumer of the OSW-EXP-113 reader.
- Reload view-model: only reader `safe_mapping` enters the OSW-EXP-107
  view-model path.
- Reload panel: the OSW-EXP-109 panel remains the read-only review renderer.
- Reload CLI: the GUI does not call the OSW-EXP-115 CLI as a subprocess.
- State writer: the GUI previews state-writer UX state files but never rewrites,
  repairs, migrates, or deletes them.
- ProjectSchema: reloaded UX state is not ProjectSchema state.

Issues `#6` through `#11` remain open and separate from reload preview output.

Downstream issue-boundary phrase: issues `#6` through `#11` remain open.

## 9. Non-Actions

This gate does not add default reload paths, background reload, directory scans,
network fetches, plugin package imports, CLI subprocess use, runtime reload
acceptance, reloadable bundle creation, export files, report files, clipboard
behavior, report attachments, open-output-folder behavior, ProjectSchema
mutation, live discovery, passive refresh, validation execution, solver
execution, dependency installation, dependency uninstall, solver uninstall,
automatic activation, trust restoration, issue mutation, release mutation, tag
mutation, asset mutation, version bump, validation-pass claim, validation-fail
claim, issue-closure claim, bundled-solver claim, or certification claim.

The GUI wrapper writes, creates, deletes, exports, and reports no files.

## 10. Testing Strategy

`tests/gui/test_optional_solver_plugin_manifest_reload_file_dialog_panel.py`
covers lazy export, inert construction, explicit loading through the reader,
embedded reload review panel rendering, cancelled selection, blocked reader
diagnostics, view-model construction suppression on blockers, prior preview
preservation after blocked follow-up reads, injected dependency error handling,
local clear behavior, no raw path display, no output file creation, and source
guardrails against directory scans, network calls, CLI imports, ProjectSchema
imports, plugin discovery, solver execution, and file writes.

Adjacent continuity checks should continue to cover the OSW-EXP-109 reload
panel, OSW-EXP-113 reader, OSW-EXP-115 CLI explicit-path preview, and
OSW-EXP-107 reload view-model.

## 11. Future Gates

Runtime reload acceptance, activation review, discovery refresh, ProjectSchema
integration, validation, issue/release workflows, export/report integration, and
certification remain future-gated.
