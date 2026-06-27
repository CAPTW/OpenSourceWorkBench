# Optional solver plugin manifest discovery refresh view-model

## Status

Experimental pure discovery-refresh view-model implemented.

This gate (OSW-EXP-083) implements the pure, side-effect-free discovery-refresh
view-model for the contract designed in OSW-EXP-082.

Status boundaries:

- pure Python view-model
- no runtime discovery integration
- no passive discovery behavior change
- no activation persistence
- no deactivation persistence
- no GUI behavior
- no CLI behavior
- no plugin package import
- no directory scan
- no network fetch
- no discovery execution
- no validation execution
- no solver execution
- no dependency installation
- no issue/release/tag/asset mutation

## Purpose

Translate already-supplied activation/deactivation candidate state (or
caller-supplied discovery source records) into deterministic discovery-refresh
readiness, source inclusion/exclusion, acknowledgement, diagnostic, conflict,
unsafe-claim, trust, and action-state records that a future implementation gate
can bind to safely.

Refresh lifecycle inputs and acknowledgement satisfaction are supplied by the
caller; this layer only classifies and renders them. It does not run discovery,
change passive discovery, or persist any state.

## Public module and class names

Module:

`src/osw/experimental/optional_solvers/plugin_manifest_discovery_refresh_viewmodel.py`

Public view-model and records:

- `OptionalSolverPluginManifestDiscoveryRefreshViewModel`
- `OptionalSolverPluginManifestDiscoveryRefreshSummaryViewModel`
- `OptionalSolverPluginManifestDiscoveryRefreshSourceInput`
- `OptionalSolverPluginManifestDiscoverySourceRowViewModel`
- `OptionalSolverPluginManifestDeactivatedCandidateRowViewModel`
- `OptionalSolverPluginManifestDiscoveryRefreshAcknowledgementRowViewModel`
- `OptionalSolverPluginManifestDiscoveryRefreshDiagnosticViewModel`
- `OptionalSolverPluginManifestDiscoveryRefreshConflictRowViewModel`
- `OptionalSolverPluginManifestDiscoveryRefreshUnsafeClaimRowViewModel`
- `OptionalSolverPluginManifestDiscoveryRefreshTrustBadgeViewModel`
- `OptionalSolverPluginManifestDiscoveryRefreshActionState`
- `OptionalSolverPluginManifestDiscoveryRefreshMode`
- `OptionalSolverPluginManifestDiscoveryRefreshState`
- `OptionalSolverPluginManifestDiscoveryRefreshReadiness`
- `OptionalSolverPluginManifestDiscoverySourceState`

Builders/helpers: `build_optional_solver_plugin_manifest_discovery_refresh_viewmodel`,
`render_optional_solver_plugin_manifest_discovery_refresh_summary` (in-memory),
`summarize_*`, `explain_*`,
`redact_optional_solver_plugin_manifest_discovery_source_reference`. Convenience
constructors: `from_sources`, `from_activation_viewmodel`, `built_in_only`,
`unavailable`, `all_blocked`, `result_preview`.

## Input boundary

The view-model consumes supplied data only:

- an `OptionalSolverPluginManifestActivationViewModel` (OSW-EXP-079)
- caller-supplied `OptionalSolverPluginManifestDiscoveryRefreshSourceInput` records
- caller-supplied acknowledgement satisfaction, refresh-requested flag, refresh
  mode, built-in source counts, and result-preview flag

It performs no file IO, no JSON parsing from paths, no plugin package import, no
directory scan, no network fetch, and no discovery execution.

## Refresh modes

The OSW-EXP-082 modes are modeled (none executed): `built_in_only_refresh`,
`activated_candidates_preview_refresh`,
`activated_candidates_user_initiated_refresh`, `deactivated_candidates_excluded`,
`deactivated_candidates_visible_but_inactive`,
`blocked_due_to_untrusted_or_conflicting_sources`.

## Refresh state machine

The OSW-EXP-082 states are modeled: `refresh_unavailable`, `refresh_requested`,
`refresh_blocked`, `refresh_ready`, `refresh_running_future_gate`,
`refresh_result_preview`, `refresh_error`. The blocked transitions are exposed via
`blocked_transitions` (e.g., preview-only directly to discovery execution; an
inactive/deactivated candidate directly to an active discovery source; refresh to
validation/install/solver/issue-closure/release-mutation).

## Readiness rules

Per-refresh readiness: `unavailable_no_activation_state`,
`unavailable_no_active_candidates`, `built_in_only_ready`,
`blocked_acknowledgement`, `blocked_conflict`, `blocked_unsafe_claim`,
`ready_preview_only`, `ready_future_refresh`, `result_preview`, `error`.

Ready requires supplied source state, an includable active candidate (or
built-in-only mode), no conflict/unsafe blockers, and all required
acknowledgements satisfied. Ready is still not validation evidence and still not
discovery execution in this gate.

## Acknowledgement model

Required acknowledgement identifiers: `refresh_not_validation`,
`refresh_not_install`, `refresh_not_solver_execution`,
`refresh_not_issue_closure`, `refresh_not_certification`,
`untrusted_manifest_source`, `conflict_or_override_visible`,
`deactivated_candidates_excluded`, `no_network_fetch`,
`no_plugin_package_import`. Missing required acknowledgements are visibly
blocking. The caller supplies satisfaction booleans; the view-model never
persists them.

