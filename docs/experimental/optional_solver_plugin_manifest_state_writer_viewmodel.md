# Optional solver plugin manifest state writer view-model

## 1. Status

OSW-EXP-101 adds a pure, side-effect-free, in-memory state-writer
readiness/write-plan view-model:

- public module:
  `src/osw/experimental/optional_solvers/plugin_manifest_state_writer_viewmodel.py`
- public class:
  `OptionalSolverPluginManifestStateWriterViewModel`
- no writer implementation
- no file writes
- no directory creation
- no runtime state files
- no settings files
- no schema files
- no export files
- no report files
- no reloadable bundles
- no ProjectSchema mutation
- no GUI behavior
- no CLI behavior
- no reload behavior
- no export behavior
- no discovery execution
- no validation execution
- no solver execution

## 2. Purpose

The view-model answers whether supplied optional solver plugin manifest UX state
is unavailable, blocked, dry-run-only, ready for future write review, or waiting
for a future writer gate. It makes storage options, schema readiness, redaction,
acknowledgements, stale-source/re-preview, conflicts, unsafe claims,
evidence/history, atomicity/error planning, non-action flags, diagnostics, and
disabled/future actions deterministic before any real writer exists.

Persisted state remains non-authoritative. It is not validation evidence, trust
restoration, automatic activation, dependency installation, discovery success,
solver execution, issue closure, release mutation, bundled-solver evidence, or
certification.

## 3. Public module/class names

The public module is:

`osw.experimental.optional_solvers.plugin_manifest_state_writer_viewmodel`

The public class is:

`OptionalSolverPluginManifestStateWriterViewModel`

The package export also exposes:

- `build_optional_solver_plugin_manifest_state_writer_viewmodel`
- `summarize_optional_solver_plugin_manifest_state_writer_viewmodel`
- `explain_optional_solver_plugin_manifest_state_writer_viewmodel`
- `render_optional_solver_plugin_manifest_state_writer_viewmodel`
- `redact_optional_solver_plugin_manifest_state_writer_source_reference`
- `STATE_WRITER_REQUIRED_ACKS`
- `OSPMG_STATE_WRITER_*` diagnostic constants

## 4. Input boundary

The view-model only transforms supplied in-memory records. Callers may provide
sources, candidates, acknowledgement states, diagnostics, redaction rows,
stale-source rows, conflict rows, unsafe-claim rows, and evidence/history rows.

The adapters from persistence view-models, schema models, and export-summary
view-models consume already-supplied records without mutating those inputs. The
view-model does not read files, parse files from paths, inspect path existence,
import plugin packages, scan directories, fetch network manifests, run
discovery, run validation, execute solvers, or install/uninstall anything.

## 5. Writer readiness model

The readiness vocabulary is:

- `unavailable_no_state`
- `unavailable_no_explicit_request`
- `dry_run_only`
- `blocked_acknowledgement`
- `blocked_redaction_review`
- `blocked_unredacted_path`
- `blocked_secret_like_content`
- `blocked_schema_version_missing`
- `blocked_schema_unsupported`
- `blocked_schema_migration_required`
- `blocked_stale_source_repreview`
- `blocked_conflict`
- `blocked_shared_stack_warning`
- `blocked_unsafe_claim`
- `ready_for_future_write`
- `future_writer_required`
- `error`

Precedence is error/no-state/no-explicit-request, schema blockers, redaction
blockers, stale-source blockers, conflict/shared-stack blockers, unsafe claims,
acknowledgements, dry-run-only, ready-for-future-write, and future-writer-required
states.

## 6. Write-plan model

The write-plan record includes a plan id, readiness, state scope, schema version,
redacted target reference display, target approval state, planned counts,
blockers, warnings, and diagnostics.

All write-effect flags remain false:

- `would_write`
- `would_create_directory`
- `would_mutate_project_schema`
- `would_reload`
- `would_export`

The default target reference is `no default write path`.

