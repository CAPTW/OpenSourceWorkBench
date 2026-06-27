# Optional solver plugin manifest export-summary GUI design

## 1. Status

This gate is design-only.

No runtime behavior is added in this gate. No GUI implementation is added in
this gate. This document defines a future PySide review contract only.

Status boundaries:

- no GUI implementation
- no file export
- no file writes
- no export file creation
- no report file creation
- no clipboard behavior
- no report attachment
- no open-output-folder behavior
- no reloadable bundle creation
- no persistence implementation
- no runtime persistence behavior
- no settings file creation
- no runtime state file creation
- no schema file creation
- no ProjectSchema mutation
- no file dialog
- no save dialog
- no CLI behavior
- no reload behavior
- no activation source mutation
- no deactivation source mutation
- no reactivation source mutation
- no discovery-refresh source mutation
- no persistence source mutation
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

## 2. Purpose

Define future PySide export-summary GUI semantics for optional solver plugin
manifest UX state.

The design preserves:

- OSW-EXP-091 export-summary design semantics
- OSW-EXP-097 export-summary view-model records
- OSW-EXP-092 persistence view-model records
- OSW-EXP-093 persistence schema-model records
- OSW-EXP-095 persistence GUI review-panel boundaries
- OSW-EXP-096 persistence CLI design boundaries
- optional solver and plugin manifest safety boundaries

The export-summary GUI must be distinct from file export, file writes, clipboard
behavior, report attachment, reloadable bundle creation, persistence, validation,
trust restoration, dependency installation, solver execution, issue closure,
release mutation, and certification.

## 3. Current state before export-summary GUI

- Export-summary design exists in OSW-EXP-091.
- Pure export-summary view-model records exist in OSW-EXP-097.
- Persistence view-model and schema model exist in OSW-EXP-092 and OSW-EXP-093.
- A persistence GUI review panel exists in OSW-EXP-095.
- A persistence CLI design exists in OSW-EXP-096.
- No export-summary GUI exists.
- No file export behavior exists for this manifest state line.
- No clipboard, report attachment, reloadable bundle, persistence writer,
  reload, or CLI export-summary command exists.
- User/plugin manifests remain untrusted and non-validating.
- Built-in manifests remain authoritative by default when a shared-stack
  conflict appears.

## 4. Definition of export-summary GUI

The future export-summary GUI is a view-model-driven review surface for
redacted, human-reviewable, non-authoritative export summaries.

It may eventually render data already present in
`OptionalSolverPluginManifestExportSummaryViewModel`:

- export summary header
- export summary sections
- source/provenance summary rows
- candidate summary rows
- acknowledgement rows
- diagnostic rows
- redaction/privacy rows
- stale-source/re-preview rows
- shared-stack/conflict rows
- unsafe-claim rows
- evidence/history rows
- limitation rows
- non-action flags
- disabled/future action states
- safety guidance

The future GUI must not:

- write export files
- copy to clipboard
- attach reports
- create reloadable bundles
- persist state
- reload state
- mutate ProjectSchema
- mutate candidate state
- automatically activate candidates
- restore trust
- run discovery
- run validation
- execute solvers
- install dependencies
- uninstall dependencies
- uninstall solvers
- import plugin packages
- scan directories
- fetch network manifests
- close issues
- mutate releases, tags, or assets

## 5. User flow states

The future GUI should map view-model state into explicit screens/states:

- no state supplied / export summary unavailable
- no explicit export-summary request
- summary preview
- source/provenance review
- candidate summary review
- acknowledgement review
- redaction review required
- unredacted path blocked
- stale-source/re-preview required
- conflict/shared-stack blocked
- unsafe claim blocked
- limitations visible
- ready preview only
- future file export required
- future clipboard required
- future report attachment required
- future reloadable bundle required
- export summary error

The ready preview only state is not permission to export a file, copy text, attach
a report, write state, reload state, mutate ProjectSchema, trust a manifest,
activate a candidate, run discovery, run validation, or execute a solver.

