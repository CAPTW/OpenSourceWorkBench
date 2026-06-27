# Optional solver plugin manifest deactivation view-model

## Status

Experimental pure deactivation view-model extension implemented.

- Pure Python data/state transformation.
- No deactivation persistence.
- No GUI behavior.
- No CLI behavior.
- No discovery execution.
- No validation execution.
- No file deletion.
- No dependency uninstall.
- No solver uninstall.
- No solver execution.

This gate (OSW-EXP-085) implements the pure deactivation view-model extension
promised by the OSW-EXP-081 deactivation design, on top of the OSW-EXP-079
activation view-model. It adds deactivation-specific records and deterministic
state transformation only.

## Purpose

Translate already-supplied activation/deactivation candidate data into
deactivation readiness, acknowledgement, evidence-retention, shared-stack,
diagnostic, trust, and disabled/future action-state records that a future GUI or
source-integration gate can bind to safely.

Deactivation lifecycle inputs and acknowledgement satisfaction are supplied by
the caller; this layer only classifies and renders them. It does not deactivate
anything, persist state, delete files, uninstall anything, run discovery,
validate, or execute solvers.

## Public module and class names

Module:

`src/osw/experimental/optional_solvers/plugin_manifest_deactivation_viewmodel.py`

Public view-model and records:

- `OptionalSolverPluginManifestDeactivationViewModel`
- `OptionalSolverPluginManifestDeactivationSummaryViewModel`
- `OptionalSolverPluginManifestDeactivationCandidateInput`
- `OptionalSolverPluginManifestDeactivationCandidateRowViewModel`
- `OptionalSolverPluginManifestDeactivationAcknowledgementRowViewModel`
- `OptionalSolverPluginManifestDeactivationDiagnosticViewModel`
- `OptionalSolverPluginManifestDeactivationSharedStackRowViewModel`
- `OptionalSolverPluginManifestDeactivationEvidenceRowViewModel`
- `OptionalSolverPluginManifestDeactivationTrustBadgeViewModel`
- `OptionalSolverPluginManifestDeactivationActionState`
- `OptionalSolverPluginManifestDeactivationAction`
- `OptionalSolverPluginManifestDeactivationState`
- `OptionalSolverPluginManifestDeactivationReadiness`

Builders/helpers: `build_optional_solver_plugin_manifest_deactivation_viewmodel`,
`render_optional_solver_plugin_manifest_deactivation_summary` (in-memory),
`summarize_*`, `explain_*`,
`redact_optional_solver_plugin_manifest_deactivation_source_reference`.
Convenience constructors: `from_candidates`, `from_activation_viewmodel`,
`unavailable`, `all_deactivated`, `all_blocked`.

## Input boundary

The view-model consumes supplied data only:

- an `OptionalSolverPluginManifestActivationViewModel` (OSW-EXP-079)
- caller-supplied `OptionalSolverPluginManifestDeactivationCandidateInput` records
- caller-supplied acknowledgement satisfaction, deactivation/lifecycle state,
  evidence state, and shared-stack/conflict flags

It performs no file IO, no file deletion, no uninstall, no JSON parsing from
paths, no plugin package import, no directory scan, no network fetch, and no
discovery execution.

## Deactivation state machine

The OSW-EXP-081 states are modeled: `active_candidate`, `deactivation_requested`,
`deactivation_blocked`, `deactivated`, `deactivation_error`,
`reactivation_requested`, and `future_reactivation_required`. The blocked
transitions are exposed via `blocked_transitions` (e.g., inactive-preview
directly to deactivated; deactivation to discovery/validation execution;
deactivation to dependency/solver uninstall; deactivation to solver execution;
deactivation to issue closure; deactivation to release mutation).

## Readiness rules

Per-view-model readiness: `unavailable_no_activation_state`,
`unavailable_no_active_candidates`, `blocked_acknowledgement`,
`blocked_state_conflict`, `blocked_shared_stack_warning`, `ready_non_persistent`,
`deactivated`, `reactivation_future_gate`, and `error`.

Ready (`ready_non_persistent`) requires supplied active-candidate state, no state
conflict, shared-stack warnings absent or acknowledged, and all required
acknowledgements satisfied. Ready is still not persisted, still not file
deletion, still not uninstall, still not validation failure, still not issue
closure, and still not discovery execution in this gate.

## Acknowledgement model

Required acknowledgement identifiers: `not_file_deletion`,
`not_dependency_uninstall`, `not_solver_uninstall`, `not_issue_closure`,
`not_release_mutation`, `not_validation_evidence_deletion`,
`no_discovery_execution`, `no_solver_execution`, `deactivation_history_visible`,
and `conflict_or_shared_stack_warning` (required only when a shared stack or state
conflict exists). Missing required acknowledgements are visibly blocking. The
caller supplies satisfaction booleans; the view-model never persists them.

## Diagnostic vocabulary

