# Optional solver plugin manifest export-summary view-model

## Status

Implemented in OSW-EXP-097 as a pure, side-effect-free, in-memory view-model.

This gate adds source and tests for
`src/osw/experimental/optional_solvers/plugin_manifest_export_summary_viewmodel.py`
and the public class
`OptionalSolverPluginManifestExportSummaryViewModel`.

Status boundaries:

- no file export
- no file writes
- no export file creation
- no clipboard behavior
- no report attachment
- no reloadable bundle creation
- no runtime persistence behavior
- no persistence writer
- no settings file creation
- no runtime state file creation
- no schema file creation
- no ProjectSchema mutation
- no GUI behavior
- no CLI behavior
- no reload behavior
- no source behavior mutation
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

## Purpose

The view-model converts supplied optional solver plugin manifest UX state into a
redacted, human-reviewable, non-authoritative in-memory export summary. It exists
so future GUI, CLI, report, support-summary, file-export, clipboard, and bundle
gates have a deterministic record contract without granting permission to write,
persist, reload, validate, execute, trust, or mutate anything.

OSW-EXP-100 defines the future state writer as a separate design-only contract.
The export-summary view-model remains non-writing and non-persistent; it does
not become a state writer, runtime state file creator, settings file creator,
schema file creator, reload path, ProjectSchema integration, GUI/CLI action,
automatic activation, trust restoration, discovery execution, validation
execution, solver execution, issue mutation, release mutation, tag mutation,
asset mutation, version bump, validation-pass/fail claim, or certification
claim.

An export summary remains:

- redaction-first
- provenance-preserving
- acknowledgement-aware
- history-retaining
- non-validating
- non-persistent
- non-reloadable by default
- non-writing
- non-installing
- non-executing
- non-mutating
- issue/release-safe

## Public API

Public construction helpers:

- `OptionalSolverPluginManifestExportSummaryViewModel.empty`
- `OptionalSolverPluginManifestExportSummaryViewModel.unavailable`
- `OptionalSolverPluginManifestExportSummaryViewModel.from_records`
- `OptionalSolverPluginManifestExportSummaryViewModel.from_persistence_viewmodel`
- `OptionalSolverPluginManifestExportSummaryViewModel.from_persistence_schema_model`
- `OptionalSolverPluginManifestExportSummaryViewModel.redaction_required`
- `OptionalSolverPluginManifestExportSummaryViewModel.stale_source_repreview_required`
- `OptionalSolverPluginManifestExportSummaryViewModel.unsafe_claim_blocked`
- `build_optional_solver_plugin_manifest_export_summary_viewmodel`
- `redact_optional_solver_plugin_manifest_export_summary_source_reference`
- `render_optional_solver_plugin_manifest_export_summary`
- `summarize_optional_solver_plugin_manifest_export_summary_viewmodel`
- `explain_optional_solver_plugin_manifest_export_summary_viewmodel`

All helpers are in-memory only. They do not inspect path existence, read files,
write files, parse JSON from paths, import plugin packages, scan directories,
fetch URLs, run discovery, run validation, execute solvers, install or uninstall
dependencies, mutate ProjectSchema, mutate issues, mutate releases, mutate tags,
or upload assets.

## Record model

The view-model exposes frozen records for:

- header state and deterministic counts
- sections
- source/provenance rows
- candidate rows
- acknowledgement rows
- diagnostic rows
- redaction/privacy rows
- stale-source/re-preview rows
- conflict/shared-stack rows
- unsafe-claim rows
- evidence/history rows
- limitation rows
- non-action flags
- disabled/future action states

`to_sections()` returns the section records. `to_text_lines()` returns redacted
text lines in memory. `to_mapping()` returns a JSON-like mapping in memory. None
of these helpers creates an export file or report attachment.

## Readiness

The readiness values are:

- `unavailable_no_state`
- `unavailable_no_explicit_request`
- `blocked_acknowledgement`
- `blocked_redaction_review`
- `blocked_unredacted_path`
- `blocked_stale_source_repreview`
- `blocked_conflict`
- `blocked_shared_stack_warning`
- `blocked_unsafe_claim`
- `ready_preview_only`
- `future_file_export_required`
- `future_clipboard_required`
- `future_report_attachment_required`
- `future_reloadable_bundle_required`
- `error`

