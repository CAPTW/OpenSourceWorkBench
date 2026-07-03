# Optional Solver Plugin Manifest Reload Acceptance Persistence CLI Write Design

## 1. Status

Design-only.

This gate adds no CLI write implementation, no CLI source edits, no source
edits, no writer invocation, no file writes, no file reading, no file parsing,
no input state file reading, no input state file parsing, no reload
file-reader invocation, no OSW-EXP-102 state-writer invocation, no GUI
behavior, no GUI subprocess, and no subprocess use.

It performs no runtime reload acceptance, no active acceptance mutation, no
ProjectSchema mutation, no default target path, no background write, no
directory scan, no network fetch, no plugin package import, no reloadable
bundle creation, no export file creation, no report file creation, no
clipboard behavior, no report attachment, no open-output-folder behavior, no
live discovery, no passive refresh, no validation execution, no solver
execution, no dependency installation, no dependency uninstall, no solver
uninstall, no automatic activation, no trust restoration, no issue mutation,
no release mutation, no tag mutation, no asset mutation, no version bump, no
validation-pass claim, no validation-fail claim, no issue-closure claim, no
bundled-solver claim, and no certification claim.

## 2. Purpose

This document designs a future explicit-target, dry-run-first,
acknowledgement-gated, confirmation-gated CLI write workflow for optional
solver plugin manifest reload acceptance persistence records.

The design builds on:

- OSW-EXP-125 reload acceptance persistence view-model records.
- OSW-EXP-126 reload acceptance persistence writer plans and results.
- OSW-EXP-128 dry-run-only persistence CLI review/plan behavior.
- OSW-EXP-132 GUI write policy for explicit target, fresh dry-run,
  acknowledgement, and confirmation gates.

The future CLI write path is only for local review-record persistence. It is
not runtime reload acceptance, not validation success, not validation failure,
not ProjectSchema mutation, not trust restoration, not automatic activation,
not issue closure, not release mutation, and not certification.

## 3. Current State Before CLI Write

Reload acceptance persistence already has a pure view-model, an explicit-path
dry-run-first writer, a dry-run-only CLI review surface, a display-only GUI
review panel, and an explicit GUI write panel.

No CLI actual-write command exists. OSW-EXP-128 keeps `write-future` disabled
and future-only. This gate does not change that command, does not edit CLI
source, does not call the writer, and does not write local persistence records.

## 4. Future CLI Write Workflow Definition

A future CLI write workflow may extend
`optional-solver-plugin-manifest-reload-acceptance-persistence` to persist a
local review record only after all of these gates pass:

1. The command receives a supplied persistence view-model record or a
   separately gated safe in-memory integration source.
2. The caller supplies an explicit target path.
3. The CLI performs a dry-run plan first.
4. The dry-run result is fresh for the current view-model, target, schema, and
   replacement policy.
5. Required acknowledgements are present and not expired.
6. The caller supplies explicit write confirmation.
7. Replacement is separately acknowledged when the target exists.
8. The OSW-EXP-126 writer remains the only actual write API.

The workflow must not create runtime accepted state, mutate ProjectSchema, run
discovery, run validation, execute solvers, install dependencies, activate
candidates, restore trust, close issues, mutate releases, push tags, upload
assets, or claim certification.

## 5. Future CLI Command Vocabulary

The future command family should remain:

`python -m osw.cli optional-solver-plugin-manifest-reload-acceptance-persistence <subcommand>`

Future CLI write vocabulary may include:

- `plan` for dry-run writer planning.
- `write` for the separately gated actual local review-record write.
- `write-future` while implementation remains disabled.
- `--target <path>` for explicit caller-supplied targets.
- `--dry-run` to force planning-only output.
- `--acknowledge-local-persistence` for the persistence acknowledgement gate.
- `--confirm-write` for the final write confirmation gate.
- `--allow-replace` for explicit existing-target replacement policy.
- `--format text|json` for stdout-first output.

