# Optional solver plugin manifest activation view-model

## Status

Experimental pure activation view-model implemented.

This gate (OSW-EXP-079) implements the pure, side-effect-free activation
view-model for the contract designed in OSW-EXP-078.

Status boundaries:

- pure Python view-model
- no activation persistence
- no GUI behavior
- no CLI activation
- no plugin package import
- no directory scan
- no network fetch
- no discovery execution
- no validation execution
- no solver execution
- no dependency installation
- no issue/release/tag/asset mutation

## Purpose

Translate already-supplied previewed plugin manifest data (or caller-supplied
activation candidates plus acknowledgement/lifecycle state) into deterministic
activation-readiness, acknowledgement, diagnostic, conflict, trust, and
action-state records that a future GUI implementation gate can bind to safely.

Activation lifecycle inputs (requested / active / deactivated) and
acknowledgement satisfaction are supplied by the caller; this layer only
classifies and renders them. It does not persist activation and does not turn
preview into activation.

## Public module and class names

Module:

`src/osw/experimental/optional_solvers/plugin_manifest_activation_viewmodel.py`

Public view-model and records:

- `OptionalSolverPluginManifestActivationViewModel`
- `OptionalSolverPluginManifestActivationSummaryViewModel`
- `OptionalSolverPluginManifestActivationCandidateInput`
- `OptionalSolverPluginManifestActivationCandidateRowViewModel`
- `OptionalSolverPluginManifestActivationAcknowledgementRowViewModel`
- `OptionalSolverPluginManifestActivationDiagnosticViewModel`
- `OptionalSolverPluginManifestActivationConflictRowViewModel`
- `OptionalSolverPluginManifestActivationTrustBadgeViewModel`
- `OptionalSolverPluginManifestActivationActionState`
- `OptionalSolverPluginManifestActivationAction`
- `OptionalSolverPluginManifestActivationState`
- `OptionalSolverPluginManifestActivationReadiness`

Builders and helpers:

- `build_optional_solver_plugin_manifest_activation_viewmodel`
- `render_optional_solver_plugin_manifest_activation_summary` (in-memory only)
- `summarize_optional_solver_plugin_manifest_activation_viewmodel`
- `explain_optional_solver_plugin_manifest_activation_viewmodel`

Convenience constructors on the view-model class: `from_candidates`,
`from_explicit_import_viewmodel`, `from_loader_report`, `empty`,
`preview_required`, `all_blocked`.

## Input boundary

The view-model consumes supplied data only:

- an `OptionalSolverPluginManifestExplicitImportGuiViewModel` (OSW-EXP-076)
- an `OptionalSolverPluginManifestLoadReport` (adapted via the explicit-import
  builder)
- caller-supplied `OptionalSolverPluginManifestActivationCandidateInput` records
- caller-supplied acknowledgement satisfaction and requested/active/deactivated
  stack-id sets

It performs no file IO, no JSON parsing from paths, no plugin package import,
and no discovery execution.

## Activation state machine

The view-model models the OSW-EXP-078 state machine:

- `inactive_preview`
- `activation_requested`
- `activation_blocked`
- `activation_ready`
- `active_candidate`
- `deactivated`
- `activation_error`

A candidate not yet requested stays `inactive_preview`; a requested candidate
becomes `activation_ready` or `activation_blocked`; caller-supplied active or
deactivated state maps to `active_candidate` or `deactivated`.

## Readiness rules

Per-candidate readiness:

- `unavailable_before_preview` (no preview data)
- `blocked_schema`
- `blocked_conflict`
- `blocked_unsafe_claim`
- `blocked_acknowledgement`
- `ready`
- `active_candidate`
- `deactivated`
- `error`

`ready` requires preview data, no schema/conflict/unsafe blockers, and all
required acknowledgements satisfied. `ready` and `active_candidate` are still not
validation evidence.

## Acknowledgement model

Required acknowledgement identifiers:

- `untrusted_source` (required when any candidate is untrusted)
- `no_validation_pass`
- `no_dependency_install`
- `no_solver_execution`
- `no_issue_closure`
- `no_certification`
- `conflict_or_override` (required when conflicts exist)
- `unsafe_claim` (required when unsafe claims exist)

Missing required acknowledgements are visibly blocking. The caller supplies
satisfaction booleans; the view-model never persists them.

## Diagnostic vocabulary

The view-model surfaces the OSW-EXP-078 `OSPMG_ACTIVATION_*` codes, exposed as
`OSPMG_ACTIVATION_DIAGNOSTIC_CODES` and on each view-model as
`reserved_activation_diagnostic_codes`:

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

None of these diagnostics are validation-pass evidence.

## Rendered view-model sections

- summary (counts, readiness tallies, honesty flags)
- candidate rows (readiness, state, blockers, warnings, required
  acknowledgements, diagnostics, redacted source reference)
- acknowledgement rows
- diagnostics
- conflicts
- trust/provenance badges
- action states
- in-memory redacted summary (`render_*`)

The summary carries honesty flags that remain false: `validation_execution_
performed`, `discovery_execution_performed`, `solver_execution_performed`,
`dependency_installation_performed`, `issue_mutation_performed`,
`release_mutation_performed`, and `certification_claimed`.

## Source/trust/provenance behavior

User-selected and plugin-provided manifests are untrusted by default. Source
references are redacted by default (path-like references shortened to their final
segment). A trust label is not certification, and an active candidate is not
validation evidence.

## Relationship to OSW-EXP-078 design

This gate implements the pure view-model layer of the OSW-EXP-078 activation
design. GUI activation, persistence, discovery integration, validation, install,
and execution remain future-gated.

## Relationship to OSW-EXP-076/077 explicit import preview

The activation view-model adapts the OSW-EXP-076 explicit-import view-model and
OSW-EXP-077 preview panel data without mutating them and without adding PySide/Qt
imports. Previewed manifest data remains untrusted by default; preview is not
activation.

## Relationship to optional solver health panel and discovery refresh

Activation view-model state is not health validation and does not run passive
discovery. A future discovery refresh integration gate may consume active
candidates; this gate only models the state.

## Relationship to CLI and export summary

No CLI behavior changes and no CLI activation command are added. The in-memory
redacted summary helper writes no files, touches no clipboard, and opens no
shell, browser, or output folder.

## Non-actions

This gate does not:

- activate anything
- persist activation
- implement GUI activation behavior
- implement CLI activation
- import plugin packages
- scan directories
- fetch network manifests
- run discovery
- run validation
- execute solvers
- install dependencies
- mutate issues, releases, tags, or assets
- bump versions
- make any validation-pass claim, issue-closure claim, bundled-solver claim, or
  certification claim

User-selected and plugin-provided manifests remain untrusted; skipped-missing
optional validation remains neither pass nor failure, and issues `#6` through
`#11` stay open.

## Future gates

- `OSW-EXP-080_OPTIONAL_SOLVER_PLUGIN_MANIFEST_ACTIVATION_GUI_IMPLEMENTATION`
- `OSW-EXP-081_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DEACTIVATION_DESIGN`
- `OSW-EXP-082_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DISCOVERY_REFRESH_INTEGRATION_DESIGN`
- `OSW-VALID` prepared-machine validation reuse
