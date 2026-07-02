# Optional Solver Plugin Manifest Reload Acceptance Persistence GUI Review Design

## 1. Status

Design-only.

This gate adds no GUI implementation, no GUI source edits, no source edits, no
writer invocation, no file writes, no file reading, no file parsing, no input
state-file reading, no input state-file parsing, no reload file-reader
invocation, no OSW-EXP-102 state-writer invocation, no CLI behavior, no CLI
subprocess, and no subprocess use.

This gate also adds no runtime reload acceptance, no active acceptance
mutation, no ProjectSchema mutation, no default target path, no background
write, no directory scan, no network fetch, no plugin package import, no
reloadable bundle creation, no export file creation, no report file creation,
no clipboard behavior, no report attachment, no open-output-folder behavior,
no live discovery, no passive refresh, no validation execution, no solver
execution, no dependency installation, no dependency uninstall, no solver
uninstall, no automatic activation, no trust restoration, no issue mutation, no
release mutation, no tag mutation, no asset mutation, no version bump, no
validation-pass claim, no validation-fail claim, no issue-closure claim, no
bundled-solver claim, and no certification claim.

The future GUI review surface remains separately gated. This document is not
implementation authorization and does not approve OSW-EXP-130 work inside this
gate.

## 2. Purpose

This design defines a future GUI review surface over OSW-EXP-125 persistence
view-model records and OSW-EXP-126 writer dry-run/result records.

The design preserves boundaries between reload preview, acceptance review,
persistence review, dry-run planning, actual write, runtime acceptance,
ProjectSchema state, validation, issue/release workflows, and certification.
Persistence GUI review is a display surface only until a separate implementation
gate adds a PySide panel.

## 3. Current State Before Persistence GUI Review

- The reload acceptance persistence design exists.
- The reload acceptance persistence view-model exists.
- The reload acceptance persistence writer exists.
- The reload acceptance persistence CLI review/plan exists.
- The reload acceptance CLI review exists.
- The reload acceptance GUI review exists.
- No persistence GUI review panel exists.
- No GUI invocation of writer exists.
- No GUI persistence write exists.
- No runtime reload acceptance exists.

Issues `#6` through `#11` remain open. Package metadata remains `0.1.5rc1`.
The public prerelease remains `v0.1.5-rc1`.

## 4. Future GUI Surface Definition

The future GUI surface is a PySide review panel over supplied persistence
view-model records and supplied writer dry-run/result records. It may render
persistence readiness, dry-run/write-plan data, writer result data, target
display, acknowledgements, expiry, diagnostics, non-action flags,
disabled/future actions, and safety guidance.

The future panel must not write files on construction, write files on refresh,
write files on preview success, write files on target selection, accept runtime
reload, mutate ProjectSchema, run discovery, run validation, run solver
execution, activate candidates, restore trust, close issues, mutate releases,
or claim certification.

Future GUI review is display-only unless a later gate explicitly authorizes a
different behavior. Even a future write success would mean only local
review-record persistence, not runtime acceptance or validation evidence.

## 5. Future GUI User Flow

Suggested future GUI states:

- `no_persistence_viewmodel`
- `persistence_not_requested`
- `persistence_preview`
- `dry_run_plan_available`
- `dry_run_plan_blocked`
- `target_required`
- `acknowledgement_required`
- `redaction_blocked`
- `stale_source_repreview_required`
- `conflict_review_required`
- `unsafe_claim_blocked`
- `writer_future_only`
- `write_future_disabled`
- `persisted_review_record_display`
- `runtime_acceptance_still_required`
- `persistence_error`

The flow starts with supplied persistence records. It may display supplied
writer dry-run/result rows. It does not choose a target, call a writer, write a
file, accept runtime reload, mutate ProjectSchema, activate candidates, restore
trust, validate solvers, execute solvers, mutate issues, mutate releases, or
certify anything.

## 6. Input Policy

The future GUI consumes supplied persistence view-model records only. It may
consume supplied writer dry-run/result records only. It performs no file reading
in this gate, no input state file reading, no input state-file reading, no file
parsing, no input state file parsing, no input state-file parsing, no reload
file-reader invocation, no writer invocation in this design gate, no CLI calls,
and no subprocess.

The future GUI must display no raw file content, no plugin code, no default
target path, no background write, no directory scan, no network fetch, and no
plugin import. It must treat supplied records as untrusted review data unless a
future gate proves otherwise.

