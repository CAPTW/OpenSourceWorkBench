# Optional Solver Plugin Manifest Reload View-Model

## Status

The pure reload view-model is implemented.

This gate adds no file reading, no file parsing from path, no runtime reload
implementation, no GUI behavior, no CLI behavior, no ProjectSchema mutation,
no discovery/validation/solver execution, no automatic activation, and no trust
restoration.

The view-model is an in-memory review layer only. It consumes caller-supplied
payload mappings/records and exposes deterministic rows, diagnostics, text, and
mapping output for future GUI/CLI/file-reader gates.

## Purpose

The purpose of this gate is to provide a pure review model for optional solver
plugin manifest persisted UX state before any runtime reload behavior exists.

It turns a caller-supplied mapping shaped like the OSW-EXP-102 state-writer
payload into reviewable reload state. It does not select a path, read a state
file, parse JSON from disk, scan directories, fetch network manifests, import
plugin packages, run discovery, run validation, execute solvers, mutate
ProjectSchema, close issues, mutate releases, restore trust, or activate
candidates.

## Public Module/Class Names

Public module:

- `src/osw/experimental/optional_solvers/plugin_manifest_reload_viewmodel.py`

Public classes and records:

- `OptionalSolverPluginManifestReloadViewModel`
- `OptionalSolverPluginManifestReloadSummary`
- `OptionalSolverPluginManifestReloadSourceRow`
- `OptionalSolverPluginManifestReloadCandidateRow`
- `OptionalSolverPluginManifestReloadAcknowledgementRow`
- `OptionalSolverPluginManifestReloadDiagnostic`
- `OptionalSolverPluginManifestReloadActionState`
- `OptionalSolverPluginManifestReloadEvidenceRow`
- `OptionalSolverPluginManifestReloadConflictRow`
- `OptionalSolverPluginManifestReloadUnsafeClaimRow`
- `OptionalSolverPluginManifestReloadSchemaRow`
- `OptionalSolverPluginManifestReloadRedactionRow`
- `OptionalSolverPluginManifestReloadStaleSourceRow`
- `OptionalSolverPluginManifestReloadState`
- `OptionalSolverPluginManifestReloadReadiness`
- `OptionalSolverPluginManifestReloadAction`
- `OptionalSolverPluginManifestReloadInput`

Public constructors/helpers:

- `OptionalSolverPluginManifestReloadViewModel.from_payload_mapping(...)`
- `OptionalSolverPluginManifestReloadViewModel.from_state_writer_payload(...)`
- `OptionalSolverPluginManifestReloadViewModel.unavailable(...)`
- `OptionalSolverPluginManifestReloadViewModel.empty()`
- `OptionalSolverPluginManifestReloadViewModel.blocked(...)`
- `OptionalSolverPluginManifestReloadViewModel.sample_ready_for_review()`
- `build_optional_solver_plugin_manifest_reload_viewmodel(...)`
- `render_optional_solver_plugin_manifest_reload_viewmodel(...)`

## Input Policy

Allowed input is caller-supplied in-memory data only:

- mapping payloads produced by the explicit local state writer;
- already-built mapping fixtures in tests;
- caller-supplied source labels used only for display/redaction;
- pure records that have already been converted to mappings by the caller.

The view-model does not accept a path and read it, does not open files, does not
parse JSON from a path, does not inspect filesystem state, does not scan plugin
directories, does not fetch network manifests, does not load plugin packages,
does not run discovery/validation/solver execution, and does not treat persisted
state as trusted truth.

Path-like `source_label` strings are reduced to a display name and marked
redacted. The raw path-like string is not retained in mapping output.

## State/Readiness Model

Reload states include:

- `no_reload_request`
- `target_missing`
- `target_not_selected`
- `source_reference_redacted`
- `schema_review`
- `schema_unsupported`
- `schema_migration_required`
- `payload_kind_mismatch`
- `redaction_review_required`
- `acknowledgement_review_required`
- `stale_source_repreview_required`
- `conflict_review_required`
- `unsafe_claim_blocked`
- `history_evidence_review`
- `reload_preview_ready`
- `reload_blocked`
- `reload_error`
- `future_activation_review_required`
- `future_discovery_refresh_required`

