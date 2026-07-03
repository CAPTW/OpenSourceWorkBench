# Optional Solver Plugin Manifest Reload Acceptance Persistence ProjectSchema Boundary Implementation

## Status

Experimental ProjectSchema boundary implemented for OSW-EXP-138. It is pure
in-memory, supplied-record-only, deterministic, redaction-first,
non-authoritative, and non-mutating.

It performs no ProjectSchema source edit, no ProjectSchema test edit, no
ProjectSchema mutation, no ProjectSchema field addition, no ProjectSchema
migration, no ProjectSchema validation evidence creation, no file reads or
writes, no file parsing, no input state-file reading or parsing, no writer
invocation, no reload file-reader invocation, no OSW-EXP-102 state-writer
invocation, no CLI/GUI calls, no subprocess use, no runtime reload acceptance,
no active acceptance mutation, no default target path, no background write, no
directory scan, no network fetch, no plugin package import, no reloadable
bundle creation, no export/report file creation, no clipboard behavior, no
report attachment, no open-output-folder behavior, no live discovery, no
passive refresh, no validation execution, no solver execution, no dependency
installation, no dependency uninstall, no solver uninstall, no automatic
activation, no trust restoration, no issue/release/tag/asset mutation, no
version bump, no validation-pass claim, no validation-fail claim, no
issue-closure claim, no bundled-solver claim, and no certification claim.

## Purpose

The implementation turns the OSW-EXP-137 design into a deterministic review
model that keeps supplied reload acceptance persistence records, persistence
view-model records, writer results, CLI write results, GUI write results, and
summary audit records separate from ProjectSchema state and ProjectSchema
validation evidence.

The boundary model is not a ProjectSchema importer. It does not inspect the
repository, persisted files, runtime state files, settings files, plugin
packages, discovery state, or live validation state. It only normalizes and
redacts caller-supplied in-memory mappings or objects with `to_mapping()`.

## Public Module/Class Names

The public module is
`osw.experimental.optional_solvers.plugin_manifest_reload_acceptance_persistence_projectschema_boundary`.

The main class is
`OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary`.
Supporting public records include
`ReloadAcceptancePersistenceProjectSchemaBoundaryState`,
`ReloadAcceptancePersistenceProjectSchemaBoundaryReadiness`,
`ReloadAcceptancePersistenceProjectSchemaBoundaryDiagnostic`,
`ReloadAcceptancePersistenceProjectSchemaBoundaryRow`,
`ReloadAcceptancePersistenceProjectSchemaBoundarySourceRecord`,
`ReloadAcceptancePersistenceProjectSchemaBoundaryAction`,
`ReloadAcceptancePersistenceProjectSchemaBoundaryActionRow`,
`ReloadAcceptancePersistenceProjectSchemaBoundaryNonActionFlags`, and
`ReloadAcceptancePersistenceProjectSchemaBoundarySummary`.

Public builders/renderers include
`build_optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary`
and
`render_optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary`.

## Input Policy

Inputs are caller-supplied mappings or in-memory record objects only:

- persistence record mapping;
- persistence view-model mapping;
- writer result mapping;
- CLI write result mapping;
- GUI write result mapping;
- summary audit mapping;
- optional issue-state snapshot;
- optional prepared-machine validation snapshot;
- optional caller diagnostics and limitations.

Missing input renders unavailable/no-record guidance. Supplied records remain
review inputs only. The module does not accept paths as authority, open files,
parse state files, call readers or writers, call CLI/GUI code, run discovery,
run validation, run solvers, or mutate ProjectSchema.

## State/Readiness Model

State and readiness are review-only. Empty input reports
`no_records_supplied`. Explicit unavailable input reports `unavailable`.
Supplied records report `records_with_blockers` and
`projectschema_blocked` because ProjectSchema import, mutation, migration,
validation evidence, trust restoration, activation, issue/release mutation,
and certification remain blocked until separate future gates.

Readiness is not ProjectSchema readiness, not validation readiness, and not a
prepared-machine validation result.

## ProjectSchema Non-Meaning

Supplied persistence records are not ProjectSchema state. Supplied summary
audit records are not ProjectSchema state. CLI write success and GUI write
success are not ProjectSchema mutation. Writer success is local review-record
metadata only.