## 6. GUI entry points

Future entry points may include:

- persistence GUI panel
- optional solver manifest review surfaces
- plugin manager or health panel
- future report/support summary area
- future export summary area

This gate adds no menu item, no button, no callback, no file dialog, no save
dialog, no clipboard action, no report attachment, and no widget. Entry points
are reserved design language only.

## 7. Rendered sections

The future GUI should render these sections from the supplied view-model:

- header
- sections list
- summary
- sources/provenance
- candidates
- acknowledgements
- diagnostics
- redaction/privacy
- stale-source/re-preview
- conflicts/shared-stack
- unsafe claims
- evidence/history
- limitations
- non-action flags
- action states
- safety guidance

Sections may be tabs, collapsible panels, or stacked review groups in a later
implementation. This design does not create a widget or choose a final layout.

## 8. Header / summary section

The header / summary section should show:

- summary kind
- state scope
- generated-by display
- schema version display
- source count
- candidate count
- acknowledgement count
- diagnostic count
- warning count
- error count
- conflict count
- unsafe claim count
- stale source count
- redaction required count
- evidence retained
- history retained
- limitations count
- export performed false
- file write performed false
- clipboard performed false
- report attachment performed false
- reloadable bundle created false
- persistence performed false
- validation success claimed false
- validation failure claimed false
- issue closure claimed false
- release mutation performed false
- certification claimed false

These fields are display-only. False non-action values must remain visible so a
reviewer can see that preview state did not perform side effects.

## 9. Section rendering

Each rendered section should display:

- section id
- title
- severity
- lines
- rows
- diagnostics
- visible yes/no
- collapsed-by-default yes/no
- recommended next review action
- blocked yes/no
- future gate reference, when applicable

Section rendering must be deterministic and derived from the view-model. The GUI
must not create hidden state by rereading files, probing directories, importing
plugins, fetching manifests, running discovery, or recomputing validation.

## 10. Source/provenance review

The source/provenance review should show:

- source id
- source label
- source type
- source reference display
- source reference redacted yes/no
- raw reference blocked yes/no
- trust label
- trust label is not certification
- built-in relationship
- plugin/user source untrusted by default
- redaction status
- stale-source state
- re-preview required yes/no
- diagnostics
- limitations

Raw absolute paths are not shown by default. User-selected and plugin-provided
sources remain untrusted by default. A trust label is not certification and is
not validation evidence.

## 11. Candidate summary review

The candidate summary review should show:

- stack id
- display name
- source id
- source type
- source label
- source reference display
- source reference redacted yes/no
- trust label
- activation state
- deactivation state
- reactivation state
- discovery-refresh state
- persistence state
- export-summary state
- readiness
- blockers
- warnings
- required acknowledgements
- diagnostics
- stale-source state
- re-preview required
- redaction status
- built-in relationship
- shared-stack indicators
- evidence/history state
- automatic activation implied false
- trusted source implied false
- not validation evidence true

Candidate rows must not become candidate mutation controls. They are review rows
only. Activation, deactivation, reactivation, discovery-refresh, persistence,
reload, export, validation, and solver actions remain absent or disabled.

## 12. Acknowledgement review

The acknowledgement review should render the required OSW-EXP-097 export-summary
acknowledgements:

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

Each row should show:

- acknowledgement id
- label
- satisfied yes/no
- required yes/no
- blocking yes/no
- warning text
- expiry policy

Acknowledgement state is future widget-local state unless a later explicit gate
defines otherwise. Acknowledgements do not create validation evidence, restore
trust, install dependencies, execute solvers, close issues, mutate releases, copy
to clipboard, attach reports, or write export files.

Acknowledgements should expire when:

- source references change
- stale-source state changes
- redaction policy changes
- unsafe claims appear
- validation, issue, release, tag, asset, or certification boundaries change
- a future implementation gate changes action availability

