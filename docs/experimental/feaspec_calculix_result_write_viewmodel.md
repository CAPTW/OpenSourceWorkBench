# FEASpec CalculiX result write view-model

## Status

Experimental UI-agnostic view-model implemented. No GUI dialog
implementation. No file dialog implementation. No writer invocation. No
ResultDataset file write. No solver execution.

This view-model is a pure Python state/action layer for a future reviewed
ResultDataset write dialog. It consumes existing result-import, draft-mapping,
write-plan, schema-payload, and optional writer-result records and exposes
panels, rows, acknowledgements, disabled reasons, save-target analysis, and
safety messages.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- The public release, release tag, release assets, and GitHub issues are not
  edited by this work.

## Package path

- `src/osw/experimental/feaspec/calculix_result_write_viewmodel.py`
- Public exports are also available from `osw.experimental.feaspec`.

## Public API

- `build_calculix_result_write_viewmodel`
- `evaluate_calculix_result_write_actions`
- `preview_calculix_result_write_record`
- `plan_calculix_result_write_save_path`
- `explain_calculix_result_write_viewmodel`

Public state/result types:

- `FEASpecCalculiXResultWriteViewModel`
- `FEASpecCalculiXResultWriteViewModelInput`
- `FEASpecCalculiXResultWritePanel`
- `FEASpecCalculiXResultWriteAction`
- `FEASpecCalculiXResultWriteActionState`
- `FEASpecCalculiXResultWriteDisabledReason`
- `FEASpecCalculiXResultWriteAcknowledgementState`
- `FEASpecCalculiXResultWriteSavePlan`
- `FEASpecCalculiXResultWriteSafetyMessage`
- `FEASpecCalculiXResultWriteRow`

## Consumed evidence

The view-model accepts already-built records from the existing stack:

- result import plan;
- ResultDataset draft mapping;
- ResultDataset write plan;
- ResultDataset schema payload;
- optional writer-result summary from a separate caller-owned write action.

It does not build parser evidence, invoke the library writer, call the CLI
write command, inspect ProjectSchema, or open GUI widgets.

## Panels

The view-model exposes stable panel identifiers for a future dialog:

- source result directory;
- artifact summary;
- diagnostics;
- draft mapping;
- write plan;
- schema manifest;
- safety limitations;
- write actions;
- write result.

These are identifiers and data rows only. No PySide widgets, Qt classes, or
runtime dialog classes are implemented in this gate.

## Actions

The view-model computes state for:

- preview import;
- preview draft mapping;
- preview write plan;
- preview schema;
- choose output directory;
- acknowledge limitations;
- acknowledge review required;
- acknowledge overwrite;
- acknowledge create directory;
- write ResultDataset;
- open written output.

The write action can become enabled only when result/import/write/schema
records are present, blockers are absent, path safety is acceptable, and all
required acknowledgements are represented. The view-model still does not
perform the write.

## Action states

Action states are:

- hidden;
- disabled;
- enabled;
- completed;
- failed.

Completed and failed write states are display-only summaries of an optional
writer-result record supplied by the caller. They are not produced by invoking
the writer from the view-model.

## Disabled reasons

Disabled reasons include:

- missing result directory;
- missing output directory;
- import plan blocked;
- write plan blocked;
- schema blocked;
- missing limitations acknowledgement;
- missing review acknowledgement;
- overwrite required;
- create directory required;
- unsafe path;
- writer failed;
- write not available.

Disabled reasons are intended to be visible in a future GUI and kept aligned
with CLI/write-plan safety semantics.

## Save path planning

`plan_calculix_result_write_save_path` performs lexical path and existing
write-plan payload analysis only. It reports:

- safe path;
- parent missing;
- overwrite required;
- create directory required;
- unsafe path;
- can select;
- can write target.

It does not call `Path.exists`, create directories, write files, open file
dialogs, invoke the writer, or copy artifacts.

## CLI and GUI consistency

The view-model preserves the same review-first meanings as the CLI write
command:

- plan and preview before write;
- explicit output directory;
- limitations acknowledgement;
- review-required acknowledgement;
- overwrite acknowledgement;
- create-directory acknowledgement;
- no artifact copying;
- no hidden solver execution;
- issue `#8` remains open.

