# Optional solver plugin manifest state persistence design

## Status

Design-only.

No runtime behavior is added in this gate. This document defines the future
safety contract, UX flow, storage model, schema boundaries, redaction policy,
acknowledgement policy, migration policy, diagnostics, and follow-up gates for
optional solver plugin manifest state persistence. It is not implementation
authorization and does not read as one.

Status boundaries:

- no runtime behavior added
- no runtime source behavior added
- no persistence implementation
- no file writes
- no settings file creation
- no project schema mutation
- no GUI persistence behavior
- no CLI persistence behavior
- no activation/deactivation/reactivation/discovery-refresh source mutation
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

OSW-EXP-092 implementation follow-up: OSW-EXP-092 implements the pure
persistence view-model only, while file writes, settings files, ProjectSchema
mutation, GUI persistence behavior, CLI persistence behavior, reload behavior,
export summary behavior, discovery integration, validation, install/uninstall,
solver execution, issue closure, and release mutation remain future-gated.

## Purpose

Define future persistence semantics for optional solver plugin manifest UX state,
while preserving the activation, deactivation, reactivation, discovery-refresh,
and explicit-import safety boundaries.

The purpose is to:

- define what optional solver plugin manifest state is eligible for future
  persistence and what is forbidden
- preserve the OSW-EXP-079/080 activation boundaries
- preserve the OSW-EXP-081/085/086 deactivation boundaries
- preserve the OSW-EXP-087/088/089 reactivation boundaries
- preserve the OSW-EXP-082/083/084 discovery-refresh boundaries
- make persistence distinct from validation, trust restoration, plugin
  installation, solver installation, solver execution, issue closure, release
  mutation, and certification

Persisted state is not validation evidence. Persisted state is not trust
restoration. Persisted state is not automatic activation. Persisted state is not
dependency installation. Persisted state is not solver execution. Persisted state
is not issue closure. Persisted state is not release mutation. Persisted state is
not certification.

## Current state before persistence

- The explicit import GUI exists (OSW-EXP-077) but does not persist state.
- Activation design/view-model/GUI exist (OSW-EXP-078/079/080).
- Deactivation design/view-model/GUI exist (OSW-EXP-081/085/086).
- Reactivation design/view-model/GUI exist (OSW-EXP-087/088/089).
- Discovery-refresh design/view-model/GUI exist (OSW-EXP-082/083/084).
- All current surfaces remain non-persistent, non-installing, non-validating,
  non-executing, and issue/release-safe.
- User-selected and plugin-provided manifests remain untrusted and non-validating.

Issues `#6` through `#11` remain open. Package metadata remains `0.1.5rc1`. The
public prerelease remains `v0.1.5-rc1`.

## Definition of persisted manifest state

Persisted manifest state is a future local, explicit, versioned record of
user-facing optional solver plugin manifest UX state that can be reloaded later.

Persisted manifest state may eventually include:

- redacted manifest source references
- source fingerprint or source identity metadata if a future gate defines it
- preview status
- activation state
- deactivation state
- reactivation state
- acknowledgement satisfaction state
- stale-source/re-preview requirement state
- deactivation history
- reactivation history
- discovery-refresh inclusion/exclusion preferences
- unsafe-claim diagnostics
- conflict/shared-stack diagnostics
- evidence-retention references
- schema version and migration metadata

## What persisted state must not include

Persisted manifest state must not include:

- raw secret paths when redaction is required
- plugin code
- plugin package imports
- solver binaries
- dependency install instructions as executable actions
- validation-pass claims
- issue-closure readiness claims
- certification claims
- release/tag/asset mutation commands
- arbitrary executable scripts
- unrestricted external URLs

## Storage location options

Future options, discussed without choosing an implementation:

- project-local state file
- user profile/cache state file
- explicit export/import state bundle
- in-memory session-only model
- redacted report/export summary

Tradeoffs:

- project-local improves portability but can leak local paths if careless
- user-profile state improves privacy but is harder to share
- export summary is review-friendly but may not be reloadable
- session-only is safest but not persistent

A future gate selects a storage model; this design gate selects none and writes
nothing.

## Persistence preconditions

Future preconditions before persistence may be allowed:

