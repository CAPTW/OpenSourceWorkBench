# Optional solver plugin manifest discovery refresh integration design

## Status

Design-only.

No runtime behavior is added in this gate. This document defines the future
safety contract, UX flow, data boundaries, state model, diagnostics, and
follow-up gates for integrating optional solver plugin manifest
activation/deactivation state with optional solver discovery refresh. It is not
implementation authorization and does not read as one.

Status boundaries:

- no runtime source behavior added
- no discovery integration implementation
- no passive discovery behavior change
- no activation persistence
- no deactivation persistence
- no GUI behavior change
- no CLI behavior change
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

Define future integration between activated/deactivated plugin manifest state and
optional solver discovery refresh, while preserving the activation,
deactivation, and preview safety boundaries.

The purpose is to:

- define how activated/deactivated candidates may affect future discovery inputs
- preserve the activation/deactivation/preview boundaries
- make discovery refresh distinct from validation, installation, solver
  execution, issue closure, release mutation, and certification

Discovery refresh is not validation success. Discovery refresh is not dependency
installation. Discovery refresh is not solver execution. Discovery refresh is not
certification.

## Current state before discovery-refresh integration

- The explicit import GUI preview exists (OSW-EXP-074..077).
- The activation design, view-model, and GUI exist (OSW-EXP-078..080).
- The deactivation design exists (OSW-EXP-081).
- Activated/deactivated state is not persisted by the product yet.
- Discovery refresh does not consume activated plugin manifest candidates yet.
- User-selected and plugin-provided manifests remain untrusted and
  non-validating.

Issues `#6` through `#11` remain open. Package metadata remains `0.1.5rc1`. The
public prerelease remains `v0.1.5-rc1`.

## Definition of discovery-refresh integration

Discovery-refresh integration is a future explicit workflow where optional solver
discovery may consider active manifest candidates supplied by an activation state
source.

It may eventually mean:

- activated candidates can be included in a discovery input set
- deactivated candidates can be excluded or shown as excluded
- built-in manifests remain authoritative
- refresh results can show provenance and trust labels
- refresh summaries can distinguish built-in/passive data from activated
  user/plugin candidate data

It must not mean:

- validation success
- dependency installation
- solver execution
- plugin package import
- directory scanning outside approved sources
- network fetching
- issue closure
- release, tag, or asset mutation
- certification
- trusted-by-default status

## Discovery refresh modes

Future modes (none implemented in this gate):

- `built_in_only_refresh`
- `activated_candidates_preview_refresh`
- `activated_candidates_user_initiated_refresh`
- `deactivated_candidates_excluded`
- `deactivated_candidates_visible_but_inactive`
- `blocked_due_to_untrusted_or_conflicting_sources`

This gate implements none of these modes.

## Preconditions

Future preconditions before a refresh may consider activated candidates:

- explicit user action (never automatic)
- active candidate state supplied by the activation view-model or a future
  persistence layer
- candidate provenance is visible
- trust label is visible
- unsafe actions remain disabled unless a future gate explicitly allows them
- conflicts are visible
- deactivated candidates are clearly excluded or marked inactive
- the user acknowledges refresh is not validation
- the user acknowledges refresh is not install
- the user acknowledges refresh is not solver execution
- the user acknowledges refresh does not close issues

## User acknowledgement model

Future acknowledgement categories:

- `refresh_not_validation`
- `refresh_not_install`
- `refresh_not_solver_execution`
- `refresh_not_issue_closure`
- `refresh_not_certification`
- `untrusted_manifest_source`
- `conflict_or_override_visible`
- `deactivated_candidates_excluded`
- `no_network_fetch`
- `no_plugin_package_import`

Acknowledgements are recorded as future in-memory state only. They do not grant
trust-by-default and do not constitute validation evidence.

## Source/trust/provenance model

Future labels:

- `source_type`: `built_in`, `activated_user_selected_json_file`,
  `activated_plugin_manifest`, `deactivated_manifest`,
  `future_persisted_activation`
