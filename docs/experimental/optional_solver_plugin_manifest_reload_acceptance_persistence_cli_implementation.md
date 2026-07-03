# Optional Solver Plugin Manifest Reload Acceptance Persistence CLI Implementation

## 1. Status

Experimental reload acceptance persistence CLI implemented.

- Stdout-first.
- Dry-run planning only.
- `write-future` disabled and future-only.
- write-future disabled for actual writes.
- No actual CLI writes.
- No runtime reload acceptance.
- No active acceptance mutation.
- No ProjectSchema mutation.
- No input state-file reading.
- No input state-file parsing.
- No reload file-reader invocation.
- No OSW-EXP-102 state-writer invocation.
- No GUI behavior.
- No GUI subprocess.
- No subprocess use.
- No default target path.
- No background write.
- No directory scan.
- No network fetch.
- No plugin package import.
- No discovery/validation/solver execution.
- No automatic activation.
- No trust restoration.
- No issue/release/tag/asset mutation.
- No validation-pass, validation-fail, issue-closure, bundled-solver, or
  certification claim.

## 2. Purpose

OSW-EXP-128 implements the OSW-EXP-127 CLI review surface so terminals and CI
logs can inspect reload acceptance persistence readiness and dry-run writer
plans without performing persistence writes or runtime acceptance.

## 3. Public Command And Module Names

The command family is:

`python -m osw.cli optional-solver-plugin-manifest-reload-acceptance-persistence <subcommand>`

The module is
`osw.cli.optional_solver_manifest_reload_acceptance_persistence`.

The supported subcommands are `explain`, `preview`, `plan`, `diagnostics`,
`acknowledgements`, `expiry`, `storage`, `actions`, `safety`, and
`write-future`.

## 4. State Source Policy

State sources are deterministic in-memory
`OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel` records. The
CLI exposes unavailable, empty, sample, blocked, ready, and writer-ready samples.
It does not accept a reload-state input path and does not read or parse input
state files.

## 5. Subcommand Behavior

`explain` renders the boundary. `preview` renders all sections. `plan` invokes
the OSW-EXP-126 writer only through dry-run planning. `diagnostics`,
`acknowledgements`, `expiry`, `storage`, `actions`, and `safety` render focused
sections. `write-future` returns `2`, renders disabled/future-only guidance, and
does not call an actual writer.

## 6. Output Modes

Text output is stable and stdout-first. JSON output uses sorted keys and stable
indentation. Neither output mode creates export files, report files, reloadable
bundles, clipboard entries, report attachments, or open-folder behavior.

## 7. Dry-Run/Write-Plan Behavior

`plan` constructs `ReloadAcceptancePersistenceWriteRequest` with `dry_run=True`
and calls `plan_reload_acceptance_persistence_write`. The result renders status,
redacted target display, dry-run state, planned/written booleans, payload kind,
schema version, byte count, SHA-256, blockers, diagnostics, non-action flags,
and safety guidance. The target file is not created.

## 8. `write-future` Disabled Behavior

`write-future` is intentionally disabled and future-only. It returns exit code
`2` and states that no file is created even when `--target` is supplied. It does
not call the writer with `dry_run=False`.

## 9. Target Policy

`--target` is accepted only for `plan` and `write-future` review. There is no
default target path, no hidden persistence, no background write, and no
directory scan. Target display is redacted by default.

## 10. Request/Result Rendering

The CLI renders request mode, target-required/selected state, allow-replace,
caller acknowledgement, writer status, planned/written booleans, payload kind,
schema version, deterministic hash, blockers, warnings, diagnostics, and exit
semantics. Command success means rendering completed only.

## 11. Acknowledgement Rendering

The CLI renders required persistence acknowledgements, including
`acceptance_not_validation`, `acceptance_not_validation_failure`,
`acceptance_not_trust_restoration`, `acceptance_not_automatic_activation`,
`acceptance_not_discovery_success`, `acceptance_not_dependency_install`,
`acceptance_no_solver_execution`, `acceptance_not_issue_closure`,
`acceptance_not_release_mutation`, `acceptance_not_certification`,
`acceptance_not_persistence_write`,
`acceptance_not_project_schema_mutation`, `redaction_reviewed`,
`unredacted_paths_blocked`, `stale_source_requires_repreview`,
`untrusted_source_remains_untrusted`,
`activation_review_required_after_acceptance`, `no_discovery_execution`,
`no_plugin_package_import`, `no_validation_execution`, `no_solver_execution`,
`trust_label_not_certification`, and `persisted_acknowledgements_may_expire`.

