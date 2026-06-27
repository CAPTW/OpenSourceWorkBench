# Optional solver plugin manifest persistence GUI design

## 1. Status

Design-only.

No runtime behavior is added in this gate. No GUI implementation is added in
this gate. No persistence implementation is added in this gate. This document
defines a future PySide persistence GUI safety contract and UX model only.

Status boundaries:

- no runtime behavior
- no GUI implementation
- no persistence implementation
- no file writes
- no settings file creation
- no runtime state file creation
- no schema file creation
- no ProjectSchema mutation
- no file dialog
- no save dialog
- no reload behavior
- no export behavior
- no clipboard behavior
- no open-output-folder behavior
- no CLI behavior
- no activation/deactivation/reactivation/discovery-refresh source mutation
- no automatic activation
- no trust restoration
- no file restoration
- no file rewrite
- no file deletion
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

Define future PySide persistence GUI semantics for optional solver plugin
manifest UX state.

The persistence GUI design preserves the explicit-import, activation,
deactivation, reactivation, discovery-refresh, persistence view-model, and
persistence schema-model boundaries. It makes the persistence GUI distinct from
file writes, settings file creation, runtime state file creation, schema file
creation, ProjectSchema mutation, reload behavior, export behavior, clipboard
behavior, open-output-folder behavior, validation, trust restoration, dependency
installation, dependency uninstall, solver uninstall, solver execution, issue
closure, release mutation, tag mutation, asset mutation, version bump, and
certification.

The future GUI is a review/control surface only. It must not be described as
permission to persist anything until a later implementation gate authorizes a
specific writer and its tests.

## 3. Current state before persistence GUI

- OSW-EXP-090 defines the future optional solver plugin manifest state
  persistence contract as design-only.
- OSW-EXP-091 defines the adjacent state export-summary contract as design-only.
- OSW-EXP-092 implements the pure persistence view-model.
- OSW-EXP-093 implements the pure in-memory persistence schema model.
- Activation, deactivation, reactivation, and discovery-refresh GUI surfaces
  exist as view-model-driven review panels.
- No persistence GUI exists.
- No persistence writer exists.
- No settings file, runtime state file, schema file, reload behavior, or export
  behavior exists for this optional solver plugin manifest state line.
- All current surfaces remain non-installing, non-validating, non-executing, and
  issue/release-safe.
- User/plugin manifests remain untrusted and non-validating.
- Built-ins remain authoritative by default.

Issues `#6` through `#11` remain open. Package metadata remains `0.1.5rc1`. The
public prerelease remains `v0.1.5-rc1`.

## 4. Definition of persistence GUI

The future persistence GUI is a view-model/schema-model driven review surface
for future optional solver plugin manifest persistence readiness.

It may eventually render:

- persistence summary
- persistence candidate rows
- manifest source/provenance rows
- acknowledgement rows
- diagnostic rows
- redaction/privacy review rows
- schema/migration rows
- stale-source/re-preview rows
- conflict/shared-stack rows
- unsafe-claim rows
- evidence/history retention rows
- trust/provenance badges
- disabled/future action states
- non-action flags
- safety guidance

It must not:

- write files
- create settings files
- create runtime state files
- create schema files
- mutate ProjectSchema
- reload state
- export summaries
- create reloadable bundles
- mutate candidate state
- automatically activate candidates
- restore trust
- restore, rewrite, or delete manifest files
- run discovery
- run validation
- execute solvers
- install or uninstall dependencies
- uninstall solvers
- import plugin packages
- scan directories
- fetch network manifests
- close issues
- mutate releases, tags, or assets
- bump versions
- claim validation pass, validation failure, issue closure, bundled solvers, or
  certification

## 5. User flow states

The future persistence GUI should render these states without implementing their
callbacks in this gate:

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

`ready preview only` means the supplied in-memory view-model and schema-model
records can be reviewed. It does not mean a file was written, settings were
created, ProjectSchema was mutated, state was reloaded, an export was produced,
trust was restored, a candidate was activated, validation passed, validation
failed, an issue may close, a release changed, or certification exists.

