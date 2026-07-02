# Optional Solver Plugin Manifest Reload Acceptance Persistence Design

## 1. Status

Design-only.

This gate adds no reload acceptance persistence implementation, no source edits,
no CLI source edits, no GUI source edits, no runtime source edits, no
state-writer source edits, no file-reader source edits, no reload view-model
source edits, no reload acceptance view-model source edits, no persistence
writes, no checked-in state files, no ProjectSchema mutation, no runtime reload
acceptance, and no active acceptance mutation.

This gate also adds no file IO, no file reading, no file parsing, no reader
invocation, no CLI behavior, no GUI behavior, no subprocess use, no default
reload path, no background reload, no directory scan, no network fetch, no
plugin package import, no reloadable bundle creation, no export file creation,
no report file creation, no clipboard behavior, no report attachment, no
open-output-folder behavior, no live discovery, no passive refresh, no
validation execution, no solver execution, no dependency installation, no
dependency uninstall, no solver uninstall, no automatic activation, no trust
restoration, no issue mutation, no issue closure, no release mutation, no tag
mutation, no asset mutation, no version bump, no validation-pass claim, no
validation-fail claim, no bundled-solver claim, and no certification claim.

This document is not implementation authorization. Future implementation must
arrive through separate, reviewed gates.

## 2. Purpose

The purpose is to define future persistence semantics for reload acceptance UX
state. The design connects OSW-EXP-119
`OptionalSolverPluginManifestReloadAcceptanceViewModel` records to a future
persistence plan while preserving the distinction between preview, review,
acceptance, persistence, reload, ProjectSchema, discovery, validation,
issue/release workflows, and certification.

The design also records how a future implementation may relate to the
OSW-EXP-102 state writer without editing, invoking, extending, or authorizing
that writer in this gate.

## 3. Current State Before Acceptance Persistence

- The OSW-EXP-102 state writer exists for explicit local optional-solver UX
  state writes through caller-supplied paths.
- The OSW-EXP-113 reload file reader exists for bounded explicit-path reader
  diagnostics and safe reload mappings.
- The OSW-EXP-107 reload view-model exists for supplied reload mappings.
- The OSW-EXP-115 reload CLI explicit-path preview exists and remains
  reader-first and preview-only.
- The OSW-EXP-117 reload GUI file-dialog preview exists and remains
  reader-first and preview-only.
- The OSW-EXP-118 reload acceptance design exists.
- The OSW-EXP-119 reload acceptance view-model exists and is the acceptance
  policy source of truth.
- The OSW-EXP-121 reload acceptance GUI review panel exists and is
  view-model-only.
- The OSW-EXP-123 reload acceptance CLI review exists and is stdout-first and
  review-only.
- No reload acceptance persistence exists.
- No runtime reload acceptance exists.
- No ProjectSchema mutation exists.
- No automatic acceptance write exists.

User/plugin supplied state remains untrusted by default. Built-ins remain
authoritative by default. Issues `#6` through `#11` remain open, and
skipped-missing remains skipped-missing.

## 4. Definition Of Reload Acceptance Persistence

Future reload acceptance persistence is an explicit, redacted, user-scoped
record of review and acknowledgement state derived from
`OptionalSolverPluginManifestReloadAcceptanceViewModel`.

Future reload acceptance persistence may eventually persist:

- selected acceptance review summary;
- supplied preview provenance;
- acknowledgement states and acknowledgement expiry metadata;
- blocker and diagnostic context;
- accepted-for-session-review marker if explicitly requested;
- non-action flags;
- disabled/future action states;
- evidence/history references as reference-only.

Future reload acceptance persistence must not persist:

- runtime accepted state as trusted truth;
- automatic activation state;
- trust restoration;
- validation success or validation failure;
- ProjectSchema mutation;
- issue closure;
- release, tag, or asset mutation;
- certification;
- raw secrets;
- unredacted absolute paths by default;
- executable plugin code;
- solver execution outputs as validation truth.

## 5. Non-Meaning Of Reload Acceptance Persistence

Reload acceptance persistence is not runtime reload acceptance. Reload
acceptance persistence is not validation success. Reload acceptance persistence
is not validation failure. Reload acceptance persistence is not trust
restoration. Reload acceptance persistence is not automatic activation. Reload
acceptance persistence is not discovery success. Reload acceptance persistence is
not dependency installation. Reload acceptance persistence is not dependency
uninstall. Reload acceptance persistence is not solver uninstall. Reload
acceptance persistence is not solver execution. Reload acceptance persistence is
not ProjectSchema mutation. Reload acceptance persistence is not issue closure.
Reload acceptance persistence is not release mutation. Reload acceptance
persistence is not tag mutation. Reload acceptance persistence is not asset
mutation. Reload acceptance persistence is not certification. Reload acceptance
persistence is not report generation. Reload acceptance persistence is not
reloadable bundle creation. Reload acceptance persistence is not prepared-machine
validation.