## 7. Storage-option model

The storage-option records are future-only and not allowed in this gate:

- `project_local`
- `user_profile_cache`
- `session_local_ephemeral`
- `explicit_user_chosen_file`
- `no_default_write_path`

Each option records privacy, stale-state, ProjectSchema-confusion, portability,
cleanup, and diagnostic notes. `no_default_write_path` remains the default.

## 8. File-format/schema-boundary model

The file-format/schema-boundary record is conceptual. It records:

- `format_kind`
- `conceptual_format`
- schema version required/supported state
- migration-required state
- stable-key and deterministic-ordering requirements
- redaction metadata requirements
- migration-note retention
- ProjectSchema boundary text

It also records that no schema file is created and no actual JSON writer is
implemented.

## 9. Source/trust/provenance model

Source rows include source id, source type, label, redacted display reference,
trust label, persisted-state kind, fingerprint display text, stale-source state,
re-preview state, raw-reference blocking, and diagnostics.

User/plugin manifest sources remain untrusted by default. Trust labels are not
certification. Persisted writer state is not validation evidence and is not trust
restoration.

## 10. Candidate writer model

Candidate rows include stack id, display name, source id/type, trust label,
activation/deactivation/reactivation/discovery-refresh/persistence/writer state,
readiness, blockers, warnings, required acknowledgements, diagnostics,
stale-source state, redaction status, built-in relationship, shared-stack
indicators, deactivation/reactivation history state, historical evidence state,
and validation-evidence state.

Candidate rows explicitly keep these false:

- issue closure implied
- automatic activation implied
- trust restoration implied

## 11. Acknowledgement and expiry model

The required acknowledgement identifiers are:

- `state_write_not_validation`
- `state_write_not_trust_restoration`
- `state_write_not_automatic_activation`
- `state_write_not_dependency_install`
- `state_write_no_solver_execution`
- `state_write_not_issue_closure`
- `state_write_not_release_mutation`
- `state_write_not_certification`
- `local_path_redaction_reviewed`
- `unredacted_paths_blocked`
- `persisted_acknowledgements_may_expire`
- `stale_source_requires_repreview`
- `untrusted_source_remains_untrusted`
- `activation_review_required_after_reload`
- `no_discovery_execution`
- `no_plugin_package_import`
- `trust_label_not_certification`
- `export_summary_not_reloadable_bundle`

Each acknowledgement exposes required/satisfied/persisted state and expiry flags
for reload, source fingerprint, schema, unsafe claims, and trust-policy changes.
Missing required acknowledgements block future writing.

## 12. Diagnostic vocabulary

The view-model reserves and surfaces `OSPMG_STATE_WRITER_*` diagnostics:

