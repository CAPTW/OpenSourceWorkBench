# Optional solver plugin manifest export-summary CLI implementation

## 1. Status

Experimental export-summary CLI review is implemented.

The CLI is stdout-first review only. It creates no export files, no report
files, and no reloadable bundles. It adds no clipboard behavior, no report
attachment, no open-output-folder behavior, no GUI behavior, no reload behavior,
no ProjectSchema mutation, no live discovery, no passive refresh, no plugin
package import, no directory scan, no network fetch, no validation execution, no
solver execution, no dependency install/uninstall, no issue/release/tag/asset
mutation, no validation-pass/fail claim, and no certification claim.

`write-summary` is registered only as a disabled future action. It returns a
blocked status and writes nothing.

## 2. Purpose

The CLI gives maintainers and test harnesses a deterministic way to inspect
optional solver plugin manifest export-summary view-model state from the command
line. It is a thin renderer over supplied in-memory state and the OSW-EXP-097
export-summary view-model semantics.

It does not become persistence, report generation, reload, validation evidence,
trust restoration, automatic activation, ProjectSchema state, issue closure,
release mutation, bundled-solver evidence, or certification.

## 3. Public command names

The repository uses a flat `python -m osw.cli` namespace. This gate adds:

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

Supported state-source flags are `--sample-state`, `--empty-state`, and
`--unavailable-state`. Supported output formats are `--format text` and
`--format json`.

## 4. State source policy

This CLI uses deterministic in-memory state only:

- `--sample-state` builds a deterministic supplied-state sample for tests and
  review.
- `--empty-state` builds an empty in-memory view-model.
- `--unavailable-state` is the default and states that live source integration
  is future-gated.

The CLI does not scan plugin folders, import plugin packages, read arbitrary
manifest directories, fetch manifests from the network, run passive refresh, run
validation, execute solvers, or reload existing state files as authority.

## 5. Output modes

Text output is stable, line-oriented, and section-labelled.

JSON output is deterministic and sorted. It includes the command, selected
subcommand, state-source policy, stdout/file-output flags, selected section,
full view-model mapping, CLI diagnostics, view-model diagnostic vocabulary, and
non-action boundaries.

JSON output is stdout review data only. It is not a reloadable bundle, not a
report attachment, not clipboard data, not ProjectSchema state, not validation
evidence, not issue closure evidence, and not certification.

## 6. Stdout-first behavior

Every review command writes to stdout and creates no file output. A successful
exit code means the review command rendered, not that optional solver validation
passed.

`write-summary` is the only blocked action command. It writes its blocked status
to stderr, returns nonzero, and creates no files.

## 7. File-output boundary

No command writes export-summary files in this gate. There is no `--output`
argument, no default path, no background export, no directory creation, no
overwrite policy, and no file-output payload format.

Future file output requires a separate gate. That future gate must preserve
explicit paths, redaction review, unredacted path blockers, secret-like content
blockers, no default path, no hidden report/export output, and the distinction
between state-writer local state files and export-summary files.

## 8. Redaction/privacy behavior

Raw absolute paths are hidden by default. The deterministic sample uses a
caller-supplied full path internally only to prove redaction; the CLI output
shows the basename and redaction state.

Home directories, environment variables, secrets, tokens, credentials, API keys,
private network paths, and secret-like payloads remain blocked or redacted.
Fingerprints are not trust signals. Redaction review remains visible and is not
trust restoration.

## 9. Acknowledgement behavior

The CLI renders acknowledgement rows from the view-model plus the design
aliases used by OSW-EXP-104:

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

Acknowledgements do not validate, persist, reload, trust, activate, close
issues, mutate releases, or certify anything.

## 10. Diagnostics

The CLI surfaces `OSPMG_EXPORT_SUMMARY_*` diagnostics from the view-model and
the implementation-level `OSPMG_EXPORT_SUMMARY_CLI_*` diagnostics:

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

Diagnostics are review state. They are not validation success or validation
failure.

## 11. Stale-source/re-preview behavior

Stale-source rows are visible. Stale sources are not silently trusted. The CLI
does not read source files, restore files, rewrite files, delete files, refresh
sources, or run discovery. Re-preview remains a future source-integration gate.
Stale state is not validation failure.

