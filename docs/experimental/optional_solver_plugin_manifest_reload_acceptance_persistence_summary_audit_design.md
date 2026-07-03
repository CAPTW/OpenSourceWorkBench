# Optional Solver Plugin Manifest Reload Acceptance Persistence Summary Audit Design

## Status

This gate is design-only.

It adds no summary audit implementation, no CLI source edits, no GUI source
edits, no source edits, no writer invocation, no file writes, no file reading,
no file parsing, no input state file reading, no input state file parsing, no
reload file-reader invocation, no OSW-EXP-102 state-writer invocation, no CLI
behavior, no GUI behavior, no CLI subprocess, no GUI subprocess, and no
subprocess use.

It adds no runtime reload acceptance, no active acceptance mutation, no
ProjectSchema mutation, no default target path, no background write, no
directory scan, no network fetch, no plugin package import, no reloadable bundle
creation, no export file creation, no report file creation, no clipboard
behavior, no report attachment, no open-output-folder behavior, no live
discovery, no passive refresh, no validation execution, no solver execution, no
dependency installation, no dependency uninstall, no solver uninstall, no
automatic activation, no trust restoration, no issue mutation, no release
mutation, no tag mutation, no asset mutation, no version bump, no
validation-pass claim, no validation-fail claim, no issue-closure claim, no
bundled-solver claim, and no certification claim.

## Purpose

This document defines a future summary/audit surface for the optional solver
plugin manifest reload acceptance persistence chain. The future surface would
summarize supplied persistence view-model records, supplied writer records,
supplied CLI write records, and supplied GUI write records without becoming an
authoritative acceptance or validation layer.

The design preserves the boundary between preview, acceptance review,
persistence review, local review-record write, summary audit, runtime
acceptance, ProjectSchema state, validation, issue/release state, and
certification.

## Current Persistence Chain

- OSW-EXP-124 defines reload acceptance persistence design.
- OSW-EXP-125 implements the reload acceptance persistence view-model.
- OSW-EXP-126 implements the explicit-path, dry-run-first writer for local
  review records.
- OSW-EXP-128 implements a stdout-first, dry-run-only CLI review and write-plan
  surface.
- OSW-EXP-130 implements a display-only GUI review panel.
- OSW-EXP-132 implements an explicit-target, dry-run-first GUI write panel.
- OSW-EXP-134 implements an explicit-target, dry-run-first CLI write workflow.

No summary/audit surface exists yet. No prepared-machine validation result is
created by this chain. No runtime reload acceptance exists in this chain.

## Future Summary/Audit Surface Definition

The future summary/audit surface is a non-authoritative review surface over
supplied records. It may be a CLI command, GUI panel, in-memory report model, or
other review-only presentation, but this gate does not implement any of those.

The future surface may summarize:

- chain coverage from OSW-EXP-124 through OSW-EXP-134;
- available review and write surfaces;
- persistence view-model readiness;
- writer dry-run and write results;
- CLI review, CLI write, GUI review, and GUI write records;
- acknowledgements and confirmation state;
- expiry and invalidation state;
- redaction and target/storage policy state;
- provenance and trust limitations;
- stale-source, conflict, unsafe-claim, and evidence/history states;
- diagnostics, non-action flags, disabled/future actions, and safety guidance;
- live optional validation separation and prepared-machine validation state, if
  supplied separately.

The future surface must remain non-authoritative: it does not accept runtime
reload, mutate ProjectSchema, validate solvers, close issues, mutate releases,
or certify solver/plugin support.

## Input Policy

The future summary/audit surface may consume supplied persistence view-model
mappings, supplied writer result mappings, supplied CLI write result mappings,
supplied GUI write result mappings, supplied summary metadata, supplied
issue-state snapshot if separately provided and redacted, and supplied
prepared-machine validation status if separately provided.

The future summary/audit surface must not perform file reading, file parsing,
input state file reading, input state file parsing, reload file-reader
invocation, OSW-EXP-102 state-writer invocation, writer invocation, CLI calls,
GUI calls, subprocess use, GitHub issue queries, GitHub release queries,
network fetches, directory scans, discovery execution, validation execution, or
solver execution. It must not display raw file content or plugin code.

## Future Audit Sections

A future audit should include these sections:

- chain summary;
- surface inventory;
- persistence view-model summary;
- writer summary;
- CLI review/plan summary;
- CLI write summary;
- GUI review summary;
- GUI write summary;
- acknowledgement summary;
- expiry/invalidation summary;
- target/storage policy summary;
- schema/migration summary;
- redaction/privacy summary;
- provenance/trust summary;
- stale-source/re-preview summary;
- conflict/shared-stack summary;
- unsafe-claim summary;
- evidence/history summary;
- diagnostics summary;
- non-action flags summary;
- disabled/future actions summary;
- validation/prepared-machine separation;
- issue/release/certification separation;
- remaining gaps;
- next gates.

## Chain Coverage Summary

The future chain summary should list each gate id, artifact type, implementation
status, safety boundary summary, proof status, non-authoritative caveat, and
follow-up gate. At minimum:

| Gate | Artifact type | Summary audit treatment |
| --- | --- | --- |
| OSW-EXP-124 | design | Persistence semantics design only. |
| OSW-EXP-125 | view-model | Supplied-record readiness and safety state. |
| OSW-EXP-126 | writer | Explicit-path, dry-run-first local review-record writer. |
| OSW-EXP-128 | CLI review | Stdout-first review and dry-run writer planning. |
| OSW-EXP-130 | GUI review | Display-only PySide review panel. |
| OSW-EXP-132 | GUI write | Explicit-target GUI local review-record write. |
| OSW-EXP-134 | CLI write | Explicit-target CLI local review-record write. |

Each row must state that the record is not runtime acceptance, not validation
evidence, not ProjectSchema state, not issue closure, not release mutation, and
not certification.

## CLI/GUI Write Summary

For supplied CLI or GUI write records, the future summary may render:

- source surface: CLI or GUI;
- redacted target display;
- dry-run SHA-256;
- final write SHA-256;
- payload kind and schema version;
- bytes count;
- status;
- blockers, warnings, and diagnostics;
- acknowledgement and confirmation state;
- replacement policy;
- cleanup status and temp-file status;
- local-review-record-only caveat.

The summary must never treat matching hashes, a successful write status, or a
clean diagnostic list as validation success, validation failure, runtime
acceptance, ProjectSchema mutation, trust restoration, automatic activation,
issue closure, release mutation, bundled solver support, or certification.

## Non-Authoritative Record Policy

Persisted reload acceptance records and summary/audit output are local
review-state only. They are not runtime reload acceptance, not validation
evidence, not validation failure, not ProjectSchema state, not trust
restoration, not automatic activation, not discovery success, not dependency
installation, not solver execution, not issue closure, not release mutation,
not bundled solver support, and not certification.

The future audit may report `persistence_write_performed` only when a supplied
record says the OSW-EXP-126 writer completed an explicit local review-record
write. That flag never means runtime reload acceptance.

## Acknowledgement Summary

The future summary must render acknowledgement coverage and expiry for:

- `acceptance_not_validation`
- `acceptance_not_validation_failure`
- `acceptance_not_trust_restoration`
- `acceptance_not_automatic_activation`
- `acceptance_not_discovery_success`
- `acceptance_not_dependency_install`
- `acceptance_no_solver_execution`
- `acceptance_not_issue_closure`
- `acceptance_not_release_mutation`
- `acceptance_not_certification`
- `acceptance_not_persistence_write`
- `acceptance_not_project_schema_mutation`
- `redaction_reviewed`
- `unredacted_paths_blocked`
- `stale_source_requires_repreview`
- `untrusted_source_remains_untrusted`
- `activation_review_required_after_acceptance`
- `no_discovery_execution`
- `no_plugin_package_import`
- `no_validation_execution`
- `no_solver_execution`
- `trust_label_not_certification`
- `persisted_acknowledgements_may_expire`

Acknowledgements are not validation evidence and not trust restoration.
Missing, stale, or expired acknowledgements must block any future authoritative
summary language.

## Expiry / Invalidation Summary

The future summary must surface expiry and invalidation reasons, including:

- reload;
- target change;
- source fingerprint change;
- schema version change;
- unsafe claim appearance;
- trust policy change;
- future discovery-refresh result;
- file reader policy change;
- GUI file-dialog policy change;
- CLI explicit-path policy change;
- acceptance policy change;
- ProjectSchema policy change;
- validation issue state change;
- persistence schema change;
- persistence storage-policy change;
- persistence CLI policy change;
- persistence GUI policy change;
- writer policy change;
- summary audit policy change.

Expiry is not validation failure. It means the review record must be revisited
before any future flow relies on it.

## Target/Storage Policy Summary