- `OSPMG_STATE_WRITER_NOT_IMPLEMENTED`
- `OSPMG_STATE_WRITER_DRY_RUN_ONLY`
- `OSPMG_STATE_WRITER_ACK_REQUIRED`
- `OSPMG_STATE_WRITER_NOT_VALIDATION`
- `OSPMG_STATE_WRITER_NOT_TRUST_RESTORE`
- `OSPMG_STATE_WRITER_NOT_AUTOMATIC_ACTIVATION`
- `OSPMG_STATE_WRITER_NO_INSTALL`
- `OSPMG_STATE_WRITER_NO_SOLVER_EXECUTION`
- `OSPMG_STATE_WRITER_NOT_ISSUE_CLOSURE`
- `OSPMG_STATE_WRITER_NOT_RELEASE_MUTATION`
- `OSPMG_STATE_WRITER_NOT_CERTIFICATION`
- `OSPMG_STATE_WRITER_REDACTION_REQUIRED`
- `OSPMG_STATE_WRITER_UNREDACTED_PATH_BLOCKED`
- `OSPMG_STATE_WRITER_SECRET_LIKE_CONTENT_BLOCKED`
- `OSPMG_STATE_WRITER_SCHEMA_VERSION_REQUIRED`
- `OSPMG_STATE_WRITER_SCHEMA_UNSUPPORTED`
- `OSPMG_STATE_WRITER_SCHEMA_MIGRATION_REQUIRED`
- `OSPMG_STATE_WRITER_STALE_SOURCE_REPREVIEW_REQUIRED`
- `OSPMG_STATE_WRITER_UNTRUSTED_SOURCE`
- `OSPMG_STATE_WRITER_CONFLICT_BLOCKED`
- `OSPMG_STATE_WRITER_SHARED_STACK_WARNING`
- `OSPMG_STATE_WRITER_UNSAFE_CLAIM`
- `OSPMG_STATE_WRITER_EVIDENCE_RETAINED`
- `OSPMG_STATE_WRITER_HISTORY_RETAINED`
- `OSPMG_STATE_WRITER_NO_DISCOVERY_EXECUTION`
- `OSPMG_STATE_WRITER_NO_PLUGIN_IMPORT`
- `OSPMG_STATE_WRITER_PROJECT_SCHEMA_MUTATION_DISABLED`
- `OSPMG_STATE_WRITER_RELOAD_DISABLED`
- `OSPMG_STATE_WRITER_EXPORT_DISABLED`
- `OSPMG_STATE_WRITER_FUTURE_GATE`

## 13. Redaction/privacy policy

The view-model redacts path-like source references to a basename for display.
Unredacted paths are blocked. Secret-like source content is blocked. Fingerprints
are not trust signals. Redaction rows expose privacy warnings, whether redaction
was reviewed, whether content is safe to share, and which diagnostics apply.

## 14. Schema/migration policy

Schema/migration rows require a schema version, block unsupported schema
versions, block required migrations until future review, record migration notes,
record that no schema file was created, and state that state-writer schema
records are not ProjectSchema records.

## 15. Stale-source and re-preview policy

Stale-source rows show stale-source state, re-preview requirement, redacted
display reference, and future-policy requirements. They explicitly state that
old previews are not silently trusted and that no file IO, file restoration,
file rewrite, or file deletion is performed.

## 16. Conflict/shared-stack policy

Conflict rows retain built-in, user, and plugin source state. Built-ins win by
default. Conflicts remain visible. Persisted state does not override built-ins.
Shared-stack warnings require acknowledgement and future policy before any real
write.

## 17. Unsafe-claim policy

Unsafe-claim rows record claim id, related source/candidate ids, claim text,
blocking state, warning text, and false acceptance flags. Unsafe claims are not
accepted by the writer and are not persisted as truth.

## 18. Evidence/history retention policy

Evidence/history rows retain deactivation history, reactivation history, and
historical validation evidence as references only. Skipped-missing remains
skipped-missing. Writer state is not validation evidence and does not rewrite
issue closure, validation evidence, or historical evidence.

## 19. Atomicity/error handling plan model

Atomicity/error records are future requirements only. They require write-plan
review first, target-path policy review, future atomic temp/replace behavior,
reserved path-redacted diagnostics, future rollback policy, and no partial-write
claim in this gate.

## 20. Non-action flags

All non-action flags remain false, including:

- writer implemented
- dry-run performed
- file write performed
- runtime state file created
- settings file created
- schema file created
- export file created
- report file created
- reloadable bundle created
- ProjectSchema mutation performed
- GUI behavior added
- CLI behavior added
- reload behavior added
- export behavior added
- clipboard performed
- report attachment performed
- open-output-folder performed
- automatic activation performed
- trust restoration performed
- file restoration/rewrite/deletion performed
- dependency install/uninstall performed
- solver uninstall performed
- plugin package import performed
- directory scan performed
- network fetch performed
- discovery/validation/solver execution performed
- issue/release/tag/asset mutation performed
- version bump performed
- validation-pass/fail claim made
- certification claimed

## 21. Action-state model

