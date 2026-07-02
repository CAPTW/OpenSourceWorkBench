# Optional Solver Plugin Manifest Reload Acceptance GUI Implementation

## 1. Status

Experimental reload acceptance GUI review panel implemented.

The implemented panel is
`OptionalSolverPluginManifestReloadAcceptancePanel` in
`src/osw/gui/dialogs/optional_solver_plugin_manifest_reload_acceptance_panel.py`.
It is a PySide review surface over an already-built
`OptionalSolverPluginManifestReloadAcceptanceViewModel`.

This implementation adds no runtime reload acceptance, no persistence writes, no
ProjectSchema mutation, no file IO, no reader invocation, no CLI bridge, no GUI
file dialog, no default reload path, no background reload, no directory scan, no
network fetch, no plugin package import, no reloadable bundle creation, no
export file creation, no report file creation, no clipboard behavior, no report
attachment, no open-output-folder behavior, no live discovery, no passive
refresh, no validation execution, no solver execution, no dependency
installation, no dependency uninstall, no solver uninstall, no automatic
activation, no trust restoration, no issue mutation, no release mutation, no tag
mutation, no asset mutation, no version bump, no validation-pass claim, no
validation-fail claim, no issue-closure claim, no bundled-solver claim, and no
certification claim.

## 2. Public GUI Surface

The public class is exported lazily from `osw.gui.dialogs` as
`OptionalSolverPluginManifestReloadAcceptancePanel`.

The constructor accepts an optional supplied
`OptionalSolverPluginManifestReloadAcceptanceViewModel`. If no view-model is
supplied, the panel uses the view-model `unavailable()` state. Construction does
not open a native dialog, read files, parse persisted state, call the reload file
reader, call CLI code, or create output files.

The panel exposes focused inspection helpers for tests and future callers:

- `set_view_model(...)`;
- `refresh()`;
- `summary_text()`;
- `blocker_rows_text()`;
- `acknowledgement_rows_text()`;
- `expiry_rows_text()`;
- `accepted_state_text()`;
- `provenance_text()`;
- `schema_migration_text()`;
- `redaction_privacy_text()`;
- `candidate_lifecycle_text()`;
- `stale_source_text()`;
- `conflict_text()`;
- `unsafe_claim_text()`;
- `evidence_history_text()`;
- `trust_text()`;
- `diagnostics_text()`;
- `non_action_flags_text()`;
- `action_state_text()`;
- `safety_text()`;
- `available_action_names()`;
- `disabled_action_reasons()`;
- `rendered_text()`.

These helpers return rendered review text only. They do not accept, persist,
activate, validate, discover, execute, install, uninstall, trust, close issues,
mutate releases, push tags, upload assets, or certify anything.

## 3. Input Policy

The panel consumes only the supplied acceptance view-model `to_mapping()` output.
It does not accept paths, raw file content, JSON text, reader requests, CLI
output, ProjectSchema state, or plugin packages.

The panel does not independently reinterpret reload payloads. The acceptance
view-model remains the policy source for readiness, blockers, acknowledgements,
diagnostics, accepted-for-session-review state, evidence/history, non-action
flags, and disabled/future actions.

## 4. Rendering Sections

The panel renders stable review sections:

- summary/readiness;
- preconditions and blockers;
- acknowledgements;
- acknowledgement expiry;
- accepted-state scope;
- reader and preview provenance;
- schema/migration;
- redaction/privacy;
- candidate lifecycle;
- stale-source/re-preview;
- conflict/shared-stack;
- unsafe claims;
- evidence/history;
- trust/provenance;
- diagnostics;
- non-action flags;
- disabled/future actions;
- safety guidance.

The compact summary repeats safety booleans for no validation evidence, no
validation failure, no ProjectSchema mutation, no persistence write, no
automatic activation, no trust restoration, no discovery, no solver execution,
no issue/release mutation, and no certification.

## 5. Accepted-State Scope

Accepted-for-session-review rows are displayed only when supplied by the
view-model. The panel does not create accepted state and does not turn accepted
state into persisted runtime state.