The view-model surfaces the OSW-EXP-081 `OSPMG_DEACTIVATION_*` codes, exposed as
`OSPMG_DEACTIVATION_DIAGNOSTIC_CODES` and on each view-model as
`reserved_diagnostic_codes`: `OSPMG_DEACTIVATION_ACTIVE_REQUIRED`,
`OSPMG_DEACTIVATION_ACK_REQUIRED`, `OSPMG_DEACTIVATION_NOT_FILE_DELETE`,
`OSPMG_DEACTIVATION_NOT_UNINSTALL`, `OSPMG_DEACTIVATION_NOT_VALIDATION`,
`OSPMG_DEACTIVATION_NO_DISCOVERY_EXECUTION`,
`OSPMG_DEACTIVATION_NO_SOLVER_EXECUTION`,
`OSPMG_DEACTIVATION_NOT_ISSUE_CLOSURE`,
`OSPMG_DEACTIVATION_NOT_RELEASE_MUTATION`,
`OSPMG_DEACTIVATION_EVIDENCE_RETAINED`,
`OSPMG_DEACTIVATION_SHARED_STACK_WARNING`, `OSPMG_DEACTIVATION_STATE_CONFLICT`,
`OSPMG_DEACTIVATION_PERSISTENCE_NOT_IMPLEMENTED`, and
`OSPMG_DEACTIVATION_DEACTIVATED`. None of these diagnostics are validation-pass or
validation-fail evidence.

## Rendered view-model sections

- summary (readiness, state, counts, evidence-retained, honesty flags)
- deactivation candidate rows (with redacted references)
- acknowledgements
- diagnostics
- shared-stack/conflicts
- evidence retention
- trust/provenance badges
- action states
- in-memory redacted summary (`render_*`)

The summary carries honesty flags that remain false: `file_deletion_performed`,
`dependency_uninstall_performed`, `solver_uninstall_performed`,
`discovery_execution_performed`, `validation_execution_performed`,
`solver_execution_performed`, `issue_mutation_performed`,
`release_mutation_performed`, and `certification_claimed`.
`deactivation_performed` stays false unless the caller supplies already-deactivated
state.

## Source/trust/provenance behavior

User-selected and plugin-provided manifests are untrusted by default. Source
references are redacted by default (path-like references shortened to their final
segment). A trust label is not certification, and a deactivated state is not
validation evidence.

## Validation and evidence policy

Deactivation does not delete or rewrite validation evidence. Deactivation does
not convert skipped-missing into pass or fail. Deactivation does not close live
validation issues. Historical validation evidence is retained and reportable. A
deactivated candidate is not a validation failure; it is simply non-active.

## Relationship to OSW-EXP-081 design

This gate implements the pure view-model extension layer of the OSW-EXP-081
deactivation design. Deactivation persistence, GUI button behavior, CLI behavior,
discovery integration, validation, install/uninstall, solver execution, issue
closure, and release mutation remain future-gated.

## Relationship to OSW-EXP-079 activation view-model

The deactivation view-model adapts OSW-EXP-079 activation view-model records
(candidate and conflict rows) without mutating them and without adding PySide/Qt
imports. It does not persist activation or deactivation state and does not turn a
deactivated state into validation evidence.

## Relationship to OSW-EXP-080 activation GUI

No GUI code is added in this gate. The activation GUI may display a `deactivated`
state when supplied by a view-model, but this gate adds no buttons, callbacks,
menus, persistence, or widget behavior.

## Relationship to OSW-EXP-083/084 discovery-refresh view-model and GUI

The discovery-refresh view-model and GUI continue to treat deactivated candidates
as excluded or inactive. This gate changes no discovery-refresh source behavior
and no passive discovery behavior.

## Relationship to live optional validation issues

Issues `#6` through `#11` remain open. Deactivation is not live optional
validation; a deactivated state must not mark issues ready to close. Skipped-missing
remains skipped-missing; prepared-machine validation remains a separate gate.

## Relationship to CLI and export summary

No CLI behavior changes and no CLI deactivation command are added. The in-memory
redacted summary helper writes no files, touches no clipboard, and opens no shell,
browser, or output folder.

## Non-actions

This gate does not:

- implement deactivation or deactivation persistence
- implement GUI or CLI behavior
- delete manifest files
- uninstall dependencies or solvers
- import plugin packages, scan directories, or fetch network manifests
- run discovery, validation, or solvers
- install dependencies
- mutate issues, releases, tags, or assets
- bump versions
- make any validation-pass claim, validation-fail claim, issue-closure claim,
  bundled-solver claim, or certification claim

Deactivation is not deletion. Deactivation is not uninstall. Deactivation is not a
validation failure. User-selected and plugin-provided manifests remain untrusted;
built-ins remain authoritative; historical validation evidence is retained;
skipped-missing optional validation remains neither pass nor failure, and issues
`#6` through `#11` stay open.

## GUI implementation status

A PySide GUI surface for this view-model is implemented in OSW-EXP-086:
[Optional solver plugin manifest deactivation GUI implementation](optional_solver_plugin_manifest_deactivation_gui_implementation.md)
(`src/osw/gui/dialogs/optional_solver_plugin_manifest_deactivation_panel.py`).
The panel renders this view-model's records only and stays view-model driven and
non-mutating; the view-model itself remains pure and gains no PySide/Qt imports.

## Future gates

- `OSW-EXP-087_OPTIONAL_SOLVER_PLUGIN_MANIFEST_REACTIVATION_DESIGN` — designed in
  [Optional solver plugin manifest reactivation design](optional_solver_plugin_manifest_reactivation_design.md)
  (design-only; reactivation view-model/GUI/persistence remain future-gated).
- A future deactivation persistence gate (out of scope here).
- A future deactivation source/discovery-integration gate.
- `OSW-VALID` prepared-machine validation reuse.
