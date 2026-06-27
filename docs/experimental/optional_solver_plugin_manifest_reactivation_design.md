# Optional solver plugin manifest reactivation design

## Status

Design-only.

No runtime behavior is added in this gate. This document defines the future
safety contract, UX flow, state model, diagnostics, acknowledgement
requirements, evidence-retention policy, and follow-up gates for optional solver
plugin manifest reactivation. It is not implementation authorization and does not
read as one.

Status boundaries:

- no runtime behavior added
- no runtime source behavior added
- no reactivation implementation
- no reactivation persistence
- no GUI reactivation behavior
- no CLI reactivation
- no activation source mutation
- no deactivation source mutation
- no automatic activation
- no trust restoration
- no file restoration
- no file rewrite
- no file deletion
- no dependency installation
- no dependency uninstall
- no solver uninstall
- no plugin package import
- no directory scan
- no network fetch
- no discovery execution
- no validation execution
- no solver execution
- no issue mutation
- no issue closure
- no release mutation
- no tag mutation
- no asset mutation
- no version bump
- no validation-pass claim
- no validation-fail claim
- no certification claim

## Purpose

Define future reactivation semantics for deactivated optional solver plugin
manifest candidates, while preserving the existing activation, deactivation, and
discovery-refresh boundaries.

The purpose is to:

- define what reactivation means and what reactivation does not mean
- preserve the OSW-EXP-079/080 activation boundaries
- preserve the OSW-EXP-081/085/086 deactivation boundaries
- preserve the OSW-EXP-082/083/084 discovery-refresh boundaries
- make reactivation distinct from validation, trust restoration, file
  restoration, dependency install/uninstall, discovery, issue closure, release
  mutation, and certification

Reactivation is not validation. Reactivation is not trust restoration.
Reactivation is not file restoration. Reactivation is not automatic activation.
Reactivation is not dependency installation. Reactivation is not solver
execution. Reactivation is not issue closure. Reactivation is not release
mutation. Reactivation is not certification.

## Current state before reactivation

- OSW-EXP-078 added the activation design.
- OSW-EXP-079 added the pure activation view-model.
- OSW-EXP-080 added the view-model-driven activation GUI surface.
- OSW-EXP-081 added the design-only deactivation contract.
- OSW-EXP-085 added the pure deactivation view-model extension (which already
  represents `deactivated`, `reactivation_requested`, and
  `future_reactivation_required` states).
- OSW-EXP-086 added the view-model-driven deactivation GUI surface.
- OSW-EXP-082 through OSW-EXP-084 added the discovery-refresh integration design,
  pure view-model, and GUI surface.
- Activation, deactivation, and discovery-refresh surfaces remain non-persistent
  and non-executing.
- User-selected and plugin-provided manifests remain untrusted and
  non-validating.

Issues `#6` through `#11` remain open. Package metadata remains `0.1.5rc1`. The
public prerelease remains `v0.1.5-rc1`.

## Definition of reactivation

Reactivation is a future explicit user action that asks OSW to reconsider a
deactivated plugin manifest candidate for the activation path again.

Reactivation may eventually mean:

- the candidate leaves a deactivated-only review state and enters a
  `reactivation_requested` state
- the candidate is routed back through activation acknowledgement/review
  requirements
- the candidate may become `reactivation_ready` or `future_activation_required`
- the candidate can appear in future summaries as reactivation-requested or
  reactivation-ready
- deactivation history remains visible

## What reactivation does not mean

Reactivation must not mean:

- automatic activation
- trusted-by-default status
- trust restoration
- validation success
- validation failure reversal
- dependency installation
- dependency uninstall
- solver uninstall
- solver execution
- plugin package import
- restoring or rewriting manifest files
- deleting manifest files
- closing issues
- editing releases, tags, or assets
- deleting historical evidence
- deleting deactivation history
- certification

## Reactivation preconditions

Future preconditions before reactivation may be allowed:

- explicit user action (never automatic)
- the candidate is currently `deactivated` or marked `future_reactivation_required`
- the candidate provenance is visible
- the trust label is visible
- deactivation history is retained and visible
- the user acknowledges reactivation is not validation
- the user acknowledges reactivation is not trust restoration
- the user acknowledges reactivation is not dependency install
- the user acknowledges reactivation is not solver execution
- the user acknowledges reactivation is not issue closure
- the user acknowledges reactivation is not release mutation
- conflicts and shared-stack warnings are visible
- stale or missing source references require re-preview or future explicit policy
  rather than silent activation
