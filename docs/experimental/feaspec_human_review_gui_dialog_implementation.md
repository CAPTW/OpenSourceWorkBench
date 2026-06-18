# FEASpec human review GUI dialog implementation

## 1. Title

FEASpec human review GUI dialog implementation

## 2. Status

- Read-only GUI dialog implemented.
- Bound to the existing pure Python human-review dialog view-model.
- No record save integration.
- No file dialog.
- No result import implementation.
- No installed-only run gate implementation.
- No solver execution.

The implementation is an experimental PySide6 dialog surface for inspecting
existing human-review evidence. It does not write review records, export
bundles, result artifacts, run metadata, ProjectSchema files, release assets,
credentials, or solver outputs.

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
forced disabled because no record save integration exists in this gate.

## 11. Safety copy

The safety panel states:

- experimental prerelease human-review dialog;
- no solver execution;
- no `ccx` invocation;
- no result import or installed-only run gate implementation;
- external solvers are optional and not bundled;
- issue `#8` live validation remains separate;
- no industrial certification or production accuracy claim;
- record save integration is not implemented in this gate.

VFEA remains experimental. This dialog is not evidence of live CalculiX
validation and is not an authorization to run a solver.

## 12. Record preview

The record preview displays the in-memory view-model record preview as JSON.
It preserves `solver_execution_performed=false` from the record model. The
preview is not persisted by this dialog.

## 13. Test accessors

The dialog exposes narrow test accessors:

- `panel_names()`;
- `diagnostic_row_count()`;
- `warning_row_count()`;
- `safety_text()`;
- `record_preview_text()`;
- `action_enabled(action)`;
- `action_disabled_reason(action)`.

These accessors exist to keep GUI tests stable without adding workflow side
effects.

## 14. No-side-effect boundary

This gate adds no:

- record save integration;
- file dialog;
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

- `OSW-EXP-024_FEASPEC_HUMAN_REVIEW_GUI_SAVE_INTEGRATION`
- `OSW-EXP-025_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`
- `OSW-EXP-026_FEASPEC_RESULT_IMPORT_DESIGN`
