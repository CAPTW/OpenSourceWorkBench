# FEASpec human review GUI dialog implementation

## 1. Title

FEASpec human review GUI dialog implementation

## 2. Status

- Read-only GUI dialog implemented.
- Bound to the existing pure Python human-review dialog view-model.
- Explicit JSON review-record save implemented when a caller provides a safe
  path.
- Review-record JSON file dialog path selection implemented.
- No result import implementation.
- No installed-only run gate implementation.
- No solver execution.

The implementation is an experimental PySide6 dialog surface for inspecting
existing human-review evidence. The follow-up save integration writes only one
human-review JSON record to an explicit caller-provided path. It does not write
export bundles, result artifacts, run metadata, ProjectSchema files, release
assets, credentials, or solver outputs.

## 3. Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- The public release, release tag, and release assets are unchanged by this
  gate.
- Issue `#8` live validation remains separate and open until installed
  CalculiX evidence exists on a prepared machine.

## 4. Module path

- `src/osw/gui/dialogs/feaspec_human_review_dialog.py`
- Dialog package export: `osw.gui.dialogs.FEASpecHumanReviewDialog`

The module imports PySide6 only inside the optional GUI layer and binds to
`osw.experimental.feaspec.human_review_viewmodel`. It does not import solver
adapters, runners, exporters, result importers, ProjectSchema persistence,
VLM providers, or credential handling.

## 5. Dialog class

`FEASpecHumanReviewDialog` accepts either a `HumanReviewDialogState` or a
mapping of view-model inputs. The dialog normalizes that input through
`build_human_review_dialog_state` and then renders the resulting state.

The dialog is read-only. Action buttons display view-model enablement and
disabled reasons; they do not perform persistence, export, import, run, or
solver handoff behavior.

## 6. Panels

The implemented panels are:

- source/evidence;
- diagnostics;
- engineering summary;
- export preview;
- review actions;
- safety/limitations;
- record preview.

The panel identifiers mirror the view-model `HumanReviewDialogPanel` values so
tests can verify CLI/GUI consistency without duplicating decision logic.

## 7. Source/evidence panel

The source/evidence panel shows:

- source FEASpec id;
- reviewer;
- reviewed timestamp;
- validator report hash.

The panel is read-only and does not load files or mutate source evidence.

## 8. Diagnostics panel

The diagnostics panel renders:

- severity;
- diagnostic code;
- message;
- target reference;
- whether a diagnostic can be accepted away.

Blocker/error diagnostics remain visible as blocking evidence. Warning rows
are also shown separately with whether a reason is required or already
provided. The GUI does not implement warning acceptance editing in this gate.

## 9. Engineering and export preview panels

The engineering panel renders existing bridge and case-plan summaries. The
export preview panel renders existing no-run export preview/write summaries.
These panels are data display only; they do not create or write export bundles.

## 10. Review action panel

The review action panel displays:

- needs changes;
- reject;
- approve no-run export;
- request installed-only run;
- preview record;
- save record.

Enablement comes from the view-model action availability. Disabled reasons are
shown as button tooltips and in the action summary list. The save button is
enabled only when a safe explicit JSON path is available, the parent directory
exists, overwrite is either unnecessary or acknowledged, and the record preview
is valid.

## 11. Safety copy

The safety panel states:

- experimental prerelease human-review dialog;
- no solver execution;
- no `ccx` invocation;
- no result import or installed-only run gate implementation;
- external solvers are optional and not bundled;
- issue `#8` live validation remains separate;
- no industrial certification or production accuracy claim;
- record save uses a review-record JSON file dialog or explicit JSON path.

VFEA remains experimental. This dialog is not evidence of live CalculiX
validation and is not an authorization to run a solver.

## 12. Record preview

The record preview displays the in-memory view-model record preview as JSON.
It preserves `solver_execution_performed=false` from the record model. The
dialog can persist this preview only as one validated FEASpec human-review JSON
record at an explicit caller-provided path.

The follow-up
[FEASpec human review GUI file dialog design](feaspec_human_review_gui_file_dialog_design.md)
defined the path chooser for that explicit JSON save path. The follow-up
[FEASpec human review GUI file dialog implementation](feaspec_human_review_gui_file_dialog_implementation.md)
adds review-record JSON file dialog selection only. It adds no export bundle
write, result import, run gate, SolverAdapter/runner/subprocess path,
ProjectSchema mutation, VLM API, or solver execution.

## 13. Test accessors

The dialog exposes narrow test accessors:

- `panel_names()`;
- `diagnostic_row_count()`;
- `warning_row_count()`;
- `safety_text()`;
- `record_preview_text()`;
- `action_enabled(action)`;
- `action_disabled_reason(action)`.
- `set_save_path(path)`;
- `set_overwrite_enabled(bool)`;
- `trigger_save_record()`;
- `last_save_status()`;
- `last_save_error()`;
- `saved_record_path()`.

These accessors exist to keep GUI tests stable without adding workflow side
effects.

## 14. No-side-effect boundary

This gate adds no:

- export bundle chooser;
- result import implementation;
- installed-only run gate implementation;
- CalculiX execution;
- SolverAdapter integration;
- runner integration;
- subprocess or external command invocation;
- ProjectSchema mutation;
- VLM API or credentials;
- dependency install or upgrade;
- release, tag, asset, or issue mutation.

External solvers are optional and not bundled. No industrial certification is
claimed.

## 15. Future implementation slices

- [FEASpec human review GUI save integration](feaspec_human_review_gui_save_integration.md)
- [FEASpec human review GUI file dialog design](feaspec_human_review_gui_file_dialog_design.md)
- [FEASpec human review GUI file dialog implementation](feaspec_human_review_gui_file_dialog_implementation.md)
- `OSW-EXP-027_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`
- `OSW-EXP-028_FEASPEC_RESULT_IMPORT_MODEL`
