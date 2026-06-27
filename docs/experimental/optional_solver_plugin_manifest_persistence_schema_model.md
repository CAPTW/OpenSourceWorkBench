# Optional solver plugin manifest persistence schema model

## Status

Implemented as a pure experimental schema model for OSW-EXP-093.

This gate adds versioned, in-memory, JSON-compatible data records and
deterministic construction, normalization, mapping conversion, and validation
helpers only. It adds no runtime persistence behavior, no persistence
implementation, no file writes, no schema file creation, no settings file
creation, no runtime state file creation, no ProjectSchema mutation, no GUI
persistence behavior, no CLI persistence behavior, no reload behavior, no export
behavior, no automatic activation, no trust restoration, no file restoration, no
file rewrite, no file deletion, no dependency installation, no dependency
uninstall, no solver uninstall, no plugin package import, no directory scan, no
network fetch, no discovery execution, no validation execution, no solver
execution, no issue mutation, no issue closure, no release mutation, no tag
mutation, no asset mutation, no version bump, no validation-pass claim, no
validation-fail claim, and no certification claim.

## Purpose

The persistence schema model defines the versioned, in-memory shape that a future
optional solver plugin manifest persistence layer would serialize. It turns
already-supplied records into a normalized header, source, candidate,
acknowledgement, diagnostic, redaction-policy, migration, conflict, unsafe-claim,
evidence/history, non-action-flag, and validation-summary structure.

It exists so that a future schema writer, settings-file model, GUI, CLI, reload,
or export gate can agree on one redaction-first, acknowledgement-aware,
schema-versioned contract without this gate writing anything.

## Public module/class names

- Module:
  `osw.experimental.optional_solvers.plugin_manifest_persistence_schema_model`
- Main class:
  `OptionalSolverPluginManifestPersistenceSchemaModel`
- Builder:
  `build_optional_solver_plugin_manifest_persistence_schema_model`
- Mapping validator:
  `validate_optional_solver_plugin_manifest_persistence_schema_mapping`
- Redaction helper:
  `redact_optional_solver_plugin_manifest_persistence_schema_source_reference`
- Record types:
  `OptionalSolverPluginManifestPersistenceSchemaHeader`,
  `...SchemaSourceRecord`, `...SchemaCandidateRecord`,
  `...SchemaAcknowledgementRecord`, `...SchemaDiagnosticRecord`,
  `...SchemaRedactionPolicyRecord`, `...SchemaMigrationRecord`,
  `...SchemaConflictRecord`, `...SchemaUnsafeClaimRecord`,
  `...SchemaEvidenceHistoryRecord`, `...SchemaNonActionFlags`,
  `...SchemaValidationSummary`.

The package-level experimental optional-solver namespace re-exports the public
records, constants, and helper functions for this gate.

## Input boundary

All inputs are caller-supplied records or caller-supplied mappings:

- a schema version string
- source/provenance records
- candidate records
- acknowledgement records
- conflict/shared-stack records
- unsafe-claim records
- a redaction-policy record
- an evidence/history record
- migration metadata

The schema model does not read files, parse JSON from paths, inspect path
existence, scan directories, import plugin packages, run discovery, run
validation, execute solvers, install or uninstall dependencies, mutate issues, or
mutate releases. Everything happens in-memory on supplied data.

## Schema header and version model

The header carries the schema version, whether that version is supported, an
optional created-by/created-at display, the state scope and kind, the redaction
policy id, and migration flags. The default redaction policy id is
`redaction_first_v1`.

The current supported in-memory schema version is `osw-exp-093-schema-1`. The
header records a version but does not stamp wall-clock time itself; timestamps are
caller-supplied display strings.

## Supported versions and migration policy

Supported versions are the current version plus the `osw-exp-092-preview` marker.
An unsupported or missing version is a blocker and sets migration-required on the
migration record.

This gate performs no migration and creates no schema file. A future migration or
writer gate must define its own upgrade and write behavior. Migration here is a
diagnostic state, not an action.

## Record types

The complete model contains a header plus tuples of source, candidate,
acknowledgement, diagnostic, conflict, and unsafe-claim records, a redaction
policy record, a migration record, an evidence/history record, a non-action-flags
record, and a deterministic validation summary. All records are frozen
dataclasses and are JSON-compatible once converted with `to_mapping`.

