# Optional Solver Plugin Manifest Reload Acceptance Persistence ProjectSchema Boundary Design

## Status

This gate is design-only.

It adds no ProjectSchema implementation, no ProjectSchema source edits, no
ProjectSchema test edits, no source edits, no CLI source edits, no GUI source
edits, and no experimental optional-solver source edits.

It performs no writer invocation, no file writes, no file reading, no file
parsing, no input state-file reading, no input state-file parsing, no reload
file-reader invocation, no OSW-EXP-102 state-writer invocation, no CLI
behavior, no GUI behavior, and no subprocess use.

It adds no runtime reload acceptance, no active acceptance mutation, no
ProjectSchema mutation, no ProjectSchema fields, no ProjectSchema migration, no
ProjectSchema validation evidence, no default target path, no background write,
no directory scan, no network fetch, no plugin package import, no reloadable
bundle creation, no export file creation, no report file creation, no clipboard
behavior, no report attachment, no open-output-folder behavior, no live
discovery, no passive refresh, no validation execution, no solver execution, no
dependency installation, no dependency uninstall, no solver uninstall, no
automatic activation, no trust restoration, no issue mutation, no release
mutation, no tag mutation, no asset mutation, no version bump, no
validation-pass claim, no validation-fail claim, no issue-closure claim, no
bundled-solver claim, and no certification claim.

## Purpose

This document defines a strict boundary between local reload acceptance
persistence records, reload acceptance persistence summary audits, and
ProjectSchema state.

The design preserves separate meanings for reload preview, acceptance review,
local persistence review, local review-record writes, summary audit, runtime
reload acceptance, ProjectSchema state, validation evidence, issue/release
state, and certification claims.

It must not be read as authorization to implement ProjectSchema behavior. Any
ProjectSchema integration remains a future separately gated design,
implementation, validation, and review activity.

## Current Persistence Chain

The current reload acceptance persistence chain is local, non-authoritative, and
review-record oriented:

- The OSW-EXP-125 persistence view-model summarizes supplied reload acceptance
  view-model records as future-writer readiness and review state.
- The OSW-EXP-126 persistence writer writes explicit-path local review-record
  payloads only when separately invoked by allowed callers.
- The OSW-EXP-134 CLI write path persists local review records through the
  writer only after explicit target, dry-run, acknowledgement, and confirmation.
- The OSW-EXP-132 GUI write path persists local review records through the
  writer only after explicit target, dry-run, acknowledgement, and confirmation.
- The OSW-EXP-136 summary audit summarizes supplied persistence view-model,
  writer, CLI, and GUI records only.

All of those surfaces remain local review-record and non-authoritative
surfaces. They are not ProjectSchema state, not runtime reload acceptance, not
prepared-machine validation, not validation evidence, not validation failure,
not issue closure, not release mutation, and not certification.

## ProjectSchema Non-Meaning

Reload acceptance persistence records, writer results, CLI writes, GUI writes,
and summary audits are not:

- ProjectSchema state;
- ProjectSchema validation evidence;
- ProjectSchema validation failure;
- ProjectSchema solver inventory;
- ProjectSchema plugin registry;
- ProjectSchema trust policy;
- ProjectSchema activation state;
- ProjectSchema dependency state;
- ProjectSchema release state;
- ProjectSchema certification state.

A local record can describe what a user reviewed or wrote locally. It cannot
make that state authoritative for a project.

## Persistence Schema Vs ProjectSchema Schema

The persistence payload schema remains separate from the ProjectSchema schema.
The summary audit schema remains separate from the ProjectSchema schema. The
writer payload schema remains separate from the ProjectSchema schema.

Schema-name similarity must not imply compatibility. A field named like a
ProjectSchema concept is still only a persistence or audit review field unless a
future ProjectSchema gate explicitly maps it, tests it, and accepts it.

Migration between the persistence payload schema, summary audit schema, writer
payload schema, and ProjectSchema schema requires a future explicit gate. This
gate adds no ProjectSchema fields and performs no ProjectSchema migration.

## Prohibited Automatic Flows

The boundary prohibits these automatic flows:

- persistence record -> ProjectSchema import;
- summary audit -> ProjectSchema import;
- CLI write -> ProjectSchema mutation;
- GUI write -> ProjectSchema mutation;
- reload acceptance -> ProjectSchema validation evidence;
- trust label -> ProjectSchema trusted solver state;
- persisted active candidate -> ProjectSchema activated candidate;
- skipped-missing -> ProjectSchema validation success;
- unsafe claim -> ProjectSchema truth;
- issue/release/certification claim -> ProjectSchema evidence.

Every one of these flows remains blocked until a separate gate defines,
implements, tests, validates, and reviews it.

## Future Integration Preconditions

Any future ProjectSchema integration must require all of the following before
ProjectSchema mutation or ProjectSchema validation evidence is considered:

- separate ProjectSchema boundary implementation design;
- prepared-machine validation review;
- explicit user opt-in;
- ProjectSchema schema version review;
- persistence schema version review;
- source/provenance review;
- stale-source re-preview;
- conflict/shared-stack review;
- unsafe-claim review;
- acknowledgement expiry review;
- redaction/privacy review;
- validation issue state review;
- issue/release/certification separation review.

Missing any precondition blocks ProjectSchema import, ProjectSchema mutation,
ProjectSchema validation evidence, trust restoration, activation, issue
mutation, release mutation, tag mutation, asset mutation, and certification
claims.

## Future Permitted Data Candidates

Future boundary review may consider these data candidates as review inputs only:

- redacted source identifiers;
- persistence payload kind/schema version;
- writer SHA-256 and bytes count;
- CLI/GUI surface identity;
- summary audit gate coverage;
- non-action flags;
- diagnostics references;
- limitations;
- prepared-machine validation status if supplied later.

These candidates are not ProjectSchema fields in this gate. They are not
ProjectSchema state and are not ProjectSchema validation evidence.

## ProjectSchema Mutation Blockers

A future boundary must block ProjectSchema mutation when any of these conditions
are present:

- runtime acceptance not separately completed;
- prepared-machine validation missing;
- stale source present;
- conflict/shared-stack unresolved;
- unsafe claim present;
- trust/provenance unclear;
- schema migration required;
- acknowledgements expired;
- raw paths unredacted;
- secrets/tokens/API keys present;
- validation issues #6 through #11 unresolved;
- issue/release/certification claims present.

The blocked state must be visible as review output. It must not be converted
into a pass, failure, issue closure, release mutation, bundled-solver claim, or
certification claim.

## Validation Evidence Boundary

Persistence writes are not validation evidence. GUI writes are not validation
evidence. CLI writes are not validation evidence. Summary audit is not
validation evidence.

Skipped-missing remains skipped-missing. Prepared-machine validation remains
separate. This gate makes no validation-pass claim and no validation-fail claim.

ProjectSchema validation evidence can only be created by a future gate that
defines its inputs, validation scope, machine state, diagnostics, review
requirements, and issue/release separation.

## Trust/Provenance Boundary

User/plugin manifests remain untrusted by default. Trust labels are not
certification. Fingerprints are not trust signals.

Summary audit trust rows are review-only. A recorded trusted-looking label does
not restore ProjectSchema trust state, does not activate a solver, and does not
validate a solver.

ProjectSchema trust state cannot be restored from persistence state. Future
trust restoration remains blocked unless a separate gate defines the trust
model, provenance review, stale-source review, conflict review, unsafe-claim
review, prepared-machine validation review, and explicit user approval.

## Candidate Lifecycle Boundary

Persisted inactive remains review-only. Persisted active requires future
activation review. Deactivated remains deactivated review state. Reactivation
requires future review. Discovery-refresh state remains review state.

This boundary allows no automatic activation and no trust restoration. A
persisted record does not override built-ins, built-in solver entries, or other
authoritative defaults.

## Built-In/Shared-Stack Boundary

Built-ins remain authoritative by default. Persisted records do not override
built-ins. Conflicts remain visible. Shared-stack warnings remain visible.

ProjectSchema cannot absorb unresolved conflicts. A future ProjectSchema gate
must preserve the conflict/shared-stack review state instead of hiding it behind
ProjectSchema fields.

## Issue/Release/Certification Boundary

Persistence records do not close issues. Summary audit does not close issues.
The ProjectSchema boundary does not mutate issues.

This gate performs no release mutation, no tag mutation, no asset mutation, no
version bump, no bundled-solver claim, and no certification claim.

Any future issue, release, tag, asset, version, bundled-solver, validation-pass,
validation-fail, issue-closure, or certification action requires a separate
release or validation gate.

