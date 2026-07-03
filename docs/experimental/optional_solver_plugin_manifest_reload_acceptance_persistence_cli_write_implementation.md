# Optional Solver Plugin Manifest Reload Acceptance Persistence CLI Write Implementation

## 1. Status

Experimental reload acceptance persistence CLI write implemented.

This gate adds the `write` subcommand to
`optional-solver-plugin-manifest-reload-acceptance-persistence`.

The implementation is explicit-target, dry-run-first,
acknowledgement-gated, confirmation-gated, redaction-first, and
non-authoritative. It writes only local reload acceptance persistence review
records through the OSW-EXP-126 writer API when all gates pass.

This gate does not implement runtime reload acceptance, active acceptance
mutation, ProjectSchema mutation, default target paths, background writes,
directory scan, network fetch, plugin package import, input state-file reading
or parsing, reload file-reader invocation, OSW-EXP-102 state-writer invocation,
GUI behavior, GUI subprocess use, subprocess use, reloadable bundle creation,
export file creation, report file creation, clipboard behavior, report
attachment, open-output-folder behavior, live discovery, passive refresh,
validation execution, solver execution, dependency installation, dependency
uninstall, solver uninstall, automatic activation, trust restoration, issue
mutation, release mutation, tag mutation, asset mutation, version bump,
validation-pass claim, validation-fail claim, issue-closure claim,
bundled-solver claim, or certification claim.

## 2. Purpose

The OSW-EXP-133 design defined a future CLI write workflow for reload
acceptance persistence records. OSW-EXP-134 implements that narrow workflow:
write an explicit local review record only after the CLI builds a fresh dry-run
writer result, the caller supplies an explicit target, the caller acknowledges
the persistence write boundary, and the caller confirms the write.

The written record is not runtime reload acceptance. It is not validation
success. It is not validation failure. It is not ProjectSchema state. It is not
trust restoration. It is not automatic activation. It is not discovery success.
It is not dependency installation. It is not solver execution. It is not issue
closure. It is not release mutation. It is not certification.

## 3. Implemented Command

Command family:

```text
optional-solver-plugin-manifest-reload-acceptance-persistence
```

Implemented subcommand:

```text
write
```

The command remains stdout-first for successful JSON/text results and returns
structured stderr output for blocked or failed write attempts. Existing
`explain`, `preview`, `plan`, `diagnostics`, `acknowledgements`, `expiry`,
`storage`, `actions`, `safety`, and `write-future` review commands remain
available. `write-future` remains a disabled compatibility review path.

## 4. Required Write Gates

The `write` subcommand requires:

- `--target <path>`: an explicit caller-supplied local output path;
- `--acknowledge-persistence-write`: caller acknowledgement that the record is
  local review persistence only;
- `--confirm-persistence-write`: explicit write confirmation after dry-run
  planning;
- a fresh writer dry run using `dry_run=True`;
- a non-blocked dry-run result before any actual writer call;
- `--allow-replace` when replacing an existing target is intended.

Missing target, acknowledgement, or confirmation exits before writer
invocation and writes no file. A blocked dry-run exits before `dry_run=False`
is called and writes no file.

## 5. Writer Invocation Policy

The CLI uses only the OSW-EXP-126 reload acceptance persistence writer API.

Write sequence:

1. Build `ReloadAcceptancePersistenceWriteRequest` with `dry_run=True`.
2. Call `write_reload_acceptance_persistence_record` for the dry-run result.
3. Stop if the dry-run result is not `planned`.
4. Build a second `ReloadAcceptancePersistenceWriteRequest` with
   `dry_run=False`.
5. Call `write_reload_acceptance_persistence_record` for the actual local
   review-record write.

The CLI does not bypass writer path checks, redaction checks, schema checks,
acknowledgement checks, existing-target checks, symlink checks, parent checks,
or secret/unredacted-path checks.

## 6. Target Policy

The target path is explicit and caller supplied. There is no default target
path and no background target path. The CLI does not create directories, scan
directories, fetch network manifests, import plugin packages, or infer target
paths from source files.

Text and JSON output use the writer redacted target display. Raw absolute
paths, home directories, environment-derived paths, secrets, tokens, API keys,
credentials, and secret-like values remain blocked or redacted.

Existing targets are blocked unless `--allow-replace` is supplied. Symlink
targets, directory targets, and missing parents remain writer-policy governed.

## 7. State Source Policy

The CLI consumes deterministic in-memory persistence view-model records only.
It does not read files, parse files, read input state files, parse input state
files, invoke the reload file reader, invoke the OSW-EXP-102 state writer, call
GUI code, use CLI subprocesses, or use subprocesses.

