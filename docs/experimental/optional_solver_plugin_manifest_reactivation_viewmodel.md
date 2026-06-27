# Optional solver plugin manifest reactivation view-model

## Status

Experimental pure reactivation view-model extension implemented.

- Pure Python data/state transformation.
- No reactivation persistence.
- No GUI behavior.
- No CLI behavior.
- No automatic activation.
- No trust restoration.
- No file restore, no file rewrite, and no file deletion.
- No discovery execution.
- No validation execution.
- No solver execution.
- No dependency install and no dependency uninstall.
- No solver uninstall.
- No issue mutation and no release mutation.

This gate (OSW-EXP-088) implements the pure reactivation view-model extension
promised by the OSW-EXP-087 reactivation design, on top of the OSW-EXP-085
deactivation view-model. It adds reactivation-specific records and deterministic
state transformation only.

## Purpose

Translate already-supplied deactivation/reactivation candidate data into
reactivation readiness, acknowledgement, stale-source/re-preview,
deactivation-history, evidence-retention, shared-stack, diagnostic, trust, and
disabled/future action-state records that a future GUI or source-integration gate
can bind to safely.

Reactivation lifecycle inputs, stale-source state, and acknowledgement
satisfaction are supplied by the caller; this layer only classifies and renders
them. It does not reactivate anything, automatically activate candidates, restore
trust, persist state, restore/rewrite/delete files, install/uninstall anything,
run discovery, validate, or execute solvers.

## Public module and class names

Module:

`src/osw/experimental/optional_solvers/plugin_manifest_reactivation_viewmodel.py`

Public view-model and records:

- `OptionalSolverPluginManifestReactivationViewModel`
- `OptionalSolverPluginManifestReactivationSummaryViewModel`
- `OptionalSolverPluginManifestReactivationCandidateInput`
- `OptionalSolverPluginManifestReactivationCandidateRowViewModel`
- `OptionalSolverPluginManifestReactivationAcknowledgementRowViewModel`
- `OptionalSolverPluginManifestReactivationDiagnosticViewModel`
- `OptionalSolverPluginManifestReactivationSharedStackRowViewModel`
- `OptionalSolverPluginManifestReactivationStaleSourceRowViewModel`
- `OptionalSolverPluginManifestReactivationEvidenceRowViewModel`
- `OptionalSolverPluginManifestReactivationTrustBadgeViewModel`
- `OptionalSolverPluginManifestReactivationActionState`
- `OptionalSolverPluginManifestReactivationAction`
- `OptionalSolverPluginManifestReactivationState`
- `OptionalSolverPluginManifestReactivationReadiness`

Builders/helpers: `build_optional_solver_plugin_manifest_reactivation_viewmodel`,
`render_optional_solver_plugin_manifest_reactivation_summary` (in-memory),
`summarize_*`, `explain_*`,
`redact_optional_solver_plugin_manifest_reactivation_source_reference`.
Convenience constructors: `from_candidates`, `from_deactivation_viewmodel`,
`from_activation_viewmodel`, `unavailable`, `all_blocked`,
`all_future_activation_required`.

## Input boundary

The view-model consumes supplied data only:

- an `OptionalSolverPluginManifestDeactivationViewModel` (OSW-EXP-085)
- an `OptionalSolverPluginManifestActivationViewModel` (OSW-EXP-079)
- caller-supplied `OptionalSolverPluginManifestReactivationCandidateInput` records
- caller-supplied acknowledgement satisfaction, stale-source state,
  deactivation-history/evidence state, and shared-stack/conflict/unsafe-claim flags

It performs no file IO, no file restore/rewrite/delete, no install or uninstall,
no JSON parsing from paths, no plugin package import, no directory scan, no network
fetch, and no discovery execution.

## Reactivation state machine

The OSW-EXP-087 states are modeled: `deactivated`, `reactivation_requested`,
`reactivation_blocked`, `reactivation_ready`, `future_activation_required`,
`active_candidate_future_gate`, and `reactivation_error`. The blocked transitions
are exposed via `blocked_transitions` (e.g., inactive-preview directly to
reactivated; deactivated directly to active_candidate without review and
acknowledgements; reactivation to discovery/validation execution; reactivation to
dependency installation; reactivation to solver execution; reactivation to issue
closure; reactivation to release mutation; reactivation to certification claim).

