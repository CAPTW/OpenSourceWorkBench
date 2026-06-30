# Optional Solver Plugin Manifest Reload CLI Design

## 1. Status

This gate is design-only.

It adds no reload CLI implementation, no CLI source edits, no command parser,
no command handler, no command registration, no runtime behavior, and no source
behavior mutation.

It adds no file dialog behavior, no file reader/parser implementation, no file
reading implementation, no file parsing implementation, no runtime file
reading, no runtime state parsing, no runtime reload behavior, no default
reload path, no background reload, no reloadable bundle creation, no export
file creation, no report file creation, no clipboard behavior, no report
attachment, no open-output-folder behavior, no GUI behavior, and no
ProjectSchema mutation.

It also adds no live discovery, no passive refresh, no plugin package import,
no directory scan, no network fetch, no validation execution, no solver
execution, no dependency installation, no dependency uninstall, no solver
uninstall, no automatic activation, no trust restoration, no issue mutation, no
release mutation, no tag mutation, no asset mutation, no version bump, no
validation-pass claim, no validation-fail claim, no issue-closure claim, no
bundled-solver claim, and no certification claim.

## 2. Purpose

This document defines a future command-line review surface for optional solver
plugin manifest reload state. The future surface is a headless, stdout-first,
review-only CLI contract over already-built OSW-EXP-107 reload view-model
records.

The design preserves the OSW-EXP-106 reload design, the OSW-EXP-107 reload
view-model, the OSW-EXP-108/109 reload GUI review boundary, the state-writer
and persistence CLI boundaries, export-summary CLI/GUI boundaries,
ProjectSchema boundaries, discovery boundaries, validation boundaries,
issue/release boundaries, and certification boundaries.

## 3. Current State Before Reload CLI

Reload design exists in
[optional_solver_plugin_manifest_reload_design.md](optional_solver_plugin_manifest_reload_design.md).
The pure reload view-model exists in
[optional_solver_plugin_manifest_reload_viewmodel.md](optional_solver_plugin_manifest_reload_viewmodel.md).
The reload GUI design and implementation exist in
[optional_solver_plugin_manifest_reload_gui_design.md](optional_solver_plugin_manifest_reload_gui_design.md)
and
[optional_solver_plugin_manifest_reload_gui_implementation.md](optional_solver_plugin_manifest_reload_gui_implementation.md).

The persistence CLI exists for review, dry-run, and explicit local state writes
through the state-writer library in
[optional_solver_plugin_manifest_persistence_cli_implementation.md](optional_solver_plugin_manifest_persistence_cli_implementation.md).
The export-summary CLI exists as stdout-first human review in
[optional_solver_plugin_manifest_export_summary_cli_implementation.md](optional_solver_plugin_manifest_export_summary_cli_implementation.md).
The state writer exists for caller-supplied local UX state files in
[optional_solver_plugin_manifest_state_writer_implementation.md](optional_solver_plugin_manifest_state_writer_implementation.md).

No reload CLI exists. No reload file reader/parser exists. No runtime reload
behavior exists. No default reload path exists. User/plugin manifests remain
untrusted by default, and reload state remains non-validating.

## 4. Definition Of Reload CLI

Reload CLI means a future headless, stdout-first review surface over
already-built reload view-model records. It may render summary/readiness,
source/provenance, schema/migration state, candidate lifecycle review,
acknowledgements and expiry, redaction/privacy blockers, stale-source/re-preview
state, conflicts/shared-stack warnings, unsafe claims, evidence/history,
trust/provenance boundaries, diagnostics, disabled/future action states, safety
guidance, and exit-code guidance.

Reload CLI must not read files, parse files, choose default paths, run reload,
activate candidates, restore trust, run discovery, run validation, execute
solvers, install dependencies, uninstall dependencies, uninstall solvers, mutate
ProjectSchema, close issues, mutate releases, push tags, upload assets, or claim
certification.

## 5. Non-Meaning Of CLI Reload Review