## 7. Target Selection Policy

Future target selection, if separately implemented, must be explicit. It must
not use a default path, must not write on selection, must not create
directories, must not scan directories, must block symlinks unless separately
gated, must block an existing target unless explicit replacement policy is
separately designed, must display only a redacted target label, must never imply
runtime acceptance, and must never imply validation evidence.

Target selection is not dry-run success. Target selection is not persistence
write. Target selection is not ProjectSchema mutation. Target selection is not
trust restoration, activation, issue closure, release mutation, or
certification.

## 8. Layout Model

Future layout sections:

- summary/readiness
- target/storage policy
- dry-run/write-plan
- writer result
- request/result details
- acknowledgements
- expiry
- schema/migration
- redaction/privacy
- provenance
- candidate lifecycle
- stale-source/re-preview
- conflict/shared-stack
- unsafe claims
- evidence/history
- diagnostics
- non-action flags
- disabled/future actions
- safety guidance

Each section is a review section. No section is an acceptance button, save
button, validation command, solver command, issue command, release command, tag
command, asset command, or certification command.

## 9. Summary/Readiness Display

The future summary/readiness display renders persistence state, readiness,
requested or not-requested state, dry-run plan state, writer future-only state,
blocked and ready counts, warning counts, diagnostic counts, target required
state, and explicit false states for runtime acceptance, ProjectSchema,
validation, activation, trust, issue/release, and certification.

Summary success is not validation success. Summary blocked state is not
validation failure. Summary readiness is not runtime acceptance or
ProjectSchema state.

## 10. Target/Storage Display

The future target/storage display renders storage policy id, storage label,
redacted target display, target required state, target blocked state, parent
missing state, directory target blocked state, symlink blocked state, existing
target replacement policy, no default path, no background path, and no
directory creation.

The GUI must not expose raw absolute paths by default. Target display remains
redacted review data.

## 11. Dry-Run/Write-Plan Display

The future dry-run/write-plan display renders `dry_run`, `planned`,
`writer_future_only`, bytes count, SHA-256, payload kind/schema, blockers,
warnings, diagnostics, non-action flags, disabled/future actions, and safety
guidance.

Dry-run is not write. Dry-run success is not validation success. Dry-run
success is not validation failure. Dry-run success is not runtime acceptance.
Dry-run success is not ProjectSchema mutation. Dry-run success is not issue
closure, release mutation, trust restoration, activation, or certification.

## 12. Writer Result Display

The future writer result display renders status, target display,
planned/written state, bytes count, SHA-256, cleanup status, temp-file status,
diagnostics, warnings, and blockers.

If a future gate enables actual writer results, write success is still only a
local review-record persistence event. It is not runtime reload acceptance, not
validation success, not validation failure, not ProjectSchema mutation, not
trust restoration, not automatic activation, not issue closure, not release
mutation, and not certification.

## 13. Acknowledgement Display

The future acknowledgement display renders required, satisfied, missing,
expired, blocking, and advisory state for:

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

Acknowledgements are not validation evidence. Acknowledgements are not
validation failure. Acknowledgements are not trust restoration. Missing or
expired acknowledgements block any future GUI write.

## 14. Expiry Display

The future expiry display renders these expiry reasons:

- reload
- source fingerprint change
- schema version change
- unsafe claim appearance
- trust policy change
- future discovery-refresh result
- file reader policy change
- GUI file-dialog policy change
- CLI explicit-path policy change
- acceptance policy change
- ProjectSchema policy change
- validation issue state change
- persistence schema change
- persistence storage-policy change
- persistence CLI policy change
- persistence GUI policy change
- writer policy change

Expiry requires re-review. Expiry is not validation failure and not issue
closure evidence.

## 15. Schema/Migration Display

The future schema/migration display renders payload kind, schema version, schema
mismatch, unsupported schema, migration required, schema mismatch is not
validation failure, persistence schema remains separate from ProjectSchema, and
the GUI does not repair or migrate files.

Schema/migration review is not ProjectSchema mutation. It does not create schema
files or state files.

## 16. Redaction/Privacy Display

The future redaction/privacy display renders raw paths hidden by default,
basename/hash/source-id/display-name preferred, secrets/tokens/API keys blocked,
unredacted path allowances require future explicit policy, fingerprints are not
trust signals, diagnostics use redacted context, GUI must not display full file
content, and GUI must not display plugin code.