## Readiness rules

Per-view-model readiness: `unavailable_no_deactivation_state`,
`unavailable_no_deactivated_candidates`, `blocked_acknowledgement`,
`blocked_conflict`, `blocked_shared_stack_warning`,
`blocked_stale_source_repreview`, `blocked_unsafe_claim`, `ready_non_persistent`,
`future_activation_required`, `active_candidate_future_gate`, and `error`.

Ready (`ready_non_persistent`) requires a supplied deactivated candidate, no
unsafe claim, no unresolved conflict, shared-stack warnings absent or
acknowledged, stale-source re-preview absent or acknowledged, and all required
acknowledgements satisfied. Ready is still not persisted, still not automatic
activation, still not trust restoration, still not validation evidence, still not
dependency installation, and still not solver execution; it routes back through
future activation review.

## Acknowledgement model

Required acknowledgement identifiers: `reactivation_not_validation`,
`reactivation_not_trust_restoration`, `reactivation_not_install`,
`reactivation_no_solver_execution`, `reactivation_not_issue_closure`,
`reactivation_not_release_mutation`, `reactivation_history_retained`,
`reactivation_requires_activation_review`, `untrusted_source`,
`no_discovery_execution`, `no_plugin_package_import`,
`trust_label_not_certification`, plus the conditional
`conflict_or_shared_stack_warning` (required only when a conflict or shared stack
exists) and `stale_source_requires_repreview` (required only when a stale/missing
source exists). Missing required acknowledgements are visibly blocking. The caller
supplies satisfaction booleans; the view-model never persists them.

## Diagnostic vocabulary

The view-model surfaces the OSW-EXP-087 `OSPMG_REACTIVATION_*` codes, exposed as
`OSPMG_REACTIVATION_DIAGNOSTIC_CODES` and on each view-model as
`reserved_diagnostic_codes`: `OSPMG_REACTIVATION_DEACTIVATED_REQUIRED`,
`OSPMG_REACTIVATION_ACK_REQUIRED`, `OSPMG_REACTIVATION_UNTRUSTED_SOURCE`,
`OSPMG_REACTIVATION_NOT_TRUST_RESTORE`, `OSPMG_REACTIVATION_NOT_VALIDATION`,
`OSPMG_REACTIVATION_NO_INSTALL`, `OSPMG_REACTIVATION_NO_SOLVER_EXECUTION`,
`OSPMG_REACTIVATION_NOT_ISSUE_CLOSURE`, `OSPMG_REACTIVATION_NOT_RELEASE_MUTATION`,
`OSPMG_REACTIVATION_NOT_CERTIFICATION`, `OSPMG_REACTIVATION_HISTORY_RETAINED`,
`OSPMG_REACTIVATION_REVIEW_REQUIRED`, `OSPMG_REACTIVATION_CONFLICT_BLOCKED`,
`OSPMG_REACTIVATION_SHARED_STACK_WARNING`,
`OSPMG_REACTIVATION_STALE_SOURCE_REPREVIEW_REQUIRED`,
`OSPMG_REACTIVATION_UNSAFE_CLAIM`, `OSPMG_REACTIVATION_NO_DISCOVERY_EXECUTION`,
`OSPMG_REACTIVATION_NO_PLUGIN_IMPORT`,
`OSPMG_REACTIVATION_PERSISTENCE_NOT_IMPLEMENTED`, and
`OSPMG_REACTIVATION_FUTURE_GATE`. None of these diagnostics are validation-pass or
validation-failure-reversal evidence.

## Rendered view-model sections

- summary (readiness, state, counts, history/evidence-retained, honesty flags)
- reactivation candidate rows (with redacted references)
- acknowledgements
- diagnostics
- shared-stack/conflicts
- stale-source/re-preview
- evidence retention and deactivation history
- trust/provenance badges
- action states
- in-memory redacted summary (`render_*`)

The summary carries honesty flags that remain false: `reactivation_performed`,
`automatic_activation_performed`, `trust_restoration_performed`,
`file_restore_performed`, `file_rewrite_performed`, `file_deletion_performed`,
`dependency_installation_performed`, `dependency_uninstall_performed`,
`solver_uninstall_performed`, `discovery_execution_performed`,
`validation_execution_performed`, `solver_execution_performed`,
`issue_mutation_performed`, `release_mutation_performed`, and
`certification_claimed`.