CLI reload review is not validation success. CLI reload review is not validation
failure. CLI reload review is not trust restoration. CLI reload review is not
automatic activation. CLI reload review is not discovery success. CLI reload
review is not dependency installation. CLI reload review is not solver
execution. CLI reload review is not ProjectSchema mutation. CLI reload review
is not issue closure. CLI reload review is not release mutation. CLI reload
review is not certification. CLI reload review is not report generation. CLI
reload review is not export file creation. CLI reload review is not reloadable
bundle creation.

## 6. Future Command Vocabulary

Future implementation should follow the repository's flat
`python -m osw.cli` command pattern. The designed command group is:

```text
python -m osw.cli optional-solver-plugin-manifest-reload explain
python -m osw.cli optional-solver-plugin-manifest-reload preview
python -m osw.cli optional-solver-plugin-manifest-reload sections
python -m osw.cli optional-solver-plugin-manifest-reload sources
python -m osw.cli optional-solver-plugin-manifest-reload candidates
python -m osw.cli optional-solver-plugin-manifest-reload acknowledgements
python -m osw.cli optional-solver-plugin-manifest-reload diagnostics
python -m osw.cli optional-solver-plugin-manifest-reload schema
python -m osw.cli optional-solver-plugin-manifest-reload redaction
python -m osw.cli optional-solver-plugin-manifest-reload stale-sources
python -m osw.cli optional-solver-plugin-manifest-reload conflicts
python -m osw.cli optional-solver-plugin-manifest-reload unsafe-claims
python -m osw.cli optional-solver-plugin-manifest-reload evidence
python -m osw.cli optional-solver-plugin-manifest-reload actions
python -m osw.cli optional-solver-plugin-manifest-reload read-file
python -m osw.cli optional-solver-plugin-manifest-reload accept
```

These names are future design vocabulary only. This gate adds no command, no
parser branch, no argparse/click/Typer behavior, and no CLI source changes.

`read-file` and `accept` are disabled/future-only vocabulary. They must remain
blocked until separate file-reader/parser and reload acceptance gates define
their behavior.

## 7. Future User Flow

Future CLI states should mirror the OSW-EXP-107 reload view-model vocabulary:

- `no_reload_request`
- `unavailable_no_payload`
- `target_missing`
- `target_not_selected`
- `source_reference_redacted`
- `schema_review`
- `schema_unsupported`
- `schema_migration_required`
- `payload_kind_mismatch`
- `redaction_review_required`
- `acknowledgement_review_required`
- `stale_source_repreview_required`
- `conflict_review_required`
- `unsafe_claim_blocked`
- `history_evidence_review`
- `reload_preview_ready`
- `reload_blocked`
- `reload_error`
- `future_activation_review_required`
- `future_discovery_refresh_required`

These states describe review readiness only. They do not authorize reload
acceptance, ProjectSchema mutation, activation, discovery refresh, validation,
solver execution, or issue/release mutation.

## 8. State Source Policy

This design gate adds no state source implementation. A future CLI may consume
already-built reload view-model records, deterministic sample state, empty
state, or unavailable state for tests and review.

The future CLI must not read a state file in this gate. It must not parse JSON
from disk in this gate. It must not infer a default path, perform background
reload, inspect filesystem state, scan plugin folders, import plugin packages,
fetch network manifests, run passive discovery, run validation, execute
solvers, or treat persisted state as authoritative truth.

Any future state-file reader must be a separate file-reader/parser gate with
explicit path policy, schema checks, redaction checks, and tests.

## 9. Output Modes

Future output modes, without implementation:

- stable plain text
- section-filtered text
- diagnostics-only output
- JSON-like stdout output
- redaction-focused output
- action-state output

Output modes must exclude:

- file output
- export file output
- report output
- reloadable bundle output
- clipboard output
- report attachment output
- open-output-folder behavior
- validation evidence output
- issue closure evidence output
- certification output

JSON-like output is stdout-only unless a future writer/export gate says
otherwise. Stdout output is not a reloadable bundle, not ProjectSchema state,
not validation evidence, not issue closure evidence, and not certification.

## 10. Summary/Readiness Output

The summary/readiness output should show state, readiness, payload kind, payload
schema version, writer version, source display, redacted source flag, candidate
counts, acknowledgement counts, diagnostic counts, blocker counts, warning
counts, and future-action counts.

