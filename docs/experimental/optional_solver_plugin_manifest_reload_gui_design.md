# Optional Solver Plugin Manifest Reload GUI Design

## Status

This gate is design-only.

It adds no reload GUI implementation, no GUI source edits, no runtime behavior
added, and no source behavior mutation. It adds no file dialog behavior, no
file reading implementation, no file parsing implementation, no runtime reload
behavior, no default reload path, no background reload, no reloadable bundle
creation, no export file creation, no report file creation, no clipboard
behavior, no report attachment, no open-output-folder behavior, no CLI behavior,
and no ProjectSchema mutation.

It also adds no live discovery, no passive refresh, no plugin package import,
no directory scan, no network fetch, no validation execution, no solver
execution, no dependency installation, no dependency uninstall, no solver
uninstall, no automatic activation, no trust restoration, no issue mutation, no
release mutation, no tag mutation, no asset mutation, no version bump, no
validation-pass claim, no validation-fail claim, no issue-closure claim, no
bundled-solver claim, and no certification claim.

## Purpose

This document defines a future PySide review surface for OSW-EXP-107 reload
view-model state. The future surface is a read-only, preview-first GUI contract
for already-built reload view-model records.

The design preserves the OSW-EXP-106 reload design, the OSW-EXP-107 reload
view-model, persistence GUI boundaries, export-summary GUI boundaries,
persistence and export-summary CLI boundaries, ProjectSchema boundaries,
discovery boundaries, validation boundaries, issue/release boundaries, and
certification boundaries.

## Current State Before Reload GUI

Reload design exists. A pure reload view-model exists. Persistence GUI review
panel behavior exists for persistence review. Export-summary GUI review panel
behavior exists for human-readable export-summary review. Persistence CLI and
export-summary CLI behavior exist with bounded non-validation semantics. The
state writer exists for explicit local UX state files.

No reload GUI exists. No file reader/parser exists for reload. No runtime
reload behavior exists. No file dialog for reload exists. User/plugin manifests
remain untrusted by default, and reload state remains non-validating.

## Definition Of Reload GUI

Reload GUI means a future read-only, preview-first review surface over
already-built reload view-model records. The panel may render the summary and
readiness, source/provenance, schema/migration state, candidate lifecycle review,
acknowledgements and expiry, redaction/privacy blockers, stale-source/re-preview
state, conflicts/shared-stack warnings, unsafe claims, evidence/history,
trust/provenance boundaries, diagnostics, disabled/future action states, and
safety guidance.

Reload GUI must not read files, parse files, choose default paths, run reload,
activate candidates, restore trust, run discovery, run validation, execute
solvers, install dependencies, uninstall dependencies, uninstall solvers, mutate
ProjectSchema, close issues, mutate releases, push tags, upload assets, or claim
certification.

## Non-Meaning Of GUI Reload Review

GUI reload review is not validation success. GUI reload review is not validation
failure. GUI reload review is not trust restoration. GUI reload review is not
automatic activation. GUI reload review is not discovery success. GUI reload
review is not dependency installation. GUI reload review is not solver
execution. GUI reload review is not ProjectSchema mutation. GUI reload review is
not issue closure. GUI reload review is not release mutation. GUI reload review
is not certification. GUI reload review is not report generation. GUI reload
review is not reloadable bundle creation.

## Future User Flow

Future GUI states should mirror the OSW-EXP-107 reload view-model vocabulary:

- `no_reload_request`
- `no_payload`
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

These states describe review readiness only. They do not authorize reload
acceptance, ProjectSchema mutation, activation, discovery refresh, validation,
solver execution, or issue/release mutation.

## Data Input Policy

The future panel receives already-built reload view-model objects. It does no
direct file path opening, no JSON parsing in panel code, no filesystem
inspection, no directory scan, no network fetch, and no plugin import. File
dialog and file reader behavior stays future-gated. Source labels must already
be redacted before display or must be rendered through redacted display fields
provided by the view-model.

## Layout And Rendered Sections

The future GUI should expose predictable sections or tabs:

- Summary
- Source / Provenance
- Schema / Migration
- Candidates
- Acknowledgements / Expiry
- Redaction / Privacy
- Stale Sources / Re-preview
- Conflicts / Shared Stack
- Unsafe Claims
- Evidence / History
- Trust
- Diagnostics
- Actions
- Safety Guidance

The design favors read-only tables and plain text panels, consistent with the
existing persistence and export-summary review panels.

## Summary/Readiness Display

The summary/readiness display should show state, readiness, payload kind,
payload schema version, writer version, source display, redacted source flag,
candidate counts, acknowledgement counts, diagnostic counts, blocker counts, and
warning counts.

