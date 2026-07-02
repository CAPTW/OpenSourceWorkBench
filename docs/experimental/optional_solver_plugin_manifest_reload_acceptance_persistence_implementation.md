# Optional Solver Plugin Manifest Reload Acceptance Persistence Implementation

## 1. Status

- Experimental reload acceptance persistence writer implemented.
- Explicit-path only.
- Dry-run-first.
- Review-record writer only.
- No runtime reload acceptance.
- No active acceptance mutation.
- No ProjectSchema mutation.
- No default path.
- No background write.
- No directory scan.
- No network fetch.
- No plugin package import.
- No reload file-reader invocation.
- No CLI behavior.
- No GUI behavior.
- No subprocess use.
- No discovery/validation/solver execution.
- No automatic activation.
- No trust restoration.
- No issue/release/tag/asset mutation.
- No certification claims.

## 2. Purpose

OSW-EXP-126 adds a bounded library writer for local reload acceptance
persistence review records. It turns an already-built
`OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel` into
deterministic JSON for review-state persistence only.

## 3. Public module/class names

The implementation lives in
`src/osw/experimental/optional_solvers/plugin_manifest_reload_acceptance_persistence_writer.py`.
The public surface is
`OptionalSolverPluginManifestReloadAcceptancePersistenceWriter`,
`ReloadAcceptancePersistenceWriteRequest`,
`ReloadAcceptancePersistenceWriteResult`,
`ReloadAcceptancePersistenceWriteStatus`,
`ReloadAcceptancePersistenceWriteDiagnostic`,
`ReloadAcceptancePersistenceWritePayload`, and
`ReloadAcceptancePersistenceWritePathPolicy`.

Helper functions expose payload building, dry-run planning, and explicit
review-record writing.

## 4. Request/result model

`ReloadAcceptancePersistenceWriteRequest` carries the supplied persistence
view-model, explicit target path, dry-run flag, replacement policy, caller
acknowledgement, optional schema expectations, optional redaction allowances,
and redacted request context.

`ReloadAcceptancePersistenceWriteResult` carries status, redacted target
display, planned/written flags, byte count, SHA-256, payload identity,
diagnostics, blockers, warnings, non-action flags, and stable text/mapping
rendering.

## 5. Payload model

The payload contains `payload_kind`, `payload_schema_version`, writer metadata,
summary, storage, write plan, the supplied acceptance persistence mapping,
acknowledgements, expiry, provenance, schema, redaction/privacy, candidate
lifecycle, stale-source, conflict/shared-stack, unsafe-claim, evidence/history,
diagnostics, non-action flags, disabled/future actions, safety guidance, and
limitations.

## 6. Serialization behavior

JSON serialization is deterministic: sorted keys, stable indentation, UTF-8,
and a trailing newline. The result SHA-256 is computed over the exact planned
or written bytes.

## 7. Path policy

The writer requires an explicit caller-supplied target path. It rejects missing
targets, directory targets, symlink targets, missing parents, parent paths that
are not directories, and existing targets unless `allow_replace=True`. It never
creates parent directories and never scans directory contents.

## 8. Dry-run behavior

Dry-run is the default. Dry-run builds, serializes, sizes, and hashes the
payload, returns planned status, and creates no target or temporary file.

## 9. Actual write behavior

Actual write requires `dry_run=False`,
`caller_acknowledged_persistence_write=True`, an explicit safe target, a ready
persistence view-model, and a clean payload safety scan. It writes only the
review record to the requested target.

## 10. Atomic write and cleanup behavior

Actual writes use a same-directory temporary file, flush and fsync the file,
then replace the target with `os.replace`. On replace failure, the writer
attempts to remove the temporary file and reports cleanup status.

## 11. Readiness/blocking behavior

The writer treats the OSW-EXP-125 `writer_future_only` or `ready_future_only`
state as the explicit writer handoff. Other readiness states, blockers, missing
acknowledgements, stale-source state, conflicts, unsupported schema, migration
requirements, unsafe claims, unredacted paths, and secret-like values block
writes.

## 12. Redaction/privacy behavior

The result and payload expose only basename/redacted target displays. The writer
inspects only the in-memory payload it is about to write, blocks secret-like
keys/values, and blocks unredacted absolute paths, home directory references,
and environment-variable-looking values unless a caller explicitly opts into a
future policy.

## 13. Schema/migration behavior

Payload kind and schema version are explicit. Optional request expectations
block when they do not match. Schema mismatch is not validation failure, and
the persistence schema remains separate from ProjectSchema.

## 14. Acknowledgement behavior

The writer preserves acknowledgement rows from the persistence view-model and
blocks when the supplied view-model is not ready because required
acknowledgements are missing or expired.

## 15. Stale-source/re-preview behavior

Stale-source or source-fingerprint blockers in the supplied view-model block
writes. The writer does not inspect referenced source files and does not
re-preview them.

## 16. Conflict/shared-stack behavior