The boundary output is not ProjectSchema state, ProjectSchema validation
evidence, ProjectSchema validation failure, ProjectSchema trust state,
ProjectSchema activation state, ProjectSchema release state, or ProjectSchema
certification state.

## Schema Separation

The implementation renders explicit rows stating:

- persistence schema is separate from ProjectSchema schema;
- summary audit schema is separate from ProjectSchema schema;
- writer schema is separate from ProjectSchema schema.

Schema-name similarity does not create compatibility. Migration remains
blocked and future-only.

## Prohibited Automatic Flows

The boundary renders blocked/future-only rows for:

- persistence record to ProjectSchema import;
- summary audit to ProjectSchema import;
- CLI write to ProjectSchema mutation;
- GUI write to ProjectSchema mutation;
- reload acceptance to ProjectSchema validation evidence;
- trust label to ProjectSchema trusted solver state;
- persisted active candidate to ProjectSchema activated candidate;
- skipped-missing to ProjectSchema validation success;
- unsafe claim to ProjectSchema truth;
- issue/release/certification claim to ProjectSchema evidence.

## Future Integration Preconditions

Any future ProjectSchema integration remains blocked until separate gates
provide ProjectSchema boundary design, prepared-machine validation review,
explicit user opt-in, ProjectSchema schema version review, persistence schema
version review, source/provenance review, stale-source re-preview,
conflict/shared-stack review, unsafe-claim review, acknowledgement expiry
review, redaction/privacy review, validation issue state review, and
issue/release/certification separation review.

## Future Permitted Data Candidates

The model lists potential future review inputs as non-authoritative candidates
only: redacted source identifiers, payload kind/schema version, writer hash and
byte count, CLI/GUI surface identity, summary audit gate coverage, non-action
flags, diagnostics references, limitations, and prepared-machine validation
status if supplied later.

None of these candidates are ProjectSchema fields in this gate.

## ProjectSchema Mutation Blockers

Mutation blockers include missing runtime acceptance, missing prepared-machine
validation, stale source, unresolved conflict/shared-stack state, unsafe
claims, unclear trust/provenance, required schema migration, expired
acknowledgements, unredacted paths, secrets/tokens/API keys, open live optional
validation issues `#6` through `#11`, and issue/release/certification claims.

The blockers are visible review output. They are not validation failure,
issue-closure evidence, release evidence, bundled-solver evidence, or
certification evidence.

## Validation Evidence Boundary

Persistence writes are not validation evidence. CLI writes are not validation
evidence. GUI writes are not validation evidence. Summary audit is not
validation evidence. Skipped-missing remains skipped-missing.
Prepared-machine validation remains separate and supplied-only.

## Trust/Provenance Boundary

User/plugin manifests remain untrusted by default. Trust labels are not
certification. Fingerprints are not trust signals. The boundary does not
restore trust, activate candidates, import plugin packages, or validate
solvers.

## Candidate Lifecycle Boundary

Persisted inactive remains review-only. Persisted active requires future
activation review. Deactivated remains deactivated review state. Reactivation
requires future review. Discovery-refresh state remains review state.

## Built-In/Shared-Stack Boundary

Built-ins remain authoritative by default. Persisted records do not override
built-ins. Conflicts and shared-stack warnings remain visible.

## Issue/Release/Certification Boundary

The boundary does not close issues, mutate releases, push tags, upload assets,
bump versions, claim bundled-solver support, claim validation success, claim
validation failure, or claim certification. Live optional validation issues
`#6` through `#11` are represented as separate/open unless a supplied snapshot
says otherwise for review display only.

## Redaction/Privacy Boundary

`to_mapping()` and `to_text_lines()` redact raw absolute paths to display names
and replace secret-like keys or values with `<redacted-secret-like-value>`.
Remote URL references are not treated as authority. Full file contents, plugin
code, tokens, API keys, credentials, and raw local paths are not displayed.

## Diagnostics Vocabulary

Diagnostics use the
`OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_*` family for
unavailable input, separate schema, blocked ProjectSchema import, blocked
ProjectSchema mutation, blocked ProjectSchema validation evidence, blocked
trust restoration, blocked activation, blocked issue/release actions, blocked
certification, prepared-machine requirements, and generic errors.

