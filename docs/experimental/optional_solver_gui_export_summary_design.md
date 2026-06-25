# Optional solver GUI export summary design

## Status

Design-only.

This gate adds:

- no export implementation
- no file dialog
- no clipboard integration
- no solver execution
- no external solver command execution
- no dependency installation
- no solver installation
- no issue mutation
- no release mutation

## Current baseline

- `v0.1.5-rc1` is a public prerelease.
- The optional solver GUI health panel is implemented as a PySide display
  component over a supplied view-model.
- The pure optional solver health view-model is implemented.
- The CLI doctor preview is implemented.
- Issues `#6` through `#11` remain open and `skipped-missing`.
- External solvers are not bundled.

## Purpose

The future export summary workflow should help users capture a redacted
optional-solver health summary for support, debugging, and prepared-machine
planning while preserving privacy by default.

Primary uses include support, debugging, and prepared-machine planning.

The export should be easy to inspect before writing and should not imply that a
machine has passed installed-only validation.

## Export scope

The future export payload may include:

- summary counts
- stack card summaries
- health states
- missing, partial, discovered, and unknown classifications
- diagnostics
- guidance text
- validation history rows
- release and version context
- timestamp and source surface
- issue references

The payload should preserve the same health-state semantics rendered by the GUI
health panel and CLI doctor preview.

## Out-of-scope data

The export payload must exclude by default:

- full `PATH`
- environment variable values
- credentials or secrets
- raw solver outputs
- raw validation artifacts
- private user paths unless explicitly opted in
- issue mutation payloads

Exported setup summaries are not a transport for release, issue, validation, or
solver-run artifacts.

## Supported future formats

Initial future formats should be text-oriented and reviewable:

- JSON
- Markdown
- plain text

Binary or proprietary formats are out of scope for the initial export summary
workflow.

## Redaction and privacy

- Redacted paths remain redacted by default.
- Environment values are never exported by default.
- Full path export requires explicit opt-in and a warning.
- The export preview should show exactly what will be included.
- No telemetry is collected.

The default export should be safe to attach to support requests without
revealing user home paths, local directory names, environment values,
credentials, or provider secrets.

## File path policy

The future implementation should require an explicit save path. It should not
choose an implicit destination and should not create parent directories
implicitly.

Path handling rules:

- explicit save path only
- no implicit parent directory creation
- overwrite requires confirmation
- safe extension policy for JSON, Markdown, and plain-text outputs
- traversal and unsafe path rejection

The path checker should treat a selected path as untrusted user input until it
has been normalized, checked against traversal rules, checked for an existing
parent directory, and matched to an allowed extension.

## GUI action flow

The future GUI action flow should be explicit:

The user should preview payload, choose a format, choose a destination, and
acknowledge privacy warnings before saving.

1. User opens the export summary action.
2. GUI previews the payload.
3. User chooses a format.
4. User chooses a destination.
5. User acknowledges the privacy warning if full paths are requested.
6. User saves.
7. GUI shows success or failure.

The initial implementation should not offer a shell action to open the output
file or output folder after save.

## Action-state design

Future action-state rows should distinguish available redacted export from
disabled or unavailable actions:

- export redacted summary is available when the view-model is valid
- export full paths is disabled unless explicit opt-in is available
- copy summary remains a future action; no clipboard in the initial
  implementation
- open output folder is unavailable initially
- run validation remains unavailable without an explicit validation gate
- install solver remains unavailable
- close issue remains unavailable

The health panel should continue to render unsafe or future actions as disabled
or unavailable rather than silently executing side effects.

## Export payload boundary

The future export payload builder should consume the health panel view-model
only. It should not call the CLI, passive discovery service, plugin loading,
solver adapters, issue APIs, release APIs, or GUI controls.

Boundary rules:

- pure export payload builder consumes view-model only
- GUI widget does not perform serialization directly
- no discovery execution during export
- no solver execution during export
- no subprocess usage during export

Serialization should be owned by a small pure export layer so tests can verify
redaction, field inclusion, deterministic ordering, and error handling without
opening GUI file dialogs.

## Export view-model follow-up

[Optional solver GUI export summary view-model](optional_solver_gui_export_summary_viewmodel.md)
implements that pure payload layer. It consumes an already-built
`OptionalSolverHealthPanelViewModel`, returns redacted payload records,
renders JSON, Markdown, and plain text in memory, and analyzes save paths
without writing files. It still adds no GUI export action, file dialog,
clipboard integration, shell/browser action, discovery execution, solver
execution, dependency installation, issue mutation, release mutation,
validation-pass claim, issue-closure claim, bundled-solver claim, or
certification claim.

## Export implementation follow-up

[Optional solver GUI export summary implementation](optional_solver_gui_export_summary_implementation.md)
adds the PySide health-panel action for writing a redacted summary to an
explicit user-selected `.json`, `.md`, or `.txt` target. The implementation
uses the pure payload/save-plan layer, rejects unsupported or unsafe paths,
requires existing parent directories, requires overwrite confirmation, writes
one selected file on success, and still adds no clipboard integration,
shell/browser action, open-output-folder action, discovery refresh, solver
execution, dependency installation, issue mutation, release mutation,
validation-pass claim, issue-closure claim, bundled-solver claim, or
certification claim.

## Discovery refresh design follow-up

[Optional solver GUI discovery refresh design](optional_solver_gui_discovery_refresh_design.md)
records how a later explicit passive refresh should interact with export
summaries. Exports before refresh use the current accepted view-model; exports
after refresh use the refreshed accepted view-model. The design adds no refresh
source behavior, background worker, active validation, solver execution,
dependency installation, issue mutation, or release mutation.

## Validation relationship

An exported summary is not validation evidence. It is a portable rendering of
passive setup state and guidance.

`skipped-missing` remains not pass evidence. Issue closure requires separate
prepared-machine validation and closure-review gates.

Skipped-missing remains not pass evidence.

## Failure handling

Future implementation should surface bounded, user-facing failures for:

- invalid path
- overwrite denied
- serialization failure
- permission error
- redaction policy violation

Failure messages should avoid revealing full local paths unless the user has
explicitly opted into full-path handling for the export.

## Tests for future implementation

Future implementation tests should cover:

- redacted JSON payload
- Markdown payload
- plain text payload
- unsafe path rejection
- overwrite guard
- no clipboard side effects
- no shell or browser side effects
- no solver side effects
- privacy warnings

Tests should be deterministic, solver-free, network-free, and independent of
optional solver packages.

## Non-goals

- no implementation in this gate
- no clipboard
- no file dialog
- no shell or browser action
- no solver execution
- no external solver command execution
- no install workflow
- no issue mutation
- no release mutation
- no certification claim

## Future gates

- `OSW-EXP-064_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_VIEWMODEL` - completed as a
  pure payload/view-model layer in
  [Optional solver GUI export summary view-model](optional_solver_gui_export_summary_viewmodel.md).
- `OSW-EXP-065_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_IMPLEMENTATION` - completed
  as redacted GUI export wiring in
  [Optional solver GUI export summary implementation](optional_solver_gui_export_summary_implementation.md).
- `OSW-EXP-066_OPTIONAL_SOLVER_GUI_DISCOVERY_REFRESH_DESIGN` - completed as a
  design-only passive refresh workflow contract in
  [Optional solver GUI discovery refresh design](optional_solver_gui_discovery_refresh_design.md).