## 13. Diagnostic rendering

The diagnostic rendering should display:

- diagnostic code
- severity
- message
- blocker yes/no
- related section
- related source id
- related candidate stack id
- suggested fix
- future gate reference

Diagnostics are review signals, not validation pass/fail evidence. A diagnostic
row must not run discovery, run validation, execute a solver, import a plugin
package, scan directories, fetch network manifests, install dependencies, close
issues, or mutate releases.

## 14. Redaction/privacy review

The redaction/privacy review should show:

- raw reference supplied yes/no
- display reference
- redaction status
- redaction required yes/no
- unredacted path blocked yes/no
- redaction reviewed yes/no
- secret-like content blocked yes/no
- privacy warning
- fingerprint is not trust signal yes/no

The future GUI must be redaction-first. Absolute paths, home-directory details,
environment values, access tokens, API keys, password-like text, and other
sensitive local references remain blocked unless a later privacy gate explicitly
defines a reviewed display policy. This gate adds no file dialog and no save
dialog that could expose paths.

## 15. Stale-source/re-preview review

The stale-source/re-preview review should show:

- source id
- source label
- stale-source state
- re-preview required yes/no
- source reference display
- old preview not silently trusted yes/no
- no file IO performed yes
- no file restoration performed yes
- no file rewrite performed yes
- no file deletion performed yes
- future policy required if source cannot be re-previewed

Stale, missing, moved, or changed sources must require re-preview before future
use. Re-preview is not implemented here. The GUI must not scan directories,
compare files, restore files, rewrite files, delete files, or run discovery.

## 16. Conflict/shared-stack review

The conflict/shared-stack review should show:

- stack id
- active source state
- deactivated source state
- reactivation source state
- persistence state
- export-summary state
- built-ins win by default yes/no
- conflict visible yes/no
- exported state does not override built-in yes/no
- future policy required yes/no

Conflicts must remain visible. Built-ins remain authoritative by default.
User/plugin manifests remain untrusted. The GUI must not resolve shared-stack
conflicts by mutating candidate state, restoring trust, deleting records, or
auto-activating a candidate.

## 17. Unsafe-claim review

The unsafe-claim review should show:

- claim id
- claim text
- blocked yes/no
- accepted false
- reason
- related diagnostic code
- future gate required

Unsafe claims include validation success, validation failure reversal, issue
closure, bundled solver availability, release mutation, tag mutation, asset
mutation, dependency installation, solver execution, trust restoration, and
industrial certification. Unsafe claims must remain blocked display state.

## 18. Evidence/history review

The evidence/history review should show:

- evidence id
- evidence kind
- source id
- candidate stack id
- deactivation history state
- reactivation history state
- historical evidence state
- validation evidence state
- historical validation evidence retained
- skipped-missing remains skipped-missing
- validation success claimed false
- validation failure claimed false
- issue closure implied false

Deactivation/reactivation history and historical evidence must be retained. The
GUI must not erase history, turn skipped-missing into pass/fail evidence, close
issues, or certify optional solver availability.

## 19. Limitation review

The limitation review should show:

- limitation id
- title
- text
- severity
- related section
- future gate, if any

Limitations are first-class visible rows. They must include the educational and
research scope boundary, non-validation boundary, non-certification boundary,
non-persistence boundary, non-reloadable-bundle boundary, no solver execution,
and live optional validation issue separation.

## 20. Trust/provenance behavior

Trust/provenance behavior should follow these rules:

- user-selected and plugin-provided manifests are untrusted by default
- built-ins remain authoritative by default
- trust labels are labels only
- trust label is not certification
- source fingerprints are not trust restoration
- export summaries are not validation evidence
- export summaries are not persistence
- export summaries are not reloadable bundles
- export-summary GUI is not file export
- export-summary GUI is not clipboard behavior
- export-summary GUI is not report attachment

