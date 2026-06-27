# Optional solver plugin manifest persistence CLI design

## 1. Status

Design-only.

No runtime behavior is added in this gate. No CLI implementation is added in
this gate. No persistence implementation is added in this gate. This document
defines future command vocabulary, output semantics, dry-run behavior, redaction
review, acknowledgement expiry, schema/migration review, stale-source handling,
diagnostics, disabled/future actions, and follow-up gates for optional solver
plugin manifest persistence CLI review.

Status boundaries:

- no runtime behavior
- no CLI implementation
- no persistence implementation
- no file writes
- no settings file creation
- no runtime state file creation
- no schema file creation
- no ProjectSchema mutation
- no save command implementation
- no load command implementation
- no reload behavior
- no export behavior
- no clipboard behavior
- no open-output-folder behavior
- no GUI behavior
- no activation/deactivation/reactivation/discovery-refresh source mutation
- no persistence view-model or schema-model source mutation
- no manifest file restoration
- no manifest file rewrite
- no manifest file deletion
- no file restoration
- no file rewrite
- no file deletion
- no automatic activation
- no trust restoration
- no dependency installation
- no dependency uninstall
- no solver uninstall
- no plugin package import
- no directory scan
- no network fetch
- no discovery execution
- no validation execution
- no solver execution
- no issue mutation
- no issue closure
- no release mutation
- no tag mutation
- no asset mutation
- no version bump
- no validation-pass claim
- no validation-fail claim
- no certification claim

## 2. Purpose

Define future CLI semantics for optional solver plugin manifest persistence
readiness.

The persistence CLI design preserves explicit-import, activation, deactivation,
reactivation, discovery-refresh, persistence view-model, schema-model, and
persistence GUI boundaries. It makes persistence CLI distinct from file writes,
settings file creation, runtime state file creation, schema file creation,
ProjectSchema mutation, save command behavior, load command behavior, reload
behavior, export behavior, clipboard behavior, open-output-folder behavior,
validation, trust restoration, dependency installation, dependency uninstall,
solver uninstall, solver execution, issue closure, release mutation, tag
mutation, asset mutation, version bump, and certification.

The future CLI is a dry-run/review/explain surface only unless a later explicit
implementation and writer gate authorizes more. It must not be described as
permission to persist, reload, export, activate, trust, validate, install,
execute, close issues, mutate releases, mutate tags, mutate assets, or certify
anything.

## 3. Current state before persistence CLI

- OSW-EXP-090 defines the future optional solver plugin manifest state
  persistence contract as design-only.
- OSW-EXP-091 defines the adjacent state export-summary contract as design-only.
- OSW-EXP-092 implements the pure persistence view-model.
- OSW-EXP-093 implements the pure in-memory persistence schema model.
- OSW-EXP-094 defines the persistence GUI contract as design-only.
- OSW-EXP-095 implements a view-model/schema-model driven PySide persistence GUI
  review surface.
- No persistence CLI exists.
- No persistence writer exists.
- No settings file, runtime state file, schema file, reload behavior, load
  behavior, save behavior, or export behavior exists for this optional solver
  plugin manifest state line.
- All current persistence surfaces remain non-writing, non-installing,
  non-validating, non-executing, and issue/release-safe.
- User-selected and plugin-provided manifests remain untrusted and
  non-validating.
- Built-ins remain authoritative by default.

Issues `#6` through `#11` remain open. Package metadata remains `0.1.5rc1`. The
public prerelease remains `v0.1.5-rc1`.

## 4. Definition of persistence CLI

The future persistence CLI is a dry-run/review/explain interface over optional
solver plugin manifest persistence readiness records supplied by the
OSW-EXP-092 persistence view-model and OSW-EXP-093 persistence schema model.

It may eventually support conceptual commands such as:

- `osw optional-solvers persistence doctor`
- `osw optional-solvers persistence explain`
- `osw optional-solvers persistence preview`
- `osw optional-solvers persistence schema`
- `osw optional-solvers persistence redaction`
- `osw optional-solvers persistence acknowledgements`
- `osw optional-solvers persistence diagnostics`
- `osw optional-solvers persistence history`
- `osw optional-solvers persistence actions`