## 6. GUI entry points

Future entry points may be considered without implementing them here:

- plugin manifest review panel
- activation panel
- deactivation panel
- reactivation panel
- discovery-refresh panel
- plugin manager or health panel
- future preferences/settings area
- future report/export summary area

This gate adds no menu item, button, callback, file dialog, save dialog, widget,
toolbar action, context menu, settings page, report action, or panel source.

## 7. Rendered sections

The future persistence GUI should render these sections when supplied by the
OSW-EXP-092 persistence view-model and OSW-EXP-093 schema model:

- summary
- sources/provenance
- candidates
- acknowledgements
- diagnostics
- redaction/privacy
- schema/migration
- stale-source/re-preview
- conflicts/shared-stack
- unsafe claims
- evidence/history
- trust/provenance badges
- action states
- non-action flags
- safety guidance

Every rendered section is read-only until a later GUI implementation gate defines
specific widget behavior. No table, badge, disabled action, or guidance text
authorizes file IO.

## 8. Summary section

The summary should show future fields:

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
- reload performed false
- export performed false
- discovery/validation/solver/issue/release side effects false
- tag/asset/version side effects false
- validation-pass claim false
- validation-fail claim false
- certification claim false

The summary should keep `persistence_performed=false`,
`file_write_performed=false`, `settings_file_created=false`,
`runtime_state_file_created=false`, `project_schema_mutation_performed=false`,
`discovery_execution_performed=false`, `validation_execution_performed=false`,
`solver_execution_performed=false`, `issue_mutation_performed=false`,
`release_mutation_performed=false`, `tag_mutation_performed=false`, and
`asset_mutation_performed=false`.

## 9. Candidate/source review

Candidate and source rows should render:

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

Source references should prefer redacted display names, basenames, caller-supplied
labels, or fingerprint displays. The GUI must not inspect paths, restore files,
rewrite files, delete files, fetch network manifests, or scan directories to make
the rows appear more complete.

## 10. Acknowledgement review

The acknowledgement review should render these acknowledgement identifiers:

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
- expires when a future gate decides a new trust, activation, migration,
  redaction, or validation boundary invalidates it

A persisted acknowledgement is a record that a warning was shown. It is not
validation evidence, trust restoration, dependency installation permission,
solver execution permission, issue closure evidence, release mutation evidence,
or certification.

## 11. Redaction/privacy review

The redaction/privacy review should render:

- redaction policy id
- whether redaction is required
- whether a raw absolute path was supplied
- whether an unredacted path is blocked
- whether a secret-like reference is blocked
- the safe source reference display
- whether local path redaction was reviewed
- whether review is still required

Raw absolute paths are not shown by default. Home-directory paths, environment
variables, tokens, API keys, unrestricted URLs, and solver or plugin install
paths remain blocked unless a future privacy gate defines a review policy.

The GUI must not add clipboard behavior, open-output-folder behavior, file
dialogs, save dialogs, file writes, or export behavior to reveal or move source
references.

## 12. Schema/migration review

The schema/migration review should render:

- schema version display
- schema version present
- schema version supported
- migration required
- migration status
- migration notes
- migration blocker state
- schema review required state
- whether this gate creates a schema file: false

Missing schema version and unsupported schema version states are blockers or
review-required states. Migration review is not migration execution. This gate
creates no schema file, writes no runtime state file, creates no settings file,
and mutates no ProjectSchema field.

## 13. Stale-source/re-preview review

The stale-source/re-preview review should render:

- stale source state
- missing/moved/changed source marker
- re-preview required flag
- safe source reference display
- not silently trusted text
- no file IO text
- future policy required text

A stale, missing, moved, or changed source must require re-preview before future
use. The GUI must not locate the file, restore the file, rewrite the file, delete
the file, fetch it from a network location, import a plugin package, scan a
directory, trust it, activate it, or run discovery.

