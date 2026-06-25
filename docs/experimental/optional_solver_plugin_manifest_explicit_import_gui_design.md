# Optional solver plugin manifest explicit import GUI design

## Status

Design-only.

No runtime source behavior is added in this gate. This document defines a
future GUI workflow for explicitly selecting plugin manifest JSON files and
previewing them safely. It is not implementation authorization and does not
read as one.

Status boundaries:

- no file dialog implementation
- no QFileDialog implementation
- no file loading implementation
- no JSON parsing from GUI source
- no plugin activation
- no plugin package import
- no directory scan
- no network fetch
- no discovery execution
- no solver execution
- no dependency installation
- no issue mutation
- no release mutation

## Current baseline

- `v0.1.5-rc1 public prerelease` is the current public release.
- Package metadata remains `0.1.5rc1`.
- Plugin manifest loader model exists.
- Plugin manifest CLI preview (`optional-solver-plugin-manifest-preview`) exists.
- Plugin manifest GUI view-model exists.
- `OptionalSolverPluginManifestPanel` display-only GUI exists (OSW-EXP-074).
- Optional solver health/export/refresh GUI exists.
- `#6~#11 open/skipped-missing`.
- External solvers not bundled.

Issues `#6` through `#11` remain open. This gate does not change their state.

## Purpose

The future GUI should let users explicitly select local plugin manifest JSON
files and preview the loader report for those files, without turning user or
plugin metadata into trusted runtime behavior.

The purpose is to:

- define future explicit user-selected JSON manifest preview behavior
- preserve the OSW-EXP-074 display-only boundaries
- make preview distinct from activation, validation, discovery, installation,
  issue closure, and certification

Preview is the act of reading a chosen JSON file's loader report and showing
accepted, rejected, conflict, diagnostic, source, and trust rows. Preview never
means the manifest is activated, validated, installed, discovered, trusted, or
certified.

## Existing boundary from OSW-EXP-074

- `OptionalSolverPluginManifestPanel` consumes an already-built
  `OptionalSolverPluginManifestGuiViewModel`.
- The current panel is display-only.
- The current panel does not choose files or load files.
- The current panel renders summary, accepted/rejected/conflict tables,
  diagnostics, trust/source labels, safety guidance, and disabled/future action
  states only.

This design adds a future explicit import path *in front of* that display-only
panel. It does not change the panel's display-only contract in this gate.

## Future entry points

Possible future entry points, defined here without implementing them:

- a future Optional solver plugin manifest panel action/footer button
- a future Plugin Manager or optional solver UX surface entry
- an explicit menu/action label such as `Preview plugin manifest JSON`

Entry-point rules:

- no automatic startup prompt
- no automatic plugin manifest loading on startup
- no directory scan
- no plugin package scan
- no network fetch

Every future entry point must be user-initiated and must lead only to a
preview, never to activation.

## Future explicit JSON file chooser behavior

Defined as future behavior, not as code in this gate:

- user-initiated only
- local explicit file selection only
- JSON files only
- recommended file filter: `*.json`
- reject unsupported extensions
- cancel is a no-op
- no automatic directory recursion
- no remote URL input
- no plugin package import
- no plugin activation

The chooser only collects explicit local file paths from the user. Reading,
parsing, and report generation are delegated to the existing loader semantics in
a future implementation gate; the GUI widgets must not parse JSON directly.

## File safety and failure states

The future GUI must define clear, non-destructive UX and diagnostics for each
failure state. None of these failure states may run discovery, execute solvers,
activate manifests, or mutate project, issue, or release state.

Expected handling:

- cancelled selection: cancel is a no-op; the prior preview/panel state is
  preserved.
- missing file: report a missing-file diagnostic; preview nothing.
- unreadable file: report an unreadable-file diagnostic.
- unsupported extension: reject non-`.json` extensions with a clear diagnostic.
- oversized file: reject files above a future size limit before parsing.
- invalid UTF-8 or unreadable text: report an undecodable-content diagnostic.
- invalid JSON: report an invalid JSON diagnostic; show no accepted rows.
- valid JSON but schema-invalid manifest: report a schema-invalid diagnostic and
  keep the record rejected.
- duplicate stack id conflicts: show conflict rows; built-ins win by default.
- unsafe claims inside manifest: surface unsafe-claim indicators (installer
  wording, executable code references, bundled-solver claims, certification or
  production-readiness claims) and keep the record rejected.
- plugin override attempts: surface override-attempt diagnostics; plugin
  override stays disabled by default.
- third-party trust warning: show an untrusted-source warning for user-selected
  and plugin-provided manifests.

Failures preserve current state and present diagnostics. They do not silently
hide rejected or conflicting records.

## Suggested diagnostic code reservations

The following diagnostic code names are reserved as design-only names for a
future implementation gate. They are not implemented in this gate. They are a
GUI-import (`OSPMG`) vocabulary distinct from existing loader and CLI
diagnostics, and a future implementation gate should reconcile them with the
loader/report semantics rather than duplicate parsing:

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

These names are reservations only. No diagnostic emitter, runtime constant, or
GUI handler is added in this gate.

## Source and trust labeling

The future GUI must label where a previewed manifest came from and how much it
is trusted. Suggested labels:

- `source_type: user_selected_json_file` for explicitly chosen local files.
- `trust_label: untrusted_user_file` (or an equivalent untrusted label) for
  user-selected files.

The GUI should reuse the existing loader/CLI source and trust vocabulary:

- built-in trusted
- reviewed project
- user provided
- third-party plugin
- organization managed
- untrusted
- invalid

Labeling rules:

- the source reference should avoid exposing sensitive absolute paths by
  default; display redacted references and require future explicit opt-in for
  full paths.
- third-party and plugin-provided manifests are not trusted by default.
- a trust label is not certification.
- preview is not activation.
- preview is not validation.
- preview is not installation.

## Relationship to built-in manifests

- Built-in manifests remain authoritative by default.
- User-selected and plugin-provided manifests must not override built-ins
  silently.
- The built-ins-win (or explicit conflict) policy must be visible in the
  preview.
- Conflicts must be previewed, not hidden.

Any explicit override policy requires a separate future trust and activation
gate; this design does not offer an override action.

## Relationship to plugin-provided manifests

- Explicit user-selected JSON preview is separate from plugin package loading.
- This design must not, and does not, authorize importing plugin packages.
- Plugin-provided manifests remain untrusted unless a future explicit trust gate
  says otherwise.

Selecting a JSON file is a data-preview action. It is not a plugin import,
plugin activation, or plugin discovery action.

## Relationship to CLI preview

- The future GUI preview should preserve the semantics of
  `optional-solver-plugin-manifest-preview`.
- GUI and CLI should share loader and report semantics in a future
  implementation gate rather than re-deriving parsing in the GUI.
- This design does not change the CLI.

The CLI preview remains the automation-oriented surface; the GUI import preview
is review-focused and should optimize for readable comparison, diagnostics, and
safety warnings over the same accepted/rejected/conflict records.

## Relationship to optional solver health panel

- Previewing a manifest is not health validation.
- Previewing a manifest does not alter passive discovery.
- The optional solver health panel refresh must not start using user-selected or
  plugin-provided manifests unless a later explicit gate defines activation
  semantics.

The health panel continues to evaluate built-in/passive discovery evidence; the
explicit import preview is a separate, non-activating surface.

## Relationship to export summary

- Redacted export summaries may later include preview state only if that is
  explicitly designed in a future gate.
- Export must not expose sensitive local paths by default.
- This design does not implement export behavior.

## Future implementation test plan

A later implementation gate should add tests that verify:

- cancel is a no-op and preserves prior state
- unsupported extensions are rejected
- invalid JSON produces a diagnostic and no accepted rows
- schema-invalid manifests produce a diagnostic and stay rejected
- conflict rows are visible (built-ins win by default)
- untrusted-source warnings are visible for user/plugin manifests
- no activation action is triggered by preview
- no discovery execution occurs
- no solver execution occurs
- no dependency installation occurs
- no issue mutation occurs
- no release mutation occurs

These are future tests. This gate adds only a focused docs test for this design
document and the related guardrail/risk/checklist references.

## Non-actions

This gate explicitly does not:

- implement QFileDialog
- implement file loading
- parse JSON from GUI source
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
- build or upload assets
- create, move, delete, or push tags
- bump versions
- claim live optional validation success
- claim issue closure
- claim bundled solvers
- claim certification

No runtime source, GUI source, view-model source, CLI source, loader source,
discovery source, or plugin manager source is changed in this gate.

This design also adds no validation-pass claim, no issue-closure claim, no
bundled-solver claim, and no certification claim. A previewed manifest is
untrusted preview data only; skipped-missing optional validation remains neither
pass nor failure, and issues `#6` through `#11` stay open.

## View-model implementation follow-up

[Optional solver plugin manifest explicit import GUI view-model](optional_solver_plugin_manifest_explicit_import_gui_viewmodel.md)
implements the pure view-model layer for this design (OSW-EXP-076). It consumes
already-built loader reports or caller-supplied import diagnostics and produces
summary, selected-source, accepted/rejected/conflict, diagnostic,
`OSPMG_IMPORT_*`, trust-badge, guidance, and action-state records with redacted
source references. OSW-EXP-076 implements the pure view-model layer only;
file-dialog implementation and file loading remain future-gated. The view-model
adds no GUI widget, file dialog, file loading, JSON parsing from paths, plugin
activation, plugin package import, directory scan, network fetch, discovery
execution, solver execution, dependency installation, issue mutation, release
mutation, validation-pass claim, issue-closure claim, bundled-solver claim, or
certification claim.

## Future gates

Proposed follow-up candidates, not implemented here:

- `OSW-EXP-076_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPLICIT_IMPORT_GUI_VIEWMODEL`
- `OSW-EXP-077_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPLICIT_IMPORT_GUI_IMPLEMENTATION`
- `OSW-EXP-078_OPTIONAL_SOLVER_PLUGIN_MANIFEST_ACTIVATION_DESIGN`
- `OSW-VALID` prepared-machine validation reuse

Numbering note: the earlier OSW-EXP-072 design doc tentatively reserved
`OSW-EXP-075` for an activation design, and the OSW-EXP-074 implementation doc
tentatively reserved `OSW-EXP-076` for an activation design. This explicit
import line follows the established design -> view-model -> implementation
cadence already used by OSW-EXP-072 -> OSW-EXP-073 -> OSW-EXP-074, so the
explicit-import view-model and implementation take `OSW-EXP-076` and
`OSW-EXP-077`, and the activation design shifts to `OSW-EXP-078`. If the repo
later re-reserves a different sequence, follow the repo's latest convention and
update this mapping. Activation, trust elevation, and any live validation remain
separate, later gates regardless of numbering.
