# Optional solver plugin manifest state writer implementation

## Status

OSW-EXP-102 implements an explicit local state writer library API for optional
solver plugin manifest UX state.

The implementation is intentionally bounded:

- explicit local state writer only
- caller-supplied target path required
- deterministic JSON serialization
- dry-run planning without writing
- actual write only through explicit caller acknowledgement
- same-directory atomic temp-file/replace write strategy
- no default write path
- no directory creation
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
- no discovery execution
- no validation execution
- no solver execution
- no issue mutation
- no release mutation
- no tag mutation
- no asset mutation
- no version bump
- no validation-pass claim
- no validation-fail claim
- no issue-closure claim
- no certification claim

This gate may write a caller-chosen local state file from the writer API. It does
not create default runtime state, settings, schema, export, report, or bundle
files.

## Public API

Public module:

`osw.experimental.optional_solvers.plugin_manifest_state_writer`

Public names:

- `OptionalSolverPluginManifestStateWriter`
- `OptionalSolverPluginManifestStateWriterRequest`
- `OptionalSolverPluginManifestStateWriterResult`
- `OptionalSolverPluginManifestStateWriterStatus`
- `OptionalSolverPluginManifestStateWriterDiagnostic`
- `build_optional_solver_plugin_manifest_state_writer_payload`
- `plan_optional_solver_plugin_manifest_state_write`
- `write_optional_solver_plugin_manifest_state`

The package-level experimental optional-solver namespace exports these names.

## Request model

`OptionalSolverPluginManifestStateWriterRequest` requires an explicit
`target_path` and carries:

- `allow_replace`
- `dry_run`
- `require_existing_parent`
- `expected_schema_version`
- `operation_label`
- `caller_acknowledged_write`
- `encoding`
- `newline`

Missing targets, directory targets, symlink targets, missing parents, and
existing targets without `allow_replace=True` block writing.

## Result model

`OptionalSolverPluginManifestStateWriterResult` reports:

- status
- redacted target display
- planned and written byte counts
- deterministic SHA-256
- payload key and section counts
- diagnostics, blockers, and warnings
- write and file-write booleans
- temp-file and atomic-replace booleans
- false non-action flags for runtime state files, settings files, schema files,
  export files, report files, reloadable bundles, ProjectSchema mutation, GUI,
  CLI, reload, export, clipboard, report attachment, open-output-folder,
  discovery, validation, solver execution, issue/release/tag/asset mutation,
  version bump, validation-pass/fail claims, issue closure, and certification.

## Payload model

The writer builds a deterministic JSON-compatible payload from supplied
`OptionalSolverPluginManifestStateWriterViewModel` records, mappings returned by
`to_mapping()`, or an already-built payload mapping.

Payload sections include:

- `payload_kind`
- `payload_schema_version`
- `writer_version`
- `generated_by`
- `state_scope`
- `header`
- `summary`
- `storage_options`
- `write_plan`
- `write_plans`
- `file_format`
- `schema_boundary`
- `sources`
- `provenance`
- `candidates`
- `acknowledgements`
- `redaction_privacy`
- `schema_migration`
- `stale_sources`
- `conflicts`
- `unsafe_claims`
- `evidence_history`
- `atomicity_error_handling_plan`
- `diagnostics`
- `limitations`
- `non_action_flags`
- `action_states`
- `migration_notes`
- `safety_boundary`

The payload preserves the supplied trust, provenance, acknowledgement expiry,
redaction, stale-source/re-preview, conflict/shared-stack, unsafe-claim, and
evidence/history records. Persisted state remains local UX state only.

## Deterministic serialization

Serialization uses UTF-8, sorted JSON keys, stable indentation, and a trailing
newline. The writer does not add timestamps, random ids, environment variables,
or machine-specific default paths.

The planned SHA-256 is computed over the serialized bytes and is available for
dry-run and actual-write results.

## Write policy

The writer writes only when all are true:

