# Optional Solver Plugin Manifest Reload Acceptance ViewModel

## 1. Status

Experimental reload acceptance view-model implemented.

The implementation is pure in-memory, side-effect-free, and view-model only. It
adds no reload acceptance implementation, no runtime reload acceptance, no
persistence writes, no ProjectSchema mutation, no GUI or CLI behavior, no file
IO, no reader invocation, no discovery/validation/solver execution, no automatic
activation, and no trust restoration.

## 2. Purpose

The module models whether an already-built optional solver plugin manifest reload
preview is ready for a future explicit acceptance action. It gives future GUI
and CLI gates deterministic rows for readiness, blockers, acknowledgements,
diagnostics, accepted-for-session-review state, future review requirements,
non-action flags, and disabled/future actions.

## 3. Public Module And Class Names

- `src/osw/experimental/optional_solvers/plugin_manifest_reload_acceptance_viewmodel.py`
- `OptionalSolverPluginManifestReloadAcceptanceViewModel`
- `ReloadAcceptanceState`
- `ReloadAcceptanceReadiness`
- `ReloadAcceptanceAction`
- `ReloadAcceptanceInput`
- `ReloadAcceptanceSummary`
- `ReloadAcceptanceAcknowledgementRow`
- `ReloadAcceptanceDiagnostic`
- `ReloadAcceptanceBlockerRow`
- `ReloadAcceptanceActionState`
- `ReloadAcceptanceAcceptedStateRow`
- `ReloadAcceptanceSourceProvenanceRow`
- `ReloadAcceptanceEvidenceHistoryRow`
- `ReloadAcceptanceTrustBadge`
- `ReloadAcceptanceNonActionFlags`

## 4. Inputs And Construction Policy

The view-model consumes supplied reload view-model objects or already-built
reload preview mappings. It does not accept paths, raw file content, or reader
requests. It never calls the reload file reader and never calls GUI or CLI code.

Supported constructors include `unavailable()`, `from_reload_viewmodel()`,
`from_preview_mapping()`, `ready_for_future_acceptance()`,
`accepted_for_session_review()`, and
`build_optional_solver_plugin_manifest_reload_acceptance_viewmodel()`.

## 5. State And Readiness Model

The state vocabulary covers no preview, not requested, blocked,
ready-for-future-acceptance, accepted-for-session-review, future-review-required,
and error states. The readiness vocabulary distinguishes missing preview,
not-requested, reader-blocked, view-model-blocked, acknowledgement-blocked,
stale-source, conflict, shared-stack, unsafe-claim, unsupported-schema,
migration-required, unredacted-path, secret-like-value, policy-change,
ready-future-only, accepted-for-session-review, future-review, and error
conditions.

## 6. Acceptance Preconditions

Future acceptance requires a supplied reload preview, an explicit request, no
reader or reload view-model blockers, supported schema without migration,
completed redaction/privacy review, no stale-source or conflict blocker, no
unsafe claim, and all required acknowledgements satisfied for the current
preview.

## 7. Acceptance Blockers

The implementation surfaces blockers for missing preview, reader blocked,
reload view-model blocked, missing or expired acknowledgement, stale-source or
re-preview required, conflict review, shared-stack review, unsafe claim,
unsupported schema, migration required, unredacted path, secret-like value, trust
policy changes, source fingerprint changes, acceptance policy changes, and error
state.

## 8. Acknowledgement Model

Required acknowledgements are visible, deterministic, non-persisted, and
individually marked as satisfied, missing, expired, and blocking. They preserve
the boundaries that acceptance is not validation evidence, validation failure,
trust restoration, automatic activation, discovery success, dependency
installation, solver execution, issue closure, release mutation, certification,
persistence write, or ProjectSchema mutation.

## 9. Acknowledgement Expiry Policy

The view-model exposes expiry reasons for reload, source fingerprint change,
schema version change, unsafe-claim appearance, trust policy change, future
discovery-refresh result, file-reader policy change, GUI file-dialog policy
change, CLI explicit-path policy change, acceptance policy change, ProjectSchema
policy change, and validation issue state change.

## 10. Accepted-State Scope Model

