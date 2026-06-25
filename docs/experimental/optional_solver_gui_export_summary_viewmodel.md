# Optional solver GUI export summary view-model

## Status

Experimental pure export payload/view-model implemented.

This gate adds:

- pure export summary payload models
- redacted JSON rendering
- Markdown rendering
- plain-text rendering
- save-plan analysis
- privacy warnings and acknowledgement flags

This gate does not add:

- no file write
- no file dialog
- no clipboard
- no shell or browser action
- no discovery execution
- no solver execution
- no external solver command execution
- no subprocess usage
- no dependency installation
- no solver installation
- no issue mutation
- no release mutation

## Relationship to export summary design

This implementation follows
[Optional solver GUI export summary design](optional_solver_gui_export_summary_design.md).
It provides the pure payload and rendering layer for a future GUI export
workflow while keeping file dialogs, file writes, clipboard behavior,
shell/browser opening, and GUI action wiring in later gates.

## GUI implementation follow-up

[Optional solver GUI export summary implementation](optional_solver_gui_export_summary_implementation.md)
adds the PySide health-panel wiring that uses this pure payload layer. The GUI
action remains redacted by default, requires an explicit `.json`, `.md`, or
`.txt` target, rejects missing parent directories, requires overwrite
confirmation, and writes exactly one selected file. It adds no clipboard,
shell/browser action, discovery execution, solver execution, dependency
installation, issue mutation, release mutation, validation-pass claim,
issue-closure claim, bundled-solver claim, or certification claim.

## Package path and public API

Package path:

- `src/osw/experimental/optional_solvers/gui_export_summary_viewmodel.py`

Public API:

- `OptionalSolverExportSummaryFormat`
- `OptionalSolverExportSummaryOptions`
- `OptionalSolverExportSummaryPayload`
- `OptionalSolverExportSummaryViewModel`
- `OptionalSolverExportSummarySavePlan`
- `OptionalSolverExportSummaryDiagnostic`
- `OptionalSolverExportSummaryPrivacyWarning`
- `OptionalSolverExportSummaryRenderResult`
- `build_optional_solver_export_summary_viewmodel`
- `build_optional_solver_export_summary_payload`
- `render_optional_solver_export_summary_json`
- `render_optional_solver_export_summary_markdown`
- `render_optional_solver_export_summary_text`
- `plan_optional_solver_export_summary_save`
- `explain_optional_solver_export_summary`

## Export formats

Supported pure render formats:

- `json`
- `markdown`
- `text`

The renderers return in-memory strings only. They do not write files.

## Payload fields

The payload records:

- app/tool name
- package version when supplied
- generated timestamp when supplied
- source context
- summary counts
- stack card summaries
- health states
- diagnostics
- guidance
- validation history
- issue references
- safety notes
- privacy notes
- redaction state
- non-bundled solver disclaimer
- not-validation-evidence flag

## JSON rendering

`render_optional_solver_export_summary_json` returns deterministic JSON text
from an already-built payload. JSON rendering is in-memory only and has no file
write behavior.

## Markdown rendering

`render_optional_solver_export_summary_markdown` returns Markdown text with the
summary, stack statuses, diagnostics, guidance, validation history, privacy
notes, and safety notes.

## Plain-text rendering

`render_optional_solver_export_summary_text` returns plain text with the same
redacted payload content for environments where Markdown is not desired.

## Save-plan analysis

`plan_optional_solver_export_summary_save` analyzes a supplied path only.

The save plan:

- requires an explicit path
- rejects missing parent directories
- rejects traversal or unsafe paths
- rejects unsupported extensions
- supports `.json`, `.md`, and `.txt`
- blocks overwrite by default
- reports whether the target exists
- reports `would_write_file=false`

The save plan is deterministic and side-effect-free. It does not create
directories, open dialogs, or write files.

## Privacy and redaction

- Export summaries are redacted by default.
- Environment values are never exported.
- Full paths require explicit opt-in warning and acknowledgement flags.
- Default JSON, Markdown, and text output omit full user paths.
- Redacted path markers remain redacted.
- The payload records no telemetry, credentials, provider secrets, issue
  mutation payloads, or raw solver outputs.

## Safety boundary

- export summary is not validation evidence
- no discovery execution
- no solver execution
- no external solver command execution
- no subprocess
- no file write
- no file dialog
- no clipboard, shell, or browser action
- no install workflow
- no issue mutation
- no release mutation
- no bundled solver claim
- no certification claim

## Relationship to #6~#11

The export summary can include issue references for:

- Gmsh: `#6`
- GNU Octave: `#7`
- CalculiX `ccx`: `#8`
- OpenFOAM: `#9`
- CoolProp / Cantera: `#10`
- PyVista / meshio: `#11`

Issues `#6` through `#11` remain open. `skipped-missing` is not pass evidence,
and exported summaries cannot close issues.

## Future gates

- `OSW-EXP-065_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_IMPLEMENTATION` - completed
  as redacted GUI export wiring in
  [Optional solver GUI export summary implementation](optional_solver_gui_export_summary_implementation.md).
- `OSW-EXP-066_OPTIONAL_SOLVER_GUI_DISCOVERY_REFRESH_DESIGN`