- `dry_run=False`
- `caller_acknowledged_write=True`
- the target path is explicit
- the parent directory already exists
- the target is not a directory or symlink
- replacing an existing target is explicitly allowed
- the payload schema version matches any supplied expectation
- the supplied view-model readiness is `ready_for_future_write`
- no supplied blocker diagnostics remain
- schema, redaction, stale-source, conflict, unsafe-claim, and acknowledgement
  preconditions are satisfied

`dry_run=True` never writes. Failed preflight never writes. Serialization failure
does not leave a target file behind. The writer creates a same-directory
temporary file and uses atomic replace; temporary files are cleaned up after a
replace failure when possible.

## Blocking and readiness

Actual writes are blocked for unavailable state, missing explicit requests,
missing/unsupported/migration-required schema state, redaction review blockers,
unredacted paths, secret-like content, stale-source re-preview blockers,
conflicts, shared-stack warnings, unsafe claims, missing acknowledgements,
`dry_run_only`, `future_writer_required`, and errors.

`future_writer_required` remains explicit and safe: this writer does not silently
override a supplied view-model that still says a future writer is required.

## Diagnostics

The writer surfaces:

- `OSPMG_STATE_WRITER_WRITE_PLANNED`
- `OSPMG_STATE_WRITER_WRITE_COMPLETED`
- `OSPMG_STATE_WRITER_WRITE_BLOCKED`
- `OSPMG_STATE_WRITER_WRITE_ERROR`
- path, caller-acknowledgement, schema-version, payload-secret, payload-path,
  serialization, and atomic-replace diagnostics

Diagnostics are writer-library diagnostics. They are not validation evidence and
do not claim validation success, validation failure, issue closure, release
mutation, bundled solvers, or certification.

## CLI follow-up

OSW-EXP-103 adds a bounded persistence CLI that calls this writer library for
dry-run planning and explicit local writes. The CLI does not bypass preflight:
actual write still requires a caller-supplied target path, explicit write mode,
caller acknowledgement, existing parent directory, replacement opt-in when
needed, schema compatibility, view-model readiness, and no blocker diagnostics.
The CLI adds no GUI behavior, reload behavior, ProjectSchema mutation, live
discovery, validation execution, solver execution, dependency install/uninstall,
report/export/clipboard/open-folder behavior, issue mutation, release mutation,
tag mutation, asset mutation, version bump, validation-pass/fail claim,
issue-closure claim, bundled-solver claim, or certification claim.

## Relationship to prior gates

OSW-EXP-100 remains the design-only state-writer contract. OSW-EXP-101 remains
the pure non-writing view-model. This gate consumes those records without
mutating them and adds only the explicit writer API.

OSW-EXP-090, OSW-EXP-092, OSW-EXP-093, OSW-EXP-095, OSW-EXP-096, OSW-EXP-097,
and OSW-EXP-099 remain separate persistence, schema, GUI, CLI-design, and
export-summary contracts.

## Future gates

Future separate gates remain required for GUI writer controls, CLI writer
commands, reload behavior, ProjectSchema integration, report/export integration,
settings files, runtime state files, schema files, reloadable bundles, source
integration, discovery integration, validation, install/uninstall, solver
execution, issue/release/tag/asset mutation, trust elevation, and certification
claims.

Issues `#6` through `#11` remain open. Package metadata remains `0.1.5rc1`.
The public prerelease remains `v0.1.5-rc1`.

## Follow-up: reload file reader design (OSW-EXP-112)

OSW-EXP-112 designs the future explicit local file reader/parser that would read
state-writer-produced UX state files back into reload review
([optional_solver_plugin_manifest_reload_file_reader_design.md](optional_solver_plugin_manifest_reload_file_reader_design.md)).
That reader is the inverse-but-asymmetric counterpart of this writer: it reads only
this bounded payload family, validates and redacts it, and returns a safe in-memory
mapping for review. It is design-only — no reader is implemented, no file is read,
and the writer's boundaries (no runtime reload, no trust restoration, no
ProjectSchema mutation) are preserved.

## Follow-up: reader implemented (OSW-EXP-113)