Lower-level supplied diagnostics are surfaced as supplied-only review rows and
are explicitly not ProjectSchema truth, validation evidence, or authority.

## Non-Action Flags

All non-action flags remain false, including `project_schema_mutated`,
`project_schema_field_added`, `project_schema_migration_performed`,
`project_schema_validation_evidence_created`, file IO flags, reader/writer
invocation flags, CLI/GUI/subprocess flags, discovery/validation/solver flags,
activation/trust flags, issue/release/tag/asset flags, version flags,
validation-pass/fail claim flags, issue-closure claim flags, bundled-solver
claim flags, and certification flags.

## Disabled/Future Actions

Disabled/future actions include importing persistence records or summary audits
to ProjectSchema, mutating or migrating ProjectSchema, creating ProjectSchema
validation evidence, runtime acceptance, trust restoration, activation,
discovery refresh, validation, solver execution, dependency install/uninstall,
solver uninstall, export/report/reloadable bundle creation, clipboard/report
attachment/open-folder behavior, issue/release/tag/asset mutation, validation
success/failure claims, and certification claims.

## Mapping/Text Output

`to_mapping()` returns deterministic JSON-compatible dictionaries with
redacted supplied records, policy rows, diagnostics, live issue separation,
prepared-machine validation separation, non-action flags, and disabled actions.

`to_text_lines()` renders deterministic plain-text review lines from the same
data. Text output repeats the core non-meaning statements: supplied persistence
records and summary audits are not ProjectSchema state; CLI/GUI write success
is not ProjectSchema mutation; persistence, summary audit, and writer schemas
are separate from ProjectSchema schema.

## Relationships

OSW-EXP-137 provides the design contract implemented here. OSW-EXP-136 summary
audit records may be supplied as review input, but this implementation does
not invoke the summary audit module to discover state. OSW-EXP-134 CLI write
and OSW-EXP-132 GUI write results may be supplied as local review-record
inputs, but write success remains separate from ProjectSchema mutation.
OSW-EXP-126 writer output may be supplied as metadata, but the writer is not
imported or invoked. OSW-EXP-125 persistence view-model output may be supplied
as review state, but readiness is not ProjectSchema readiness.

Reload acceptance GUI/CLI, reload file reader, explicit-path preview, and live
optional validation issues remain separate surfaces. Prepared-machine
validation remains a future supplied-only gate.

## Security/Privacy Review

The module imports only lightweight standard-library modules. It performs no
file or process operations, blocks raw paths and secrets, keeps plugin code and
full file contents out of output, and treats all supplied data as
non-authoritative review data.

## Testing Strategy

Focused unit tests cover public exports, unavailable/no-input guidance,
supplied persistence/summary/CLI/GUI/writer records, schema separation,
prohibited flows, preconditions, non-authoritative candidate rows, mutation
blockers, validation evidence boundaries, trust/provenance boundaries,
candidate lifecycle boundaries, built-in/shared-stack boundaries,
issue/release/certification boundaries, redaction, diagnostics, lower-level
diagnostic surfacing, non-action flags, disabled future actions, live issue
separation, prepared-machine validation separation, deterministic mapping/text,
and AST/source scans against ProjectSchema imports, file IO, writer/reader
imports or calls, CLI/GUI imports or calls, subprocess use, discovery,
validation, solver imports, and GitHub issue/release/tag/asset mutation calls.

## Non-Actions

This implementation does not edit ProjectSchema source/tests, mutate
ProjectSchema, add ProjectSchema fields, add ProjectSchema migration, create
ProjectSchema validation evidence, write files, read files, parse files, read
or parse input state files, invoke writer, invoke reload file reader, invoke
OSW-EXP-102 state writer, call CLI/GUI behavior, use subprocesses, accept
runtime reload, mutate active acceptance, add default target paths, write in
background, scan directories, fetch network manifests, import plugin packages,
create reloadable bundles, create export/report files, use clipboard behavior,
attach reports, open output folders, run live discovery, run passive refresh,
execute validation, execute solvers, install or uninstall dependencies,
uninstall solvers, automatically activate candidates, restore trust, mutate
issues/releases/tags/assets, bump versions, claim validation success, claim
validation failure, claim issue closure, claim bundled-solver support, or
claim certification.

## Future Gates

Suggested next gate:

- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION`, if a
  prepared machine is available.
