# FEASpec CalculiX result write GUI file dialog

Status: experimental output-directory selection implemented. No writer
invocation. No ResultDataset file write on selection. No solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- The public release, release tag, release assets, and GitHub issues are not
  edited by this work.

## Package path

- `src/osw/gui/dialogs/feaspec_calculix_result_write_dialog.py`

## Behavior

The result write dialog now exposes an output-directory chooser for the
existing `FEASpecCalculiXResultWriteViewModel` evidence. The chooser uses
QFileDialog directory selection only through `getExistingDirectory`; it does
not select an individual `result_dataset.json` file.

The behavior is:

- accepted directory selection updates the read-only output-directory field;
- accepted directory selection refreshes the visible save-plan analysis;
- cancel is no-op and leaves the current selection unchanged;
- selection does not create directories;
- selection does not write files;
- selection does not copy artifacts;
- selection does not invoke the library writer.

## Testability

The dialog accepts an injectable output-directory chooser so GUI tests can
exercise accepted and canceled selections without opening a native dialog. The
test accessors expose:

- selected output-directory text;
- save-plan display text;
- output-directory control state;
- file-dialog invocation count;
- write invocation count.

Tests use `tmp_path` generated paths and do not add tracked solver output
fixtures.

## Path Safety

The GUI selection step remains display-only. It delegates lexical save-target
analysis to `plan_calculix_result_write_save_path` and surfaces the resulting
state in the write-plan panel. Unsafe paths, missing parent/create-directory
requirements, and overwrite requirements remain visible as save-plan evidence.

The chooser itself must not:

- create a missing output directory;
- create a missing parent directory;
- overwrite planned ResultDataset files;
- mark acknowledgements as accepted;
- bypass the view-model or save-plan helper.

## Safety Boundary

This implementation preserves:

- no writer invocation;
- no ResultDataset file write;
- no artifact copying;
- no directory creation during selection;
- no CLI behavior change;
- no library writer behavior change;
- no solver execution;
- no CalculiX `ccx` invocation;
- no subprocess use;
- no SolverAdapter;
- no runner;
- no ProjectSchema mutation;
- no VLM API;
- no provider credentials;
- no release, tag, asset, or issue mutation.

External solvers are optional and not bundled. This GUI selection is not
engineering validation, live solver validation, or certification evidence.

## Relationship To The View-Model

The dialog still consumes the existing `FEASpecCalculiXResultWriteViewModel`.
The view-model remains a pure Python state layer with no PySide/Qt imports and
no file-dialog implementation. The dialog uses the existing save-plan helper
for display-only path analysis and does not persist selected paths into a
project schema.

## Relationship To Issue #8

The file dialog does not validate live `ccx`. Issue `#8` remains open until a
separate prepared-machine live CalculiX validation gate records passing
evidence. Choosing an output directory is not solver validation and must not be
used to close issue `#8`.

## Non-Goals

- no writer integration;
- no GUI write action;
- no ResultDataset persistence;
- no artifact copying;
- no CLI behavior change;
- no library writer behavior change;
- no solver execution;
- no live `ccx` validation;
- no SolverAdapter or runner integration;
- no subprocess use;
- no ProjectSchema mutation;
- no VLM API or provider credentials;
- no bundled solver;
- no certification;
- no industrial certification.

## Next Implementation Slices

- `OSW-EXP-050_FEASPEC_RESULT_IMPORT_WRITE_GUI_WRITER_INTEGRATION_DESIGN`
- [FEASpec CalculiX result write GUI writer integration design](feaspec_calculix_result_write_gui_writer_integration_design.md)
  records the future writer-call boundary, final confirmation, acknowledgement
  gating, failure recovery, post-write display, retry behavior, and test plan.
  It adds no GUI writer invocation, no GUI file writes, no GUI or view-model
  source mutation, no CLI behavior change, no library writer behavior change,
  no solver execution, and no issue `#8` validation.
- `OSW-EXP-051_FEASPEC_RESULT_IMPORT_WRITE_GUI_WRITER_INTEGRATION`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