OSW-EXP-113 implements that reader
([optional_solver_plugin_manifest_reload_file_reader_implementation.md](optional_solver_plugin_manifest_reload_file_reader_implementation.md)).
It reads only this writer's payload family from an explicit caller path, validates
kind/schema/redaction/unsafe-claim/stale/conflict boundaries, and returns a safe
review mapping. It reads but never writes, repairs, or migrates files, and it
preserves the writer's no-runtime-reload, no-trust-restoration, and
no-ProjectSchema-mutation boundaries.

## Follow-up: CLI explicit-path design (OSW-EXP-114)

OSW-EXP-114 designs a future CLI `load-preview --path` bridge from this writer's
payload family, through the OSW-EXP-113 reader, into reload view-model review
([optional_solver_plugin_manifest_reload_cli_explicit_path_design.md](optional_solver_plugin_manifest_reload_cli_explicit_path_design.md)).
The design adds no CLI implementation, no path argument implementation, no file
reading/parsing at runtime in this gate, no default/background reload, no
ProjectSchema mutation, no discovery/validation/solver execution, no activation,
no trust restoration, no issue/release mutation, and no certification claim.

## Follow-up: GUI file-dialog design (OSW-EXP-116)

OSW-EXP-116 designs a future GUI file-dialog bridge from an explicit
user-selected state file, through the OSW-EXP-113 reader, into reload view-model
review
([optional_solver_plugin_manifest_reload_gui_file_dialog_design.md](optional_solver_plugin_manifest_reload_gui_file_dialog_design.md)).
The design does not edit writer source, implement GUI file dialogs, open files
from GUI code, parse writer payloads outside the reader, add default/background
reload, mutate ProjectSchema, run discovery/validation/solver execution,
activate candidates, restore trust, mutate issues/releases/tags/assets, or claim
certification.

## Follow-up: reload acceptance persistence design (OSW-EXP-124)

OSW-EXP-124 designs future reload acceptance persistence semantics
([optional_solver_plugin_manifest_reload_acceptance_persistence_design.md](optional_solver_plugin_manifest_reload_acceptance_persistence_design.md)).
It treats this OSW-EXP-102 writer as the closest future pattern for explicit
target paths, redaction, dry-run planning, deterministic JSON, hashes, and
atomic writes. It does not edit or invoke writer source, does not implement an
acceptance writer, creates no checked-in state files, writes no persistence,
mutates no ProjectSchema, accepts no runtime reload state, performs no file IO
in this gate, and claims no validation pass/fail, issue closure, release
mutation, bundled solver support, or certification.

## Follow-up: reload acceptance persistence view-model (OSW-EXP-125)

OSW-EXP-125 implements the pure in-memory reload acceptance persistence
view-model
([optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel.md](optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel.md)).
It uses the state writer only as a future pattern for explicit storage policy
and dry-run planning. It does not import, edit, invoke, or wrap this writer.

The view-model writes no files, creates no checked-in state files, performs no
runtime reload acceptance, mutates no ProjectSchema, reads no files, parses no
files, invokes no reader, calls no CLI/GUI behavior, uses no subprocesses, runs
no discovery, validation, or solver execution, activates no candidates, restores
no trust, mutates no issues/releases/tags/assets, and claims no certification.

## Follow-up: Reload Acceptance Persistence Writer (OSW-EXP-126)

OSW-EXP-126 implements a separate reload acceptance persistence writer
([optional_solver_plugin_manifest_reload_acceptance_persistence_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_implementation.md)).
It borrows the state writer's explicit-write and deterministic-payload posture
without importing, editing, invoking, or wrapping this state writer.

The reload acceptance persistence writer is scoped to reload acceptance
persistence records only. It remains dry-run-first and explicit-target-path
only, requires caller acknowledgement for actual writes, and does not mutate
ProjectSchema, accept runtime reloads, invoke readers, call CLI/GUI behavior,
run discovery/validation/solver execution, activate candidates, restore trust,
mutate issues/releases/tags/assets, or claim certification.
