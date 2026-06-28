# Optional solver plugin manifest state writer design

## 1. Status

Design-only.

No runtime behavior is added in this gate. No writer implementation is added in
this gate. This document defines future optional solver plugin manifest state
writer safety semantics before any writer exists.

Status boundaries:

- no runtime behavior
- no writer implementation
- no file writes
- no runtime state file creation
- no settings file creation
- no schema file creation
- no export file creation
- no report file creation
- no reloadable bundle creation
- no ProjectSchema mutation
- no GUI behavior
- no CLI behavior
- no reload behavior
- no export behavior
- no clipboard behavior
- no report attachment
- no open-output-folder behavior
- no file dialog
- no save dialog
- no activation/deactivation/reactivation/discovery-refresh/persistence/export
  source mutation
- no automatic activation
- no trust restoration
- no manifest file restoration
- no manifest file restore
- no manifest file rewrite
- no manifest file deletion
- no file restoration
- no file restore
- no file rewrite
- no file deletion
- no dependency installation
- no dependency install
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
- no validation failure claim
- no issue-closure claim
- no certification claim

## Implementation follow-up: state writer view-model (OSW-EXP-101)

OSW-EXP-101 implements the first pure in-memory state-writer readiness and
write-plan view-model:
[optional_solver_plugin_manifest_state_writer_viewmodel.md](optional_solver_plugin_manifest_state_writer_viewmodel.md).
It adds deterministic storage-option, schema/migration, redaction,
acknowledgement, stale-source, conflict/shared-stack, unsafe-claim,
evidence/history, atomicity/error-plan, non-action flag, diagnostic, and
disabled/future action records.

The implementation remains non-writing: no writer implementation, no file
writes, no directory creation, no runtime state files, no settings files, no
schema files, no export/report files, no reloadable bundles, no ProjectSchema
mutation, no GUI behavior, no CLI behavior, no reload/export behavior, no
discovery execution, no validation execution, no solver execution, and no
issue/release/tag/asset mutation.

## 2. Purpose

Define future writer semantics for optional solver plugin manifest UX state.

The state writer design preserves the OSW-EXP-090 state persistence design,
OSW-EXP-092 persistence view-model, OSW-EXP-093 persistence schema model,
OSW-EXP-095 persistence GUI, OSW-EXP-096 persistence CLI design, OSW-EXP-097
export-summary view-model, OSW-EXP-099 export-summary GUI, and optional
solver/plugin manifest safety boundaries.

The future writer must remain distinct from validation evidence, trust
restoration, automatic activation, solver discovery, dependency installation,
dependency uninstall, solver uninstall, solver execution, issue closure, release
mutation, tag mutation, asset mutation, export summaries, reloadable bundles,
ProjectSchema state, validation-pass claims, validation-fail claims, issue-closure
claims, bundled-solver claims, and certification.

Persisted manifest UX state would be a local review record. It is not validation
evidence. It is not trust restoration. It is not automatic activation. It is not
solver discovery success. It is not dependency installation. It is not solver
execution. It is not issue closure. It is not release mutation. It is not
certification.

## 3. Current state before state writer

- Persistence design exists from OSW-EXP-090.
- Pure persistence view-model exists from OSW-EXP-092.
- Pure in-memory persistence schema model exists from OSW-EXP-093.
- Persistence GUI review panel exists from OSW-EXP-095.
- Persistence CLI design exists from OSW-EXP-096.
- Export-summary view-model exists from OSW-EXP-097.
- Export-summary GUI review panel exists from OSW-EXP-099.
- No state writer exists.
- No state file write path exists.
- No reload behavior exists.
- No ProjectSchema persistence integration exists.
- No settings file path exists for this optional solver plugin manifest line.
- No export writer exists.
- No reloadable bundle writer exists.
- User/plugin manifests remain untrusted and non-validating.
- Built-ins remain authoritative by default.

Issues `#6` through `#11` remain open. Package metadata remains `0.1.5rc1`.
The public prerelease remains `v0.1.5-rc1`.

## 4. Definition of state writer

