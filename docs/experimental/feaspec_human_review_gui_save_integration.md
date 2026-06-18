# FEASpec human review GUI save integration

## 1. Title

FEASpec human review GUI save integration

## 2. Status

- Experimental JSON review-record save implemented.
- No file dialog.
- No solver execution.

The GUI save path writes one FEASpec human-review JSON record to an explicit
caller-provided path. It does not select files for the user, create parent
directories, write export bundles, write `.inp` files, import results, request
runs, or execute solvers.

## 3. Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- The public release, release tag, and release assets are unchanged.
- Issue `#8` live validation remains separate and open until installed
  CalculiX evidence exists on a prepared machine.

## 4. Package path

- GUI module: `src/osw/gui/dialogs/feaspec_human_review_dialog.py`
- Dialog class: `FEASpecHumanReviewDialog`
- JSON IO helper: `dump_human_review_record`

## 5. Save behavior

- Explicit path only.
- Overwrite is blocked unless the dialog is constructed or configured with
  overwrite enabled.
- Parent directories are not created implicitly.
- The in-memory record preview is validated before writing.
- The write operation creates one JSON review record.
- The save status is surfaced through the dialog status label and test
  accessors.

## 6. Disabled reasons

The Save Record action is disabled when:

- the save path is missing;
- the parent directory is missing;
- the record preview is invalid;
- overwrite is required but not acknowledged.

Disabled reasons are shown in the action summary and save button tooltip.

## 7. Safety boundary

- No file dialog.
- No export bundle.
- No `.inp`.
- No solver execution.
- No `ccx`.
- No SolverAdapter.
- No runner.
- No subprocess or external command invocation.
- No result import.
- No ProjectSchema mutation.
- No VLM API or credentials.
- No dependency install or upgrade.

External solvers are optional and not bundled. This GUI save integration is not
live CalculiX validation and does not close issue `#8`.

## 8. Testing

Focused GUI tests cover:

- `tmp_path` save;
- overwrite guard;
- missing parent handling;
- invalid record preview handling;
- no `.inp` output;
- no export bundle output;
- no solver side effects;
- close/cancel without side effects.

Guardrail tests scan the GUI source and docs for file-dialog, solver,
adapter/runner, subprocess, result-import, ProjectSchema, VLM, and certification
drift.

## 9. Non-goals

- No file dialog in this gate.
- No run gate.
- No result import.
- No export write from the GUI.
- No CalculiX execution.
- No certification.
- No bundled external solver.
- No stable production claim.

## 10. Next implementation slices

- [FEASpec human review GUI file dialog design](feaspec_human_review_gui_file_dialog_design.md)
- `OSW-EXP-026_FEASPEC_HUMAN_REVIEW_GUI_FILE_DIALOG_IMPLEMENTATION`
- `OSW-EXP-027_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`
- `OSW-EXP-028_FEASPEC_RESULT_IMPORT_MODEL`