Trust elevation requires a separate future gate with evidence and user review.

## 21. Non-action flag rendering

The future GUI should visibly render non-action flags from the view-model:

- export performed false
- file write performed false
- export file created false
- report file created false
- clipboard performed false
- report attachment performed false
- reloadable bundle created false
- persistence performed false
- settings file created false
- runtime state file created false
- schema file created false
- ProjectSchema mutation performed false
- GUI implementation performed false
- CLI behavior performed false
- reload performed false
- source behavior mutation performed false
- automatic activation performed false
- trust restoration performed false
- file restoration performed false
- file rewrite performed false
- file deletion performed false
- dependency installation performed false
- dependency uninstall performed false
- solver uninstall performed false
- plugin package import performed false
- directory scan performed false
- network fetch performed false
- discovery execution performed false
- validation execution performed false
- solver execution performed false
- issue mutation performed false
- release mutation performed false
- tag mutation performed false
- asset mutation performed false
- version bump performed false
- validation-pass claim false
- validation-fail claim false
- issue-closure claim false
- certification claim false

Non-action flags are part of the review surface, not implementation switches.

## 22. Action-state model

The action-state model should render every action as disabled or future-only
unless a later gate explicitly implements it:

- review summary: enabled only as display
- acknowledge export boundaries: future widget-local only
- review redaction: future widget-local only
- request file export: disabled/future-only
- copy to clipboard: disabled/future-only
- attach report: disabled/future-only
- create reloadable bundle: disabled/future-only
- persist state: disabled/future-only
- reload state: disabled/future-only
- mutate ProjectSchema: disabled/future-only
- activate candidate: disabled/future-only
- restore trust: disabled/future-only
- run discovery: disabled/future-only
- run validation: disabled/future-only
- execute solver: disabled/future-only
- install dependency: disabled/future-only
- uninstall dependency: disabled/future-only
- uninstall solver: disabled/future-only
- close issue: disabled/future-only
- mutate release: disabled/future-only
- mutate tag: disabled/future-only
- mutate asset: disabled/future-only

No disabled action is wired to a callback in this design gate.

## 23. Relationship to OSW-EXP-091 export-summary design

OSW-EXP-091 defines export-summary semantics as design-only. This GUI design is
a future review surface over that contract. It does not change the OSW-EXP-091
definition of export summary, export preconditions, acknowledgement model,
redaction policy, stale-source policy, conflict policy, unsafe-claim policy,
validation/evidence policy, ProjectSchema boundary, or non-actions.

## 24. Relationship to OSW-EXP-097 export-summary view-model

OSW-EXP-097 implements `OptionalSolverPluginManifestExportSummaryViewModel`.
The future GUI should consume that view-model rather than rereading files,
running discovery, importing plugins, scanning directories, fetching network
manifests, recomputing validation, or mutating source state.

The GUI should render:

- `header`
- `sections`
- `source_rows`
- `candidate_rows`
- `acknowledgement_rows`
- `diagnostics`
- `redaction_rows`
- `stale_source_rows`
- `conflict_rows`
- `unsafe_claim_rows`
- `evidence_history_rows`
- `limitation_rows`
- `non_action_flags`
- `actions`
- `reserved_diagnostic_codes`

This design does not change the view-model source.

## 25. Relationship to persistence view-model, schema model, GUI, and CLI

The future export-summary GUI may sit near the persistence GUI panel, but it is
not persistence and does not save or reload state.

- OSW-EXP-092 persistence view-model remains pure.
- OSW-EXP-093 persistence schema model remains in-memory and non-writing.
- OSW-EXP-095 persistence GUI remains review-only and non-writing.
- OSW-EXP-096 persistence CLI remains design-only.
- Export-summary GUI must not mutate persistence view-model, schema-model, GUI,
  or CLI behavior.

Persistence writer behavior, settings files, runtime state files, schema files,
ProjectSchema integration, reload behavior, and state bundles require separate
future gates.