- unsafe claims are visible and blocked or explicitly handled by future policy

If any precondition is unmet, reactivation is blocked (see the state machine).

## User acknowledgement model

Future reactivation requires explicit acknowledgements before it can proceed:

- `reactivation_not_validation`
- `reactivation_not_trust_restoration`
- `reactivation_not_install`
- `reactivation_no_solver_execution`
- `reactivation_not_issue_closure`
- `reactivation_not_release_mutation`
- `reactivation_history_retained`
- `reactivation_requires_activation_review`
- `untrusted_source`
- `conflict_or_shared_stack_warning` (when conflicts or shared stack ids exist)
- `stale_source_requires_repreview` (when the source reference is stale/missing)
- `no_discovery_execution`
- `no_plugin_package_import`
- `trust_label_not_certification`

Acknowledgements are recorded as future in-memory state only. They do not grant
trust-by-default and do not constitute validation evidence.

## Source/trust/provenance model

Future labels:

- `source_type`: `built_in`, `user_selected_json_file`, `plugin_provided_manifest`,
  `future_imported_manifest`, `future_persisted_activation`
- `trust_label`: `built_in`, `untrusted_user_file`, `untrusted_plugin_manifest`,
  `future_trusted_by_user`
- `activation_state`: `inactive_preview`, `activation_ready`, `active_candidate`,
  `deactivated`, `reactivation_requested`, `reactivation_blocked`,
  `reactivation_ready`, `future_activation_required`, `reactivation_error`

Rules:

- the source reference must be redacted by default
- a trust label is not certification
- a reactivation state is not validation evidence
- user-selected and plugin-provided manifests are untrusted by default
- deactivation history is retained

## Reactivation state machine

Future reactivation state machine:

- `deactivated`
- `reactivation_requested`
- `reactivation_blocked`
- `reactivation_ready`
- `future_activation_required`
- `active_candidate_future_gate`
- `reactivation_error`

Allowed transitions:

- `deactivated` -> `reactivation_requested` (explicit user request)
- `reactivation_requested` -> `reactivation_blocked` (precondition unmet, missing
  acknowledgement, unresolved conflict/shared-stack warning, stale source, or
  unsafe claim)
- `reactivation_requested` -> `reactivation_ready` (all preconditions and
  acknowledgements satisfied)
- `reactivation_ready` -> `future_activation_required` (routes back through future
  activation review)
- `future_activation_required` -> `active_candidate_future_gate` (only via a
  future activation/persistence gate)
- any state -> `reactivation_error` (unexpected future runtime error)

Blocked transitions:

- `inactive_preview` -> reactivated directly
- `deactivated` -> `active_candidate` directly without review and acknowledgements
- `reactivation_*` -> discovery execution
- `reactivation_*` -> validation execution
- `reactivation_*` -> dependency installation
- `reactivation_*` -> dependency uninstall
- `reactivation_*` -> solver uninstall
- `reactivation_*` -> solver execution
- `reactivation_*` -> issue closure
- `reactivation_*` -> release mutation
- `reactivation_*` -> certification claim

## Conflict and shared-stack policy

Future reactivation must handle:

- built-in candidate conflicts
- user/plugin candidates with duplicate stack ids
- one source active while another remains deactivated

Rules:

- reactivating a user/plugin source must not override built-ins silently
- the built-ins-win policy must remain visible
- reactivation must not silently hide conflicts
- conflicting candidates should route to `reactivation_blocked` or
  `future_activation_required` until a future policy resolves them

## Stale source and re-preview policy

- Reactivation must not silently trust old preview data.
- Missing, moved, or changed manifest sources must require re-preview or a future
  explicit policy.
- Reactivation must not read files in this design gate.
- Future implementation may model stale-source diagnostics without performing
  file IO.
- Reactivation must not restore, rewrite, or delete manifest files.
- If stale-source re-preview is required, it must be a separate future explicit
  user action through the explicit import preview boundary.

## Validation and evidence policy

- Reactivation is not validation success.
- Reactivation is not validation failure reversal.
- Reactivation does not delete or rewrite historical validation evidence.
- Deactivation history remains visible.
- Skipped-missing remains skipped-missing.
- Reactivation must not close live validation issues.
- Prepared-machine validation remains a separate gate.

A reactivation-ready candidate is not a validation pass; it is simply a
deactivated candidate routed back toward future activation review.