## 14. Conflict/shared-stack review

The conflict/shared-stack review should render:

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

Built-ins remain authoritative by default. Persisted state must not silently
override built-ins, hide duplicate stack ids, or convert a user/plugin manifest
into a trusted source.

## 15. Unsafe-claim review

The unsafe-claim review should render claims such as:

- bundled solver binaries
- automatic dependency installation
- automatic dependency uninstall
- validation success
- validation failure reversal
- issue closure readiness
- release mutation readiness
- industrial certification
- proprietary solver parity
- full OpenFOAM, ANSYS, MATLAB, Abaqus, or other commercial-tool replacement
- solver execution during persistence, reload, discovery, validation, or export

Unsafe claims are blocked display state. The GUI must not accept them as truth,
turn them into validation-pass claims, turn them into validation-fail claims, or
route them to issue/release actions.

## 16. Evidence/history review

The evidence/history review should render:

- deactivation history retained
- reactivation history retained
- historical validation evidence retained
- skipped-missing remains skipped-missing
- issue closure implied false
- validation success claimed false
- validation failure claimed false
- evidence deleted or rewritten false

Persistence GUI is not validation evidence. It must preserve historical evidence
and limitations as supplied data. It must not delete evidence, rewrite evidence,
reverse failures, promote skipped-missing evidence, or claim live optional
validation completion.

## 17. Trust/provenance behavior

Trust/provenance badges should show:

- source type
- trust label
- source label
- source reference display
- activation/deactivation/reactivation/discovery-refresh/persistence state
- untrusted-by-default text for user/plugin manifests
- built-in authoritative-by-default text for built-ins
- trust label is not certification

The GUI must keep user-selected and plugin-provided manifests untrusted by
default. A trust label is not certification. Persisted state is not trust
restoration. Reloaded state is not automatic activation.

## 18. Action-state model

The action-state model should distinguish:

- current display-only review rows
- widget-local acknowledgement toggles only if a future implementation injects a
  pure callback
- future-only actions
- unavailable unsafe actions
- blocked actions
- disabled actions

All save/settings/ProjectSchema/reload/export actions are disabled or
future-only. All discovery/validation/install/uninstall/solver/issue/release
actions are disabled or future-only. No file dialog callback is invoked. No save
dialog callback is invoked. No file write callback is invoked. No settings
callback is invoked. No ProjectSchema mutation callback is invoked. No
reload/export callback is invoked. No clipboard callback is invoked. No
open-output-folder callback is invoked.

## 19. Non-action flags

The GUI should render false non-action flags from the view-model/schema model and
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

## 20. Diagnostics reserved

Future persistence GUI diagnostic code names are reserved only:

- `OSPMG_PERSISTENCE_GUI_NOT_IMPLEMENTED`
- `OSPMG_PERSISTENCE_GUI_STATE_UNAVAILABLE`
- `OSPMG_PERSISTENCE_GUI_EXPLICIT_REQUEST_REQUIRED`
- `OSPMG_PERSISTENCE_GUI_ACK_REQUIRED`
- `OSPMG_PERSISTENCE_GUI_NOT_VALIDATION`
- `OSPMG_PERSISTENCE_GUI_NOT_TRUST_RESTORE`
- `OSPMG_PERSISTENCE_GUI_NO_INSTALL`
- `OSPMG_PERSISTENCE_GUI_NO_SOLVER_EXECUTION`
- `OSPMG_PERSISTENCE_GUI_NOT_ISSUE_CLOSURE`
- `OSPMG_PERSISTENCE_GUI_NOT_RELEASE_MUTATION`
- `OSPMG_PERSISTENCE_GUI_REDACTION_REQUIRED`
- `OSPMG_PERSISTENCE_GUI_UNREDACTED_PATH_BLOCKED`
- `OSPMG_PERSISTENCE_GUI_STALE_SOURCE_REPREVIEW_REQUIRED`
- `OSPMG_PERSISTENCE_GUI_SCHEMA_VERSION_REQUIRED`
- `OSPMG_PERSISTENCE_GUI_SCHEMA_MIGRATION_REQUIRED`
- `OSPMG_PERSISTENCE_GUI_UNTRUSTED_SOURCE`
- `OSPMG_PERSISTENCE_GUI_CONFLICT_BLOCKED`
- `OSPMG_PERSISTENCE_GUI_UNSAFE_CLAIM`
- `OSPMG_PERSISTENCE_GUI_EVIDENCE_RETAINED`
- `OSPMG_PERSISTENCE_GUI_HISTORY_RETAINED`
- `OSPMG_PERSISTENCE_GUI_NO_DISCOVERY_EXECUTION`
- `OSPMG_PERSISTENCE_GUI_NO_PLUGIN_IMPORT`
- `OSPMG_PERSISTENCE_GUI_FUTURE_GATE`

