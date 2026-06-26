# Optional solver plugin manifest deactivation design

## Status

Design-only.

No runtime behavior is added in this gate. This document defines the future
safety contract, UX flow, state model, diagnostics, acknowledgement
requirements, and follow-up gates for optional solver plugin manifest
deactivation. It is not implementation authorization and does not read as one.

Status boundaries:

- no runtime source behavior added
- no deactivation implementation
- no deactivation persistence
- no GUI deactivation behavior
- no CLI deactivation behavior
- no file deletion
- no dependency uninstall
- no solver uninstall
- no plugin package import
- no directory scan
- no network fetch
- no discovery execution
- no validation execution
- no solver execution
- no dependency installation
- no issue mutation
- no release mutation
- no tag mutation
- no asset mutation
- no version bump
- no validation-pass claim
- no certification claim

## Purpose

Define future deactivation semantics for active optional solver plugin manifest
candidates, while preserving the existing activation GUI and view-model
boundaries.

The purpose is to:

- define what deactivation means and what deactivation does not mean
- preserve the OSW-EXP-079 view-model and OSW-EXP-080 GUI boundaries
- make deactivation distinct from deletion, uninstall, validation, discovery,
  issue closure, release mutation, and certification

Deactivation is not deletion. Deactivation is not uninstall. Deactivation is not
validation. Deactivation is not issue closure. Deactivation is not release
mutation. Deactivation is not solver execution.

## Current state before deactivation

- OSW-EXP-078 added the activation design.
- OSW-EXP-079 added the pure activation view-model (which already represents a
  `deactivated` state).
- OSW-EXP-080 added the view-model-driven activation GUI surface.
- Activation remains non-persistent and non-executing.
- User-selected and plugin-provided manifests remain untrusted and
  non-validating.

Issues `#6` through `#11` remain open. Package metadata remains `0.1.5rc1`. The
public prerelease remains `v0.1.5-rc1`.

## Definition of deactivation

Deactivation is a future explicit user action that marks an active plugin
manifest candidate as no longer active for future optional solver manifest UX
surfaces.

Deactivation may eventually mean:

- the candidate is excluded from future activated-candidate lists
- the candidate appears with a `deactivated` state
- the candidate can be omitted from future discovery-refresh candidate sets,
  only if a later gate enables that
- the candidate can appear in redacted summaries as deactivated history, only if
  a later gate enables that

Deactivation must not mean:

- deleting the original manifest JSON file
- uninstalling a solver
- uninstalling a dependency
- deleting plugin packages
- mutating plugin manager state without a future persistence gate
- closing issues
- editing releases or tags
- removing historical validation evidence
- claiming validation failure or success
- certification
- solver execution

## Deactivation preconditions

Future preconditions before deactivation may be allowed:

- explicit user action (never automatic)
- the candidate is currently active (or activation-ready, depending on future
  policy)
- the candidate provenance is visible
- the trust label is visible
- the user acknowledges deactivation is not file deletion
- the user acknowledges deactivation is not uninstall
- the user acknowledges deactivation is not issue closure
- the user acknowledges deactivation is not release mutation
- the user acknowledges validation evidence is not silently deleted
- unresolved pending activation/discovery operations are absent or blocked

If any precondition is unmet, deactivation is blocked (see the state machine).

## User acknowledgement model

Future deactivation requires explicit acknowledgements before it can proceed:

- `not_file_deletion`
- `not_dependency_uninstall`
- `not_solver_uninstall`
- `not_issue_closure`
- `not_release_mutation`
- `not_validation_evidence_deletion`
- `no_discovery_execution`
- `no_solver_execution`
- `deactivation_history_visible`
- `conflict_or_shared_stack_warning` (when conflicts or shared stack ids exist)

Acknowledgements are recorded as future in-memory state only. They do not grant
trust-by-default and do not constitute validation evidence.

## Source/trust/provenance model

Future labels:

- `source_type`: `built_in`, `user_selected_json_file`, `plugin_provided_manifest`,
  `future_imported_manifest`
- `trust_label`: `built_in`, `untrusted_user_file`, `untrusted_plugin_manifest`,
  `future_trusted_by_user`