A future state writer is a gated, explicit, redaction-first writer for local
optional solver plugin manifest UX state.

It may eventually write a local state record containing:

- schema version
- writer version
- state scope
- redacted source references
- source ids and source types
- trust labels
- activation/deactivation/reactivation/discovery-refresh/persistence state
  summaries
- acknowledgement state and expiry metadata
- stale-source/re-preview metadata
- conflict/shared-stack summaries
- unsafe-claim blockers
- evidence/history references
- diagnostics and limitations
- non-action flags
- migration notes

It must never write:

- raw secrets
- API keys or tokens
- unrestricted absolute paths
- plugin code
- solver binaries
- install scripts
- executable commands
- validation-pass claims
- validation-fail claims
- issue-closure claims
- release/tag/asset mutation commands
- certification claims
- unreviewed third-party manifest trust assertions
- raw VLM or solver execution instructions

## 5. Future storage-location options

This design discusses storage-location options without choosing an
implementation. No default write path exists in this gate, and all options remain
disabled until an explicit implementation gate.

| Option | Potential use | Main risks |
| --- | --- | --- |
| Project-local `.osw/optional_solver_manifest_state.json` | Portable local project review state. | Privacy leaks, accidental trust restoration, stale state after source movement, ProjectSchema confusion, cleanup ambiguity, and test determinism risk. |
| User-profile/cache location | Local user preference and acknowledgement review state. | Harder portability, profile cleanup behavior, stale cross-project state, and accidental shared-stack trust confusion. |
| Session-local ephemeral file | Temporary diagnostics during an explicit future workflow. | Cleanup behavior and user confusion if it looks durable. |
| Explicit user-chosen file | User-controlled storage. | File dialog/save dialog policy, path privacy, portability, overwrite behavior, and export/reloadable-bundle confusion. |
| No default write path | Safest default until implementation. | Requires explicit future user flow and may frustrate users expecting persistence. |

Every option must treat persisted state as non-validating, non-trust-restoring,
non-activating, non-installing, non-executing, issue/release-safe, and separate
from ProjectSchema.

## 6. File format boundary

The future format is conceptual only:

- versioned JSON-like state
- schema version required
- stable keys
- deterministic ordering
- redaction metadata
- diagnostics
- limitations
- migration notes
- checksum/fingerprint fields only when supplied by a caller
- non-action flags
- acknowledgement expiry metadata

No schema file is created in this gate. No actual JSON writer is implemented in
this gate. The file format boundary is a future contract for review and testing,
not current serialization behavior.

## 7. Write preconditions

A future writer must require:

- explicit user action
- explicit state scope
- supported schema version
- redaction review complete
- unredacted paths blocked or explicitly future-policy-approved
- secret-like content blocked
- required acknowledgements satisfied
- acknowledgement expiry visible
- stale-source/re-preview reviewed
- conflicts surfaced
- shared-stack warnings surfaced
- unsafe claims blocked
- history/evidence retention policy visible
- dry-run/write plan available
- non-actions visible
- user/plugin untrusted-by-default status preserved
- built-ins-authoritative-by-default policy preserved

These preconditions are future requirements only. This gate implements no
precondition checker and performs no writes.

## 8. Dry-run/write-plan model

Dry-run is required before any future write.

A future dry-run/write-plan model must:

- show the planned target path only when redacted or explicitly approved
- list planned sections, keys, counts, and diagnostics
- list acknowledgement and expiry state
- list conflicts, stale sources, unsafe claims, and limitations
- show non-action flags
- not write
- not create directories
- not create settings files
- not create runtime state files
- not create schema files
- not create export files
- not create report files
- not create reloadable bundles
- not mutate ProjectSchema
- not reload
- not export
- not copy to clipboard
- not attach reports
- not open output folders
- not import plugin packages
- not scan directories
- not fetch network manifests
- not run discovery
- not validate
- not run solvers

Dry-run success is not persistence success. Write-plan readiness is not
validation success and is not validation failure. A ready write plan is not trust
restoration, automatic activation, issue closure, release mutation, or
certification.