Honesty flags must be visible and false for validation evidence, validation
failure, trust restoration, automatic activation, discovery execution, plugin
package import, validation execution, solver execution, ProjectSchema mutation,
issue closure, release mutation, and certification.

## 11. Source/Provenance Output

The source/provenance output should show source id, source type, redacted source
reference, `source_reference_redacted`, provenance label, trust label, and
source display. User/plugin sources are untrusted by default. Built-ins are
authoritative by default. Trust label is not certification. Fingerprints are
not trust signals.

The CLI must not inspect the path behind a redacted display label to make the
row appear more complete.

## 12. Schema/Migration Output

The schema/migration output should show that payload kind is required, payload
schema version is required, unsupported schema blocks reload review, and
migration-required blocks reload review.

Schema mismatch is not validation failure. Schema migration is a separate
future gate. The persistence schema model remains separate from ProjectSchema.
This gate creates no schema file and performs no schema migration.

## 13. Candidate Lifecycle Output

Candidate lifecycle output should show persisted lifecycle state and reload
review state. Inactive preview remains review-only. Persisted active requires
future activation review. Deactivated remains deactivated review state.
Reactivation routes to future activation review. Discovery-refresh state remains
review state.

The CLI provides no automatic activation and no trust restoration.

## 14. Acknowledgements And Expiry Output

The acknowledgement and expiry output should include:

- `reload_not_validation`
- `reload_not_trust_restoration`
- `reload_not_automatic_activation`
- `reload_not_discovery_success`
- `reload_not_dependency_install`
- `reload_no_solver_execution`
- `reload_not_issue_closure`
- `reload_not_release_mutation`
- `reload_not_certification`
- `redaction_reviewed`
- `unredacted_paths_blocked`
- `stale_source_requires_repreview`
- `untrusted_source_remains_untrusted`
- `activation_review_required_after_reload`
- `no_discovery_execution`
- `no_plugin_package_import`
- `no_validation_execution`
- `no_solver_execution`
- `trust_label_not_certification`
- `persisted_acknowledgements_may_expire`

Expiry reasons should include reload, source fingerprint change, schema version
change, unsafe claim appearance, trust policy change, and future
discovery-refresh result.

Satisfied acknowledgements do not validate, trust, activate, reload, close
issues, mutate releases, or certify anything.

## 15. Redaction/Privacy Output

Redaction/privacy output should state that raw absolute paths are hidden by
default. Basename, hash, source id, and display-name fields are preferred.
Home directories, environment variables, secrets, tokens, API keys,
credentials, private network paths, solver install paths, and plugin install
paths are blocked or redacted by default.

Unredacted paths require explicit future policy. Fingerprints are not trust
signals. Redaction review happens before activation review.

## 16. Stale-Source/Re-Preview Output

Stale-source/re-preview output should show that old preview data is not
silently trusted and that missing, moved, or changed sources require re-preview.
The CLI does no source file IO in this design gate. A future CLI must not fix
stale state silently. Stale-source state is not validation failure.

## 17. Conflict/Shared-Stack Output

Conflict/shared-stack output should make conflicts visible. Built-ins win by
default. Persisted state does not override built-ins. Shared-stack warnings are
visible. The CLI does not resolve conflicts. Future policy is required for
conflict resolution.

## 18. Unsafe-Claim Output

Unsafe claims are visible and blocked. They are not displayed as truth. Unsafe
claims include validation success. Unsafe claims include validation failure.
Unsafe claims also include issue closure, release mutation, bundled solver,
dependency installation, dependency uninstall, solver uninstall, solver
execution, trust restoration, automatic activation, industrial certification,
proprietary solver parity, and full commercial replacement claims.

## 19. Evidence/History Output

Evidence/history output should retain deactivation/reactivation history and
historical evidence as reference only. Skipped-missing remains skipped-missing.
Reload is not validation evidence. The CLI does no evidence deletion/rewrite and
implies no issue closure.

## 20. Diagnostics Output

Diagnostics output renders `OSPMG_RELOAD_*` diagnostics from the view-model with
severity, code, message, section/context, blocker/warning status, and redacted
context. Diagnostic rows must never be presented as validation success or
validation failure.

Representative view-model codes include:

