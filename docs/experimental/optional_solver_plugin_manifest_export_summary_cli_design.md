# Optional solver plugin manifest export-summary CLI design

## 1. Status

This gate is design-only.

It adds no runtime behavior and no export-summary CLI implementation. It edits
no CLI source and adds no command parser, no command handler, and no command
registration.

This gate records no CLI source edits.

This design performs no export file creation, no report file creation, no
reloadable bundle creation, no clipboard behavior, no report attachment, no
open-output-folder behavior, no GUI behavior, no reload behavior, no
ProjectSchema mutation, no live discovery, no passive refresh, no plugin package
import, no directory scan, no network fetch, no validation execution, no solver
execution, no dependency installation, no dependency uninstall, no solver
uninstall, no issue mutation, no release mutation, no tag mutation, no asset
mutation, no version bump, no validation-pass claim, no validation-fail claim,
no issue-closure claim, no bundled-solver claim, and no certification claim.

## Implementation follow-up

OSW-EXP-105 implements this command vocabulary as a stdout-first review CLI in
[optional solver plugin manifest export-summary CLI implementation](optional_solver_plugin_manifest_export_summary_cli_implementation.md).
The implementation keeps `write-summary` disabled/future-only and still creates
no export files, report files, or reloadable bundles.

## 2. Purpose

This document defines future export-summary CLI semantics for optional solver
plugin manifest UX state.

The future export-summary CLI should preserve the OSW-EXP-091 export-summary
design, the OSW-EXP-097 export-summary view-model, the OSW-EXP-099
export-summary GUI review panel, the OSW-EXP-103 persistence CLI, and the
OSW-EXP-100 through OSW-EXP-102 state-writer boundaries.

The design keeps export summary distinct from persistence state, state-writer
local state files, reloadable bundles, validation evidence, trust restoration,
automatic activation, ProjectSchema state, issue closure, release mutation, and
certification.

## 3. Current state before export-summary CLI

The current line has these bounded pieces:

- OSW-EXP-091 defines state export-summary semantics as design-only.
- OSW-EXP-097 implements a pure export-summary view-model.
- OSW-EXP-098 defines export-summary GUI semantics.
- OSW-EXP-099 implements a review-only export-summary GUI panel.
- OSW-EXP-100 defines state-writer semantics as design-only.
- OSW-EXP-101 implements a pure state-writer view-model.
- OSW-EXP-102 implements the explicit local state-writer library.
- OSW-EXP-103 implements a dry-run-first persistence CLI over that writer.

No export-summary CLI exists. No export/report/clipboard/open-folder behavior
exists for this line. No reload behavior exists. No live discovery integration
exists. User/plugin manifests remain untrusted and non-validating.

## 4. Definition of export-summary CLI

The future export-summary CLI is an explicit, redaction-first, stdout-first,
human-reviewable summary surface over supplied export-summary view-model state.

It may eventually:

- print an export summary to stdout
- print diagnostics
- print acknowledgements
- print source/provenance rows
- print candidate lifecycle summaries
- print redaction/privacy state
- print stale-source/re-preview state
- print conflict/shared-stack state
- print unsafe-claim state
- print evidence/history state
- print limitations
- print non-action flags
- print disabled/future action states
- optionally write a future export-summary file only under a separate
  implementation gate

It must never:

- treat export summary as validation evidence
- treat export summary as trust restoration
- treat export summary as automatic activation
- treat export summary as ProjectSchema state
- treat export summary as a reloadable bundle
- close issues
- mutate releases
- mutate tags
- mutate assets
- claim certification

## 5. Future command vocabulary

Future implementation should follow the repository's existing
`python -m osw.cli` flat command pattern. The designed command group is:

```text
python -m osw.cli optional-solver-plugin-manifest-export-summary explain
python -m osw.cli optional-solver-plugin-manifest-export-summary preview
python -m osw.cli optional-solver-plugin-manifest-export-summary sections
python -m osw.cli optional-solver-plugin-manifest-export-summary sources
python -m osw.cli optional-solver-plugin-manifest-export-summary candidates
python -m osw.cli optional-solver-plugin-manifest-export-summary acknowledgements
python -m osw.cli optional-solver-plugin-manifest-export-summary diagnostics
python -m osw.cli optional-solver-plugin-manifest-export-summary redaction
python -m osw.cli optional-solver-plugin-manifest-export-summary stale-sources
python -m osw.cli optional-solver-plugin-manifest-export-summary conflicts
python -m osw.cli optional-solver-plugin-manifest-export-summary unsafe-claims
python -m osw.cli optional-solver-plugin-manifest-export-summary evidence
python -m osw.cli optional-solver-plugin-manifest-export-summary limitations
python -m osw.cli optional-solver-plugin-manifest-export-summary actions
python -m osw.cli optional-solver-plugin-manifest-export-summary write-summary
```