Conflict and shared-stack blockers remain visible and block writes. Built-ins
remain authoritative by default, and the writer does not resolve conflicts.

## 17. Unsafe-claim behavior

Unsafe validation, issue, release, trust, install, solver, bundled-solver, or
certification claims are not rendered as truth. Unsafe-claim blockers prevent
writes.

## 18. Evidence/history behavior

Evidence/history rows are preserved as reference-only data. The writer does
not delete, rewrite, elevate, or treat evidence/history as validation evidence
or validation failure.

## 19. Diagnostics vocabulary

Writer diagnostics use `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_*` codes for
planned, completed, blocked, path-policy, caller-acknowledgement, payload
safety, schema mismatch, view-model blockers, serialization errors, and atomic
replace failures.

## 20. Non-action flags

All downstream non-action flags remain false. Only
`persistence_write_performed` may become true, and only for the explicit local
review-record write. It never implies runtime reload acceptance, ProjectSchema
mutation, validation, activation, trust restoration, issue/release mutation, or
certification.

## 21. Relationship to persistence design

This gate implements the explicit, redacted, dry-run-first local writer
designed by OSW-EXP-124. It does not broaden that design into runtime
acceptance or authoritative state.

## 22. Relationship to persistence view-model

The writer consumes OSW-EXP-125 persistence view-model records and does not
change that view-model source. The view-model remains the policy/readiness
source.

## 23. Relationship to OSW-EXP-102 state writer

The writer follows the same explicit local write style as OSW-EXP-102 but does
not invoke or edit the OSW-EXP-102 state writer.

## 24. Relationship to reload acceptance GUI/CLI

Existing GUI and CLI acceptance review surfaces remain review-only. This gate
adds no GUI or CLI behavior and no subprocess bridge.

## 25. Relationship to ProjectSchema

The persisted review record is not ProjectSchema state. The writer imports no
ProjectSchema code and mutates no project schema.

## 26. Relationship to live optional validation issues

Writing a review record does not validate optional solvers and does not close
issues #6 through #11. Prepared-machine validation remains separate.

## 27. Security/privacy review

The writer is local, explicit-path, redaction-first, no-default-path, and
no-directory-scan. It blocks secret-like values and raw path disclosures in the
payload it plans to write.

## 28. Non-actions

This gate performs no runtime reload acceptance, active acceptance mutation,
ProjectSchema mutation, default reload path selection, background write,
directory scan, network fetch, plugin package import, input state-file reading
or parsing, reload file-reader invocation, OSW-EXP-102 state-writer invocation,
CLI behavior, GUI behavior, subprocess use, reloadable bundle creation, export
file creation, report file creation, clipboard behavior, report attachment,
open-output-folder behavior, live discovery, passive refresh, validation
execution, solver execution, dependency installation, dependency uninstall,
solver uninstall, automatic activation, trust restoration, issue mutation,
release mutation, tag mutation, asset mutation, version bump, validation-pass
claim, validation-fail claim, issue-closure claim, bundled-solver claim, or
certification claim.

## 29. Testing strategy

Focused unit tests cover module imports/exports, dry-run defaults, path
blockers, replacement policy, dry-run hashing, acknowledged actual writes,
trailing newline, SHA-256, atomic temp cleanup, blocked view-models, policy
blockers, payload sections, safety text, redaction, secret blocking,
non-action flags, schema mismatches, forbidden imports/calls, and absence of
dry-run output files.

## 30. Follow-up: Persistence CLI Design (OSW-EXP-127)

OSW-EXP-127 designs the future stdout-first reload acceptance persistence CLI
([optional_solver_plugin_manifest_reload_acceptance_persistence_cli_design.md](optional_solver_plugin_manifest_reload_acceptance_persistence_cli_design.md)).
The writer remains a local API boundary and is not invoked by this design gate.

The future CLI design keeps actual writer invocation separately gated. It adds
no CLI implementation, no source edits, no file writes, no input state-file
reading or parsing, no reload file-reader invocation, no OSW-EXP-102
state-writer invocation, no GUI behavior, no subprocess use, no runtime reload
acceptance, no ProjectSchema mutation, no discovery, validation, solver
execution, activation, trust restoration, issue/release/tag/asset mutation,
validation claim, or certification claim.

## 31. Follow-up: Persistence CLI Implementation (OSW-EXP-128)

OSW-EXP-128 implements the stdout-first persistence CLI review/write-plan
surface
([optional_solver_plugin_manifest_reload_acceptance_persistence_cli_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_cli_implementation.md)).
The CLI uses this writer only through `plan_reload_acceptance_persistence_write`
with `dry_run=True`; it does not call the actual write function, does not create
files, and keeps `write-future` disabled. It adds no input state-file
reading/parsing, no reload file-reader invocation, no OSW-EXP-102 state-writer
invocation, no GUI behavior, no subprocess use, no runtime reload acceptance,
no ProjectSchema mutation, no discovery/validation/solver execution, no
activation, no trust restoration, no issue/release/tag/asset mutation, no
validation claim, and no certification claim.