Accepted-for-session-review remains session/review scoped, untrusted by default,
not ProjectSchema state, not persistence, not validation evidence, not
validation failure, not automatic activation, not trust restoration, not issue
closure, not release mutation, and not certification.

## 6. Redaction And Privacy

The renderer treats source and diagnostic text as review data. Path-like values
are reduced to basename display. Secret-like strings, including token/API key
markers, are rendered as `<redacted-secret>`.

Redaction is a display boundary only. The panel does not inspect files, repair
payloads, rewrite state, migrate schema, or store secrets.

## 7. Relationship To Reload Acceptance ViewModel

The panel consumes OSW-EXP-119 acceptance view-model records without editing the
view-model source. It relies on `to_mapping()` and keeps all disabled/future
action states visible. Any enabled unsafe action in a future view-model would be
visible through `available_action_names()` and review text.

## 8. Relationship To Reload GUI File Dialog

The OSW-EXP-117 reload GUI file-dialog panel remains the explicit-file,
reader-first preview wrapper. This acceptance panel has no file-dialog widget and
no file opening behavior. It can be shown after another caller has already built
the acceptance view-model records, but it does not call that preview wrapper or
the reader.

## 9. Relationship To Reload CLI

The OSW-EXP-115 CLI explicit path remains stdout-first and preview-only. This
panel does not parse CLI output and does not use the CLI as a subprocess bridge.
CLI acceptance remains a separate future gate.

## 10. Relationship To Persistence And ProjectSchema

The panel writes no persistence/state files and creates no schema files. Reload
acceptance review state is not ProjectSchema state. ProjectSchema integration
remains a separate future gate with its own preview, migration, rollback, tests,
and explicit user/caller confirmation.

## 11. Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. Reload acceptance GUI review is not live
optional validation, not skipped-missing success, not validation failure, not
issue closure, not release evidence, and not certification evidence.

## 12. Testing Strategy

`tests/gui/test_optional_solver_plugin_manifest_reload_acceptance_panel.py`
covers lazy export, inert construction, supplied ready and accepted view-model
states, blocker diagnostics, acknowledgement expiry rendering, future activation
and discovery-review warnings, redaction of path and secret-like strings,
non-action flags, disabled/future actions, no output file creation, and source
guardrails against file dialogs, clipboard, subprocesses, CLI bridges, reader
imports, ProjectSchema mutation, discovery, network access, file writes,
dependency install/uninstall, issue/release mutation, and certification claims.

Adjacent continuity checks cover the acceptance view-model, acceptance GUI
design docs, reload GUI file-dialog panel, and reload preview panel.

## 13. Non-Actions

This gate does not add runtime reload acceptance, file IO, reader invocation,
CLI behavior, GUI file-dialog behavior, acceptance callbacks, acceptance CLI
commands, persistence writes, ProjectSchema mutation, default reload paths,
background reload, directory scans, network fetches, plugin package imports, CLI
subprocess use, reloadable bundles, export files, report files, clipboard
behavior, report attachments, open-output-folder behavior, live discovery,
passive refresh, validation execution, solver execution, dependency
installation, dependency uninstall, solver uninstall, automatic activation,
trust restoration, issue mutation, release mutation, tag mutation, asset
mutation, version bump, validation-pass claim, validation-fail claim,
issue-closure claim, bundled-solver claim, or certification claim.

## 14. Future Gates

Future gates may design and implement CLI acceptance review, accepted-state
storage boundaries, activation/discovery-review consumption, ProjectSchema
integration, and prepared-machine optional validation. Each remains separate and
must preserve explicit user/caller review, no hidden trust restoration, no
automatic activation, no skipped-missing-as-success, and no certification
claims.

## 15. Follow-up: Acceptance CLI Design (OSW-EXP-122)