These names are future design vocabulary only. This gate adds no command, no
parser branch, no argparse/click/Typer behavior, and no CLI source changes.

The future persistence CLI must not implement these command meanings unless a
future explicit gate defines and implements them:

- `save`
- `load`
- `reload`
- `write`
- `export`
- `bundle`
- `install`
- `validate`
- `run`
- `close-issue`

## 5. Future command vocabulary

Safe future command categories, without implementation:

- doctor/readiness: explain whether supplied persistence readiness records are
  unavailable, blocked, ready-preview-only, or future-write-required.
- explain/diagnostics: expand `OSPMG_PERSISTENCE_*` and future
  `OSPMG_PERSISTENCE_CLI_*` diagnostics into human-readable reasons.
- preview/state summary: print supplied sources, candidates, summary counts, and
  non-action flags.
- redaction review: show redacted source references and blocked unredacted path
  states.
- schema/migration review: show schema version display, support state,
  migration-required state, and future migration policy requirements.
- acknowledgement review: show required acknowledgements, satisfaction state,
  persisted display state, and expiry policy.
- stale-source/re-preview review: show stale, missing, moved, or changed source
  blockers without locating or restoring files.
- conflict/shared-stack review: show built-ins-win conflicts and shared-stack
  warnings without resolving them in favor of untrusted sources.
- unsafe-claim review: show claims that must remain blocked.
- evidence/history review: show retained historical validation evidence,
  deactivation history, and reactivation history.
- action-state review: show disabled/future-only actions and non-action flags.

These are future design vocabulary only. They do not authorize CLI
implementation, persistence implementation, file writes, settings files, runtime
state files, schema files, ProjectSchema mutation, save/load/reload behavior,
export behavior, validation execution, solver execution, issue mutation, release
mutation, tag mutation, asset mutation, or certification.

## 6. CLI output modes

Future output modes, without implementation:

- plain text
- table-like text
- JSON-like dry-run summary
- diagnostics-only output
- redaction report
- non-action flag report

Rules:

- no output file is written
- JSON-like output is stdout-only unless a future writer/export gate says
  otherwise
- stdout output is not a reloadable bundle
- stdout output is not validation evidence
- stdout output is not a settings file
- stdout output is not a runtime state file
- stdout output is not a schema file
- stdout output is not a ProjectSchema mutation

## 7. CLI entry points

Future entry points, without implementation:

- the existing `osw` CLI
- optional solver doctor/list/explain surfaces if a later gate extends them
- a future experimental subcommand group
- a future plugin manifest state group

This gate adds no command. This gate changes no parser. This gate adds no
click/argparse/Typer behavior. This gate changes no CLI source.

## 8. User flow states

The future persistence CLI should describe these states:

- no state supplied / persistence unavailable
- no explicit persistence request
- candidate/source review
- acknowledgement review
- redaction review required
- unredacted path blocked
- stale-source/re-preview required
- schema version missing
- schema migration required
- conflict/shared-stack blocked
- unsafe claim blocked
- ready preview only
- future write required
- schema review required
- persistence error

`ready preview only` means supplied in-memory view-model and schema-model records
can be reviewed. It does not mean persistence implementation exists, a file was
written, settings were created, runtime state was created, ProjectSchema was
mutated, state was loaded, state was reloaded, an export was produced, trust was
restored, a candidate was activated, validation passed, validation failed, an
issue may close, a release changed, a tag changed, an asset changed, or
certification exists.

## 9. Dry-run and non-action model

Dry-run is the default future posture for persistence CLI.

Dry-run does not save. Dry-run does not load. Dry-run does not reload. Dry-run
does not write files. Dry-run does not write settings. Dry-run does not create
runtime state files. Dry-run does not create schema files. Dry-run does not
mutate ProjectSchema. Dry-run does not run discovery. Dry-run does not run
validation. Dry-run does not execute solvers. Dry-run does not install
dependencies. Dry-run does not uninstall dependencies. Dry-run does not uninstall
solvers. Dry-run does not import plugin packages. Dry-run does not scan
directories. Dry-run does not fetch network manifests. Dry-run does not close
issues. Dry-run does not mutate releases. Dry-run does not mutate tags. Dry-run
does not mutate assets. Dry-run does not bump versions. Dry-run does not claim
validation success, validation failure, issue closure, bundled solvers, or
certification.