`ready_preview_only` means the supplied state can be previewed in memory. It does
not mean file export, clipboard copy, report attachment, reloadable-bundle
creation, persistence, reload, ProjectSchema mutation, automatic activation,
trust restoration, discovery, validation, solver execution, issue closure,
release mutation, tag mutation, asset mutation, validation evidence, or
certification.

## Acknowledgements

The required acknowledgement identifiers are:

- `export_not_validation`
- `export_not_persistence`
- `export_not_reloadable_bundle`
- `export_not_trust_restoration`
- `export_not_install`
- `export_no_solver_execution`
- `export_not_issue_closure`
- `export_not_release_mutation`
- `redaction_reviewed`
- `unredacted_paths_blocked`
- `stale_source_requires_repreview`
- `untrusted_source_remains_untrusted`
- `no_discovery_execution`
- `no_plugin_package_import`
- `trust_label_not_certification`

Missing acknowledgements are visible blockers. Satisfied acknowledgements only
allow a ready in-memory preview when no other blocker is present; they do not
grant trust, persistence, reloadability, validation evidence, installation,
solver execution, issue closure, release mutation, or certification.

## Diagnostics

The reserved and implemented diagnostic vocabulary is:

- `OSPMG_EXPORT_SUMMARY_NOT_IMPLEMENTED`
- `OSPMG_EXPORT_SUMMARY_ACK_REQUIRED`
- `OSPMG_EXPORT_SUMMARY_NOT_VALIDATION`
- `OSPMG_EXPORT_SUMMARY_NOT_PERSISTENCE`
- `OSPMG_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE`
- `OSPMG_EXPORT_SUMMARY_NOT_TRUST_RESTORE`
- `OSPMG_EXPORT_SUMMARY_NO_INSTALL`
- `OSPMG_EXPORT_SUMMARY_NO_SOLVER_EXECUTION`
- `OSPMG_EXPORT_SUMMARY_NOT_ISSUE_CLOSURE`
- `OSPMG_EXPORT_SUMMARY_NOT_RELEASE_MUTATION`
- `OSPMG_EXPORT_SUMMARY_REDACTION_REQUIRED`
- `OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED`
- `OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED`
- `OSPMG_EXPORT_SUMMARY_UNTRUSTED_SOURCE`
- `OSPMG_EXPORT_SUMMARY_CONFLICT_BLOCKED`
- `OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM`
- `OSPMG_EXPORT_SUMMARY_EVIDENCE_RETAINED`
- `OSPMG_EXPORT_SUMMARY_HISTORY_RETAINED`
- `OSPMG_EXPORT_SUMMARY_NO_DISCOVERY_EXECUTION`
- `OSPMG_EXPORT_SUMMARY_NO_PLUGIN_IMPORT`
- `OSPMG_EXPORT_SUMMARY_FUTURE_GATE`

These diagnostics are review signals only. They are not validation-pass evidence
and not validation-fail evidence.

## Source, trust, and provenance

Source rows preserve supplied source ids, source types, labels, trust labels,
summary kind, persistence kind, fingerprint display text, stale-source state, and
diagnostics. Source references are redacted by default; path-like references are
shortened to their final segment and raw/unredacted references are represented as
blocked. Secret-like values are replaced by a redacted placeholder.

User-selected and plugin-provided manifests remain untrusted by default. Built-in
manifest rows can be represented as authoritative by default. A trust label is
not certification and a fingerprint is not a trust signal.

## Candidate summary

Candidate rows preserve stack id, display name, source id/type, trust label,
activation state, deactivation state, reactivation state, discovery-refresh
state, persistence state, export-summary state, readiness, blockers, warnings,
required acknowledgements, diagnostics, stale-source state, redaction status,
built-in relationship, shared-stack indicators, deactivation history state,
reactivation history state, historical evidence state, and validation-evidence
state.

Candidate rows explicitly keep:

- `automatic_activation_implied=false`
- `trusted_source_implied=false`
- `validation_evidence_implied=false`
- `issue_closure_implied=false`

## Redaction and stale-source policy

