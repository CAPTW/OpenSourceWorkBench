# FEASpec human review UI design

## 1. Title

FEASpec human review UI design

## 2. Status

- Design-only.
- No GUI implementation.
- No solver execution.

## 3. Release context

- v0.1.4-rc1 is a public prerelease.
- This is post-release design work on `develop`.
- No release mutation, tag mutation, asset mutation, issue mutation, or live
  optional validation execution is introduced in this gate.

## 4. Relationship to existing layers

This design defines the human-review boundary that sits between:

- FEASpec candidate and approved records.
- FEASpec validator report.
- FEASpec-to-ProjectSchema bridge diagnostics.
- CalculiX case-plan diagnostics.
- No-run export preview.
- No-run export write summary.
- Result import / run-gate design documents.

It does not implement any downstream execution path.

## 5. Safety principle

- No automatic unreviewed solver execution.
- No implicit `ccx` run after no-run export preview/write.
- Review, export, run, and import are separate gates.
- Any future run flow must be user-authenticated and installed-only.

## 6. Review workflow

The UI flow is designed to support:

1. Load FEASpec candidate or approved spec.
2. Inspect source data and evidence confidence.
3. Inspect validator diagnostics.
4. Inspect bridge diagnostics.
5. Inspect case-plan diagnostics.
6. Inspect no-run export preview output.
7. Present approval decision (`approve`, `reject`, `needs-changes`) or request.
8. Optionally accept warnings and continue when allowed.
9. Record outcome:
   - approved for no-run export,
   - or approved to request installed-only run.

## 7. Review states

- `unreviewed`
- `needs changes`
- `rejected`
- `approved for no-run export`
- `approved for installed-only run request`

## 8. Screen/panel design

- Source/evidence panel.
- Geometry graph summary panel.
- Materials/sections panel.
- Boundary/load panel.
- Diagnostics panel.
- Provenance and human-review panel.
- Export preview panel.
- Safety and limitations panel.

## 9. Required review record fields

- Reviewer identity.
- Timestamp.
- Action.
- Accepted warnings.
- Rejected diagnostics.
- Review notes.
- Source FEASpec identifier.
- Validator report hash or summary.
- Bridge/case/export summary.

## 10. Approval blockers

The following block approval:

- candidate spec not reviewed.
- validator blockers / errors.
- missing explicit units.
- missing explicit human review.
- unresolved bridge diagnostics.
- case-plan not ready where required.
- no-run export not reviewed.

## 11. Warning acceptance

- Warnings can be accepted only with explicit user action.
- Each accepted warning must record a reason.
- Blocker diagnostics cannot be accepted away.

## 12. No-run export relationship

- Preview must remain a read path.
- Preview shows planned bundle metadata and diagnostics only.
- Write command can persist a local no-run bundle.
- No solver execution is tied to preview or bundle write.
- `README_RUN_FIRST.txt` is required to be reviewed before any installed-only run request.

## 13. Installed-only run gate relationship

- Run gate remains separate from review/export.
- Run gate requires explicit user authorization.
- Run gate requires installed `ccx` availability.
- Run gate requires reviewed no-run artifact metadata.
- No hidden solver installation.
- Issue `#8` remains open until installed-only validation passes.

## 14. Result import relationship

- Result import is separate from review and run.
- Import consumes explicit result artifacts only.
- Import must never invoke solver execution.
- Result import links result artifacts to review/export/run metadata.

## 15. CLI/GUI consistency

- CLI preview/write and GUI workflows must present matching states and
  diagnostics.
- JSON/text preview fields should map directly to UI panels so behavior is
  predictable and auditable.
- `blocked`, `ready-with-warnings`, and `ready` semantics must stay aligned.

## 16. UX copy guidelines

- Prerelease and experimental wording must be explicit.
- No certification claim.
- No bundled external solver claims.
- No “run now” without explicit installed-only authorization flow.

## 17. Future persistence model

- The [FEASpec human review record model](feaspec_human_review_record_model.md)
  now provides the experimental data boundary for reviewer, action, accepted
  warning, diagnostic decision, validator summary, bridge/case/export summary,
  and solver-execution flag evidence.
- The record model is not a GUI implementation.
- The [FEASpec human review CLI approval](feaspec_human_review_cli_approval.md)
  workflow can create, validate, and summarize JSON review records, but it is
  not a GUI implementation, run gate, result importer, or solver execution
  path.
- Future GUI persistence may store a review record with a project draft and/or
  export manifest only in a separately scoped gate.

## 18. Future GUI commands/actions

- load FEASpec.
- run validation preview.
- review diagnostics.
- approve for no-run export.
- write no-run export.
- request run gate.
- import results.

The follow-up
[FEASpec human review GUI dialog design](feaspec_human_review_gui_dialog_design.md)
refines the future dialog contract with entry points, panels, disabled action
reasons, warning acceptance, approval gating, record preview, save behavior,
CLI/GUI consistency, and a future view-model proposal. It is design-only and
does not add GUI implementation, result import, run gate behavior, SolverAdapter
or runner integration, subprocess calls, ProjectSchema mutation, VLM APIs,
dependency installation, or solver execution.

[FEASpec human review GUI dialog view-model](feaspec_human_review_gui_dialog_viewmodel.md)
now implements the UI-agnostic state/action layer under the experimental
FEASpec package. It is not a PySide/Qt widget implementation and does not add
result import, a run gate, solver execution, ProjectSchema mutation, VLM APIs,
dependency installation, or live issue `#8` validation.

## 19. Non-goals

- No GUI implementation.
- No result import implementation.
- No run gate implementation.
- No solver execution.
- No VLM API.
- No certification.
- No bundled solvers.

## 20. Future implementation slices

- `OSW-EXP-019_FEASPEC_HUMAN_REVIEW_RECORD_MODEL` provides the experimental
  record model only.
- `OSW-EXP-020_FEASPEC_HUMAN_REVIEW_CLI_APPROVAL` provides the record-only CLI
  workflow.
- `OSW-EXP-021_FEASPEC_HUMAN_REVIEW_GUI_DIALOG_DESIGN`
- `OSW-EXP-022_FEASPEC_HUMAN_REVIEW_GUI_DIALOG_VIEWMODEL`
- `OSW-EXP-023_FEASPEC_HUMAN_REVIEW_GUI_DIALOG_IMPLEMENTATION`
- `OSW-EXP-024_FEASPEC_HUMAN_REVIEW_GUI_SAVE_INTEGRATION`
- `OSW-EXP-025_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`
