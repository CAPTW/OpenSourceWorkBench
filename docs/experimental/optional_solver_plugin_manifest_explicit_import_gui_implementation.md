# Optional solver plugin manifest explicit import GUI implementation

## Status

Experimental PySide explicit import preview GUI implemented.

This panel is preview-only. It adds no activation, no discovery execution, no
solver execution, no dependency installation, no issue mutation, and no release
mutation.

Boundary summary: preview-only; no activation; no discovery execution; no solver execution; no dependency installation; no issue mutation; no release mutation.

Activation follow-up: [Optional solver plugin manifest activation design](optional_solver_plugin_manifest_activation_design.md)
(OSW-EXP-078) defines the future, design-only activation contract. This panel
remains preview-only; activation is a separate future gate.

## Purpose

The panel lets a user explicitly choose one local plugin manifest JSON file and
preview the resulting loader/report state. It is a GUI binding over the
existing plugin manifest loader/report semantics and the OSW-EXP-076 explicit
import view-model.

## Public module and class names

Module:

`src/osw/gui/dialogs/optional_solver_plugin_manifest_explicit_import_panel.py`

Public class:

- `OptionalSolverPluginManifestExplicitImportPanel`

Lazy package export:

- `osw.gui.dialogs.OptionalSolverPluginManifestExplicitImportPanel`

## User flow

Initial state:

- no selected sources
- preview-only guidance is visible
- activation, discovery, validation, install, close-issue, and export actions
  are disabled or future-only

Choose JSON:

- the user presses `Choose plugin manifest JSON`
- the panel calls an injected chooser, or `QFileDialog.getOpenFileName` with
  `JSON files (*.json)` from this GUI layer
- the selected path is checked before loader execution
- the existing loader builds the report
- the OSW-EXP-076 view-model renders the preview state

Cancel/no-op:

- a cancelled chooser result preserves the current panel state
- no file is opened, read, parsed, activated, installed, or executed

Unsupported, missing, unreadable, invalid, schema-invalid, and conflict states:

- unsupported extensions, missing paths, directories, URLs, unreadable paths,
  and oversized files are surfaced as import diagnostics before or instead of
  loader execution
- invalid JSON and schema-invalid manifests preserve existing loader
  diagnostics and map into `OSPMG_IMPORT_*` diagnostics through the view-model
- conflicts are rendered as preview rows; built-ins win by default

## Rendered sections

- summary counts and state
- selected source rows with redacted source references
- accepted manifest rows
- rejected manifest rows
- conflict rows
- loader and explicit-import diagnostics
- trust/source labels
- safety guidance
- action states

## File selection boundary

The GUI supports explicit local JSON only:

- no recursion
- no directory selection
- no URL input
- no plugin package import
- no automatic discovery
- no automatic startup prompt

The first implementation supports one selected JSON file at a time. Multi-file
preview remains future work.

## Trust and safety boundary

- user-selected manifests are untrusted by default
- third-party manifests are not trusted by default
- a trust label is not certification
- preview is not activation
- preview is not validation
- preview is not installation
- preview is not solver execution

## Testing strategy

Focused GUI tests use injected file chooser and loader callables, so they do
not open real dialogs. Tests cover cancel/no-op behavior, unsupported and
missing paths before loader execution, oversized files, invalid JSON,
schema-invalid reports, accepted/rejected/conflict rows, diagnostics,
trust/source labels, disabled action states, and source-level non-action
guardrails.

## Relationship to OSW-EXP-075 design

OSW-EXP-075 defined the explicit JSON import/preview GUI contract. This
implementation follows that contract for a single user-selected local JSON file
and keeps activation, discovery, validation, installation, issue closure, and
release work out of scope.

## Relationship to OSW-EXP-076 view-model

The panel consumes
`OptionalSolverPluginManifestExplicitImportGuiViewModel`. The view-model
remains pure and still has no PySide/Qt imports, file IO, JSON parsing from
paths, activation, discovery, validation, solver execution, dependency
installation, or external state mutation.

## Relationship to OSW-EXP-074 display-only panel

The existing `OptionalSolverPluginManifestPanel` remains a display-only panel
for already-built `OptionalSolverPluginManifestGuiViewModel` records. This gate
does not turn it into an activation or file-loading surface.

## Relationship to CLI preview

The GUI preserves the same accepted/rejected/conflict/diagnostic/source/trust
semantics as `optional-solver-plugin-manifest-preview`. CLI behavior is
unchanged.

## Relationship to health panel and export summary

Previewing a user-selected manifest is not health validation and does not alter
optional solver passive discovery. Export writing, clipboard integration,
shell/browser actions, and open-output-folder actions are not implemented by
this panel.

## Non-actions

This gate does not:

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
- mutate tags
- mutate assets
- bump versions
- claim validation success
- claim issue closure
- claim bundled solvers
- claim certification

## Future gates

- `OSW-EXP-078_OPTIONAL_SOLVER_PLUGIN_MANIFEST_ACTIVATION_DESIGN`
- future trust-elevation design, if any
- future multi-file explicit preview, if approved
- prepared-machine `OSW-VALID` reuse, separate from this preview