## 10. Summary output section

The future summary output should show these fields:

- state scope
- schema version display
- candidate count
- source count
- acknowledgement count
- acknowledgement required count
- diagnostic count
- conflict count
- unsafe claim count
- stale source count
- redaction required count
- migration required count
- evidence retained
- history retained
- persistence ready count
- persistence blocked count
- persistence performed false
- file write performed false
- settings file created false
- runtime state file created false
- ProjectSchema mutation performed false
- discovery execution performed false
- validation execution performed false
- solver execution performed false
- issue mutation performed false
- release mutation performed false
- tag mutation performed false
- asset mutation performed false
- version bump performed false
- validation-pass claim false
- validation-fail claim false
- certification claim false

The summary should keep `persistence_performed=false`,
`file_write_performed=false`, `settings_file_created=false`,
`runtime_state_file_created=false`, `project_schema_mutation_performed=false`,
`discovery_execution_performed=false`, `validation_execution_performed=false`,
`solver_execution_performed=false`, `issue_mutation_performed=false`,
`release_mutation_performed=false`, `tag_mutation_performed=false`,
`asset_mutation_performed=false`, `version_bump_performed=false`,
`validation_pass_claimed=false`, `validation_fail_claimed=false`, and
`certification_claimed=false`.

## 11. Candidate/source output

Candidate and source output should include:

- stack id
- display name
- source id
- source type
- source label
- source reference display
- trust label
- activation state
- deactivation state
- reactivation state
- discovery-refresh state
- persistence state
- readiness
- blockers and warnings
- diagnostics
- stale source state
- re-preview required
- redaction status
- built-in relationship
- shared-stack indicators
- evidence/history state

The CLI must not inspect paths, restore files, rewrite files, delete files,
fetch network manifests, import plugin packages, or scan directories to make
candidate/source output appear more complete.

## 12. Acknowledgement output and expiry policy

Acknowledgement output should show:

- acknowledgement id
- label
- required state
- satisfied state
- persisted-display state
- expiry on reload
- expiry on source change
- expiry on schema change
- expiry on unsafe claims
- blocking reason

The acknowledgement output should include:

- `persistence_not_validation`
- `persistence_not_trust_restoration`
- `persistence_not_install`
- `persistence_no_solver_execution`
- `persistence_not_issue_closure`
- `persistence_not_release_mutation`
- `local_path_redaction_reviewed`
- `persisted_acknowledgements_may_expire`
- `stale_source_requires_repreview`
- `untrusted_source_remains_untrusted`
- `activation_review_required_after_reload`
- `no_discovery_execution`
- `no_plugin_package_import`
- `trust_label_not_certification`

Persisted acknowledgement expiry policy:

- expires on reload
- expires on source change
- expires on schema change
- expires on unsafe claims
- expires when a future gate adds a new trust, activation, migration,
  redaction, validation, issue, release, or certification boundary

A persisted acknowledgement is a record that a warning was shown. It is not
validation evidence, trust restoration, dependency installation permission,
solver execution permission, issue closure evidence, release mutation evidence,
or certification.

## 13. Redaction/privacy output

Redaction/privacy output should show:

- redaction policy id
- whether redaction is required
- whether raw absolute paths are blocked
- whether an unredacted path is blocked
- whether a secret-like reference is blocked
- safe source reference display
- whether local path redaction was reviewed
- whether review remains required

Raw absolute paths are not shown by default. Home-directory paths, environment
variables, tokens, API keys, unrestricted URLs, solver install paths, and plugin
install paths remain blocked unless a future explicit privacy gate defines a
review policy.

