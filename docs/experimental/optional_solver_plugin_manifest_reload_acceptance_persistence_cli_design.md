# Optional Solver Plugin Manifest Reload Acceptance Persistence CLI Design

## 1. Status

This is a design-only gate for a future reload acceptance persistence CLI. It
adds no CLI implementation, no CLI source edits, no source edits, no writer
invocation, no file writes, no file reading, no file parsing, no input state
file reading, no input state file parsing, no reload file-reader invocation, no
OSW-EXP-102 state-writer invocation, no GUI behavior, no GUI subprocess, no
runtime reload acceptance, no active acceptance mutation, no ProjectSchema
mutation, no default reload path, no background write, no directory scan, no
network fetch, no plugin package import, no reloadable bundle creation, no
export file creation, no report file creation, no clipboard behavior, no
report attachment, no open-output-folder behavior, no live discovery, no
passive refresh, no validation execution, no solver execution, no dependency
installation, no dependency uninstall, no solver uninstall, no automatic
activation, no trust restoration, no issue mutation, no release mutation, no
tag mutation, no asset mutation, no version bump, no validation-pass claim, no
validation-fail claim, no issue-closure claim, no bundled-solver claim, and no
certification claim.

The future implementation remains separately gated. This document only defines
the review/write-plan contract for that future work.

## 2. Purpose

OSW-EXP-125 added a pure reload acceptance persistence view-model. OSW-EXP-126
added an explicit-path, dry-run-first writer API for local review records. A
future CLI may make that persistence path inspectable from terminals and CI
logs, but the CLI must not make persistence look like runtime reload
acceptance, validation evidence, ProjectSchema state, issue closure, release
mutation, or certification.

The future CLI exists to render what would be persisted, why a write is ready
or blocked, and what safety boundaries remain in force.

## 3. Current State Before This CLI

- `OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel` is the
  in-memory source for persistence readiness and write-plan review data.
- The OSW-EXP-126 writer accepts an already-built persistence view-model and an
  explicit target path. It can plan deterministic JSON in dry-run mode and
  write only when a caller supplies explicit acknowledgement.
- The existing reload acceptance CLI remains a stdout-first acceptance review
  surface. It does not write persistence records.
- The existing reload acceptance GUI panel remains view-model-only and
  non-writing.

This design gate does not invoke any of those runtime APIs.

## 4. Future Command Vocabulary

The future command family should be:

`python -m osw.cli optional-solver-plugin-manifest-reload-acceptance-persistence <subcommand>`

Recommended future subcommands:

- `explain`
- `preview`
- `plan`
- `summary`
- `acknowledgements`
- `expiry`
- `diagnostics`
- `storage`
- `actions`
- `safety`
- `write-future`

`write-future` is the only command name that hints at an eventual actual write.
It must remain disabled/future-only until the future implementation gate wires
the writer intentionally. In this design gate there is no command parser, no
CLI implementation, and no path input.

## 5. State Source Policy

Future CLI review must consume deterministic in-memory persistence
view-model records. The intended state sources are:

- an unavailable/no-record sample;
- a not-requested sample;
- a blocked sample;
- a ready/future-writer-only sample;
- a persisted-review-record/future-only sample;
- a caller-supplied in-memory
  `OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel` when the
  CLI implementation later exposes a safe integration seam.

The CLI must not read input state files, parse input state files, invoke the
reload file reader, or invoke the OSW-EXP-102 state writer. It must not accept a
reload-state input path as a shortcut around the view-model boundary.

## 6. Explicit Target Path Policy

A future actual write requires an explicit target path and caller
acknowledgement. There is no default write path, no hidden persistence, no
background write, and no directory scan. The future implementation may define a
target option for dry-run planning and acknowledged writes, but this design gate
adds no CLI option and no path behavior.

Future target display must be redacted by default. Raw absolute paths, home
directories, environment variable expansions, secrets, tokens, and API keys
must not be echoed as truth. A basename, display name, source id, or hash is the
preferred display form.

