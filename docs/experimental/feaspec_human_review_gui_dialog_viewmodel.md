# FEASpec human review GUI dialog view-model

## 1. Title

FEASpec human review GUI dialog view-model

## 2. Status

- Experimental UI-agnostic view-model implemented.
- No GUI implementation.
- No solver execution.

The view-model is a pure Python state/action layer that a future GUI can bind
to. It does not import PySide, Qt, GUI modules, SolverAdapter, runner modules,
subprocess APIs, exporters, renderers, VLM providers, credentials,
ProjectSchema persistence, or result import behavior.

## 3. Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- The public release, tag, and assets remain unchanged.
- Issue `#8` live validation remains separate and open until installed
  CalculiX evidence exists on a prepared machine.

## 4. Package path

- `src/osw/experimental/feaspec/human_review_viewmodel.py`
- Public exports are also available from `osw.experimental.feaspec`.

## 5. Public API

- `build_human_review_dialog_state`
- `evaluate_human_review_actions`
- `build_human_review_record_preview`
- `build_human_review_save_plan`
- `explain_human_review_action_state`

Public state/result types:

- `HumanReviewDialogPanel`
- `HumanReviewDialogAction`
- `HumanReviewActionAvailability`
- `HumanReviewDialogDiagnosticRow`
- `HumanReviewDialogWarningRow`
- `HumanReviewRecordPreview`
- `HumanReviewSavePlan`
- `HumanReviewDialogState`

## 6. Panels

The view-model exposes these panel identifiers:

- source/evidence;
- diagnostics;
- engineering summary;
- export preview;
- review actions;
- safety/limitations;
- record preview.

These are identifiers only. No PySide widgets or runtime dialog classes are
implemented in this gate.

## 7. Action-state logic

The view-model computes availability and disabled reasons for:

- needs changes;
- reject;
- approve no-run export;
- request installed-only run;
- accept warning;
- reject diagnostic;
- preview record;
- save record.

The action states align with the human review record model and CLI approval
workflow. They do not authorize or trigger solver execution.

## 8. Disabled reasons

Disabled reasons include:

- missing reviewer;
- missing timestamp;
- missing source id;
- missing validator summary/hash;
- blockers/errors;
- unresolved warning reasons;
- missing README/limitations acknowledgement.

Installed-only run request additionally requires no-run export acknowledgement
and run-gate-separate acknowledgement. It records intent for a future gate
only.

## 9. Save plan

`build_human_review_save_plan` performs path analysis only:

- no write;
- no parent creation;
- overwrite detection;
- JSON-path validation.

The save plan reports `safe_path`, `parent_missing`, `overwrite_required`, and
`can_save` booleans plus disabled reasons. It does not call the JSON IO writer.

## 10. CLI/GUI consistency

The view-model keeps the same states/actions/diagnostic semantics as CLI
approval:

- `mark_needs_changes`;
- `reject`;
- `approve_no_run_export`;
- `request_installed_only_run`;
- accepted warning reasons;
- rejected diagnostic reasons;
- `solver_execution_performed=false`.

The record preview uses the existing human review record model so a future GUI
can show the same evidence that the CLI create/validate/summary workflow
uses.

## 11. Safety boundary

- No PySide/Qt import.
- No GUI implementation.
- No solver execution.
- No `ccx`.
- No SolverAdapter.
- No runner.
- No subprocess.
- No exporter/renderer side effects.
- No result import implementation.
- No run gate implementation.
- No ProjectSchema mutation.
- No VLM API or credentials.
- No dependency install or upgrade.
- No bundled external solver.
- No industrial certification.

External solvers are optional and not bundled. This view-model is not evidence
that live optional validation passed.

## 12. Future implementation slices

- `OSW-EXP-023_FEASPEC_HUMAN_REVIEW_GUI_DIALOG_IMPLEMENTATION` added a
  read-only GUI dialog implemented in `src/osw/gui/dialogs/` and bound to this
  view-model. The dialog adds no record save integration, no file dialog, no
  result import implementation, no installed-only run gate implementation, no
  SolverAdapter/runner/subprocess path, no ProjectSchema mutation, no VLM API,
  and no solver execution.
- `OSW-EXP-024_FEASPEC_HUMAN_REVIEW_GUI_SAVE_INTEGRATION`
- `OSW-EXP-025_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`