## Redaction/Privacy Boundary

Raw paths are hidden by default. Secrets, tokens, and API keys are blocked.
Plugin code is not displayed. Full file content is not displayed.

ProjectSchema integration cannot require secret leakage. Diagnostics use
redacted context and must not reveal raw local paths, full manifest contents,
plugin source code, tokens, API keys, or credentials.

## Diagnostics Vocabulary

Future boundary review may reserve the
`OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_*` diagnostic
family:

- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_UNAVAILABLE`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_SEPARATE_SCHEMA`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_IMPORT_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_MUTATION_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_VALIDATION_EVIDENCE_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_TRUST_RESTORATION_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ACTIVATION_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ISSUE_RELEASE_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_CERTIFICATION_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_PREPARED_MACHINE_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ERROR`

Diagnostics are review signals only. They do not authorize ProjectSchema
mutation, validation evidence, runtime reload acceptance, issue mutation,
release mutation, tag mutation, asset mutation, version bump, bundled-solver
claims, or certification claims.

## Non-Action Flags

Future boundary review must show false/safety states for:

- `runtime_reload_acceptance_performed`
- `project_schema_mutated`
- `project_schema_field_added`
- `project_schema_migration_performed`
- `project_schema_validation_evidence_created`
- `default_reload_path_used`
- `background_reload_performed`
- `directory_scan_performed`
- `network_fetch_performed`
- `plugin_package_imported`
- `cli_subprocess_used`
- `gui_subprocess_used`
- `reloadable_bundle_created`
- `export_file_created`
- `report_file_created`
- `clipboard_used`
- `report_attached`
- `output_folder_opened`
- `live_discovery_executed`
- `passive_refresh_executed`
- `validation_executed`
- `solver_executed`
- `dependency_installed`
- `dependency_uninstalled`
- `solver_uninstalled`
- `candidate_activated`
- `trust_restored`
- `issue_mutated`
- `release_mutated`
- `tag_mutated`
- `asset_mutated`
- `version_bumped`
- `validation_pass_claimed`
- `validation_fail_claimed`
- `issue_closure_claimed`
- `bundled_solver_claimed`
- `certification_claimed`

False/safety states are not proof of validation. They only preserve the
non-action boundary for review.

## Disabled/Future Actions

These actions remain disabled/future-only:

- `import_persistence_record_to_project_schema`
- `import_summary_audit_to_project_schema`
- `mutate_project_schema`
- `migrate_project_schema`
- `create_project_validation_evidence`
- `accept_for_session_review`
- `accept_as_trusted`
- `activate_reloaded_candidate`
- `refresh_discovery`
- `validate_solver`
- `execute_solver`
- `install_dependency`
- `uninstall_dependency`
- `uninstall_solver`
- `create_export_summary`
- `create_report_file`
- `create_reloadable_bundle`
- `copy_to_clipboard`
- `attach_to_report`
- `open_output_folder`
- `close_issue`
- `mutate_release`
- `push_tag`
- `upload_asset`
- `claim_validation_success`
- `claim_validation_failure`
- `claim_certification`

Disabled/future actions remain absent from this gate. They are not hidden
actions, callbacks, subprocesses, CLI calls, GUI calls, writer calls, reader
calls, or ProjectSchema mutations.

## Relationship To OSW-EXP-136 Summary Audit

The OSW-EXP-136 summary audit remains supplied-record-only. Summary audit is not
ProjectSchema state. This gate does not invoke summary audit implementation.

A future boundary may display supplied summary audit output only. It must not
read audit files, invoke the audit implementation to discover state, convert
summary audit rows to ProjectSchema fields, or treat audit rows as validation
evidence.

## Relationship To OSW-EXP-134 CLI Write And OSW-EXP-132 GUI Write

CLI/GUI writes are local review-record persistence only. Write success does not
imply ProjectSchema mutation. Write success does not imply validation evidence.

This gate does not invoke CLI/GUI and does not add CLI behavior or GUI behavior.
Any future display of CLI/GUI write output must consume supplied records and
preserve the ProjectSchema boundary.

## Relationship To OSW-EXP-126 Writer

The writer creates local review-record payloads only. The writer does not mutate
ProjectSchema. This gate does not call writer.

Future ProjectSchema integration must not bypass writer diagnostics, writer
redaction, writer schema/version review, writer bytes/hash evidence, or writer
limitation state. Even then, writer output remains non-authoritative until a
separate ProjectSchema gate accepts it as a reviewed input.

## Relationship To OSW-EXP-125 Persistence View-Model

The persistence view-model remains UX readiness and review state. It is not
ProjectSchema readiness. It is not ProjectSchema validation evidence.

Future ProjectSchema work must not treat view-model readiness as a project
mutation precondition without separate prepared-machine validation, provenance,
schema, stale-source, conflict, unsafe-claim, acknowledgement, redaction, and
issue/release separation review.

## Relationship To Reload Acceptance GUI/CLI

Acceptance GUI/CLI remain review-only. Acceptance success does not imply
ProjectSchema mutation. Acceptance success does not imply validation or trust.

Runtime reload acceptance remains separate from local persistence and from
ProjectSchema state. This gate does not accept runtime reload and does not add
acceptance commands, buttons, callbacks, or state mutation.

## Relationship To Reload File Reader And Explicit-Path Preview

The reload file reader remains explicit-path and bounded. ProjectSchema boundary
does not read input state files. Preview success does not imply ProjectSchema
mutation.

This gate performs no file reading, no file parsing, no input state-file
reading, no input state-file parsing, and no reload file-reader invocation.

## Relationship To Live Optional Validation Issues

Issues #6 through #11 remain open. Boundary output is not live optional
validation. Prepared-machine validation remains separate. Issue state is not
mutated.

Skipped-missing validation remains skipped-missing. No boundary record may turn
missing optional solver/package evidence into validation success, validation
failure, issue closure, release mutation, bundled-solver support, or
certification.

## Security/Privacy Review

The boundary requires:

- no raw path leak;
- no secret leak;
- no full file content display;
- no plugin code display;
- no remote URL fetch;
- no script execution;
- no plugin import;
- no solver execution;
- malicious payload remains rejected/blocked data;
- diagnostics remain redacted.

Security/privacy review must block ProjectSchema integration when raw paths,
secrets, tokens, API keys, full file contents, plugin code, untrusted remote
URLs, executable content, or solver execution assumptions appear in supplied
records.

## Non-Actions

This gate does not:

- implement ProjectSchema behavior;
- edit ProjectSchema source;
- edit ProjectSchema tests;
- edit source;
- edit CLI source;
- edit GUI source;
- edit experimental optional-solver source;
- invoke writer;
- read/write files;
- parse files;
- read input state files;
- parse input state files;
- invoke reload file reader;
- invoke OSW-EXP-102 state writer;
- call CLI/GUI;
- use subprocess;
- accept runtime reload;
- mutate active acceptance;
- mutate ProjectSchema;
- add ProjectSchema fields/migration;
- create ProjectSchema validation evidence;
- run discovery/validation/solver execution;
- install/uninstall dependencies;
- uninstall solvers;
- activate candidates;
- restore trust;
- mutate issues/releases/tags/assets;
- bump versions;
- create reloadable bundles, export files, or report files;
- use clipboard, report attachment, or open-output-folder behavior;
- claim validation success, validation failure, issue closure, bundled solver
  support, or certification.

## Future Implementation Test Plan

Future OSW-EXP-138 or repo-consistent implementation gate must test:

- boundary model consumes supplied records only;
- no ProjectSchema source edit;
- no ProjectSchema mutation;
- no ProjectSchema fields;
- no ProjectSchema migration;
- no ProjectSchema validation evidence;
- no file IO;
- no writer invocation;
- no reader invocation;
- no CLI/GUI calls;
- no subprocess;
- no validation/solver execution;
- ProjectSchema import blocked;
- ProjectSchema validation evidence blocked;
- trust restoration blocked;
- activation blocked;
- issue/release/certification blocked;
- redaction;
- non-action flags;
- diagnostics;
- prepared-machine validation separation.

Implementation tests must also keep issues #6 through #11 open until a
dedicated prepared-machine validation and issue/release gate provides separate
evidence.

## Future Gates

Suggested future sequence:

- `OSW-EXP-138_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_IMPLEMENTATION`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` if a prepared
  machine is available
- `OSW-EXP-139_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_RELEASE_AUDIT_DESIGN`
  if needed

Those gates must not be collapsed into this design gate. This document only
defines the ProjectSchema boundary contract.