Accepted or persisted review state must never store secrets as truth.

## 17. Provenance Display

The future provenance display renders persistence view-model source, acceptance
state id, preview identifier, payload fingerprint if safe, writer generated_by
metadata, limitations, untrusted-by-default source, and trust label is not
certification.

Provenance is reference-only. It is not validation evidence, trust restoration,
ProjectSchema state, issue closure, release evidence, or certification.

## 18. Candidate Lifecycle Display

The future candidate lifecycle display renders inactive preview remains
review-only, persisted active requires future activation review, deactivated
remains deactivated review state, reactivation routes to future activation
review, discovery-refresh state remains review state, no automatic activation,
no trust restoration, and persisted record does not override built-ins.

Built-ins remain authoritative by default. Persisted review records never select
trusted winners.

## 19. Stale-Source/Re-Preview Display

The future stale-source/re-preview display renders old preview not silently
trusted, missing/moved/changed sources require re-preview, persistence GUI does
not inspect referenced source files, stale-source state is not validation
failure, and re-preview remains future-gated.

The GUI must not read referenced source files to repair stale-source state.

## 20. Conflict/Shared-Stack Display

The future conflict/shared-stack display renders conflicts visible, built-ins
win by default, persisted acceptance record does not override built-ins,
shared-stack warnings visible, GUI does not resolve conflicts, and future policy
required.

Conflict review never installs dependencies, uninstalls dependencies, uninstalls
solvers, activates candidates, restores trust, or validates solvers.

## 21. Unsafe-Claim Display

The future unsafe-claim display renders unsafe claims visible and blocked,
unsafe claims not persisted as truth, validation success/failure claims
blocked, issue closure claims blocked, release mutation claims blocked, bundled
solver claims blocked, dependency installation claims blocked, solver execution
claims blocked, trust restoration claims blocked, and certification claims
blocked.

Unsafe claims remain data to reject or review. The GUI must not repeat them as
truth.

## 22. Evidence/History Display

The future evidence/history display renders deactivation/reactivation history
retained as reference-only, historical evidence retained as reference-only,
skipped-missing remains skipped-missing, persisted record is not validation
evidence, no evidence deletion/rewrite, and no issue closure implied.

Historical evidence is context, not a validation pass, validation fail,
certification, release claim, or issue-closure claim.

## 23. Diagnostics Vocabulary

Future GUI diagnostics reserve `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_*`
codes:

- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_UNAVAILABLE`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_NOT_REQUESTED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_PREVIEW_RENDERED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_PLAN_FUTURE_ONLY`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_FUTURE_ONLY`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_TARGET_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_TARGET_REDACTED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_ACK_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_DRY_RUN_NOT_WRITE`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_NOT_RUNTIME_ACCEPTANCE`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_NO_VALIDATION_CLAIM`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_NO_PROJECT_SCHEMA_MUTATION`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_ERROR`

The design also requires surfacing OSW-EXP-125, OSW-EXP-126, and OSW-EXP-128
diagnostics without rewriting them as truth.

## 24. Non-Action Flags

Future GUI must render false/safety states for:

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

Future `persistence_write_performed` may only mean explicit local review-record
write and never runtime acceptance, validation evidence, validation failure,
ProjectSchema mutation, activation, trust restoration, issue closure, release
mutation, or certification.

## 25. Disabled/Future Actions

Future GUI must render disabled/future actions:

- `choose_target`
- `plan_persistence_record`
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

Disabled/future action rows are not buttons that perform those actions in this
design gate.

## 26. Relationship To OSW-EXP-126 Writer

GUI design may later display writer dry-run/result records. This gate does not
call writer. The writer remains explicit-path, dry-run-first, and
acknowledgement-gated. GUI must not bypass writer path/redaction/safety
policies.

Actual GUI writer invocation, if ever needed, requires a separate gate and
focused tests.

## 27. Relationship To OSW-EXP-128 CLI

The CLI remains stdout-first and dry-run-only. GUI design does not call CLI and
does not use CLI subprocess. GUI and CLI share persistence view-model and writer
contracts. CLI success does not imply GUI persistence or runtime acceptance.

## 28. Relationship To OSW-EXP-125 Persistence View-Model