The CLI must not add clipboard behavior, open-output-folder behavior, file
writes, save command behavior, export behavior, or state bundle behavior to
reveal or move source references.

## 14. Schema/migration output

Schema/migration output should show:

- schema version display
- schema version present
- schema version supported
- schema migration required
- migration status
- migration notes
- migration blocker state
- schema review required state
- whether this gate creates a schema file: false

Missing schema version and unsupported schema version states are blockers or
review-required states. Migration review is not migration execution. This gate
creates no schema file, writes no runtime state file, creates no settings file,
and mutates no ProjectSchema field.

## 15. Stale-source/re-preview output

Stale-source/re-preview output should show:

- stale source state
- missing source marker
- moved source marker
- changed source marker
- re-preview required flag
- safe source reference display
- not silently trusted text
- no file IO text
- future policy required text

A stale, missing, moved, or changed source must require re-preview before future
use. The CLI must not locate the file, restore the file, rewrite the file,
delete the file, fetch it from a network location, import a plugin package, scan
a directory, trust it, activate it, or run discovery.

## 16. Conflict/shared-stack output

Conflict/shared-stack output should show:

- stack id
- built-in source
- user/plugin source
- active source state
- deactivated source state
- reactivation source state
- discovery-refresh source state
- persistence state
- built-ins-win default
- conflict visible
- required future policy

Built-ins remain authoritative by default. Persisted or previewed user/plugin
state must not silently override built-ins, hide duplicate stack ids, or convert
a user/plugin manifest into a trusted source.

## 17. Unsafe-claim output

Unsafe-claim output should show and block claims such as:

- bundled solver binaries
- automatic dependency installation
- automatic dependency uninstall
- solver uninstall readiness
- validation success
- validation failure reversal
- issue closure readiness
- release mutation readiness
- tag mutation readiness
- asset mutation readiness
- industrial certification
- proprietary solver parity
- full OpenFOAM, ANSYS, MATLAB, Abaqus, or other commercial-tool replacement
- solver execution during persistence, reload, discovery, validation, or export

Unsafe claims are blocked display state. The CLI must not accept them as truth,
turn them into validation-pass claims, turn them into validation-fail claims, or
route them to issue/release/tag/asset actions.

## 18. Evidence/history output

Evidence/history output should show:

- deactivation history retained
- reactivation history retained
- historical validation evidence retained
- skipped-missing remains skipped-missing
- issue closure implied false
- validation success claimed false
- validation failure claimed false
- evidence deleted or rewritten false

Persistence CLI is not validation evidence. It must preserve historical evidence
and limitations as supplied data. It must not delete evidence, rewrite evidence,
reverse failures, promote skipped-missing evidence, or claim live optional
validation completion.

## 19. Trust/provenance behavior

Trust/provenance output should show:

- source type
- trust label
- source label
- source reference display
- activation/deactivation/reactivation/discovery-refresh/persistence state
- untrusted-by-default text for user-selected and plugin-provided manifests
- built-in authoritative-by-default text for built-ins
- trust label is not certification

The CLI must keep user-selected and plugin-provided manifests untrusted by
default. A trust label is not certification. Persisted state is not trust
restoration. Reloaded state is not automatic activation.

## 20. Action-state output

Action-state output should distinguish:

- current dry-run review rows
- future-only actions
- unavailable unsafe actions
- blocked actions
- disabled actions

All save/settings/ProjectSchema/reload/export actions are disabled or
future-only. All discovery/validation/install/uninstall/solver/issue/release
actions are disabled or future-only. No file write callback is invoked. No
settings callback is invoked. No ProjectSchema mutation callback is invoked. No
reload/export callback is invoked. No clipboard callback is invoked. No
open-output-folder callback is invoked.

## 21. Non-action flags

The CLI should print false non-action flags from the view-model/schema model and
block any truthy value:

- persistence performed false
- file write performed false
- settings file created false
- runtime state file created false
- ProjectSchema mutation performed false
- GUI behavior added false
- CLI behavior added false
- reload behavior added false
- export behavior added false
- automatic activation performed false
- trust restoration performed false
- file restoration performed false
- file rewrite performed false
- file deletion performed false
- dependency installation performed false
- dependency uninstall performed false
- solver uninstall performed false
- plugin package import performed false
- directory scan performed false
- network fetch performed false
- discovery execution performed false
- validation execution performed false
- solver execution performed false
- issue mutation performed false
- release mutation performed false
- tag mutation performed false
- asset mutation performed false
- version bump performed false
- validation-pass claim false
- validation-fail claim false
- certification claimed false

## 22. Exit-code policy

Future exit-code policy should be careful and non-validating:

- `0`: dry-run review completed and no supplied readiness blocker exists.
- `1`: persistence readiness is blocked, malformed, unavailable, stale,
  unacknowledged, unredacted, migration-required, conflicted, or unsafe.
- `2`: optional strict mode found rejected input or conflicts, if a future gate
  defines such a mode.
- `>2`: CLI invocation error or unexpected internal error.

Exit code `0` is not validation success. Exit code `1` is not validation
failure. No exit code closes issues, mutates releases, mutates tags, mutates
assets, certifies optional solvers, or proves installed-only validation.

## 23. Diagnostics reserved

Future persistence CLI diagnostic code names are reserved only:

- `OSPMG_PERSISTENCE_CLI_NOT_IMPLEMENTED`
- `OSPMG_PERSISTENCE_CLI_STATE_UNAVAILABLE`
- `OSPMG_PERSISTENCE_CLI_EXPLICIT_REQUEST_REQUIRED`
- `OSPMG_PERSISTENCE_CLI_ACK_REQUIRED`
- `OSPMG_PERSISTENCE_CLI_NOT_VALIDATION`
- `OSPMG_PERSISTENCE_CLI_NOT_TRUST_RESTORE`
- `OSPMG_PERSISTENCE_CLI_NO_INSTALL`
- `OSPMG_PERSISTENCE_CLI_NO_SOLVER_EXECUTION`
- `OSPMG_PERSISTENCE_CLI_NOT_ISSUE_CLOSURE`
- `OSPMG_PERSISTENCE_CLI_NOT_RELEASE_MUTATION`
- `OSPMG_PERSISTENCE_CLI_REDACTION_REQUIRED`
- `OSPMG_PERSISTENCE_CLI_UNREDACTED_PATH_BLOCKED`
- `OSPMG_PERSISTENCE_CLI_STALE_SOURCE_REPREVIEW_REQUIRED`
- `OSPMG_PERSISTENCE_CLI_SCHEMA_VERSION_REQUIRED`
- `OSPMG_PERSISTENCE_CLI_SCHEMA_MIGRATION_REQUIRED`
- `OSPMG_PERSISTENCE_CLI_UNTRUSTED_SOURCE`
- `OSPMG_PERSISTENCE_CLI_CONFLICT_BLOCKED`
- `OSPMG_PERSISTENCE_CLI_UNSAFE_CLAIM`
- `OSPMG_PERSISTENCE_CLI_EVIDENCE_RETAINED`
- `OSPMG_PERSISTENCE_CLI_HISTORY_RETAINED`
- `OSPMG_PERSISTENCE_CLI_NO_DISCOVERY_EXECUTION`
- `OSPMG_PERSISTENCE_CLI_NO_PLUGIN_IMPORT`
- `OSPMG_PERSISTENCE_CLI_FUTURE_GATE`

These names are reservations only. This gate adds no diagnostic emitter,
runtime constant, CLI parser, CLI handler, source file, command callback, writer,
or action wiring. A future CLI may also display the OSW-EXP-092/093
`OSPMG_PERSISTENCE_*` diagnostics already supplied by the persistence view-model
and schema model.

## 24. Relationship to OSW-EXP-092 persistence view-model

OSW-EXP-092 implements the pure
`OptionalSolverPluginManifestPersistenceViewModel`. The future CLI should consume
its supplied rows:

- summary
- candidate rows
- source rows
- acknowledgement rows
- diagnostic rows
- redaction/privacy rows
- schema/migration rows
- stale-source/re-preview rows
- conflict/shared-stack rows
- unsafe-claim rows
- evidence/history rows
- trust/provenance badges
- action states
- guidance text

