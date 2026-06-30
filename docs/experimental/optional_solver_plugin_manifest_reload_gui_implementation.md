# Optional Solver Plugin Manifest Reload GUI Implementation

## Status

Experimental reload GUI review panel implemented. The panel is
read-only/review-only over already-built reload view-model records. It has no
file dialog, no file reader/parser, no runtime reload behavior, no default
reload path, no background reload, no ProjectSchema mutation, no
discovery/validation/solver execution, no automatic activation, and no trust
restoration.

## Purpose

OSW-EXP-109 implements the review surface designed in OSW-EXP-108. The panel
lets future GUI entry points display OSW-EXP-107 reload view-model records while
keeping reload separate from file loading, validation evidence, validation
failure, trust restoration, automatic activation, discovery success,
ProjectSchema state, issue closure, release mutation, bundled solver support,
and certification.

## Public Module/Class Names

- `src/osw/gui/dialogs/optional_solver_plugin_manifest_reload_panel.py`
- `OptionalSolverPluginManifestReloadPanel`
- Lazy dialog export:
  `osw.gui.dialogs.OptionalSolverPluginManifestReloadPanel`

## GUI Flow

The panel is constructed with an already-built
`OptionalSolverPluginManifestReloadViewModel`. It renders the supplied records
immediately. `set_view_model()` and `refresh()` replace or redraw only supplied
view-model objects; they do not select files, read files, parse files, or run
reload.

## Data Input Policy

The panel consumes already-built reload view-model records only. It does not
accept a path as an instruction to load data. It does not inspect the
filesystem, scan directories, fetch network manifests, import plugin packages,
run discovery, run validation, execute solvers, mutate ProjectSchema, activate
candidates, restore trust, close issues, or mutate releases/tags/assets.

## Rendered Sections

The panel renders these sections:

- Summary / readiness
- Source / provenance
- Schema / migration
- Candidates
- Acknowledgements / expiry
- Redaction / privacy
- Stale sources / re-preview
- Conflicts / shared stack
- Unsafe claims
- Evidence / history
- Trust
- Diagnostics
- Actions
- Safety guidance

## Summary/Readiness Rendering

The summary displays state, readiness, payload kind/version, writer version,
source display, source redaction flag, counts, blocker/warning counts, and
honesty flags. The honesty flags remain false for validation evidence,
validation failure, trust restoration, automatic activation, discovery,
validation, solver execution, ProjectSchema mutation, issue closure, release
mutation, and certification.

## Source/Provenance Rendering

Source rows show source id, source type, redacted display reference, redaction
flag, provenance label, trust label, user/plugin untrusted-by-default flag,
built-in authoritative-by-default flag, fingerprint-not-trust-signal flag, and
trust-label-not-certification flag.

## Schema/Migration Rendering

Schema rows show required payload kind/version, supported-schema state,
migration-required state, blocker state, schema-mismatch-not-validation-failure,
and schema-model-separate-from-ProjectSchema. Migration remains future-gated.

## Candidate Lifecycle Rendering

Candidate rows show persisted lifecycle state and reload review state. Inactive
preview remains review-only. Persisted active and reactivation states require
future activation review. Deactivated candidates remain deactivated review
state. Discovery-refresh state remains review state. The panel performs no
automatic activation and no trust restoration.

## Acknowledgement/Expiry Rendering

Acknowledgement rows show required acknowledgement ids, labels, required state,
satisfied state, expired state, blocker state, and expiry reasons. Expiry
reasons include reload, source fingerprint change, schema version change,
unsafe claim appearance, trust policy change, and future discovery-refresh
result.

## Redaction/Privacy Rendering

Redaction rows show raw-path hiding, redaction review state, unredacted-path
blockers, secret-like content blockers, fingerprint-not-trust-signal state, and
redaction-before-activation-review state. The panel does not leak raw paths
unless the supplied view-model already intentionally contains a redacted display
value.

## Stale-Source/Re-Preview Rendering

Stale-source rows show stale state, re-preview requirements, old-preview-not-
silently-trusted state, no-source-file-IO state, and stale-source-not-validation-
failure state. The panel does not read source files or silently fix stale
sources.

## Conflict/Shared-Stack Rendering

Conflict rows show conflict id, candidate id, conflict type, built-ins-win-by-
default state, persisted-state-does-not-override-built-ins state, shared-stack
warning visibility, reload-does-not-resolve-conflict state, and blocker state.

## Unsafe-Claim Rendering

Unsafe-claim rows show claim id, candidate id, claim type, claim text, blocked
state, and not-reloaded-as-truth state. Unsafe claims include validation
success, validation failure, issue closure, release mutation, bundled solver,
dependency installation, solver execution, trust restoration, and certification
claims.

## Evidence/History Rendering

Evidence/history rows show deactivation/reactivation history retention,
historical evidence as reference only, skipped-missing preservation, reload-is-
not-validation-evidence state, no evidence deletion/rewrite, and no issue
closure implication.

## Diagnostics Rendering

Diagnostics rows show `OSPMG_RELOAD_*` severity, code, message, blocker state,
related section/context, and suggested fix. Diagnostics are review guidance; the
panel does not convert them into validation success or validation failure.

## Action-State Rendering

