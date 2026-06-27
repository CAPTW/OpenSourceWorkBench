# Optional solver plugin manifest persistence view-model

## Status

Implemented as a pure experimental view-model for OSW-EXP-092.

This gate adds deterministic data records only. It adds no runtime persistence
behavior, no persistence implementation, no file writes, no settings file
creation, no ProjectSchema mutation, no GUI persistence behavior, no CLI
persistence behavior, no reload behavior, no export behavior, no automatic
activation, no trust restoration, no file restoration, no file rewrite, no file
deletion, no dependency installation, no dependency uninstall, no solver
uninstall, no plugin package import, no directory scan, no network fetch, no
discovery execution, no validation execution, no solver execution, no issue
mutation, no issue closure, no release mutation, no tag mutation, no asset
mutation, no version bump, no validation-pass claim, no validation-fail claim,
and no certification claim.

## Purpose

The persistence view-model turns already-supplied optional solver plugin manifest
UX state into inspectable readiness, acknowledgement, diagnostic, redaction,
schema, stale-source, conflict, unsafe-claim, evidence/history, trust, and action
rows.

It is intended for future GUI/CLI/reload/export gates to render the same safety
contract without making this gate responsible for saving state.

## Public module/class names

- Module:
  `osw.experimental.optional_solvers.plugin_manifest_persistence_viewmodel`
- Main class:
  `OptionalSolverPluginManifestPersistenceViewModel`
- Builder:
  `build_optional_solver_plugin_manifest_persistence_viewmodel`
- Summary helper:
  `summarize_optional_solver_plugin_manifest_persistence_viewmodel`
- Render helper:
  `render_optional_solver_plugin_manifest_persistence_summary`
- Explanation helper:
  `explain_optional_solver_plugin_manifest_persistence_viewmodel`
- Redaction helper:
  `redact_optional_solver_plugin_manifest_persistence_source_reference`

The package-level experimental optional-solver namespace exports the public
records and helper functions for this gate.

## Input boundary

All inputs are caller-supplied records:

- persistence candidates
- source/provenance rows
- acknowledgement maps
- persisted-acknowledgement display maps
- schema/migration metadata
- conflict/shared-stack rows
- unsafe-claim rows
- historical evidence/history rows

The view-model does not read files, parse JSON from paths, inspect path
existence, scan directories, import plugin packages, run discovery, run
validation, execute solvers, install or uninstall dependencies, mutate issues,
or mutate releases.

## Persistence state machine

The view-model exposes these persistence states:

- `persistence_unavailable`
- `persistence_requested`
- `persistence_blocked`
- `persistence_ready_preview`
- `persistence_future_write_required`
- `persistence_schema_review_required`
- `persistence_redaction_review_required`
- `persistence_stale_source_repreview_required`
- `persistence_error`

These are display states only. They do not create persisted state and do not
authorize writes.

## Readiness rules

Readiness values are:

- `unavailable_no_state`
- `unavailable_no_explicit_request`
- `blocked_acknowledgement`
- `blocked_redaction_review`
- `blocked_unredacted_path`
- `blocked_stale_source_repreview`
- `blocked_schema_version`
- `blocked_schema_migration`
- `blocked_conflict`
- `blocked_shared_stack_warning`
- `blocked_unsafe_claim`
- `ready_preview_only`
- `future_write_required`
- `schema_review_required`
- `error`

`ready_preview_only` means the supplied in-memory records are coherent enough to
preview. It does not mean persistence implementation exists. It does not mean a
state file, settings file, ProjectSchema update, reloadable bundle, activation,
trust restoration, export, issue closure, release mutation, validation pass,
validation fail, or certification claim occurred.

## Acknowledgement model

The required acknowledgement identifiers are:

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

Acknowledgement rows show whether each warning was satisfied, whether it came
from supplied persisted acknowledgement display state, and whether it expires on
reload, source change, schema change, or unsafe claims.

Persisted acknowledgements may expire. A reloaded acknowledgement would be a
record that a warning was shown, not permission to activate, trust, validate,
install, execute, close issues, mutate releases, or certify anything.
A trust label is not certification.

## Diagnostic vocabulary

The view-model reserves and emits `OSPMG_PERSISTENCE_*` diagnostics:

- `OSPMG_PERSISTENCE_NOT_IMPLEMENTED`
- `OSPMG_PERSISTENCE_ACK_REQUIRED`
- `OSPMG_PERSISTENCE_NOT_VALIDATION`
- `OSPMG_PERSISTENCE_NOT_TRUST_RESTORE`
- `OSPMG_PERSISTENCE_NO_INSTALL`
- `OSPMG_PERSISTENCE_NO_SOLVER_EXECUTION`
- `OSPMG_PERSISTENCE_NOT_ISSUE_CLOSURE`
- `OSPMG_PERSISTENCE_NOT_RELEASE_MUTATION`
- `OSPMG_PERSISTENCE_REDACTION_REQUIRED`
- `OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED`
- `OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED`
- `OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED`
- `OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED`
- `OSPMG_PERSISTENCE_UNTRUSTED_SOURCE`
- `OSPMG_PERSISTENCE_CONFLICT_BLOCKED`
- `OSPMG_PERSISTENCE_UNSAFE_CLAIM`
- `OSPMG_PERSISTENCE_EVIDENCE_RETAINED`
- `OSPMG_PERSISTENCE_HISTORY_RETAINED`
- `OSPMG_PERSISTENCE_NO_DISCOVERY_EXECUTION`
- `OSPMG_PERSISTENCE_NO_PLUGIN_IMPORT`
- `OSPMG_PERSISTENCE_FUTURE_GATE`

Diagnostics are explanatory. They do not trigger runtime behavior.

## Rendered/view-model sections

The complete view-model contains:

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
- disabled/future action rows
- safety and guidance text
- blocked-transition text

The render helper returns an in-memory, redacted, JSON-ready dictionary. It writes
nothing and creates no export file.

## Redaction/privacy policy

Source references are redacted by default. The helper displays caller-provided
labels first; otherwise it shortens slash or backslash paths to the final name.
It does not inspect path existence and does no file IO.

Unredacted raw local paths, secret-like references, and required redaction-review
states block readiness until explicit supplied review state is present. This
policy is a display policy only, not a writer.

## Schema/migration policy

The view-model requires supplied schema-version display metadata unless the caller
explicitly marks a placeholder schema version accepted. A migration-required flag
blocks readiness with `blocked_schema_migration`.

This gate creates no schema file and performs no migration. Future schema model,
file persistence, settings-file, GUI, CLI, reload, and export gates must define
their own write and migration behavior.

## Stale-source and re-preview policy

Stale, missing, moved, or changed sources require re-preview. The view-model can
display stale-source rows and the `stale_source_requires_repreview`
acknowledgement, but it does not locate the file, restore it, rewrite it, delete
it, fetch it, trust it, or activate it.

If a future reload cannot re-preview a source, that future gate must define a
separate policy. This view-model does no file IO.

## Validation/evidence policy

Persisted state is not validation evidence. It is not validation success and not
validation failure. Skipped-missing remains skipped-missing.

Historical validation evidence, deactivation history, and reactivation history
remain visible and retained as supplied data. Persistence does not erase history,
rewrite evidence, delete evidence, validate optional stacks, close issues, or
claim live optional validation completion.

## Relationship to OSW-EXP-090 design

OSW-EXP-090 defined optional solver plugin manifest state persistence semantics
as design-only. OSW-EXP-092 implements the pure persistence view-model slice of
that design. It keeps the OSW-EXP-090 redaction-first, acknowledgement-aware,
schema-aware, non-validating, non-installing, non-executing, non-mutating, and
future-gated boundary.

File persistence, settings files, ProjectSchema mutation, GUI persistence, CLI
persistence, reload behavior, export behavior, source integration, discovery
integration, validation, install/uninstall behavior, solver execution, issue
actions, and release actions remain separate future gates.

## Relationship to activation/deactivation/reactivation/discovery-refresh

The view-model can adapt already-built activation, deactivation, reactivation,
and discovery-refresh view-model records into persistence-review records.

Those adapters are pure transformations. They do not mutate activation,
deactivation, reactivation, or discovery-refresh state. They do not turn
activation review into automatic activation. They do not turn deactivation into
file deletion. They do not turn reactivation into trust restoration. They do not
turn discovery-refresh into discovery execution.

## Relationship to GUI and CLI

This gate adds no GUI behavior and no CLI behavior. It imports no PySide, Qt,
file-dialog code, command runner, subprocess path, or CLI command module.

