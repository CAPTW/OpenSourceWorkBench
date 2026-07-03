# Optional Solver Plugin Manifest Reload Acceptance Persistence GUI Write Design

## 1. Status

Design-only.

This gate adds no GUI write implementation, no GUI source edits, no source
edits, no writer invocation, no file writes, no file reading, no file parsing,
no input state file reading, no input state-file reading, no input state file
parsing, no input state-file parsing, no reload file-reader invocation, no
OSW-EXP-102 state-writer invocation, no CLI behavior, no CLI subprocess, and no
subprocess use.

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

The future GUI write workflow remains separately gated. This document is not
implementation authorization and does not approve OSW-EXP-132 implementation
work inside this gate.

## 2. Purpose

This design defines a future GUI write workflow over the OSW-EXP-130
display-only panel and OSW-EXP-126 explicit-path dry-run-first writer.

The design preserves boundaries between reload preview, acceptance review,
persistence review, dry-run planning, target selection, actual local review
record write, runtime acceptance, ProjectSchema state, validation,
issue/release workflows, and certification. A future GUI write action, if ever
implemented, may write only a local non-authoritative review record through the
writer contract; it must never imply runtime acceptance or validation evidence.

## 3. Current State Before GUI Write

- The reload acceptance persistence design exists.
- The reload acceptance persistence view-model exists.
- The explicit-path dry-run-first persistence writer exists.
- The dry-run-only persistence CLI review/plan surface exists.
- The display-only persistence GUI review panel exists.
- The reload acceptance GUI and CLI review surfaces exist.
- No GUI write workflow exists.
- No GUI target chooser for persistence writes exists.
- No GUI writer invocation exists.
- No GUI persistence write exists.
- No runtime reload acceptance exists.

Issues `#6` through `#11` remain open. Package metadata remains `0.1.5rc1`.
The public prerelease remains `v0.1.5-rc1`.

## 4. Future GUI Write Workflow Definition

The future GUI write workflow is an explicit user-driven path layered on top of
the OSW-EXP-130 display-only review panel. It starts from a supplied
OSW-EXP-125 persistence view-model, requests an explicit target path through a
future target chooser, requests a writer dry-run plan through the OSW-EXP-126
writer API, displays the dry-run result, requires user acknowledgement and
confirmation, and then, only in a separately authorized implementation gate,
may call the writer for an actual local review-record write.

The workflow must not write on panel construction, write on refresh, write on
target selection, write on dry-run display, write on acknowledgement display,
or write without a final explicit confirmation. It must not accept runtime
reload, mutate ProjectSchema, run discovery, run validation, run solver
execution, activate candidates, restore trust, close issues, mutate releases,
push tags, upload assets, or claim certification.

## 5. Future GUI User Flow

Suggested future states:

- `no_persistence_viewmodel`
- `persistence_not_requested`
- `target_not_selected`
- `target_selected_redacted`
- `target_policy_blocked`
- `dry_run_required`
- `dry_run_plan_requested`
- `dry_run_plan_available`
- `dry_run_plan_blocked`
- `acknowledgement_required`
- `confirmation_required`
- `write_ready_future_only`
- `write_in_progress_future_only`
- `write_completed_local_review_record`
- `write_blocked`
- `write_error`
- `runtime_acceptance_still_required`

The future user flow separates review, target selection, dry-run planning,
acknowledgement, confirmation, local review-record write, and runtime
acceptance. The GUI must keep each state visible and must not silently advance
from review into persistence, runtime acceptance, validation, activation,
ProjectSchema mutation, issue mutation, release mutation, or certification.

## 6. Target Chooser Policy

Future target chooser behavior, if separately implemented, must be explicit.
It must use no default target path, must not preselect hidden storage, must not
write on selection, must not create directories, must not scan directories,
must not fetch network manifests, must not import plugin packages, must block
symlink targets unless separately gated, must block directory targets, must
block missing parents, must block an existing target unless an explicit replace
policy is separately designed, and must display only a redacted target label.

Target selection is not a dry-run plan. Target selection is not a write. Target
selection is not runtime reload acceptance, not validation evidence, not
validation failure, not ProjectSchema mutation, not trust restoration, not
activation, not issue closure, not release mutation, and not certification.

## 7. Dry-Run Policy