## Source/trust/provenance behavior

User-selected and plugin-provided manifests are untrusted by default. Source
references are redacted by default (path-like references shortened to their final
segment). A trust label is not certification, a reactivation state is not
validation evidence, and reactivation is not trust restoration.

## Stale-source and re-preview policy

A missing/moved/changed source is not silently trusted. A stale source blocks
reactivation until the caller supplies the `stale_source_requires_repreview`
acknowledgement (representing a future explicit re-preview through the explicit
import boundary). The view-model reads no files and performs no file restoration,
rewrite, or deletion; re-preview itself remains a future, separate explicit user
action.

## Validation and evidence policy

Reactivation is not validation success and is not validation failure reversal. It
does not delete or rewrite deactivation history or historical validation evidence.
Deactivation history and evidence remain retained and visible. Skipped-missing
remains skipped-missing. Reactivation does not close live validation issues. A
reactivation-ready candidate is simply a deactivated candidate routed back toward
future activation review.

## Relationship to OSW-EXP-087 design

This gate implements the pure view-model extension layer of the OSW-EXP-087
reactivation design. Reactivation persistence, GUI button behavior, CLI behavior,
source mutation, discovery integration, validation, install/uninstall, solver
execution, issue closure, and release mutation remain future-gated.

## Relationship to OSW-EXP-085 deactivation view-model

The reactivation view-model adapts OSW-EXP-085 deactivation view-model records
(deactivated candidate and shared-stack rows) without mutating them and without
adding PySide/Qt imports. It does not persist state and does not convert
deactivated state into active candidate state.

## Relationship to OSW-EXP-079 activation view-model

Reactivation routes back through future activation review. This gate changes no
activation view-model source. Reactivation-ready is not active-candidate
persistence, and the adapter from the activation view-model reads deactivated
candidate rows without mutating them.

## Relationship to OSW-EXP-080/086 activation and deactivation GUI

No GUI code is added in this gate. A future reactivation GUI can bind to this
view-model, but this gate adds no buttons, callbacks, menus, persistence, or
widget behavior.

## Relationship to OSW-EXP-083/084 discovery-refresh view-model and GUI

Reactivation is not discovery refresh. Reactivated or reactivation-ready
candidates do not automatically become discovery inputs. This gate changes no
discovery-refresh source behavior and no passive discovery behavior.

## Relationship to live optional validation issues

Issues `#6` through `#11` remain open. Reactivation is not live optional
validation; a reactivation-ready or future-activation-required state must not mark
issues ready to close. Skipped-missing remains skipped-missing, and
prepared-machine validation remains a separate gate.

## Relationship to CLI and export summary

No CLI behavior changes and no CLI reactivation command are added. The in-memory
redacted summary helper writes no files, touches no clipboard, and opens no shell,
browser, or output folder.

## Non-actions

This gate does not:

- implement reactivation or reactivation persistence
- automatically activate candidates or restore trust
- implement GUI or CLI behavior
- restore, rewrite, or delete files
- install or uninstall dependencies, or uninstall solvers
- import plugin packages, scan directories, or fetch network manifests
- run discovery, validation, or solvers
- mutate issues, releases, tags, or assets
- bump versions
- make any validation-pass claim, validation-failure-reversal claim,
  issue-closure claim, bundled-solver claim, or certification claim

Reactivation is not automatic activation. Reactivation is not trust restoration.
Reactivation is not validation. User-selected and plugin-provided manifests remain
untrusted; built-ins remain authoritative; deactivation history and historical
validation evidence are retained; skipped-missing optional validation remains
neither pass nor failure, and issues `#6` through `#11` stay open.

## Future gates

- `OSW-EXP-089_OPTIONAL_SOLVER_PLUGIN_MANIFEST_REACTIVATION_GUI_IMPLEMENTATION`
- `OSW-EXP-090_OPTIONAL_SOLVER_PLUGIN_MANIFEST_STATE_PERSISTENCE_DESIGN`
- `OSW-EXP-091_OPTIONAL_SOLVER_PLUGIN_MANIFEST_STATE_EXPORT_SUMMARY_DESIGN`
- `OSW-VALID` prepared-machine validation reuse