- `activation_state`: `inactive_preview`, `activation_ready`, `active_candidate`,
  `deactivation_requested`, `deactivated`, `deactivation_blocked`,
  `deactivation_error`

Rules:

- the source reference must be redacted by default
- a trust label is not certification
- a deactivated state is not validation evidence
- user-selected and plugin-provided manifests are untrusted by default

## Deactivation state machine

Future deactivation state machine:

- `active_candidate`
- `deactivation_requested`
- `deactivation_blocked`
- `deactivated`
- `deactivation_error`
- `reactivation_requested` (future-only; reactivation is a later gate)

Allowed transitions:

- `active_candidate` -> `deactivation_requested` (explicit user request)
- `deactivation_requested` -> `deactivation_blocked` (precondition unmet, missing
  acknowledgement, or unresolved conflict/shared-stack warning)
- `deactivation_requested` -> `deactivated` (all preconditions and
  acknowledgements satisfied)
- `deactivated` -> `reactivation_requested` (future reactivation gate only)
- any state -> `deactivation_error` (unexpected future runtime error)

Blocked transitions:

- `inactive_preview` -> `deactivated` directly without active-candidate context
- `deactivation_*` -> discovery execution
- `deactivation_*` -> validation execution
- `deactivation_*` -> dependency uninstall
- `deactivation_*` -> solver execution
- `deactivation_*` -> issue closure
- `deactivation_*` -> release mutation

## Conflict and shared-stack policy

Future deactivation must handle:

- built-in candidate conflicts
- user/plugin candidates with duplicate stack ids
- one source active while another source remains preview-only

Rules:

- deactivating a user/plugin source must not deactivate built-ins silently
- the built-ins-win policy must remain visible
- deactivation must not silently hide conflicts
- shared-stack situations must surface a warning before deactivation

## Validation and evidence policy

- Deactivation must not delete or rewrite validation evidence.
- Deactivation must not convert skipped-missing into pass or fail.
- Deactivation must not close live validation issues.
- Deactivation must not claim solver capability changed.
- Historical evidence should stay reportable if a future persistence/export gate
  supports it.

A deactivated candidate is not a validation failure; it is simply non-active.

## Relationship to activation GUI

- The activation GUI remains view-model driven.
- Deactivation must be a separate future action/state from activation review.
- Displaying the `deactivated` state is allowed only when supplied by the
  view-model.
- This gate adds no buttons, callbacks, persistence, or state mutation.

## Relationship to activation view-model

- OSW-EXP-079 already includes a `deactivated` state representation.
- This design may refine future deactivation semantics but must not change the
  view-model source.
- A future view-model extension gate may add deactivation-specific rows,
  acknowledgements, diagnostics, or transition plans.

## Relationship to explicit import GUI

- File loading and preview do not imply activation.
- Activation does not imply deactivation.
- Deactivation must not delete imported JSON files.
- Deactivation must not change explicit import preview history unless a future
  persistence/export gate defines it.

## Relationship to optional solver health panel and discovery refresh

- Deactivation is not health validation.
- Deactivation must not automatically run passive discovery.
- Discovery refresh using active/deactivated state remains a future separate
  gate.
- The health panel must show deactivated candidates as non-active, not as
  validation failures.

## Relationship to CLI

- No CLI behavior change in this gate.
- No CLI deactivation command.
- A future CLI deactivation design would require a separate gate.

## Relationship to export summary

- Future redacted export summaries may include deactivation state.
- Sensitive local paths must stay redacted by default.
- Deactivation state is not validation evidence.
- No export behavior is implemented in this gate.

## Diagnostics reserved for future deactivation

Reserved design-only diagnostic code names (not implemented in this gate):

