# Optional solver plugin manifest export-summary GUI implementation

## Status

Implemented in OSW-EXP-099 as a bounded PySide review panel:

- module:
  `src/osw/gui/dialogs/optional_solver_plugin_manifest_export_summary_panel.py`
- public class: `OptionalSolverPluginManifestExportSummaryPanel`
- package export: `osw.gui.dialogs.OptionalSolverPluginManifestExportSummaryPanel`
- focused test:
  `tests/gui/test_optional_solver_plugin_manifest_export_summary_panel.py`

The panel is view-model driven, non-exporting, non-writing, non-persistent,
non-reloadable, non-installing, non-executing, non-mutating, and
issue/release-safe.

## Purpose

`OptionalSolverPluginManifestExportSummaryPanel` renders the OSW-EXP-097
`OptionalSolverPluginManifestExportSummaryViewModel` in a GUI review surface.
It implements the OSW-EXP-098 GUI design as a read-only panel for supplied
in-memory records.

The panel lets users inspect export summary header and counts, sections,
source/provenance rows, candidate summary rows, acknowledgement rows,
diagnostics, redaction/privacy rows, stale-source/re-preview rows,
conflict/shared-stack rows, unsafe-claim rows, evidence/history rows, limitation
rows, trust/provenance text, non-action flags, safety guidance, and
disabled/future action states.

## GUI flow

The initial state uses
`OptionalSolverPluginManifestExportSummaryViewModel.unavailable()` and shows
`unavailable_no_state` / `export_summary_unavailable`. Supplied view-models can
be installed through `set_view_model()`.

Acknowledgement interaction is optional, widget-local and non-persistent. If a
caller injects an acknowledgement callback, acknowledgement buttons update local
acknowledgement state and rebuild the supplied view-model. Without a callback,
acknowledgement rows and buttons are display-only.

No acknowledgement state is persisted by the panel.

## Rendered sections

The panel renders tables for sections, sources/provenance, candidates,
acknowledgements, diagnostics, redaction/privacy, stale sources and re-preview,
conflicts and shared stacks, unsafe claims, evidence/history, and limitations.

It renders plain-text panels for trust/provenance, non-action flags, safety
guidance, and action state.

## Header and summary behavior

The summary label renders summary kind, state scope, generated-by display, schema
version display, source count, candidate count, acknowledgement count,
diagnostic count, warning count, error count, conflict count, unsafe claim count,
stale source count, redaction required count, evidence retained count, history
retained count, limitation count, readiness, export-summary state, and explicit
false non-action flags.

The header states `export_performed=False`, `file_write_performed=False`,
`export_file_created=False`, `clipboard_performed=False`,
`report_attachment_performed=False`, `reloadable_bundle_created=False`,
`persistence_performed=False`, `validation_success_claimed=False`,
`validation_failure_claimed=False`, `issue_closure_claimed=False`,
`release_mutation_performed=False`, and `certification_claimed=False`.

## Diagnostics, trust, and provenance behavior

Diagnostics are rendered as review rows with severity, category, code, message,
source reference, stack id, suggested fix, and blocker state. The panel renders
`OSPMG_EXPORT_SUMMARY_*` diagnostics from the view-model and keeps
`OSPMG_EXPORT_SUMMARY_GUI_*` as design vocabulary in the OSW-EXP-098 design doc.

Trust/provenance text states that user-selected and plugin-provided manifests are
untrusted by default, built-ins are authoritative by default, trust labels are
not certification, and export summaries are not validation evidence, validation
success, validation failure, persistence, reloadable bundles, automatic
activation, or trust restoration.

## Redaction and stale-source behavior

Redaction rows show raw-reference state, display reference, redaction status,
redaction-required state, unredacted-path blocking, redaction-reviewed state,
secret-like content blocking, privacy warnings, and fingerprint-is-not-trust
signal state.

Stale-source rows state that old preview data is not silently trusted and that no
file IO, file restoration, file rewrite, or file deletion is performed. Stale,
missing, moved, or changed source data requires re-preview or a future policy
gate.

## History, conflict, unsafe-claim, and limitation behavior

Evidence/history rows keep deactivation history, reactivation history, and
historical validation evidence visible. Skipped-missing remains skipped-missing.
Export summaries do not imply issue closure, validation success, validation
failure, evidence deletion, or evidence rewrite.

Conflict/shared-stack rows keep built-ins winning by default and show that
exported user/plugin state does not override built-ins silently. Unsafe claims
are rendered as blocked and not accepted by export summaries. Limitations are
rendered as first-class visible rows.

## Non-actions

This implementation explicitly performs:

- no file export
- no file writes
- no export file creation
- no report file creation
- no clipboard behavior
- no report attachment
- no open-output-folder behavior
- no reloadable bundle creation
- no runtime persistence behavior
- no settings file creation
- no runtime state file creation
- no schema file creation
- no ProjectSchema mutation
- no CLI behavior
- no reload behavior
- no source behavior mutation
- no automatic activation
- no trust restoration
- no file restoration
- no file rewrite
- no file deletion
- no dependency installation
- no dependency uninstall
- no solver uninstall
- no plugin package import
- no directory scan
- no network fetch
- no discovery execution
- no validation execution
- no solver execution
- no issue mutation
- no release mutation
- no tag mutation
- no asset mutation
- no version bump
- no validation-pass claim
- no validation-fail claim
- no issue-closure claim
- no bundled-solver claim
- no certification claim

## Relationship to prior gates

OSW-EXP-091 defined export-summary semantics. OSW-EXP-097 implemented the pure
export-summary view-model. OSW-EXP-098 defined the export-summary GUI safety
contract. OSW-EXP-099 implements only the bounded GUI review surface over that
view-model.

The export-summary view-model remains free of PySide/Qt imports.

## Relationship to live optional validation issues

issues `#6` through `#11` remain open. Export-summary GUI review is not live
optional validation, not validation success, not validation failure, and not
issue-closure evidence.

Package metadata remains `0.1.5rc1`, and the public prerelease remains
`v0.1.5-rc1`.

## Future gates

Future gates remain required for file export, clipboard behavior, report
attachment, reloadable bundle creation, CLI export, persistence writer, settings
files, ProjectSchema integration, report integration, source integration,
discovery integration, validation, dependency install/uninstall behavior, solver
uninstall behavior, solver execution behavior, issue/release/tag/asset mutation,
and validation or certification claims.