A future GUI write workflow must require a successful writer dry-run plan before
any actual writer call. The dry-run plan must use the OSW-EXP-126 writer API and
must be displayed before confirmation. Dry-run planning must be explicit and
must use the selected explicit target path, caller-supplied persistence
view-model, redaction policy, schema expectations, acknowledgement state, and
replacement policy.

Dry-run is not write. Dry-run success is not validation success. Dry-run
success is not validation failure. Dry-run success is not runtime acceptance.
Dry-run success is not ProjectSchema mutation. Dry-run success is not issue
closure, release mutation, trust restoration, activation, bundled-solver
support, or certification.

## 8. Write Preconditions

Future GUI write preconditions:

- supplied persistence view-model is present
- explicit persistence request is visible
- explicit target path is selected
- target policy accepts the selected path
- writer dry-run plan completed successfully
- dry-run payload kind and schema version match expectations
- required acknowledgements are satisfied
- required acknowledgements are not expired
- stale-source and source-fingerprint blockers are absent
- conflict/shared-stack blockers are absent
- unsupported schema and migration blockers are absent
- unsafe validation/issue/release/install/solver/trust/certification claims are
  absent
- raw path and secret-like value blockers are absent
- user confirmation is explicit and current

Missing or expired preconditions block the future write. Blocked write state is
not validation failure and is not issue closure evidence.

## 9. Write Confirmation Policy

Future write confirmation must be separate from target selection and dry-run
planning. The confirmation dialog or panel must summarize the redacted target,
payload kind, schema version, byte count, SHA-256, acknowledgement state,
replacement policy, and safety boundaries.

Confirmation must state that a future write, if enabled, writes only a local
non-authoritative review record. It is not runtime reload acceptance, not
validation evidence, not validation failure, not ProjectSchema mutation, not
trust restoration, not automatic activation, not discovery success, not
dependency installation, not solver execution, not issue closure, not release
mutation, and not certification.

## 10. Writer Invocation Boundary

This design gate performs no writer invocation. A future implementation gate
may invoke only the OSW-EXP-126 writer API and must not bypass writer
path/redaction/schema/payload safety policies.

The future GUI must not invoke the OSW-EXP-102 state writer, must not invoke the
reload file reader, must not call the OSW-EXP-128 CLI, must not use CLI
subprocesses, and must not use subprocesses. It must not write through ad hoc
file APIs outside the persistence writer boundary.

## 11. Writer Result Display

Future writer result display must render:

- status
- redacted target display
- dry-run state
- planned state
- written state
- write performed state
- persistence write performed state
- bytes count
- SHA-256
- payload kind
- schema version
- cleanup status
- temp-file status
- diagnostics
- warnings
- blockers
- non-action flags
- safety guidance

Write success, if a future gate enables it, remains only local review-record
persistence. It is not runtime reload acceptance, validation success,
validation failure, ProjectSchema mutation, trust restoration, automatic
activation, issue closure, release mutation, tag mutation, asset mutation,
bundled-solver support, or certification.

## 12. Acknowledgement Display

The future acknowledgement display must render required, satisfied, missing,
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

Acknowledgements are not validation evidence, not validation failure, and not
trust restoration. Missing or expired acknowledgements block a future GUI write.

## 13. Expiry / Invalidation Policy

Future GUI write readiness expires or invalidates on:

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
- GUI write policy change
- target path change
- target replacement policy change
- dry-run payload hash change
- acknowledgement set change

Expiry requires re-review, re-acknowledgement, and a new dry-run plan before any
future write. Expiry is not validation failure and not issue closure evidence.

## 14. Schema/Migration Policy

The future GUI write workflow must render payload kind, payload schema version,
schema support state, schema mismatch state, unsupported schema state, migration
required state, and expected writer schema policy.

Schema mismatch is not validation failure. The persistence schema remains
separate from ProjectSchema. The GUI must not repair files, migrate files,
create schema files, or mutate ProjectSchema.

## 15. Redaction/Privacy Policy

Future GUI write behavior must be redaction-first. Raw absolute paths are
hidden by default. Basename, source id, display name, and safe hash display are
preferred. Home directories, environment variables, tokens, API keys, bearer
strings, password-like values, plugin code, full JSON payloads, script content,
and full file contents must not be displayed.

Unredacted path allowances require future explicit policy. Fingerprints are not
trust signals. Writer diagnostics remain redacted. Malicious payload data
remains blocked data, not truth.

## 16. Provenance Display