The CLI must not mutate the view-model, add CLI command behavior to it, add file
IO to it, make it run discovery, make it run validation, make it execute solvers,
or make it install/uninstall dependencies.

## 25. Relationship to OSW-EXP-093 schema model

OSW-EXP-093 implements the pure in-memory
`OptionalSolverPluginManifestPersistenceSchemaModel`. The future CLI may print
its versioned records, redaction policy, migration record, validation summary,
non-action flags, and mapping-validation diagnostics.

The CLI must not turn the schema model into a writer. It must not create schema
files, runtime state files, settings files, reloadable bundles, exports, or
ProjectSchema records.

## 26. Relationship to OSW-EXP-095 persistence GUI

OSW-EXP-095 implements `OptionalSolverPluginManifestPersistencePanel`, a PySide
review surface over the same supplied view-model and optional schema-model
records. The CLI should share the same safety vocabulary and record boundaries
but remain headless, stdout-oriented, and dry-run/review/explain oriented.

The CLI design does not alter the GUI panel, add GUI behavior, add file dialogs,
add save dialogs, add clipboard behavior, add open-output-folder behavior, or
change widget-local acknowledgement behavior.

## 27. Relationship to ProjectSchema

No ProjectSchema mutation occurs in this gate.

The persistence CLI should treat ProjectSchema integration as future-gated. A
future project-local state model would require a separate design and
implementation gate with schema, migration, preview, rollback, docs, and focused
tests. Project validation must not treat persisted optional solver manifest
state or persistence CLI output as solver validation evidence.

## 28. Relationship to activation/deactivation/reactivation/discovery-refresh

The persistence CLI may review state that originated from activation,
deactivation, reactivation, and discovery-refresh view-models, but it must not
mutate those sources.

- Activation state is not automatic activation.
- Deactivation state is not file deletion, dependency uninstall, or solver
  uninstall.
- Reactivation state is not trust restoration, automatic activation, file
  restoration, file rewrite, or file deletion.
- Discovery-refresh state is not discovery execution, passive discovery behavior
  change, validation execution, solver execution, or dependency installation.

## 29. Relationship to GUI, CLI, reload, export, and reports

This gate adds no GUI behavior, no CLI implementation, no reload behavior, no
export behavior, no clipboard behavior, no open-output-folder behavior, no file
dialog, and no save dialog.

Future preferences/settings, report, export-summary, CLI, reload, and writer
surfaces require separate gates. Export summaries remain non-reloadable unless a
future state-bundle gate defines otherwise. A report/export surface is not
validation evidence.

OSW-EXP-098 designs export-summary GUI semantics only. It does not add CLI
behavior, persistence CLI behavior, GUI implementation, file export, file writes,
export file creation, report file creation, clipboard behavior, report
attachment, open-output-folder behavior, reloadable bundle creation, runtime
persistence behavior, settings files, runtime state files, schema files,
ProjectSchema mutation, reload behavior, source mutation, automatic activation,
trust restoration, file restore/rewrite/delete behavior, dependency
install/uninstall behavior, solver uninstall behavior, plugin package import,
directory scan, network fetch, discovery execution, validation execution, solver
execution, issue/release/tag/asset mutation, version bump, validation-pass/fail
claim, issue-closure claim, bundled-solver claim, or certification claim.

## 30. Relationship to live optional validation issues

Issues `#6` through `#11` remain open. The persistence CLI is not live optional
validation. Persisted state is not live optional validation. Persistence preview
is not validation success and not validation failure. Skipped-missing remains
skipped-missing. Prepared-machine validation remains a separate gate.

The CLI must not mark issues ready to close, mutate issue state, mutate release
state, edit tags, edit assets, or claim public validation evidence.

## 31. Failure handling

The future CLI should report failure states without side effects:

- no state supplied
- unsupported view-model shape
- unsupported schema version
- missing schema version
- migration required
- redaction required
- unredacted path blocked
- stale source requires re-preview
- conflict/shared-stack blocked
- unsafe claim blocked
- acknowledgement missing
- non-action flag violation
- persistence error supplied by the model