## Source/provenance records

Source records carry an id, type, label, a redacted display reference, a
redaction flag, a trust label, the persisted-state kind, a fingerprint display, a
stale-source state, a re-preview flag, and a raw-reference-blocked flag.

Sources are untrusted by default. Raw absolute paths are blocked. A stale source
requires re-preview. A source is never trusted, restored, fetched, or activated by
this model.

## Candidate records

Candidate records carry the stack id, display name, source linkage, trust label,
and the activation, deactivation, reactivation, discovery-refresh, and
persistence display states, plus blockers, warnings, required acknowledgements,
diagnostics, redaction status, and history states.

A candidate record never implies activation, persistence, validation, or trust.
It is inspectable in-memory display state only.

## Acknowledgement records and expiry

Acknowledgement records carry an id, label, required/satisfied/persisted flags,
and expiry flags for reload, source change, schema change, and unsafe claims. By
default every acknowledgement expires on reload, on source change, on schema
change, and on an unsafe claim.

A persisted acknowledgement is a record that a warning was shown, not permission
to activate, trust, validate, install, execute, close issues, mutate releases, or
certify anything. A trust label is not certification.

## Diagnostic vocabulary

The schema model reuses the reserved `OSPMG_PERSISTENCE_*` diagnostic vocabulary
from the OSW-EXP-092 persistence view-model, including
`OSPMG_PERSISTENCE_NOT_IMPLEMENTED`, `OSPMG_PERSISTENCE_ACK_REQUIRED`,
`OSPMG_PERSISTENCE_REDACTION_REQUIRED`,
`OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED`,
`OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED`,
`OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED`,
`OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED`,
`OSPMG_PERSISTENCE_CONFLICT_BLOCKED`, and `OSPMG_PERSISTENCE_UNSAFE_CLAIM`.

Diagnostics are explanatory. They do not trigger runtime behavior. Every built
model includes a `OSPMG_PERSISTENCE_NOT_IMPLEMENTED` honesty diagnostic.

## Validation summary

The validation summary is a deterministic count-only view: record, source,
candidate, acknowledgement, diagnostic, conflict, unsafe-claim, redaction-issue,
stale-source, migration-required, blocker, warning, and error counts, plus
`ready_for_future_write`, `persistence_performed`, and `file_write_performed`,
which are always false in this gate.

The summary is derived purely from supplied records, so identical inputs always
produce identical summaries.

## Mapping conversion (to_mapping / from_mapping)

`to_mapping` returns an in-memory, redacted, JSON-ready dictionary with top-level
keys for schema version, created-by/created-at, state scope, manifest sources,
candidates, acknowledgements, diagnostics, conflicts, unsafe claims, redaction
policy, evidence history, migration notes, and non-action flags. `from_mapping`
rebuilds a model from such a dictionary.

Round-tripping is a pure transformation. It writes nothing, opens no file, and
never sets a non-action flag to true.

## Mapping validation

`validate_optional_solver_plugin_manifest_persistence_schema_mapping` validates a
supplied mapping in-memory and returns diagnostic records. It flags a missing
schema version, an unsupported version, a missing redaction policy, any truthy
non-action flag, blocked raw paths, stale sources, present conflicts, unsafe
claims, and missing required acknowledgements.

Validation here means structural in-memory checks. It is not optional solver
validation, not solver execution, and not a validation-pass or validation-fail
claim.

## Redaction/privacy policy

The redaction policy record is redaction-first: redaction required, raw absolute
paths not allowed, unredacted paths blocked, secret-like content blocked, and path
review required. The redaction helper displays caller-provided labels first;
otherwise it shortens slash or backslash paths to the final name and never
inspects path existence.

This is a display policy only, not a writer. A raw or unredacted reference is
blocked rather than stored.

## Stale-source and re-preview policy

Stale, missing, moved, or changed sources require re-preview. The model can carry
stale-source state and a re-preview flag, but it does not locate the file, restore
it, rewrite it, delete it, fetch it, trust it, or activate it.

A future reload that cannot re-preview a source must define its own policy. This
model does no file IO.

## Conflict/shared-stack policy

Conflict records describe a shared stack id where a built-in and a user/plugin
source overlap. Built-ins win by default, the conflict stays visible, and a future
policy gate is required.