## 7. Output Modes

The future CLI should be stdout-first. It should provide stable text output for
humans and deterministic JSON output for tests, automation review, and support
logs. JSON output must use sorted/stable keys and avoid environment-dependent
values.

No output mode may create export files, report files, reloadable bundles,
clipboard entries, report attachments, or open-output-folder behavior.

## 8. Dry-Run/Write-Plan Output

The future CLI must render a dry-run write plan before any acknowledged write
is available. The plan should show:

- requested action;
- dry-run state;
- target display and whether it was redacted;
- payload kind;
- schema version;
- byte count and hash only when derived from safe deterministic JSON;
- path policy;
- storage policy;
- blockers;
- warnings;
- diagnostics;
- non-action flags;
- disabled/future actions;
- safety guidance.

Dry-run output is not validation success, validation failure, runtime reload
acceptance, ProjectSchema mutation, trust restoration, activation, discovery
success, issue closure, release mutation, or certification.

## 9. Actual Write Future Gate

Actual write behavior remains future-gated. A future implementation may call
the OSW-EXP-126 writer only after it has explicit command coverage, target path
policy, caller acknowledgement text, overwrite handling, diagnostics tests, and
no-side-effect tests.

Even then, an actual write is a local non-authoritative review record only. It
does not create runtime accepted state, does not make a plugin trusted, does
not activate a candidate, does not mutate ProjectSchema, does not validate a
solver, and does not close issues or mutate releases.

## 10. Request/Result Rendering

Future text and JSON output must render:

- request mode;
- dry-run versus future write;
- caller acknowledgement status;
- target required/selected/missing state;
- allow-replace status;
- target-exists status;
- redacted target display;
- result status;
- planned/written booleans;
- payload kind and schema version;
- deterministic hash when available;
- blockers, warnings, and diagnostics;
- explicit safety guidance.

Command success means the CLI rendered the request/result review. It is not
permission to treat blocked output as a pass.

## 11. Acknowledgement Rendering

The future CLI must render persistence and acceptance acknowledgements with
required/satisfied/missing/expired/blocking state. It must include:

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

Acknowledgements are review gates. They are not validation evidence, not
validation failure, and not trust restoration.

## 12. Acknowledgement Expiry Rendering

The future CLI must render acknowledgement expiry reasons:

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
- persistence storage-policy change.

Expired acknowledgements block persistence planning until a future review flow
renews them.

## 13. Schema/Migration Rendering

Future output must show payload kind, schema id, schema version, writer schema
version, and migration state. Unsupported schema and migration-required states
block persistence. Schema mismatch is not validation failure and not a reason
to repair or migrate files from the CLI.

The persistence schema remains separate from ProjectSchema. CLI review must
never present persistence schema data as project state.

## 14. Redaction/Privacy Rendering

Future output must state that raw paths are hidden by default. It must prefer
basename, source-id, display-name, or hash display. Home directories,
environment variables, secrets, tokens, API keys, bearer strings, and
password-like values must be blocked or redacted.

Fingerprints are not trust signals. Diagnostics must use redacted context.
Accepted state and persisted review records must never store secrets as truth.

## 15. Provenance Rendering

Future output should render safe provenance supplied by the persistence
view-model and writer result:

- redacted source display;
- source fingerprint when already safe;
- payload hash when already safe;
- reader or acceptance preview provenance carried in redacted form;
- limitations and policy notes;
- evidence/history reference labels.

It must not display full file content, raw absolute paths, secrets, tokens, or
API keys.

## 16. Candidate Lifecycle Rendering

Future output must keep candidate lifecycle language review-only:

- inactive preview remains review-only;
- persisted active state still needs future activation review;
- deactivated remains deactivated review state;
- reactivation routes to a future activation review;
- discovery-refresh state remains review state;
- no automatic activation;
- no trust restoration;
- persisted review state does not override built-ins.

## 17. Stale-Source/Re-Preview Rendering

