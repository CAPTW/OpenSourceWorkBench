# Optional solver plugin manifest GUI view-model

## Status

Experimental pure view-model implemented.

This gate adds GUI-ready display records for already-built optional solver
plugin manifest loader reports.

Status boundaries:

- no GUI implementation
- no file dialog
- no plugin package loading
- no directory scan
- no network fetch
- no solver execution
- no dependency installation

## Relationship to GUI design and CLI preview

The view-model implements the pure boundary described by
[Optional solver plugin manifest GUI design](optional_solver_plugin_manifest_gui_design.md).
It consumes the same loader report semantics shown by
`optional-solver-plugin-manifest-preview`.

The CLI remains the automation-oriented preview surface. This view-model is the
future GUI display contract for summary headers, tables, trust badges,
diagnostics, guidance, and disabled action states.

## Package path and public API

Package path:

`src/osw/experimental/optional_solvers/plugin_manifest_gui_viewmodel.py`

Public API:

- `OptionalSolverPluginManifestGuiViewModel`
- `OptionalSolverPluginManifestSummaryViewModel`
- `OptionalSolverPluginManifestAcceptedRowViewModel`
- `OptionalSolverPluginManifestRejectedRowViewModel`
- `OptionalSolverPluginManifestConflictRowViewModel`
- `OptionalSolverPluginManifestDiagnosticRowViewModel`
- `OptionalSolverPluginManifestTrustBadgeViewModel`
- `OptionalSolverPluginManifestAction`
- `OptionalSolverPluginManifestActionState`
- `build_optional_solver_plugin_manifest_gui_viewmodel`
- `summarize_optional_solver_plugin_manifest_gui_viewmodel`
- `explain_optional_solver_plugin_manifest_gui_viewmodel`

## Input load report

The builder consumes an `OptionalSolverPluginManifestLoadReport` that was
created by the loader model.

The view-model does not load files, parse JSON, open file dialogs, import
plugin packages, scan directories, fetch manifests from a network, run
discovery, execute solvers, or install dependencies.

Optional display inputs are selected stack id, filter text, trust filters, and
source filters.

## Summary model

The summary model records total and visible counts for accepted manifests,
rejected manifests, conflicts, and diagnostics.

The status text states that the preview is not validation evidence.

## Accepted manifest rows

Accepted manifest rows include stack id, display name, source type, source
label/reference, trust label, related issue, support status, capabilities
summary, and not-validation-evidence text. The capabilities summary is a
compact comma-separated list for table display.

Accepted means loader policy accepted the manifest metadata for preview. It
does not mean the plugin, package, solver, or environment passed validation.

## Rejected manifest rows

Rejected manifest rows include stack id, source type, source label/reference,
trust label, rejection reason, diagnostics, suggested fix, and unsafe claim
indicators.

Unsafe claim indicators cover installer command wording, executable code
references, external-solver bundling claims, and certification claims.

## Conflict rows

Conflict rows include duplicate stack id, winning source/trust, rejected
source/trust, source references, the loader message, built-ins-win text, and
plugin-override-disabled text.

Plugin overrides remain disabled by default.

## Diagnostics rows

Diagnostic rows preserve severity, category, code, message, source reference,
stack id, and suggested fix from the loader diagnostics.

## Trust badge model

Trust badges collect source/trust labels from accepted, rejected, and conflict
records.

The badge text warns that third-party/plugin manifests are not trusted by
default and that a trust label is not certification.

## Action-state model

Action states are display placeholders only:

- choose explicit JSON files: future/display-only
- activate manifest: unavailable
- run discovery with plugin manifests: unavailable
- run validation: unavailable
- install solver: unavailable
- close issue: unavailable

File dialogs, manifest activation, discovery with plugin manifests, validation,
installer behavior, and issue closure remain outside this gate.

## Safety boundary

The view-model is data-only preview.

- not validation evidence
- no plugin code execution
- no plugin package loading
- no directory scan
- no network fetch
- no solver execution
- no install actions
- no issue closure action

Third-party/plugin manifests are not trusted by default. External solvers are
not bundled.

## Relationship to health panel

A future GUI can display loader reports through this view-model.

No activation is performed in this gate. Discovery refresh remains built-in
unless a future activation model explicitly accepts plugin manifests.

Export summaries should not include plugin preview data until a separate future
integration gate defines that behavior.

## GUI implementation follow-up

[Optional solver plugin manifest GUI implementation](optional_solver_plugin_manifest_gui_implementation.md)
adds the PySide display component over this view-model. The component renders
summary counts, accepted/rejected/conflict rows, diagnostics, trust badges,
safety text, and disabled action states from already-built view-model records.

The GUI implementation adds no file dialog, file loading, plugin loading,
plugin activation, plugin package import, directory scan, network fetch,
discovery execution, solver execution, dependency installation, issue mutation,
release mutation, validation-pass claim, issue-closure claim, bundled-solver
claim, or certification claim.

## Future gates

- `OSW-EXP-074_OPTIONAL_SOLVER_PLUGIN_MANIFEST_GUI_IMPLEMENTATION`
- `OSW-EXP-075_OPTIONAL_SOLVER_PLUGIN_MANIFEST_ACTIVATION_DESIGN`
- `OSW-VALID` prepared-machine validation reuse