## 26. Relationship to ProjectSchema

No ProjectSchema mutation occurs in this gate.

The future GUI must not write export summaries into ProjectSchema, treat export
summaries as project validation evidence, or infer solver readiness from export
summary display. Any project-local state or report attachment requires a later
gate with focused tests.

## 27. Relationship to reports

The future GUI may provide a review surface near future report/support summary
areas, but this gate adds no report file creation, no report attachment, no
clipboard behavior, and no file export. A report attachment is not validation
evidence. A support summary is not issue closure. Any report integration or file
write requires a separate gate.

## 28. Relationship to live optional validation issues

Live optional validation issues `#6` through `#11` remain open and separate.

An export summary GUI is not live optional validation. It is not validation
success, not validation failure, not issue closure, not bundled solver evidence,
and not certification. Skipped-missing remains skipped-missing until a dedicated
installed-machine validation gate records otherwise.

## 29. Failure handling

The future GUI should handle failure states without side effects:

- show export summary unavailable
- show explicit request required
- show missing acknowledgements
- show redaction required
- show unredacted path blocked
- show stale-source/re-preview required
- show conflict/shared-stack blocked
- show unsafe claim blocked
- show export summary error
- keep all file/export/clipboard/report/reload/persistence actions disabled

Failure handling must not attempt repair by reading files, restoring files,
rewriting files, deleting files, installing dependencies, running discovery,
running validation, executing solvers, or mutating issues/releases.

## 30. Diagnostics reserved

Future export-summary GUI diagnostic code names are reserved only:

- `OSPMG_EXPORT_SUMMARY_GUI_NOT_IMPLEMENTED`
- `OSPMG_EXPORT_SUMMARY_GUI_STATE_UNAVAILABLE`
- `OSPMG_EXPORT_SUMMARY_GUI_EXPLICIT_REQUEST_REQUIRED`
- `OSPMG_EXPORT_SUMMARY_GUI_ACK_REQUIRED`
- `OSPMG_EXPORT_SUMMARY_GUI_NOT_VALIDATION`
- `OSPMG_EXPORT_SUMMARY_GUI_NOT_PERSISTENCE`
- `OSPMG_EXPORT_SUMMARY_GUI_NOT_RELOADABLE_BUNDLE`
- `OSPMG_EXPORT_SUMMARY_GUI_NOT_TRUST_RESTORE`
- `OSPMG_EXPORT_SUMMARY_GUI_NO_INSTALL`
- `OSPMG_EXPORT_SUMMARY_GUI_NO_SOLVER_EXECUTION`
- `OSPMG_EXPORT_SUMMARY_GUI_NOT_ISSUE_CLOSURE`
- `OSPMG_EXPORT_SUMMARY_GUI_NOT_RELEASE_MUTATION`
- `OSPMG_EXPORT_SUMMARY_GUI_REDACTION_REQUIRED`
- `OSPMG_EXPORT_SUMMARY_GUI_UNREDACTED_PATH_BLOCKED`
- `OSPMG_EXPORT_SUMMARY_GUI_STALE_SOURCE_REPREVIEW_REQUIRED`
- `OSPMG_EXPORT_SUMMARY_GUI_UNTRUSTED_SOURCE`
- `OSPMG_EXPORT_SUMMARY_GUI_CONFLICT_BLOCKED`
- `OSPMG_EXPORT_SUMMARY_GUI_UNSAFE_CLAIM`
- `OSPMG_EXPORT_SUMMARY_GUI_EVIDENCE_RETAINED`
- `OSPMG_EXPORT_SUMMARY_GUI_HISTORY_RETAINED`
- `OSPMG_EXPORT_SUMMARY_GUI_LIMITATION_VISIBLE`
- `OSPMG_EXPORT_SUMMARY_GUI_NO_DISCOVERY_EXECUTION`
- `OSPMG_EXPORT_SUMMARY_GUI_NO_PLUGIN_IMPORT`
- `OSPMG_EXPORT_SUMMARY_GUI_NO_FILE_EXPORT`
- `OSPMG_EXPORT_SUMMARY_GUI_NO_CLIPBOARD`
- `OSPMG_EXPORT_SUMMARY_GUI_NO_REPORT_ATTACHMENT`
- `OSPMG_EXPORT_SUMMARY_GUI_FUTURE_GATE`