Readiness values include:

- `unavailable_no_payload`
- `blocked_payload_kind_mismatch`
- `blocked_schema_version_missing`
- `blocked_schema_unsupported`
- `blocked_schema_migration_required`
- `blocked_redaction_review`
- `blocked_unredacted_path`
- `blocked_secret_like_content`
- `blocked_acknowledgement`
- `blocked_stale_source_repreview`
- `blocked_conflict`
- `blocked_shared_stack_warning`
- `blocked_unsafe_claim`
- `ready_review_only`
- `future_activation_review_required`
- `future_discovery_refresh_required`
- `error`

Precedence is deterministic: no payload, payload-kind mismatch, missing or
unsupported schema, schema migration, redaction and secret blockers, unsafe
claims, stale-source/re-preview, conflict/shared-stack, acknowledgement
blockers, future activation/discovery review, ready review-only, and explicit
error.

## Payload/Schema Behavior

The view-model expects the OSW-EXP-102 state-writer payload kind:

- `optional_solver_plugin_manifest_state_writer_state`

The supported payload schema version is:

- `osw-exp-102-state-writer-1`

Missing schema version produces `blocked_schema_version_missing`. Unsupported
schema version produces `blocked_schema_unsupported`. Migration-required state
produces `blocked_schema_migration_required`.

Schema mismatch is not validation failure. The schema model remains separate
from ProjectSchema. This gate creates no schema files and performs no schema
migration.

## Redaction/Privacy Behavior

The view-model is redaction-first:

- raw path-like labels are hidden by default;
- display names, source ids, and caller-supplied redacted labels are used;
- unredacted path blockers are surfaced;
- secret-like content blockers are surfaced;
- fingerprints are not trust signals;
- redaction review precedes any future activation review.

Diagnostics include `OSPMG_RELOAD_REDACTION_REQUIRED`,
`OSPMG_RELOAD_UNREDACTED_PATH_BLOCKED`, and
`OSPMG_RELOAD_SECRET_LIKE_CONTENT_BLOCKED` as applicable.

## Acknowledgement And Expiry Behavior

The required acknowledgement categories are:

- `reload_not_validation`
- `reload_not_trust_restoration`
- `reload_not_automatic_activation`
- `reload_not_discovery_success`
- `reload_not_dependency_install`
- `reload_no_solver_execution`
- `reload_not_issue_closure`
- `reload_not_release_mutation`
- `reload_not_certification`
- `redaction_reviewed`
- `unredacted_paths_blocked`
- `stale_source_requires_repreview`
- `untrusted_source_remains_untrusted`
- `activation_review_required_after_reload`
- `no_discovery_execution`
- `no_plugin_package_import`
- `no_validation_execution`
- `no_solver_execution`
- `trust_label_not_certification`
- `persisted_acknowledgements_may_expire`

Acknowledgements may expire because of reload, source fingerprint change, schema
version change, unsafe claim appearance, trust policy change, or a future
discovery-refresh result. Missing acknowledgements surface
`OSPMG_RELOAD_ACK_REQUIRED`. Expired acknowledgements surface
`OSPMG_RELOAD_ACK_EXPIRED`.

## Candidate Lifecycle Reload Policy

Candidate rows preserve persisted lifecycle state as review state:

- inactive preview state remains review-only;
- persisted active state requires future activation review and does not mean
  active after reload;
- deactivated state remains deactivated review state;
- reactivation state routes to future activation review;
- discovery-refresh state remains review state and routes to a future
  discovery-refresh review;
- skipped-missing remains skipped-missing if represented.

The view-model performs no automatic activation and no trust restoration.

## Stale-Source/Re-Preview Behavior

Stale-source rows show that old preview state is not silently trusted.
Missing/moved/changed sources require re-preview when represented by supplied
mapping records. The view-model performs no source file IO and does not attempt
to fix stale state.