Accepted-for-session-review is representation-only supplied state. It is scoped
to session/review, remains untrusted by default, and is not persistence,
ProjectSchema state, validation evidence, validation failure, automatic
activation, trust restoration, discovery success, dependency installation,
solver execution, issue closure, release mutation, or certification.

## 11. Reader And Preview Provenance

Reader diagnostics may be represented as supplied blocker context, but the
module never invokes the reader. Preview provenance rows are copied from supplied
reload view-model mappings and keep source displays redacted when the upstream
preview marked them redacted.

## 12. Schema And Migration Policy

Unsupported schemas and migration-required states block acceptance. Schema
review remains separate from ProjectSchema, and migration remains a future gate.

## 13. Redaction And Privacy Policy

Unredacted path and secret-like value signals block acceptance. The view-model
does not inspect files and does not recover raw paths; it only reflects supplied
preview state.

## 14. Candidate Lifecycle Policy

Candidate lifecycle remains review-only. Accepted-for-session-review does not
activate, deactivate, reactivate, install, uninstall, or trust candidates.
Future activation and discovery-refresh review requirements remain visible.

## 15. Stale-Source And Re-Preview Policy

Stale sources or source fingerprint changes block acceptance and require a fresh
preview. Stale-source state is not validation failure.

## 16. Conflict And Shared-Stack Policy

Conflicts and shared-stack warnings remain visible. Built-ins remain
authoritative by default, persisted or reloaded state does not override them, and
future review is required before activation or discovery refresh.

## 17. Unsafe-Claim Policy

Unsafe claims about validation pass/fail, issue closure, release mutation,
bundled solvers, dependency installation, solver execution, trust restoration,
automatic activation, or certification are blocked and not accepted as truth.

## 18. Evidence And History Policy

Evidence/history rows remain reference-only. They are not new validation
evidence, not validation failure, not issue closure, not release mutation, and
not certification.

## 19. Diagnostics Vocabulary

The view-model reserves and emits `OSPMG_RELOAD_ACCEPTANCE_*` diagnostics for
not requested, preview missing, reader blocked, view-model blocked,
acknowledgement required, stale-source re-preview, conflict review,
shared-stack review, unsafe claim, unsupported schema, migration required,
unredacted path, secret-like value, trust policy change, source fingerprint
change, policy change, ready, accepted-for-session-review, future activation
review, future discovery refresh, and error.

## 20. Non-Action Flags

`ReloadAcceptanceNonActionFlags` exposes false flags for runtime reload
acceptance, persistence write, ProjectSchema mutation, default/background reload,
directory scan, network fetch, plugin package import, CLI subprocess use,
reloadable bundle creation, export/report creation, clipboard/report/open-folder
behavior, discovery, passive refresh, validation, solver execution, dependency
install/uninstall, solver uninstall, automatic activation, trust restoration,
issue/release/tag/asset mutation, version bump, validation-pass/fail claim,
issue-closure claim, bundled-solver claim, and certification claim.

## 21. Disabled And Future Action States

Every exposed action is disabled and future-only: request acceptance,
accept-for-session-review, accept as trusted, activate reloaded candidate,
refresh discovery, validate solver, execute solver, install/uninstall
dependency, uninstall solver, mutate ProjectSchema, persist state, create export
summary, create report file, create reloadable bundle, copy to clipboard, attach
to report, open output folder, close issue, mutate release, push tag, upload
asset, claim validation success, claim validation failure, and claim
certification.

## 22. Mapping And Text Output Behavior

`to_mapping()` returns deterministic JSON-compatible data. `to_text_lines()`
returns stable plain-text review lines with state, readiness, acknowledgements,
blockers, diagnostics, disabled actions, and safety guidance. Both outputs keep
acceptance separate from validation, trust, activation, persistence, ProjectSchema,
issues, releases, and certification.

## 23. Relationship To Reload Acceptance Design

OSW-EXP-118 designed reload acceptance as a future explicit reviewed-preview
boundary. OSW-EXP-119 implements only the pure view-model needed to test that
boundary before any GUI or CLI acceptance action exists.

## 24. Relationship To Reload View-Model

The acceptance view-model consumes OSW-EXP-107 reload view-model objects or
already-built mappings. It does not modify the reload view-model source and does
not reinterpret raw persisted state files.