The persistence view-model remains the source of readiness and persistence
review. GUI does not compute independent acceptance policy. GUI renders
view-model mapping/text and supplied writer plan/result rows.

## 29. Relationship To Reload Acceptance GUI/CLI

Existing acceptance GUI remains review-only. Existing acceptance CLI remains
review-only. Persistence GUI is separate from acceptance review. Acceptance
success does not imply persistence. Persistence success does not imply runtime
acceptance.

## 30. Relationship To Reload File Reader And Explicit-Path Preview

The file reader remains explicit-path and bounded. Persistence GUI does not read
input state files. Persistence GUI does not invoke file reader in this design
gate. Preview success does not imply acceptance. Acceptance success does not
imply persistence.

## 31. Relationship To ProjectSchema

This gate adds no ProjectSchema mutation. A persistence record is not
ProjectSchema state. A persistence record is not project validation evidence.
Future ProjectSchema integration requires a separate gate.

## 32. Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. GUI persistence output is not live
optional validation. Skipped-missing remains skipped-missing. Prepared-machine
validation remains separate.

## 33. Security/Privacy Review

Security and privacy policy:

- no raw path leak
- no secret leak
- no full file content display
- no plugin code display
- no remote URL fetch
- no script execution
- no plugin import
- no solver execution
- malicious payload remains rejected/blocked data
- writer diagnostics remain redacted

The GUI must not display raw absolute paths, home directories, environment
values, tokens, API keys, bearer strings, plugin source code, full JSON payload
content, or executable script content.

## 34. Non-Actions

This gate does not implement GUI behavior, edit GUI source, edit source, invoke
writer, write files, read files, parse files, invoke reload file reader, invoke
OSW-EXP-102 state writer, call CLI, use subprocess, accept runtime reload,
perform active acceptance mutation, mutate ProjectSchema, add default target
path, add background write, scan directories, fetch network manifests, import
plugin packages, create reloadable bundles, create export files, create report
files, add clipboard behavior, add report attachment, add open-output-folder
behavior, add live discovery, add passive refresh, run validation, run solver
execution, install dependencies, uninstall dependencies, uninstall solvers,
automatically activate candidates, restore trust, mutate issues, mutate
releases, mutate tags, mutate assets, bump version, claim validation-pass,
claim validation-fail, claim issue closure, claim bundled solver, or claim
certification.

## 35. Future Implementation Test Plan

Future OSW-EXP-130 must test:

- panel imports
- panel consumes supplied persistence view-model records
- panel consumes supplied writer dry-run/result records
- construction does not write files
- refresh does not write files
- target selection does not write files
- no writer invocation unless explicitly scoped
- no file reading/parsing
- no file-reader invocation
- no CLI/subprocess
- target redaction
- diagnostics rendering
- acknowledgements rendering
- expiry rendering
- dry-run/write-plan rendering
- writer result rendering
- non-action flags rendering
- disabled/future action rendering
- no ProjectSchema mutation
- no discovery/validation/solver execution
- no issue/release/tag/asset mutation
- no certification claim

The future implementation test plan must also include source guardrails against
writer invocation, CLI calls, file reader calls, subprocess use, ProjectSchema
mutation, discovery, validation, solver execution, issue/release/tag/asset
mutation, and certification claims unless a later prompt explicitly scopes such
behavior.

## 36. Future Gates

Suggested future gates:

- `OSW-EXP-130_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_REVIEW_IMPLEMENTATION`
- `OSW-EXP-131_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_DESIGN`, if write UI is ever needed
- `OSW-EXP-132_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_DESIGN`, if actual CLI writes are ever needed
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION`, if a prepared machine is available

If later repository docs reserve different numbering, the next gate should map
this design contract to the latest repo convention and explain the mapping.

## 37. Implementation Follow-Up: OSW-EXP-130

OSW-EXP-130 implements this design as a display-only PySide review panel
([optional_solver_plugin_manifest_reload_acceptance_persistence_gui_review_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_gui_review_implementation.md)).
The implementation consumes supplied persistence view-model records and supplied
writer dry-run/result records only. It does not invoke the writer, write files,
read or parse input state files, invoke the reload file reader, call CLI code,
use subprocesses, accept runtime reload, mutate ProjectSchema, run discovery,
run validation, execute solvers, activate candidates, restore trust, mutate
issues/releases/tags/assets, or claim certification.