Persistence only records a future review-state artifact if a later implementation
gate authorizes one. It does not make accepted UX state trusted, executable,
validating, or project-authoritative.

## 6. Future Persistence User Flow

Future persistence flow states are:

- `persistence_unavailable`
- `no_acceptance_viewmodel`
- `acceptance_not_requested`
- `persistence_not_requested`
- `persistence_requested`
- `acknowledgement_required`
- `persistence_blocked`
- `stale_source_repreview_required`
- `conflict_review_required`
- `unsafe_claim_blocked`
- `persistence_ready_future_only`
- `persisted_review_record_future_only`
- `runtime_acceptance_still_required`
- `future_activation_review_required`
- `future_discovery_refresh_required`
- `persistence_error`

The future flow remains explicit:

1. A caller obtains a reload preview through existing reader-first preview
   surfaces.
2. A caller reviews acceptance readiness through the OSW-EXP-119 view-model and
   the OSW-EXP-121/123 GUI or CLI review surfaces.
3. A caller explicitly requests future persistence of review-state metadata.
4. Future persistence checks acknowledgement, redaction, stale-source, conflict,
   unsafe-claim, schema, and storage policy blockers.
5. Future persistence exposes a dry-run write plan before any write.
6. A future writer may persist only redacted non-authoritative review state.
7. Runtime reload acceptance, activation, discovery refresh, validation, and
   ProjectSchema work remain separate gates.

## 7. Storage-Location Policy

Future storage options may include:

- explicit user-selected path;
- project-local optional path, only after a separate policy gate;
- user-profile/cache path, only after a separate policy gate;
- session-only non-persistent mode.

This gate defines no default write path. It creates no default reload path, no
background write, no hidden persistence, no directory creation, and no checked-in
state file. Any project-local or user-profile/cache storage policy must be
separately designed, tested, and approved.

## 8. File Format Boundary

A future conceptual JSON-like record may contain:

- payload kind;
- schema version;
- acceptance summary;
- acknowledgement rows;
- expiry metadata;
- blocker and diagnostic rows;
- redaction/privacy metadata;
- accepted-state scope;
- provenance summary;
- non-action flags;
- disabled/future action states;
- limitations;
- safety guidance.

This gate creates no schema file and no writer implementation. A future
implementation may reuse or extend OSW-EXP-102 state-writer patterns for
redaction, dry-run planning, deterministic JSON, hashes, and atomic writes, but
that requires a separate gate. The persistence schema remains separate from
ProjectSchema.

## 9. Write Preconditions

Future persistence may require:

- explicit user action;
- explicit target policy;
- supported payload kind and schema;
- redaction review;
- acknowledgement review;
- no unresolved stale-source blocker;
- no unresolved conflict/shared-stack blocker;
- no unsafe-claim blocker;
- no secret-like value blocker;
- no unredacted-path blocker;
- no changed acceptance policy without re-review;
- no changed source fingerprint without re-preview.

Missing or expired acknowledgements, unsafe claims, schema mismatch, unresolved
redaction blockers, and changed policy/source fingerprints must block future
persistence.

## 10. Dry-Run/Write-Plan Model

Future persistence must expose a dry-run write plan first. The plan must list
the target, planned size, planned hash, schema, redaction summary,
acknowledgement state, blockers, and non-action flags.

Dry-run is not write. Write-plan success is not validation success. Write-plan
success is not validation failure. Write-plan success is not runtime acceptance.
Write-plan success is not ProjectSchema mutation. Write-plan success is not
issue closure, release mutation, or certification.

## 11. Acknowledgement Persistence Model

Future persistence must render and preserve these acknowledgement identifiers:

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
validation failure. Acknowledgements are not trust restoration. Persisted
acknowledgements may expire. Missing or expired acknowledgements block future
persistence.

## 12. Acknowledgement Expiry Policy

Future persisted acknowledgement state expires for:

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

Expiry means re-review is required. Expiry is not validation failure and is not
issue closure evidence.

## 13. Accepted-State Scope Persistence

Persisted acceptance UX state is session/review scoped by default, untrusted by
default, and non-authoritative. A persisted review record is not runtime accepted
state. It is not ProjectSchema state. It is not validation evidence. It is not
validation failure. It is not automatic activation. It is not trust restoration.
It does not override built-ins. Future activation and discovery review remain
required where applicable.

## 14. Provenance Persistence

Future persistence may summarize reader diagnostics and preview provenance when
they are already redacted in supplied review records. A payload hash may be
recorded only when supplied as safe/redacted metadata.