## 25. Relationship To Reload File Reader

The acceptance view-model may reflect supplied reader-blocked context, but it
does not import or call the OSW-EXP-113 file reader. Reader-first CLI and GUI
preview remain separate.

## 26. Relationship To Reload GUI File Dialog

The OSW-EXP-117 GUI file-dialog remains preview-only. A future GUI acceptance
gate may consume this view-model, but this gate adds no GUI buttons, dialogs,
file opening behavior, or CLI subprocess bridge.

## 27. Relationship To Reload CLI Explicit Path

The OSW-EXP-115 CLI explicit path remains stdout-first preview-only. A future
CLI acceptance gate may consume this view-model, but this gate adds no CLI
commands or path behavior.

## 28. Relationship To State Writer And Persistence

The module writes nothing and persists nothing. State writer and persistence
contracts remain separate, explicit, acknowledgement-bound gates.

## 29. Relationship To ProjectSchema

Accepted-for-session-review is not ProjectSchema state. No ProjectSchema
mutation or integration is implemented.

## 30. Relationship To Live Optional Validation Issues

Reload acceptance is not validation evidence and not validation failure. Live
optional validation issues `#6` through `#11` remain open and separate.

## 31. Security And Privacy Review

The module is path-free, reader-free, Qt-free, CLI-free, IO-free, solver-free,
and optional-dependency-light. It surfaces redaction, secret-like value,
source-fingerprint, trust-policy, unsafe-claim, evidence/history, and
non-certification boundaries without inspecting external content.

## 32. Non-Actions

This gate adds no runtime reload acceptance, file IO, reader invocation, GUI
behavior, CLI behavior, file-reader source edit, reload view-model source edit,
acceptance button, acceptance CLI command, persistence write, ProjectSchema
mutation, default reload path, background reload, directory scan, network fetch,
plugin package import, CLI subprocess use, reloadable bundle, export file,
report file, clipboard behavior, report attachment, open-output-folder behavior,
live discovery, passive refresh, validation execution, solver execution,
dependency installation, dependency uninstall, solver uninstall, automatic
activation, trust restoration, issue mutation, release mutation, tag mutation,
asset mutation, version bump, validation-pass claim, validation-fail claim,
issue-closure claim, bundled-solver claim, or certification claim.

## 33. Testing Strategy

Focused tests cover imports/exports, no-preview, not-requested, missing
acknowledgements, ready future-only state, accepted-for-session-review
representation, reader/view-model blockers, stale-source, conflict, shared
stack, unsafe claim, schema, migration, redaction/privacy, policy changes,
future activation/discovery review, acknowledgement expiry, source/evidence
trust boundaries, non-action flags, disabled actions, deterministic mapping/text
output, diagnostic vocabulary, error state, and non-mutation of supplied input.

## 34. Future Gates

Future gates may design and implement GUI/CLI acceptance actions, accepted-state
storage boundaries, activation/discovery-review consumption, ProjectSchema
integration, and validation/issue/release workflows. Each remains separate and
must preserve explicit user/caller review, no hidden trust restoration, no
automatic activation, no skipped-missing-as-success, and no certification claims.

## 35. Follow-up: Acceptance GUI Design (OSW-EXP-120)

OSW-EXP-120 designs a future PySide review surface that consumes this view-model
without editing this source module
([optional_solver_plugin_manifest_reload_acceptance_gui_design.md](optional_solver_plugin_manifest_reload_acceptance_gui_design.md)).
The design renders readiness, blockers, acknowledgements, expiry, provenance,
diagnostics, non-action flags, and disabled/future actions only. It adds no GUI
implementation, no acceptance buttons, no callbacks, no runtime acceptance, no
persistence writes, no ProjectSchema mutation, no discovery, no validation, no
solver execution, no activation, no trust restoration, no issue/release/tag/asset
mutation, and no certification claims.

## 36. Follow-up: Acceptance GUI Implementation (OSW-EXP-121)

