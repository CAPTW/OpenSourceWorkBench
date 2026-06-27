# Optional solver plugin manifest persistence GUI implementation

## Status

Experimental PySide persistence GUI surface implemented.

- view-model/schema-model driven.
- No runtime persistence behavior.
- No file writes.
- No settings file creation.
- No runtime state file creation.
- No schema file creation.
- No ProjectSchema mutation.
- No file dialog and no save dialog.
- No reload behavior and no export behavior.
- No clipboard behavior and no open-output-folder behavior.
- No CLI behavior.
- No discovery execution, validation execution, or solver execution.
- No issue mutation, release mutation, tag mutation, asset mutation, or version
  bump.

This gate (OSW-EXP-095) implements a PySide review panel that renders the pure
OSW-EXP-092 persistence view-model and, when supplied by the caller, OSW-EXP-093
in-memory schema model records. It adds GUI source only; it does not implement
the product behavior of saving, reloading, exporting, or restoring optional
solver plugin manifest state.

## Purpose

Render optional solver plugin manifest persistence readiness for human review:
sources, candidates, acknowledgements, diagnostics, redaction/privacy,
schema/migration, stale-source/re-preview, conflicts/shared stacks, unsafe
claims, evidence/history retention, trust/provenance, non-action flags, safety
guidance, and disabled/future action states.

The panel lets a user inspect what a future persistence writer would require
without writing files, creating settings, creating runtime state, mutating
ProjectSchema, reloading state, exporting summaries, activating candidates,
restoring trust, running discovery, running validation, or executing solvers.

## Public module and class names

- Module:
  `src/osw/gui/dialogs/optional_solver_plugin_manifest_persistence_panel.py`
- Public class: `OptionalSolverPluginManifestPersistencePanel`
- Lazy package export: `OptionalSolverPluginManifestPersistencePanel` is exported
  from `osw.gui.dialogs` through the existing lazy `__getattr__` hook.

Constructor seams:

- `view_model`: an `OptionalSolverPluginManifestPersistenceViewModel` (defaults
  to `.unavailable()`).
- `schema_model`: an optional `OptionalSolverPluginManifestPersistenceSchemaModel`
  supplied by the caller for display only.
- `acknowledgement_callback`: an optional pure callback that receives the
  widget-local acknowledgement map and returns a fresh view-model.
- `theme_tokens`: optional theme tokens.

## User flow

- Empty/no-state view: persistence is unavailable, no sources or candidates are
  shown, and the not-implemented diagnostic and non-action flags are visible.
- Source/candidate review: supplied manifest UX state renders with redacted source
  references, trust labels, lifecycle state, persistence readiness, blockers, and
  warnings.
- Acknowledgement review: required acknowledgements render with satisfied,
  persisted, blocking, and expiry-on-reload/source/schema/unsafe-claim state.
- Schema/migration review: supplied schema version and migration rows render, and
  supplied schema model records render as in-memory records only.
- Redaction/privacy review: redacted display references, unredacted path blockers,
  and secret-like content blockers render without exposing raw local paths.
- Stale-source review: stale/missing/moved/changed sources require future
  re-preview and are not silently trusted.
- Conflict/shared-stack review: built-ins remain authoritative by default and
  conflicts remain visible after a future reload.
- Unsafe-claim review: unsafe claims are blocked and not accepted by persistence.
- Evidence/history review: deactivation/reactivation history and historical
  validation evidence are retained; skipped-missing remains skipped-missing.
- Action review: all persistence, reload, export, discovery, validation, solver,
  install, issue, release, tag, asset, and trust-restoration actions remain
  disabled/future-only.

Acknowledgement interaction is widget-local and non-persistent. When a pure
acknowledgement callback is injected, acknowledge actions toggle the panel-local
acknowledgement map and rebuild a supplied view-model. Without a callback, the
panel is display-only.

## Rendered sections

- Summary with readiness, state, counts, and honesty/non-action flags.
- Sources.
- Candidates.
- Acknowledgements and expiry policy.
- Diagnostics using `OSPMG_PERSISTENCE_*` codes.
- Redaction/privacy rows.
- Schema/migration rows plus supplied schema-model record summary.
- Stale-source/re-preview rows.
- Conflict/shared-stack rows.
- Unsafe-claim rows.
- Evidence/history rows.
- Trust/provenance text.
- Non-action flags.
- Safety guidance and blocked transitions.
- Action states and disabled reasons.

## Action boundary

The panel implements no action that persists, reloads, exports, scans, validates,
executes, installs, uninstalls, or mutates external state.