This implementation does not add state-file load options and does not add
`--path` as an input option.

## 8. Output Model

Text and JSON output include:

- command and subcommand identity;
- state source;
- target policy;
- dry-run result;
- writer result;
- status;
- target display;
- bytes count;
- SHA-256;
- payload kind and schema version;
- diagnostics;
- warnings;
- blockers;
- cleanup and temp-file status;
- non-action flags;
- disabled/future actions;
- safety guidance;
- exit-code policy.

Successful write output states that the result is local review-record
persistence only and not runtime acceptance, validation success, validation
failure, ProjectSchema mutation, trust restoration, automatic activation,
issue closure, release mutation, or certification.

## 9. Exit-Code Policy

Exit codes are command outcome only:

- `0`: command completed; for `write`, the writer reported a completed local
  review-record write;
- `1`: writer error;
- `2`: CLI gate blocked, dry-run blocked, or `write-future` disabled.

Exit code `0` is not validation success, not validation failure, not runtime
acceptance, not ProjectSchema mutation, not issue closure, not release
mutation, and not certification. For `write`, exit code `0` does not imply any
write beyond the reported local review-record writer result.

## 10. Diagnostics

OSW-EXP-134 adds or uses the following CLI write diagnostics:

- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_TARGET_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_ACK_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_CONFIRM_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_DRY_RUN_NOT_WRITE`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_COMPLETED_LOCAL_ONLY`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_ERROR`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_NO_VALIDATION_CLAIM`

The CLI surfaces OSW-EXP-125 persistence view-model diagnostics and OSW-EXP-126
writer diagnostics without rewriting them as validation truth.

## 11. Non-Action Flags

The write result may set `persistence_write_performed`,
`actual_cli_write_performed`, and `writer_called_with_dry_run_false` to `true`
only when the OSW-EXP-126 writer reports a completed explicit local
review-record write.

All other safety flags remain false:

- `runtime_reload_acceptance_performed`
- `active_acceptance_mutation_performed`
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

## 12. Disabled And Future Actions

The write subcommand enables only explicit local review-record persistence
through the writer gate. The following remain disabled or future-only:

- runtime reload acceptance;
- active acceptance mutation;
- accepting as trusted;
- activating reloaded candidates;
- discovery refresh;
- validation;
- solver execution;
- dependency installation;
- dependency uninstall;
- solver uninstall;
- ProjectSchema mutation;
- reloadable bundle creation;
- export file creation;
- report file creation;
- clipboard behavior;
- report attachment;
- open-output-folder behavior;
- issue closure;
- release mutation;
- tag push;
- asset upload;
- validation success claim;
- validation failure claim;
- certification claim.

## 13. Relationship To OSW-EXP-126 Writer

The CLI delegates local review-record persistence to the OSW-EXP-126 writer.
The writer remains the authority for deterministic serialization, target
checks, replacement policy, path redaction, acknowledgement enforcement,
schema checks, blocker diagnostics, temp-file cleanup, and atomic replace
reporting.

The CLI does not implement an independent persistence writer and does not
invoke the older OSW-EXP-102 state writer.

## 14. Relationship To OSW-EXP-128 CLI Review

The OSW-EXP-128 CLI review and dry-run planning commands remain stdout-first
and non-writing. OSW-EXP-134 adds only the separate `write` subcommand. Review
commands still write no files and do not call the writer with `dry_run=False`.

The legacy `write-future` command remains disabled/future-only for compatibility
and returns a blocked status.

## 15. Relationship To OSW-EXP-133 Design

This implementation follows the OSW-EXP-133 CLI write design: explicit target,
dry-run-first planning, caller acknowledgement, confirmation, replacement
review, writer-policy enforcement, redacted output, no default path, no
background write, no reader invocation, no GUI subprocess, no ProjectSchema
mutation, no validation, no solver execution, no activation, no trust
restoration, no issue/release mutation, and no certification claim.

## 16. Relationship To GUI Persistence Write

The CLI does not call GUI code and does not use GUI subprocesses. The
OSW-EXP-132 GUI write panel remains a separate implementation path that uses
the same writer contract directly rather than shelling out to the CLI.

CLI write success does not imply GUI write success, runtime reload acceptance,
ProjectSchema mutation, validation evidence, issue closure, release mutation,
or certification.

## 17. Relationship To ProjectSchema

The persistence record is not ProjectSchema state. The CLI does not mutate
ProjectSchema, does not import ProjectSchema write paths, and does not treat
the persisted review record as project validation evidence.