- `OSPMG_DEACTIVATION_ACTIVE_REQUIRED`
- `OSPMG_DEACTIVATION_ACK_REQUIRED`
- `OSPMG_DEACTIVATION_NOT_FILE_DELETE`
- `OSPMG_DEACTIVATION_NOT_UNINSTALL`
- `OSPMG_DEACTIVATION_NOT_VALIDATION`
- `OSPMG_DEACTIVATION_NO_DISCOVERY_EXECUTION`
- `OSPMG_DEACTIVATION_NO_SOLVER_EXECUTION`
- `OSPMG_DEACTIVATION_NOT_ISSUE_CLOSURE`
- `OSPMG_DEACTIVATION_NOT_RELEASE_MUTATION`
- `OSPMG_DEACTIVATION_EVIDENCE_RETAINED`
- `OSPMG_DEACTIVATION_SHARED_STACK_WARNING`
- `OSPMG_DEACTIVATION_STATE_CONFLICT`
- `OSPMG_DEACTIVATION_PERSISTENCE_NOT_IMPLEMENTED`
- `OSPMG_DEACTIVATION_DEACTIVATED`

These names are reservations only. No diagnostic emitter, runtime constant, or
GUI handler is added in this gate.

## Future implementation test plan

A later implementation gate must add tests that verify:

- deactivation is unavailable before activation
- deactivation requires explicit acknowledgement
- deactivation does not delete files
- deactivation does not uninstall dependencies
- deactivation does not run discovery
- deactivation does not run validation
- deactivation does not execute solvers
- deactivation does not close issues
- deactivation does not mutate releases, tags, or assets
- deactivation preserves provenance and redaction
- deactivation preserves historical validation evidence
- the deactivated state renders distinctly from a validation failure
- the shared-stack / built-ins-win policy remains visible
- no trusted-by-default behavior is introduced

These are future tests. This gate adds only a focused docs test for this design
document and the related guardrail/risk/checklist/validation references.

## Non-actions

This gate explicitly does not:

- implement deactivation
- implement deactivation persistence
- implement deactivation GUI button behavior
- implement CLI deactivation
- alter activation view-model source
- alter activation GUI source
- delete manifest files
- uninstall dependencies
- uninstall solvers
- import plugin packages
- scan directories
- fetch network manifests
- run discovery
- run validation
- install dependencies
- execute solvers
- mutate issues
- mutate releases
- create, move, delete, or push tags
- build or upload assets
- bump versions
- claim validation success
- claim issue closure
- claim bundled solvers
- claim certification

No runtime source, GUI source, view-model source, CLI source, loader source,
discovery source, or plugin manager source is changed in this gate. This design
adds no validation-pass claim, no issue-closure claim, no bundled-solver claim,
and no certification claim. User-selected and plugin-provided manifests remain
untrusted; skipped-missing optional validation remains neither pass nor failure,
and issues `#6` through `#11` stay open.

## Discovery-refresh integration follow-up

[Optional solver plugin manifest discovery refresh integration design](optional_solver_plugin_manifest_discovery_refresh_integration_design.md)
(OSW-EXP-082) defines the future, design-only contract for letting
activated/deactivated candidates affect optional solver discovery refresh.
Deactivated candidates are excluded or shown inactive; the integration remains
explicit, provenance-preserving, non-validating, non-installing, and
non-executing, and adds no runtime discovery behavior.

## Future gates

Proposed follow-up candidates, not implemented here:

- `OSW-EXP-082_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DISCOVERY_REFRESH_INTEGRATION_DESIGN`
- `OSW-EXP-083_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DEACTIVATION_VIEWMODEL_EXTENSION`
  (only if deactivation-specific state beyond OSW-EXP-079 is needed)
- `OSW-EXP-084_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DEACTIVATION_GUI_IMPLEMENTATION`
  (only if a separate GUI action is approved)
- `OSW-EXP-085_OPTIONAL_SOLVER_PLUGIN_MANIFEST_REACTIVATION_DESIGN`
  (only if reactivation is needed)
- `OSW-VALID` prepared-machine validation reuse

Numbering note: this continues the established activation cadence
(OSW-EXP-078 design -> OSW-EXP-079 view-model -> OSW-EXP-080 GUI). The next
recommended gate is the discovery-refresh integration design (OSW-EXP-082);
deactivation view-model extension, deactivation GUI, and reactivation are
later, optional, separately gated steps. If the repo later re-reserves a
different sequence, follow the repo's latest convention and update this mapping.
Persistence, discovery integration, validation, install/uninstall, solver
execution, and any live validation remain separate, later gates regardless of
numbering.