## Diagnostic vocabulary

The view-model surfaces the OSW-EXP-082 `OSPMG_DISCOVERY_REFRESH_*` codes,
exposed as `OSPMG_DISCOVERY_REFRESH_DIAGNOSTIC_CODES` and on each view-model as
`reserved_diagnostic_codes`:
`OSPMG_DISCOVERY_REFRESH_ACTIVE_CANDIDATE_REQUIRED`,
`OSPMG_DISCOVERY_REFRESH_DEACTIVATED_EXCLUDED`,
`OSPMG_DISCOVERY_REFRESH_ACK_REQUIRED`,
`OSPMG_DISCOVERY_REFRESH_UNTRUSTED_SOURCE`,
`OSPMG_DISCOVERY_REFRESH_CONFLICT_BLOCKED`,
`OSPMG_DISCOVERY_REFRESH_UNSAFE_CLAIM`,
`OSPMG_DISCOVERY_REFRESH_NOT_VALIDATION`,
`OSPMG_DISCOVERY_REFRESH_NO_INSTALL`,
`OSPMG_DISCOVERY_REFRESH_NO_SOLVER_EXECUTION`,
`OSPMG_DISCOVERY_REFRESH_NO_NETWORK_FETCH`,
`OSPMG_DISCOVERY_REFRESH_NO_PLUGIN_IMPORT`,
`OSPMG_DISCOVERY_REFRESH_NOT_ISSUE_CLOSURE`,
`OSPMG_DISCOVERY_REFRESH_NOT_CERTIFICATION`,
`OSPMG_DISCOVERY_REFRESH_INTEGRATION_NOT_IMPLEMENTED`. None of these diagnostics
are validation-pass evidence.

## Rendered view-model sections

- summary (mode, state, readiness, counts, honesty flags)
- discovery source rows (included/excluded with redacted references)
- deactivated candidate rows (excluded by default)
- acknowledgements
- diagnostics
- conflicts
- unsafe claims
- trust/provenance badges
- action states
- in-memory redacted summary (`render_*`)

The summary carries honesty flags that remain false:
`discovery_execution_performed`, `validation_execution_performed`,
`solver_execution_performed`, `dependency_installation_performed`,
`network_fetch_performed`, `plugin_package_import_performed`,
`issue_mutation_performed`, `release_mutation_performed`, and
`certification_claimed`.

## Source/trust/provenance behavior

User-selected and plugin-provided manifests are untrusted by default. Source
references are redacted by default (path-like references shortened to their final
segment). A trust label is not certification, and discovery inclusion is not
validation evidence.

## Built-in precedence/conflict policy

Built-ins win by default and are authoritative; user/plugin candidates must not
override built-ins silently. Duplicate stack ids are visible; conflicts block the
refresh input and surface a conflict row with `built_ins_win_default` true and a
required-future-policy note.

## Relationship to OSW-EXP-082 design

This gate implements the pure view-model layer of the OSW-EXP-082
discovery-refresh integration design. Runtime discovery integration, GUI refresh
behavior, CLI refresh behavior, validation, install, solver execution, issue
closure, and release mutation remain future-gated.

## Relationship to OSW-EXP-079 activation view-model

The discovery-refresh view-model adapts OSW-EXP-079 activation view-model
records (active and deactivated candidate rows) without mutating them and without
adding PySide/Qt imports. It does not persist activation state and does not turn
an active candidate into validation evidence.

## Relationship to OSW-EXP-081 deactivation design

Deactivated candidates are excluded by default or represented as inactive
history. A deactivated state is not a validation failure, not uninstall, and not
file deletion. This gate implements no deactivation source changes.

## Relationship to health panel and passive discovery

No passive discovery behavior change, no discovery service source edits, no
background refresh, and no startup refresh. Activated candidates are kept
separate from built-in/passive discovery data, and the health panel keeps its
existing behavior until a future implementation gate.

## Relationship to live optional validation issues

Issues `#6` through `#11` remain open. Discovery refresh is not live optional
validation; refresh-ready or result-preview state must not mark issues ready to
close. Skipped-missing remains skipped-missing; prepared-machine validation
remains a separate gate.

## Relationship to CLI and export summary

No CLI behavior changes and no CLI discovery-refresh command are added. The
in-memory redacted summary helper writes no files, touches no clipboard, and
opens no shell, browser, or output folder.

## Non-actions

This gate does not:

- run discovery or change passive discovery behavior
- implement runtime discovery integration
- persist activation or deactivation state
- implement GUI or CLI behavior
- import plugin packages
- scan directories
- fetch network manifests
- run validation
- execute solvers
- install dependencies
- mutate issues, releases, tags, or assets
- bump versions
- make any validation-pass claim, issue-closure claim, bundled-solver claim, or
  certification claim

User-selected and plugin-provided manifests remain untrusted; built-ins remain
authoritative; skipped-missing optional validation remains neither pass nor
failure, and issues `#6` through `#11` stay open.

## Future gates

- `OSW-EXP-084_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DISCOVERY_REFRESH_GUI_IMPLEMENTATION`
- `OSW-EXP-085_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DEACTIVATION_VIEWMODEL_EXTENSION`
- `OSW-EXP-086_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DEACTIVATION_GUI_IMPLEMENTATION`
- `OSW-VALID` prepared-machine validation reuse