- `OSPMG_RELOAD_NOT_IMPLEMENTED`
- `OSPMG_RELOAD_DESIGN_ONLY`
- `OSPMG_RELOAD_TARGET_REQUIRED`
- `OSPMG_RELOAD_TARGET_MISSING`
- `OSPMG_RELOAD_TARGET_IS_DIRECTORY`
- `OSPMG_RELOAD_TARGET_SYMLINK_REVIEW_REQUIRED`
- `OSPMG_RELOAD_PAYLOAD_KIND_MISMATCH`
- `OSPMG_RELOAD_SCHEMA_VERSION_REQUIRED`
- `OSPMG_RELOAD_SCHEMA_UNSUPPORTED`
- `OSPMG_RELOAD_SCHEMA_MIGRATION_REQUIRED`
- `OSPMG_RELOAD_REDACTION_REQUIRED`
- `OSPMG_RELOAD_UNREDACTED_PATH_BLOCKED`
- `OSPMG_RELOAD_SECRET_LIKE_CONTENT_BLOCKED`
- `OSPMG_RELOAD_ACK_REQUIRED`
- `OSPMG_RELOAD_ACK_EXPIRED`
- `OSPMG_RELOAD_STALE_SOURCE_REPREVIEW_REQUIRED`
- `OSPMG_RELOAD_UNTRUSTED_SOURCE`
- `OSPMG_RELOAD_CONFLICT_VISIBLE`
- `OSPMG_RELOAD_SHARED_STACK_VISIBLE`
- `OSPMG_RELOAD_UNSAFE_CLAIM_BLOCKED`
- `OSPMG_RELOAD_EVIDENCE_RETAINED`
- `OSPMG_RELOAD_HISTORY_RETAINED`
- `OSPMG_RELOAD_NOT_VALIDATION`
- `OSPMG_RELOAD_NOT_TRUST_RESTORE`
- `OSPMG_RELOAD_NOT_AUTOMATIC_ACTIVATION`
- `OSPMG_RELOAD_NO_DISCOVERY_EXECUTION`
- `OSPMG_RELOAD_NO_PLUGIN_IMPORT`
- `OSPMG_RELOAD_NO_VALIDATION_EXECUTION`
- `OSPMG_RELOAD_NO_SOLVER_EXECUTION`
- `OSPMG_RELOAD_PROJECT_SCHEMA_MUTATION_DISABLED`
- `OSPMG_RELOAD_FUTURE_GATE`

## 21. Reload CLI Diagnostic Reservations

Future CLI-specific diagnostic names are reserved only:

- `OSPMG_RELOAD_CLI_NOT_IMPLEMENTED`
- `OSPMG_RELOAD_CLI_REVIEW_ONLY`
- `OSPMG_RELOAD_CLI_STDOUT_ONLY`
- `OSPMG_RELOAD_CLI_FILE_READER_DISABLED`
- `OSPMG_RELOAD_CLI_FILE_PARSER_DISABLED`
- `OSPMG_RELOAD_CLI_DEFAULT_PATH_DISABLED`
- `OSPMG_RELOAD_CLI_BACKGROUND_RELOAD_DISABLED`
- `OSPMG_RELOAD_CLI_ACCEPT_DISABLED`
- `OSPMG_RELOAD_CLI_RELOAD_BUNDLE_DISABLED`
- `OSPMG_RELOAD_CLI_EXPORT_FILE_DISABLED`
- `OSPMG_RELOAD_CLI_REPORT_FILE_DISABLED`
- `OSPMG_RELOAD_CLI_CLIPBOARD_DISABLED`
- `OSPMG_RELOAD_CLI_REPORT_ATTACHMENT_DISABLED`
- `OSPMG_RELOAD_CLI_OPEN_OUTPUT_FOLDER_DISABLED`
- `OSPMG_RELOAD_CLI_NOT_VALIDATION`
- `OSPMG_RELOAD_CLI_NOT_TRUST_RESTORE`
- `OSPMG_RELOAD_CLI_NOT_AUTOMATIC_ACTIVATION`
- `OSPMG_RELOAD_CLI_NOT_ISSUE_CLOSURE`
- `OSPMG_RELOAD_CLI_NOT_RELEASE_MUTATION`
- `OSPMG_RELOAD_CLI_NOT_CERTIFICATION`
- `OSPMG_RELOAD_CLI_NO_DISCOVERY_EXECUTION`
- `OSPMG_RELOAD_CLI_NO_PLUGIN_IMPORT`
- `OSPMG_RELOAD_CLI_NO_VALIDATION_EXECUTION`
- `OSPMG_RELOAD_CLI_NO_SOLVER_EXECUTION`
- `OSPMG_RELOAD_CLI_PROJECT_SCHEMA_MUTATION_DISABLED`
- `OSPMG_RELOAD_CLI_FUTURE_GATE`