## 9. Redaction/privacy policy

The future writer is redaction-first.

Policy:

- raw absolute paths are hidden by default
- basename, hash, source id, display name, or redacted source reference is
  preferred
- home directories are redacted
- environment variables are redacted or blocked
- secrets, tokens, API keys, and secret-like content are blocked
- unredacted path persistence is blocked unless a future explicit policy gate
  defines approval semantics
- fingerprints are provenance hints, not trust
- a redaction report is part of the future write plan
- stored state must not leak unrestricted local machine layout

Redaction review is not validation. Redaction review is not trust restoration.

## 10. Acknowledgement model and expiry policy

The future writer must require explicit acknowledgement records before a write
can occur. Required acknowledgement concepts include:

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
- `state_writer_not_automatic_activation`
- `state_writer_not_reloadable_bundle`

Acknowledgements must expire on reload, source change, schema change, unsafe
claims, unreviewed conflicts, redaction policy changes, and future policy changes
that alter write semantics. Persisted acknowledgement state records that a
warning was shown; it does not grant permission to activate, trust, validate,
install, execute, close issues, mutate releases, mutate tags, mutate assets, or
certify anything.

## 11. Schema and migration behavior

A future writer must require a schema version. Missing, unsupported, or stale
schema versions are blockers.

Migration behavior:

- schema version is required
- unsupported schema is blocked
- migration-required state is visible
- migration notes are retained
- automatic migration is not implied
- migration review happens before any future write
- migration review does not mutate ProjectSchema
- migration review does not create schema files in this gate
- migration review is not reload behavior
- migration review is not export behavior

## 12. Stale-source and re-preview behavior

The future writer must treat stale, missing, moved, changed, or fingerprint-
mismatched sources as requiring re-preview. Old preview records are not silently
trusted.

Stale-source policy:

- stale source state blocks writing until reviewed by future policy
- re-preview requirements remain visible in state
- stale source handling does not restore files
- stale source handling does no file rewrite
- stale source handling does no file deletion
- stale source handling does not scan directories
- stale source handling does not fetch network manifests
- stale source handling does not run discovery
- stale source handling does not run validation
- stale source handling does not execute solvers

## 13. Conflict/shared-stack behavior

The future writer must preserve conflict and shared-stack context.

Policy:

- built-ins remain authoritative by default
- user/plugin manifests remain untrusted by default
- shared-stack warnings remain visible
- conflicts are blockers or explicit warnings under future policy
- persisted user/plugin state never silently overrides built-ins
- a persisted conflict summary is not activation
- a persisted conflict summary is not trust restoration
- a persisted shared-stack summary is not validation evidence

## 14. Unsafe-claim behavior

The future writer must block unsafe claims.

Unsafe claims include:

- validation success
- validation failure
- issue closure
- release mutation
- tag mutation
- asset mutation
- bundled-solver availability
- certification
- automatic activation
- trust restoration
- dependency installation
- solver execution
- discovery success

Unsafe claims must remain blocked display state, not persisted truth. If an
unsafe claim appears in supplied manifest UX state, a future writer must record a
blocker/diagnostic summary without accepting the claim.

## 15. Evidence/history retention

The future writer must retain evidence/history references as references, not as
new validation evidence.

Policy:

- deactivation history is retained
- reactivation history is retained
- historical validation evidence references are retained
- skipped-missing remains skipped-missing
- old validation evidence is not rewritten
- evidence is not deleted
- evidence retention is not validation success
- evidence retention is not validation failure
- issue `#6` through issue `#11` remain live optional validation issues unless a
  separate issue/validation gate changes them

## 16. Trust/provenance behavior

Trust/provenance behavior is explicit and conservative:

- user-selected manifests are untrusted by default
- plugin-provided manifests are untrusted by default
- built-ins remain authoritative by default
- trust labels are review labels, not certification
- source type and source id are preserved
- source display references are redacted
- fingerprints are provenance hints, not trust restoration
- persisted state does not restore trust
- persisted state does not activate candidates
- persisted state does not install plugins or solvers