In-memory review actions are available for requesting dry-run review, reviewing
write plans, reviewing redaction/schema/migration/stale-source/conflict/unsafe
claim state, and acknowledging safety text.

Unsafe or future actions are disabled or marked future-only:

- write state file
- create runtime state file
- create settings file
- create schema file
- create export file
- create report file
- create reloadable bundle
- mutate ProjectSchema
- reload state
- export state
- copy to clipboard
- attach report
- open output folder
- import plugin package
- scan directory
- fetch network manifest
- run discovery
- run validation
- install dependency
- uninstall dependency
- uninstall solver
- execute solver
- close issue
- mutate release
- push tag
- upload asset

## 22. Relationship to OSW-EXP-100 design

OSW-EXP-100 defined state-writer semantics as design-only. OSW-EXP-101 is the
first pure implementation follow-up. It implements the in-memory readiness and
write-plan records, not the actual writer.

## 22a. Relationship to OSW-EXP-102 writer implementation

OSW-EXP-102 adds
[optional_solver_plugin_manifest_state_writer_implementation.md](optional_solver_plugin_manifest_state_writer_implementation.md),
an explicit local writer library API that consumes this view-model or its
mapping output. The writer requires a caller-supplied target path, deterministic
JSON serialization, dry-run/preflight review, explicit write acknowledgement,
and atomic temp-file/replace behavior.

This view-model remains non-writing. OSW-EXP-102 does not mutate this
view-model's records or turn them into ProjectSchema state, reload behavior,
GUI/CLI controls, export/report/clipboard behavior, discovery, validation,
solver execution, issue/release mutation, validation-pass/fail claims, trust
restoration, automatic activation, or certification.

## 23. Relationship to OSW-EXP-092/093 persistence models

OSW-EXP-092 supplied the persistence view-model. OSW-EXP-093 supplied the pure
in-memory persistence schema model. OSW-EXP-101 can adapt supplied records from
both without mutating them. It does not change persistence view-model behavior,
schema-model behavior, or persistence source behavior.

## 24. Relationship to GUI, CLI, reload, export, ProjectSchema

This gate does not implement GUI behavior, CLI behavior, reload behavior, export
behavior, ProjectSchema mutation, file dialogs, save dialogs, clipboard
behavior, report attachment, or open-output-folder behavior.

Future GUI/CLI/reload/export/ProjectSchema gates must continue to treat the
state-writer view-model as review evidence, not as permission to write or trust
state.

## 25. Relationship to live optional validation issues

Issues `#6` through `#11` remain open. State-writer readiness is not validation
pass evidence, validation fail evidence, issue closure, bundled solver evidence,
or certification.

## 26. Non-actions

This gate does not:

- implement an actual writer
- write files
- create directories
- create runtime state files
- create settings files
- create schema files
- create export files
- create report files
- create reloadable bundles
- mutate ProjectSchema
- implement GUI behavior
- implement CLI behavior
- implement reload behavior
- implement export behavior
- add file dialog behavior
- add save dialog behavior
- add clipboard behavior
- add report attachment behavior
- add open-output-folder behavior
- automatically activate candidates
- restore trust
- restore files
- rewrite manifest files
- delete files
- install dependencies
- uninstall dependencies
- uninstall solvers
- import plugin packages
- scan directories
- fetch network manifests
- run discovery
- run validation
- execute solvers
- mutate issues
- mutate releases
- mutate tags
- mutate assets
- bump versions
- claim validation success
- claim validation failure
- claim issue closure
- claim bundled solvers
- claim certification

## 27. Future gates

Future separate gates are required for:

- OSW-EXP-102 state writer implementation
- atomic write strategy
- runtime state files
- settings files
- schema files
- GUI writer controls
- CLI writer commands
- reload behavior
- export/report integration
- reloadable bundles
- ProjectSchema integration
- source integration
- discovery integration
- validation
- install/uninstall
- solver execution
- issue/release/tag/asset actions
