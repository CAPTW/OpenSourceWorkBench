# FEASpec CalculiX result write dialog

Status: experimental display-only GUI dialog implemented. No QFileDialog. No
writer invocation. No ResultDataset file write. No solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- The public release, release tag, release assets, and GitHub issues are not
  edited by this work.

## Package path

- `src/osw/gui/dialogs/feaspec_calculix_result_write_dialog.py`

## Dialog input

The dialog accepts `FEASpecCalculiXResultWriteViewModel` only. It does not
accept a writer object, output path provider, file-dialog provider, runner, or
solver adapter. The view-model remains the single source for panels, rows,
actions, disabled reasons, acknowledgements, safety messages, planned files,
and optional writer-result summary text.

## Panels and tabs

The dialog renders display-only panels for:

- source result directory;
- artifact summary;
- diagnostics;
- draft mapping;
- write plan;
- schema and manifest;
- safety and limitations;
- actions;
- result summary.

Each panel is read-only. The dialog is an inspection surface for reviewed
write-plan evidence, not a persistence command surface.

## Action rendering

The dialog renders action labels and disabled reasons from the view-model. The
write action, output-directory action, and open-output action stay disabled in
this gate. A future gate may add a file-dialog integration, but this
implementation has no QFileDialog and no active directory-selection control.

## Acknowledgement rendering

The dialog renders limitation, review-required, overwrite, and create-directory
acknowledgements as disabled checkboxes. They show current view-model state but
do not mutate state, write files, or change planned paths.

## Planned files and result summary

The write-plan panel lists planned standard ResultDataset files from the
existing view-model payload. The result panel renders an optional
writer-result summary when the caller provides one. Rendering an existing
summary does not invoke the writer.

## Safety boundary

This GUI dialog preserves:

- no QFileDialog;
- no writer invocation;
- no ResultDataset file write;
- no artifact copy;
- no CLI behavior change;
- no solver execution;
- no subprocess;
- no SolverAdapter;
- no runner;
- no ProjectSchema mutation;
- no VLM API;
- no provider credentials;
- no release, tag, asset, or issue mutation.

The dialog must not become a hidden persistence path or a direct external
execution path.

External solvers are optional and not bundled.

## Relationship to issue #8

The dialog does not validate live `ccx`. Issue `#8` remains open until a
separate prepared-machine live CalculiX validation gate records passing
evidence. Displaying ResultDataset write evidence is not live solver
validation and must not close issue `#8`.

## Fixture policy

GUI tests use `tmp_path` generated in-memory view-model payloads and avoid
tracked solver output fixtures. The tests do not stage `.dat`, `.frd`, `.sta`,
`.cvg`, `.out`, `.err`, or solver logs.

## Non-goals

- no file-dialog implementation;
- no writer invocation;
- no ResultDataset persistence;
- no artifact copying;
- no CLI behavior change;
- no solver execution;
- no live `ccx` validation;
- no SolverAdapter or runner integration;
- no subprocess use;
- no ProjectSchema mutation;
- no VLM API or provider credentials;
- no bundled solver;
- no certification;
- no industrial certification.

## Next implementation slices

- [FEASpec CalculiX result write GUI file dialog planning](feaspec_calculix_result_write_gui_file_dialog_planning.md)
  defines `OSW-EXP-048_FEASPEC_RESULT_IMPORT_WRITE_GUI_FILE_DIALOG_PLANNING`
  as design/planning-only. It adds no QFileDialog implementation, no GUI source
  changes, no writer invocation, no ResultDataset file write, no solver
  execution, and no issue `#8` validation.
- `OSW-EXP-049_FEASPEC_RESULT_IMPORT_WRITE_GUI_FILE_DIALOG_IMPLEMENTATION`
- `OSW-EXP-050_FEASPEC_RESULT_IMPORT_WRITE_GUI_WRITER_INTEGRATION_NO_SOLVER`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
