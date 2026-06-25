# Optional solver GUI health panel implementation

## Status

Experimental PySide display component implemented.

This gate is view-model driven and adds:

- PySide display component for an already-built health panel view-model
- summary, stack card, details, diagnostics, guidance, validation-history, and
  action-state rendering
- deterministic test accessors for GUI tests

This gate does not add:

- no discovery execution
- no solver execution
- no external solver command execution
- no subprocess usage
- no active smoke validation
- no dependency installation
- no solver installation
- no optional solver package import
- no issue mutation
- no issue closure action
- no release mutation

## Package path and public class

Package path:

- `src/osw/gui/dialogs/optional_solver_health_panel.py`

Public class:

- `OptionalSolverHealthPanel`

The class is lazily exported from `osw.gui.dialogs`.

## Relationship to pure view-model

The panel accepts an `OptionalSolverHealthPanelViewModel` object that is built
outside the widget. It reads frozen dataclass fields and renders them into
read-only PySide controls.

The view-model is built outside the widget.

The panel does not call optional solver discovery services, CLI commands,
plugin loading, solver adapters, shell commands, installers, issue APIs, or
release APIs. Refresh, copy, docs, validation, install, and close-issue actions
are rendered as action state only.

## Rendered sections

The panel renders:

- summary header
- stack cards/list
- details panel
- diagnostics panel
- guidance and safety panel
- validation history panel
- action-state panel

## Stack cards

Stack card rows display:

- stack id
- display name
- issue reference
- health state
- support status
- missing requirements count
- diagnostics count
- non-bundled disclaimer indicator
- selected state

Missing optional stacks remain setup evidence, not application failure.

## Details panel

The details panel displays:

- capabilities
- executable requirements
- Python package requirements
- environment hints
- prepared-machine notes
- safety notes
- documentation references
- version/help probe declarations marked by the view-model as not executed

Requirement rows are read-only. Probe declarations are not executed by the
panel.

## Diagnostics panel

Diagnostics render supplied view-model rows:

- severity
- code
- message
- field/path
- suggested fix
- redaction notice, when present

Diagnostics come from supplied view-model data only.

## Guidance and safety panel

Guidance renders:

- prepared-machine guidance
- no-bundled-solver notice
- validation-gate guidance
- issue closure guidance
- manifest safety notes

The safety panel repeats the no-execution, no-install, no-issue-closure, and
non-bundled-solver boundaries.

## Action-state panel

The action-state panel renders view-model action rows and disabled placeholder
buttons:

- refresh passive discovery: display-only future placeholder; no discovery call
- run validation: disabled; explicit OSW-VALID gate required
- install solver: unavailable
- close issue: unavailable
- copy summary: display-only future placeholder; no clipboard access
- open docs: display-only future placeholder; no shell or browser action
- export summary: enabled when a redacted payload can be rendered; writes only
  one explicitly selected `.json`, `.md`, or `.txt` file after path and
  overwrite checks

The GUI does not execute discovery, validation, install, issue-closure,
clipboard, shell, or browser actions from this panel.

## Export summary design follow-up

[Optional solver GUI export summary design](optional_solver_gui_export_summary_design.md)
defines the future redacted summary export workflow for this panel. It covers
export scope, supported text-oriented formats, privacy defaults, explicit path
selection, overwrite confirmation, action-state behavior, and a pure payload
builder boundary without adding exporter source, file dialogs, clipboard
integration, shell/browser actions, discovery execution, solver execution,
dependency installation, issue mutation, or release mutation.

[Optional solver GUI export summary view-model](optional_solver_gui_export_summary_viewmodel.md)
implements the pure payload/rendering/save-plan layer for that future workflow.

[Optional solver GUI export summary implementation](optional_solver_gui_export_summary_implementation.md)
adds the redacted export action to this panel. The action uses the pure export
payload layer, requires an explicit `.json`, `.md`, or `.txt` destination,
rejects missing parent directories, requires overwrite confirmation, writes
exactly one selected file on success, and still adds no clipboard behavior,
shell/browser opening, output-folder opening, discovery refresh, solver
execution, dependency installation, issue mutation, release mutation,
validation-pass claim, issue-closure claim, bundled-solver claim, or
certification claim.

## Discovery refresh design follow-up

[Optional solver GUI discovery refresh design](optional_solver_gui_discovery_refresh_design.md)
records the future explicit passive refresh workflow for this panel. The
contract keeps widgets from calling discovery directly: a future injected
runner would produce passive reports, the pure builder would create a new
view-model, and the widget would swap the accepted view-model atomically while
preserving selected stack and filters where safe. The design adds no source
behavior in this gate and keeps active validation, solver execution,
dependency installation, issue mutation, and release mutation out of the
panel.

## Privacy and redaction

- Redacted paths remain redacted.
- Full paths supplied in passive reports are not displayed by the view-model or
  panel.
- Environment values are not displayed.
- The panel does not collect telemetry, credentials, provider secrets, or local
  environment values.

## Safety boundary

- no discovery execution
- no solver execution
- no external solver command execution
- no subprocess usage
- no install action
- no issue closure action
- no dependency installation
- no release mutation
- no bundled solver claim
- no certification claim

## Relationship to #6~#11

The panel can display setup state for:

- Gmsh: `#6`
- GNU Octave: `#7`
- CalculiX `ccx`: `#8`
- OpenFOAM: `#9`
- CoolProp / Cantera: `#10`
- PyVista / meshio: `#11`

Issues `#6` through `#11` remain open. `skipped-missing` evidence remains not
pass evidence, and issue closure remains outside this panel.

## Future gates

- `OSW-EXP-063_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_DESIGN` - completed as a
  design-only export workflow contract in
  [Optional solver GUI export summary design](optional_solver_gui_export_summary_design.md).
- `OSW-EXP-064_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_VIEWMODEL` - completed as a
  pure payload/view-model layer in
  [Optional solver GUI export summary view-model](optional_solver_gui_export_summary_viewmodel.md).
- `OSW-EXP-065_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_IMPLEMENTATION` - completed
  as redacted GUI export wiring in
  [Optional solver GUI export summary implementation](optional_solver_gui_export_summary_implementation.md).
- `OSW-EXP-066_OPTIONAL_SOLVER_GUI_DISCOVERY_REFRESH_DESIGN` - completed as a
  design-only passive refresh workflow contract in
  [Optional solver GUI discovery refresh design](optional_solver_gui_discovery_refresh_design.md).
- `OSW-VALID` prepared-machine validation reuse

Earlier planning named the discovery refresh placeholder
`OSW-EXP-064_OPTIONAL_SOLVER_GUI_DISCOVERY_REFRESH_DESIGN`. The export-summary
sequence now reserves `OSW-EXP-064` and `OSW-EXP-065` for export view-model and
implementation gates before discovery refresh design.