- explicit user action (never automatic)
- visible source/provenance labels
- visible trust label
- visible redaction preview
- visible non-validation warning
- visible non-install/non-execution warning
- visible stale-source/re-preview policy
- visible acknowledgement invalidation policy
- schema version available
- write target explicitly chosen or approved by future policy
- no live discovery/validation/solver execution required

## User acknowledgement model

Future persistence requires explicit acknowledgements before it can proceed:

- `persistence_not_validation`
- `persistence_not_trust_restoration`
- `persistence_not_install`
- `persistence_no_solver_execution`
- `persistence_not_issue_closure`
- `persistence_not_release_mutation`
- `local_path_redaction_reviewed`
- `persisted_acknowledgements_may_expire`
- `stale_source_requires_repreview`
- `untrusted_source_remains_untrusted`
- `activation_review_required_after_reload`
- `no_discovery_execution`
- `no_plugin_package_import`
- `trust_label_not_certification`

Acknowledgements are recorded as future in-memory state only. They do not grant
trust-by-default and do not constitute validation evidence.

## Acknowledgement persistence and invalidation policy

Define:

- which acknowledgements may be persisted (the non-validation/non-install/
  non-execution/redaction-reviewed safety acknowledgements may be persisted as
  records of what the user saw)
- which acknowledgements must expire on reload (any acknowledgement that grants
  forward action, e.g. activation-review or stale-source acceptance)
- which acknowledgements must expire when the source fingerprint changes
- which acknowledgements must expire when the schema version changes
- which acknowledgements must expire when unsafe claims appear

Persisted acknowledgement is not validation evidence. Persisted acknowledgement
does not imply trust restoration. Persisted acknowledgement does not imply issue
closure. A reloaded acknowledgement is a record that a warning was shown, not a
grant of forward permission.

## Source/trust/provenance model

Future labels:

- `source_type`: `built_in`, `user_selected_json_file`, `plugin_provided_manifest`,
  `future_imported_manifest`, `future_persisted_state`, `future_state_bundle`
- `trust_label`: `built_in`, `untrusted_user_file`, `untrusted_plugin_manifest`,
  `future_trusted_by_user`
- `persisted_state_kind`: `session_only`, `project_local`, `user_profile`,
  `exported_summary`, `imported_state_bundle`

Rules:

- the source reference must be redacted by default
- a trust label is not certification
- persisted state is not validation evidence
- persisted state is not trust restoration
- user-selected and plugin-provided manifests are untrusted by default

## Redaction and privacy policy

- Raw absolute paths are not shown by default.
- Source references use basename, hash, or caller-supplied display names where
  possible.
- The user must review any unredacted path before export.
- No secrets, tokens, or API keys in persisted state.
- No environment variables or home-directory paths unless explicitly allowed by a
  future gate.
- Persisted diagnostics should be useful without leaking private paths.

## State schema model

Conceptual top-level fields (not implemented; no schema file is created):

- `schema_version`
- `created_by_osw_version`
- `created_at`
- `state_scope`
- `manifest_sources`
- `candidates`
- `acknowledgements`
- `diagnostics`
- `conflicts`
- `unsafe_claims`
- `activation_state`
- `deactivation_state`
- `reactivation_state`
- `discovery_refresh_state`
- `evidence_history`
- `redaction_policy`
- `migration_notes`
- `non_action_flags`

This is a conceptual model only. This gate creates no schema file and performs no
file writes.

## State machine interaction

Persisted state may interact conceptually with: `inactive_preview`,
`activation_ready`, `active_candidate`, `deactivated`, `reactivation_requested`,
`reactivation_ready`, `future_activation_required`, discovery-refresh
included/excluded states, and stale-source/re-preview required states.

Blocked transitions:

- persisted state directly to active candidate without review
- persisted state directly to trusted source
- persisted state directly to discovery execution
- persisted state directly to validation execution
- persisted state directly to dependency install
- persisted state directly to solver execution
- persisted state directly to issue closure
- persisted state directly to release mutation
- persisted state directly to certification claim

## Stale-source and re-preview policy

- Reloaded state must not silently trust old preview data.
- Missing, moved, or changed sources must require re-preview or a future explicit
  policy.