- `trust_label`: `built_in`, `untrusted_user_file`, `untrusted_plugin_manifest`,
  `future_trusted_by_user`
- `discovery_source_state`: `built_in_only`, `active_candidate_included`,
  `deactivated_excluded`, `conflict_blocked`, `unsafe_claim_blocked`,
  `refresh_blocked`

Rules:

- source references must be redacted by default
- a trust label is not certification
- discovery inclusion is not validation evidence
- user-selected and plugin-provided manifests are untrusted by default

## Built-in precedence and conflict policy

- Built-ins win by default.
- User/plugin manifests must not override built-ins silently.
- Duplicate stack ids must be visible.
- Deactivated user/plugin candidates must not suppress built-ins.
- Discovery refresh must not hide conflicts.
- Conflicts should block or mark refresh as blocked until a future explicit
  policy defines resolution.

## Deactivated candidate policy

- Deactivated candidates are not active discovery inputs by default.
- A deactivated state is not a validation failure.
- A deactivated state does not delete manifest files.
- A deactivated state does not uninstall dependencies or solvers.
- Deactivated candidates may appear in future summaries as inactive history.
- Reactivation remains future-gated.

## Unsafe claim policy

Future discovery refresh must block or warn on activated candidates that claim:

- bundled solver binaries
- automatic dependency install
- validation success
- issue closure readiness
- industrial certification
- proprietary solver parity
- full OpenFOAM, ANSYS, MATLAB, or Abaqus replacement
- solver execution during discovery

The preferred outcome is block or refresh-with-blockers, never silent success.

## Refresh state machine

Future refresh state machine:

- `refresh_unavailable`
- `refresh_requested`
- `refresh_blocked`
- `refresh_ready`
- `refresh_running_future_gate`
- `refresh_result_preview`
- `refresh_error`

Allowed transitions:

- `refresh_unavailable` -> `refresh_requested` (explicit user request once active
  candidates exist)
- `refresh_requested` -> `refresh_blocked` (precondition unmet, missing
  acknowledgement, conflict, or unsafe claim)
- `refresh_requested` -> `refresh_ready` (all preconditions and acknowledgements
  satisfied)
- `refresh_ready` -> `refresh_running_future_gate` (only a future implementation
  gate may run passive discovery)
- `refresh_running_future_gate` -> `refresh_result_preview`
- any state -> `refresh_error` (unexpected future runtime error)

Blocked transitions:

- preview-only directly to discovery execution
- an inactive/deactivated candidate directly to an active discovery source
- refresh to validation execution
- refresh to dependency installation
- refresh to solver execution
- refresh to issue closure
- refresh to release mutation

## Diagnostics reserved for future discovery-refresh integration

Reserved  diagnostic code names (not implemented in this gate):

- `OSPMG_DISCOVERY_REFRESH_ACTIVE_CANDIDATE_REQUIRED`
- `OSPMG_DISCOVERY_REFRESH_DEACTIVATED_EXCLUDED`
- `OSPMG_DISCOVERY_REFRESH_ACK_REQUIRED`
- `OSPMG_DISCOVERY_REFRESH_UNTRUSTED_SOURCE`
- `OSPMG_DISCOVERY_REFRESH_CONFLICT_BLOCKED`
- `OSPMG_DISCOVERY_REFRESH_UNSAFE_CLAIM`
- `OSPMG_DISCOVERY_REFRESH_NOT_VALIDATION`
- `OSPMG_DISCOVERY_REFRESH_NO_INSTALL`
- `OSPMG_DISCOVERY_REFRESH_NO_SOLVER_EXECUTION`
- `OSPMG_DISCOVERY_REFRESH_NO_NETWORK_FETCH`
- `OSPMG_DISCOVERY_REFRESH_NO_PLUGIN_IMPORT`
- `OSPMG_DISCOVERY_REFRESH_NOT_ISSUE_CLOSURE`
- `OSPMG_DISCOVERY_REFRESH_NOT_CERTIFICATION`
- `OSPMG_DISCOVERY_REFRESH_INTEGRATION_NOT_IMPLEMENTED`

