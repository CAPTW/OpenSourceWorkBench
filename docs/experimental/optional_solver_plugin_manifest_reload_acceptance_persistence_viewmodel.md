# Optional Solver Plugin Manifest Reload Acceptance Persistence ViewModel

## 1. Status

Experimental reload acceptance persistence view-model implemented.

- Pure in-memory.
- View-model-only.
- Future-writer-only.
- No persistence writes.
- No checked-in state files.
- No runtime reload acceptance.
- No active acceptance mutation.
- No file IO.
- No file reading.
- No file parsing.
- No reader invocation.
- No CLI behavior.
- No GUI behavior.
- No subprocess use.
- No ProjectSchema mutation.
- No discovery/validation/solver execution.
- No automatic activation.
- No trust restoration.

It also performs no dependency installation, dependency uninstall, solver
uninstall, issue/release/tag/asset mutation, version bump, validation-pass or
validation-fail claim, issue-closure claim, bundled-solver claim, or
certification claim.

## 2. Purpose

The purpose is to model future persistence readiness for reviewed reload
acceptance UX state without writing that state. The view-model lets tests and
future callers inspect storage policy, write-plan preconditions,
acknowledgements, expiry, blockers, diagnostics, provenance, evidence/history,
non-action flags, disabled/future actions, and safety guidance before any
writer is implemented.

## 3. Public module/class names

The module is
`osw.experimental.optional_solvers.plugin_manifest_reload_acceptance_persistence_viewmodel`.

The primary class is
`OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel`.

Public record and enum names include `ReloadAcceptancePersistenceState`,
`ReloadAcceptancePersistenceReadiness`, `ReloadAcceptancePersistenceAction`,
`ReloadAcceptancePersistenceSummary`,
`ReloadAcceptancePersistenceStorageOption`,
`ReloadAcceptancePersistenceSchemaRow`,
`ReloadAcceptancePersistenceAcknowledgementRow`,
`ReloadAcceptancePersistenceExpiryRow`,
`ReloadAcceptancePersistenceBlockerRow`,
`ReloadAcceptancePersistenceDiagnostic`,
`ReloadAcceptancePersistenceNonActionFlags`,
`ReloadAcceptancePersistenceActionRow`,
`ReloadAcceptancePersistenceWritePlan`,
`ReloadAcceptancePersistenceProvenanceRow`, and
`ReloadAcceptancePersistenceEvidenceRow`.

## 4. Input policy

Inputs are already-built
`OptionalSolverPluginManifestReloadAcceptanceViewModel` objects or safe
in-memory mappings supplied by the caller. The module does not accept paths,
does not read files, does not parse persisted state files, does not invoke the
reload file reader, does not invoke a state writer, and does not call CLI or GUI
code.

## 5. Construction behavior

`unavailable()`, `from_acceptance_viewmodel()`, `from_acceptance_mapping()`,
`build_optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel()`,
and `ready_for_future_writer()` construct deterministic records. Construction
copies supplied mapping data into view-model rows, redacts unsafe display
values, maps acceptance blockers into persistence blockers, and never mutates
the supplied object or mapping.

## 6. Persistence state/readiness model

States cover `persistence_unavailable`, `no_acceptance_viewmodel`,
`acceptance_not_requested`, `persistence_not_requested`,
`persistence_requested`, `acknowledgement_required`, `persistence_blocked`,
`stale_source_repreview_required`, `conflict_review_required`,
`unsafe_claim_blocked`, `persistence_ready_future_only`,
`persisted_review_record_future_only`, `runtime_acceptance_still_required`,
`future_activation_review_required`, `future_discovery_refresh_required`, and
`persistence_error`.

Readiness is derived from supplied acceptance records, persistence request
state, acknowledgements, storage policy, dry-run confirmation, and policy flags.

## 7. Write-plan model

The write plan records target display, schema id, schema version, payload kind,
source count, acknowledgement count, provenance count, evidence count, blocker
count, warning count, diagnostic count, dry-run requirement, and writer
future-only state. `write_performed`, `persistence_write_performed`,
`runtime_reload_acceptance_performed`, and `project_schema_mutated` remain
false.

## 8. Storage-location policy

Storage is explicit and future-only. No default path is selected. Raw paths are
hidden by default. The view-model can describe an explicit future
user-selected target display, but it does not create directories, open files,
write files, or choose hidden storage.

## 9. File-format/schema boundary

The view-model reserves a persistence schema id, schema version, and payload
kind. The persistence schema is separate from ProjectSchema. Unsupported schema
and migration-required conditions block future persistence. The module creates
no schema files and performs no repair or migration.

## 10. Write preconditions

Future persistence requires an acceptance view-model, an explicit persistence
request, required acknowledgements, non-expired acknowledgements, storage
policy, dry-run confirmation, supported schema, no migration blocker, no stale
source blocker, no conflict/shared-stack blocker, no unsafe claim blocker, no
unredacted path blocker, no secret-like value blocker, and no trust/source/
policy change blocker.

## 11. Acknowledgement model