This gate adds no parser, no command registration, no CLI behavior, and no
path handling.

## 6. Future CLI User Flow

Suggested future states:

- `write_not_requested`
- `target_required`
- `target_redacted`
- `dry_run_required`
- `dry_run_plan_available`
- `dry_run_plan_blocked`
- `acknowledgement_required`
- `confirmation_required`
- `replace_acknowledgement_required`
- `stale_dry_run_replan_required`
- `redaction_blocked`
- `schema_or_migration_blocked`
- `stale_source_repreview_required`
- `conflict_review_required`
- `unsafe_claim_blocked`
- `writer_invocation_ready`
- `writer_result_completed`
- `writer_result_blocked`
- `runtime_acceptance_still_required`
- `persistence_error`

Every state remains local review-record state only.

## 7. Input Policy

The future CLI write workflow consumes supplied persistence view-model records
and supplied writer dry-run/result mappings. It must not read input state
files, parse input state files, invoke the reload file reader, invoke the
OSW-EXP-102 state writer, call GUI code, use GUI subprocesses, use
subprocesses, display raw file content, display plugin code, select a default
target path, perform a background write, scan directories, fetch network
manifests, or import plugin packages.

## 8. Target Policy

Future target handling must be explicit and redacted.

The future CLI must:

- require `--target` for actual writes;
- use no default target path;
- perform no write during target parsing;
- create no directories;
- scan no directories;
- reject directory targets;
- block symlink targets unless a later gate explicitly changes policy;
- block missing parents;
- block existing targets unless `--allow-replace` and replacement
  acknowledgement are present;
- display a redacted target label;
- never imply runtime acceptance;
- never imply validation evidence.

## 9. Dry-Run Policy

Dry-run planning is mandatory before any write. It should render dry-run state,
planned status, payload kind, schema version, byte count, SHA-256, target
display, replacement state, blockers, warnings, diagnostics, non-action flags,
disabled/future actions, and safety guidance.

Dry-run success is not a write, not runtime reload acceptance, not validation
success, not validation failure, not ProjectSchema mutation, not trust
restoration, not automatic activation, not issue closure, not release
mutation, and not certification.

## 10. Write Preconditions

Future CLI actual write must require:

- supplied persistence view-model record;
- explicit target path;
- successful fresh dry-run for the same target and request;
- required acknowledgements present and unexpired;
- explicit write confirmation;
- explicit replacement permission when needed;
- supported persistence schema;
- no migration blocker;
- no stale-source blocker;
- no conflict/shared-stack blocker;
- no unsafe-claim blocker;
- no unredacted path blocker;
- no secret-like value blocker;
- writer result safety checks from OSW-EXP-126.

Missing preconditions must block without writer invocation.

## 11. Write Confirmation Policy

Future CLI writes require a dedicated confirmation flag such as
`--confirm-write`. Acknowledgement alone is not confirmation. Confirmation
alone is not acknowledgement.

Confirmation text must state that the write is only local review-record
persistence and remains non-authoritative. It must state that write completion
does not accept runtime reload, mutate ProjectSchema, validate solvers, install
dependencies, execute solvers, activate candidates, restore trust, close
issues, mutate releases, or certify support.

## 12. Replacement Policy

Future CLI replacement must be opt-in. Existing targets block by default.

When replacement is requested, the CLI must still require dry-run, explicit
replacement acknowledgement, local review-record acknowledgement, and final
write confirmation. Replacement must not delete unrelated files, scan
directories, create directories, or imply migration of old payloads.

## 13. Writer Invocation Boundary

This design gate invokes no writer.

A future implementation may invoke only the OSW-EXP-126 reload acceptance
persistence writer. It must not invoke the OSW-EXP-102 state writer, reload
file reader, CLI subprocesses, GUI subprocesses, solver runners, validation
tools, discovery paths, dependency installers, or plugin import paths.

