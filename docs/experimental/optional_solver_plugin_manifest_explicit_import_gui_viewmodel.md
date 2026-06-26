# Optional solver plugin manifest explicit import GUI view-model

## Status

Experimental pure view-model implemented.

This gate (OSW-EXP-076) implements the pure, side-effect-free view-model layer
for the explicit plugin manifest JSON import/preview GUI designed in
OSW-EXP-075.

Status boundaries:

- pure Python view-model
- no GUI widget
- no QFileDialog
- no file dialog
- no file loading
- no JSON parsing from a path
- no plugin activation
- no plugin package import
- no directory scan
- no network fetch
- no discovery execution
- no solver execution
- no dependency installation

## Purpose

Translate already-supplied explicit-import loader/report data (or a
caller-supplied import state such as cancel or an import error) into
deterministic, GUI-ready records that a future explicit-import surface can bind
to without performing any side effects.

The view-model is an adapter over already-produced loader reports, not a loader
itself. File selection, reading, and parsing belong to a future runner
(OSW-EXP-077).

## Public module and class names

Module:

`src/osw/experimental/optional_solvers/plugin_manifest_explicit_import_gui_viewmodel.py`

Public view-model and records:

- `OptionalSolverPluginManifestExplicitImportGuiViewModel`
- `OptionalSolverPluginManifestExplicitImportSummaryViewModel`
- `OptionalSolverPluginManifestExplicitImportSourceRowViewModel`
- `OptionalSolverPluginManifestExplicitImportDiagnosticViewModel`
- `OptionalSolverPluginManifestExplicitImportActionState`
- `OptionalSolverPluginManifestExplicitImportAction`
- `OptionalSolverPluginManifestExplicitImportState`

Builders and helpers:

- `build_optional_solver_plugin_manifest_explicit_import_gui_viewmodel`
- `build_optional_solver_plugin_manifest_explicit_import_empty_viewmodel`
- `build_optional_solver_plugin_manifest_explicit_import_cancelled_viewmodel`
- `build_optional_solver_plugin_manifest_explicit_import_error_viewmodel`
- `redact_optional_solver_plugin_manifest_source_reference`
- `render_optional_solver_plugin_manifest_explicit_import_summary`
- `summarize_optional_solver_plugin_manifest_explicit_import_gui_viewmodel`
- `explain_optional_solver_plugin_manifest_explicit_import_gui_viewmodel`

The view-model class also exposes convenience constructors `from_loader_report`,
`from_cancelled_selection`, `from_no_selection`, and `from_import_diagnostics`.

## Input boundary

The view-model consumes supplied reports/records only:

- an already-built `OptionalSolverPluginManifestLoadReport`
- accepted/rejected/conflict/diagnostic records inside that report
- caller-supplied explicit-import diagnostics for cancel/missing/unreadable
  states
- safe display strings and precomputed counts

It does not read or parse files. It does not call the loader, open files, parse
JSON from a path, import plugin packages, scan directories, or fetch URLs. A
future runner supplies the report; this layer only transforms it.

## Rendered view-model sections

- summary (counts, state, honesty flags)
- selected source rows (redacted references)
- accepted/rejected/conflict rows (reused from the OSW-EXP-074 GUI view-model
  row semantics)
- loader diagnostic rows
- explicit-import (`OSPMG_IMPORT_*`) diagnostics
- trust/source badges
- action states (display/future/unavailable)
- guidance text and safety guidance

The summary carries explicit honesty flags that remain false: `preview_only`
is true while `activation_performed`, `discovery_execution_performed`,
`solver_execution_performed`, and `dependency_installation_performed` are
false, and `third_party_manifests_trusted_by_default` /
`external_solvers_bundled` are false.

## Source redaction behavior

`redact_optional_solver_plugin_manifest_source_reference` is a pure helper that
avoids exposing sensitive absolute paths by default:

- a caller-provided safe label is preserved (not redacted)
- path-like references are shortened to their final segment and marked redacted
- non-path references (for example `builtin:gmsh`) are kept as-is
- the helper never inspects the filesystem, never calls `Path.exists()`, and
  never opens files

Source rows display the redacted reference and a redaction flag.

## Diagnostic vocabulary