These names are reservations only. No diagnostic emitter, runtime constant, or
GUI handler is added in this gate.

## Relationship to activation GUI

- The activation GUI remains view-model driven and non-persistent.
- Discovery refresh integration must not turn the activation GUI into a discovery
  runner.
- Active candidate display is not discovery evidence.
- This gate adds no buttons, callbacks, source mutation, or refresh behavior.

## Relationship to deactivation design

- Deactivated candidates are excluded or displayed inactive by future policy.
- Deactivation is not deletion, uninstall, validation failure, or discovery
  execution.
- This gate does not implement a deactivation view-model extension or GUI
  deactivation behavior.

## Relationship to optional solver health panel

- Health panel refresh remains existing behavior until a future implementation
  gate.
- Activated candidates should be clearly separated from built-in/passive
  discovery data.
- Missing optional stacks remain `skipped-missing`, not pass.
- The health panel must not close validation issues.

## Relationship to CLI

- No CLI behavior change in this gate.
- No CLI discovery refresh integration command.
- A future CLI design/implementation would require a separate gate.

## Relationship to export summary

- Future redacted export summaries may include refresh input state and excluded
  deactivated candidates.
- Sensitive local paths must stay redacted by default.
- Refresh state is not validation evidence.
- No export behavior is implemented in this gate.

## Relationship to live optional validation issues

- Issues `#6` through `#11` remain open.
- Discovery refresh is not live optional validation.
- A refresh result must not mark issues ready to close.
- Skipped-missing remains skipped-missing.
- Prepared-machine validation remains a separate gate.

## Future implementation test plan

A later implementation gate must add tests that verify:

- refresh is unavailable without active candidates
- built-in-only mode is unaffected
- an activated candidate is included only with explicit acknowledgement
- a deactivated candidate is excluded by default
- a deactivated candidate is displayed as inactive history if supplied
- the built-ins-win conflict is visible
- a conflict blocks the refresh input
- an unsafe claim blocks or warns
- no network fetch occurs
- no plugin package import occurs
- no directory scan occurs
- no dependency installation occurs
- no solver execution occurs
- no validation-pass claim is made
- no issue closure occurs
- no release, tag, or asset mutation occurs
- source references are redacted
- a trust label is not certification
- skipped-missing is not pass

These are future tests. This gate adds only a focused docs test for this design
document and the related guardrail/risk/checklist/validation references.

## Non-actions

This gate explicitly does not:

- implement discovery integration
- change passive discovery behavior
- implement activation persistence
- implement deactivation persistence
- implement GUI refresh behavior
- implement CLI refresh behavior
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
and no certification claim. Built-ins remain authoritative by default;
user-selected and plugin-provided manifests remain untrusted; skipped-missing
optional validation remains neither pass nor failure, and issues `#6` through
`#11` stay open.

## Future gates

Proposed follow-up candidates, not implemented here:

- `OSW-EXP-083_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DISCOVERY_REFRESH_VIEWMODEL`
- `OSW-EXP-084_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DISCOVERY_REFRESH_GUI_IMPLEMENTATION`
- `OSW-EXP-085_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DEACTIVATION_VIEWMODEL_EXTENSION`
- `OSW-EXP-086_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DEACTIVATION_GUI_IMPLEMENTATION`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_REFRESH_VALIDATION` (only if a prepared
  machine is available)

Numbering note: this continues the established activation/deactivation cadence
(OSW-EXP-078..080 activation design -> view-model -> GUI; OSW-EXP-081
deactivation design). The discovery-refresh integration design (this gate, 082)
is followed by its own view-model (083) and GUI (084), with the deactivation
view-model extension and GUI as later optional gates (085, 086). If the repo
later re-reserves a different sequence, follow the repo's latest convention and
update this mapping. Discovery execution, persistence, validation,
install/uninstall, solver execution, and any live validation remain separate,
later gates regardless of numbering.