The future CLI must not bypass writer path, redaction, schema, acknowledgement,
payload safety, atomic write, or cleanup policies.

## 14. Writer Result Output

Future output must render:

- writer status;
- target display;
- dry-run versus actual write;
- planned and written booleans;
- byte count;
- SHA-256;
- payload kind;
- schema version;
- cleanup status;
- temporary-file status;
- diagnostics;
- warnings;
- blockers;
- local-review-record-only caveat.

Writer completion means only an explicit local review-record persistence file
was written. It is not runtime acceptance, ProjectSchema state, validation
evidence, issue state, release state, or certification.

## 15. Acknowledgement Output

Future CLI output must render acknowledgement IDs and their required,
satisfied, missing, expired, and blocking states:

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

Acknowledgements are not validation evidence, not validation failure, not trust
restoration, not automatic activation, not discovery success, not issue
closure, not release mutation, and not certification. Missing or expired
acknowledgements block future CLI writes.

## 16. Expiry / Invalidation Policy

Future CLI writes must invalidate dry-run and acknowledgement state when any of
these change:

- reload;
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
- CLI write policy change;
- dry-run payload hash change;
- target path change;
- replacement policy change.

Invalidated state must require re-plan before write.

## 17. Schema/Migration Policy

Future output must render payload kind, schema version, expected writer schema,
schema mismatch, unsupported schema, migration required, and migration blocked
states.

Schema mismatch is not validation failure. The persistence schema remains
separate from ProjectSchema. The CLI must not repair files, migrate files, or
mutate ProjectSchema.

## 18. Redaction/Privacy Policy

Future CLI output must hide raw paths by default and prefer basename, hash,
source id, or display-name labels. Secrets, tokens, API keys, bearer strings,
password-like values, unredacted home paths, and environment-variable-looking
values must be blocked or redacted.

Fingerprints are diagnostic context, not trust signals. Diagnostics must use
redacted context. The CLI must not display full file content or plugin code.

## 19. Provenance Output

Future CLI output should render supplied persistence view-model source,
acceptance state id, preview identifier, safe payload fingerprint, writer
generated-by metadata, limitations, untrusted-by-default source labels, and
trust-label caveats.

Provenance remains reference-only. Trust labels are not certification.

## 20. Candidate Lifecycle Output

Future CLI output must keep candidate lifecycle state review-only:

- inactive previews remain review-only;
- persisted active state requires future activation review;
- deactivated candidates remain deactivated review state;
- reactivation routes to a future activation review;
- discovery-refresh state remains review state;
- no automatic activation;
- no trust restoration;
- persisted records do not override built-ins.

## 21. Stale-Source/Re-Preview Output

Future output must state that old previews are not silently trusted. Missing,
moved, or changed sources require re-preview. CLI write planning and actual
write must not inspect referenced source files.

Stale-source state is not validation failure. Re-preview remains separately
gated.

## 22. Conflict/Shared-Stack Output

Future output must render conflicts and shared-stack warnings. Built-ins win by
default. Persisted acceptance records do not override built-ins. The CLI must
not resolve conflicts, choose trusted winners, install stacks, uninstall
stacks, or mutate runtime activation state.

## 23. Unsafe-Claim Output

Future output must show unsafe claims as blocked review data, not truth. The
CLI must block validation success claims, validation failure claims, issue
closure claims, release mutation claims, bundled solver claims, dependency
installation claims, solver execution claims, trust restoration claims, and
certification claims.

## 24. Evidence/History Output

Future CLI output must retain deactivation/reactivation history and historical
evidence as reference-only context. Skipped-missing remains skipped-missing.
Persisted records are not validation evidence. The CLI must not delete,
rewrite, elevate, or reinterpret evidence and must not imply issue closure.

## 25. Diagnostics Vocabulary

Reserve `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_*` diagnostics:

- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_UNAVAILABLE`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_NOT_REQUESTED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_DRY_RUN_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_TARGET_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_TARGET_REDACTED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_ACK_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_CONFIRM_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_REPLACE_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_STALE_DRY_RUN`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_DRY_RUN_NOT_WRITE`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_COMPLETED_LOCAL_ONLY`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_NOT_RUNTIME_ACCEPTANCE`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_NO_VALIDATION_CLAIM`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_NO_PROJECT_SCHEMA_MUTATION`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_ERROR`

The future CLI must also surface OSW-EXP-125, OSW-EXP-126, and OSW-EXP-128
diagnostics without rewriting them as validation truth.

## 26. Exit-Code Policy

Future CLI exit code `0` means command completion only. It is not validation
success, not validation failure, not runtime acceptance, not persistence
authority, not ProjectSchema mutation, not issue closure, not release mutation,
and not certification.

Recommended future nonzero meanings:

- `2`: usage error, missing explicit target, missing acknowledgement, missing
  confirmation, stale dry-run, or blocked write precondition.
- `3`: writer blocked local review-record persistence.
- `4`: writer error while attempting an explicitly confirmed local write.

Nonzero exit codes are CLI/request/write diagnostics only; they are not solver
validation failure.

## 27. Non-Action Flags

Future text and JSON output must include false or safety states for:

- `runtime_reload_acceptance_performed`
- `active_acceptance_mutation_performed`
- `project_schema_mutated`
- `default_reload_path_used`
- `default_target_path_used`
- `background_reload_performed`
- `background_write_performed`
- `directory_scan_performed`
- `network_fetch_performed`
- `plugin_package_imported`
- `input_state_file_read`
- `input_state_file_parsed`
- `reload_file_reader_invoked`
- `state_writer_invoked`
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

Future `persistence_write_performed` may only mean an explicit local
review-record write and never runtime acceptance.

## 28. Disabled/Future Actions

Future CLI output must render disabled/future actions:

- `request_dry_run_plan`
- `write_persistence_record`
- `persist_acceptance_record`
- `write_acceptance_state`
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

These are review rows unless a later gate implements a specific action.

## 29. Relationship To OSW-EXP-128 CLI

OSW-EXP-128 remains stdout-first and dry-run-only. This gate does not edit that
CLI and does not change `write-future`. A future write implementation must
preserve OSW-EXP-128 output determinism, redaction, non-action flags,
diagnostics, and exit-code honesty.

OSW-EXP-128 command success does not imply CLI persistence, GUI persistence,
runtime acceptance, validation evidence, issue closure, release mutation, or
certification.

## 30. Relationship To OSW-EXP-132 GUI Write Panel

OSW-EXP-132 is the existing explicit-target, dry-run-first,
acknowledgement-gated, confirmation-gated GUI write implementation. A future
CLI write workflow should align with those safety gates but must not call GUI
code, use GUI subprocesses, or depend on PySide.

GUI write success and future CLI write success both remain local
review-record-only outcomes.

## 31. Relationship To OSW-EXP-126 Writer

The OSW-EXP-126 writer remains the only allowed future write API for reload
acceptance persistence records. The future CLI may call it only after explicit
target, fresh dry-run, acknowledgement, confirmation, and replacement gates
pass.

This design invokes no writer and edits no writer source.

## 32. Relationship To OSW-EXP-125 Persistence View-Model

The OSW-EXP-125 persistence view-model remains the source of readiness,
storage policy, dry-run requirements, acknowledgements, expiry, blockers,
diagnostics, non-action flags, disabled/future actions, provenance,
evidence/history, and safety guidance.

The future CLI must not compute independent reload acceptance policy.

## 33. Relationship To Reload Acceptance GUI/CLI

Existing reload acceptance GUI and CLI surfaces remain review-only.
Persistence write review is separate from acceptance review. Acceptance review
success does not imply persistence. Persistence write success does not imply
runtime acceptance.