Acknowledgements are not validation evidence, not validation failure, and not
trust restoration.

## 12. Expiry Rendering

The CLI renders expiry reasons for reload, source fingerprint change, schema
version change, unsafe claim appearance, trust policy change, future
discovery-refresh result, file-reader policy change, GUI file-dialog policy
change, CLI explicit-path policy change, acceptance policy change,
ProjectSchema policy change, validation issue state change, persistence schema
change, and persistence storage-policy change.

## 13. Schema/Migration Rendering

Output shows payload kind, schema id, schema version, support state, and
migration state. Unsupported schema and migration-required states block future
persistence. Schema mismatch is not validation failure.

## 14. Redaction/Privacy Rendering

Raw paths are hidden by default. Basename/source-id/display-name/hash display is
preferred. Home directories, environment variables, secrets, tokens, API keys,
and bearer/password-like values are redacted or blocked.

## 15. Provenance Rendering

Provenance rows are rendered as redacted, non-authoritative, untrusted-by-default
context. Fingerprints are not trust signals. Full file content, raw absolute
paths, secrets, tokens, and API keys are not displayed.

## 16. Candidate Lifecycle Rendering

Inactive previews remain review-only. Persisted active or reactivation concepts
still require future activation review. Persisted review state does not override
built-ins and does not restore trust.

## 17. Stale-Source/Re-Preview Rendering

Old previews are not silently trusted. Missing, moved, or changed sources
require re-preview. The CLI does not inspect referenced source files, and
stale-source state is not validation failure.

## 18. Conflict/Shared-Stack Rendering

Conflicts and shared-stack warnings remain visible. Built-ins win by default.
The CLI does not resolve conflicts, install stacks, uninstall stacks, or choose
trusted winners.

## 19. Unsafe-Claim Rendering

Unsafe validation success, validation failure, issue closure, release mutation,
bundled-solver, dependency installation, solver execution, trust restoration, and
certification claims are visible as blocked diagnostics and are not rendered as
truth.

## 20. Evidence/History Rendering

Evidence/history rows are reference-only. Skipped-missing remains
skipped-missing. The CLI does not delete, rewrite, or elevate evidence and does
not imply issue closure.

## 21. Diagnostics Rendering

The CLI renders `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_*` diagnostics plus
supplied view-model and dry-run writer `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_*`
diagnostics. Diagnostics are not validation results.

## 22. Non-Action Flags Rendering

JSON and text include false/non-action rows for actual CLI writes, writer
`dry_run=False`, input state-file reading/parsing, reload file-reader
invocation, OSW-EXP-102 state-writer invocation, runtime acceptance,
ProjectSchema mutation, discovery, validation, solver execution, activation,
trust restoration, issue/release/tag/asset mutation, version bump,
validation-pass/fail claim, issue-closure claim, bundled-solver claim, and
certification claim.

## 23. Disabled/Future Action Rendering

The CLI renders request persistence, dry-run planning, write review-record,
persist acceptance record, acceptance, activation, discovery, validation,
execution, dependency, ProjectSchema, export/report/reloadable-bundle,
clipboard/report/open-folder, issue, release, tag, asset, validation-claim, and
certification action rows. Only dry-run planning is enabled.

## 24. Exit-Code Policy

Review commands return `0` when rendering completes, including blocked review
states. Exit code `0` is not validation success, not validation failure, not
runtime acceptance, not persistence write, not ProjectSchema mutation, not issue
closure, not release mutation, and not certification. `write-future` returns
`2`.

## 25. Relationship To OSW-EXP-127 Design

This gate implements the OSW-EXP-127 stdout-first, explicit-target,
dry-run-first CLI contract while preserving the design's no-write and
no-runtime-acceptance boundaries.

## 26. Relationship To OSW-EXP-126 Writer

The CLI uses the OSW-EXP-126 writer only through
`plan_reload_acceptance_persistence_write` with `dry_run=True`. It does not call
`write_reload_acceptance_persistence_record` and does not expose actual writer
behavior.

## 27. Relationship To OSW-EXP-125 Persistence View-Model

The OSW-EXP-125 persistence view-model remains the source of persistence
readiness, blockers, acknowledgements, expiry, storage policy, non-action flags,
disabled/future actions, provenance, evidence/history, and safety guidance.

## 28. Relationship To Reload Acceptance CLI/GUI