These names do not implement diagnostics in source code. A future implementation
gate may map OSW-EXP-097 `OSPMG_EXPORT_SUMMARY_*` diagnostics into GUI display
diagnostics.

## 31. Non-actions

This gate does not:

- implement GUI code
- implement file export
- write files as runtime behavior
- create export files
- create report files
- add clipboard behavior
- add report attachment behavior
- add open-output-folder behavior
- create reloadable bundles
- implement runtime persistence behavior
- create settings files
- create runtime state files
- create schema files
- mutate ProjectSchema
- implement CLI behavior
- implement reload behavior
- mutate activation source behavior
- mutate deactivation source behavior
- mutate reactivation source behavior
- mutate discovery-refresh source behavior
- mutate persistence source behavior
- automatically activate candidates
- restore trust
- restore files
- rewrite files
- delete files
- install dependencies
- uninstall dependencies
- uninstall solvers
- import plugin packages
- scan directories
- fetch network manifests
- run discovery
- run validation
- execute solvers
- mutate issues
- mutate releases
- mutate tags
- mutate assets
- bump versions
- claim validation success
- claim validation failure
- claim issue closure
- claim certification

## 32. Implementation test plan for a later gate

A later OSW-EXP-099 implementation gate should test, without adding file export:

- widget imports remain optional and PySide-only
- panel consumes a supplied `OptionalSolverPluginManifestExportSummaryViewModel`
- summary fields render false non-action flags
- source/provenance rows redact paths
- candidate rows do not activate or trust candidates
- acknowledgements are widget-local and non-persistent
- diagnostics render severity, blocker, and suggested fix
- stale-source rows require re-preview without scanning directories
- conflicts keep built-ins authoritative by default
- unsafe claims remain blocked
- limitations remain visible
- all file/export/clipboard/report/reload/persistence actions remain absent,
  disabled, or future-only
- no file dialog, save dialog, open-output-folder action, clipboard callback,
  report attachment callback, persistence writer, reload callback, discovery
  callback, validation callback, solver callback, issue callback, release
  callback, tag callback, or asset callback is invoked

Those are future tests. This gate adds only focused docs tests for this design
document and related guardrail/risk/checklist/validation references.

## 33. Future gates

Suggested follow-up gates:

- `OSW-EXP-099_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_GUI_IMPLEMENTATION`
- `OSW-EXP-100_OPTIONAL_SOLVER_PLUGIN_MANIFEST_STATE_WRITER_DESIGN`
- `OSW-EXP-101_OPTIONAL_SOLVER_PLUGIN_MANIFEST_STATE_WRITER_VIEWMODEL_OR_SCHEMA_EXTENSION`
- `OSW-EXP-102_OPTIONAL_SOLVER_PLUGIN_MANIFEST_STATE_WRITER_IMPLEMENTATION`
- `OSW-EXP-103_OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_CLI_IMPLEMENTATION`
- `OSW-EXP-104_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_CLI_DESIGN`
- `OSW-EXP-105_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_CLI_IMPLEMENTATION`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` if a prepared
  machine is available

This sequence follows the latest optional solver plugin manifest UX numbering:
OSW-EXP-091 designed export summaries, OSW-EXP-097 implemented the pure
export-summary view-model, and OSW-EXP-098 designs the future GUI review surface.
If the repository later reserves different numbering, follow the newest
decision-log mapping and keep implementation, writer, CLI, validation, issue,
release, tag, asset, and certification gates separate.