- A future implementation may compare fingerprints, mtimes, user-supplied source
  IDs, or content hashes only if a separate gate defines it.
- This design gate does no file IO.
- Persistence must not restore, rewrite, or delete manifest files.

## Conflict and shared-stack policy

- Built-ins win by default.
- Persisted user/plugin state must not override built-ins silently.
- Duplicate stack ids must remain visible after reload.
- Deactivated/reactivated state must not hide conflicts.
- Conflicts should route to blocked or review-required states until a future
  policy resolves them.

## Unsafe claim policy

Persisted state must not convert unsafe claims into accepted claims. Unsafe claims
include:

- bundled solver binaries
- automatic dependency install
- validation success
- validation failure reversal
- issue closure readiness
- industrial certification
- proprietary solver parity
- full OpenFOAM/ANSYS/MATLAB/Abaqus replacement
- solver execution during discovery/persistence/reload

## Validation and evidence policy

- Persisted state is not validation success.
- Persisted state is not validation failure.
- Persisted state does not delete or rewrite historical evidence.
- Skipped-missing remains skipped-missing.
- Persisted state must not close live validation issues.
- Prepared-machine validation remains a separate gate.
- Evidence references must preserve limitations and diagnostics.

## Relationship to activation view-model and GUI

- Activation state may be represented conceptually.
- Reloaded activation-ready state must still require visible review.
- This gate does not alter activation view-model or GUI source.
- Persistence must not silently activate candidates.

## Relationship to deactivation view-model and GUI

- Deactivation state and history may be represented conceptually.
- Persisted deactivation state is not file deletion or uninstall.
- This gate does not alter deactivation view-model or GUI source.
- Persistence must preserve evidence history and deactivation history.

## Relationship to reactivation view-model and GUI

- Reactivation state may be represented conceptually.
- Persisted reactivation-ready state is not automatic activation.
- Persisted reactivation-ready state is not trust restoration.
- This gate does not alter reactivation view-model or GUI source.
- Reloaded reactivation candidates must route through future activation review.

## Relationship to discovery-refresh view-model and GUI

- Persisted discovery-refresh preferences are not discovery execution.
- Reloaded included/excluded state must not automatically run discovery.
- Deactivated candidates remain excluded or inactive unless future policy changes
  state.
- This gate does not alter discovery-refresh view-model or GUI source.

## Relationship to explicit import GUI

- Explicit import preview does not imply persistence.
- Persistence must not bypass explicit import preview safety.
- Persisted references to imported files must be redacted by default.
- Missing or changed sources require re-preview or future policy.

## Relationship to ProjectSchema

- No ProjectSchema mutation in this gate.
- Future persistence may choose project-local state only through a separate
  schema/persistence design gate.
- Persisted optional solver manifest state should remain experimental unless
  promoted by a future decision.
- Project validation must not treat persisted state as solver validation evidence.

## Relationship to CLI

- No CLI behavior change in this gate.
- No CLI state save/load command.
- A future CLI persistence design would require a separate gate.

## Relationship to export summary

- Future redacted export summaries may include persisted state summaries.
- Export summaries may be non-reloadable unless a future state-bundle gate defines
  reload semantics.
- Sensitive local paths must stay redacted by default.
- No export behavior is implemented in this gate.

## Relationship to live optional validation issues

- Issues `#6` through `#11` remain open.
- Persisted state is not live optional validation.
- Persisted state must not mark issues ready to close.
- Skipped-missing remains skipped-missing.
- Prepared-machine validation remains a separate gate.

## Diagnostics reserved for future persistence

Reserved design-only diagnostic code names (not implemented in this gate):