Any future ProjectSchema integration requires a separate design and
implementation gate.

## 18. Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. CLI persistence write output is not live
optional validation. Skipped-missing remains skipped-missing. Prepared-machine
validation remains separate.

## 19. Security And Privacy

The implementation avoids raw path leakage in normal output, blocks
secret-like display values through the existing redaction helper, and delegates
payload secret/path policy to the writer. The CLI does not show full file
content, plugin code, remote URL fetch results, script output, solver output,
environment secrets, tokens, API keys, or credentials.

Malicious or unsafe payload state remains rejected or blocked data. Writer
diagnostics remain redacted and are not truth claims.

## 20. Tests

Focused OSW-EXP-134 tests cover:

- command registration;
- required explicit target;
- acknowledgement gate;
- confirmation gate;
- dry-run-first ordering;
- successful explicit local review-record write under `tmp_path`;
- JSON and text safety output;
- no raw target path leakage;
- existing target blocked unless `--allow-replace`;
- blocked view-model stops after dry run and writes no file;
- writer error return code;
- review commands and `write-future` still write no file;
- no `--path` input option;
- source guardrails against file reading/parsing, reload reader invocation,
  OSW-EXP-102 state-writer invocation, GUI imports, subprocess use,
  ProjectSchema mutation, discovery, validation, and solver execution.

## 21. Non-Actions

This gate does not add runtime reload acceptance, active acceptance mutation,
ProjectSchema mutation, default target path, background write, directory scan,
network fetch, plugin package import, input state-file reading, input
state-file parsing, reload file-reader invocation, OSW-EXP-102 state-writer
invocation, GUI behavior, GUI subprocess use, subprocess use, reloadable
bundle creation, export file creation, report file creation, clipboard
behavior, report attachment, open-output-folder behavior, live discovery,
passive refresh, validation execution, solver execution, dependency
installation, dependency uninstall, solver uninstall, automatic activation,
trust restoration, issue mutation, release mutation, tag mutation, asset
mutation, version bump, validation-pass claim, validation-fail claim,
issue-closure claim, bundled-solver claim, or certification claim.

## 22. Future Gates

Suggested next gate:

- `OSW-EXP-135_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECT_SCHEMA_DESIGN`, if ProjectSchema review is ever needed.

Prepared-machine validation remains separate:

- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION`, if a prepared
  machine is available.

## 23. Summary Audit Follow-Up (OSW-EXP-136)

OSW-EXP-136 adds a separate supplied-record summary audit
([optional_solver_plugin_manifest_reload_acceptance_persistence_summary_audit_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_summary_audit_implementation.md)).
The audit can summarize this CLI write result as local review-record evidence
only. It does not invoke this CLI, call the writer, read or parse input state
files, invoke the reload file reader or OSW-EXP-102 state writer, accept
runtime reload, mutate ProjectSchema, run discovery/validation/solver
execution, activate candidates, restore trust, mutate issues/releases/tags or
assets, or claim certification.

## 24. ProjectSchema Boundary Follow-Up (OSW-EXP-137)

OSW-EXP-137 defines the separate ProjectSchema boundary design
([optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary_design.md](optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary_design.md)).
CLI write success remains local review-record persistence only. It is not
ProjectSchema state, ProjectSchema validation evidence, ProjectSchema
validation failure, ProjectSchema trust state, ProjectSchema activation state,
issue closure, release mutation, bundled-solver support, or certification.

## 25. ProjectSchema Boundary Implementation Follow-Up (OSW-EXP-138)

OSW-EXP-138 implements the separate supplied-record ProjectSchema boundary
([optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary_implementation.md)).
The boundary may summarize CLI write mappings only when supplied by a caller.
It does not invoke this CLI, read or parse input state files, call the writer,
mutate ProjectSchema, create ProjectSchema validation evidence, accept runtime
reload, run discovery/validation/solver execution, restore trust, activate
candidates, mutate issues/releases/tags/assets, or claim certification.

## 26. Prepared-Machine Prerequisites Follow-Up

`OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` was later
parked because no safe runnable prepared-machine manifest-state validation
command was found and the local optional solver/package prerequisites were
missing. The parked prerequisites are documented in
[Optional solver prepared-machine manifest-state validation prerequisites](optional_solver_prepared_machine_manifest_state_validation_prerequisites.md).

CLI write success remains explicit local review-record persistence only. It is
not prepared-machine validation, not validation success, not validation
failure, not ProjectSchema mutation, not issue closure, not release mutation,
not bundled-solver support, and not certification.