Persisted provenance must use redacted target/source display, source ids,
display names, or hashes. It must retain limitations. It must not store raw
absolute paths by default, secrets, tokens, API keys, full file content,
executable plugin code, or unreviewed network references.

## 15. Schema/Migration Policy

Future persistence requires payload kind and schema version fields. Unsupported
schemas block persistence. Migration-required state blocks persistence. Schema
mismatch is not validation failure. The persistence schema model remains
separate from ProjectSchema. This design gate does not repair, migrate, or write
files. Any future migration requires a separate gate.

## 16. Redaction/Privacy Policy

Raw paths are hidden by default. Basename, hash, source-id, and display-name
forms are preferred. Home directories, environment variables, secrets, tokens,
and API keys are blocked. Unredacted path allowances require a future explicit
policy gate. Fingerprints are not trust signals. Diagnostics use redacted
context. Persisted acceptance records must never store secrets as truth.

## 17. Candidate Lifecycle Persistence

Inactive preview remains review-only. Persisted active state requires future
activation review. Deactivated remains deactivated review state. Reactivation
routes to future activation review. Discovery-refresh state remains review
state. Future persistence performs no automatic activation, no trust
restoration, and no override of built-ins.

## 18. Stale-Source/Re-Preview Persistence

Old preview is not silently trusted. Missing, moved, or changed sources require
re-preview. Persistence does not inspect referenced source files. Stale-source
state is not validation failure. Re-preview remains future-gated. Future
discovery-refresh results may expire acknowledgements.

## 19. Conflict/Shared-Stack Persistence

Conflicts remain visible. Built-ins win by default. A persisted acceptance
record does not override built-ins. Shared-stack warnings remain visible.
Persistence does not resolve conflicts. Any policy that changes conflict
resolution requires a future gate.

## 20. Unsafe-Claim Persistence

Unsafe claims remain visible and blocked. Unsafe claims are not persisted as
truth. Validation success and validation failure claims are blocked. Issue
closure claims are blocked. Release mutation claims are blocked. Bundled solver
claims are blocked. Dependency installation claims are blocked. Solver execution
claims are blocked. Trust restoration claims are blocked. Certification claims
are blocked.

## 21. Evidence/History Persistence

Deactivation and reactivation history may be retained as reference-only.
Historical evidence may be retained as reference-only. Skipped-missing remains
skipped-missing. A persisted acceptance record is not validation evidence and is
not validation failure. Persistence must delete no evidence, rewrite no
evidence, and imply no issue closure.

## 22. Diagnostics Vocabulary

Future persistence may reserve these `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_*`
diagnostics:

- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_NOT_REQUESTED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNAVAILABLE`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACCEPTANCE_MISSING`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACKNOWLEDGEMENT_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CONFLICT_REVIEW_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SHARED_STACK_REVIEW_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNSAFE_CLAIM_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_UNSUPPORTED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_MIGRATION_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNREDACTED_PATH_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SECRET_LIKE_VALUE_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TRUST_POLICY_CHANGED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SOURCE_FINGERPRINT_CHANGED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_POLICY_CHANGED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STORAGE_POLICY_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_DRY_RUN_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_READY`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITER_FUTURE_ONLY`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ERROR`

Diagnostics are review and planning vocabulary. They are not validation success,
validation failure, issue closure, release mutation, or certification.

## 23. Non-Action Flags

Future persisted records must display false/safety states for:

- `runtime_reload_acceptance_performed`
- `persistence_write_performed`
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

These rows must remain false unless a separate future gate explicitly designs and
implements a different behavior.

## 24. Disabled/Future Actions

Future persisted records must render disabled/future actions for:

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

Disabled/future means no action is implemented by this design gate.

## 25. Relationship To Reload Acceptance View-Model

Persistence design consumes OSW-EXP-119 reload acceptance view-model records.
Persistence does not compute acceptance policy independently. Persistence does
not mutate view-model records. Persistence does not create accepted runtime
state. Persistence preserves mapping and text semantics from the view-model.

## 26. Relationship To Reload Acceptance GUI And CLI

The GUI review panel remains view-model-only. The CLI review remains
stdout-first and review-only. Persistence design does not call GUI code and does
not call CLI code. GUI review success and CLI review success do not imply
persistence. Persistence success, if later implemented, does not imply runtime
acceptance.

## 27. Relationship To Reload File Reader And Explicit-Path Preview

The reload file reader remains explicit-path and bounded. Preview success does
not imply acceptance. Acceptance readiness does not imply persistence.
Persistence does not read files or invoke the reader in this design gate.

## 28. Relationship To State Writer

The OSW-EXP-102 state writer is the closest writer pattern. This gate does not
edit or invoke it. A future implementation may reuse its redaction, dry-run,
hash, deterministic JSON, and atomic-write approach. Future integration requires
separate tests and gates.

## 29. Relationship To ProjectSchema

This gate performs no ProjectSchema mutation. Persisted acceptance UX state is
not ProjectSchema state. Persisted acceptance UX state is not project validation
evidence. Future ProjectSchema integration requires a separate gate.

## 30. Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. Persistence does not close issues.
Persistence output is not live optional validation. Skipped-missing remains
skipped-missing. Prepared-machine validation remains separate.

## 31. Security/Privacy Review

Future persistence must keep secrets out of diagnostics, avoid raw path leaks,
avoid full file content display, avoid remote URL fetch, avoid script execution,
avoid plugin package import, avoid solver execution, and avoid trust
restoration. Malicious payloads remain rejected or blocked data. Denial-of-
service controls are inherited from reader, view-model, and future writer
boundaries. Persisted JSON must remain redacted.

## 32. Non-Actions

This gate does not implement reload acceptance persistence, edit source, edit
CLI source, edit GUI source, edit runtime source, edit state-writer source, edit
file-reader source, edit reload view-model source, edit reload acceptance
view-model source, write persistence/state files, create checked-in state files,
mutate ProjectSchema, accept runtime reload, perform active acceptance mutation,
perform file IO, read files, parse files, invoke the reader, call GUI code, call
CLI code, use subprocess, add default reload path, add background reload, scan
directories, fetch network manifests, import plugin packages, create reloadable
bundles, create export files, create report files, add clipboard behavior, add
report attachment, add open-output-folder behavior, add live discovery, add
passive refresh, run validation, run solver execution, install dependencies,
uninstall dependencies, uninstall solvers, automatically activate candidates,
restore trust, mutate issues, mutate releases, mutate tags, mutate assets, bump
version, claim validation-pass, claim validation-fail, claim issue closure,
claim bundled solver, or claim certification.

## 33. Future Implementation Test Plan

Future OSW-EXP-125/126 gates must test:

- persistence view-model consumes supplied acceptance view-model records;
- no runtime acceptance;
- no file writes until an implementation gate explicitly scopes writer
  behavior;
- dry-run plan before write;
- no default path;
- no background write;
- no ProjectSchema mutation;
- raw paths and secrets are not leaked;
- missing acknowledgements block;
- expired acknowledgements block;
- stale-source, conflict, unsafe-claim, schema, and redaction blockers remain
  visible;
- non-action flags are preserved;
- disabled/future actions are preserved;
- ready state is future-only until writer implementation;
- write success is not validation success or validation failure;
- write success is not runtime acceptance;
- no issue/release/tag/asset mutation;
- existing acceptance view-model, GUI, and CLI tests still pass;
- existing state writer tests still pass.

## 34. Future Gates

Suggested sequence:

- `OSW-EXP-125_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_VIEWMODEL`
- `OSW-EXP-126_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_IMPLEMENTATION`
- `OSW-EXP-127_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_REVIEW_DESIGN`, if needed
- `OSW-EXP-128_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_REVIEW_DESIGN`, if needed
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION`, if a prepared machine is available

Runtime reload acceptance, activation, discovery refresh, ProjectSchema
integration, validation, issue/release workflows, export/report integration,
reloadable bundles, and certification remain future-gated.

## 35. Follow-up: Acceptance Persistence ViewModel (OSW-EXP-125)

OSW-EXP-125 implements the pure in-memory reload acceptance persistence
view-model described by this design
([optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel.md](optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel.md)).
It adds future-writer-only planning records, storage policy rows,
acknowledgements, expiry, blockers, diagnostics, non-action flags,
disabled/future actions, provenance, evidence/history, and safety guidance.

The implementation remains non-writing and performs no persistence write, no
checked-in state file creation, no runtime reload acceptance, no file IO, no
reader or writer invocation, no CLI/GUI behavior, no subprocess use, no
ProjectSchema mutation, no discovery, no validation, no solver execution, no
automatic activation, no trust restoration, no issue/release/tag/asset mutation,
and no certification claim.

## 37. Follow-up: Persistence Writer Implementation (OSW-EXP-126)

OSW-EXP-126 implements the first persistence writer
([optional_solver_plugin_manifest_reload_acceptance_persistence_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_implementation.md))
for reload acceptance records. It remains explicit-target-path only,
dry-run-first, deterministic, local, redacted, and caller-acknowledged before
actual writes.

The implementation preserves this design's boundaries: no runtime reload
acceptance, no active acceptance mutation, no default path, no background write,
no input state-file reading or parsing, no reader invocation, no CLI/GUI
behavior, no subprocess use, no ProjectSchema mutation, no discovery,
validation, solver execution, activation, trust restoration,
issue/release/tag/asset mutation, validation-pass/fail claim, bundled-solver
claim, or certification claim.