OSW-EXP-121 implements
`OptionalSolverPluginManifestReloadAcceptancePanel` as the PySide review surface
over this view-model
([optional_solver_plugin_manifest_reload_acceptance_gui_implementation.md](optional_solver_plugin_manifest_reload_acceptance_gui_implementation.md)).
The panel consumes `to_mapping()` output only and renders readiness, blockers,
acknowledgements, expiry, accepted-state scope, provenance, diagnostics,
non-action flags, disabled/future actions, and safety guidance.

The implementation does not edit this source module, invoke readers, call CLI
code, perform file IO, add acceptance buttons or callbacks, accept runtime
reload state, write persistence, mutate ProjectSchema, run discovery,
validation, or solver execution, activate candidates, restore trust, mutate
issues/releases/tags/assets, or claim certification.

## 37. Follow-up: Acceptance CLI Design (OSW-EXP-122)

OSW-EXP-122 defines future CLI rendering over supplied
`OptionalSolverPluginManifestReloadAcceptanceViewModel` records
([optional_solver_plugin_manifest_reload_acceptance_cli_design.md](optional_solver_plugin_manifest_reload_acceptance_cli_design.md)).
The design keeps this view-model as the sole acceptance policy source of truth
and adds no CLI source edits, no acceptance CLI commands, no acceptance flags,
no callbacks, no file IO, no reader invocation, no GUI subprocess use, no
runtime reload acceptance, no persistence writes, no ProjectSchema mutation, no
discovery, no validation, no solver execution, no automatic activation, no trust
restoration, no issue/release/tag/asset mutation, and no certification claims.

## 38. Follow-up: Acceptance CLI Implementation (OSW-EXP-123)

OSW-EXP-123 implements a stdout-first CLI renderer over this view-model
([optional_solver_plugin_manifest_reload_acceptance_cli_implementation.md](optional_solver_plugin_manifest_reload_acceptance_cli_implementation.md)).
The CLI uses deterministic in-memory sample, unavailable, not-requested,
blocked, ready, and accepted-for-session-review records, then renders
`to_mapping()` output and safety guidance.

The implementation does not edit this source module, add independent acceptance
policy, read files, invoke the reader, call GUI code, mutate ProjectSchema,
write persistence, run discovery, validation, or solver execution, activate
candidates, restore trust, mutate issues/releases/tags/assets, or claim
certification.

## 39. Follow-up: Acceptance Persistence Design (OSW-EXP-124)

OSW-EXP-124 designs future persistence for reviewed acceptance UX state
([optional_solver_plugin_manifest_reload_acceptance_persistence_design.md](optional_solver_plugin_manifest_reload_acceptance_persistence_design.md)).
The persistence design keeps this view-model as the acceptance-policy source of
truth and adds no source edits, no independent persistence policy, no writer
implementation, no persistence writes, no runtime reload acceptance, no
ProjectSchema mutation, no file IO, no reader invocation, no discovery,
validation, solver execution, activation, trust restoration, issue/release/tag/
asset mutation, or certification claims.

## 40. Follow-up: Acceptance Persistence ViewModel (OSW-EXP-125)

OSW-EXP-125 adds a pure in-memory future persistence planning view-model
([optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel.md](optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel.md))
that consumes this acceptance view-model through `to_mapping()` or equivalent
safe mappings. It does not edit this module and does not add independent
acceptance policy.

The persistence view-model remains future-writer-only: it writes no files,
creates no checked-in state files, performs no runtime reload acceptance,
mutates no ProjectSchema, calls no CLI/GUI behavior, invokes no reader or
writer, runs no discovery, validation, or solver execution, and makes no
issue/release/certification claims.

## Follow-up: Acceptance Persistence Writer (OSW-EXP-126)

OSW-EXP-126 implements a separately gated persistence writer
([optional_solver_plugin_manifest_reload_acceptance_persistence_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_implementation.md))
that consumes downstream persistence view-model records derived from this
acceptance view-model. The writer does not add independent acceptance policy and
does not mutate this acceptance view-model.

The writer remains explicit-target-path only, dry-run-first, and
caller-acknowledged before actual writes. It does not accept runtime reloads,
perform active acceptance mutation, invoke readers, call CLI/GUI behavior, use
subprocesses, mutate ProjectSchema, run discovery/validation/solver execution,
activate candidates, restore trust, mutate issues/releases/tags/assets, claim
validation pass/fail evidence, or claim certification.
