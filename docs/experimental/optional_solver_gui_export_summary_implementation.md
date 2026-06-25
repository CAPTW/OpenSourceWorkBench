# Optional solver GUI export summary implementation

## Status

Experimental GUI export action implemented.

This gate adds:

- redacted summary export only
- explicit save-file dialog for `.json`, `.md`, and `.txt`
- overwrite confirmation before replacing an existing target
- status and error display in the health panel

This gate does not add:

- no clipboard
- no shell or browser action
- no open-output-folder action
- no discovery refresh
- no solver execution
- no external solver command execution
- no dependency installation
- no solver installation
- no issue mutation
- no release mutation

## Package path / GUI class

Package path:

- `src/osw/gui/dialogs/optional_solver_health_panel.py`

Public class:

- `OptionalSolverHealthPanel`

## Relationship to export summary view-model

The GUI action delegates payload creation, rendering, and save-path analysis to
[Optional solver GUI export summary view-model](optional_solver_gui_export_summary_viewmodel.md).
The dialog does not serialize health state itself.

The GUI consumes an already-built `OptionalSolverHealthPanelViewModel`, uses
the export payload layer to render a redacted summary, and writes the selected
rendered string only after the save plan allows it.

## Supported formats

- JSON
- Markdown
- plain text

The selected filename extension must be `.json`, `.md`, or `.txt`.

## Save path and overwrite policy

The implementation uses an explicit save path only:

- parent directory must already exist
- missing parent directories are rejected
- parent directories are not created implicitly
- unsupported extensions are rejected
- unsafe traversal paths are rejected by the save-plan layer
- existing targets require explicit overwrite confirmation
- canceling the dialog writes nothing
- a successful export writes exactly one selected file

Tests inject the path chooser and overwrite confirmation to keep GUI behavior
deterministic and headless.

## Redaction/privacy behavior

Exported content is redacted by default.

- redacted paths remain redacted
- full user paths are omitted by default
- environment variable values are not exported
- credentials, secrets, raw solver outputs, and raw validation artifacts are
  not exported
- the exported summary states that it is not validation evidence

Full-path export is not enabled by this GUI action.

## Export status/error display

The health panel exposes status and error text after export attempts. The
status reports cancel, success, or bounded failure state. The error text
reports save-plan diagnostics such as missing parent directory, unsupported
extension, unsafe path, or overwrite denial.

Deterministic test accessors report:

- export status text
- export error text
- last export path
- last export format
- exported file summary text
- export action enabled state
- export action reason

## Safety boundary

- export summary is not validation evidence
- no discovery execution
- no solver execution
- no external solver command execution
- no subprocess usage
- no dependency installation
- no issue mutation
- no release mutation
- no clipboard access
- no shell or browser action
- no open-output-folder action
- no bundled solver claim
- no certification claim

## Relationship to #6~#11

The export can include issue references for optional solver validation issues:

- Gmsh: `#6`
- GNU Octave: `#7`
- CalculiX `ccx`: `#8`
- OpenFOAM: `#9`
- CoolProp / Cantera: `#10`
- PyVista / meshio: `#11`

Issues `#6` through `#11` remain open. `skipped-missing` remains not pass
evidence, and exported summaries cannot close issues.

## Future gates

- `OSW-EXP-066_OPTIONAL_SOLVER_GUI_DISCOVERY_REFRESH_DESIGN`
- `OSW-EXP-067_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_POLISH`
- `OSW-VALID` prepared-machine validation reuse