OSW-EXP-122 defines future stdout-first CLI acceptance review over the same
OSW-EXP-119 acceptance view-model records rendered by this GUI panel
([optional_solver_plugin_manifest_reload_acceptance_cli_design.md](optional_solver_plugin_manifest_reload_acceptance_cli_design.md)).
The design keeps GUI and CLI as separate renderers over supplied records. It
adds no CLI source edits, no acceptance CLI commands, no acceptance flags, no
callbacks, no file IO, no reader invocation, no GUI subprocess use, no runtime
reload acceptance, no persistence writes, no ProjectSchema mutation, no
discovery, no validation, no solver execution, no automatic activation, no trust
restoration, no issue/release/tag/asset mutation, and no certification claims.

## 16. Follow-up: Acceptance CLI Implementation (OSW-EXP-123)

OSW-EXP-123 implements the CLI counterpart to this GUI review panel
([optional_solver_plugin_manifest_reload_acceptance_cli_implementation.md](optional_solver_plugin_manifest_reload_acceptance_cli_implementation.md)).
The CLI and GUI remain sibling renderers over supplied acceptance view-model
records. The CLI does not call this panel, this panel does not call the CLI, and
no GUI subprocess bridge is introduced.

The implementation remains review-only: no runtime acceptance, file IO, reader
invocation, persistence write, ProjectSchema mutation, discovery, validation,
solver execution, activation, trust restoration, issue/release/tag/asset
mutation, or certification claim.

## 17. Follow-up: Acceptance Persistence Design (OSW-EXP-124)

OSW-EXP-124 designs future persistence of reload acceptance review-state
metadata
([optional_solver_plugin_manifest_reload_acceptance_persistence_design.md](optional_solver_plugin_manifest_reload_acceptance_persistence_design.md)).
The GUI panel remains view-model-only and non-writing. The persistence design
adds no GUI source edits, no GUI behavior, no file dialog, no persistence writes,
no runtime reload acceptance, no ProjectSchema mutation, no file IO, no reader
invocation, no CLI subprocess, no discovery, no validation, no solver execution,
no activation, no trust restoration, no issue/release/tag/asset mutation, and no
certification claims.

## 18. Follow-up: Acceptance Persistence ViewModel (OSW-EXP-125)

OSW-EXP-125 adds a pure in-memory reload acceptance persistence view-model
([optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel.md](optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel.md)).
The GUI panel remains a view-model-only acceptance renderer and does not invoke
the persistence view-model or any writer behavior.

The persistence view-model adds no GUI source edits, no GUI behavior, no file
dialog, no file IO, no writer or reader invocation, no subprocess use, no
persistence write, no ProjectSchema mutation, no runtime reload acceptance, no
discovery, no validation, no solver execution, no activation, no trust
restoration, no issue/release/tag/asset mutation, and no certification claim.

## 19. Follow-up: Acceptance Persistence Writer (OSW-EXP-126)

OSW-EXP-126 implements an explicit reload acceptance persistence writer
([optional_solver_plugin_manifest_reload_acceptance_persistence_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_implementation.md)).
The GUI panel remains view-model-only and review-only; it does not call the
writer, show a save dialog, pass target paths, write files, or create persisted
reload acceptance state.

The writer remains separately gated and local API-only. It is dry-run-first,
requires explicit target paths and caller acknowledgement for actual writes, and
does not add GUI behavior, runtime reload acceptance, ProjectSchema mutation,
discovery, validation, solver execution, activation, trust restoration,
issue/release/tag/asset mutation, validation claims, or certification claims.

## 20. Follow-up: Acceptance Persistence CLI Design (OSW-EXP-127)

OSW-EXP-127 designs a future CLI review/write-plan surface for reload
acceptance persistence
([optional_solver_plugin_manifest_reload_acceptance_persistence_cli_design.md](optional_solver_plugin_manifest_reload_acceptance_persistence_cli_design.md)).
This GUI panel remains view-model-only and non-writing; it does not call that
future CLI, invoke the writer, pass target paths, write files, or spawn
subprocesses.

The CLI design gate adds no GUI source edits, no GUI behavior, no writer
invocation, no file writes, no input state-file reading or parsing, no reload
file-reader invocation, no ProjectSchema mutation, no runtime acceptance, no
discovery, validation, solver execution, activation, trust restoration,
issue/release/tag/asset mutation, validation claim, or certification claim.