The OSW-EXP-123 acceptance CLI and OSW-EXP-121 GUI acceptance panel remain
review-only sibling surfaces. This CLI does not call GUI code and does not turn
acceptance review into runtime acceptance.

## 29. Relationship To Reload File Reader And Explicit-Path Preview

The OSW-EXP-113 reload file reader and OSW-EXP-115 explicit-path preview remain
reader/preview paths. This CLI does not read input state files, parse input
state files, or invoke the reload file reader.

## 30. Relationship To ProjectSchema

Persistence CLI output is not ProjectSchema state. The implementation imports no
ProjectSchema mutation path and does not describe dry-run planning as project
mutation.

## 31. Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. Persistence review and dry-run planning
are not prepared-machine validation, not validation success, not validation
failure, and not issue closure.

## 32. Security/Privacy Review

The CLI is explicit-target, redaction-first, dry-run-only, no-default-path, and
no-directory-scan. Raw target paths and secret-like values are redacted from
text and JSON output.

## 33. Non-Actions

This gate performs no actual CLI write, no writer call with `dry_run=False`, no
runtime reload acceptance, no active acceptance mutation, no input state-file
reading/parsing, no reload file-reader invocation, no OSW-EXP-102 state-writer
invocation, no GUI behavior, no subprocess use, no ProjectSchema mutation, no
default/background write, no directory scan, no network fetch, no plugin package
import, no reloadable bundle creation, no export/report file creation, no
clipboard/report/open-folder behavior, no discovery, no validation, no solver
execution, no dependency install/uninstall, no automatic activation, no trust
restoration, no issue/release/tag/asset mutation, no version bump, no
validation-pass/fail claim, no issue-closure claim, no bundled-solver claim, and
no certification claim.

## 34. Testing Strategy

Focused unit tests cover module imports, dispatcher registration, default
unavailable state, explanation text, dry-run planning without target, dry-run
planning with target and no file creation, deterministic JSON, diagnostics,
acknowledgements, expiry, storage, actions, safety, `write-future`, absence of
`--path`, redaction/no secret leaks, source guardrails, and no created output or
runtime state files. Adjacent writer, persistence view-model, acceptance
view-model, acceptance CLI, acceptance panel, and state writer tests remain in
the required check set.

## 35. Future Gates

Future gates may design/implement GUI persistence review, ProjectSchema-safe
integration review, prepared-machine validation evidence, issue/release-safe
reporting, or a separately authorized actual CLI write surface. Each remains
separately gated and must preserve explicit-target, redaction-first,
acknowledgement-bound, non-authoritative, non-validation,
non-trust-restoration, non-activation, ProjectSchema-safe, issue/release-safe,
and certification-safe boundaries.

## 36. Follow-up: Persistence GUI Review Design (OSW-EXP-129)

OSW-EXP-129 designs a future display-only PySide review surface for reload
acceptance persistence planning and writer results
([optional_solver_plugin_manifest_reload_acceptance_persistence_gui_review_design.md](optional_solver_plugin_manifest_reload_acceptance_persistence_gui_review_design.md)).
The GUI design does not call this CLI, does not use a CLI subprocess, does not
invoke the writer, and does not write files. CLI success still does not imply
GUI persistence, runtime reload acceptance, ProjectSchema mutation, validation
evidence, issue closure, release mutation, or certification.

## 37. Follow-up: Persistence GUI Review Implementation (OSW-EXP-130)

OSW-EXP-130 implements the display-only persistence GUI review panel
([optional_solver_plugin_manifest_reload_acceptance_persistence_gui_review_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_gui_review_implementation.md)).
The GUI consumes supplied persistence view-model records and supplied writer
dry-run/result records only. It does not call this CLI, does not use a CLI
subprocess, does not invoke the writer, does not write files, does not accept
runtime reload, does not mutate ProjectSchema, does not run discovery,
validation, or solver execution, and does not mutate issues/releases or claim
certification.

## 38. Follow-up: Persistence GUI Write Design (OSW-EXP-131)

OSW-EXP-131 designs a future explicit-target, dry-run-first GUI write workflow
([optional_solver_plugin_manifest_reload_acceptance_persistence_gui_write_design.md](optional_solver_plugin_manifest_reload_acceptance_persistence_gui_write_design.md)).
The GUI write design does not call this CLI, does not use a CLI subprocess, and
does not make CLI success evidence of GUI persistence, runtime reload
acceptance, ProjectSchema mutation, validation evidence, issue closure, release
mutation, or certification. Any future GUI write remains separately gated and
must use the writer boundary directly rather than shelling out to the CLI.