Acknowledgements cover that acceptance is not validation, not validation
failure, not trust restoration, not automatic activation, not discovery
success, not dependency installation, not solver execution, not issue closure,
not release mutation, not certification, not persistence write, and not
ProjectSchema mutation. They also cover redaction review, unredacted path
blocking, stale-source re-preview, untrusted source handling, future activation
review, no discovery execution, no plugin package import, no validation
execution, no solver execution, trust label not certification, and
acknowledgement expiry.

## 12. Acknowledgement expiry model

Expiry reasons include reload, source fingerprint change, schema version
change, unsafe claim appearance, trust policy change, future discovery-refresh
result, file-reader policy change, GUI file-dialog policy change, CLI
explicit-path policy change, acceptance policy change, ProjectSchema policy
change, validation issue state change, persistence schema change, and
persistence storage policy change.

## 13. Accepted-state scope model

Accepted-for-session-review remains session/review scoped and untrusted by
default. It is not persisted truth, not runtime reload acceptance, not
ProjectSchema state, not validation evidence, not validation failure, not
automatic activation, not trust restoration, not discovery success, not solver
execution, not issue closure, not release mutation, and not certification.

## 14. Provenance model

Provenance rows summarize supplied acceptance provenance as redacted,
non-authoritative, untrusted-by-default context. Safe supplied fingerprints may
be carried, but fingerprints are not trust signals. The module does not inspect
or open referenced sources.

## 15. Schema/migration model

Schema rows state that payload kind and schema version are required, unsupported
schema blocks future persistence, migration-required blocks future persistence,
schema mismatch is not validation failure, the persistence schema remains
separate from ProjectSchema, and the view-model does not repair or migrate
files.

## 16. Redaction/privacy model

Raw absolute paths are hidden by default. Basenames, display names, source ids,
and safe fingerprints are preferred. Home directories, environment variables,
secrets, tokens, and API keys are blocked or redacted. Accepted state must never
store secrets as truth.

## 17. Candidate lifecycle model

Persisted acceptance review state is not automatic activation. Persisted active
or reactivation concepts remain future activation-review matters. Deactivated
state remains deactivated review state. Discovery-refresh state remains review
state. Built-ins remain authoritative by default.

## 18. Stale-source/re-preview model

Old previews are not silently trusted. Missing, moved, or changed sources
require re-preview. This view-model does not inspect source files. Stale-source
state is not validation failure. Re-preview and discovery refresh remain
future-gated.

## 19. Conflict/shared-stack model

Conflicts and shared-stack review requirements remain visible blockers.
Built-ins win by default. The view-model does not resolve conflicts and does
not override built-ins.

## 20. Unsafe-claim model

Unsafe validation, issue, release, trust, dependency installation, solver
execution, bundled-solver, or certification claims are blocked and not rendered
as truth.

## 21. Evidence/history model

Evidence/history rows are retained as reference-only. They are not validation
evidence, not validation failure, and imply no issue closure or release
mutation. The module deletes, rewrites, or creates no evidence.

## 22. Diagnostics vocabulary

The `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_*` vocabulary includes not-requested,
unavailable, acceptance-missing, acknowledgement-required, stale-source
re-preview required, conflict review required, shared-stack review required,
unsafe claim blocked, unsupported schema, migration required, unredacted path
blocked, secret-like value blocked, trust policy changed, source fingerprint
changed, policy changed, storage policy required, dry run required, ready,
writer future-only, and error diagnostics.

## 23. Non-action flags

All non-action flags remain false. The flags include runtime reload acceptance,
persistence write, ProjectSchema mutation, default reload path, background
reload, directory scan, network fetch, plugin package import, CLI subprocess,
GUI subprocess, reloadable bundle, export file, report file, clipboard, report
attachment, output folder opening, live discovery, passive refresh, validation,
solver execution, dependency install/uninstall, solver uninstall, candidate
activation, trust restoration, issue/release/tag/asset mutation, version bump,
validation-pass/fail claim, issue-closure claim, bundled-solver claim, and
certification claim.

## 24. Disabled/future actions

Disabled and future-only actions include `persist_acceptance_record`,
`write_acceptance_state`, `accept_for_session_review`, `accept_as_trusted`,
`activate_reloaded_candidate`, `refresh_discovery`, `validate_solver`,
`execute_solver`, `install_dependency`, `uninstall_dependency`,
`uninstall_solver`, `mutate_project_schema`, `create_export_summary`,
`create_report_file`, `create_reloadable_bundle`, `copy_to_clipboard`,
`attach_to_report`, `open_output_folder`, `close_issue`, `mutate_release`,
`push_tag`, `upload_asset`, `claim_validation_success`,
`claim_validation_failure`, and `claim_certification`.

## 25. Mapping/text output

`to_mapping()` returns deterministic JSON-compatible records. `to_text_lines()`
returns stable review text. Text and mapping output do not claim validation
success, validation failure, runtime acceptance, persistence write, issue
closure, release mutation, trust restoration, activation, or certification.

## 26. Relationship to reload acceptance persistence design

