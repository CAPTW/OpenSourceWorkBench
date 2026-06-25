# Optional solver GUI health panel view-model

## Status

Experimental pure view-model implemented.

This gate adds no GUI behavior:

- no PySide implementation
- no Qt implementation
- no GUI widget implementation
- no CLI behavior change
- no discovery execution
- no solver execution
- no external solver command execution
- no subprocess usage
- no optional solver package imports
- no dependency installation
- no solver installation
- no plugin loading
- no issue mutation
- no release mutation

## Relationship to GUI health panel design

This implementation follows
[Optional solver GUI health panel design](optional_solver_gui_health_panel_design.md).
It provides the UI-agnostic data layer for future PySide widgets while keeping
all widget rendering, file dialogs, refresh wiring, clipboard behavior, browser
opening, and validation execution in later gates.

## Package path and public API

Package path:

- `src/osw/experimental/optional_solvers/gui_health_viewmodel.py`

Public API:

- `OptionalSolverHealthPanelViewModel`
- `OptionalSolverHealthSummaryViewModel`
- `OptionalSolverStackCardViewModel`
- `OptionalSolverStackDetailsViewModel`
- `OptionalSolverDiagnosticRowViewModel`
- `OptionalSolverRequirementRowViewModel`
- `OptionalSolverGuidanceRowViewModel`
- `OptionalSolverValidationHistoryRowViewModel`
- `OptionalSolverHealthPanelAction`
- `OptionalSolverHealthPanelActionState`
- `build_optional_solver_health_panel_viewmodel`
- `build_optional_solver_stack_card_viewmodel`
- `summarize_optional_solver_health_panel`
- `explain_optional_solver_health_panel`

## Inputs and outputs

Inputs:

- built-in or supplied `OptionalSolverManifest` records
- supplied passive `OptionalSolverDiscoveryReport` or stack reports
- optional validation history rows
- optional selected stack id
- optional filter text
- optional health-state filters

Outputs are frozen dataclass records intended for future GUI rendering. If no
discovery report is supplied, stacks render as `unknown`; the builder does not run discovery.

## Summary model

`OptionalSolverHealthSummaryViewModel` records:

- total stacks
- counts by health state
- missing count
- partial count
- discovered count
- open issue count
- validation warning count

Counts are computed over visible cards after filter application.

## Stack cards

`OptionalSolverStackCardViewModel` records:

- stack id
- display name
- related issue
- issue reference
- health state
- support status
- short status text
- missing requirements count
- diagnostics count
- non-bundled disclaimer indicator
- selected state

Cards are sorted deterministically by stack id and use the same passive
health-state semantics as the CLI doctor preview.

## Details panel model

`OptionalSolverStackDetailsViewModel` records:

- capabilities
- executable requirements
- Python package requirements
- environment hints
- version/help probe text marked as not executed
- prepared-machine notes
- safety notes
- documentation references

Requirement rows are display-only. Probe declarations remain explanatory and
are not executed by the view-model.

## Diagnostics rows

`OptionalSolverDiagnosticRowViewModel` preserves:

- stack id
- severity
- code
- message
- path
- suggested fix
- redaction notice when a passive diagnostic reports redacted local evidence

Diagnostics are rendered from supplied passive discovery reports only.

## Guidance rows

`OptionalSolverGuidanceRowViewModel` includes:

- prepared-machine guidance
- manifest safety notes
- no-bundled-solver notice
- validation-gate guidance
- issue closure guidance

Skipped-missing evidence remains setup evidence, not a pass.

## Action-state model

`OptionalSolverHealthPanelActionState` records display-only action availability:

- refresh passive discovery: future action placeholder
- run validation: unavailable without an explicit validation gate
- install solver: unavailable
- close issue: unavailable
- copy summary: future action placeholder, no clipboard access
- open docs: future action placeholder, no shell or browser action

The action-state model does not execute actions.

## Privacy and redaction

- Paths already redacted by discovery remain redacted.
- Full paths in supplied reports are not displayed by default.
- Environment values are never displayed.
- The view-model stores no credentials or provider secrets.

## Safety boundary

- no discovery execution
- no solver execution
- no external solver command execution
- no subprocess usage
- no optional package imports
- no install actions
- no issue closure actions
- no release mutation
- no bundled solver claim
- no certification claim

## Relationship to CLI doctor

The view-model uses the same health-state semantics as
`optional-solver-doctor`:

- `missing`
- `partially_installed`
- `discovered`
- `unknown`

It only turns those passive records into GUI-friendly rendering data. It does
not replace prepared-machine validation and does not change issue state.

## GUI implementation follow-up

[Optional solver GUI health panel implementation](optional_solver_gui_health_panel_implementation.md)
consumes this view-model from PySide display code. The widget renders the
existing records and keeps action states disabled/display-only; it does not
perform discovery, execute solvers, install dependencies, access clipboard or
browser APIs, mutate issues, or edit releases.

## Export summary design follow-up

[Optional solver GUI export summary design](optional_solver_gui_export_summary_design.md)
defines the future summary export workflow over data derived from this
view-model. The design keeps the future export payload builder pure and
view-model-driven, requires redaction by default, excludes environment values
by default, and keeps file dialogs, clipboard access, shell/browser actions,
discovery execution, solver execution, dependency installation, issue mutation,
and release mutation out of this design gate.

[Optional solver GUI export summary view-model](optional_solver_gui_export_summary_viewmodel.md)
implements that pure export payload layer over this health panel view-model. It
renders JSON, Markdown, and plain text in memory and analyzes save paths without
adding GUI widgets, file dialogs, file writes, clipboard access, shell/browser
actions, discovery execution, solver execution, issue mutation, or release
mutation.

[Optional solver GUI export summary implementation](optional_solver_gui_export_summary_implementation.md)
adds the GUI wiring that consumes this view-model through the export payload
layer. The action writes only a redacted `.json`, `.md`, or `.txt` summary to
one explicit selected file and still does not make this pure health view-model
perform discovery, execute solvers, install dependencies, mutate issues, edit
releases, claim validation success, claim issues are closure-ready, bundle
solvers, or claim certification.

## Discovery refresh design follow-up

[Optional solver GUI discovery refresh design](optional_solver_gui_discovery_refresh_design.md)
defines a future explicit passive refresh flow that would build a new health
panel view-model from new passive reports. The design preserves the pure
builder boundary: widgets request refresh through a future injected runner,
then swap an already-built view-model rather than mutating cards in place.

## Future gates

- `OSW-EXP-062_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_IMPLEMENTATION` - completed as
  a display-only PySide panel in
  [Optional solver GUI health panel implementation](optional_solver_gui_health_panel_implementation.md).
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
