# Optional Solver Plugin Manifest Reload Acceptance CLI Implementation

## 1. Status

Experimental reload acceptance CLI review is implemented as a stdout-first,
review-only command family. It performs no runtime reload acceptance, no active
acceptance mutation, no persistence writes, no ProjectSchema mutation, no file
IO, no file reading, no file parsing, no reader invocation, no GUI calls, no GUI
subprocess use, no discovery, no validation, no solver execution, no automatic
activation, and no trust restoration.

This gate does not mutate issues, releases, tags, assets, versions, validation
evidence, validation-failure evidence, issue-closure evidence, bundled-solver
claims, or certification claims.

## 2. Purpose

The CLI makes OSW-EXP-119 reload acceptance view-model state inspectable from a
terminal without converting review into runtime acceptance. It is intended for
human and CI log review of acceptance readiness, blockers, acknowledgements,
expiry, diagnostics, non-action flags, disabled/future actions, and safety
guidance.

## 3. Public Command Names

The public command family is:

```text
python -m osw.cli optional-solver-plugin-manifest-reload-acceptance <subcommand>
```

Implemented subcommands are `explain`, `preview`, `summary`, `blockers`,
`acknowledgements`, `expiry`, `diagnostics`, `actions`, `safety`, and
`accept-future`.

## 4. State Source Policy

The command consumes deterministic, in-memory
`OptionalSolverPluginManifestReloadAcceptanceViewModel` records only. Supported
state flags are `--sample-state`, `--empty-state`, `--unavailable-state`,
`--not-requested-state`, `--blocked-state`, `--ready-state`, and
`--accepted-state`.

The default state is unavailable/no preview. The command accepts no `--path`,
does not read or parse files, does not call the reload file reader, and does not
inspect referenced source files.

## 5. Command Behavior

Review subcommands render supplied or synthetic in-memory acceptance records.
Blocked review states still return `0` when rendering succeeds because the exit
code means command completion only. `accept-future` is disabled/future-only and
returns `2` without mutating state.

## 6. Output Modes

Text output is stable and sectioned for terminal review. `--json` emits
deterministic JSON with sorted keys. Section filters are available for
diagnostics, blockers, acknowledgements, actions, and safety-only review.

## 7. Summary/Readiness Rendering

The CLI renders state, readiness, disabled/future action state, requested state,
preview availability, blocker count, acknowledgement count,
ready-for-future-only state, accepted-for-session-review state, and honesty flags
for no validation, no validation failure, no ProjectSchema mutation, no
persistence write, no activation, no trust restoration, no discovery, no solver
execution, no issue/release mutation, and no certification.

## 8. Preconditions And Blockers Rendering

The CLI renders missing preview, reader-blocked diagnostics, view-model-blocked
diagnostics, missing acknowledgements, stale-source/re-preview requirements,
conflict/shared-stack review, unsafe claims, unsupported schema, migration
requirements, unredacted-path blocks, secret-like value blocks, trust-policy
changes, source-fingerprint changes, and acceptance policy changes.

## 9. Acknowledgement Rendering

The CLI renders all required acknowledgement identifiers with required,
satisfied, expired, and blocking state. The acknowledgement rows explicitly state
that acknowledgement is not validation evidence and not trust restoration.

## 10. Acknowledgement Expiry Rendering

The CLI renders expiry reasons for reload, source fingerprint change, schema
version change, unsafe claim appearance, trust policy change, future discovery
refresh result, file reader policy change, GUI file-dialog policy change, CLI
explicit-path policy change, acceptance policy change, ProjectSchema policy
change, and validation issue state change.

## 11. Accepted-State Scope Rendering

Accepted-for-session-review rows are rendered as session/review scoped,
untrusted by default, not persistence, not ProjectSchema state, not validation
evidence, not validation failure, not automatic activation, not trust
restoration, and not an override of built-ins.

## 12. Reader And Preview Provenance Rendering

The CLI renders supplied provenance rows when present in the view-model mapping:
redacted source display, source id, provenance label, trust label, source
fingerprint-change state, untrusted-by-default state, built-in authority state,
and trust-label-not-certification state. Raw absolute paths, secrets, tokens,
API keys, and full file contents are not displayed by the deterministic samples.

## 13. Schema/Migration Rendering

The CLI renders payload-kind and schema-version requirements, unsupported schema
blocking, migration-required blocking, the fact that schema mismatch is not
validation failure, and the boundary between reload persistence schema and
ProjectSchema. The CLI does not repair or migrate files.

## 14. Redaction/Privacy Rendering

The CLI renders that raw paths are hidden by default, basename/hash/source-id
display is preferred, home directories and environment values are blocked,
secret-like values are blocked, future explicit policy is required for
unredacted path allowances, fingerprints are not trust signals, diagnostics use
redacted context, and accepted state must never store secrets as truth.

## 15. Candidate Lifecycle Rendering