Failure handling must be read-only. It must not attempt recovery by writing
files, restoring files, rewriting files, deleting files, scanning directories,
fetching network manifests, importing plugin packages, running discovery,
running validation, executing solvers, installing dependencies, uninstalling
dependencies, uninstalling solvers, closing issues, or mutating releases.

## 32. Implementation test plan for a later gate

A later CLI implementation gate should add tests that verify:

- no state supplied prints persistence unavailable
- no explicit persistence request prints unavailable/no-request state
- candidate/source rows print from injected view-model/schema-model data
- acknowledgement rows and expiry policy print
- redaction/privacy rows print
- unredacted paths are blocked
- schema/migration rows print
- stale-source/re-preview rows print
- conflict/shared-stack rows print
- unsafe-claim rows print
- evidence/history rows print
- trust/provenance output says trust label is not certification
- action states print disabled/future-only
- non-action flags print false
- JSON-like output is stdout-only
- exit codes do not imply validation success or validation failure
- save/settings/ProjectSchema/load/reload/export commands are absent or
  disabled/future-only
- discovery/validation/install/uninstall/solver/issue/release actions are absent
  or disabled/future-only
- no file write callback is invoked
- no settings callback is invoked
- no ProjectSchema mutation callback is invoked
- no reload/export callback is invoked
- no clipboard callback is invoked
- no open-output-folder callback is invoked

These are future tests. This gate adds only focused docs tests for this design
document and related guardrail/risk/checklist/validation references.

## 33. Non-actions

This gate explicitly does not:

- implement CLI code
- implement persistence
- write files
- create settings files
- create runtime state files
- create schema files
- mutate ProjectSchema
- implement save command
- implement load command
- implement reload behavior
- implement export behavior
- add clipboard behavior
- add open-output-folder behavior
- implement GUI behavior
- alter activation view-model or GUI source
- alter deactivation view-model or GUI source
- alter reactivation view-model or GUI source
- alter discovery-refresh view-model or GUI source
- alter persistence view-model, schema model, or GUI source
- restore, rewrite, or delete manifest files
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
- create, move, delete, or push tags
- build or upload assets
- bump versions
- claim validation success
- claim validation failure
- claim issue closure
- claim bundled solvers
- claim certification

No runtime source, GUI source, view-model source, schema-model source, CLI
source, loader source, discovery source, plugin manager source, ProjectSchema
source, persistence writer, settings file, runtime state file, schema file,
export file, reloadable bundle, release asset, tag, issue, release, version
metadata, or solver/runtime artifact is changed by this design gate.

## 34. Future gates

Proposed follow-up gates, not implemented here:

- `OSW-EXP-097_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_VIEWMODEL`
- `OSW-EXP-098_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_GUI_DESIGN`
- `OSW-EXP-099_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_GUI_IMPLEMENTATION`
- `OSW-EXP-100_OPTIONAL_SOLVER_PLUGIN_MANIFEST_STATE_WRITER_DESIGN`
- `OSW-EXP-101_OPTIONAL_SOLVER_PLUGIN_MANIFEST_STATE_WRITER_VIEWMODEL_OR_SCHEMA_EXTENSION`
- `OSW-EXP-102_OPTIONAL_SOLVER_PLUGIN_MANIFEST_STATE_WRITER_IMPLEMENTATION`
- `OSW-EXP-103_OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_CLI_IMPLEMENTATION`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` if a prepared
  machine is available

Numbering note: this follows the established optional solver plugin manifest
sequence. OSW-EXP-090 designed persistence, OSW-EXP-091 designed export
summaries, OSW-EXP-092 implemented the persistence view-model, OSW-EXP-093
implemented the persistence schema model, OSW-EXP-094 designed the persistence
GUI, OSW-EXP-095 implemented the persistence GUI, and OSW-EXP-096 designs the
future persistence CLI. If the repo later reserves different numbering, follow
the latest repository convention while preserving these safety boundaries.
