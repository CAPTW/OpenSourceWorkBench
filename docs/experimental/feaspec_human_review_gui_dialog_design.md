# FEASpec human review GUI dialog design

## 1. Title

FEASpec human review GUI dialog design

## 2. Status

- Design-only.
- No GUI implementation.
- No solver execution.

This gate defines a future dialog contract only. It does not add or modify
runtime GUI classes, result import behavior, installed-only run behavior,
SolverAdapter handoff, runner handoff, subprocess calls, VLM APIs, credentials,
ProjectSchema mutation, release assets, tags, or issues.

## 3. Release context

- `v0.1.4-rc1` is a public prerelease.
- This is post-release development on `develop`.
- The public release, release tag, and release assets are unchanged by this
  design.

## 4. Relationship to existing layers

The future dialog maps existing experimental review and export evidence into a
GUI review surface:

- FEASpec human review record model.
- CLI create/validate/summary commands.
- FEASpec validator.
- FEASpec-to-ProjectSchema bridge and CalculiX case/export preview evidence.
- Result import / run gate design.

The dialog remains downstream of validation evidence and upstream of future
export, run request, and result import surfaces. It must not blur review,
export, run, and import gates.

## 5. Existing GUI pattern references

Read-only inspection for this design used these OSW GUI patterns:

- `ReportExportDialog`: explicit user paths, confirmation buttons, object
  names, theme tokens, and no hidden workflow side effects.
- `PluginManagerDialog` and `ExecutablePathDialog`: manifest-first tables,
  diagnostics panes, safe local settings, warning copy, and injected services.
- `CalculixDeckDialog`: preview/status/diagnostics layout patterns only; the
  future human-review dialog must not add new run or parser behavior in this
  gate.
- `PropertiesPanel`: tabbed summaries and read-only section widgets.
- `WarningsProgressPanel`: stacked warning cards and visible warning states.
- `WorkflowStepper`: import-safe state contracts and disabled/active step
  semantics.
- GUI tests: optional PySide6 skip/offscreen conventions and stable object-name
  assertions for later implementation tests.

This gate performed read-only inspection only and makes no GUI source changes.

## 6. Dialog entry points

Future entry points should include:

- from FEASpec file;
- from no-run export preview;
- from no-run export write summary;
- from future project context.

Each entry point must load explicit evidence and show the same review states as
the CLI record workflow.

## 7. Dialog layout

The future dialog should use a left navigation or tab model with these panels:

- source/evidence panel;
- diagnostics panel;
- geometry/material/BC/load summary panel;
- export preview panel;
- review action panel;
- safety/limitations panel.

The default view should be read-only inspection. Mutating or saving actions
must be explicit buttons with visible disabled reasons when unavailable.

## 8. Source/evidence panel

The source/evidence panel should show:

- source FEASpec id;
- source type;
- evidence refs;
- confidence summary;
- human-readable notes.

Evidence should remain traceable to the loaded FEASpec, validator report,
bridge summary, case-plan summary, export preview summary, and export write
summary where present.

## 9. Diagnostics panel

The diagnostics panel should combine:

- validator diagnostics;
- bridge diagnostics;
- case-plan diagnostics;
- export diagnostics;
- severity filters;
- blocker highlighting.

Blockers and errors must be visually distinct from warnings. Blocker
diagnostics cannot be accepted away.

## 10. Review action panel

The review action panel should support:

- needs changes;
- reject;
- approve no-run export;
- request installed-only run;
- notes;
- reviewer;
- timestamp.

Actions should map directly to the human review record model states and CLI
actions. The review action panel records intent and evidence only; it does not
execute solver commands.

## 11. Warning acceptance UX

Warning acceptance should require:

- a warning list;
- an explicit checkbox/action;
- a required reason;
- disabled blocker diagnostics that cannot be accepted away.

Warning acceptance should be recorded per diagnostic code. The UI should not
offer one global "accept all" path for unresolved technical warnings.

## 12. Approval gating

Approval gates should be visible and deterministic:

- no-run export approval requires no blockers/errors;
- installed-only run request requires limitations/readme/run-gate
  acknowledgement;
- action buttons disabled with visible reasons.

Installed-only run request approval is a request for a later run gate. It is
not solver execution and does not authorize an automatic run.

## 13. Record preview

The record preview should include:

- JSON preview;
- summary preview;
- validation status;
- save path preview.

The JSON preview should match the CLI record schema closely enough that a
reviewer can compare GUI and CLI evidence without translation surprises.

## 14. Save behavior

Save behavior should be conservative:

- explicit save only;
- overwrite confirmation;
- no parent-dir creation unless future implementation explicitly chooses it;
- no solver execution.

Saving a review record should write only review evidence in a caller-chosen
path. It must not write export bundles, result artifacts, run metadata,
ProjectSchema files, release assets, credentials, or solver outputs.

## 15. CLI/GUI consistency

CLI/GUI consistency is required:

- same review states;
- same actions;
- same diagnostic decision semantics;
- same no-run/export/run separation copy.

The future GUI should use the same source evidence and blocked/warning/ready
semantics as `feaspec-human-review-create`,
`feaspec-human-review-validate`, and `feaspec-human-review-summary`.

## 16. Accessibility and UX

The dialog should prioritize:

- clear severity labels;
- keyboard-friendly action order;
- non-destructive default;
- readable experimental warnings.

The default action should not be approval. Rejection, needs-changes, and cancel
paths should be easy to reach without hidden side effects.

## 17. Safety copy

User-facing copy should state:

- prerelease/experimental;
- no bundled solver;
- no certification;
- no solver run;
- issue `#8` live validation separate.

The dialog must not claim stable production readiness, industrial
certification, bundled external solvers, live `ccx` validation, SolverAdapter
integration, result import implementation, run gate implementation, or VFEA
completion.

## 18. Future GUI view-model proposal

Future view-model only names:

- `FEASpecHumanReviewDialogState`
- `FEASpecHumanReviewDialogViewModel`
- `FEASpecHumanReviewActionState`

There is no implementation in this gate. A later view-model gate should define
plain state objects before PySide6 widget behavior is added.

## 19. Future implementation test plan

Future implementation tests should cover:

- dialog construction;
- disabled actions;
- warning acceptance;
- JSON preview;
- save overwrite confirmation;
- no solver calls.

Runtime GUI tests should use the repository's optional PySide6 skip/offscreen
patterns and stable object-name assertions. They should not require external
solver executables, network access, or heavy optional stacks.

## 20. Non-goals

- No GUI implementation.
- No result import implementation.
- No run gate implementation.
- No solver execution.
- No VLM API.
- No ProjectSchema mutation.
- No certification.
- No bundled external solver.
- No SolverAdapter integration.
- No runner integration.
- No subprocess or external command invocation.
- No dependency install or upgrade.
- No issue mutation.
- No release, tag, or asset mutation.

## 21. Next implementation slices

- `OSW-EXP-022_FEASPEC_HUMAN_REVIEW_GUI_DIALOG_VIEWMODEL`
- `OSW-EXP-023_FEASPEC_HUMAN_REVIEW_GUI_DIALOG_IMPLEMENTATION`
- `OSW-EXP-024_FEASPEC_HUMAN_REVIEW_GUI_SAVE_INTEGRATION`
- `OSW-EXP-025_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`