Honesty flags must be visible and false for validation evidence, validation
failure, trust restoration, automatic activation, discovery execution, plugin
package import, validation execution, solver execution, ProjectSchema mutation,
issue closure, release mutation, and certification.

## Source/Provenance Display

The source/provenance display should show source type, redacted source
reference, `source_reference_redacted`, provenance label, trust label, and
source display. User/plugin sources are untrusted by default. Built-ins are
authoritative by default. Trust label is not certification.

## Schema/Migration Display

The schema/migration display should show that payload kind is required, payload
schema version is required, unsupported schema blocks reload review, and
migration-required blocks reload review. Schema mismatch is not validation
failure. The persistence schema model remains separate from ProjectSchema.
Migration is future-gated.

## Candidate Lifecycle Display

The candidate lifecycle display should show persisted lifecycle state and reload
review state. Inactive preview remains review-only. Persisted active requires
future activation review. Deactivated remains deactivated review state.
Reactivation routes to future activation review. Discovery-refresh state remains
review state. The GUI provides no automatic activation and no trust restoration.

## Acknowledgement And Expiry Display

The acknowledgement and expiry display should include:

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

Expiry reasons shown by the future GUI should include reload, source fingerprint
change, schema version change, unsafe claim appearance, trust policy change, and
future discovery-refresh result.

## Redaction/Privacy Display

The redaction/privacy display should state that raw paths are hidden by default.
Basename, hash, source-id, or display-name fields are preferred. Home
directories, environment variables, secrets, tokens, and API keys are blocked.
Unredacted paths require future policy. Fingerprints are not trust signals.
Redaction review happens before activation review.

## Stale-Source/Re-Preview Display

The stale-source/re-preview display should show that old preview is not silently
trusted and that missing, moved, or changed sources require re-preview. The GUI
does no source IO from GUI code. Stale-source state is not validation failure.
Re-preview remains future-gated.

## Conflict/Shared-Stack Display

The conflict/shared-stack display should make conflicts visible. Built-ins win
by default. Persisted state does not override built-ins. Shared-stack warnings
are visible. The GUI does not resolve conflicts. Future policy is required for
conflict resolution.

## Unsafe-Claim Display

Unsafe claims are visible and blocked. They are not displayed as truth. Unsafe
claims include validation success. Unsafe claims include validation failure.
Unsafe claims also include issue closure, release mutation, bundled solver,
dependency installation, solver execution, trust restoration, and certification.

## Evidence/History Display

The evidence/history display should retain deactivation/reactivation history and
historical evidence as reference only. Skipped-missing remains skipped-missing.
Reload is not validation evidence. The GUI does no evidence deletion/rewrite and
implies no issue closure.

## Diagnostics Display

The diagnostics display renders `OSPMG_RELOAD_*` diagnostics with severity,
code, message, section, blocker/warning status, and redacted context. Diagnostic
rows must never be presented as validation success or validation failure.

Representative codes include `OSPMG_RELOAD_NOT_IMPLEMENTED`,
`OSPMG_RELOAD_DESIGN_ONLY`, `OSPMG_RELOAD_TARGET_REQUIRED`,
`OSPMG_RELOAD_PAYLOAD_KIND_MISMATCH`, `OSPMG_RELOAD_SCHEMA_UNSUPPORTED`,
`OSPMG_RELOAD_SCHEMA_MIGRATION_REQUIRED`, `OSPMG_RELOAD_REDACTION_REQUIRED`,
`OSPMG_RELOAD_UNREDACTED_PATH_BLOCKED`,
`OSPMG_RELOAD_SECRET_LIKE_CONTENT_BLOCKED`, `OSPMG_RELOAD_ACK_REQUIRED`,
`OSPMG_RELOAD_ACK_EXPIRED`, `OSPMG_RELOAD_STALE_SOURCE_REPREVIEW_REQUIRED`,
`OSPMG_RELOAD_UNTRUSTED_SOURCE`, `OSPMG_RELOAD_CONFLICT_VISIBLE`,
`OSPMG_RELOAD_SHARED_STACK_VISIBLE`, `OSPMG_RELOAD_UNSAFE_CLAIM_BLOCKED`,
`OSPMG_RELOAD_EVIDENCE_RETAINED`, `OSPMG_RELOAD_HISTORY_RETAINED`,
`OSPMG_RELOAD_NOT_VALIDATION`, `OSPMG_RELOAD_NOT_TRUST_RESTORE`,
`OSPMG_RELOAD_NOT_AUTOMATIC_ACTIVATION`,
`OSPMG_RELOAD_NO_DISCOVERY_EXECUTION`, `OSPMG_RELOAD_NO_PLUGIN_IMPORT`,
`OSPMG_RELOAD_NO_VALIDATION_EXECUTION`, `OSPMG_RELOAD_NO_SOLVER_EXECUTION`,
`OSPMG_RELOAD_PROJECT_SCHEMA_MUTATION_DISABLED`, and
`OSPMG_RELOAD_FUTURE_GATE`.