Future output must show stale-source and re-preview states clearly:

- old previews are not silently trusted;
- missing, moved, or changed sources require re-preview;
- CLI persistence review does not inspect referenced source files;
- stale-source state is not validation failure;
- re-preview remains future-gated;
- a future discovery-refresh result may expire acknowledgements.

## 18. Conflict/Shared-Stack Rendering

Conflicts and shared-stack warnings must be visible. Built-ins win by default.
Persisted review state does not override built-ins. The CLI must not resolve
conflicts, install stacks, uninstall stacks, mutate dependencies, or select
trusted winners.

## 19. Unsafe-Claim Rendering

Unsafe claims must be visible and blocked without being rendered as truth. This
includes validation success claims, validation failure claims, issue closure
claims, release mutation claims, bundled solver claims, dependency installation
claims, solver execution claims, trust restoration claims, and certification
claims.

## 20. Evidence/History Rendering

Deactivation/reactivation history and historical evidence remain reference-only
data. Skipped-missing remains skipped-missing. Persisted review state is not
validation evidence, not validation failure, and not issue closure evidence.
The CLI must not delete, rewrite, or elevate evidence/history rows.

## 21. Diagnostics Vocabulary

Future CLI diagnostics should reserve `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_*`
codes for command-level behavior such as unavailable view-models, missing
target, dry-run-only mode, future-write disabled state, acknowledgement
requirements, redaction blockers, target policy blockers, writer result
rendering, and safety guidance.

It should also render supplied `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_*` view-model
and writer diagnostics without treating them as validation results.

## 22. Exit-Code Policy

Review commands should return exit code `0` when rendering completes, including
blocked or unavailable review states. Exit code `0` is command completion only.
It is not validation success, not validation failure, not runtime acceptance,
not persistence success, not ProjectSchema mutation, not issue closure, not
release mutation, and not certification.

`write-future` should remain disabled/future-only until the future
implementation gate and return deterministic nonzero status, preferably `2`,
with safety text.

## 23. Non-Action Flags

Future text and JSON output must include false/non-action rows for:

- `runtime_reload_acceptance_performed`
- `active_acceptance_mutation_performed`
- `persistence_write_performed`
- `project_schema_mutated`
- `default_reload_path_used`
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

Only an acknowledged future implementation may ever show a local
`persistence_write_performed` true result, and that still must not imply any
other action.

## 24. Disabled/Future Actions

Future output must render disabled/future actions:

- `request_persistence`
- `plan_persistence_write`
- `write_acceptance_review_record`
- `persist_acceptance_record`
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

These are visibility rows, not implemented commands.

## 25. Relationship To OSW-EXP-126 Writer

The OSW-EXP-126 writer is the future local API boundary for explicit-path,
dry-run-first, acknowledgement-gated write behavior. The future CLI may render
writer plans and results, but this design gate invokes no writer and edits no
writer source.

## 26. Relationship To OSW-EXP-125 Persistence View-Model

The OSW-EXP-125 persistence view-model remains the source of persistence
readiness, blockers, acknowledgements, expiry, storage policy, non-action
flags, disabled/future actions, provenance, evidence/history, and safety
guidance. The future CLI must not duplicate independent acceptance policy.

## 27. Relationship To Reload Acceptance CLI/GUI

The OSW-EXP-123 reload acceptance CLI and OSW-EXP-121 GUI panel remain sibling
review surfaces over acceptance view-model records. The persistence CLI must not
call GUI code, use GUI subprocesses, or turn acceptance review into persistence
without an explicit future persistence command.

## 28. Relationship To Reload File Reader And Explicit-Path Preview

The OSW-EXP-113 reload file reader and OSW-EXP-115 CLI explicit-path preview
remain preview paths for persisted state-writer payloads. The persistence CLI
must not read input state files, parse input state files, invoke the reload
file reader, or use explicit reload preview paths as persistence input.

## 29. Relationship To State Writer/Persistence