Future provenance display must render persistence view-model source,
acceptance state id, preview identifier, source display, source kind, payload
fingerprint when safe, writer generated_by metadata, limitations,
untrusted-by-default state, non-authoritative state, and trust label is not
certification.

Provenance is reference-only. It is not validation evidence, validation
failure, trust restoration, ProjectSchema state, issue closure, release
evidence, or certification.

## 17. Candidate Lifecycle Display

Future candidate lifecycle display must render inactive preview review-only
state, persisted active still requiring future activation review, deactivated
remaining deactivated review state, reactivation routing to future activation
review, discovery-refresh state remaining review state, no automatic
activation, no trust restoration, and no built-in override.

Built-ins remain authoritative by default. Persisted review records never
select trusted winners.

## 18. Stale-Source/Re-Preview Display

Future stale-source/re-preview display must render old previews not silently
trusted, missing/moved/changed sources requiring re-preview, persistence GUI not
inspecting referenced source files, stale-source state not validation failure,
and re-preview remaining future-gated.

The GUI must not read referenced source files to repair stale-source state.

## 19. Conflict/Shared-Stack Display

Future conflict/shared-stack display must render conflicts visible, built-ins
winning by default, persisted records not overriding built-ins, shared-stack
warnings visible, GUI not resolving conflicts, and future policy required.

Conflict review never installs dependencies, uninstalls dependencies, uninstalls
solvers, activates candidates, restores trust, validates solvers, closes
issues, mutates releases, or claims certification.

## 20. Unsafe-Claim Display

Future unsafe-claim display must render unsafe claims visible and blocked,
unsafe claims not persisted as truth, validation success claims blocked,
validation failure claims blocked, issue closure claims blocked, release
mutation claims blocked, bundled solver claims blocked, dependency
installation claims blocked, solver execution claims blocked, trust restoration
claims blocked, and certification claims blocked.

Unsafe claims remain data to reject or review. The GUI must not repeat them as
truth.

## 21. Evidence/History Display

Future evidence/history display must render deactivation/reactivation history
retained as reference-only, historical evidence retained as reference-only,
skipped-missing remains skipped-missing, persisted record is not validation
evidence, no evidence deletion/rewrite, and no issue closure implied.

Historical evidence is context, not a validation pass, validation fail,
certification, release claim, or issue-closure claim.

## 22. Diagnostics Vocabulary

Future GUI write diagnostics reserve `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_*`
codes:

- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_UNAVAILABLE`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_NOT_REQUESTED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_TARGET_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_TARGET_SELECTED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_TARGET_REDACTED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_TARGET_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_DRY_RUN_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_DRY_RUN_REQUESTED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_DRY_RUN_PLANNED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_DRY_RUN_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_ACK_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_CONFIRMATION_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_FUTURE_ONLY`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_COMPLETED_LOCAL_RECORD`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_NOT_RUNTIME_ACCEPTANCE`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_NO_VALIDATION_CLAIM`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_NO_PROJECT_SCHEMA_MUTATION`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_ERROR`

The future GUI must also surface OSW-EXP-125, OSW-EXP-126, OSW-EXP-128, and
OSW-EXP-130 diagnostics without rewriting them as truth.

## 23. Non-Action Flags

Future GUI write review must render false/safety states for:

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
write. It never means runtime acceptance, validation evidence, validation
failure, ProjectSchema mutation, activation, trust restoration, issue closure,
release mutation, or certification.

## 24. Disabled/Future Actions

Future GUI write review must render disabled/future actions:

- `choose_target`
- `plan_persistence_record`
- `request_dry_run_plan`
- `confirm_persistence_write`
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

## 25. Relationship To OSW-EXP-130 GUI Review Panel

The OSW-EXP-130 panel remains display-only. This design treats that panel as
the review foundation for persistence readiness and supplied writer-result
records. A future write workflow must not weaken the display-only panel
contract, must not write during panel construction or refresh, and must not
turn review rendering into writer invocation.

## 26. Relationship To OSW-EXP-126 Writer

Any future actual GUI write must use the OSW-EXP-126 writer API. This gate does
not invoke the writer. The writer remains explicit-path, dry-run-first,
caller-acknowledgement-gated, redaction-first, schema-aware, and
non-authoritative. GUI code must not bypass writer path, redaction, schema,
payload-safety, temp-file, cleanup, or diagnostic policies.

## 27. Relationship To OSW-EXP-128 CLI

The OSW-EXP-128 CLI remains stdout-first and dry-run-only. GUI write design
does not call the CLI and does not use CLI subprocess. CLI success does not
imply GUI persistence, runtime reload acceptance, ProjectSchema mutation,
validation evidence, issue closure, release mutation, or certification.

## 28. Relationship To OSW-EXP-125 Persistence View-Model

The persistence view-model remains the source of readiness and write-plan
preconditions. The future GUI must consume supplied in-memory view-model
records and must not compute independent acceptance policy, edit the
view-model, read input state files, or create runtime accepted state.

## 29. Relationship To Reload Acceptance GUI/CLI

Existing reload acceptance GUI and CLI surfaces remain review-only. Persistence
GUI write is separate from acceptance review. Acceptance success does not imply
persistence. Persistence write success does not imply runtime acceptance.

## 30. Relationship To Reload File Reader And Explicit-Path Preview

The reload file reader remains explicit-path and bounded. This GUI write design
does not read input state files, parse input state files, invoke the reload file
reader, or preview source files. Preview success does not imply acceptance,
acceptance review does not imply persistence, and persistence write does not
imply runtime acceptance.

## 31. Relationship To ProjectSchema

This gate adds no ProjectSchema mutation. A persistence review record is not
ProjectSchema state and is not project validation evidence. Future
ProjectSchema integration requires a separate gate.

## 32. Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. GUI persistence output is not live
optional validation, not prepared-machine validation, not validation success,
not validation failure, and not issue closure. Skipped-missing remains
skipped-missing.

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
- no hidden default target
- no directory scan
- malicious payload remains rejected/blocked data
- writer diagnostics remain redacted

The GUI must not display raw absolute paths, home directories, environment
values, tokens, API keys, bearer strings, plugin source code, full JSON payload
content, or executable script content.

## 34. Non-Actions

This gate does not implement GUI write behavior, edit GUI source, edit source,
invoke writer, write files, read files, parse files, read input state files,
parse input state files, invoke reload file reader, invoke OSW-EXP-102 state
writer, call CLI, use CLI subprocess, use subprocess, accept runtime reload,
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

Future OSW-EXP-132 must test:

- panel imports remain stable
- target chooser is explicit and has no default target path
- target chooser does not write files
- target chooser does not create directories
- target chooser redacts target display
- dry-run request uses only OSW-EXP-126 writer planning
- dry-run planning creates no files
- actual writer call is absent unless explicitly scoped
- no file reading or parsing
- no input state-file reading or parsing
- no reload file-reader invocation
- no OSW-EXP-102 state-writer invocation
- no CLI call or CLI subprocess
- no subprocess use
- required acknowledgements block when missing or expired
- confirmation is required after dry-run
- confirmation expires on target or payload change
- writer result rendering distinguishes planned and written state
- writer result rendering says local review record only
- non-action flags render false for downstream behavior
- disabled/future actions render unsafe actions disabled
- no ProjectSchema mutation
- no discovery/validation/solver execution
- no issue/release/tag/asset mutation
- no validation-pass/fail, issue-closure, bundled-solver, or certification
  claim

## 36. Future Gates

Suggested future gates:

- `OSW-EXP-132_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_IMPLEMENTATION`, if write UI is ever needed
- `OSW-EXP-133_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_DESIGN`, if actual CLI writes are ever needed
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION`, if a prepared machine is available

If later repository docs reserve different numbering, the next gate should map
this design contract to the latest repo convention and explain the mapping.

## 37. Follow-up: Persistence GUI Write Implementation (OSW-EXP-132)

OSW-EXP-132 implements this design as an explicit-target, dry-run-first,
acknowledgement-gated, confirmation-gated GUI write panel
([optional_solver_plugin_manifest_reload_acceptance_persistence_gui_write_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_gui_write_implementation.md)).
The implementation writes only local review records through the OSW-EXP-126
writer after all gates pass. It does not write on construction, refresh, target
assignment, or dry-run; chooses no default target path; performs no background
write; reads or parses no input state files; invokes no reload file reader or
OSW-EXP-102 state writer; calls no CLI; uses no subprocess; accepts no runtime
reload; mutates no ProjectSchema; runs no discovery, validation, or solver
execution; performs no automatic activation or trust restoration; mutates no
issues/releases/tags/assets; and claims no certification.