Stale-source state is not validation failure.

## Conflict/Shared-Stack Behavior

Conflict rows keep conflicts visible. Built-ins win by default. Persisted state
does not override built-ins, and reload does not resolve conflicts.

Shared-stack warnings remain visible and future-gated. Conflict resolution
requires a separate policy gate.

## Unsafe-Claim Behavior

Unsafe-claim rows are visible and blocked. They are not reloaded as truth.

Unsafe claims include validation success, validation failure, issue closure,
release mutation, bundled solver, dependency installation, solver execution,
trust restoration, and certification claims.

## Evidence/History Retention

Evidence/history rows retain deactivation/reactivation history and historical
evidence as reference only. Skipped-missing remains skipped-missing. Reload is
not validation evidence.

The view-model performs no evidence deletion, no evidence rewrite, and implies
no issue closure.

## Trust/Provenance Boundary

Source rows show source type, source display, provenance label, trust label, and
whether a source reference was redacted.

User/plugin sources remain untrusted by default. Built-ins remain authoritative
by default. A trust label is not certification. Reload is not trust restoration
and is not validation evidence.

## Diagnostics

The view-model reserves and surfaces `OSPMG_RELOAD_*` diagnostics, including:

- `OSPMG_RELOAD_PAYLOAD_KIND_MISMATCH`
- `OSPMG_RELOAD_SCHEMA_VERSION_REQUIRED`
- `OSPMG_RELOAD_SCHEMA_UNSUPPORTED`
- `OSPMG_RELOAD_SCHEMA_MIGRATION_REQUIRED`
- `OSPMG_RELOAD_REDACTION_REQUIRED`
- `OSPMG_RELOAD_UNREDACTED_PATH_BLOCKED`
- `OSPMG_RELOAD_SECRET_LIKE_CONTENT_BLOCKED`
- `OSPMG_RELOAD_ACK_REQUIRED`
- `OSPMG_RELOAD_ACK_EXPIRED`
- `OSPMG_RELOAD_STALE_SOURCE_REPREVIEW_REQUIRED`
- `OSPMG_RELOAD_UNTRUSTED_SOURCE`
- `OSPMG_RELOAD_CONFLICT_VISIBLE`
- `OSPMG_RELOAD_SHARED_STACK_VISIBLE`
- `OSPMG_RELOAD_UNSAFE_CLAIM_BLOCKED`
- `OSPMG_RELOAD_EVIDENCE_RETAINED`
- `OSPMG_RELOAD_HISTORY_RETAINED`
- `OSPMG_RELOAD_NOT_VALIDATION`
- `OSPMG_RELOAD_NOT_TRUST_RESTORE`
- `OSPMG_RELOAD_NOT_AUTOMATIC_ACTIVATION`
- `OSPMG_RELOAD_NO_DISCOVERY_EXECUTION`
- `OSPMG_RELOAD_NO_PLUGIN_IMPORT`
- `OSPMG_RELOAD_NO_VALIDATION_EXECUTION`
- `OSPMG_RELOAD_NO_SOLVER_EXECUTION`
- `OSPMG_RELOAD_PROJECT_SCHEMA_MUTATION_DISABLED`
- `OSPMG_RELOAD_FUTURE_GATE`

These diagnostics are not validation success and not validation failure.

## Action States

All reload action states are disabled or future-only in this gate:

- read reload file;
- parse reload file;
- migrate schema;
- accept reload as trusted;
- activate reloaded candidate;
- refresh discovery;
- validate solver;
- execute solver;
- install dependency;
- uninstall dependency;
- uninstall solver;
- mutate ProjectSchema;
- create export summary;
- create report file;
- create reloadable bundle;
- copy to clipboard;
- attach to report;
- open output folder;
- close issue;
- mutate release;
- push tag;
- upload asset;
- claim validation success/failure;
- claim certification.

## Mapping/Text Output Behavior