## 34. Relationship To Reload File Reader And Explicit-Path Preview

The reload file reader remains explicit-path and bounded. CLI write must not
read input state files, parse input state files, or invoke the reload file
reader. Explicit-path preview success does not imply acceptance, persistence,
or runtime trust.

## 35. Relationship To ProjectSchema

No ProjectSchema mutation is allowed. A persistence record is not
ProjectSchema state and not project validation evidence. Future ProjectSchema
integration requires a separate gate.

## 36. Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. Reload acceptance persistence CLI write
output is not live optional validation, not prepared-machine validation, not
validation success, not validation failure, and not issue closure.

Skipped-missing remains skipped-missing.

## 37. Security/Privacy Review

The future CLI write design is explicit-target, redaction-first,
dry-run-first, acknowledgement-gated, confirmation-gated, no-default-path, and
no-directory-scan.

It must prevent raw path leaks, secret leaks, full file content display,
plugin code display, remote URL fetches, script execution, plugin imports,
solver execution, and unsafe payload truth claims. Malicious payloads remain
blocked data. Writer diagnostics remain redacted.

## 38. Non-Actions

This gate does not implement CLI write behavior, edit CLI source, edit source,
invoke writer, write files, read files, parse files, read input state files,
parse input state files, invoke the reload file reader, invoke the
OSW-EXP-102 state writer, add GUI behavior, use GUI subprocesses, use
subprocesses, accept runtime reload, perform active acceptance mutation,
mutate ProjectSchema, add default target paths, add background writes, scan
directories, fetch network manifests, import plugin packages, create
reloadable bundles, create export files, create report files, add clipboard
behavior, add report attachment, add open-output-folder behavior, add live
discovery, add passive refresh, run validation, run solver execution, install
dependencies, uninstall dependencies, uninstall solvers, automatically
activate candidates, restore trust, mutate issues, mutate releases, mutate
tags, mutate assets, bump versions, claim validation success, claim validation
failure, claim issue closure, claim bundled solvers, or claim certification.

## 39. Future Implementation Test Plan

Future OSW-EXP-134 must test:

- command registration and help text;
- write command remains unavailable unless implemented in that gate;
- supplied persistence view-model records only;
- no input state-file reading or parsing;
- no reload file-reader invocation;
- no OSW-EXP-102 state-writer invocation;
- explicit target requirement;
- no default target path;
- no background write;
- dry-run-first planning;
- fresh dry-run requirement;
- acknowledgement requirement;
- confirmation requirement;
- replacement requirement;
- writer invocation happens only after gates pass;
- blocked preconditions do not invoke writer;
- construction/import/help do not write files;
- no CLI subprocess or GUI subprocess;
- target redaction;
- text and JSON output determinism;
- writer result output;
- acknowledgement output;
- expiry output;
- schema/migration output;
- redaction/privacy output;
- provenance output;
- candidate lifecycle output;
- stale-source/re-preview output;
- conflict/shared-stack output;
- unsafe-claim output;
- evidence/history output;
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_*` diagnostics;
- exit-code policy;
- non-action flags;
- disabled/future actions;
- no runtime reload acceptance;
- no ProjectSchema mutation;
- no discovery, validation, or solver execution;
- no dependency installation or uninstall;
- no activation or trust restoration;
- no issue/release/tag/asset mutation;
- no certification claim.

## 40. Future Gates

Suggested sequence:

- `OSW-EXP-134_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_IMPLEMENTATION`
- `OSW-EXP-135_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECT_SCHEMA_DESIGN`, if ProjectSchema review is ever needed.
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION`, if a prepared machine is available.

Each future gate remains separately scoped and must preserve explicit-target,
dry-run-first, redaction-first, acknowledgement-gated, confirmation-gated,
non-authoritative, non-validation, non-trust-restoring, non-activating,
ProjectSchema-safe, issue/release-safe, and certification-safe boundaries.