The CLI renders that inactive preview remains review-only, persisted active
requires future activation review, deactivated remains a review state,
reactivation routes to future activation review, discovery-refresh state remains
review state, automatic activation is absent, trust restoration is absent, and
accepted state does not override built-ins.

## 16. Stale-Source/Re-Preview Rendering

The CLI renders that old previews are not silently trusted, missing/moved/changed
sources require re-preview, the acceptance CLI does not inspect referenced source
files, stale-source state is not validation failure, re-preview remains
future-gated, and future discovery-refresh results may expire acknowledgements.

## 17. Conflict/Shared-Stack Rendering

The CLI renders conflicts as visible, built-ins as authoritative by default,
accepted state as non-overriding, shared-stack warnings as visible, conflict
resolution as out of scope, and future policy as required.

## 18. Unsafe-Claim Rendering

The CLI renders unsafe claims as visible and blocked data, not truth. Validation
success/failure, issue closure, release mutation, bundled solver, dependency
installation, solver execution, trust restoration, and certification claims are
blocked.

## 19. Evidence/History Rendering

The CLI renders deactivation/reactivation history as retained,
historical evidence as reference-only, skipped-missing as skipped-missing,
accepted state as not validation evidence, no evidence deletion or rewrite, and
no issue closure implied.

## 20. Diagnostics Rendering

The CLI renders `OSPMG_RELOAD_ACCEPTANCE_*` diagnostics from the view-model and
also lists the reserved acceptance diagnostic vocabulary for review visibility.

## 21. Non-Action Flags Rendering

The CLI renders false safety rows for runtime reload acceptance, persistence
write, ProjectSchema mutation, default reload path, background reload, directory
scan, network fetch, plugin package import, CLI subprocess use, reloadable
bundle creation, export/report file creation, clipboard/report/open-folder
behavior, live discovery, passive refresh, validation execution, solver
execution, dependency install/uninstall, solver uninstall, candidate activation,
trust restoration, issue/release/tag/asset mutation, version bump,
validation-pass/fail claims, issue-closure claims, bundled-solver claims, and
certification claims.

## 22. Disabled/Future Action Rendering

The CLI renders disabled/future-only actions for request acceptance,
accept-for-session-review, accept-as-trusted, activate reloaded candidate,
refresh discovery, validate solver, execute solver, install/uninstall
dependency, uninstall solver, mutate ProjectSchema, persist state, create export
summary, create report file, create reloadable bundle, copy to clipboard, attach
to report, open output folder, close issue, mutate release, push tag, upload
asset, claim validation success, claim validation failure, and claim
certification.

## 23. Exit-Code Policy

Review commands return `0` when rendering completes. Exit code `0` means command
completion only; it is not validation success, validation failure, runtime
acceptance, issue closure, release mutation, or certification. `accept-future`
returns `2` because acceptance mutation is disabled/future-only.

## 24. Safety Guidance

The CLI prints guidance that CLI acceptance review is not runtime acceptance,
preview success is not acceptance, command success is not acceptance, exit code
`0` is not validation success or validation failure, readiness is not validation
evidence or validation failure, accepted-for-session-review remains untrusted by
default, trust labels are not certification, skipped-missing remains
skipped-missing, live issues `#6` through `#11` remain open, and
prepared-machine validation remains separate.

## 25. Relationship To Reload Acceptance CLI Design

This implementation follows OSW-EXP-122
([optional_solver_plugin_manifest_reload_acceptance_cli_design.md](optional_solver_plugin_manifest_reload_acceptance_cli_design.md)).
It implements the stdout-first review surface that design described while
preserving the design's non-actions and disabled/future acceptance mutation.

## 26. Relationship To Reload Acceptance View-Model

The CLI consumes OSW-EXP-119
`OptionalSolverPluginManifestReloadAcceptanceViewModel` records and their
`to_mapping()` representation. It does not edit the view-model source and does
not add independent acceptance policy.

## 27. Relationship To Reload Acceptance GUI Panel

The CLI is a sibling renderer to the OSW-EXP-121 GUI acceptance panel. Both
render supplied acceptance view-model records. The CLI does not call GUI code and
the GUI does not become a CLI subprocess bridge.

## 28. Relationship To Reload CLI Explicit-Path Preview

The OSW-EXP-115 `load-preview --path` command remains reader-first and
preview-only. This acceptance CLI accepts no path, invokes no reader, and does
not infer acceptance from preview command success.

## 29. Relationship To State Writer/Persistence

The CLI writes no state files, settings files, schema files, export files,
report files, reloadable bundles, or release assets. Persisted acknowledgement
or accepted-state storage remains future-gated.

## 30. Relationship To ProjectSchema

Accepted reload review state is not ProjectSchema state. The CLI mutates no
ProjectSchema, produces no ProjectSchema validation evidence, and does not
repair, migrate, or persist project data.

## 31. Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. CLI acceptance review is not optional
solver validation, not skipped-missing success, not validation failure, not
issue closure, not release evidence, and not certification evidence.