The Actions section renders disabled/future-only rows and disabled buttons for
file read, file parse, migration, accepting reload as trusted, activation,
discovery refresh, validation, solver execution, dependency install/uninstall,
solver uninstall, ProjectSchema mutation, export summary, report file,
reloadable bundle, clipboard, report attachment, open-output-folder, issue
closure, release mutation, tag push, asset upload, validation success/failure
claim, and certification claim.

## Safety Guidance

Safety guidance explicitly states review-only behavior and confirms no file
dialog, no file reader/parser, no file reading/parsing, no runtime reload, no
default reload path, no background reload, no reloadable bundle creation, no
export/report file creation, no clipboard behavior, no report attachment, no
open-output-folder behavior, no CLI behavior, no ProjectSchema mutation, no
live discovery, no passive refresh, no plugin package import, no directory
scan, no network fetch, no validation execution, no solver execution, no
dependency installation, no dependency uninstall, no solver uninstall, no
automatic activation, no trust restoration, no issue/release/tag/asset
mutation, no version bump, no validation-pass claim, no validation-fail claim,
no issue-closure claim, no bundled-solver claim, and no certification claim.

## Relationship To Reload View-Model

The panel consumes OSW-EXP-107 view-model records and does not mutate them. GUI
and CLI reload surfaces should share semantics through the reload view-model,
not through widgets. File-reader/parser behavior remains separate.

## Relationship To Persistence GUI/State Writer

The state writer writes explicit local UX state files through caller-supplied
paths. Persistence GUI reviews write-plan/persistence state. Reload GUI reviews
already-built reload view-model records and writes no files.

## Relationship To Export-Summary GUI/CLI

Export summary is human-review output. Reload GUI is machine-readable UX-state
review. Export summaries are not reloadable bundles. The reload panel creates
no reports, no export files, and no reloadable bundles.

## Relationship To ProjectSchema

There is no ProjectSchema mutation. Reloaded state is not ProjectSchema state
and is not project validation evidence. Future ProjectSchema integration
requires a separate gate.

## Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. Reload GUI does not close issues. Reload
GUI output is not live optional validation. Skipped-missing remains
skipped-missing. Prepared-machine validation remains separate.

Downstream issue-boundary phrase: issues `#6` through `#11` remain open.

## Non-Actions

Required boundary phrases for downstream checks: no file dialog; no file
reader/parser; no runtime reload behavior; no ProjectSchema mutation;
no discovery/validation/solver execution; no automatic activation; no trust
restoration; no CLI behavior; no reloadable bundle creation; no export/report
file creation; no clipboard behavior.

Compact downstream phrase: no export/report file creation.

This gate does not add file dialog behavior, file reader/parser implementation,
runtime file reading, runtime state parsing, default reload path, background
reload, reloadable bundle creation, export file creation, report file creation,
clipboard behavior, report attachment, open-output-folder behavior, CLI
behavior, ProjectSchema mutation, live discovery, passive refresh, plugin
package import, directory scan, network fetch, validation execution, solver
execution, dependency installation, dependency uninstall, solver uninstall,
automatic activation, trust restoration, issue mutation, release mutation, tag
mutation, asset mutation, version bump, validation-pass claim, validation-fail
claim, issue-closure claim, bundled-solver claim, or certification claim.

## Testing Strategy

Focused GUI tests cover guarded import/lazy export, unavailable and ready
view-model rendering, schema/migration blockers, redaction/unredacted/secret
blockers, acknowledgement expiry blockers, stale-source/re-preview blockers,
conflict/shared-stack rows, unsafe-claim rows, evidence/history rows,
trust/provenance rows, `OSPMG_RELOAD_*` diagnostics, disabled/future action
states, safety guidance, `set_view_model()` refresh, view-model immutability,
no file creation, and source checks for forbidden GUI/file/CLI/discovery/
validation/solver/project behavior.

## Follow-up: GUI File-Dialog Design (OSW-EXP-116)

OSW-EXP-116 designs a future GUI file-dialog bridge from explicit user file
selection to the OSW-EXP-113 reader and OSW-EXP-107 reload view-model review.
That design keeps this panel pure and unchanged: no GUI source edits, no file
dialog widgets, no file opening behavior, no runtime file reading/parsing, no
default/background reload, no CLI subprocess use, no ProjectSchema mutation, no
discovery/validation/solver execution, no activation, no trust restoration, no
issue/release/tag/asset mutation, and no certification claim.

## Follow-up: GUI File-Dialog Implementation (OSW-EXP-117)

OSW-EXP-117 adds
`OptionalSolverPluginManifestReloadFileDialogPanel` as a separate outer
chooser/controller around this review panel. The wrapper may invoke the
OSW-EXP-113 reader after an explicit user-selected path, but this original
`OptionalSolverPluginManifestReloadPanel` remains a pure renderer over supplied
reload view-model records and still has no direct file dialog, file reader,
runtime reload acceptance, ProjectSchema mutation, discovery/validation/solver
execution, activation, trust restoration, issue/release/tag/asset mutation, or
certification behavior.

## Future Gates

Future gates remain separate:

- `OSW-EXP-110_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_CLI_DESIGN`
- `OSW-EXP-111_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_CLI_IMPLEMENTATION`
- `OSW-EXP-112_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_FILE_READER_DESIGN`
- `OSW-EXP-113_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_FILE_READER_IMPLEMENTATION`
- `OSW-EXP-116_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_FILE_DIALOG_DESIGN`
- `OSW-EXP-117_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_FILE_DIALOG_IMPLEMENTATION`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` if a prepared
  machine is available