- `OSPMG_PERSISTENCE_NOT_IMPLEMENTED`
- `OSPMG_PERSISTENCE_ACK_REQUIRED`
- `OSPMG_PERSISTENCE_NOT_VALIDATION`
- `OSPMG_PERSISTENCE_NOT_TRUST_RESTORE`
- `OSPMG_PERSISTENCE_NO_INSTALL`
- `OSPMG_PERSISTENCE_NO_SOLVER_EXECUTION`
- `OSPMG_PERSISTENCE_NOT_ISSUE_CLOSURE`
- `OSPMG_PERSISTENCE_NOT_RELEASE_MUTATION`
- `OSPMG_PERSISTENCE_REDACTION_REQUIRED`
- `OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED`
- `OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED`
- `OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED`
- `OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED`
- `OSPMG_PERSISTENCE_UNTRUSTED_SOURCE`
- `OSPMG_PERSISTENCE_CONFLICT_BLOCKED`
- `OSPMG_PERSISTENCE_UNSAFE_CLAIM`
- `OSPMG_PERSISTENCE_EVIDENCE_RETAINED`
- `OSPMG_PERSISTENCE_HISTORY_RETAINED`
- `OSPMG_PERSISTENCE_NO_DISCOVERY_EXECUTION`
- `OSPMG_PERSISTENCE_NO_PLUGIN_IMPORT`
- `OSPMG_PERSISTENCE_FUTURE_GATE`

These names are reservations only. No diagnostic emitter, runtime constant, or GUI
handler is added in this gate.

## Future implementation test plan

A later implementation gate must add tests that verify:

- persistence is unavailable unless explicitly requested
- persistence requires redaction review
- an unredacted path blocks export/save unless future policy allows it
- reload does not silently trust stale sources
- reload does not auto-activate candidates
- reload does not restore trust
- reload does not install dependencies
- reload does not run discovery
- reload does not run validation
- reload does not execute solvers
- reload does not close issues
- reload does not mutate releases/tags/assets
- persisted acknowledgements expire when the source changes
- persisted acknowledgements expire when the schema version changes
- schema migration diagnostics surface
- the built-ins-win / shared-stack policy remains visible
- unsafe claims block or warn
- source references are redacted
- a trust label is not certification
- skipped-missing remains skipped-missing

These are future tests. This gate adds only a focused docs test for this design
document and the related guardrail/risk/checklist/validation references.

## Non-actions

This gate explicitly does not:

- implement persistence
- implement file writes
- create settings files
- implement project schema mutation
- implement GUI persistence behavior
- implement CLI persistence behavior
- alter activation view-model or GUI source
- alter deactivation view-model or GUI source
- alter reactivation view-model or GUI source
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
- claim validation failure
- claim issue closure
- claim bundled solvers
- claim certification

No runtime source, GUI source, view-model source, CLI source, loader source,
discovery source, plugin manager source, or ProjectSchema source is changed in
this gate. This design adds no validation-pass claim, no validation-fail claim, no
issue-closure claim, no bundled-solver claim, and no certification claim.
User-selected and plugin-provided manifests remain untrusted; deactivation and
reactivation history and historical validation evidence are retained;
skipped-missing optional validation remains neither pass nor failure, and issues
`#6` through `#11` stay open.

## Future gates

Proposed follow-up candidates, not implemented here:

- `OSW-EXP-091_OPTIONAL_SOLVER_PLUGIN_MANIFEST_STATE_EXPORT_SUMMARY_DESIGN`
- `OSW-EXP-092_OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_VIEWMODEL`
- `OSW-EXP-093_OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_SCHEMA_MODEL`
- `OSW-EXP-094_OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_GUI_DESIGN`
- `OSW-EXP-095_OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_GUI_IMPLEMENTATION`
- `OSW-EXP-096_OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_CLI_DESIGN`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` (only if a
  prepared machine is available)

Numbering note: this continues the established optional-solver plugin manifest
cadence (activation/deactivation/reactivation each ran design -> view-model ->
GUI). State persistence begins with this design (090), followed by export-summary
design (091) and then persistence view-model/schema/GUI/CLI gates (092+). If the
repo later re-reserves a different sequence, follow the repo's latest convention
and update this mapping. Persistence implementation, schema files, discovery
integration, validation, install/uninstall, solver execution, and any live
validation remain separate, later gates regardless of numbering.

## Follow-up: schema model (OSW-EXP-093)

OSW-EXP-092 implemented the persistence view-model. OSW-EXP-093 implements the
pure, in-memory persistence schema model that defines the versioned record shape a
future writer would serialize. See
[optional_solver_plugin_manifest_persistence_schema_model.md](optional_solver_plugin_manifest_persistence_schema_model.md).
The schema model still creates no schema file and writes nothing; persistence
implementation remains a separate, later gate.
