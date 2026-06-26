# Optional solver plugin manifest activation design

## Status

Design-only.

No runtime behavior is added in this gate. This document defines the future
safety contract, UX flow, data boundaries, diagnostics, and follow-up gate
sequence for optional solver plugin manifest activation. It is not implementation
authorization and does not read as one.

Status boundaries:

- no runtime source behavior added
- no activation implementation
- no activation persistence
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

Define future activation semantics for user-selected or plugin-provided optional
solver manifests, while preserving the existing preview-only import and
display-only boundaries.

The purpose is to:

- define what activation means and what activation does not mean
- preserve preview-only import (OSW-EXP-075/076/077) and display-only panel
  (OSW-EXP-074) boundaries
- make activation distinct from trust, validation, discovery, installation,
  issue closure, release mutation, and certification

Activation is not validation. Activation is not solver execution. Activation is
not dependency installation. Activation is not trust-by-default.

## Current state before activation

- OSW-EXP-074 added a display-only `OptionalSolverPluginManifestPanel`.
- OSW-EXP-075 defined the explicit plugin manifest JSON import/preview GUI design.
- OSW-EXP-076 implemented the pure explicit-import GUI view-model.
- OSW-EXP-077 implemented the preview-only PySide explicit-import panel.
- OSW-MAINT-019 reconciled the GUI import-workflow test with the current API.
- User-selected and plugin-provided manifests are still untrusted preview data
  only. There is no activation behavior yet.

Issues `#6` through `#11` remain open. Package metadata remains `0.1.5rc1`. The
public prerelease remains `v0.1.5-rc1`.

## Definition of activation

Activation is a future explicit user acknowledgement that a previewed manifest
source may become an active manifest candidate for future optional solver UX
surfaces.

Activation may eventually mean:

- the source is visible as an active candidate in a health/discovery UI
- the source is labeled with provenance and trust state
- the source can be included in a future passive discovery refresh, only if a
  later gate enables that
- the source can appear in redacted summaries, only if a later gate enables that

Activation must not mean:

- solver validation success
- dependency installation
- solver execution
- plugin code execution
- plugin package import
- issue closure
- release mutation
- certification
- trusted-by-default status

## Activation preconditions

Future preconditions before activation may be allowed:

- explicit user action (never automatic)
- the manifest was previewed first
- the loader report has no schema blockers
- conflicts are visible
- built-in override attempts are visible and blocked by default
- unsafe claims are visible
- the user acknowledges the untrusted-source warning
- the user acknowledges that preview is not validation
- the user acknowledges that activation is not installation
- the user acknowledges that activation is not solver execution

If any precondition is unmet, activation is blocked (see the state machine).

## User acknowledgement model

Future activation requires explicit acknowledgements before it can proceed:

- untrusted source acknowledgement
- no validation-pass acknowledgement
- no dependency-install acknowledgement
- no solver-execution acknowledgement
- no issue-closure acknowledgement
- no certification acknowledgement
- conflict/override acknowledgement (when conflicts or built-in overrides exist)
- unsafe-claim acknowledgement (when unsafe claims are present)

Acknowledgements are recorded as future in-memory state only. They do not grant
trust-by-default and do not constitute validation evidence.

## Source/trust/provenance model

Future labels:

- `source_type`: `built_in`, `user_selected_json_file`, `plugin_provided_manifest`,
  `future_imported_manifest`
- `trust_label`: `built_in`, `untrusted_user_file`, `untrusted_plugin_manifest`,
  `future_trusted_by_user`
- `activation_state`: `inactive_preview`, `activation_requested`,
  `activation_ready`, `activation_blocked`, `active_candidate`, `deactivated`

Rules:

- the source reference must be redacted by default
- a trust label is not certification
- user-selected and plugin-provided manifests are untrusted by default
- `future_trusted_by_user` is an explicit, acknowledged, per-source state, never
  a default, and still is not certification

## Conflict and built-in precedence policy

- Built-in manifests win by default.
- User-selected and plugin-provided manifests must not override built-ins
  silently.
- Duplicate stack IDs must be visible.
- Conflict resolution requires an explicit future policy.
- Activation of conflicting manifests should be blocked or marked
  active-with-conflict-blockers until a future gate defines otherwise.

## Unsafe claim policy

Activation must not permit manifests that claim:

- bundled solver binaries
- automatic install
- validation success
- issue closure readiness
- industrial certification
- proprietary solver parity
- full OpenFOAM, ANSYS, MATLAB, or Abaqus replacement

unless a future explicit gate defines safe diagnostic handling. The preferred
outcome is block or active-with-blockers, never silent success.

## Relationship to explicit import GUI

- The explicit import GUI remains preview-only.
- Activation must be a separate, distinct user action from preview.
- Cancel/no-op preview behavior remains unchanged.
- Choosing a file and loading a file do not imply activation.

## Relationship to loader and CLI preview

- Existing loader/report semantics remain the source of
  accepted/rejected/conflict/diagnostic evidence.
- `optional-solver-plugin-manifest-preview` remains preview-only.
- CLI activation is not implemented by this design.
- A future CLI activation design would require a separate gate.