## Relationship to activation view-model and GUI

- Reactivation routes back through future activation review.
- The activation GUI remains view-model driven and non-persistent.
- This gate adds no activation GUI buttons, callbacks, persistence, or source
  mutation.
- Reactivation-ready is not active-candidate persistence.

## Relationship to deactivation view-model and GUI

- OSW-EXP-085/086 already display `deactivated` and future-reactivation states
  where supplied.
- This design may refine future reactivation semantics but must not change the
  deactivation view-model or GUI source.
- A future reactivation view-model extension gate may add reactivation-specific
  rows, acknowledgements, diagnostics, or transition plans.

## Relationship to discovery-refresh view-model and GUI

- Reactivation is not discovery refresh.
- Reactivation must not automatically include candidates in discovery inputs.
- Discovery-refresh integration using reactivated candidates remains a future
  separate gate.
- Deactivated candidates remain excluded or inactive until a future gate changes
  supplied state.

## Relationship to explicit import GUI

- File loading and preview do not imply activation, deactivation, or
  reactivation.
- Reactivation must not delete or rewrite imported JSON files.
- Reactivation must not bypass explicit import preview boundaries.
- If stale-source re-preview is required, it must be a separate future explicit
  user action.

## Relationship to optional solver health panel and passive discovery

- Reactivation is not health validation.
- Reactivation must not automatically run passive discovery.
- The health panel must show reactivation-related states as non-validating.
- Missing optional stacks remain skipped-missing, not pass.

## Relationship to CLI

- No CLI behavior change in this gate.
- No CLI reactivation command.
- A future CLI reactivation design would require a separate gate.

## Relationship to export summary

- Future redacted export summaries may include reactivation state and retained
  deactivation history.
- Sensitive local paths must stay redacted by default.
- Reactivation state is not validation evidence.
- No export behavior is implemented in this gate.

## Relationship to live optional validation issues

- Issues `#6` through `#11` remain open.
- Reactivation is not live optional validation.
- Reactivation-ready or future-activation-required state must not mark issues
  ready to close.
- Skipped-missing remains skipped-missing.
- Prepared-machine validation remains a separate gate.

## Diagnostics reserved for future reactivation

Reserved design-only diagnostic code names (not implemented in this gate):

- `OSPMG_REACTIVATION_DEACTIVATED_REQUIRED`
- `OSPMG_REACTIVATION_ACK_REQUIRED`
- `OSPMG_REACTIVATION_UNTRUSTED_SOURCE`
- `OSPMG_REACTIVATION_NOT_TRUST_RESTORE`
- `OSPMG_REACTIVATION_NOT_VALIDATION`
- `OSPMG_REACTIVATION_NO_INSTALL`
- `OSPMG_REACTIVATION_NO_SOLVER_EXECUTION`
- `OSPMG_REACTIVATION_NOT_ISSUE_CLOSURE`
- `OSPMG_REACTIVATION_NOT_RELEASE_MUTATION`
- `OSPMG_REACTIVATION_NOT_CERTIFICATION`
- `OSPMG_REACTIVATION_HISTORY_RETAINED`
- `OSPMG_REACTIVATION_REVIEW_REQUIRED`
- `OSPMG_REACTIVATION_CONFLICT_BLOCKED`
- `OSPMG_REACTIVATION_SHARED_STACK_WARNING`
- `OSPMG_REACTIVATION_STALE_SOURCE_REPREVIEW_REQUIRED`
- `OSPMG_REACTIVATION_UNSAFE_CLAIM`
- `OSPMG_REACTIVATION_NO_DISCOVERY_EXECUTION`
- `OSPMG_REACTIVATION_NO_PLUGIN_IMPORT`
- `OSPMG_REACTIVATION_PERSISTENCE_NOT_IMPLEMENTED`
- `OSPMG_REACTIVATION_FUTURE_GATE`

These names are reservations only. No diagnostic emitter, runtime constant, or
GUI handler is added in this gate.

## Future implementation test plan

A later implementation gate must add tests that verify:

- reactivation is unavailable before deactivation
- reactivation requires explicit acknowledgement
- reactivation does not imply validation success
- reactivation does not imply trust restoration
- reactivation does not install dependencies
- reactivation does not uninstall dependencies or solvers
- reactivation does not execute solvers
- reactivation does not run discovery
- reactivation does not close issues
- reactivation does not mutate releases, tags, or assets
- reactivation preserves deactivation history
- reactivation preserves historical validation evidence
- stale source requires re-preview or explicit future policy
- the built-ins-win / shared-stack policy remains visible
- unsafe claims block or warn
- source references are redacted
- a trust label is not certification
- skipped-missing remains skipped-missing
- no trusted-by-default behavior is introduced