Redaction/privacy rows show whether a raw reference was supplied, the redacted
display reference, redaction status, redaction-required state, unredacted-path
blocking, review state, secret-like content blocking, privacy warning, and the
fact that fingerprints are not trust signals.

Stale-source rows state that old preview data is not silently trusted and that no
file IO, file restoration, file rewrite, or file deletion is performed. Missing,
moved, or changed sources require re-preview or a future policy gate.

## Conflicts, unsafe claims, and evidence

Conflict/shared-stack rows keep built-ins winning by default, keep conflicts
visible, and state that exported user/plugin state does not override built-ins.
Unsafe-claim rows remain blocked and are never accepted by export summaries.

Evidence/history rows retain deactivation history, reactivation history, and
historical validation evidence. Skipped-missing remains skipped-missing. Export
summaries do not imply issue closure, validation success, validation failure, or
evidence deletion/rewrite.

## Non-action flags and action states

All non-action flags remain false, including file export, file writes, export
file creation, clipboard behavior, report attachment, reloadable bundle creation,
persistence, settings file creation, runtime state file creation, schema file
creation, ProjectSchema mutation, GUI behavior, CLI behavior, reload behavior,
automatic activation, trust restoration, file restoration/rewrite/deletion,
dependency install/uninstall, solver uninstall, plugin package import, directory
scan, network fetch, discovery execution, validation execution, solver
execution, issue mutation, issue closure, release mutation, tag mutation, asset
mutation, version bump, bundled-solver claim, and certification claim.

Unsafe or future actions are disabled or marked future-only:

- write export file
- copy to clipboard
- attach to report
- create reloadable bundle
- persist state
- reload state
- mutate ProjectSchema
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

Each requires a future gate.

## Relationship to prior gates

OSW-EXP-091 defined the export-summary design. OSW-EXP-092 supplied the pure
persistence view-model. OSW-EXP-093 supplied the pure in-memory persistence schema
model. OSW-EXP-095 supplied a review-only persistence GUI panel. OSW-EXP-096
supplied the persistence CLI design.

OSW-EXP-097 binds the design to deterministic in-memory records and adapters
from the persistence view-model/schema model. It does not mutate those prior
models or their source behavior.

OSW-EXP-098 follows this view-model with a design-only future export-summary GUI
review contract. It does not modify this module and does not add GUI
implementation, file export, file writes, export file creation, report file
creation, clipboard behavior, report attachment, open-output-folder behavior,
reloadable bundle creation, runtime persistence behavior, settings files,
runtime state files, schema files, ProjectSchema mutation, CLI behavior, reload
behavior, source mutation, automatic activation, trust restoration, file
restore/rewrite/delete behavior, dependency install/uninstall behavior, solver
uninstall behavior, plugin package import, directory scan, network fetch,
discovery execution, validation execution, solver execution, issue/release/tag
or asset mutation, version bump, validation-pass/fail claim, issue-closure
claim, bundled-solver claim, or certification claim.

OSW-EXP-099 implements a bounded PySide review panel over this view-model as
`OptionalSolverPluginManifestExportSummaryPanel`. The implementation does not
modify this view-model and keeps this module PySide/Qt-free. It adds no file
export, file writes, export file creation, report file creation, clipboard
behavior, report attachment, open-output-folder behavior, reloadable bundle
creation, runtime persistence behavior, settings files, runtime state files,
schema files, ProjectSchema mutation, CLI behavior, reload behavior, source
mutation, automatic activation, trust restoration, dependency install/uninstall
behavior, solver uninstall behavior, plugin package import, directory scan,
network fetch, discovery execution, validation execution, solver execution,
issue/release/tag/asset mutation, version bump, validation-pass/fail claim,
issue-closure claim, bundled-solver claim, or certification claim.

## Future gates

Future work remains separate:

- OSW-EXP-098 export-summary GUI design
- export-summary GUI implementation
- export-summary CLI design and implementation
- report/support-summary integration
- file export implementation
- clipboard implementation
- reloadable state bundle design and implementation
- persistence writer
- source integration
- discovery integration
- validation gates
- install/uninstall gates
- solver-execution gates
- issue/release/tag/asset gates

Live optional validation issues `#6` through `#11` remain open. Package metadata
remains `0.1.5rc1`. The public prerelease remains `v0.1.5-rc1`.