## Relationship to optional solver health panel

- Activation is not health validation.
- Activation must not automatically run passive discovery unless a future
  explicit refresh gate allows it.
- The health panel must show activated manifest candidates as unvalidated until
  discovery/validation evidence exists.
- Missing optional stacks remain `skipped-missing`, not pass.

## Relationship to discovery refresh

- Current passive discovery remains built-in/passive unless a later gate adds
  activated manifest candidates.
- Future discovery refresh with activated manifests must be explicit and
  user-initiated.
- No automatic startup refresh.
- No active smoke validation is defined in this activation design.

## Relationship to export summary

- Future redacted export summaries may include activation state.
- Sensitive local paths must stay redacted by default.
- Activation state is not validation evidence.
- No export behavior is implemented in this gate.

## Activation state machine

Future activation state machine:

- `inactive_preview` (initial; a previewed source that has not been activated)
- `activation_requested`
- `activation_blocked`
- `activation_ready`
- `active_candidate`
- `deactivated`
- `activation_error`

Allowed transitions:

- `inactive_preview` -> `activation_requested` (explicit user request)
- `activation_requested` -> `activation_blocked` (precondition unmet, schema
  blocker, conflict, unsafe claim, or missing acknowledgement)
- `activation_requested` -> `activation_ready` (all preconditions and
  acknowledgements satisfied)
- `activation_ready` -> `active_candidate` (explicit confirm)
- `active_candidate` -> `deactivated` (explicit user deactivation)
- `deactivated` -> `inactive_preview` (re-preview)
- any state -> `activation_error` (unexpected future runtime error)

Blocked transitions:

- `inactive_preview` -> `active_candidate` directly (must pass request/ready)
- `activation_blocked` -> `active_candidate` (blockers must be cleared first)
- `active_candidate` -> any discovery/validation/install/execution state (those
  remain separate, later, explicit gates)

## Diagnostics reserved for future activation

Reserved design-only diagnostic code names (not implemented in this gate):

- `OSPMG_ACTIVATION_PREVIEW_REQUIRED`
- `OSPMG_ACTIVATION_SCHEMA_BLOCKED`
- `OSPMG_ACTIVATION_CONFLICT_BLOCKED`
- `OSPMG_ACTIVATION_UNTRUSTED_SOURCE`
- `OSPMG_ACTIVATION_UNSAFE_CLAIM`
- `OSPMG_ACTIVATION_ACK_REQUIRED`
- `OSPMG_ACTIVATION_NOT_VALIDATION`
- `OSPMG_ACTIVATION_NO_INSTALL`
- `OSPMG_ACTIVATION_NO_SOLVER_EXECUTION`
- `OSPMG_ACTIVATION_NOT_CERTIFICATION`
- `OSPMG_ACTIVATION_DEACTIVATED`
- `OSPMG_ACTIVATION_PREVIEW_ONLY_GATE`

These names are reservations only. No diagnostic emitter, runtime constant, or
GUI handler is added in this gate.

## Future implementation test plan

A later implementation gate must add tests that verify:

- activation is unavailable before preview
- activation is blocked on a schema-invalid manifest
- activation is blocked or warned on conflicts
- the built-ins-win policy is visible
- the untrusted-source warning is visible
- acknowledgements are required
- a trust label is not certification
- activation is not validation
- activation is not install
- activation is not discovery execution
- activation is not solver execution
- activation is not issue closure
- the deactivation state is visible
- source references are redacted
- no plugin package import occurs
- no directory scan occurs
- no network fetch occurs
- no issue, release, tag, or asset mutation occurs

These are future tests. This gate adds only a focused docs test for this design
document and the related guardrail/risk/checklist/validation references.

## Non-actions

This gate explicitly does not:

- implement activation
- implement activation persistence
- implement deactivation
- implement GUI activation button behavior
- implement CLI activation
- implement plugin package import
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
untrusted preview data only; skipped-missing optional validation remains neither
pass nor failure, and issues `#6` through `#11` stay open.

## Future gates

Proposed follow-up candidates, not implemented here:

- `OSW-EXP-079_OPTIONAL_SOLVER_PLUGIN_MANIFEST_ACTIVATION_VIEWMODEL`
- `OSW-EXP-080_OPTIONAL_SOLVER_PLUGIN_MANIFEST_ACTIVATION_GUI_IMPLEMENTATION`
- `OSW-EXP-081_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DEACTIVATION_DESIGN`
- `OSW-EXP-082_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DISCOVERY_REFRESH_INTEGRATION_DESIGN`
- `OSW-VALID` prepared-machine validation reuse

Numbering note: this continues the established explicit-import cadence
(OSW-EXP-075 design -> OSW-EXP-076 view-model -> OSW-EXP-077 implementation).
Activation follows the same design -> view-model -> implementation order, with
deactivation and discovery-refresh integration as separate later gates. If the
repo later re-reserves a different sequence, follow the repo's latest convention
and update this mapping. Activation, deactivation, discovery refresh, and any
live validation remain separate, later gates regardless of numbering.