These names are reservations only. This gate adds no diagnostic emitter, runtime
constant, PySide handler, source file, GUI widget, callback, or action wiring.
The GUI may also display the OSW-EXP-092/093 `OSPMG_PERSISTENCE_*` diagnostics
already supplied by the persistence view-model and schema model.

## 21. Relationship to OSW-EXP-092 persistence view-model

OSW-EXP-092 implements the pure
`OptionalSolverPluginManifestPersistenceViewModel`. The future GUI should consume
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

The GUI must not mutate the view-model, add PySide imports to it, add file IO to
it, make it run discovery, make it run validation, make it execute solvers, or
make it install/uninstall dependencies.

## 22. Relationship to OSW-EXP-093 schema model

OSW-EXP-093 implements the pure in-memory
`OptionalSolverPluginManifestPersistenceSchemaModel`. The future GUI may render
its versioned records, redaction policy, migration record, validation summary,
non-action flags, and mapping-validation diagnostics.

The GUI must not turn the schema model into a writer. It must not create schema
files, runtime state files, settings files, reloadable bundles, exports, or
ProjectSchema records.

## 23. Relationship to ProjectSchema

No ProjectSchema mutation occurs in this gate.

The persistence GUI should treat ProjectSchema integration as future-gated. A
future project-local state model would require a separate design and
implementation gate with schema, migration, preview, rollback, docs, and focused
tests. Project validation must not treat persisted optional solver manifest state
as solver validation evidence.

## 24. Relationship to activation/deactivation/reactivation/discovery-refresh

The persistence GUI may review state that originated from activation,
deactivation, reactivation, and discovery-refresh view-models, but it must not
mutate those sources.

- Activation state is not automatic activation.
- Deactivation state is not file deletion, dependency uninstall, or solver
  uninstall.
- Reactivation state is not trust restoration, automatic activation, file
  restoration, file rewrite, or file deletion.
- Discovery-refresh state is not discovery execution, passive discovery behavior
  change, validation execution, solver execution, or dependency installation.

Existing activation/deactivation/reactivation/discovery-refresh GUI tests should
continue to pass unchanged when a future persistence GUI implementation is added.

## 25. Relationship to GUI, CLI, reload, export, and reports

This gate adds no GUI source, no CLI behavior, no reload behavior, no export
behavior, no clipboard behavior, no open-output-folder behavior, no file dialog,
and no save dialog.

Future preferences/settings, report, export-summary, CLI, reload, and writer
surfaces require separate gates. Export summaries remain non-reloadable unless a
future state-bundle gate defines otherwise. A report/export surface is not
validation evidence.

## 26. Relationship to live optional validation issues

Issues `#6` through `#11` remain open. The persistence GUI is not live optional
validation. Persisted state is not live optional validation. Persistence preview
is not validation success and not validation failure. Skipped-missing remains
skipped-missing. Prepared-machine validation remains a separate gate.

The GUI must not mark issues ready to close, mutate issue state, mutate release
state, edit tags, edit assets, or claim public validation evidence.