These names reserve future display semantics only. This gate adds no diagnostic
emitter, runtime constant, CLI parser, CLI handler, source file, command
callback, file reader, parser, writer, or action wiring.

## 22. Action-State Output

The future CLI should render disabled/future-only action states for:

- read reload file
- parse reload file
- migrate schema
- accept reload as trusted
- activate reloaded candidate
- refresh discovery
- validate solver
- execute solver
- install dependency
- uninstall dependency
- uninstall solver
- mutate ProjectSchema
- create export summary
- create report file
- create reloadable bundle
- copy to clipboard
- attach to report
- open output folder
- close issue
- mutate release
- push tag
- upload asset
- claim validation success/failure
- claim certification

The action-state model is display-only in this design gate.

## 23. File-Reader Boundary

There is no file-reader implementation in this design gate. Future file reading
requires a separate file-reader/parser design and implementation gate. A future
file reader may only consume an explicit caller-selected path, must perform
schema and redaction review, must not infer default paths, and must not run
background reload.

The future CLI must not smuggle file reading through `preview`, `explain`,
`diagnostics`, JSON output, sample-state generation, or action rendering.

## 24. Reload Acceptance Boundary

There is no reload acceptance behavior in this design gate. Future acceptance,
if defined, remains review state and must not mean trusted state, automatic
activation, discovery refresh, validation, solver execution, issue closure,
release mutation, or ProjectSchema mutation.

Activation after reload requires a separate activation review. Discovery refresh
requires a separate explicit gate. ProjectSchema integration requires a separate
gate.

## 25. Exit-Code Policy

Future exit-code policy should be careful and non-validating:

- `0`: CLI review command rendered supplied state, or deterministic sample/empty
  state, without CLI invocation error.
- `1`: review state is blocked, malformed, unavailable, stale, unacknowledged,
  unredacted, migration-required, conflicted, or unsafe when strict review mode
  is requested by a future gate.
- `2`: disabled/future-only action requested, such as `read-file` or `accept`.
- `>2`: CLI invocation error or unexpected internal error.

Exit code `0` is not validation success. Exit code `1` is not validation
failure. Exit code `2` is not validation failure. No exit code closes issues,
mutates releases, mutates tags, mutates assets, certifies optional solvers, or
proves installed-only validation.

## 26. Relationship To Reload View-Model

The future CLI consumes OSW-EXP-107 reload view-model records. It must not
mutate them. It must not add file IO, path opening, discovery, validation,
solver execution, dependency changes, ProjectSchema mutation, issue mutation,
release mutation, trust restoration, or activation behavior to the view-model.

CLI and GUI reload surfaces should share semantics through the reload
view-model, not through widgets or duplicated policy.

## 27. Relationship To Reload GUI

The OSW-EXP-109 reload GUI panel remains read-only/review-only over already
built reload view-model records. This CLI design adds no GUI behavior, no file
dialog, no save dialog, no clipboard behavior, no report attachment, and no
open-output-folder behavior.

CLI and GUI should share section labels, diagnostics, acknowledgement text,
non-action flags, and safety boundaries, but the future CLI must remain headless
and must not import PySide widgets.

## 28. Relationship To Persistence CLI And State Writer

The persistence CLI writes local machine-readable UX state through the
state-writer library only after explicit path, explicit mode, acknowledgement,
and preflight requirements.

Reload CLI review is separate. This design does not read state-writer output
from disk, does not write state, does not choose default paths, does not create
settings files, does not create runtime state files, and does not create schema
files.