The GUI can bind to this model later, but the model itself is not a GUI write
command.

## Safety boundary

This implementation preserves:

- no PySide or Qt import;
- no GUI dialog implementation;
- no file dialog implementation;
- no writer invocation;
- no ResultDataset file write;
- no artifact copying;
- no CLI behavior change;
- no solver execution;
- no CalculiX `ccx` invocation;
- no subprocess;
- no SolverAdapter;
- no runner;
- no ProjectSchema mutation;
- no VLM API;
- no provider credentials;
- no dependency install or upgrade;
- no release, asset, tag, or issue mutation.

External solvers are optional and are not bundled. This view-model is not
evidence that live optional validation passed.

## Relationship to existing write layers

[FEASpec CalculiX ResultDataset write plan](feaspec_calculix_result_dataset_write_plan.md)
continues to own output-path and planned-file evidence.
[FEASpec CalculiX ResultDataset schema payload model](feaspec_calculix_result_dataset_schema.md)
continues to own payload records.
[FEASpec CalculiX ResultDataset writer](feaspec_calculix_result_dataset_writer.md)
continues to own explicit library-only persistence.
[FEASpec CalculiX result import write CLI](feaspec_calculix_result_import_write_cli.md)
continues to own the existing CLI wrapper.

This view-model is a presentation state layer over those records. It does not
alter writer behavior and does not add a GUI write command.

[FEASpec CalculiX result write dialog](feaspec_calculix_result_write_dialog.md)
now consumes this view-model in a PySide6 dialog. That dialog renders panels,
actions, disabled reasons, acknowledgements, safety text, planned files, and
optional writer-result summaries. A later GUI gate adds directory-only
QFileDialog output selection in the dialog layer, while this view-model remains
pure Python and still has no PySide/Qt import, no file-dialog implementation,
no writer invocation, no ResultDataset file write, no solver execution, and no
issue `#8` validation.

## Relationship to issue #8

The view-model does not validate live `ccx`. Issue `#8` remains open until a
separate prepared-machine live CalculiX validation gate records passing
evidence. Displaying or writing reviewed ResultDataset files is not live solver
validation.

## Non-goals

- no GUI dialog implementation;
- no file dialog implementation;
- no `QFileDialog`;
- no writer invocation from the view-model;
- no ResultDataset persistence;
- no artifact copy implementation;
- no CLI behavior change;
- no solver execution;
- no live `ccx` validation;
- no SolverAdapter or runner integration;
- no subprocess use;
- no ProjectSchema mutation;
- no VLM API or provider credentials;
- no certification;
- no industrial certification;
- no bundled solver.

## Tests

Focused tests cover:

- module imports and public exports;
- panel and row construction;
- action states;
- disabled reasons;
- acknowledgement gating;
- overwrite and create-directory gating;
- lexical save-path planning;
- preview record serialization;
- no writer invocation;
- guardrails against GUI, SolverAdapter, runner, subprocess, VLM, and provider
  credential imports.

Test result files are generated under `tmp_path`; no tracked solver output
fixtures are added by this gate.

## Next implementation slices

- `OSW-EXP-047_FEASPEC_RESULT_IMPORT_WRITE_GUI_DIALOG_IMPLEMENTATION` completed
  as a display-only dialog.
- [FEASpec CalculiX result write GUI file dialog planning](feaspec_calculix_result_write_gui_file_dialog_planning.md)
  records the future QFileDialog/output-directory policy without changing the
  view-model source, opening file dialogs, invoking the writer, writing files,
  or validating issue `#8`.
- [FEASpec CalculiX result write GUI file dialog](feaspec_calculix_result_write_gui_file_dialog.md)
  records the dialog-layer output-directory selection implementation. The
  view-model source remains unchanged and continues to provide display-only
  save-plan analysis for the selected directory.
- [FEASpec CalculiX result write GUI writer integration design](feaspec_calculix_result_write_gui_writer_integration_design.md)
  records the future GUI writer-call boundary and post-write state refresh
  contract. It does not change this view-model source and does not add writer
  invocation, GUI file writes, solver execution, or issue `#8` validation.
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
