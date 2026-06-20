# FEASpec CalculiX result write dialog

Status: experimental GUI dialog implemented. Output-directory selection is
implemented with `QFileDialog` directory selection. The dialog now includes
review-first writer integration through the existing library writer after
enabled gates and explicit confirmation. No solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- The public release, release tag, release assets, and GitHub issues are not
  edited by this work.

## Package path

- `src/osw/gui/dialogs/feaspec_calculix_result_write_dialog.py`

## Dialog input

The dialog accepts `FEASpecCalculiXResultWriteViewModel`, an optional mockable
output-directory chooser for tests, an injectable ResultDataset writer, and an
injectable confirmation callback for tests. It does not accept a runner, solver
adapter, CLI command, ProjectSchema mutator, artifact-copy provider, VLM
provider, or credential provider. The view-model remains the source for panels,
rows, actions, disabled reasons, acknowledgements, safety messages, planned
files, and optional writer-result summary text.

## Panels and tabs

The dialog renders read-only panels for:

- source result directory;
- artifact summary;
- diagnostics;
- draft mapping;
- write plan;
- schema and manifest;
- safety and limitations;
- actions;
- result summary.

Each panel remains inspectable before writing files or running solvers. The
dialog is a review-first persistence surface for ResultDataset files only; it is
not a solver execution surface.

## Action rendering

The dialog renders action labels and disabled reasons from the view-model. The
choose-output-directory action is enabled and opens a directory-only chooser.
The write action is enabled only when the reviewed write plan, schema payload,
selected output directory, and acknowledgements are ready. The open-written-
output action stays disabled in this gate.

Choosing an output directory updates dialog-local display state and visible
save-plan analysis. It does not call the writer or create files. If the selected
directory no longer matches the reviewed write-plan target, the write action is
blocked until the state is reviewed again.

## Output-directory selection

Output-directory selection uses `QFileDialog.getExistingDirectory` with a
directory-selection policy. The chooser:

- selects directories only;
- treats cancel as no-op;
- updates the read-only output-directory field;
- refreshes the write-plan panel and save target analysis;
- leaves acknowledgements unchanged;
- creates no directories;
- writes no files;
- invokes no writer.

Tests use an injected chooser and `tmp_path` paths so the native dialog is not
opened during automated coverage.

## Acknowledgement rendering

The dialog renders limitation, review-required, overwrite, and create-directory
acknowledgements as disabled checkboxes. They show current view-model state but
do not mutate state, write files, create directories, or change planned paths.

## Planned files and result summary

The write-plan panel lists planned standard ResultDataset files from the
existing view-model payload and the dialog-local selected output directory. The
result panel renders an optional writer-result summary when the caller provides
one. Rendering an existing summary does not invoke the writer. After explicit
confirmation, the dialog delegates actual ResultDataset file write behavior to
the existing library writer and displays the returned status, diagnostics, and
written-file metadata.

[FEASpec CalculiX result write GUI post-write polish](feaspec_calculix_result_write_gui_post_write_polish.md)
records the current post-write display improvements. The dialog shows a
written-file table with payload kind, size, and SHA-256 hash; grouped
diagnostics; grouped limitations; failure details; retry guidance; and a
deterministic copy-ready plain-text summary as display/accessor text only. It
adds no OS clipboard integration, no open-output shell command, no artifact
copying, no CLI behavior change, and no library writer behavior change.

## Safety boundary

This GUI dialog preserves:

- QFileDialog directory selection only;
- writer invocation only after enabled gates and explicit confirmation;
- actual ResultDataset file write only through the existing library writer;
- no artifact copy;
- no directory creation during selection;
- no CLI behavior change;
- no library writer behavior change;
- no solver execution;
- no subprocess;
- no SolverAdapter;
- no runner;
- no ProjectSchema mutation;
- no VLM API;
- no provider credentials;
- no release, tag, asset, or issue mutation.

The dialog must not become a hidden persistence path or a direct external
execution path. All writes remain explicit, review-gated, and limited to the
standard ResultDataset files.

External solvers are optional and not bundled.

## Relationship to issue #8

The dialog does not validate live `ccx`. Issue `#8` remains open until a
separate prepared-machine live CalculiX validation gate records passing
evidence. Displaying ResultDataset write evidence or selecting an output
directory is not live solver validation and must not close issue `#8`.

## Fixture policy

GUI tests use `tmp_path` generated in-memory view-model payloads and avoid
tracked solver output fixtures. The tests do not stage `.dat`, `.frd`, `.sta`,
`.cvg`, `.out`, `.err`, or solver logs.

## Non-goals

- no solver execution;
- no live `ccx` validation;
- no artifact copying;
- no open-output-folder command;
- no CLI behavior change;
- no library writer behavior change;
- no SolverAdapter or runner integration;
- no subprocess use;
- no ProjectSchema mutation;
- no VLM API or provider credentials;
- no bundled solver;
- no certification;
- no industrial certification.

## Next implementation slices

- [FEASpec CalculiX result write GUI file dialog planning](feaspec_calculix_result_write_gui_file_dialog_planning.md)
  records the earlier `OSW-EXP-048_FEASPEC_RESULT_IMPORT_WRITE_GUI_FILE_DIALOG_PLANNING`
  design/planning-only gate. That historical gate added no QFileDialog
  implementation, no GUI source changes, no writer invocation, no
  ResultDataset file write, no solver execution, and no issue `#8`
  validation.
- [FEASpec CalculiX result write GUI file dialog](feaspec_calculix_result_write_gui_file_dialog.md)
  documents `OSW-EXP-049_FEASPEC_RESULT_IMPORT_WRITE_GUI_FILE_DIALOG_IMPLEMENTATION`,
  which adds directory-only output selection while preserving no writer
  invocation, no ResultDataset file writes, no directory creation during
  selection, no solver execution, and no issue `#8` validation.
- [FEASpec CalculiX result write GUI writer integration design](feaspec_calculix_result_write_gui_writer_integration_design.md)
  documents the future writer-integration contract for final confirmation,
  acknowledgement gating, writer call boundary, failure recovery, post-write
  display, retry behavior, and state refresh while preserving no implementation
  in that design gate.
- [FEASpec CalculiX result write GUI writer integration](feaspec_calculix_result_write_gui_writer_integration.md)
  documents `OSW-EXP-051_FEASPEC_RESULT_IMPORT_WRITE_GUI_WRITER_INTEGRATION`,
  which adds the guarded GUI writer call through the existing library writer
  after enabled gates and confirmation while preserving no solver execution,
  no artifact copying, no CLI behavior change, no library writer behavior
  change, and no issue `#8` validation.
- [FEASpec CalculiX result write GUI post-write polish](feaspec_calculix_result_write_gui_post_write_polish.md)
  documents `OSW-EXP-052_FEASPEC_RESULT_IMPORT_WRITE_GUI_POST_WRITE_POLISH`,
  which improves post-write status, written files, hashes, diagnostics,
  limitations, failures, retry guidance, and copy-ready display text while
  preserving no solver execution, no artifact copying, no open-output shell,
  no OS clipboard integration, no CLI/writer behavior change, and no issue
  `#8` validation.
- `OSW-EXP-050_FEASPEC_RESULT_IMPORT_WRITE_GUI_WRITER_INTEGRATION_DESIGN`
- `OSW-EXP-051_FEASPEC_RESULT_IMPORT_WRITE_GUI_WRITER_INTEGRATION`
- `OSW-EXP-052_FEASPEC_RESULT_IMPORT_WRITE_GUI_POST_WRITE_POLISH`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