The OSW-EXP-102 state writer remains a reference for explicit local writes but
is not invoked by this design. Reload acceptance persistence records are
separate from generic optional solver plugin manifest state-writer payloads.

## 30. Relationship To ProjectSchema

Persistence CLI output is not ProjectSchema state. The future CLI must import
no ProjectSchema mutation path and must not describe persistence readiness,
write planning, or write completion as project mutation.

## 31. Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. Persistence CLI review, write planning,
or a future acknowledged local write is not prepared-machine validation, not
validation success, not validation failure, and not issue closure.

## 32. Security/Privacy Review

The future CLI must be redaction-first, explicit-target-path-only, dry-run
first, acknowledgement-gated for actual writes, no-default-path, and
no-directory-scan. It must avoid leaking secrets, tokens, API keys, home
directories, raw absolute paths, environment expansions, and full file content.

## 33. Non-Actions

This gate performs no CLI implementation, no CLI source edits, no source edits,
no writer invocation, no file writes, no file reading, no file parsing, no
input state file reading, no input state file parsing, no reload file-reader
invocation, no OSW-EXP-102 state-writer invocation, no GUI behavior, no GUI
subprocess, no runtime reload acceptance, no active acceptance mutation, no
ProjectSchema mutation, no default reload path, no background write, no
directory scan, no network fetch, no plugin package import, no reloadable
bundle creation, no export file creation, no report file creation, no clipboard
behavior, no report attachment, no open-output-folder behavior, no live
discovery, no passive refresh, no validation execution, no solver execution,
no dependency installation, no dependency uninstall, no solver uninstall, no
automatic activation, no trust restoration, no issue mutation, no release
mutation, no tag mutation, no asset mutation, no version bump, no
validation-pass claim, no validation-fail claim, no issue-closure claim, no
bundled-solver claim, or no certification claim.

## 34. Future Implementation Test Plan

A future implementation gate should test:

- command registration;
- no-default state;
- deterministic in-memory state sources;
- dry-run planning output;
- explicit target path requirement;
- acknowledged write remains future-only until wired;
- writer invocation is covered only in the future implementation;
- no input file reading or parsing;
- no reload file-reader invocation;
- no OSW-EXP-102 state-writer invocation;
- text and JSON output determinism;
- request/result rendering;
- acknowledgement and expiry rendering;
- schema/migration rendering;
- redaction/privacy rendering;
- provenance, lifecycle, stale-source, conflict, unsafe-claim, and
  evidence/history rendering;
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_*` diagnostics;
- exit-code semantics;
- non-action flags;
- disabled/future actions;
- no source overreach into GUI, file reader, reload view-model, reload
  acceptance view-model, ProjectSchema, discovery, validation, solver,
  release, issue, tag, or asset code.

## 35. Future Gates

Future gates may implement the reload acceptance persistence CLI, persistence
GUI review, ProjectSchema-safe integration review, prepared-machine validation
evidence review, and issue/release-safe reporting. Each remains separately
gated and must preserve explicit-path, dry-run-first, redaction-first,
acknowledgement-gated, non-authoritative, non-validation,
non-trust-restoration, non-activation, ProjectSchema-safe, issue/release-safe,
and certification-safe boundaries.

## 36. Implementation Follow-Up (OSW-EXP-128)

OSW-EXP-128 implements this CLI design in
[optional_solver_plugin_manifest_reload_acceptance_persistence_cli_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_cli_implementation.md).
The implementation remains stdout-first, explicit-target, and dry-run-only: it
renders deterministic in-memory persistence view-model records and calls the
OSW-EXP-126 writer only through dry-run planning. `write-future` is disabled,
returns a deterministic nonzero status, and performs no file write. The
implementation adds no input state-file reading/parsing, no reload file-reader
invocation, no OSW-EXP-102 state-writer invocation, no GUI behavior, no
subprocess use, no runtime reload acceptance, no ProjectSchema mutation, no
discovery/validation/solver execution, no issue/release/tag/asset mutation, and
no certification claim.