The view-model uses the design-only `OSPMG_IMPORT_*` vocabulary reserved in
OSW-EXP-075:

- `OSPMG_IMPORT_CANCELLED`
- `OSPMG_IMPORT_FILE_MISSING`
- `OSPMG_IMPORT_UNREADABLE`
- `OSPMG_IMPORT_UNSUPPORTED_EXTENSION`
- `OSPMG_IMPORT_FILE_TOO_LARGE`
- `OSPMG_IMPORT_INVALID_JSON`
- `OSPMG_IMPORT_SCHEMA_INVALID`
- `OSPMG_IMPORT_CONFLICT`
- `OSPMG_IMPORT_UNTRUSTED_SOURCE`
- `OSPMG_IMPORT_PREVIEW_ONLY`

The full tuple is exposed as `OSPMG_IMPORT_DIAGNOSTIC_CODES` and on each
view-model as `reserved_import_diagnostic_codes`. Loader diagnostics
(`OSPL_*`) are translated into these GUI-import codes for source-row status and
import diagnostics. A persistent `OSPMG_IMPORT_PREVIEW_ONLY` marker is always
present. None of these diagnostics are validation-pass evidence.

## Action-state safety behavior

Only safe display/preview/export-planning states may be enabled:

- `preview_selected_manifest_json` (display-only) and
  `export_redacted_summary` (in-memory only) are enabled when preview data is
  present.
- `choose_explicit_json_files` is future-only and disabled (the file dialog is a
  future implementation gate).
- `activate_manifest`, `run_discovery_with_plugin_manifests`, `run_validation`,
  `install_solver`, and `close_issue` are disabled and unavailable, each with an
  explicit disabled reason.

## Relationship to OSW-EXP-075 design

This gate implements the pure view-model layer that the OSW-EXP-075 design
document specified, while file-dialog implementation and file loading remain
future-gated. It preserves the design's preview-only, untrusted-by-default, and
preview-is-not-activation boundaries.

## Relationship to OSW-EXP-074 display panel

The view-model reuses the OSW-EXP-074 GUI view-model row semantics (accepted,
rejected, conflict, diagnostic, and trust-badge records) so the display panel
contract is unchanged. It does not require PySide6 and adds no GUI widgets.

## Relationship to loader/CLI preview

The view-model preserves the same accepted/rejected/conflict/diagnostic/source/
trust semantics as the loader model and the
`optional-solver-plugin-manifest-preview` CLI. It changes no CLI behavior.

## GUI implementation follow-up

[Optional solver plugin manifest explicit import GUI implementation](optional_solver_plugin_manifest_explicit_import_gui_implementation.md)
adds the PySide panel that binds this pure view-model to an explicit
user-initiated local JSON chooser and the existing loader/report semantics. The
implementation keeps this view-model pure: no PySide/Qt import, no file IO, no
JSON parsing from paths, no activation, no discovery execution, no validation
execution, no solver execution, no dependency installation, and no issue or
release mutation is added to this module.

## Relationship to health panel and export summary

Previewing a user-selected manifest is not health validation and does not alter
passive discovery. The view-model distinguishes preview data, passive discovery
data, validation evidence, and issue-closure evidence. The in-memory redacted
summary helper writes no files, touches no clipboard, and opens no shell,
browser, or output folder.

## Non-actions

This gate does not:

- implement a GUI widget
- import PySide/Qt
- implement QFileDialog
- load files
- parse JSON from a GUI source or a path
- activate plugin manifests
- import plugin packages
- scan directories
- fetch network manifests
- run discovery
- run validation
- install dependencies
- execute solvers
- mutate issues
- mutate releases
- mutate tags or assets
- bump versions
- make any validation-pass claim, issue-closure claim, bundled-solver claim, or
  certification claim

User-selected and plugin-provided manifests remain untrusted preview data only.
Skipped-missing optional validation remains neither pass nor failure, and issues
`#6` through `#11` stay open.

## Future gates

- `OSW-EXP-077_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPLICIT_IMPORT_GUI_IMPLEMENTATION`
- `OSW-EXP-078_OPTIONAL_SOLVER_PLUGIN_MANIFEST_ACTIVATION_DESIGN`
- `OSW-VALID` prepared-machine validation reuse