The model never resolves a conflict in favor of an untrusted source and never
hides it.

## Unsafe-claim policy

Unsafe-claim records are always blocked and never accepted by persistence. A claim
that an optional solver is certified, validated, installed, or trusted is recorded
as blocked display state with a warning, not as truth.

## Evidence/history policy

Persisted state is not validation evidence. It is not validation success and not
validation failure. Skipped-missing remains skipped-missing.

Historical validation evidence, deactivation history, and reactivation history
remain visible and retained as supplied data. The model never erases history,
rewrites evidence, deletes evidence, validates optional stacks, closes issues, or
claims live optional validation completion.

## Non-action flags

The non-action-flags record enumerates every action this gate must not perform,
and all of them are false: persistence, file writes, settings/runtime state file
creation, ProjectSchema mutation, GUI/CLI behavior, reload, export, automatic
activation, trust restoration, file restore/rewrite/delete, dependency
install/uninstall, solver uninstall, discovery/validation/solver execution,
issue/release/tag/asset mutation, and certification.

Mapping validation treats any truthy non-action flag as a blocker.

## Relationship to OSW-EXP-090 design

OSW-EXP-090 defined optional solver plugin manifest state persistence semantics as
design-only. OSW-EXP-093 implements the pure schema model slice of that design. It
keeps the redaction-first, acknowledgement-aware, schema-versioned,
non-validating, non-installing, non-executing, non-mutating, and future-gated
boundary.

## Relationship to OSW-EXP-092 persistence view-model

OSW-EXP-092 implemented the persistence view-model. This schema model can adapt an
already-built persistence view-model into schema records with
`from_persistence_viewmodel`.

That adapter is a pure transformation. It does not mutate the view-model, does not
turn preview readiness into a write, and does not create a schema file.

## Relationship to GUI and CLI

This gate adds no GUI behavior and no CLI behavior. It imports no PySide, Qt,
file-dialog code, command runner, subprocess path, or CLI command module.

Future GUI and CLI gates may serialize these records, but must keep their own
tests for acknowledgement handling, disabled actions, no direct solver execution,
no install/uninstall, no file writes unless explicitly gated, and no
issue/release mutation.

## Relationship to ProjectSchema

The schema model does not import, instantiate, or mutate ProjectSchema. It exposes
ProjectSchema mutation as a false non-action flag only.

Any future ProjectSchema persistence or project-local state model requires a
separate gate with schema, migration, unit, validation, preview, and rollback
tests.

## Relationship to export-summary design

OSW-EXP-091 defined export-summary semantics as design-only. This schema model may
provide records a future export-summary view-model can read, but this gate creates
no export summary implementation, no export file, no clipboard behavior, no
open-output-folder behavior, and no reloadable bundle.

An export summary is not persistence and not validation evidence unless a future
gate explicitly changes that boundary.

## Relationship to live optional validation issues

Issues `#6` through `#11` remain open unless a separate live optional validation
gate supplies passing installed-only evidence and performs issue triage.

This schema model does not change live optional validation state, does not turn
skipped-missing into pass or fail, does not close issues, and does not claim that
optional solver stacks are validated.

## Non-actions

This gate explicitly performs no persistence implementation, no file writes, no
schema file creation, no settings file creation, no runtime state file creation,
no ProjectSchema mutation, no GUI persistence behavior, no CLI persistence
behavior, no reload behavior, no export behavior, no automatic activation, no
trust restoration, no file restore, no file rewrite, no file deletion, no
dependency installation, no dependency uninstall, no solver uninstall, no plugin
package import, no directory scan, no network fetch, no discovery execution, no
validation execution, no solver execution, no issue mutation, no issue closure, no
release mutation, no tag mutation, no asset mutation, no version bump, no
validation-pass claim, no validation-fail claim, and no certification claim.

## Future gates

Future gates remain required for:

- persistence writer
- settings-file model
- runtime state-file model
- ProjectSchema integration
- GUI persistence behavior
- CLI persistence behavior
- reload behavior
- schema migration behavior
- export-summary view-model
- export-summary GUI/CLI/report behavior
- reloadable bundle semantics
- source integration
- discovery integration
- validation integration
- dependency install/uninstall behavior
- solver uninstall behavior
- solver execution behavior
- issue closure
- release/tag/asset/version mutation
- trust elevation
- certification or validation claims