`to_mapping()` returns deterministic JSON-compatible data for summary, sources,
candidates, acknowledgements, schema, redaction, stale sources, conflicts,
unsafe claims, evidence/history, diagnostics, actions, safety text, and reserved
diagnostic codes.

`to_text_lines()` returns stable plain-text review lines with safety boundaries.
Neither output is a reloadable bundle, validation evidence, trust restoration,
issue closure evidence, release mutation, or certification.

## Relationship to State Writer

The state writer creates explicit local UX state files using caller-supplied
paths and acknowledgement-gated preflight. This reload view-model consumes only
caller-supplied payload mappings shaped like that writer output.

The reload view-model does not read the state file itself, parse JSON from disk,
choose paths, reload from default paths, treat written state as validation
evidence, restore trust, or activate candidates.

## Relationship to Export Summary

Export summary is human-review output. Reload view-model is machine-readable
UX-state review over a supplied payload mapping.

Export summaries are not reloadable bundles. The reload view-model does not
consume export-summary output as authoritative persisted state unless a future
explicit bundle/report gate says otherwise.

## Relationship to ProjectSchema

The reload view-model performs no ProjectSchema mutation. Reloaded state is not
ProjectSchema state and is not project validation evidence. Any future
ProjectSchema integration requires a separate gate.

## Relationship to Live Optional Validation Issues

Issues #6 through #11 remain open. Reload does not close issues. Reloaded state
is not live optional validation. Skipped-missing remains skipped-missing.
Prepared-machine validation remains a separate gate.

## Non-Actions

This gate does not:

- add a file reader/parser implementation;
- perform runtime file reading;
- parse runtime state from paths;
- choose a default reload path;
- perform background reload;
- create reloadable bundles;
- add GUI behavior;
- add CLI behavior;
- mutate ProjectSchema;
- add live discovery;
- add passive refresh;
- import plugin packages;
- scan directories;
- fetch network manifests;
- run validation;
- execute solvers;
- install dependencies;
- uninstall dependencies;
- uninstall solvers;
- automatically activate candidates;
- restore trust;
- mutate issues;
- mutate releases;
- mutate tags;
- mutate assets;
- bump versions;
- claim validation-pass;
- claim validation-fail;
- claim issue closure;
- claim bundled solver support;
- claim certification.

## Testing Strategy

Focused unit tests cover:

- import without GUI/CLI extras;
- absence of forbidden runtime imports and file-reading behavior;
- unavailable/empty state;
- mapping-only valid payload review;
- path-like source label redaction;
- payload-kind/schema/migration blockers;
- redaction, unredacted path, and secret-like blockers;
- missing/expired acknowledgement blockers;
- stale-source, conflict, shared-stack, and unsafe-claim blockers;
- candidate lifecycle review-only/future-review behavior;
- evidence/history retention and skipped-missing preservation;
- user/plugin untrusted boundary and built-in authority;
- non-validation/non-trust/non-activation diagnostics;
- disabled/future-only actions;
- deterministic mapping/text output;
- input mapping immutability;
- no file creation.

Adjacent state-writer, state-writer view-model, persistence schema-model,
persistence view-model, export-summary view-model, and reload design-doc tests
remain part of the gate validation.

## OSW-EXP-108 GUI Design Follow-Up

OSW-EXP-108 designs a future GUI review surface for this view-model. That design
requires future GUI code to consume already-built reload view-model records and
remain read-only/review-only. It does not authorize file dialogs, file
reader/parser behavior, runtime reload, ProjectSchema mutation, discovery,
validation, solver execution, automatic activation, trust restoration,
issue/release mutation, or certification claims.

## Future Gates

Future gates remain separate:

- `OSW-EXP-108_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_DESIGN`
- `OSW-EXP-109_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_IMPLEMENTATION`
- `OSW-EXP-110_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_CLI_DESIGN`
- `OSW-EXP-111_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_CLI_IMPLEMENTATION`
- `OSW-EXP-112_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_FILE_READER_IMPLEMENTATION`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` if a prepared
  machine is available