`write-summary` is future-gated only. This design does not authorize source
edits, command registration, file output, report output, clipboard output,
reloadable bundle output, or open-output-folder behavior.

## 6. State source policy

This gate adds no live discovery, no passive refresh, no plugin package import,
no directory scan, and no network fetch.

Future CLI may consume supplied export-summary view-model state.
It may expose deterministic sample state, unavailable state, or explicit
in-memory records for tests. Future live source integration requires a separate
gate and must not be smuggled into export-summary CLI implementation.

The future CLI must not scan plugin folders, import third-party plugin packages,
read arbitrary manifest directories, fetch manifests from the network, run
passive discovery, run validation, execute solvers, or reload existing state
files as authoritative truth.

## 7. Output modes

Future output modes may include:

- stable plain text
- diagnostics-only output
- section-filtered output
- JSON-like stdout output
- redaction-focused output

Output modes must exclude:

- reloadable bundle output
- report attachment output
- clipboard output
- open-output-folder behavior
- hidden file export
- validation evidence output
- issue closure evidence output

JSON-like stdout output must be deterministic, redacted by default, and not a
reloadable bundle.

## 8. Stdout-first behavior

The default future export-summary CLI behavior is stdout-only.

Stdout output is not a file export, not validation evidence, not issue closure
evidence, not certification, and not reloadable state. It is a human-reviewable
summary of already-supplied export-summary view-model records.

Stdout review may return success when state is inspectable, even if warnings,
limitations, stale-source rows, or unsafe-claim rows are visible. That success
does not mean validation success.

## 9. Future file-output policy

This design gate defines no file output and creates no export files.

Any future file output requires a separate implementation gate and must follow
these rules:

- explicit output path required
- no default path
- no background export
- no directory creation by default
- redaction review required
- unredacted path blockers preserved
- secret-like content blockers preserved
- report/export files remain future-gated
- reloadable bundles remain future-gated
- state-writer local state files remain distinct from export-summary files

Future file-output behavior must not reuse the OSW-EXP-102 local state-writer
payload as an export summary and must not convert export summaries into
reloadable persistence files.

## 10. Redaction/privacy policy

Raw absolute paths are hidden by default. Basename, hash, source id, display
name, or another redacted reference should be preferred.

Home directories, environment variables, secrets, tokens, API keys, credentials,
private network paths, and secret-like payloads are blocked or redacted by
default. Fingerprints are not trust signals.

Redaction review is required before any future file output. Stdout must not leak
raw paths unless a future gate explicitly approves that policy and tests it.

## 11. Acknowledgement model

The future CLI should surface these acknowledgement identifiers:

- `export_summary_not_validation`
- `export_summary_not_persistence`
- `export_summary_not_reloadable_bundle`
- `export_summary_not_trust_restoration`
- `export_summary_not_automatic_activation`
- `export_summary_not_issue_closure`
- `export_summary_not_release_mutation`
- `export_summary_not_certification`
- `redaction_reviewed`
- `unredacted_paths_blocked`
- `stale_source_requires_repreview`
- `untrusted_source_remains_untrusted`
- `no_discovery_execution`
- `no_plugin_package_import`
- `no_validation_execution`
- `no_solver_execution`
- `trust_label_not_certification`

Missing acknowledgements are visible review state. Satisfied acknowledgements do
not validate, trust, activate, persist, reload, close issues, mutate releases,
or certify anything.

## 12. Diagnostics model

The future CLI reserves this `OSPMG_EXPORT_SUMMARY_CLI_*` vocabulary:

- `OSPMG_EXPORT_SUMMARY_CLI_NOT_IMPLEMENTED`
- `OSPMG_EXPORT_SUMMARY_CLI_PREVIEW_ONLY`
- `OSPMG_EXPORT_SUMMARY_CLI_STDOUT_ONLY`
- `OSPMG_EXPORT_SUMMARY_CLI_FILE_OUTPUT_DISABLED`
- `OSPMG_EXPORT_SUMMARY_CLI_RELOAD_BUNDLE_DISABLED`
- `OSPMG_EXPORT_SUMMARY_CLI_REPORT_ATTACHMENT_DISABLED`
- `OSPMG_EXPORT_SUMMARY_CLI_CLIPBOARD_DISABLED`
- `OSPMG_EXPORT_SUMMARY_CLI_OPEN_OUTPUT_FOLDER_DISABLED`
- `OSPMG_EXPORT_SUMMARY_CLI_NOT_VALIDATION`
- `OSPMG_EXPORT_SUMMARY_CLI_NOT_PERSISTENCE`
- `OSPMG_EXPORT_SUMMARY_CLI_NOT_RELOADABLE_BUNDLE`
- `OSPMG_EXPORT_SUMMARY_CLI_NOT_TRUST_RESTORE`
- `OSPMG_EXPORT_SUMMARY_CLI_NOT_AUTOMATIC_ACTIVATION`
- `OSPMG_EXPORT_SUMMARY_CLI_NOT_ISSUE_CLOSURE`
- `OSPMG_EXPORT_SUMMARY_CLI_NOT_RELEASE_MUTATION`
- `OSPMG_EXPORT_SUMMARY_CLI_NOT_CERTIFICATION`
- `OSPMG_EXPORT_SUMMARY_CLI_REDACTION_REQUIRED`
- `OSPMG_EXPORT_SUMMARY_CLI_UNREDACTED_PATH_BLOCKED`
- `OSPMG_EXPORT_SUMMARY_CLI_SECRET_LIKE_CONTENT_BLOCKED`
- `OSPMG_EXPORT_SUMMARY_CLI_STALE_SOURCE_REPREVIEW_REQUIRED`
- `OSPMG_EXPORT_SUMMARY_CLI_UNTRUSTED_SOURCE`
- `OSPMG_EXPORT_SUMMARY_CLI_CONFLICT_VISIBLE`
- `OSPMG_EXPORT_SUMMARY_CLI_SHARED_STACK_VISIBLE`
- `OSPMG_EXPORT_SUMMARY_CLI_UNSAFE_CLAIM_BLOCKED`
- `OSPMG_EXPORT_SUMMARY_CLI_EVIDENCE_RETAINED`
- `OSPMG_EXPORT_SUMMARY_CLI_HISTORY_RETAINED`
- `OSPMG_EXPORT_SUMMARY_CLI_NO_DISCOVERY_EXECUTION`
- `OSPMG_EXPORT_SUMMARY_CLI_NO_PLUGIN_IMPORT`
- `OSPMG_EXPORT_SUMMARY_CLI_NO_VALIDATION_EXECUTION`
- `OSPMG_EXPORT_SUMMARY_CLI_NO_SOLVER_EXECUTION`
- `OSPMG_EXPORT_SUMMARY_CLI_PROJECT_SCHEMA_MUTATION_DISABLED`
- `OSPMG_EXPORT_SUMMARY_CLI_FUTURE_GATE`

These names reserve future display semantics only. They do not implement
diagnostics in this gate.

## 13. Stale-source / re-preview behavior

Stale sources are visible. Stale sources are not silently trusted. Re-preview is
future-gated.

This design performs no file IO for source checking, no restore behavior, no
rewrite behavior, and no delete behavior. Stale state is not validation failure.
It is review state that requires user awareness or a future source-integration
policy.

## 14. Conflict/shared-stack behavior

Conflicts are visible. Built-ins win by default. Shared-stack warnings are
visible.

Export summary does not override built-ins, resolve conflicts, activate
candidates, delete conflicting records, trust user/plugin records, or mutate
source state. Future conflict resolution requires a separate policy gate.

## 15. Unsafe-claim behavior

Unsafe claims are visible and blocked. Unsafe claims are not exported as truth.

Unsafe claims include:

- validation success or validation failure reversal
- issue closure
- release mutation
- bundled solvers
- dependency installation
- dependency uninstall
- solver uninstall
- solver execution
- industrial certification
- proprietary solver parity
- full commercial replacement claims
- trust restoration
- automatic activation

The future CLI must show unsafe claims as review blockers, not as facts.

## 16. Evidence/history retention

Deactivation history is retained. Reactivation history is retained. Historical
evidence is retained as reference only.

Skipped-missing remains skipped-missing. Export summary is not validation
evidence. This design adds no evidence deletion, no evidence rewrite, no issue
closure, and no validation-pass or validation-fail claim.

## 17. Trust/provenance boundary

Source type is visible. Trust label is visible. User/plugin manifests are
untrusted by default. Built-ins are authoritative by default.

A trust label is not certification. A fingerprint is not trust restoration.
Export summary is not trust restoration and not validation evidence.

## 18. Action-state model

The future CLI should show these actions as disabled or future-only unless a
separate gate implements them:

- write export-summary file
- create report file
- attach to report
- copy to clipboard
- open output folder
- create reloadable bundle
- persist state
- reload state
- mutate ProjectSchema
- run discovery
- run validation
- execute solver
- install dependency
- uninstall dependency
- uninstall solver
- close issue
- mutate release
- push tag
- upload asset
- claim validation success
- claim validation failure
- claim certification