## 32. Security/Privacy Review

The implementation is path-free, reader-free, GUI-free, subprocess-free,
network-free, discovery-free, validation-free, solver-free, and persistence-free.
It renders redacted deterministic samples and blocks unsafe claims as data. It
does not display secrets, tokens, API keys, home directories, environment
values, or full file contents.

## 33. Non-Actions

This gate adds no runtime reload acceptance, active acceptance mutation, file IO,
file reading, file parsing, reader invocation, GUI behavior, GUI subprocess use,
reload file-reader source edit, reload view-model source edit, reload acceptance
view-model source edit, persistence write, ProjectSchema mutation, default
reload path, background reload, directory scan, network fetch, plugin package
import, reloadable bundle, export file, report file, clipboard behavior, report
attachment, open-output-folder behavior, live discovery, passive refresh,
validation execution, solver execution, dependency installation, dependency
uninstall, solver uninstall, automatic activation, trust restoration, issue
mutation, release mutation, tag mutation, asset mutation, version bump,
validation-pass claim, validation-fail claim, issue-closure claim,
bundled-solver claim, or certification claim.

## 34. Testing Strategy

Focused tests cover module import, main dispatcher registration, default
unavailable/no-preview state, explain, preview, summary, blockers,
acknowledgements, expiry, diagnostics, actions, safety, deterministic JSON,
non-action flags, disabled/future actions, unsafe claim denials, representative
sample/not-requested/blocked/ready/accepted states, `accept-future` exit code
`2`, review-command exit code `0`, no `--path`, redaction/secret suppression,
AST source guardrails, and no output/runtime file creation.

Continuity tests cover the acceptance view-model, acceptance GUI panel,
acceptance CLI design docs, and reload CLI explicit-path preview.

## 35. Future Gates

OSW-EXP-124 may design optional solver plugin manifest reload acceptance
persistence. Future runtime acceptance, accepted-state persistence,
activation/discovery review consumption, ProjectSchema integration,
prepared-machine optional validation, issue/release workflow, export/report
behavior, reloadable bundles, and certification remain separately gated.

## 36. Follow-up: Acceptance Persistence Design (OSW-EXP-124)

OSW-EXP-124 designs the future persistence boundary for acceptance UX review
state
([optional_solver_plugin_manifest_reload_acceptance_persistence_design.md](optional_solver_plugin_manifest_reload_acceptance_persistence_design.md)).
The CLI remains review-only and path-free: the persistence design adds no CLI
source edits, no CLI behavior, no writer invocation, no persistence writes, no
runtime reload acceptance, no ProjectSchema mutation, no file IO, no reader
invocation, no discovery, no validation, no solver execution, no activation, no
trust restoration, no issue/release/tag/asset mutation, and no certification
claims.

## 37. Follow-up: Acceptance Persistence ViewModel (OSW-EXP-125)

OSW-EXP-125 adds a pure in-memory reload acceptance persistence view-model
([optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel.md](optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel.md)).
The CLI implementation remains a stdout-first acceptance review surface and does
not invoke persistence behavior.

The persistence view-model consumes supplied acceptance records only and remains
future-writer-only. It adds no file IO, reader/writer invocation, CLI behavior,
GUI behavior, subprocess use, persistence write, ProjectSchema mutation,
runtime reload acceptance, discovery, validation, solver execution, activation,
trust restoration, issue/release/tag/asset mutation, or certification claim.

## 38. Follow-up: Acceptance Persistence Writer (OSW-EXP-126)

OSW-EXP-126 adds an explicit reload acceptance persistence writer
([optional_solver_plugin_manifest_reload_acceptance_persistence_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_implementation.md)).
The CLI review surface remains stdout-first and non-writing; it does not invoke
the writer, accept writer target paths, or convert review commands into
persistence commands.

The writer remains a separate local API with dry-run-first planning, explicit
target paths, caller acknowledgement for actual writes, redacted diagnostics,
and no runtime reload acceptance, ProjectSchema mutation, discovery,
validation, solver execution, activation, trust restoration,
issue/release/tag/asset mutation, validation claim, or certification claim.

## 39. Follow-up: Acceptance Persistence CLI Design (OSW-EXP-127)

OSW-EXP-127 designs a separate reload acceptance persistence CLI
([optional_solver_plugin_manifest_reload_acceptance_persistence_cli_design.md](optional_solver_plugin_manifest_reload_acceptance_persistence_cli_design.md)).
That future command family is distinct from this acceptance review CLI: this
CLI remains non-writing and does not invoke persistence behavior.

The persistence CLI design gate adds no CLI source edits, no writer invocation,
no file writes, no input state-file reading or parsing, no reload file-reader
invocation, no state-writer invocation, no GUI behavior, no subprocess use, no
runtime reload acceptance, no ProjectSchema mutation, no discovery, validation,
solver execution, activation, trust restoration, issue/release/tag/asset
mutation, validation claim, or certification claim.