## 17. Atomicity/error handling design

Atomicity is a future implementation requirement, not current behavior.

A future writer implementation must define:

- write target validation
- temporary file behavior
- fsync/durability policy if applicable
- atomic rename behavior where supported
- partial-write cleanup behavior
- parent directory creation policy
- overwrite policy
- permission error handling
- disk-full error handling
- path redaction in diagnostics
- no loss of previous valid state on failed write
- explicit failure diagnostics

This gate implements none of those actions and creates no files or directories.

## 18. Reload boundary

The state writer is separate from reload behavior.

Persisted state must not be reloadable by default. Future reload semantics
require separate design, view-model, GUI, CLI, and implementation gates. A state
write does not automatically reload, activate, trust, validate, install, execute,
close issues, mutate releases, mutate tags, mutate assets, or certify anything.

## 19. Export-summary boundary

The state writer is separate from export-summary behavior.

Export summaries are review/report artifacts; state writer output is future
local UX state. A future writer must not create export files, report files,
clipboard output, report attachments, open-output-folder behavior, or reloadable
bundles unless separate explicit gates authorize them.

## 20. ProjectSchema boundary

The state writer is separate from ProjectSchema.

No ProjectSchema mutation is allowed in this gate. A future state record must not
be treated as ProjectSchema state, solver state, material state, result state,
or project validation evidence. Any ProjectSchema integration needs a separate
schema and migration gate.

## 21. GUI boundary

The state writer is separate from GUI behavior.

This gate adds no GUI implementation, no file dialog, no save dialog, no
clipboard behavior, no report attachment, no open-output-folder behavior, no GUI
source mutation, and no widget action. A future GUI writer control requires a
separate gate and must preserve dry-run, acknowledgement, redaction, stale-source,
conflict, unsafe-claim, history, and non-action visibility.

## 22. CLI boundary

The state writer is separate from CLI behavior.

This gate adds no CLI implementation, no command parser changes, no save command,
no load command, no write command, no stdout contract, no exit-code behavior, and
no CLI source mutation. A future CLI writer command requires a separate gate and
must remain explicit, dry-run-first, redaction-first, and non-validating.

## 23. Passive discovery boundary

The state writer is separate from passive discovery.

This gate adds no runtime discovery integration and does not change passive
discovery behavior. It performs no plugin package import, no directory scan, no
network fetch, no discovery execution, no validation execution, and no solver
execution. A future source/discovery integration gate must keep user/plugin
manifests untrusted by default and built-ins authoritative by default.

## 24. Live optional validation issue boundary

Persisted manifest UX state is not live optional validation.

Issues `#6` through `#11` remain open and separate. A future state record cannot
close issues, claim validation success, claim validation failure, claim bundled
solvers, or claim certification. Validation evidence requires separate prepared
machine validation gates.

## 25. Diagnostics reserved: OSPMG_STATE_WRITER_* names

Reserved diagnostic names:

- `OSPMG_STATE_WRITER_NOT_IMPLEMENTED`
- `OSPMG_STATE_WRITER_DRY_RUN_ONLY`
- `OSPMG_STATE_WRITER_ACK_REQUIRED`
- `OSPMG_STATE_WRITER_NOT_VALIDATION`
- `OSPMG_STATE_WRITER_NOT_TRUST_RESTORE`
- `OSPMG_STATE_WRITER_NOT_AUTOMATIC_ACTIVATION`
- `OSPMG_STATE_WRITER_NO_INSTALL`
- `OSPMG_STATE_WRITER_NO_SOLVER_EXECUTION`
- `OSPMG_STATE_WRITER_NOT_ISSUE_CLOSURE`
- `OSPMG_STATE_WRITER_NOT_RELEASE_MUTATION`
- `OSPMG_STATE_WRITER_NOT_CERTIFICATION`
- `OSPMG_STATE_WRITER_REDACTION_REQUIRED`
- `OSPMG_STATE_WRITER_UNREDACTED_PATH_BLOCKED`
- `OSPMG_STATE_WRITER_SECRET_LIKE_CONTENT_BLOCKED`
- `OSPMG_STATE_WRITER_SCHEMA_VERSION_REQUIRED`
- `OSPMG_STATE_WRITER_SCHEMA_UNSUPPORTED`
- `OSPMG_STATE_WRITER_SCHEMA_MIGRATION_REQUIRED`
- `OSPMG_STATE_WRITER_STALE_SOURCE_REPREVIEW_REQUIRED`
- `OSPMG_STATE_WRITER_UNTRUSTED_SOURCE`
- `OSPMG_STATE_WRITER_CONFLICT_BLOCKED`
- `OSPMG_STATE_WRITER_SHARED_STACK_WARNING`
- `OSPMG_STATE_WRITER_UNSAFE_CLAIM`
- `OSPMG_STATE_WRITER_EVIDENCE_RETAINED`
- `OSPMG_STATE_WRITER_HISTORY_RETAINED`
- `OSPMG_STATE_WRITER_NO_DISCOVERY_EXECUTION`
- `OSPMG_STATE_WRITER_NO_PLUGIN_IMPORT`
- `OSPMG_STATE_WRITER_PROJECT_SCHEMA_MUTATION_DISABLED`
- `OSPMG_STATE_WRITER_RELOAD_DISABLED`
- `OSPMG_STATE_WRITER_EXPORT_DISABLED`
- `OSPMG_STATE_WRITER_FUTURE_GATE`

These names are reserved design vocabulary only. This gate emits no diagnostics
from runtime code.

## 26. Future implementation test plan

Future implementation gates should add tests for:

- dry-run does not write files or create directories
- write plan redacts paths
- secret-like content blocks writes
- acknowledgement expiry blocks stale writes
- unsupported schema blocks writes
- migration-required state blocks writes
- stale sources require re-preview
- conflicts and shared-stack warnings remain visible
- unsafe claims are blocked
- evidence/history references are retained
- failed writes preserve previous valid state
- partial write cleanup is deterministic
- no ProjectSchema mutation occurs
- no reload/export/GUI/CLI behavior is accidentally added outside its gate
- no discovery, validation, solver execution, install/uninstall, issue mutation,
  release mutation, tag mutation, asset mutation, version bump, validation-pass
  claim, validation-fail claim, or certification claim occurs

## 27. Non-actions

This gate intentionally does not:

- implement a state writer
- write files
- create runtime state files
- create settings files
- create schema files
- create export files
- create report files
- create reloadable bundles
- mutate ProjectSchema
- implement GUI behavior
- implement CLI behavior
- implement reload behavior
- implement export behavior
- add clipboard behavior
- add report attachment behavior
- add open-output-folder behavior
- add file dialog behavior
- add save dialog behavior
- mutate activation source behavior
- mutate deactivation source behavior
- mutate reactivation source behavior
- mutate discovery-refresh source behavior
- mutate persistence source behavior
- mutate export source behavior
- automatically activate candidates
- restore trust
- restore files
- rewrite files
- delete files
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
- mutate tags
- mutate assets
- bump versions
- claim validation success
- claim validation failure
- claim validation-pass
- claim validation-fail
- claim issue closure
- claim bundled solvers
- claim certification

## 28. Future gates

Suggested follow-up gates:

- OSW-EXP-101_OPTIONAL_SOLVER_PLUGIN_MANIFEST_STATE_WRITER_VIEWMODEL_OR_SCHEMA_EXTENSION
- OSW-EXP-102_OPTIONAL_SOLVER_PLUGIN_MANIFEST_STATE_WRITER_IMPLEMENTATION
- OSW-EXP-103_OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_CLI_IMPLEMENTATION
- OSW-EXP-104_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_CLI_DESIGN
- OSW-EXP-105_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_CLI_IMPLEMENTATION
- OSW-EXP-106_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_DESIGN
- OSW-EXP-107_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_VIEWMODEL
- OSW-EXP-108_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_DESIGN
- OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION

These gates are listed to keep implementation sequencing explicit. This gate
does not start OSW-EXP-101 or any later gate.