Future GUI and CLI gates may render these records, but must keep their own tests
for acknowledgement handling, disabled actions, no direct solver execution, no
install/uninstall, no file writes unless explicitly gated, and no issue/release
mutation.

## Relationship to ProjectSchema

The view-model does not import, instantiate, or mutate ProjectSchema. It exposes
ProjectSchema mutation as a disabled/future action and as a false honesty flag.

Any future ProjectSchema persistence or project-local state model requires a
separate gate with schema, migration, unit, validation, preview, and rollback
tests.

## Relationship to export-summary design

OSW-EXP-091 defined export-summary semantics as design-only. This persistence
view-model may provide state that a future export-summary view-model can read,
but this gate creates no export summary implementation, no export file, no
clipboard behavior, no open-output-folder behavior, and no reloadable bundle.

An export summary is not persistence and not validation evidence unless a future
gate explicitly changes that boundary.

OSW-EXP-097 adds that pure export-summary view-model as a separate in-memory
adapter over supplied persistence records. It writes no files, creates no export
files, creates no reloadable bundles, adds no clipboard/report behavior, and
does not mutate this persistence view-model or its source behavior.

## Relationship to live optional validation issues

Issues `#6` through `#11` remain open unless a separate live optional validation
gate supplies passing installed-only evidence and performs issue triage.

This view-model does not change live optional validation state, does not turn
skipped-missing into pass or fail, does not close issues, and does not claim that
optional solver stacks are validated.

## Non-actions

This gate explicitly performs no persistence implementation, no file writes, no
settings file creation, no ProjectSchema mutation, no GUI persistence behavior,
no CLI persistence behavior, no reload behavior, no export behavior, no
automatic activation, no trust restoration, no file restore, no file rewrite, no
file deletion, no dependency installation, no dependency uninstall, no solver
uninstall, no plugin package import, no directory scan, no network fetch, no
discovery execution, no validation execution, no solver execution, no issue
mutation, no issue closure, no release mutation, no tag mutation, no asset
mutation, no version bump, no validation-pass claim, no validation-fail claim,
and no certification claim.

## Future gates

Future gates remain required for:

- persistence schema model
- persistence writer
- settings-file model
- ProjectSchema integration
- GUI persistence behavior
- CLI persistence behavior
- reload behavior
- export-summary view-model
- export-summary GUI/CLI/report behavior
- reloadable bundle semantics
- source integration
- discovery integration
- validation integration
- dependency install/uninstall behavior
- solver uninstall behavior
- solver execution behavior
- issue closure
- release/tag/asset/version mutation
- trust elevation
- certification or validation claims

## Follow-up: schema model (OSW-EXP-093)

OSW-EXP-093 adds the pure, in-memory persistence schema model. It can adapt an
already-built persistence view-model with `from_persistence_viewmodel`, defines
the versioned record shape, and validates supplied mappings. It still writes
nothing and creates no schema file. See
[optional_solver_plugin_manifest_persistence_schema_model.md](optional_solver_plugin_manifest_persistence_schema_model.md).

## Follow-up: persistence GUI design (OSW-EXP-094)

OSW-EXP-094 designs the future PySide persistence GUI surface that may render
this view-model together with the OSW-EXP-093 schema model. See
[optional_solver_plugin_manifest_persistence_gui_design.md](optional_solver_plugin_manifest_persistence_gui_design.md).
The design adds no GUI implementation and no persistence implementation. It keeps
the view-model pure and keeps file writes, settings files, runtime state files,
schema files, ProjectSchema mutation, reload/export behavior, automatic
activation, trust restoration, discovery/validation/solver execution,
install/uninstall behavior, and issue/release/tag/asset mutation future-gated.

## Follow-up: persistence GUI implementation (OSW-EXP-095)

OSW-EXP-095 adds `OptionalSolverPluginManifestPersistencePanel`, a PySide review
surface that consumes this view-model without changing it. The panel renders
summary, source, candidate, acknowledgement, diagnostic, redaction,
schema/migration, stale-source, conflict, unsafe-claim, evidence/history,
trust/provenance, non-action flag, and disabled action-state records. It keeps
acknowledgement interaction widget-local and non-persistent and adds no runtime
persistence behavior, file writes, settings files, runtime state files, schema
files, ProjectSchema mutation, CLI behavior, reload/export behavior, discovery
execution, validation execution, solver execution, install/uninstall behavior,
or issue/release/tag/asset mutation.