These are future tests. This gate adds only a focused docs test for this design
document and the related guardrail/risk/checklist/validation references.

## Non-actions

This gate explicitly does not:

- implement reactivation
- implement reactivation persistence
- implement GUI reactivation button behavior
- implement CLI reactivation
- alter activation view-model source
- alter activation GUI source
- alter deactivation view-model source
- alter deactivation GUI source
- alter discovery-refresh view-model or GUI source
- restore, rewrite, or delete manifest files
- install dependencies
- uninstall dependencies
- uninstall solvers
- import plugin packages
- scan directories
- fetch network manifests
- run discovery
- run validation
- execute solvers
- mutate issues
- mutate releases
- create, move, delete, or push tags
- build or upload assets
- bump versions
- claim validation success
- claim validation failure reversal
- claim issue closure
- claim bundled solvers
- claim certification

No runtime source, GUI source, view-model source, CLI source, loader source,
discovery source, or plugin manager source is changed in this gate. This design
adds no validation-pass claim, no validation-fail claim, no issue-closure claim,
no bundled-solver claim, and no certification claim. User-selected and
plugin-provided manifests remain untrusted; built-ins remain authoritative;
deactivation history and historical validation evidence are retained;
skipped-missing optional validation remains neither pass nor failure, and issues
`#6` through `#11` stay open.

## Future gates

Proposed follow-up candidates, not implemented here:

- `OSW-EXP-088_OPTIONAL_SOLVER_PLUGIN_MANIFEST_REACTIVATION_VIEWMODEL_EXTENSION`
- `OSW-EXP-089_OPTIONAL_SOLVER_PLUGIN_MANIFEST_REACTIVATION_GUI_IMPLEMENTATION`
- `OSW-EXP-090_OPTIONAL_SOLVER_PLUGIN_MANIFEST_STATE_PERSISTENCE_DESIGN`
- `OSW-EXP-091_OPTIONAL_SOLVER_PLUGIN_MANIFEST_STATE_EXPORT_SUMMARY_DESIGN`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` (only if a
  prepared machine is available)

Numbering note: this continues the established activation/deactivation cadence
(OSW-EXP-081 deactivation design -> OSW-EXP-085 deactivation view-model ->
OSW-EXP-086 deactivation GUI). Reactivation follows the same shape: this design
(087) is followed by its own view-model extension (088) and GUI (089), with
state-persistence and export-summary designs (090, 091) as later, separately
gated steps. If the repo later re-reserves a different sequence, follow the
repo's latest convention and update this mapping. Persistence, discovery
integration, validation, install/uninstall, solver execution, and any live
validation remain separate, later gates regardless of numbering.

## View-model extension follow-up

OSW-EXP-088 implements the pure reactivation view-model extension only:
[Optional solver plugin manifest reactivation view-model](optional_solver_plugin_manifest_reactivation_viewmodel.md)
(`src/osw/experimental/optional_solvers/plugin_manifest_reactivation_viewmodel.py`).
It realizes the classification/record layer of this design — reactivation
readiness, acknowledgements, diagnostics, shared-stack warnings,
stale-source/re-preview rows, deactivation-history and evidence retention, trust
badges, and disabled/future action states — and stays pure and non-mutating.
Reactivation persistence, GUI button behavior, CLI behavior, source mutation,
discovery integration, validation, install/uninstall, solver execution, issue
closure, and release mutation remain future-gated.

OSW-EXP-089 implements a view-model-driven PySide GUI surface over that
view-model:
[Optional solver plugin manifest reactivation GUI implementation](optional_solver_plugin_manifest_reactivation_gui_implementation.md)
(`src/osw/gui/dialogs/optional_solver_plugin_manifest_reactivation_panel.py`). The
panel renders reactivation readiness, candidates, acknowledgements, diagnostics,
shared-stack warnings, stale-source/re-preview rows, deactivation-history and
evidence retention, trust/provenance, and disabled/future actions only; it
implements no runtime reactivation, persistence, automatic activation, trust
restoration, file mutation, install/uninstall, discovery, validation, or solver
execution. Reactivation persistence and source mutation remain future, separate
gates.