## Action-State Model

The future GUI should render disabled/future actions for:

- choose reload file
- read reload file
- parse reload file
- migrate schema
- accept reload as trusted
- activate reloaded candidate
- refresh discovery
- validate solver
- execute solver
- install dependency
- uninstall dependency
- uninstall solver
- mutate ProjectSchema
- create export summary
- create report file
- create reloadable bundle
- copy to clipboard
- attach to report
- open output folder
- close issue
- mutate release
- push tag
- upload asset
- claim validation success/failure
- claim certification

The action-state model is display-only in this design gate.

## Future File-Dialog Boundary

There is no file dialog in this design gate. Future file dialog behavior
requires a separate gate. A future file dialog may only select an explicit user
path and must not imply load, activation, trust restoration, discovery,
validation, solver execution, or ProjectSchema mutation. There is no default
path and no background reload.

## Future Reload Acceptance Boundary

Accepting or reviewing reload remains future-gated. An accepted reload, if a
future gate defines it, is still review state. Activation requires a separate
activation review. Discovery refresh requires a separate explicit gate.
Validation remains separate. ProjectSchema mutation remains separate.

## Relationship To Reload View-Model

The future GUI consumes OSW-EXP-107 view-model records. The GUI must not mutate
them. The GUI must not create reload records from file paths. GUI and CLI should
share semantics through the reload view-model, not through widgets.

## Relationship To Persistence GUI And State Writer

Persistence GUI reviews write-plan and persistence state. The state writer
writes explicit local UX state files through caller-supplied paths. Reload GUI
reviews reloaded state. Reload GUI does not write files.

## Relationship To Export Summary GUI/CLI

Export summary is human-review output. Reload GUI is machine-readable UX-state
review. Export summaries are not reloadable bundles. Reload GUI does not create
reports or export files.

## Relationship To ProjectSchema

There is no ProjectSchema mutation. Reloaded state is not ProjectSchema state.
Reloaded state is not project validation evidence. Future ProjectSchema
integration requires a separate gate.

## Relationship To Live Optional Validation Issues

Issues #6 through #11 remain open. Reload GUI does not close issues. Reload GUI
output is not live optional validation. Skipped-missing remains skipped-missing.
Prepared-machine validation remains separate.

## Non-Actions

This gate does not implement reload GUI, edit GUI source, edit runtime source,
edit CLI source, add file dialog, read persisted state files, parse persisted
state files, add runtime reload behavior, add default reload path, add
background reload, create reloadable bundles, create export files, create report
files, add clipboard behavior, add report attachment, add open-output-folder
behavior, mutate ProjectSchema, add live discovery, add passive refresh, import
plugin packages, scan directories, fetch network manifests, run validation, run
solver execution, install dependencies, uninstall dependencies, uninstall
solvers, automatically activate candidates, restore trust, mutate issues,
mutate releases, mutate tags, mutate assets, bump version, claim
validation-pass, claim validation-fail, claim issue closure, claim bundled
solver, or claim certification.

## Future Implementation Test Plan

Future OSW-EXP-109 must test that panel imports are guarded by PySide
availability, that the panel consumes an existing reload view-model, and that
all sections render. It must test no file dialog, no file reader/parser, no raw
path leak, no automatic activation, no trust restoration, no ProjectSchema
mutation, no discovery, no validation, no solver execution, disabled/future
actions displayed, diagnostics visible, skipped-missing preserved, and
source/provenance/trust visible.

## OSW-EXP-109 Implementation Follow-Up

OSW-EXP-109 implements
`OptionalSolverPluginManifestReloadPanel` as a read-only/review-only PySide
surface over already-built reload view-model records. The implementation keeps
the design boundary: no file dialog, no file reader/parser, no runtime reload,
no ProjectSchema mutation, no discovery/validation/solver execution, no
automatic activation, no trust restoration, no issue/release mutation, and no
certification claim.

## Future Gates

Suggested sequence:

- `OSW-EXP-109_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_IMPLEMENTATION`
- `OSW-EXP-110_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_CLI_DESIGN`
- `OSW-EXP-111_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_CLI_IMPLEMENTATION`
- `OSW-EXP-112_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_FILE_READER_DESIGN`
- `OSW-EXP-113_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_FILE_READER_IMPLEMENTATION`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` if a prepared
  machine is available

If repository numbering changes, future gates should follow the latest accepted
decision-log sequence while preserving the boundaries in this document.