The future summary must show explicit target policy without exposing raw paths
by default. It must render:

- explicit target only;
- no default target path;
- no background write;
- no directory scan;
- no parent directory creation by the summary/audit surface;
- writer-owned target path safety;
- redacted target display;
- explicit replacement policy;
- local-review-record-only caveat.

The summary/audit surface must not select targets, create directories, scan
directories, or write files.

## Schema/Migration Summary

The future summary must render payload kind, schema version, schema mismatch,
unsupported schema, and migration required state. Schema mismatch is not
validation failure. The persistence schema remains separate from ProjectSchema.
The summary/audit surface does not repair, rewrite, or migrate files.

## Redaction/Privacy Summary

The future summary must keep raw paths hidden by default. It should prefer
basename, hash, source id, or display name. Secrets, tokens, and API keys must
be blocked. Any unredacted path allowance requires a future explicit policy.
Fingerprints are not trust signals. Diagnostics must use redacted context. The
summary must not print full file content and must not display plugin code.

## Provenance/Trust Summary

The future summary should render persistence view-model source, acceptance state
id, preview identifier, payload fingerprint if safe, writer `generated_by`
metadata, CLI/GUI surface identity, limitations, and untrusted-by-default
source state. A trust label is not certification.

## Stale-Source/Re-Preview Summary

The future summary must state that an old preview is not silently trusted.
Missing, moved, or changed sources require re-preview. The summary/audit
surface does not inspect referenced source files. Stale-source state is not
validation failure. Re-preview remains separately gated.

## Conflict/Shared-Stack Summary

The future summary must render conflicts and shared-stack warnings. Built-ins
win by default. A persisted acceptance record does not override built-ins. The
summary/audit surface does not resolve conflicts. Future policy is required for
any conflict resolution.

## Unsafe-Claim Summary

Unsafe claims must be visible and blocked. The future summary must not persist
or restate unsafe claims as truth. It must block validation success claims,
validation failure claims, issue closure claims, release mutation claims,
bundled solver claims, dependency installation claims, solver execution claims,
trust restoration claims, and certification claims.

## Evidence/History Summary

Deactivation/reactivation history and historical evidence are reference-only.
Skipped-missing remains skipped-missing. A persisted record and summary audit
are not validation evidence. The summary/audit surface performs no evidence
deletion or rewrite and implies no issue closure.

## Diagnostics Vocabulary

The prefix `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_*` is reserved
for future summary/audit diagnostics.

Reserve these diagnostics for a future summary/audit implementation:

- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_UNAVAILABLE`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_INPUT_MISSING`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_CHAIN_INCOMPLETE`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_WRITE_RECORD_MISSING`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_ACK_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_EXPIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_STALE_SOURCE`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_CONFLICT_VISIBLE`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_UNSAFE_CLAIM_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_NO_VALIDATION_CLAIM`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_NO_PROJECT_SCHEMA_MUTATION`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_READY_FOR_PREPARED_MACHINE_REVIEW`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_ERROR`

The future summary must surface OSW-EXP-125 through OSW-EXP-134 diagnostics
without rewriting them as truth.

## Non-Action Flags

The future summary must render false or safety states for:

- `runtime_reload_acceptance_performed`
- `project_schema_mutated`
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

`persistence_write_performed` may only mean explicit local review-record write
from the OSW-EXP-126 writer and never runtime acceptance.

## Disabled/Future Actions

The future summary must render these actions as disabled or future-only unless
a later gate explicitly implements them:

- `accept_for_session_review`
- `accept_as_trusted`
- `activate_reloaded_candidate`
- `refresh_discovery`
- `validate_solver`
- `execute_solver`
- `install_dependency`
- `uninstall_dependency`
- `uninstall_solver`
- `mutate_project_schema`
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

## Relationship To OSW-EXP-134 CLI Write

OSW-EXP-134 provides explicit-target, dry-run-first CLI local review-record
writes. The future summary may display supplied CLI write output. It does not
call the CLI, use CLI subprocesses, infer runtime acceptance from CLI success,
or treat CLI output as validation evidence.

## Relationship To OSW-EXP-132 GUI Write

OSW-EXP-132 provides explicit-target, dry-run-first GUI local review-record
writes. The future summary may display supplied GUI write records. It does not
call GUI behavior, invoke GUI subprocesses, infer runtime acceptance from GUI
success, or treat GUI output as validation evidence.

## Relationship To OSW-EXP-126 Writer