Writer payload schema must be checked before any future reload review consumes
file content. Written state is not validation evidence, trust restoration, or
automatic activation.

## 29. Relationship To Export Summary CLI/GUI

Export summary is human-review output. Reload CLI is machine-readable UX-state
review over supplied reload view-model records. Export summaries are not
reloadable bundles.

The reload CLI must not consume export-summary output as authoritative persisted
state unless a future explicit bundle/report gate says otherwise. It creates no
reports, no export files, and no reloadable bundles.

## 30. Relationship To ProjectSchema

There is no ProjectSchema mutation. Reloaded state is not ProjectSchema state.
Reloaded state is not project validation evidence. Future ProjectSchema
integration requires a separate gate with preview, migration, rollback, docs,
and focused tests.

## 31. Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. Reload CLI does not close issues. Reload
CLI output is not live optional validation. Skipped-missing remains
skipped-missing. Prepared-machine validation remains separate.

The CLI must not mark issues ready to close, mutate issue state, mutate release
state, edit tags, edit assets, or claim public validation evidence.

## 32. Future Implementation Test Plan

Future OSW-EXP-111 must test:

- command registration without GUI/PySide dependencies
- no state supplied prints unavailable/no-payload state
- deterministic sample state review
- summary/readiness output
- source/provenance output
- schema/migration output
- candidate lifecycle output
- acknowledgement rows and expiry policy
- redaction/privacy rows and no raw path leak
- stale-source/re-preview rows
- conflict/shared-stack rows
- unsafe-claim blockers
- evidence/history retention and skipped-missing preservation
- diagnostics output for `OSPMG_RELOAD_*`
- CLI diagnostic reservations for `OSPMG_RELOAD_CLI_*`
- action states print disabled/future-only
- `read-file` disabled/future-only and creates no file reader/parser behavior
- `accept` disabled/future-only and creates no reload acceptance behavior
- read-file disabled/future-only
- accept disabled/future-only
- JSON-like output is stdout-only
- exit codes do not imply validation success or validation failure
- no file dialog, no file reader/parser, no default path, no background reload
- no ProjectSchema mutation, no discovery, no validation, no solver execution
- no issue/release/tag/asset mutation and no certification claim

These are future tests. This gate adds only focused docs tests for this design
document and related guardrail/risk/checklist/validation references.

## 33. Non-Actions

This gate explicitly does not:

- implement reload CLI
- edit CLI source
- edit runtime source
- edit GUI source
- add command registration
- add file dialog behavior
- add file reader/parser behavior
- read persisted state files at runtime
- parse persisted state files at runtime
- add runtime reload behavior
- add default reload paths
- add background reload
- create reloadable bundles
- create export files
- create report files
- add clipboard behavior
- add report attachment
- add open-output-folder behavior
- mutate ProjectSchema
- add live discovery
- add passive refresh
- import plugin packages
- scan directories
- fetch network manifests
- run validation
- run solver execution
- install dependencies
- uninstall dependencies
- uninstall solvers
- automatically activate candidates
- restore trust
- mutate issues
- mutate releases
- mutate tags
- mutate assets
- bump version
- claim validation-pass
- claim validation-fail
- claim issue closure
- claim bundled solver support
- claim certification

No runtime source, GUI source, view-model source, schema-model source, CLI
source, loader source, discovery source, plugin manager source, ProjectSchema
source, persistence writer, settings file, runtime state file, schema file,
export file, report file, reloadable bundle, release asset, tag, issue, release,
version metadata, or solver/runtime artifact is changed by this design gate.

## 34. Future Gates

Suggested future gates:

- `OSW-EXP-111_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_CLI_IMPLEMENTATION`
- `OSW-EXP-112_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_FILE_READER_DESIGN`
- `OSW-EXP-113_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_FILE_READER_IMPLEMENTATION`
- `OSW-EXP-114_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_FILE_DIALOG_DESIGN`
- `OSW-EXP-115_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_FILE_DIALOG_IMPLEMENTATION`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` if a prepared
  machine is available

If repository numbering changes, future gates should follow the latest accepted
decision-log sequence while preserving the boundaries in this document.