This implementation follows
[optional_solver_plugin_manifest_reload_acceptance_persistence_design.md](optional_solver_plugin_manifest_reload_acceptance_persistence_design.md)
by implementing only the pure view-model and write-plan layer. Writer behavior
remains future-gated.

## 27. Relationship to reload acceptance view-model

The OSW-EXP-119 acceptance view-model remains the acceptance policy source. This
module consumes its `to_mapping()` output or equivalent safe mappings and adds
future persistence planning without editing or invoking the acceptance source
module.

## 28. Relationship to reload acceptance GUI and CLI

The OSW-EXP-121 GUI panel and OSW-EXP-123 CLI remain review-only acceptance
surfaces. This view-model does not call GUI or CLI code. Future GUI/CLI
persistence rendering remains separately gated.

## 29. Relationship to reload file reader and explicit-path preview

The OSW-EXP-113 file reader and OSW-EXP-115 explicit-path preview remain the
reader/preview path. This view-model does not read files, parse files, invoke
the reader, or accept file paths.

## 30. Relationship to state writer

The OSW-EXP-102 state writer remains the future writer reference, but this
module does not import, invoke, edit, or wrap it. It only prepares
future-writer-only planning records.

## 31. Relationship to ProjectSchema

The persistence schema stays separate from ProjectSchema. The module does not
mutate ProjectSchema and does not describe persistence readiness as project
state.

## 32. Relationship to live optional validation issues

Issues `#6` through `#11` remain open. Persistence readiness is not optional
validation evidence, not validation failure, not issue closure, and not
prepared-machine validation.

## 33. Security/privacy review

The implementation is redaction-first and path-hiding by default. It blocks or
redacts secret-like values and avoids raw file content. User/plugin supplied
state remains untrusted by default.

## 34. Non-actions

This gate performs no runtime reload acceptance, active acceptance mutation,
file IO, file reading, file parsing, writer invocation, reader invocation, CLI
behavior, GUI behavior, subprocess use, checked-in state file creation,
ProjectSchema mutation, persistence write, default reload path, background
reload, directory scan, network fetch, plugin package import, reloadable bundle
creation, export/report file creation, clipboard/report/open-folder behavior,
live discovery, passive refresh, validation execution, solver execution,
dependency installation, dependency uninstall, solver uninstall, automatic
activation, trust restoration, issue/release/tag/asset mutation, version bump,
validation-pass or validation-fail claim, bundled-solver claim, or
certification claim.

## 35. Testing strategy

Focused unit tests cover imports/exports, no-preview, not-requested,
acknowledgement blocking, expired acknowledgements, ready future-writer-only
state, accepted-for-session-review scope, deterministic mapping/text output,
acknowledgement rows, expiry rows, storage/schema rows, provenance redaction,
stale-source, conflict, shared-stack, unsafe claims, schema/migration/privacy
blockers, policy changes, mapped acceptance blockers, non-action flags,
disabled/future actions, evidence/history rows, helper functions, source import
and call guardrails, and absence of output/runtime state files.

## 36. Future gates

Future gates may implement the actual persistence writer, persistence CLI/GUI
rendering, ProjectSchema integration, activation/discovery-review consumption,
prepared-machine validation, issue/release workflows, or certification-safe
release evidence. Each must remain separately reviewed and preserve the
non-writing, non-validation, non-trust-restoration, non-activation,
ProjectSchema-safe, issue/release-safe, and certification-safe boundaries.

## 37. Follow-up: Persistence Writer (OSW-EXP-126)

OSW-EXP-126 implements the explicit reload acceptance persistence writer
([optional_solver_plugin_manifest_reload_acceptance_persistence_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_implementation.md))
as the separately gated consumer of this future-writer-only view-model. The
writer accepts this view-model as in-memory input, starts in dry-run mode, and
requires an explicit target path plus caller acknowledgement before any write.

The writer does not change this view-model's policy. It adds no runtime reload
acceptance, active acceptance mutation, default path, background write, reader
invocation, CLI/GUI behavior, subprocess use, ProjectSchema mutation,
discovery, validation, solver execution, activation, trust restoration,
issue/release/tag/asset mutation, validation-pass/fail claim, bundled-solver
claim, or certification claim.

## 38. Follow-up: Persistence CLI Design (OSW-EXP-127)

OSW-EXP-127 designs a future CLI review/write-plan surface over this persistence
view-model and the OSW-EXP-126 writer boundary
([optional_solver_plugin_manifest_reload_acceptance_persistence_cli_design.md](optional_solver_plugin_manifest_reload_acceptance_persistence_cli_design.md)).
The design does not change this view-model source or add CLI behavior.

The future CLI remains stdout-first, dry-run/write-plan oriented, explicit-path
only for any future write, redaction-first, and non-authoritative. This design
gate performs no writer invocation, file write, input file read or parse,
reader invocation, state-writer invocation, GUI call, subprocess use, runtime
acceptance, ProjectSchema mutation, discovery, validation, solver execution,
activation, trust restoration, issue/release/tag/asset mutation, validation
claim, or certification claim.