The OSW-EXP-126 writer remains the only persistence writer for local review
records in this line. The future summary does not invoke the writer and does
not bypass writer path, redaction, acknowledgement, dry-run, confirmation, or
replacement policies.

## Relationship To OSW-EXP-125 Persistence View-Model

The persistence view-model remains the source of readiness and persistence
review state. The future summary consumes supplied records and does not compute
independent acceptance policy.

## Relationship To Reload Acceptance GUI/CLI

Existing reload acceptance GUI and CLI surfaces remain review-only. Persistence
success does not imply acceptance success. Acceptance success does not imply
persistence success. Neither success implies runtime reload acceptance.

## Relationship To Reload File Reader And Explicit-Path Preview

The reload file reader remains explicit-path and bounded. The future summary
does not read input state files, parse input state files, or invoke the reload
file reader. Preview success does not imply acceptance, persistence, validation,
or certification.

## Relationship To ProjectSchema

The future summary performs no ProjectSchema mutation. Persistence records are
not ProjectSchema state and not project validation evidence. Any future
ProjectSchema integration requires a separate gate.

## Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. The future summary is not live optional
validation and is not prepared-machine validation. Skipped-missing remains
skipped-missing. Prepared-machine validation remains a separate gate.

## Security/Privacy Review

The future summary must preserve no raw path leak, no secret leak, no full file
content display, no plugin code display, no remote URL fetch, no script
execution, no plugin import, and no solver execution. A malicious payload
remains rejected or blocked data. Writer diagnostics remain redacted.

## Non-Actions

This gate does not implement summary audit behavior, edit CLI source, edit GUI
source, edit source, invoke writer, write files, read files, parse files, read
input state files, parse input state files, invoke reload file reader, invoke
OSW-EXP-102 state writer, call CLI, call GUI, use CLI subprocesses, use GUI
subprocesses, use subprocesses, accept runtime reload, perform active
acceptance mutation, mutate ProjectSchema, add default target path, add
background write, scan directories, fetch network manifests, import plugin
packages, create reloadable bundles, create export files, create report files,
add clipboard behavior, add report attachment, add open-output-folder behavior,
add live discovery, add passive refresh, run validation execution, run solver
execution, install dependencies, uninstall dependencies, uninstall solvers,
automatically activate candidates, restore trust, mutate issues, mutate
releases, mutate tags, mutate assets, bump versions, claim validation success,
claim validation failure, claim issue closure, claim bundled solver support, or
claim certification.

## Future Implementation Test Plan

OSW-EXP-136 should test that a future summary/audit implementation:

- imports without heavy optional dependencies;
- consumes supplied persistence view-model records;
- consumes supplied writer result records;
- consumes supplied CLI write result records;
- consumes supplied GUI write result records;
- constructs without file writes;
- refreshes without file writes;
- does not read files;
- does not parse files;
- does not invoke the reload file reader;
- does not invoke the OSW-EXP-102 state writer;
- does not invoke the writer;
- does not call CLI or GUI behavior;
- uses no subprocesses;
- renders chain coverage;
- renders CLI/GUI write summaries;
- renders acknowledgements, expiry, target/storage policy, schema/migration,
  redaction/privacy, provenance/trust, stale-source, conflict/shared-stack,
  unsafe-claim, evidence/history, diagnostics, non-action flags, and
  disabled/future actions;
- preserves no ProjectSchema mutation;
- preserves no discovery/validation/solver execution;
- preserves no issue/release/tag/asset mutation;
- makes no validation-pass, validation-fail, issue-closure, bundled-solver, or
  certification claim.

## Future Gates

Suggested next gates:

- OSW-EXP-136_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_IMPLEMENTATION
- OSW-EXP-137_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_DESIGN,
  if needed
- OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION, if a prepared
  machine is available

## OSW-EXP-136 Implementation Follow-Up

OSW-EXP-136 implements this design as a pure in-memory supplied-record summary
audit
([optional_solver_plugin_manifest_reload_acceptance_persistence_summary_audit_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_summary_audit_implementation.md)).
The implementation preserves this design's non-authoritative boundary: no
writer invocation, no file reads or writes, no input state-file parsing, no
reload file-reader or OSW-EXP-102 state-writer invocation, no CLI/GUI calls, no
subprocess use, no runtime reload acceptance, no ProjectSchema mutation, no
discovery/validation/solver execution, no activation or trust restoration, no
issue/release/tag/asset mutation, and no certification claim.