## 19. Exit-code policy

Future `explain` and `preview` commands may return success when state is
inspectable. Diagnostics-only output may return success with warnings.

Blocked export file output returns nonzero. Unsafe claims or blockers return
nonzero only when a command requests an action that would rely on them, not for
pure review.

No exit code implies validation success. Exit code `0` is not validation
success. Exit code `1` is not validation failure.

## 20. Relationship to OSW-EXP-097 export-summary view-model

Future CLI consumes export-summary view-model records. It must not mutate them.
The view-model remains pure and side-effect-free.

The future CLI should reuse the view-model sections for summary, sources,
candidates, acknowledgements, diagnostics, redaction, stale sources, conflicts,
unsafe claims, evidence/history, limitations, trust/provenance, non-action
flags, and disabled/future actions.

## 21. Relationship to OSW-EXP-099 export-summary GUI

The GUI remains review-only. This CLI design adds no GUI behavior. CLI and GUI
should share semantics, labels, diagnostics, and safety boundaries, but not
widgets or PySide dependencies.

## 22. Relationship to OSW-EXP-103 persistence CLI

The OSW-EXP-103 persistence CLI writes local machine-readable state via the
state-writer library when the user supplies an explicit target path, explicit
write mode, and explicit acknowledgement.

The future export-summary CLI is human-review-oriented. It does not reload or
persist state by default. Export-summary CLI file output is future-gated and
distinct from state-writer files.

## 23. Relationship to ProjectSchema

This design adds no ProjectSchema mutation. Export summary is not ProjectSchema
state. Export summary is not project validation evidence. Future ProjectSchema
integration requires a separate gate.

## 24. Relationship to live optional validation issues

Issues `#6` through `#11` remain open. Export-summary CLI does not close issues.
Export-summary CLI output is not live optional validation.

Skipped-missing remains skipped-missing. Prepared-machine validation remains a
separate installed-machine gate.

## 25. Non-actions

This gate explicitly does not:

- implement export-summary CLI
- edit CLI source
- add CLI source edits
- add runtime behavior
- create export files
- add export file creation
- create report files
- add report file creation
- create reloadable bundles
- add reloadable bundle creation
- add clipboard behavior
- add report attachment
- add open-output-folder behavior
- add GUI behavior
- add reload behavior
- mutate ProjectSchema
- add live discovery
- add passive refresh
- import plugin packages
- add plugin package import
- scan directories
- add directory scan
- fetch network manifests
- add network fetch
- run validation
- add validation execution
- run solver execution
- add solver execution
- install dependencies
- add dependency installation
- uninstall dependencies
- add dependency uninstall
- uninstall solvers
- add solver uninstall
- mutate issues
- add issue mutation
- mutate releases
- add release mutation
- mutate tags
- add tag mutation
- mutate assets
- add asset mutation
- bump versions
- add version bump
- claim validation-pass
- add validation-pass claim
- claim validation-fail
- add validation-fail claim
- claim issue closure
- add issue-closure claim
- claim bundled solver support
- add bundled-solver claim
- claim certification
- add certification claim

## 26. Future implementation test plan

OSW-EXP-105 or a later implementation gate must test:

- help, explain, and preview commands
- section filtering
- diagnostics rendering
- JSON and text output stability
- redaction
- no raw path leak
- no file output by default
- explicit file output if implemented
- no reloadable bundle
- no report attachment
- no clipboard
- no open-folder
- no live discovery
- no plugin import
- no validation
- no solver execution
- no issue/release mutation

The future implementation tests must keep export summary separate from
validation evidence, persistence state, state-writer files, reloadable bundles,
ProjectSchema state, issue closure, release mutation, and certification.

## 27. Future gates

The current planned sequence is:

- `OSW-EXP-105_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_CLI_IMPLEMENTATION`
- `OSW-EXP-106_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_DESIGN`
- `OSW-EXP-107_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_VIEWMODEL`
- `OSW-EXP-108_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_DESIGN`
- `OSW-EXP-109_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_IMPLEMENTATION`
- `OSW-EXP-110_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_CLI_DESIGN`
- `OSW-EXP-111_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_CLI_IMPLEMENTATION`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION`

If the repository later reserves different numbering, follow the latest
decision-log mapping and keep export-summary CLI implementation, file output,
reload, ProjectSchema integration, live source integration, discovery,
validation, solver execution, issue closure, release/tag/asset mutation, and
certification claims in separate gates.