## 27. Failure handling

The future GUI should render failure states without side effects:

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
fetching network manifests, importing plugin packages, running discovery, running
validation, executing solvers, installing dependencies, uninstalling dependencies,
uninstalling solvers, closing issues, or mutating releases.

## 28. Accessibility and UX guidance

The future GUI should keep reviewable state clear without using certification or
validation language:

- every disabled/future action should explain why it is disabled
- redaction warnings should be visible near source references
- acknowledgement expiry should be visible near acknowledgements
- stale-source/re-preview blockers should be visible near source rows
- schema/migration blockers should be visible near schema rows
- unsafe claims should be visibly blocked
- trust labels should always include "not certification"
- skipped-missing and open issue status should stay visible

The GUI should be dense and review-oriented, consistent with the existing
optional solver panels. It should avoid marketing language, installer language,
marketplace language, validation-pass language, and certification language.

## 29. Future implementation test plan

A later implementation gate should add tests that verify:

- no state supplied renders persistence unavailable
- no explicit persistence request renders unavailable/no-request state
- candidate/source rows render from injected view-model/schema-model data
- acknowledgement rows and expiry policy render
- redaction/privacy rows render
- unredacted paths are blocked
- schema/migration rows render
- stale-source/re-preview rows render
- conflict/shared-stack rows render
- unsafe-claim rows render
- evidence/history rows render
- trust/provenance badges render and trust label is not certification
- action states render disabled/future-only
- non-action flags render false
- save/settings/ProjectSchema/reload/export actions are disabled or future-only
- discovery/validation/install/uninstall/solver/issue/release actions are disabled
  or future-only
- no file dialog callback is invoked
- no save dialog callback is invoked
- no file write callback is invoked
- no settings callback is invoked
- no ProjectSchema mutation callback is invoked
- no reload/export callback is invoked
- no clipboard callback is invoked
- no open-output-folder callback is invoked
- existing activation/deactivation/reactivation/discovery-refresh GUI tests still
  pass

These are future tests. This gate adds only focused docs tests for this design
document and meta-doc references.

## 30. Non-actions

This gate explicitly does not:

- implement GUI code
- implement persistence
- write files
- create settings files
- create runtime state files
- create schema files
- mutate ProjectSchema
- add file dialogs
- add save dialogs
- implement reload behavior
- implement export behavior
- add clipboard behavior
- add open-output-folder behavior
- implement CLI behavior
- alter activation view-model or GUI source
- alter deactivation view-model or GUI source
- alter reactivation view-model or GUI source
- alter discovery-refresh view-model or GUI source
- alter persistence view-model or schema model source
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

No runtime source, GUI source, view-model source, CLI source, loader source,
discovery source, plugin manager source, ProjectSchema source, persistence writer,
settings file, runtime state file, schema file, export file, reloadable bundle,
release asset, tag, issue, release, version metadata, or solver/runtime artifact
is changed by this design gate.

## 31. Future gates

Proposed follow-up gates, not implemented here:

- `OSW-EXP-095_OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_GUI_IMPLEMENTATION`
- `OSW-EXP-096_OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_CLI_DESIGN`
- `OSW-EXP-097_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_VIEWMODEL`
- `OSW-EXP-098_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_GUI_DESIGN`
- `OSW-EXP-099_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_GUI_IMPLEMENTATION`
- `OSW-EXP-100_OPTIONAL_SOLVER_PLUGIN_MANIFEST_STATE_WRITER_DESIGN`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` if a prepared
  machine is available

Numbering note: this follows the established optional solver plugin manifest
sequence. OSW-EXP-090 designed persistence, OSW-EXP-091 designed export
summaries, OSW-EXP-092 implemented the persistence view-model, OSW-EXP-093
implemented the persistence schema model, and OSW-EXP-094 designs the future
persistence GUI. If the repo later reserves different numbering, follow the
latest repository convention while preserving these safety boundaries.
