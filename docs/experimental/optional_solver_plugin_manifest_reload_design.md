# Optional Solver Plugin Manifest Reload Design

## Status

This gate is design-only. It adds no reload implementation, no runtime behavior,
and no source edits.

The design adds no source behavior mutation, no file parsing implementation, no
file reading implementation, no runtime state loading implementation, no default
path, no background reload, and no reloadable bundle creation.

This gate adds no GUI behavior, no CLI behavior, no ProjectSchema mutation, no
export/report/clipboard/open-folder behavior, no live discovery, no passive
refresh, no plugin package import, no directory scan, no network fetch, no
validation execution, no solver execution, no dependency installation, no
dependency uninstall, no solver uninstall, no issue mutation, no release
mutation, no tag mutation, no asset mutation, no version bump, no
validation-pass claim, no validation-fail claim, no issue-closure claim, no
bundled-solver claim, and no certification claim.

## Purpose

This document defines future reload semantics for local persisted optional
solver plugin manifest UX state.

Reload must preserve state-writer, persistence CLI, export-summary CLI, GUI,
ProjectSchema, discovery, validation, issue/release, and certification
boundaries. Reload is distinct from validation evidence, trust restoration,
automatic activation, discovery success, ProjectSchema state, issue closure,
release mutation, and certification.

## Current State Before Reload

Persistence design exists in
[optional_solver_plugin_manifest_state_persistence_design.md](optional_solver_plugin_manifest_state_persistence_design.md).
The persistence view-model exists in
[optional_solver_plugin_manifest_persistence_viewmodel.md](optional_solver_plugin_manifest_persistence_viewmodel.md).
The persistence schema model exists in
[optional_solver_plugin_manifest_persistence_schema_model.md](optional_solver_plugin_manifest_persistence_schema_model.md).
The persistence GUI review panel exists in
[optional_solver_plugin_manifest_persistence_gui_implementation.md](optional_solver_plugin_manifest_persistence_gui_implementation.md).

The state-writer design, view-model, and writer exist in
[optional_solver_plugin_manifest_state_writer_design.md](optional_solver_plugin_manifest_state_writer_design.md),
[optional_solver_plugin_manifest_state_writer_viewmodel.md](optional_solver_plugin_manifest_state_writer_viewmodel.md),
and
[optional_solver_plugin_manifest_state_writer_implementation.md](optional_solver_plugin_manifest_state_writer_implementation.md).
The persistence CLI exists for explicit state writing in
[optional_solver_plugin_manifest_persistence_cli_implementation.md](optional_solver_plugin_manifest_persistence_cli_implementation.md).
Export-summary view-model, GUI, and CLI surfaces exist for human-readable
review in
[optional_solver_plugin_manifest_export_summary_viewmodel.md](optional_solver_plugin_manifest_export_summary_viewmodel.md),
[optional_solver_plugin_manifest_export_summary_gui_implementation.md](optional_solver_plugin_manifest_export_summary_gui_implementation.md),
and
[optional_solver_plugin_manifest_export_summary_cli_implementation.md](optional_solver_plugin_manifest_export_summary_cli_implementation.md).

No reload implementation exists. No reload GUI exists. No reload CLI exists. No
runtime state-file parser exists for this line. No ProjectSchema mutation exists
for this line. User/plugin manifests remain untrusted and non-validating.

Implementation follow-up: OSW-EXP-107 adds a pure, mapping-only reload
view-model in
[optional_solver_plugin_manifest_reload_viewmodel.md](optional_solver_plugin_manifest_reload_viewmodel.md).
It consumes caller-supplied in-memory payload mappings only and still adds no
file reader/parser, runtime reload behavior, GUI behavior, CLI behavior,
ProjectSchema mutation, discovery, validation, solver execution, automatic
activation, trust restoration, issue mutation, release mutation, or
certification claim.

## Definition of Reload

Future reload is an explicit user-requested transformation from a
caller-selected persisted UX state file into an in-memory candidate review
state.

Reload may eventually:

- read a caller-selected state file;
- parse deterministic JSON-like persisted UX state;
- verify schema version;
- verify payload kind;
- verify redaction metadata;
- surface source/provenance;
- surface candidate lifecycle state;
- surface acknowledgements and expiry;
- surface stale-source/re-preview requirements;
- surface conflicts/shared stacks;
- surface unsafe claims;
- surface evidence/history retention;
- surface diagnostics and limitations;
- produce review-only candidate state.

Reload must never automatically activate candidates, restore trust, run
discovery, import plugin packages, install dependencies, execute solvers, mutate
ProjectSchema, close issues, mutate releases/tags/assets, or claim
certification.

## Reload Non-Meaning

Reload is not validation success. Reload is not validation failure. Reload is
not trust restoration. Reload is not automatic activation. Reload is not
discovery success. Reload is not dependency installation. Reload is not solver
execution. Reload is not ProjectSchema mutation. Reload is not issue closure.
Reload is not release mutation. Reload is not certification. Reload is not
export summary. Reload is not report generation. Reload is not reloadable bundle
creation.

## Future User Flow States

Future reload UX and CLI surfaces should use explicit states:

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

## State Source and Path Policy

Future reload accepts an explicit caller-selected file only. There is no default
path and no background reload. Reload does not perform a directory scan, plugin
folder scan, network fetch, automatic discovery, or ProjectSchema path mutation.
That means no plugin folder scan is part of reload.

Future implementation must reject directories, missing targets, symlink
ambiguity, unsupported extension/payload, unsafe paths, and secret-like
references. Future implementation must preserve redacted target display.

## Payload/Schema Policy

Reload payloads require `payload_kind` and `payload_schema_version`. Future
reload must review `writer_version`, run a schema support check, and block when
schema migration is required.

Schema migration is a separate future gate. Schema mismatch is not validation
failure. The schema model remains separate from ProjectSchema. This gate creates
no schema file.

## Redaction/Privacy Policy

Raw absolute paths are hidden by default. Basename, hash, source-id, and display
name forms are preferred. Home directories, environment variables, secrets,
tokens, and API keys are blocked. Unredacted paths require explicit future
policy. Fingerprints are not trust signals.

Redaction review is required before activation review. Reload must not leak raw
paths in diagnostics by default.

## Acknowledgement and Expiry Policy

Future reload acknowledgement rows include:

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

Acknowledgements expire on reload, source fingerprint change, schema version
change, unsafe claim appearance, trust policy change, and future
discovery-refresh result.

## Candidate Lifecycle Reload Policy

Inactive preview state remains review-only. Persisted active candidate state
does not mean active after reload. Deactivated state remains deactivated review
state. Reactivation state routes to future activation review. Discovery-refresh
state remains review state.

Persisted active state requires future activation review. Persisted
acknowledgement state may be expired. Reload performs no automatic activation
and no trust restoration.

## Stale-Source / Re-Preview Policy

Old preview data is not silently trusted. Missing, moved, or changed sources
require re-preview. This design gate performs no source file IO. Future reload
implementation may only surface stale-source state; it must not fix it silently.
Stale-source state is not validation failure.

## Conflict/Shared-Stack Policy

Conflicts are visible. Built-ins win by default. Persisted state does not
override built-ins. Shared-stack warnings are visible. Reload does not resolve
conflicts. Future policy is required for conflict resolution.

## Unsafe-Claim Policy

Unsafe claims are visible and blocked. Unsafe claims are not reloaded as truth.
Unsafe claims include validation success/failure, issue closure, release
mutation, bundled solver, dependency installation, solver execution, trust
restoration, and certification claims.

## Evidence/History Retention

Deactivation history is retained. Reactivation history is retained. Historical
evidence is retained as reference only. Skipped-missing remains skipped-missing.
Reload is not validation evidence. Reload performs no evidence deletion/rewrite.
Reload implies no issue closure.

## Trust/Provenance Boundary

Source type is visible. Trust label is visible. User/plugin manifests are
untrusted by default. Built-ins are authoritative by default. Trust label is not
certification. Reload is not trust restoration. Reload is not validation
evidence.

## Diagnostics Model

Future reload may reserve these diagnostics:

- `OSPMG_RELOAD_NOT_IMPLEMENTED`
- `OSPMG_RELOAD_DESIGN_ONLY`
- `OSPMG_RELOAD_TARGET_REQUIRED`
- `OSPMG_RELOAD_TARGET_MISSING`
- `OSPMG_RELOAD_TARGET_IS_DIRECTORY`
- `OSPMG_RELOAD_TARGET_SYMLINK_REVIEW_REQUIRED`
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

## Action-State Model

The reload action-state model marks these actions disabled/future-gated:

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

## Future GUI Behavior Boundary

There is no GUI implementation in this gate. Future GUI must be preview-first
and review-first. File dialog behavior requires a separate gate. Accepting a
reload remains review-only unless a future activation gate explicitly allows
otherwise.

Future GUI must not run discovery, validation, or solver execution. Future GUI
must not mutate ProjectSchema or issues/releases.

## Future CLI Behavior Boundary

There is no CLI implementation in this gate. Future CLI must be explicit path
only. Its default should be explain/preview. It must provide no default path, no
background reload, no live discovery, no validation, and no solver execution.
Exit codes must not imply validation success.

## Relationship to State Writer

The state writer creates explicit local UX state files. Reload consumes only
future-compatible explicit state files. Written state is not validation
evidence. Reloaded state is not trust restoration or automatic activation.
Writer payload schema must be checked before reload.

## Relationship to Export Summary

Export summary is human-review output. Reload is machine-readable UX state
review. Export summaries are not reloadable bundles. Reload does not consume an
export summary as authoritative persisted state unless a future explicit
bundle/report gate says otherwise.

## Relationship to ProjectSchema

Reload performs no ProjectSchema mutation. Reloaded state is not ProjectSchema
state. Reloaded state is not project validation evidence. Future ProjectSchema
integration requires a separate gate.

## Relationship to Live Optional Validation Issues

Issues #6 through #11 remain open. Reload does not close issues. Reloaded state
is not live optional validation. Skipped-missing remains skipped-missing.
Prepared-machine validation remains separate.

## Non-Actions

This gate does not:

- implement reload;
- edit runtime source;
- edit CLI source;
- edit GUI source;
- read persisted state files at runtime;
- parse persisted state files at runtime;
- create reloadable bundles;
- create export files;
- create report files;
- add clipboard behavior;
- add report attachment;
- add open-output-folder behavior;
- add GUI behavior;
- add CLI behavior;
- add ProjectSchema mutation;
- add live discovery;
- add passive refresh;
- import plugin packages;
- scan directories;
- fetch network manifests;
- run validation;
- run solver execution;
- install dependencies;
- uninstall dependencies;
- uninstall solvers;
- mutate issues;
- mutate releases;
- mutate tags;
- mutate assets;
- bump version;
- claim validation-pass;
- claim validation-fail;
- claim issue closure;
- claim bundled solver;
- claim certification.

## Future Implementation Test Plan

Future OSW-EXP-107 and later gates must test:

- schema-supported reload view-model;
- unsupported schema blocker;
- migration-required blocker;
- redaction blocker;
- unredacted-path blocker;
- secret-like content blocker;
- expired acknowledgement blocker;
- stale-source/re-preview blocker;
- conflict/shared-stack display;
- unsafe-claim blocker;
- evidence/history retention;
- skipped-missing preservation;
- no automatic activation;
- no trust restoration;
- no ProjectSchema mutation;
- no discovery;
- no validation;
- no solver execution;
- no issue/release mutation;
- no raw path leak.

## OSW-EXP-108 Follow-Up

OSW-EXP-108 adds the reload GUI design as a review-only contract over
already-built reload view-model records. It does not add GUI source, file dialog
behavior, file reading/parsing, runtime reload behavior, ProjectSchema mutation,
discovery, validation, solver execution, automatic activation, trust
restoration, issue/release mutation, or certification claims.

## Future Gates

Suggested future gates:

- `OSW-EXP-107_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_VIEWMODEL`
- `OSW-EXP-108_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_DESIGN`
- `OSW-EXP-109_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_IMPLEMENTATION`
- `OSW-EXP-110_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_CLI_DESIGN`
- `OSW-EXP-111_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_CLI_IMPLEMENTATION`
- `OSW-EXP-112_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_FILE_READER_IMPLEMENTATION`
  if file parsing is intentionally split out
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` if a prepared
  machine is available