## 12. Conflict/shared-stack behavior

Conflict and shared-stack rows are visible. Built-ins win by default. Export
summary output does not override built-ins and does not resolve conflicts.
Conflict-resolution policy remains future-gated.

## 13. Unsafe-claim behavior

Unsafe claims are visible and blocked. They are not exported as truth. Unsafe
claims include validation success/failure, issue closure, release mutation,
bundled solvers, dependency installation, solver execution, industrial
certification, proprietary solver parity, and full replacement claims.

## 14. Evidence/history retention

Deactivation history, reactivation history, and historical evidence remain
visible as reference only. Skipped-missing remains skipped-missing. The CLI does
not delete evidence, rewrite evidence, turn evidence into validation success, or
imply issue closure.

## 15. Trust/provenance boundary

Source type, trust label, redaction state, and provenance rows are visible.
User/plugin manifests remain untrusted by default. Built-ins are authoritative
by default. A trust label is not certification. Export-summary output is not
trust restoration and not validation evidence.

## 16. Action-state behavior

The CLI renders view-model action states and repeats disabled/future-only
boundaries for:

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
- claim validation success/failure
- claim certification

Only review actions are enabled.

## 17. Exit-code behavior

Review commands return `0` when output is rendered. Exit code `0` is not
validation success. `write-summary` returns `2` because file-output behavior is
disabled and future-gated. Exit code `2` for that command is not validation
failure.

## 18. Relationship to OSW-EXP-097 export-summary view-model

The CLI consumes the OSW-EXP-097 view-model through supplied deterministic
records and public render/mapping semantics. It does not mutate view-model
records and does not add side effects to the view-model layer.

## 19. Relationship to OSW-EXP-099 export-summary GUI

The GUI remains review-only. This CLI shares the same source, candidate,
diagnostic, redaction, stale-source, conflict, unsafe-claim, evidence/history,
limitation, trust/provenance, and action-state semantics without importing GUI
widgets or adding GUI behavior.

## 20. Relationship to OSW-EXP-103 persistence CLI

The persistence CLI writes local machine-readable UX state through the
state-writer library after explicit path, mode, acknowledgement, and preflight
requirements. This export-summary CLI is human-review-oriented, stdout-first,
and non-writing. It does not persist state, reload state, or create
export/report outputs.

## 21. Relationship to ProjectSchema

No ProjectSchema mutation occurs. Export summaries are not ProjectSchema state
and are not project validation evidence.

## 22. Relationship to live optional validation issues

Issues `#6` through `#11` remain open. Export-summary CLI output is not live
optional validation and does not close issues. Skipped-missing remains
skipped-missing. Prepared-machine validation remains separate.

## 23. Non-actions

This gate performs no export file creation, report file creation, reloadable
bundle creation, clipboard behavior, report attachment, open-output-folder
behavior, GUI behavior, reload behavior, ProjectSchema mutation, live discovery,
passive refresh, plugin package import, directory scan, network fetch,
validation execution, solver execution, dependency installation, dependency
uninstall, solver uninstall, issue mutation, release mutation, tag mutation,
asset mutation, version bump, validation-pass claim, validation-fail claim,
issue-closure claim, bundled-solver claim, or certification claim.

## 24. Testing strategy

Focused unit tests cover:

- module import without GUI extras
- forbidden import/call guardrails
- command registration
- every review command
- unavailable, empty, and sample in-memory state policy
- stable text labels
- deterministic JSON output
- redaction of raw absolute paths
- stale-source, conflict, unsafe-claim, evidence/history, limitation, and
  action-state output
- disabled `write-summary`
- no export/report/reloadable output files
- no ProjectSchema, discovery, validation, solver, dependency, issue, release,
  tag, asset, validation-claim, issue-closure, bundled-solver, or certification
  side effects

Adjacent design, view-model, GUI panel, persistence CLI, and state-writer tests
remain part of the gate validation set.

## 25. Future gates

The next recommended gate is
`OSW-EXP-106_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_DESIGN`.

Potential later work remains separately gated:

- live export-summary source integration
- export-summary file output
- report attachment or report export integration
- reloadable bundle design and implementation
- ProjectSchema integration, if ever approved
- prepared-machine optional validation
- issue/release/tag/asset workflows