Disabled/future-only actions include `request_persistence`, `review_redaction`,
`save_state`, `create_settings_file`, `mutate_project_schema`, `reload_state`,
`export_summary`, `create_reloadable_bundle`, `automatic_activation`,
`trust_restoration`, `run_discovery`, `run_validation`, `install_dependency`,
`uninstall_dependency`, `uninstall_solver`, `execute_solver`, `close_issue`, and
`mutate_release`.

The only optionally enabled actions are `acknowledge_*` toggles, and only when a
caller injects a pure acknowledgement callback. They are widget-local and
non-persistent and write nothing.

## Trust and safety boundary

- User-selected and plugin-provided manifests remain untrusted by default.
- Built-ins remain authoritative by default.
- Trust label is not certification.
- Persisted state is not validation evidence.
- Persistence is not trust restoration.
- Persistence is not automatic activation.
- Stale or missing sources require re-preview.
- Unsafe claims are blocked.
- Skipped-missing remains skipped-missing.
- Issues `#6` through `#11` remain open.

## Testing strategy

- Offscreen Qt subprocess tests guard on PySide6 availability so base unit tests
  do not require GUI extras.
- Empty-state, rich-state, blocked-state, and ready-state view-model rendering is
  asserted through panel text accessors.
- Schema model rendering is asserted from a caller-supplied in-memory schema
  model.
- Widget-local acknowledgement interaction is asserted through an injected pure
  callback.
- Source-level guardrails assert no direct discovery, validation, solver,
  install/uninstall, file dialog, save dialog, clipboard, output-folder, browser,
  network, shell, or file-mutation paths are present in the panel source.
- The persistence view-model and schema model remain PySide/Qt-free.

## Relationship to OSW-EXP-092 view-model

The panel consumes `OptionalSolverPluginManifestPersistenceViewModel` records and
does not add PySide/Qt imports, file IO, persistence behavior, plugin imports,
directory scans, network fetches, discovery execution, validation execution,
solver execution, install/uninstall behavior, issue mutation, release mutation,
or certification claims to the view-model. The view-model remains pure.

## Relationship to OSW-EXP-093 schema model

The panel can display caller-supplied
`OptionalSolverPluginManifestPersistenceSchemaModel` records. It does not
serialize the schema model, create a schema file, create a runtime state file,
create settings, mutate ProjectSchema, run migration behavior, or convert the
schema model into persistence.

## Relationship to OSW-EXP-094 design

The panel implements the OSW-EXP-094 review-only GUI surface while preserving the
design boundary: redaction-first, acknowledgement-aware, schema/migration-aware,
stale-source-aware, conflict/unsafe-claim-aware, evidence/history-retaining,
non-validating, non-writing, non-installing, non-executing, and non-mutating.

## Relationship to existing panels

Activation, deactivation, reactivation, and discovery-refresh panels remain
view-model driven and non-persistent. This persistence panel mutates no activation
source behavior, deactivation source behavior, reactivation source behavior,
discovery-refresh source behavior, persistence view-model behavior, or schema
model behavior.

## Relationship to CLI, reload, and export

No CLI behavior changes and no persistence CLI command are added. The panel
renders an in-memory redacted summary accessor only. It adds no file dialog, no
save dialog, no reload behavior, no export behavior, no clipboard behavior, no
shell/browser action, and no open-output-folder behavior.

## Relationship to live optional validation issues

issues `#6` through `#11` remain open. Persistence readiness is not live optional
validation evidence, not validation pass, not validation fail, and not issue
closure evidence. Prepared-machine validation remains a separate gate.

Package metadata remains `0.1.5rc1`, and the public prerelease remains
`v0.1.5-rc1`.

## Non-actions

This gate explicitly performs:

- no runtime persistence behavior
- no file writes
- no settings file creation
- no runtime state file creation
- no schema file creation
- no ProjectSchema mutation
- no file dialog behavior
- no save dialog behavior
- no reload behavior
- no export behavior
- no clipboard behavior
- no open-output-folder behavior
- no CLI behavior
- no automatic activation
- no trust restoration
- no file restoration, rewrite, or deletion
- no dependency installation
- no dependency uninstall
- no solver uninstall
- no plugin package import
- no directory scan
- no network fetch
- no discovery execution
- no validation execution
- no solver execution
- no activation/deactivation/reactivation/discovery-refresh source behavior
  mutation
- no persistence view-model or schema-model behavior mutation
- no issue mutation
- no issue closure
- no release mutation
- no tag mutation
- no asset mutation
- no version bump
- no validation-pass claim
- no validation-fail claim
- no bundled-solver claim
- no certification claim

## Future gates

Future gates remain required for:

- `OSW-EXP-096_OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_CLI_DESIGN`
- persistence writer design and implementation
- settings-file and runtime state-file models
- ProjectSchema integration
- reload behavior
- export-summary view-model, GUI, CLI, and report behavior
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
