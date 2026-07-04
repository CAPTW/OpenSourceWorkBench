# Changelog

All notable OpenSolver Workbench changes are summarized here for release
review. OSW follows source-first release evidence; public tags are created only
by a dedicated release/tag gate.

## Unreleased

### OpenFOAM Template v12 pFinal Fix Implementation

- Added algorithm-aware OpenFOAM `pFinal` generation for PISO/`icoFoam` cases
  (cavity always; duct when `icoFoam`) while preserving SIMPLE/`simpleFoam`
  behavior byte-for-byte, via a `_PFINAL_SOLVER_BLOCK` (`pFinal { $p; relTol 0; }`)
  injected through a `$pfinal_block` `fvSolution` placeholder. The cavity golden
  fixture gains `pFinal`; the duct golden fixture is unchanged; `physicalProperties`
  behavior is unchanged. Source/golden/unit coverage with no live solver execution
  in the implementation gate; no issue mutation, no release/tag/asset mutation, no
  ProjectSchema mutation, no version bump, and no certification,
  production-readiness, bundled-solver, or native-Windows validation claims.

### OpenFOAM Template v12 pFinal Fix Design

- Designed an algorithm-aware OpenFOAM `pFinal` template fix for issue `#19`,
  preserving SIMPLE/`simpleFoam` behavior while planning PISO/`icoFoam`
  `system/fvSolution` support (add `pFinal { $p; relTol 0; }` for PISO cases only,
  gated on the selected algorithm rather than the property-file layout), with a
  golden fixture strategy and an `OSW_OPENFOAM_FVSOLUTION_*` diagnostics
  reservation. Design-only: no source changes, no template changes, no golden
  fixture changes, no solver execution, no live validation, no issue mutation, no
  release/tag/asset mutation, no ProjectSchema mutation, and no certification,
  production-readiness, bundled-solver, or native-Windows validation claims.

### OpenFOAM Template v12 Compatibility Fix Implementation

- Added variant-aware OpenFOAM property-file generation so legacy/ESI cases keep
  `constant/transportProperties` while OpenFOAM Foundation v11/v12 cases can emit
  `constant/physicalProperties`, selectable via the `OpenFOAMPropertyFileLayout`
  enum, the cavity/duct config `property_file_layout`, request metadata, and the
  `openfoam-write-case --property-file-layout {legacy,foundation_v11_plus}` CLI
  option (default `legacy`). Covered by unit and golden tests for both layouts on
  cavity and duct with no live solver execution in the implementation gate. Issue
  `#18` remains open for separate live validation; no OpenFOAM run, no issue
  mutation, no release/tag/asset mutation, no ProjectSchema mutation, no version
  bump, and no certification, production-readiness, bundled-solver, or
  native-Windows validation claims.

### OpenFOAM Template v12 Compatibility Fix Design

- Designed a variant-aware OpenFOAM template compatibility fix for issue `#18`,
  preserving legacy-Foundation/ESI `constant/transportProperties` support while
  planning OpenFOAM Foundation v11/v12 `constant/physicalProperties` support, with
  a variant selection policy, a golden fixture strategy, and an
  `OSW_OPENFOAM_TEMPLATE_*` diagnostics reservation. Design-only: no OpenFOAM
  source, template, or golden-fixture changes, no solver execution, no live
  validation, no issue/release/tag/asset mutation, no ProjectSchema mutation, and
  no certification, production-readiness, bundled-solver, or native-Windows
  validation claims.

### Optional Solver Prepared-Machine Validation Command Implementation

- Added a local-only optional solver prepared-machine validation command with
  explain, prerequisites, preflight, plan, run, diagnostics, evidence, and
  safety outputs, preserving no dependency installation, no solver execution,
  no ProjectSchema mutation, no issue/release mutation, and no certification
  claims.

### Optional Solver Prepared-Machine Validation Command Design

- Designed a future optional solver prepared-machine validation command with
  explicit preflight, plan, run, diagnostics, evidence, and safety boundaries
  while preserving no implementation, no dependency installation, no solver
  execution, no ProjectSchema mutation, no issue/release mutation, and no
  certification claims.

### Optional Solver Prepared-Machine Manifest-State Validation Prerequisites

- Documented the parked optional solver prepared-machine manifest-state
  validation prerequisites, including missing local solver/package
  requirements and the requirement for a safe runnable validation command
  before retrying validation.

### Optional Solver Plugin Manifest Reload Acceptance Persistence ProjectSchema Boundary Implementation

- Added a pure in-memory optional solver plugin manifest reload acceptance
  persistence ProjectSchema boundary model that keeps supplied persistence,
  writer, CLI, GUI, and summary audit records separate from ProjectSchema state
  and validation evidence while preserving no ProjectSchema mutation, no file
  IO, no writer invocation, no runtime acceptance, no discovery/validation/
  solver execution, no automatic activation, no trust restoration, no
  issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance Persistence ProjectSchema Boundary Design

- Designed the optional solver plugin manifest reload acceptance persistence
  ProjectSchema boundary to keep local persistence records, writer results,
  CLI/GUI writes, and summary audits separate from ProjectSchema state and
  validation evidence, preserving no implementation, no ProjectSchema mutation,
  no writer invocation, no file IO, no runtime acceptance, no discovery/
  validation/solver execution, no automatic activation, no trust restoration,
  no issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance Persistence Summary Audit Implementation

- Added a pure in-memory optional solver plugin manifest reload acceptance
  persistence summary audit model that summarizes supplied view-model, writer,
  CLI, and GUI records while preserving no file IO, no writer invocation, no
  runtime acceptance, no ProjectSchema mutation, no discovery/validation/solver
  execution, no automatic activation, no trust restoration, no issue/release
  mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance Persistence Summary Audit Design

- Designed the optional solver plugin manifest reload acceptance persistence
  summary audit surface as a future non-authoritative review over supplied
  persistence view-model, writer, CLI write, and GUI write records, preserving
  no summary audit implementation, no source edits, no writer invocation, no
  file reads or writes, no runtime acceptance, no ProjectSchema mutation, no
  discovery/validation/solver execution, no automatic activation, no trust
  restoration, no issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance Persistence CLI Write Implementation

- Added the optional solver plugin manifest reload acceptance persistence CLI
  `write` subcommand as an explicit-target, dry-run-first,
  acknowledgement-gated, confirmation-gated local review-record write path
  through the OSW-EXP-126 writer, preserving no input state-file
  reading/parsing, no reload file-reader or OSW-EXP-102 state-writer
  invocation, no GUI/subprocess behavior, no runtime acceptance, no
  ProjectSchema mutation, no discovery/validation/solver execution, no
  automatic activation, no trust restoration, no issue/release mutation, and no
  certification claims.

### Optional Solver Plugin Manifest Reload Acceptance Persistence CLI Write Design

- Designed the optional solver plugin manifest reload acceptance persistence CLI
  write workflow as a future explicit-target, dry-run-first,
  acknowledgement-gated, confirmation-gated path through the persistence
  writer, preserving no CLI implementation, no writer invocation, no file
  writes, no runtime acceptance, no ProjectSchema mutation, no discovery/
  validation/solver execution, no automatic activation, no trust restoration,
  no issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance Persistence GUI Write Implementation

- Added an explicit-target, dry-run-first optional solver plugin manifest reload
  acceptance persistence GUI write panel that writes local review records only
  through the OSW-EXP-126 writer after fresh dry-run, acknowledgement, and
  confirmation, preserving no write on construction/refresh/target
  assignment/dry-run, no default/background path, no input state-file parsing,
  no reload file-reader or OSW-EXP-102 state-writer invocation, no CLI
  subprocess, no runtime acceptance, no ProjectSchema mutation, no discovery/
  validation/solver execution, no automatic activation, no trust restoration,
  no issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance Persistence GUI Write Design

- Designed the optional solver plugin manifest reload acceptance persistence GUI
  write workflow as a future explicit-target, dry-run-first,
  acknowledgement-gated, confirmation-gated path through the persistence
  writer, preserving no GUI implementation, no writer invocation, no file
  writes, no runtime acceptance, no ProjectSchema mutation, no discovery/
  validation/solver execution, no automatic activation, no trust restoration,
  no issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance Persistence GUI Review Implementation

- Added a display-only optional solver plugin manifest reload acceptance
  persistence GUI review panel that renders supplied persistence view-model and
  writer dry-run/result records while preserving no writer invocation, no file
  writes, no input state-file parsing, no runtime acceptance, no ProjectSchema
  mutation, no discovery/validation/solver execution, no automatic activation,
  no trust restoration, no issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance Persistence GUI Review Design

- Designed the optional solver plugin manifest reload acceptance persistence
  GUI review surface as a future display-only PySide surface over the
  persistence view-model and writer dry-run/result records, preserving no GUI
  implementation, no writer invocation, no file writes, no runtime acceptance,
  no ProjectSchema mutation, no discovery/validation/solver execution, no
  automatic activation, no trust restoration, no issue/release mutation, and no
  certification claims.

### Optional Solver Plugin Manifest Reload Acceptance Persistence CLI Implementation

- Added a stdout-first optional solver plugin manifest reload acceptance
  persistence CLI review surface that renders deterministic persistence
  view-model records and dry-run writer plans while keeping `write-future`
  disabled/future-only and preserving no actual CLI writes, no writer call with
  `dry_run=False`, no input state-file reading or parsing, no reload
  file-reader invocation, no OSW-EXP-102 state-writer invocation, no GUI
  subprocess, no runtime reload acceptance, no active acceptance mutation, no
  ProjectSchema mutation, no default/background write, no discovery/validation/
  solver execution, no automatic activation, no trust restoration, no
  issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance Persistence CLI Design

- Designed a future stdout-first optional solver plugin manifest reload
  acceptance persistence CLI review/write-plan surface over the persistence
  view-model and explicit writer boundaries, preserving no CLI implementation,
  no source edits, no writer invocation, no file writes, no file reading or
  parsing, no input state-file parsing, no reload file-reader invocation, no
  runtime acceptance, no ProjectSchema mutation, no default/background write, no
  discovery/validation/solver execution, no automatic activation, no trust
  restoration, no issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance Persistence Writer

- Added an explicit-path, dry-run-first optional solver plugin manifest reload
  acceptance persistence writer for local review records, preserving no runtime
  acceptance, no default/background path, no input state-file parsing, no reload
  file-reader invocation, no CLI/GUI behavior, no ProjectSchema mutation, no
  discovery/validation/solver execution, no automatic activation, no trust
  restoration, no issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance Persistence ViewModel

- Added a pure in-memory optional solver plugin manifest reload acceptance
  persistence view-model that renders future writer readiness, write-plan data,
  storage policy, acknowledgements, expiry, blockers, diagnostics, non-action
  flags, disabled/future actions, provenance, evidence/history, and safety
  guidance while preserving no persistence writes, no checked-in state files,
  no runtime acceptance, no file IO, no reader/writer invocation, no CLI/GUI
  behavior, no subprocess use, no ProjectSchema mutation, no discovery/
  validation/solver execution, no automatic activation, no trust restoration,
  no issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance Persistence Design

- Designed optional solver plugin manifest reload acceptance persistence
  semantics as a future explicit, redacted, dry-run-first, non-authoritative
  review-state record over the reload acceptance view-model, preserving no
  source implementation, no persistence write, no runtime acceptance, no file
  IO, no reader invocation, no ProjectSchema mutation, no default/background
  reload, no discovery/validation/solver execution, no automatic activation, no
  trust restoration, no issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance CLI Implementation

- Added a stdout-first optional solver plugin manifest reload acceptance CLI
  review surface that renders acceptance readiness, blockers,
  acknowledgements, expiry, diagnostics, non-action flags, disabled/future
  actions, and safety guidance while preserving no runtime acceptance, no file
  IO, no reader invocation, no GUI subprocess, no persistence write, no
  ProjectSchema mutation, no discovery/validation/solver execution, no
  automatic activation, no trust restoration, no issue/release mutation, and no
  certification claims.

### Optional Solver Plugin Manifest Reload Acceptance CLI Design

- Designed optional solver plugin manifest reload acceptance CLI semantics as a
  future stdout-first review surface over supplied reload acceptance view-model
  records, preserving no CLI implementation, no acceptance commands or flags, no
  runtime acceptance, no file IO, no reader invocation, no GUI subprocess use,
  no persistence write, no ProjectSchema mutation, no discovery/validation/
  solver execution, no automatic activation, no trust restoration, no
  issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance GUI

- Added a view-model-only optional solver plugin manifest reload acceptance GUI
  review panel over supplied acceptance view-model records, rendering readiness,
  blockers, acknowledgements, expiry, accepted-state scope, provenance,
  diagnostics, non-action flags, disabled/future actions, and safety guidance
  while preserving no runtime acceptance, no file IO, no reader or CLI bridge,
  no persistence write, no ProjectSchema mutation, no discovery/validation/
  solver execution, no automatic activation, no trust restoration, no
  issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance GUI Design

- Designed optional solver plugin manifest reload acceptance GUI semantics as a
  future view-model-only review surface over the reload acceptance view-model,
  preserving no GUI implementation, no runtime acceptance, no persistence write,
  no ProjectSchema mutation, no default/background reload, no discovery/
  validation/solver execution, no automatic activation, no trust restoration,
  no issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance ViewModel

- Added a pure optional solver plugin manifest reload acceptance view-model that
  models reviewed-preview readiness, blockers, acknowledgements, diagnostics,
  accepted-for-session-review state, future activation/discovery review
  requirements, non-action flags, and disabled/future actions while preserving
  no runtime acceptance, no persistence writes, no ProjectSchema mutation, no
  discovery/validation/solver execution, no automatic activation, no trust
  restoration, no issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload Acceptance Design

- Designed optional solver plugin manifest reload acceptance semantics as a
  future explicit reviewed-preview-to-session-state boundary, preserving no
  implementation, no runtime reload acceptance, no persistence write, no
  ProjectSchema mutation, no default/background reload, no discovery/validation/
  solver execution, no automatic activation, no trust restoration, no
  issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload GUI File Dialog

- Added an explicit optional solver plugin manifest reload GUI file-dialog
  preview wrapper that routes one user-selected state-writer UX state file
  through the reload file reader and existing reload review panel, preserving
  reader-first diagnostics, redacted selected-file display, cancellation as a
  non-error, no default/background reload, no CLI subprocess use, no
  ProjectSchema mutation, no discovery/validation/solver execution, no
  automatic activation, no trust restoration, no issue/release mutation, and no
  certification claims.

### Optional Solver Plugin Manifest Reload GUI File Dialog Design

- Designed optional solver plugin manifest reload GUI file-dialog semantics as a
  future explicit user-selected file bridge from the reload GUI to the
  explicit-path library reader and reload view-model review, preserving no
  implementation, no default path, no background reload, no CLI subprocess use,
  no ProjectSchema mutation, no discovery/validation/solver execution, no
  automatic activation, no trust restoration, no issue/release mutation, and no
  certification claims.

### Optional Solver Plugin Manifest Reload CLI Explicit Path

- Added explicit-path optional solver plugin manifest reload CLI preview via
  `load-preview --path`, routing local state-writer UX state files through the
  reload file reader and reload view-model review while preserving stdout-first
  diagnostics, no default/background reload, no GUI file dialog, no
  ProjectSchema mutation, no discovery/validation/solver execution, no automatic
  activation, no trust restoration, no issue/release mutation, and no
  certification claims.

### Optional Solver Plugin Manifest Reload CLI Explicit-Path Design

- Designed optional solver plugin manifest reload CLI explicit-path semantics as
  a future `load-preview --path` bridge from the existing reload CLI to the
  explicit-path library reader and reload view-model review, preserving no
  implementation, no default path, no background reload, no GUI file dialog, no
  ProjectSchema mutation, no discovery/validation/solver execution, no automatic
  activation, no trust restoration, no issue/release mutation, and no
  certification claims.

### Optional Solver Plugin Manifest Reload File Reader

- Added an explicit-path optional solver plugin manifest reload file reader
  (`OptionalSolverPluginManifestReloadFileReader` /
  `read_optional_solver_plugin_manifest_reload_file`) that reads exactly one
  caller-provided local file, validates the bounded OSW-EXP-102 state-writer
  payload family (eligibility, size, UTF-8/JSON object root, duplicate keys,
  payload kind, schema/migration, redaction/secret, non-action flags, unsafe
  claims, stale-source, conflict, evidence), and returns `OSPMG_RELOAD_READER_*`
  diagnostics plus a sanitized in-memory mapping for OSW-EXP-107 reload view-model
  review.
- Kept the reader library-level and side-effect-free: no default paths, no
  background reload, no directory scan, no network fetch, no plugin package import,
  no CLI explicit-path wiring, no GUI file dialogs, no runtime reload acceptance,
  no reloadable bundles, no export/report files, no clipboard/open-folder behavior,
  no ProjectSchema mutation, no discovery/validation/solver execution, no
  dependency install/uninstall, no automatic activation, no trust restoration, no
  issue/release/tag/asset mutation, no version bump, and no validation-pass/fail,
  issue-closure, bundled-solver, or certification claims. The reader writes,
  creates, and deletes no files and never leaks raw paths in diagnostics.

### Optional Solver Plugin Manifest Reload File Reader Design

- Designed optional solver plugin manifest reload file-reader semantics as a
  future explicit-local-path reader/parser boundary for state-writer-produced UX
  state files, defining explicit-path, file-eligibility, encoding/JSON,
  payload-kind/schema, writer-metadata/provenance, non-action-flag,
  redaction/privacy, acknowledgement/expiry, candidate-lifecycle,
  stale-source/re-preview, conflict/shared-stack, unsafe-claim, and
  evidence/history policies, plus a reader report model, an
  `OSPMG_RELOAD_READER_*` diagnostics reservation, a security/privacy review, a
  future implementation test plan, and future gates.
- Kept the gate design-only: no file reader implementation, no parser
  implementation, no runtime file reading, no runtime state parsing, no source
  edit, no CLI source edit, no GUI source edit, no default reload path, no
  background reload, no directory scan, no network fetch, no plugin package
  import, no runtime reload, no reloadable bundle creation, no export/report file
  creation, no clipboard/report/open-folder behavior, no ProjectSchema mutation,
  no live discovery, no passive refresh, no validation execution, no solver
  execution, no dependency install/uninstall, no automatic activation, no trust
  restoration, no issue/release/tag/asset mutation, no version bump, and no
  validation-pass/fail, issue-closure, bundled-solver, or certification claims.

### Optional Solver Plugin Manifest Reload CLI

- Added a stdout-first optional solver plugin manifest reload CLI review
  surface over deterministic in-memory reload view-model state, with text/JSON
  output for summary, schema, sources, candidates, acknowledgements,
  diagnostics, redaction, stale-source, conflict, unsafe-claim,
  evidence/history, and disabled/future action states.
- Kept reload CLI implementation review-only: no file reader/parser, no
  persisted state file reading/parsing, no runtime reload, no default reload
  path, no background reload, no ProjectSchema mutation, no GUI behavior, no
  discovery/validation/solver execution, no automatic activation, no trust
  restoration, no issue/release/tag/asset mutation, no validation-pass/fail
  claim, and no certification claim.

### Optional Solver Plugin Manifest Reload CLI Design

- Designed optional solver plugin manifest reload CLI semantics as a future
  headless, stdout-first, review-only command surface over existing reload
  view-model records, preserving no CLI source edits, no file reader/parser,
  no runtime reload, no default reload path, no ProjectSchema mutation, no
  discovery/validation/solver execution, no automatic activation, no trust
  restoration, no issue/release mutation, and no certification claims.

### Optional Solver Plugin Manifest Reload GUI

- Added a read-only optional solver plugin manifest reload GUI review panel over
  existing reload view-model records, rendering schema, redaction,
  acknowledgement-expiry, stale-source, conflict, unsafe-claim,
  evidence/history, trust/provenance diagnostics, and disabled/future actions
  without file dialogs, runtime reload, file reader/parser behavior,
  ProjectSchema mutation, discovery/validation/solver execution, automatic
  activation, trust restoration, issue/release mutation, or certification
  claims.

### Optional Solver Plugin Manifest Reload GUI Design

- Designed optional solver plugin manifest reload GUI semantics as a future
  read-only, review-only PySide surface over existing reload view-model records,
  preserving no file dialog, no runtime reload, no file reader/parser, no
  ProjectSchema mutation, no discovery/validation/solver execution, no
  automatic activation, no trust restoration, no issue/release mutation, and no
  certification claims.

### Optional Solver Plugin Manifest Reload View-Model

- Added a pure optional solver plugin manifest reload view-model over
  caller-supplied persisted-state mappings, surfacing schema, redaction,
  acknowledgement-expiry, stale-source, conflict, unsafe-claim,
  evidence/history, trust/provenance diagnostics, and disabled/future actions
  without reading files, implementing runtime reload, mutating ProjectSchema,
  running discovery/validation/solver execution, restoring trust, or activating
  candidates.

### Optional Solver Plugin Manifest Reload Design

- Designed optional solver plugin manifest reload semantics as a future
  explicit, schema-aware, redaction-first, acknowledgement-aware,
  stale-source-aware, conflict-aware, unsafe-claim-blocking, non-validating,
  non-trust-restoring, non-activating, non-discovering, non-executing,
  ProjectSchema-safe, issue/release-safe workflow without implementing reload
  behavior, reading state files, or creating reloadable bundles.

### Optional Solver Plugin Manifest Export-Summary CLI

- Added a stdout-first optional solver plugin manifest export-summary CLI for
  redacted, human-reviewable diagnostics, acknowledgements, source/provenance,
  candidate, stale-source, conflict, unsafe-claim, evidence/history, limitation,
  and action-state inspection without export/report/reloadable-bundle files,
  clipboard/report/open-folder behavior, live discovery, validation, solver
  execution, ProjectSchema mutation, or issue/release mutation.

### Optional Solver Plugin Manifest Export-Summary CLI Design

- Designed optional solver plugin manifest export-summary CLI semantics as a
  future redaction-first, stdout-first, human-reviewable, non-validating,
  non-trust-restoring, non-activating, non-reloading, non-discovering,
  non-executing, no-report-attachment, no-clipboard, no-open-folder,
  issue/release-safe workflow without implementing CLI behavior or creating
  export/report/reloadable-bundle outputs.

### Optional Solver Plugin Manifest Persistence CLI

- Added a dry-run-first optional solver plugin manifest persistence CLI over the
  explicit state-writer library, requiring caller-supplied paths and
  acknowledgements for writes while preserving no live discovery, no
  ProjectSchema mutation, no GUI/reload/export/report/clipboard behavior, no
  validation, no solver execution, and issue/release-safe boundaries.

### Optional Solver Plugin Manifest State Writer

- Added an explicit local optional solver plugin manifest state writer that
  serializes redacted view-model state to caller-supplied paths with
  deterministic JSON, dry-run/preflight diagnostics, explicit write
  acknowledgement, and atomic temp-file/replace behavior.
- Preserved the bounded writer scope: no default write path, no directory
  creation, no settings files, no schema files, no export/report files, no
  reloadable bundles, no ProjectSchema mutation, no GUI/CLI/reload/export/
  clipboard/open-folder behavior, no discovery, no validation, no solver
  execution, no issue/release/tag/asset mutation, no validation-pass/fail claim,
  no issue-closure claim, and no certification claim.

### Optional Solver Plugin Manifest State Writer View-Model

- Added a pure optional solver plugin manifest state-writer readiness/write-plan
  view-model for deterministic storage options, schema readiness, redaction,
  acknowledgements, stale-source/re-preview, conflicts, unsafe claims,
  evidence/history, atomicity/error planning, non-action flags, diagnostics,
  and disabled/future actions.
- Kept the slice side-effect-free and non-writing: no writer implementation, no
  file writes, no directory creation, no runtime state files, no settings files,
  no schema files, no ProjectSchema mutation, no GUI/CLI/reload/export behavior,
  no discovery, no validation, no solver execution, and no issue/release
  mutation.

### Optional Solver Plugin Manifest State Writer Design

- Designed optional solver plugin manifest state-writer semantics as a future
  explicit, redaction-first, schema-versioned, acknowledgement-aware,
  stale-source-aware, conflict-aware, unsafe-claim-blocking, history-retaining,
  non-validating, non-trust-restoring, non-activating, non-installing,
  non-executing, and issue/release-safe workflow.
- Kept the slice docs/tests-only: no writer implementation, no file writes, no
  runtime state files, no settings files, no schema files, no export files, no
  report files, no reloadable bundles, no ProjectSchema mutation, no GUI/CLI/
  reload/export behavior, no file/save dialogs, no clipboard/report/open-folder
  behavior, no automatic activation, no trust restoration, no file mutation, no
  dependency install/uninstall, no solver uninstall, no plugin package import,
  no directory scan, no network fetch, no discovery/validation/solver execution,
  no issue/release/tag/asset mutation, no version bump, no validation-pass/fail
  claim, and no certification claim.

### Optional Solver Plugin Manifest Export-Summary GUI

- Added a view-model driven PySide export-summary GUI review surface for
  optional solver plugin manifests, preserving non-exporting, no file writes, no
  clipboard, no report attachment, no reloadable bundle, no persistence, no
  ProjectSchema mutation, no CLI/reload behavior, no discovery, no validation,
  no solver execution, and issue/release-safe boundaries.
- Rendered header, sections, source/provenance, candidate, acknowledgement,
  diagnostic, redaction/privacy, stale-source/re-preview, conflict/shared-stack,
  unsafe-claim, evidence/history, limitation, trust/provenance, non-action flag,
  safety, and disabled/future action-state records.

### Optional Solver Plugin Manifest Export-Summary GUI Design

- Designed optional solver plugin manifest export-summary GUI semantics as a
  future view-model driven, redaction-first, acknowledgement-aware,
  stale-source-aware, limitation-visible, history-retaining, non-validating,
  non-writing, non-persistent, non-reloadable, non-installing, non-executing,
  non-mutating, and issue/release-safe review workflow.
- Defined future export-summary header, sections, source/provenance, candidate
  summary, acknowledgement, diagnostics, redaction/privacy, stale-source/
  re-preview, conflict/shared-stack, unsafe-claim, evidence/history, limitation,
  non-action flag, action-state, and `OSPMG_EXPORT_SUMMARY_GUI_*` diagnostic
  design boundaries.
- Kept the slice docs/tests-only: no GUI implementation, no file export, no file
  writes, no export file creation, no report file creation, no clipboard
  behavior, no report attachment, no open-output-folder behavior, no reloadable
  bundle creation, no runtime persistence behavior, no settings file creation,
  no runtime state file creation, no schema file creation, no ProjectSchema
  mutation, no CLI behavior, no reload behavior, no source behavior mutation, no
  automatic activation, no trust restoration, no file mutation, no dependency
  install/uninstall, no solver uninstall, no plugin package import, no directory
  scan, no network fetch, no discovery execution, no validation execution, no
  solver execution, no issue/release/tag/asset mutation, no version bump, no
  validation-pass/fail claim, and no certification claim.

### Optional Solver Plugin Manifest Export-Summary View-Model

- Added a pure optional solver plugin manifest export-summary view-model for
  redacted, human-reviewable, non-authoritative summary sections, sources,
  candidates, acknowledgements, diagnostics, limitations, redaction/privacy,
  stale-source/re-preview, conflicts, unsafe claims, evidence/history,
  non-action flags, and disabled/future action states.
- Added in-memory adapters from the persistence view-model and in-memory
  persistence schema model without mutating either source contract.
- Kept the slice side-effect-free and non-writing: no file export, no file
  writes, no export file creation, no clipboard behavior, no report attachment,
  no reloadable bundle creation, no runtime persistence behavior, no settings
  file creation, no runtime state file creation, no schema file creation, no
  ProjectSchema mutation, no GUI/CLI behavior, no reload behavior, no automatic
  activation, no trust restoration, no file mutation, no dependency
  install/uninstall, no solver uninstall, no plugin package import, no directory
  scan, no network fetch, no discovery execution, no validation execution, no
  solver execution, no issue/release/tag/asset mutation, no version bump, no
  validation-pass/fail claim, and no certification claim.

### Optional Solver Plugin Manifest Persistence CLI Design

- Designed optional solver plugin manifest persistence CLI semantics as a future
  dry-run/review/explain workflow over persistence readiness, preserving
  redaction-first, acknowledgement-aware, schema/migration-aware,
  stale-source-aware, history-retaining, non-validating, non-writing,
  non-installing, non-executing, non-mutating, and issue/release-safe
  boundaries.
- Defined future command vocabulary, stdout-only output modes, user flow states,
  summary output, acknowledgement expiry, redaction/privacy, schema/migration,
  stale-source/re-preview, conflict/shared-stack, unsafe-claim,
  evidence/history, trust/provenance, action-state, exit-code, and
  `OSPMG_PERSISTENCE_CLI_*` diagnostic design boundaries.
- Kept the slice docs/tests-only: no CLI implementation, no runtime persistence
  behavior, no file writes, no settings file creation, no runtime state file
  creation, no schema file creation, no ProjectSchema mutation, no save/load/
  reload/export behavior, no clipboard/open-output-folder behavior, no GUI
  behavior, no automatic activation, no trust restoration, no file mutation, no
  dependency install/uninstall, no solver uninstall, no plugin package import,
  no directory scan, no network fetch, no discovery execution, no validation
  execution, no solver execution, no issue/release/tag/asset mutation, no
  version bump, no validation-pass/fail claim, and no certification claim.

### Optional Solver Plugin Manifest Persistence GUI

- Added `OptionalSolverPluginManifestPersistencePanel`, a view-model/schema-model
  driven PySide review panel for supplied optional solver plugin manifest
  persistence readiness records.
- Rendered summary, sources, candidates, acknowledgements and expiry policy,
  diagnostics, redaction/privacy, schema/migration, stale-source/re-preview,
  conflict/shared-stack, unsafe-claim, evidence/history, trust/provenance,
  non-action flag, safety, and disabled/future action-state sections, with
  widget-local non-persistent acknowledgement interaction through an injected
  pure callback.
- Kept the slice review-only and non-writing: no runtime persistence behavior, no
  file writes, no settings file creation, no runtime state file creation, no
  schema file creation, no ProjectSchema mutation, no file/save dialogs, no
  reload/export/clipboard/open-output-folder behavior, no CLI behavior, no
  automatic activation, no trust restoration, no file mutation, no dependency
  install/uninstall, no solver uninstall, no plugin package import, no directory
  scan, no network fetch, no discovery execution, no validation execution, no
  solver execution, no issue/release/tag/asset mutation, no version bump, no
  validation-pass/fail claim, and no certification claim.

### Optional Solver Plugin Manifest Persistence GUI Design

- Designed optional solver plugin manifest persistence GUI semantics as a future
  view-model/schema-model driven, explicit, redaction-first,
  acknowledgement-aware, schema/migration-aware, stale-source-aware,
  history-retaining, non-validating, non-writing, non-installing, non-executing,
  non-mutating, and issue/release-safe review workflow.
- Defined future summary, source/candidate, acknowledgement/expiry,
  redaction/privacy, schema/migration, stale-source/re-preview,
  conflict/shared-stack, unsafe-claim, evidence/history, trust/provenance,
  disabled action-state, non-action flag, and `OSPMG_PERSISTENCE_GUI_*`
  diagnostic design boundaries.
- Kept the slice docs/tests-only: no GUI implementation, no runtime persistence
  behavior, no file writes, no settings file creation, no runtime state file
  creation, no schema file creation, no ProjectSchema mutation, no file/save
  dialogs, no reload/export/clipboard/open-output-folder behavior, no CLI
  behavior, no automatic activation, no trust restoration, no file mutation, no
  dependency install/uninstall, no solver uninstall, no plugin package import, no
  directory scan, no network fetch, no discovery execution, no validation
  execution, no solver execution, no issue/release/tag/asset mutation, no version
  bump, no validation-pass/fail claim, and no certification claim.

### Optional Solver Plugin Manifest Persistence Schema Model

- Added a pure, in-memory optional solver plugin manifest persistence schema
  model that defines versioned, JSON-compatible records (header, source,
  candidate, acknowledgement, diagnostic, redaction-policy, migration, conflict,
  unsafe-claim, evidence/history, non-action-flags, and validation-summary) with
  deterministic construction, `to_mapping`/`from_mapping` conversion, mapping
  validation diagnostics, redaction, and adaptation from the OSW-EXP-092
  persistence view-model.
- Reused the reserved `OSPMG_PERSISTENCE_*` diagnostic vocabulary, kept a
  redaction-first policy that blocks raw absolute paths, supported the current
  schema version plus the `osw-exp-092-preview` marker with migration treated as
  a diagnostic, and kept every non-action flag false.
- Kept the slice non-writing and side-effect-free: no persistence
  implementation, no file writes, no schema file creation, no settings file
  creation, no runtime state file creation, no ProjectSchema mutation, no
  GUI/CLI persistence behavior, no reload behavior, no export behavior, no
  automatic activation, no trust restoration, no file restore/rewrite/delete, no
  dependency install/uninstall, no solver uninstall, no plugin package import, no
  directory scan, no network fetch, no discovery execution, no validation
  execution, no solver execution, no issue mutation, no release mutation, no
  version bump, no validation-pass/fail claim, and no certification claim.

### Optional Solver Plugin Manifest Persistence View-Model

- Added a pure optional solver plugin manifest persistence view-model for
  supplied UX state, including summary, candidates, sources, acknowledgements,
  diagnostics, redaction/privacy, schema/migration, stale-source/re-preview,
  conflict/shared-stack, unsafe-claim, evidence/history, trust/provenance, and
  disabled/future action records.
- Kept the slice non-writing and side-effect-free: no persistence
  implementation, no file writes, no settings file creation, no ProjectSchema
  mutation, no GUI/CLI persistence behavior, no reload behavior, no export
  behavior, no automatic activation, no trust restoration, no file
  restore/rewrite/delete, no dependency install/uninstall, no solver uninstall,
  no plugin package import, no directory scan, no network fetch, no discovery
  execution, no validation execution, no solver execution, no issue/release/tag/
  asset mutation, no version bump, no validation-pass/fail claim, and no
  certification claim.

### Optional Solver Plugin Manifest State Export Summary Design

- Designed optional solver plugin manifest state export-summary semantics as a
  future explicit, redaction-first, provenance-preserving, acknowledgement-aware,
  history-retaining, non-validating, non-persistent, non-reloadable-by-default,
  non-installing, non-executing, non-mutating, and issue/release-safe workflow.
- Defined export-summary definition and forbidden content, the export-summary vs
  persistence vs reloadable-bundle boundary, export preconditions, an
  acknowledgement model, a redaction/privacy policy, a conceptual summary content
  model, suggested text/future formats, source/trust/provenance labels, a state
  coverage model with blocked interpretations, stale-source/re-preview and
  conflict/unsafe-claim policies, a validation/evidence policy, a ProjectSchema
  boundary, and design-only `OSPMG_EXPORT_SUMMARY_*` diagnostic reservations.
- Kept the slice docs/tests-only: no export implementation, no file writes, no
  export file creation, no reloadable bundle creation, no clipboard or
  open-output-folder behavior, no persistence implementation, no settings file
  creation, no project schema mutation, no GUI/CLI export behavior, no
  activation/deactivation/reactivation/discovery-refresh source mutation, no
  automatic activation, no trust restoration, no file restore/rewrite/delete, no
  dependency install/uninstall, no solver uninstall, no plugin package import, no
  directory scan, no network fetch, no discovery execution, no validation
  execution, no solver execution, no issue/release/tag/asset mutation, no version
  bump, no validation-pass/fail claim, and no certification claim.

### Optional Solver Plugin Manifest State Persistence Design

- Designed optional solver plugin manifest state persistence semantics as a future
  explicit, versioned, redaction-first, provenance-preserving,
  acknowledgement-aware, history-retaining, non-validating, non-installing,
  non-executing, non-mutating, and issue/release-safe workflow.
- Defined persisted-state definition and forbidden content, storage location
  options, persistence preconditions, an acknowledgement persistence/invalidation
  policy, source/trust/provenance labels, a redaction/privacy policy, a conceptual
  state schema model, a state-machine interaction with blocked transitions, a
  stale-source/re-preview policy, conflict/unsafe-claim policies, a
  validation/evidence policy, and design-only `OSPMG_PERSISTENCE_*` diagnostic
  reservations.
- Kept the slice docs/tests-only: no persistence implementation, no file writes,
  no settings file creation, no project schema mutation, no GUI/CLI persistence
  behavior, no activation/deactivation/reactivation/discovery-refresh source
  mutation, no automatic activation, no trust restoration, no file
  restore/rewrite/delete, no dependency install/uninstall, no solver uninstall, no
  plugin package import, no directory scan, no network fetch, no discovery
  execution, no validation execution, no solver execution, no issue/release/tag/
  asset mutation, no version bump, no validation-pass/fail claim, and no
  certification claim.

### Optional Solver Plugin Manifest Reactivation GUI

- Added a view-model driven PySide reactivation GUI surface for optional solver
  plugin manifests, preserving non-persistence, no automatic activation, no trust
  restoration, no file mutation, no install/uninstall, no discovery, no
  validation, no execution, and issue/release-safe boundaries.
- Rendered reactivation summary, candidates, acknowledgements, blockers,
  diagnostics, shared-stack/conflict warnings, stale-source/re-preview warnings,
  deactivation-history and evidence retention, trust/provenance badges, safety
  guidance, and disabled/future action states from the OSW-EXP-088 reactivation
  view-model, with widget-local non-persistent acknowledgement interaction via an
  injected pure callback.
- Kept the slice safe: no runtime reactivation behavior, no reactivation
  persistence, no automatic activation, no trust restoration, no file
  restore/rewrite/delete, no dependency install/uninstall, no solver uninstall, no
  CLI behavior, no plugin package import, no directory scan, no network fetch, no
  discovery execution, no validation execution, no solver execution, no issue
  mutation, no release mutation, no validation-pass/fail claim, and no
  certification claim.

### Optional Solver Plugin Manifest Reactivation View-Model Extension

- Added a pure optional solver plugin manifest reactivation view-model extension
  for readiness, acknowledgements, stale-source/re-preview diagnostics,
  deactivation-history retention, evidence retention, shared-stack warnings,
  provenance, and disabled/future action states without persistence, automatic
  activation, trust restoration, file mutation, discovery, validation, solver
  execution, or issue/release mutation.
- Modeled the OSW-EXP-087 reactivation state machine and `OSPMG_REACTIVATION_*`
  vocabulary over supplied deactivation candidate data (or caller-supplied
  reactivation candidates) plus acknowledgement/stale-source state, with redacted
  source references and honesty flags that remain false.
- Kept the slice side-effect-free: no reactivation persistence, no automatic
  activation, no trust restoration, no GUI behavior, no CLI behavior, no file
  restore/rewrite/delete, no dependency install/uninstall, no solver uninstall, no
  plugin package import, no directory scan, no network fetch, no discovery
  execution, no validation execution, no solver execution, no issue mutation, no
  release mutation, no validation-pass/fail claim, and no certification claim.

### Optional Solver Plugin Manifest Reactivation Design

- Designed optional solver plugin manifest reactivation semantics as a future
  explicit, acknowledged, provenance-preserving, deactivation-history-retaining,
  non-validating, non-installing, non-executing, non-persistent, and
  issue/release-safe workflow.
- Defined reactivation definition and non-meaning, preconditions,
  acknowledgements, source/trust/provenance labels, a reactivation state machine,
  a conflict/shared-stack policy, a stale-source/re-preview policy, a
  validation/evidence-retention policy, and design-only `OSPMG_REACTIVATION_*`
  diagnostic reservations.
- Kept the slice docs/tests-only: no reactivation implementation, no reactivation
  persistence, no GUI reactivation behavior, no CLI reactivation, no automatic
  activation, no trust restoration, no file restoration/rewrite/deletion, no
  dependency install/uninstall, no solver uninstall, no plugin package import, no
  directory scan, no network fetch, no discovery execution, no validation
  execution, no solver execution, no issue/release/tag/asset mutation, no version
  bump, no validation-pass/fail claim, and no certification claim.

### Optional Solver Plugin Manifest Deactivation GUI

- Added a view-model driven PySide deactivation GUI surface for optional solver
  plugin manifests, preserving non-persistence, no-file-deletion, no-uninstall,
  no-discovery, no-validation, no-execution, and issue/release-safe boundaries.
- Rendered deactivation summary, candidates, acknowledgements, blockers,
  diagnostics, shared-stack/conflict warnings, evidence retention,
  trust/provenance badges, safety guidance, and disabled/future action states
  from the OSW-EXP-085 deactivation view-model, with widget-local non-persistent
  acknowledgement interaction via an injected pure callback.
- Kept the slice safe: no runtime deactivation behavior, no deactivation
  persistence, no file deletion, no dependency uninstall, no solver uninstall, no
  CLI behavior, no plugin package import, no directory scan, no network fetch, no
  discovery execution, no validation execution, no solver execution, no dependency
  install, no issue mutation, no release mutation, no validation-pass/fail claim,
  and no certification claim.

### Optional Solver Plugin Manifest Deactivation View-Model Extension

- Added a pure optional solver plugin manifest deactivation view-model extension
  for readiness, acknowledgements, diagnostics, evidence retention, shared-stack
  warnings, provenance, and disabled/future action states without persistence,
  deletion, uninstall, discovery, validation, solver execution, or issue/release
  mutation.
- Modeled the OSW-EXP-081 deactivation state machine and `OSPMG_DEACTIVATION_*`
  vocabulary over supplied activation candidate data (or caller-supplied
  deactivation candidates) plus acknowledgement state, with redacted source
  references and honesty flags that remain false.
- Kept the slice side-effect-free: no deactivation persistence, no GUI behavior,
  no CLI behavior, no file deletion, no dependency uninstall, no solver uninstall,
  no plugin package import, no directory scan, no network fetch, no discovery
  execution, no validation execution, no solver execution, no dependency install,
  no issue mutation, no release mutation, no validation-pass/fail claim, and no
  certification claim.

### Optional Solver Plugin Manifest Discovery Refresh GUI

- Added a view-model driven PySide discovery-refresh GUI surface for optional
  solver plugin manifests, preserving no-runtime-discovery, no-validation,
  no-install, no-execution, no-persistence, and issue/release-safe boundaries.
- Rendered refresh summary, refresh mode/state, discovery source
  inclusion/exclusion, deactivated candidates, acknowledgements, blockers,
  diagnostics, conflicts, unsafe claims, trust/provenance badges, safety
  guidance, and disabled/future action states from the OSW-EXP-083
  discovery-refresh view-model, with widget-local non-persistent acknowledgement
  interaction via an injected pure callback.
- Kept the slice safe: no runtime discovery integration, no passive discovery
  behavior change, no activation/deactivation persistence, no CLI behavior, no
  plugin package import, no directory scan, no network fetch, no discovery
  execution, no validation execution, no solver execution, no dependency install,
  no issue mutation, no release mutation, no validation-pass claim, and no
  certification claim.

### Optional Solver Plugin Manifest Discovery Refresh View-Model

- Added a pure, side-effect-free optional solver plugin manifest discovery-refresh
  view-model over supplied activation/deactivation candidate state or
  caller-supplied discovery source records plus acknowledgement and refresh
  lifecycle inputs.
- Modeled the OSW-EXP-082 refresh modes, refresh state machine, readiness rules,
  required acknowledgements, source/trust/provenance and built-in/conflict
  policies, unsafe-claim handling, and the `OSPMG_DISCOVERY_REFRESH_*` diagnostic
  vocabulary, with redacted source references and honesty flags that remain false.
- Kept the slice side-effect-free: no runtime discovery integration, no passive
  discovery behavior change, no activation/deactivation persistence, no GUI
  behavior, no CLI behavior, no PySide/Qt import, no plugin package import, no
  directory scan, no network fetch, no discovery execution, no validation
  execution, no solver execution, no dependency install, no issue/release/tag/
  asset mutation, no version bump, no validation-pass claim, and no certification
  claim.

### Optional Solver Plugin Manifest Discovery Refresh Integration Design

- Designed optional solver plugin manifest discovery-refresh integration
  semantics as a future explicit, provenance-preserving, non-validating,
  non-installing, non-executing, and issue/release-safe workflow.
- Defined the integration definition and non-meaning, refresh modes,
  preconditions, acknowledgements, source/trust/provenance labels, a built-in/
  conflict policy, a deactivated-candidate policy, an unsafe-claim policy, a
  refresh state machine, and design-only `OSPMG_DISCOVERY_REFRESH_*` diagnostic
  reservations.
- Kept the slice docs/tests-only: no discovery integration implementation, no
  passive discovery behavior change, no activation/deactivation persistence, no
  GUI/CLI behavior change, no plugin package import, no directory scan, no
  network fetch, no discovery execution, no validation execution, no solver
  execution, no dependency installation, no issue/release/tag/asset mutation, no
  version bump, no validation-pass claim, and no certification claim.

### Optional Solver Plugin Manifest Deactivation Design

- Designed optional solver plugin manifest deactivation semantics as a future
  explicit, acknowledged, provenance-preserving, non-deleting, non-uninstalling,
  non-validating, and non-executing workflow.
- Defined deactivation definition and non-meaning, preconditions,
  acknowledgements, source/trust/provenance labels, a deactivation state
  machine, a conflict/shared-stack policy, a validation/evidence-retention
  policy, and design-only `OSPMG_DEACTIVATION_*` diagnostic reservations.
- Kept the slice docs/tests-only: no deactivation implementation, no
  deactivation persistence, no GUI deactivation behavior, no CLI deactivation,
  no file deletion, no dependency uninstall, no solver uninstall, no plugin
  package import, no directory scan, no network fetch, no discovery execution,
  no validation execution, no solver execution, no issue mutation, no release
  mutation, no tag mutation, no asset mutation, no version bump, no
  validation-pass claim, and no certification claim.

### Optional Solver Plugin Manifest Activation GUI

- Added a view-model driven PySide activation GUI surface for optional solver
  plugin manifests, preserving non-persistence, no-discovery, no-validation,
  no-install, and no-execution boundaries.
- Rendered activation summary, candidates, acknowledgements, diagnostics,
  conflicts, trust/provenance badges, safety guidance, and disabled/future
  action states from the OSW-EXP-079 activation view-model, with widget-local
  non-persistent acknowledgement interaction via an injected pure callback.
- Kept the slice safe: no activation persistence, no CLI activation, no plugin
  package import, no directory scan, no network fetch, no discovery execution,
  no validation execution, no solver execution, no dependency install, no issue
  mutation, no release mutation, no validation-pass claim, and no certification
  claim.

### Optional Solver Plugin Manifest Activation View-Model

- Added a pure optional solver plugin manifest activation view-model for
  activation readiness, acknowledgements, diagnostics, conflicts, trust badges,
  and disabled/future action states without persistence, discovery, validation,
  installation, or solver execution.
- Modeled the OSW-EXP-078 state machine and `OSPMG_ACTIVATION_*` vocabulary over
  supplied preview/import data or caller-supplied candidates plus
  acknowledgement/lifecycle state, with redacted source references and honesty
  flags.
- Kept the slice side-effect-free: no activation persistence, no GUI behavior,
  no CLI activation, no PySide/Qt import, no plugin package import, no directory
  scan, no network fetch, no discovery execution, no validation execution, no
  solver execution, no dependency install, no issue mutation, no release
  mutation, no validation-pass claim, and no certification claim.

### Optional Solver Plugin Manifest Activation Design

- Designed optional solver plugin manifest activation semantics as a future
  explicit, acknowledged, non-validating, non-executing workflow.
- Defined activation definition and non-meaning, preconditions, acknowledgements,
  source/trust/provenance labels, built-ins-win conflict policy, unsafe-claim
  block policy, a future activation state machine, and design-only
  `OSPMG_ACTIVATION_*` diagnostic reservations.
- Kept the slice docs/tests-only: no activation implementation, no plugin
  package import, no directory scan, no network fetch, no discovery execution,
  no validation execution, no solver execution, no dependency install, no issue
  mutation, no release mutation, no tag mutation, no asset mutation, no version
  bump, no validation-pass claim, and no certification claim.

### Optional Solver Plugin Manifest Explicit Import GUI Implementation

- Added a preview-only PySide explicit plugin manifest JSON import panel over
  the existing loader/report and explicit-import view-model boundaries.
- Supported injected file chooser and loader seams, local `.json` path checks,
  cancel/no-op behavior, and rendering for selected sources, accepted/rejected/
  conflict rows, diagnostics, trust/source labels, safety guidance, and disabled
  unsafe actions.
- Kept the slice bounded: no plugin activation, no plugin package import, no
  directory scan, no network fetch, no discovery execution, no solver execution,
  no dependency install, no issue mutation, no release mutation, no
  validation-pass claim, no issue-closure claim, no bundled-solver claim, and no
  certification claim.

### Optional Solver Plugin Manifest Explicit Import GUI View-Model

- Added a pure explicit plugin manifest import GUI view-model for supplied
  loader reports while preserving no-file-loading, no-activation, and
  no-execution boundaries.
- Modeled summary counts, selected-source rows with redacted references,
  accepted/rejected/conflict rows, loader diagnostics, `OSPMG_IMPORT_*` import
  diagnostics, trust badges, guidance, and disabled/future action states, plus
  an in-memory redacted summary helper.
- Kept the slice side-effect-free: no GUI widget, no PySide/Qt import, no file
  dialog, no file loading, no JSON parsing from paths, no plugin activation, no
  plugin package import, no directory scan, no network fetch, no discovery
  execution, no solver execution, no dependency install, no issue mutation, no
  release mutation, no validation-pass claim, no issue-closure claim, no
  bundled-solver claim, and no certification claim.

### Optional Solver Plugin Manifest Explicit Import GUI Design

- Designed explicit plugin manifest JSON import/preview GUI behavior as a future
  gate while preserving display-only/no-activation/no-execution boundaries.
- Defined future entry points, a user-initiated JSON-only file chooser, file
  safety/failure states, design-only `OSPMG_IMPORT_*` diagnostic reservations,
  source/trust labels with user-selected files untrusted by default,
  built-ins-win conflict policy, and CLI/health/export relationships.
- Kept the slice docs/tests-only: no file dialog, no QFileDialog, no file
  loading, no JSON parsing from GUI source, no plugin activation, no plugin
  package import, no directory scan, no network fetch, no discovery execution,
  no solver execution, no dependency install, no issue mutation, no release
  mutation, no validation-pass claim, no issue-closure claim, no bundled-solver
  claim, and no certification claim.

### Optional Solver Plugin Manifest GUI Implementation

- Added a PySide optional solver plugin manifest preview panel under
  `src/osw/gui/dialogs/`.
- Rendered already-built plugin manifest GUI view-model records: summary
  counts, accepted/rejected/conflict rows, diagnostics, trust/source labels,
  safety guidance, and disabled/future action states.
- Kept the panel display-only: no file dialog, no file loading, no plugin
  activation, no plugin package loading, no directory scan, no network fetch,
  no discovery execution, no solver execution, no dependency install, no issue
  mutation, no release mutation, no validation-pass claim, no issue-closure
  claim, no bundled-solver claim, and no certification claim.

### Optional Solver Plugin Manifest GUI View-Model

- Added a pure optional solver plugin manifest GUI preview view-model under
  `src/osw/experimental/optional_solvers/`.
- Modeled summary counts, accepted/rejected/conflict rows, diagnostic rows,
  trust badges, guidance text, filters, and unavailable/future action states
  from already-built loader reports.
- Kept the slice side-effect-free: no GUI source, no CLI source, no file
  dialog, no file loading, no JSON parsing in the view-model, no plugin
  activation, no plugin package loading, no directory scan, no network fetch,
  no discovery execution, no solver execution, no dependency install, no issue
  mutation, no release mutation, no validation-pass claim, no issue-closure
  claim, no bundled-solver claim, and no certification claim.

### Optional Solver Plugin Manifest GUI Design

- Added a design-only optional solver plugin manifest GUI workflow contract.
- Defined future entry points, explicit-file preview flow,
  accepted/rejected/conflict panels, source/trust labels, diagnostics,
  safety/privacy messaging, health/export/refresh relationships, failure
  handling, and future view-model boundaries.
- Kept the slice docs/tests-only: no GUI source, no view-model source, no file
  dialog, no plugin activation, no plugin package loading, no directory scan,
  no network fetch, no solver execution, no dependency install, no issue
  mutation, no release mutation, no validation-pass claim, no issue-closure
  claim, no bundled-solver claim, and no certification claim.

### Optional Solver Plugin Manifest CLI Preview

- Added `optional-solver-plugin-manifest-preview` for explicit JSON plugin
  manifest loading previews.
- Added text/JSON output for accepted manifests, rejected manifests,
  conflicts, diagnostics, source types, and trust labels.
- Kept the command bounded to data-only explicit files: no plugin package
  loading, no directory scan, no network fetch, no solver execution, no
  dependency installation, no issue mutation, and no release mutation.

### Optional Solver Plugin Manifest Loader Model

- Added a data-only optional solver plugin manifest loader model for explicit
  dict and JSON manifest documents.
- Added source/trust labels, accepted/rejected records, duplicate-stack
  conflict diagnostics, and safety-policy diagnostics while keeping CLI/GUI
  behavior, plugin package discovery, directory scanning, network fetching,
  solver execution, dependency installation, issue mutation, and release
  mutation out of scope.

### Optional Solver Plugin Manifest Loading Design

- Added a design-only optional solver plugin manifest loading contract.
- Defined future manifest source categories, trust labels, loading boundaries,
  JSON-first format policy, candidate locations, conflict handling,
  validation diagnostics, CLI/GUI display implications, privacy/security
  rules, and validation relationship.
- Kept the slice docs/tests-only: no plugin loading implementation, no plugin
  code execution, no filesystem plugin scan, no network marketplace, no solver
  execution, no dependency install, no issue mutation, no release mutation, no
  validation-pass claim, no issue-closure claim, no bundled-solver claim, and
  no certification claim.

### Optional Solver GUI Discovery Refresh Implementation

- Wired `Refresh Passive Discovery` in the optional solver GUI health panel as
  an explicit user action.
- Added injected runner support, a default built-in passive discovery runner,
  refresh status/error text, deterministic test accessors, atomic accepted
  view-model replacement on success, failed/canceled/stale preservation, and
  export-after-refresh consistency.
- Kept the implementation passive and bounded: no automatic startup refresh,
  no background worker, no active smoke validation, no solver execution, no
  dependency install, no issue mutation, no release mutation, no
  validation-pass claim, no issue-closure claim, no bundled-solver claim, and
  no certification claim.

### Optional Solver GUI Discovery Refresh View-Model

- Added a pure optional solver GUI passive refresh state/apply layer under
  `src/osw/experimental/optional_solvers/`.
- Modeled refresh lifecycle states, request/result metadata, action states,
  stale-result handling, success/failure/cancel apply behavior, atomic health
  panel view-model replacement, selected-stack/filter preservation, and
  status/error text.
- Kept the layer side-effect-free: no GUI wiring, no background worker, no
  threading implementation, no discovery execution, no solver execution, no
  dependency install, no issue mutation, no release mutation, no
  validation-pass claim, no issue-closure claim, no bundled-solver claim, and
  no certification claim.

### Optional Solver GUI Discovery Refresh Design

- Added a design-only optional solver GUI passive discovery refresh workflow.
- Defined explicit user action, passive refresh boundaries, future injected
  runner and worker policy, atomic view-model replacement, status/error states,
  privacy/redaction behavior, export interaction, validation-gate separation,
  failure handling, and future implementation tests.
- Kept the slice docs/tests-only: no refresh implementation, no background
  worker implementation, no GUI/source mutation, no active validation, no
  solver execution, no dependency install, no issue mutation, no release
  mutation, no validation-pass claim, no issue-closure claim, no bundled-solver
  claim, and no certification claim.

### Optional Solver GUI Export Summary Implementation

- Added a GUI health-panel export action for redacted optional solver health
  summaries.
- Supported explicit `.json`, `.md`, and `.txt` exports through the existing
  pure payload/save-plan layer, with missing-parent rejection and overwrite
  confirmation.
- Kept the action side-effect-limited: exactly one selected file write on
  success, no clipboard integration, no shell/browser action, no output-folder
  opening, no discovery refresh, no solver execution, no dependency install,
  no issue mutation, no release mutation, no validation-pass claim, no
  issue-closure claim, no bundled-solver claim, and no certification claim.

### Optional Solver GUI Export Summary View-Model

- Added a pure optional solver GUI export summary payload/view-model layer
  under `src/osw/experimental/optional_solvers/`.
- Added redacted JSON, Markdown, and plain-text renderers plus save-plan
  analysis for explicit `.json`, `.md`, and `.txt` paths.
- Kept the layer side-effect-free: no GUI source, no CLI behavior change, no
  file dialog, no file write, no clipboard integration, no shell/browser
  action, no discovery execution, no solver execution, no dependency install,
  no issue mutation, no release mutation, no validation-pass claim, no
  issue-closure claim, no bundled-solver claim, and no certification claim.

### Optional Solver GUI Export Summary Design

- Added a design-only optional solver GUI export summary workflow contract.
- Defined future redacted export payload scope, JSON/Markdown/plain-text
  formats, privacy defaults, explicit save-path and overwrite policy, action
  states, payload-builder boundary, failure handling, and future tests.
- Kept the slice docs/tests-only: no export source, no file dialog, no
  clipboard integration, no shell/browser action, no discovery execution, no
  solver execution, no dependency install, no issue mutation, no release
  mutation, no validation-pass claim, no issue-closure claim, no bundled-solver
  claim, and no certification claim.

### Optional Solver GUI Health Panel Implementation

- Added a PySide display-only optional solver health panel under
  `src/osw/gui/dialogs/`.
- Rendered supplied view-model summary, stack cards, details, diagnostics,
  guidance, validation-history, safety, and action-state sections.
- Kept unsafe actions as disabled/display-only placeholders: no discovery
  execution, no solver execution, no external command execution, no subprocess
  usage, no dependency install, no solver install, no clipboard/browser action,
  no issue mutation, no release mutation, no validation-pass claim, no
  issue-closure claim, no bundled-solver claim, and no certification claim.

### Optional Solver GUI Health Panel View-Model

- Added a pure optional solver GUI health panel view-model under
  `src/osw/experimental/optional_solvers/`.
- Built deterministic summary, stack card, details, diagnostics, guidance,
  validation-history, and action-state records from supplied manifests and
  passive discovery reports.
- Preserved privacy and safety boundaries: no PySide/Qt imports, no GUI
  widgets, no CLI behavior change, no discovery execution, no active smoke
  validation, no external solver command execution, no solver execution, no
  dependency install, no issue mutation, no release mutation, no validation-pass
  claim, no issue-closure claim, no bundled-solver claim, and no certification
  claim.

### Optional Solver GUI Health Panel Design

- Added a design-only optional solver GUI health panel contract over the
  existing manifest, passive discovery, and CLI doctor preview concepts.
- Defined future entry points, panel layout, stack cards, details,
  diagnostics, guidance, validation history, redaction/privacy behavior, user
  actions, accessibility, plugin trust labels, and a pure view-model boundary.
- Kept the slice design-only: no GUI source, no view-model source, no CLI
  behavior change, no plugin loading, no active smoke validation, no external
  solver command execution, no solver execution, no dependency install, no
  issue mutation, no release mutation, no validation-pass claim, no
  issue-closure claim, no bundled-solver claim, and no certification claim.

### Optional Solver CLI Doctor Preview

- Added experimental `optional-solver-list`, `optional-solver-doctor`, and
  `optional-solver-explain` CLI preview commands.
- Exposed built-in optional solver manifests and passive discovery reports in
  text or JSON while redacting paths by default and keeping environment values
  out of output.
- Kept the CLI passive: no GUI behavior, no plugin loading, no active smoke
  validation, no external solver command execution, no solver execution, no
  dependency install, no issue mutation, no release mutation, no
  bundled-solver claim, and no certification claim.

### Optional Solver Discovery Service Implementation

- Added an experimental passive optional solver discovery service under
  `src/osw/experimental/optional_solvers/`.
- Added discovery result models, injected resolvers, default passive resolvers,
  redacted report serialization, health-state mapping, diagnostics, built-in
  manifest discovery, and explanation helpers.
- Kept discovery passive: no CLI/GUI implementation, no plugin loading, no
  active smoke validation, no external command execution, no optional solver
  imports, no solver execution, no dependency install, no issue mutation, no
  release mutation, no bundled-solver claim, and no certification claim.

### Optional Solver Discovery Service Design

- Added a design-only optional solver discovery service contract that consumes
  declarative `OptionalSolverManifest` records in future gates.
- Defined passive metadata inspection, future presence-check boundaries,
  active validation-gate separation, result concepts, diagnostics,
  health-state mapping, privacy/security rules, cache freshness, CLI/GUI
  handoff, and plugin-manifest trust boundaries.
- Preserved the boundary that discovery design does not implement source,
  call `shutil.which`, import optional solver packages, run external commands,
  execute solvers, install dependencies, mutate issues, edit releases, or claim
  validation success.

### Optional Solver Manifest Schema Model

- Added an experimental optional solver manifest schema/model package under
  `src/osw/experimental/optional_solvers/`.
- Added typed manifest, requirement, capability, probe, health-state,
  support-status, diagnostic, validation-report, JSON I/O, explanation, and
  built-in manifest APIs.
- Added built-in declarative manifests for Gmsh, GNU Octave, CalculiX,
  OpenFOAM, CoolProp/Cantera, and PyVista/meshio, mapped to issues `#6`
  through `#11`.
- Kept the schema declarative: no discovery implementation, no CLI/GUI
  implementation, no optional package imports, no health-check execution, no
  solver execution, no dependency install, no issue mutation, no release
  mutation, no bundled-solver claim, and no certification claim.

### Optional Solver Manifest UX Design

- Added a design-only optional solver manifest UX contract for Gmsh, GNU
  Octave, CalculiX, OpenFOAM, CoolProp/Cantera, and PyVista/meshio stacks.
- Defined future manifest fields, health states, CLI/GUI surfaces,
  plugin-provided manifest trust boundaries, validation relationships, and
  safety/privacy limits without implementing source behavior.
- Kept issues `#6` through `#11` open and preserved OSW-VALID-005
  `skipped-missing` evidence as neither pass nor failure.
- No manifest schema implementation, discovery implementation, CLI/GUI
  implementation, release edit, issue mutation, solver execution, dependency
  install, bundled-solver claim, or certification claim occurred.

### Next Experimental Line Selection

- Selected `Plugin ecosystem / optional solver manifest UX` as the next
  experimental line after the completed `v0.1.5-rc1` release flow, fresh
  post-public audit evidence, release-body cleanup, maintenance hardening, and
  OSW-VALID-005 optional validation discovery.
- Recorded that issues `#6` through `#11` remain open and were all classified
  as `skipped-missing` in OSW-VALID-005 because the target optional solver or
  science stacks were not installed on this machine.
- Routed the next design gate to
  `OSW-EXP-055_OPTIONAL_SOLVER_MANIFEST_UX_DESIGN`.
- No source implementation, release edit, issue mutation, solver execution,
  dependency install, version bump, bundled-solver claim, or certification
  claim occurred.

### Prepared-Machine Live Optional Validation Matrix

- Reran the live optional validation matrix for public `v0.1.5-rc1` and
  recorded installed-only discovery evidence for issues `#6` through `#11`.
- Classified Gmsh, GNU Octave, CalculiX `ccx`, OpenFOAM, CoolProp/Cantera, and
  PyVista/meshio as `skipped-missing` on this machine because the required
  executables or Python packages were not discovered.
- Wrote ignored local validation evidence under
  `artifacts/validation/live_optional/OSW-VALID-005/` and added the tracked
  summary document `docs/validation/live_optional_validation_matrix_v0_1_5rc1.md`.
- Kept issues `#6` through `#11` open. No dependency install, solver install,
  solver execution, release edit, asset mutation, tag push, issue closure,
  bundled-solver claim, or certification claim occurred.

### GUI Aggregate Timeout And Release Monitoring Hardening

- Added a deterministic GUI per-file fallback helper for environments where
  aggregate `pytest tests/gui -q` times out.
- Documented that aggregate GUI failures remain blocking, while aggregate GUI
  timeouts are warning-only only when every GUI test file passes or has expected
  skips under a complete per-file fallback.
- Added post-`v0.1.5-rc1` release monitoring notes covering public prerelease
  state, expected assets, retained public download smoke evidence, open live
  optional validation issues, unsigned portable ZIP status, no MSI/code signing,
  and no bundled external solvers.
- No release edit, asset mutation, issue mutation, solver execution, runtime
  source mutation, version bump, dependency install, bundled-solver claim, or
  certification claim occurred in this maintenance gate.

### Post-v0.1.5-rc1 Public Prerelease Follow-Up Planning

- Recorded that `v0.1.5-rc1` is now a public prerelease with the expected
  wheel, sdist, Windows portable ZIP, `SHA256SUMS.txt`, and
  `release_asset_manifest.json` assets present.
- Recorded that the post-public asset download audit passed for public
  `v0.1.5-rc1` assets, including checksum, manifest, wheel, sdist, and
  portable ZIP smoke evidence.
- Selected the next path as a narrow public release body note update to replace
  stale "post-public audit pending" wording only. This planning gate does not
  edit the release body.
- Kept issues `#6` through `#11` open for prepared-machine live optional
  validation. Issue `#8` remains `skipped-missing` because `ccx` was absent in
  the installed-only local audit.
- No release edit, issue mutation, solver execution, version bump, dependency
  install, branch/tag mutation, asset mutation, runtime source mutation,
  bundled-solver claim, or certification claim occurred in this planning gate.

### Post-v0.1.5-rc1 Worktrack Selection

- Recorded that OSW-RELEASE-041 corrected stale post-public-audit wording in
  the public `v0.1.5-rc1` release body while preserving title, prerelease
  state, tags, assets, issues, and source state.
- Selected the next worktrack as maintenance hardening for GUI aggregate
  timeout behavior and release-monitoring notes. This planning gate does not
  perform that maintenance work.
- Kept prepared-machine validation as a later track because issues `#6`
  through `#11` remain open and issue `#8` remains `skipped-missing` because
  `ccx` was absent.
- No release edit, asset mutation, issue mutation, solver execution, version
  bump, dependency install, branch/tag mutation, runtime source mutation,
  bundled-solver claim, or certification claim occurred in this planning gate.

### v0.1.5rc1 Candidate Metadata Aligned

Candidate package version: `0.1.5rc1`

- Aligned package, import, CLI, installed editable metadata, release metadata
  QA, and candidate documentation for the future `v0.1.5-rc1` prerelease
  boundary selected by OSW-PLAN-008.
- Added a `v0.1.5-rc1` candidate note documenting that metadata is aligned
  while the tag, GitHub Release, and assets are not created yet.
- Preserved the current public `v0.1.4-rc1` prerelease state and kept issues
  `#6` through `#11`, including skipped-missing issue `#8`, open for
  environment-dependent live optional validation.
- No `v0.1.5-rc1` tag, release edit/create/publish, asset build/upload, issue
  mutation, dependency install, solver execution, bundled solver claim, or
  certification claim occurred in this metadata gate.

### v0.1.4-rc1 Public Prerelease And Live Optional Validation

- Published `v0.1.4-rc1` as a public prerelease with wheel, sdist, Windows
  portable ZIP, `SHA256SUMS.txt`, and `release_asset_manifest.json` assets.
- Recorded an installed-only live optional validation matrix for issues `#6`
  through `#11`. On this machine, Gmsh, GNU Octave, CalculiX `ccx`, OpenFOAM,
  CoolProp/Cantera, and PyVista/meshio were missing, so each target was
  classified as `skipped-missing` and remains open for a prepared validation
  environment.
- Recorded an OSW-VALID-004 installed-only CalculiX issue `#8` rerun for
  `v0.1.4-rc1`. `ccx` was not discovered on this machine, so the result is
  `skipped-missing`; no solver execution, dependency install, solver install,
  release mutation, asset upload, issue closure, bundled solver claim, or
  certification claim occurred.
- Added a post-experimental ResultDataset scope review after the FEASpec/
  CalculiX parser/import/write/GUI line. The review records completed
  review-file persistence scope, keeps issues `#6` through `#11` open after
  skipped-missing CalculiX validation, notes that `develop` is newer than the
  public release tag, and requires a future release-boundary decision before
  any new version metadata, tag, release, or asset work.
- Added a post-experimental release-boundary decision selecting `v0.1.5-rc1`
  as the next prerelease boundary for the substantial FEASpec/CalculiX
  ResultDataset capability line. This decision does not bump version metadata,
  create tags, edit releases, build/upload assets, execute solvers, close
  issues, or claim live optional validation completion.
- Added a prepared-machine plan for issues `#6` through `#11`, defining
  required packages/executables, future installed-only validation commands,
  pass/partial/keep-open criteria, and separate closure-gate requirements.
- Added a design-only FEASpec IR contract for future VFEA work, defining
  `FEASpecCandidate` versus approved FEASpec, explicit units, GeometryGraph,
  materials/sections, boundary conditions, loads, dimensions, assumptions,
  evidence/confidence, diagnostics, validation states, serialization examples,
  and CalculiX-first compatibility without implementing FEASpec/VFEA, VLM APIs,
  solver execution, mandatory Abaqus, topology optimization, or certification
  claims.
- Added canonical FEASpec JSON examples and six synthetic benchmark seed
  folders for future FEASpec model and validator work. The fixtures cover
  candidate, approved, and invalid diagnostic cases with placeholder source
  metadata and planned metrics only; no generated images, solver outputs, VLM
  runs, mandatory Abaqus, or certification claims are included.
- Added an experimental FEASpec Python model layer under
  `src/osw/experimental/feaspec/` that loads, basic-checks, and serializes the
  examples and benchmark seeds. The layer is structural only and does not add a
  production/full physics validator, full ProjectSchema persistence,
  ProjectSchema mutation, solver adapter/exporter, VLM API, credential
  handling, automatic solver execution, mandatory Abaqus, topology
  optimization, or certification claim.
- Added a design-only FEASpec validator contract covering pipeline phases,
  diagnostic schema, severity taxonomy, required diagnostic codes, approval
  rules, solver handoff gates, CalculiX-first compatibility, Abaqus
  optional/non-default handling, and benchmark readiness. The contract does not
  implement the production validator, full ProjectSchema persistence,
  ProjectSchema mutation, solver adapter/exporter, VLM API, credentials, or
  solver execution.
- Added an experimental FEASpec semantic validator report layer under
  `src/osw/experimental/feaspec/`, with structured severities, diagnostic
  categories, stable diagnostic codes, phase results, approval and solver
  handoff blockers, CalculiX-first field-level compatibility, Abaqus
  optional/non-default diagnostics, and benchmark readiness checks for existing
  examples and seed fixtures. It does not implement full physics validation,
  full ProjectSchema persistence, ProjectSchema mutation, solver
  adapters/exporters, VLM APIs, credentials, or solver execution.
- Added a design-only FEASpec to ProjectSchema bridge contract that requires an
  approved FEASpec and validator report with no blockers, maps reviewed fields
  to current ProjectSchema concepts where safe, preserves explicit units,
  provenance/evidence, confidence, diagnostics, and unmapped fields, and records
  ProjectSchema extension needs. It does not mutate ProjectSchema, generate
  solver exports, call VLM APIs, handle credentials, or execute solvers.
- Added an experimental FEASpec to ProjectSchema bridge plan layer under
  `src/osw/experimental/feaspec/`, with `plan_project_from_feaspec`,
  `explain_bridge_plan`, `FEASpecProjectBridgePlan`, bridge diagnostics,
  extension needs, unmapped fields, provenance preservation, and
  ProjectSchema-compatible draft dictionaries for approved examples. It blocks
  candidates and invalid fixtures and does not persist ProjectSchema files,
  mutate ProjectSchema, call SolverAdapter/exporter code, generate solver
  decks, call VLM APIs, handle credentials, or execute solvers.
- Added a design-only FEASpec to CalculiX case-planning contract that defines
  approved-FEASpec, validator, and bridge preconditions; a future case-plan
  object shape; mesh requirements; node/element/material/section/BC/load/step
  and output planning; `FC_*` diagnostics; and issue `#8` separation. It does
  not add a case generator, `.inp` writer, SolverAdapter/exporter call, live
  `ccx` validation, or solver execution.
- Added an experimental FEASpec to CalculiX case-plan model under
  `src/osw/experimental/feaspec/`, with `plan_calculix_case_from_feaspec`,
  `plan_calculix_case_from_bridge`, `explain_calculix_case_plan`,
  `FEASpecCalculiXCasePlan`, node/element/material/section/BC/load/step/output
  planning records, and `FC_*` diagnostics. It preserves approved bridge
  evidence, blocks candidates and validator/bridge blockers, marks examples
  without explicit mesh topology as `FC_MESH_REQUIRED`, keeps
  `ready_for_solver_execution` false, and does not write `.inp` files, call
  solver adapters/exporters, run `ccx`, mutate ProjectSchema, add VLM APIs, or
  execute solvers.
- Added a design-only FEASpec to CalculiX `.inp` writer contract that defines
  future writer preconditions, proposed render/write APIs, result objects,
  deterministic file-section ordering, provenance comments, `FW_*` diagnostics,
  golden fixture strategy, issue `#8` separation, and the no-run safety
  boundary. It does not implement a writer, generate `.inp` files, call
  SolverAdapter or runner code, mutate ProjectSchema, run CalculiX, add VLM
  APIs, or execute solvers.
- Added an experimental no-run FEASpec CalculiX `.inp` renderer under
  `src/osw/experimental/feaspec/`, with public render/write/explain APIs,
  `FW_*` diagnostics, deterministic section ordering, provenance and
  no-certification comments, and overwrite-guarded caller-path writes. Approved
  examples still block until explicit mesh topology exists, test file writes
  stay under pytest `tmp_path`, and the renderer does not run `ccx`, call
  SolverAdapter or runner code, mutate ProjectSchema, validate issue `#8`, add
  VLM APIs, or add tracked `.inp` fixtures.
- Added controlled no-run FEASpec CalculiX `.inp` golden text fixtures under
  `tests/fixtures/feaspec/calculix_golden/`, with README/manifest metadata,
  SHA-256 checks, normalized renderer comparisons for synthetic cantilever and
  truss cases, and QA allowlist coverage for arbitrary `.inp` rejection. These
  fixtures are not solver outputs, do not run `ccx`, do not validate issue
  `#8`, and do not claim engineering correctness or certification.
- Added an experimental no-run FEASpec CalculiX export bundle layer under
  `src/osw/experimental/feaspec/`, with `export_calculix_case`,
  `export_calculix_case_from_feaspec`, `export_calculix_case_from_bridge`, and
  `explain_calculix_export_result`. It writes only caller-directory `.inp`,
  manifest JSON, diagnostics JSON, and `README_RUN_FIRST.txt` bundles after
  renderer success, includes checksums and no-run metadata, blocks unsafe
  basenames and overwrite risks, keeps `ready_for_solver_execution` false, and
  does not run `ccx`, call SolverAdapter or runner code, mutate ProjectSchema,
  validate issue `#8`, add VLM APIs, or stage runtime export bundles.
- Added `feaspec-calculix-export-preview`, an experimental no-run CLI command
  that reads FEASpec JSON and reports validation, bridge, case-plan, render,
  planned-file, and diagnostic status in text or JSON. It supports strict
  blocked-preview exit code `2`, writes no files, creates no output
  directories, runs no `ccx`, calls no SolverAdapter or runner code, mutates no
  ProjectSchema, validates no issue `#8`, and stages no runtime export bundles.
- Added `feaspec-calculix-export-write`, an experimental no-run CLI command
  that requires an explicit output directory and writes local export bundles
  only through the no-run exporter API. It blocks missing mesh/topology examples,
  supports text and JSON output plus explicit `--create-dir`/`--overwrite`,
  writes only `.inp`, manifest JSON, diagnostics JSON, and README files on
  success, runs no `ccx`, calls no SolverAdapter or runner code, mutates no
  ProjectSchema, validates no issue `#8`, and stages no runtime export bundles.
- Added a design-only FEASpec CalculiX result import / run gate document for
  post-export sequencing. It keeps FEASpec human review, no-run export
  preview/write, installed-only run, result import, and ResultDataset/report
  summary as separate future gates; defines `FR_*` and `FI_*` diagnostics; and
  does not implement result import, run commands, SolverAdapter/runner or
  subprocess paths, ProjectSchema mutation, solver execution, live issue `#8`
  validation, or release mutation.
- Added an experimental FEASpec human review record model under
  `src/osw/experimental/feaspec/`, with JSON-serializable reviewer state,
  action, accepted warnings, diagnostic decisions, validator summary/hash,
  bridge/case/export summaries, acknowledgements, and solver-execution flags.
  It records `solver_execution_performed=false` and does not implement a GUI,
  CLI approval command, result import, run gate, SolverAdapter/runner path,
  ProjectSchema mutation, VLM API, credential handling, issue `#8`
  validation, or solver execution.
- Added `feaspec-human-review-create`, `feaspec-human-review-validate`, and
  `feaspec-human-review-summary` as experimental record-only CLI commands for
  FEASpec human-review JSON. They validate before writing, refuse implicit
  parent-directory creation, guard overwrite behavior, support text and JSON
  output, keep `solver_execution_performed=false`, and do not implement GUI,
  result import, run gate, SolverAdapter/runner/subprocess paths,
  ProjectSchema mutation, live issue `#8` validation, VLM APIs, dependency
  install, or solver execution.
- Added a design-only FEASpec human review GUI dialog contract that maps the
  human-review record model and CLI approval workflow into future dialog entry
  points, panels, warning acceptance, approval gating, record preview, save
  behavior, CLI/GUI consistency, and view-model planning. It does not implement
  GUI source, result import, run-gate behavior, SolverAdapter/runner/subprocess
  paths, ProjectSchema mutation, live issue `#8` validation, VLM APIs,
  dependency installation, or solver execution.
- Added an experimental pure Python FEASpec human review dialog view-model
  layer under `src/osw/experimental/feaspec/`. It computes dialog panels,
  diagnostic rows, warning acceptance rows, action availability and disabled
  reasons, record previews, and save-path plans for a future GUI while avoiding
  PySide/Qt imports, GUI source mutation, result import, run-gate behavior,
  SolverAdapter/runner/subprocess paths, exporter/renderer side effects,
  ProjectSchema mutation, live issue `#8` validation, VLM APIs, dependency
  installation, and solver execution.
- Added a read-only FEASpec human review GUI dialog under `src/osw/gui/dialogs/`
  that binds to the existing view-model. It renders source evidence,
  diagnostics, warning rows, disabled action reasons, safety copy, and record
  preview only. It adds no record save integration, file dialog, result import
  implementation, installed-only run gate implementation, SolverAdapter/runner
  or subprocess path, ProjectSchema mutation, live issue `#8` validation, VLM
  API, dependency installation or upgrade, release mutation, or solver
  execution.
- Added explicit FEASpec human review GUI save integration for caller-provided
  JSON paths. The dialog validates the in-memory review record before writing,
  refuses unacknowledged overwrites, creates no parent directories, and writes
  exactly one human-review JSON record. It adds no file dialog, export bundle
  write, `.inp` write, result import implementation, installed-only run gate,
  SolverAdapter/runner/subprocess path, ProjectSchema mutation, live issue `#8`
  validation, VLM API, dependency installation or upgrade, release mutation, or
  solver execution.
- Added a design-only FEASpec human review GUI file-dialog contract for future
  review-record JSON path selection. The design covers entry points, default
  filename sanitization, JSON filters, directory policy, overwrite
  confirmation, path safety, save-plan integration, error handling, and future
  implementation tests without adding `QFileDialog` usage, GUI source mutation,
  export bundle writes, result import, run gates, SolverAdapter/runner paths,
  ProjectSchema mutation, live issue `#8` validation, VLM APIs, dependency
  changes, release mutation, or solver execution.
- Added FEASpec human review GUI file-dialog implementation for review-record
  JSON save-path selection only. The chooser is mockable in tests, uses a
  deterministic sanitized default filename and narrow JSON filter, treats
  cancel as no-op, requires overwrite confirmation, creates no parent
  directories, writes nothing until the existing save integration is triggered,
  and adds no export bundle write, `.inp` write, result import, run gate,
  SolverAdapter/runner/subprocess path, ProjectSchema mutation, live issue
  `#8` validation, VLM API, dependency installation or upgrade, release
  mutation, or solver execution.
- Added `feaspec-calculix-run-installed-only`, an experimental installed-only
  FEASpec CalculiX run gate for existing no-run export bundles. It defaults to
  dry-run, requires explicit `--execute`, `--confirm-run`, and
  `--acknowledge-readme` before invoking an already installed `ccx`, writes
  isolated runtime logs and `run_metadata.json`, and has fake-`ccx` tests for
  success, nonzero exit, timeout, missing executable, invalid bundle, and CLI
  behavior. It does not install solvers or dependencies, import results, call
  SolverAdapter or runner code, mutate ProjectSchema, validate or close issue
  `#8`, edit releases/assets/tags, add VLM APIs, bundle external solvers, or
  claim industrial certification.
- Added an experimental FEASpec CalculiX result import model under
  `src/osw/experimental/feaspec/`. It inspects explicit result directories,
  classifies run metadata, export manifests, diagnostics, stdout/stderr, and
  `.dat`/`.frd`/`.sta`/`.cvg` artifacts, preserves provenance, reports `FI_*`
  diagnostics, and builds an in-memory ResultDataset draft with artifact and
  field references. It does not parse numerical result content, write
  ResultDataset files, perform persistence itself, execute CalculiX, call
  SolverAdapter or runner code, mutate ProjectSchema, validate or close issue
  `#8`, add VLM APIs, bundle external solvers, or claim industrial
  certification.
- Added `feaspec-calculix-result-import-preview`, an experimental preview-only
  CLI command for the FEASpec CalculiX result import model. It requires an
  explicit result directory, classifies existing artifacts, reports text or JSON
  diagnostics, exposes an in-memory ResultDataset draft with `writes_files=false`,
  and supports strict exit code `2` for blocked, unsupported, or future-parser
  cases. It does not parse numerical `.dat`/`.frd` content, write ResultDataset
  files, execute CalculiX, call SolverAdapter or runner code, mutate
  ProjectSchema, validate or close issue `#8`, add VLM APIs, bundle external
  solvers, or claim industrial certification.
- Added an experimental FEASpec CalculiX `.sta` / `.cvg` status scanner under
  `src/osw/experimental/feaspec/`. It classifies text-only progress,
  convergence-message, warning, error, completion, failure, informational, and
  unknown lines with bounded snippets and counts, enriches result-import
  previews with status summaries, and preserves metadata scanner hashes and
  limits. It does not parse numeric convergence values, parse `.dat`/`.frd`
  numerical content, write ResultDataset files, execute CalculiX, call
  SolverAdapter or runner code, mutate ProjectSchema, validate or close issue
  `#8`, add VLM APIs, bundle external solvers, or claim industrial
  certification.
- Added a design-only FEASpec CalculiX `.dat` minimal parser contract. It
  defines the future accepted header/scalar/table preview subset, rejected
  unknown or unitless content, safety limits, unit-handling rules, `FP_DAT_*`
  diagnostics, output model, ResultDataset preview mapping, and fixture
  strategy without adding `.dat` parser implementation, numerical extraction,
  ResultDataset writes, solver execution, SolverAdapter/runner paths,
  ProjectSchema mutation, issue `#8` validation, bundled solvers, or
  certification claims.
- Added an experimental FEASpec CalculiX `.dat` metadata section scanner under
  `src/osw/experimental/feaspec/`. It classifies direct `.dat` heading text,
  section spans, section kinds, unsupported/unknown sections, bounded snippets,
  and section counts, then enriches result-import previews with
  `dat_section_summary` metadata. It does not extract numeric values, extract
  table rows or columns, infer units, write ResultDataset files, execute
  CalculiX, call SolverAdapter or runner code, mutate ProjectSchema, validate
  or close issue `#8`, add VLM APIs, bundle external solvers, or claim
  industrial certification.
- Added an experimental FEASpec CalculiX `.dat` minimal parser under
  `src/osw/experimental/feaspec/`. It consumes section-scanner output and
  parses only explicit scalar candidates plus small delimited table candidates
  with explicit units or caller `unit_context`, preserving raw text, line
  provenance, diagnostics, and limitations. It enriches result-import previews
  in memory only and does not implement free-form `.dat` parsing, `.frd`
  parsing, unit inference, mesh/field reconstruction, ResultDataset writes,
  solver execution, SolverAdapter/runner calls, ProjectSchema mutation, issue
  `#8` validation, VLM APIs, bundled solvers, or certification claims.
- Added an experimental FEASpec CalculiX `.frd` block metadata scanner under
  `src/osw/experimental/feaspec/`. It classifies block labels, spans, block
  kinds, unsupported/unknown records, snippets, and deferred reference
  candidates; enriches result-import model and CLI preview summaries in memory;
  and preserves the design baseline. It does not parse numerical field values,
  reconstruct mesh, build visualization arrays, infer units, write
  ResultDataset files, execute solvers, call SolverAdapter/runner code, mutate
  ProjectSchema, validate issue `#8`, add VLM APIs, bundle solvers, or claim
  certification.
- Added an experimental FEASpec CalculiX ResultDataset draft mapping layer
  under `src/osw/experimental/feaspec/`. It maps result import artifacts,
  `.sta`/`.cvg` status summaries, bounded `.dat` scalar/table candidates,
  deferred `.frd` references, provenance, diagnostics, and limitations into a
  stable in-memory draft and exposes CLI preview counts. It does not persist or
  write ResultDataset files, parse additional `.frd` numerical field values,
  reconstruct meshes, infer units, execute solvers, call SolverAdapter/runner
  code, mutate ProjectSchema, validate issue `#8`, add VLM APIs, bundle
  solvers, or claim certification.
- Added a design-only FEASpec CalculiX ResultDataset write-flow contract. It
  defines the future output layout, schema/versioning, explicit path and
  overwrite policy, atomic-write strategy, artifact references,
  validation-before-write rules, CLI/GUI future design, and `FDW_*`
  diagnostics while adding no persistence implementation, file writes, `.frd`
  numerical parsing, mesh reconstruction, solver execution, SolverAdapter or
  runner integration, ProjectSchema mutation, issue `#8` validation, bundled
  solvers, or certification claims.
- Added an experimental FEASpec CalculiX ResultDataset write plan model under
  `src/osw/experimental/feaspec/`. It validates reviewed output-directory
  intent, path safety, planned standard files, future atomic write paths,
  artifact references, draft diagnostics, provenance, and limitations
  acknowledgement in memory only. It writes no files, creates no directories,
  copies no artifacts, performs no ResultDataset persistence, contains no
  CLI/GUI behavior, executes no solver, calls no SolverAdapter or runner code,
  mutates no ProjectSchema, validates no issue `#8`, adds no VLM APIs, bundles
  no solvers, and claims no certification.
- Added an experimental FEASpec CalculiX ResultDataset schema payload model
  under `src/osw/experimental/feaspec/`. It assembles deterministic in-memory
  ResultDataset, manifest, diagnostics, provenance, and review README payload
  records from the reviewed draft mapping and write plan. It writes no files,
  creates no directories, copies no artifacts, performs no ResultDataset
  persistence, contains no CLI/GUI behavior, executes no solver, calls no
  SolverAdapter or runner code, mutates no ProjectSchema, validates no issue
  `#8`, adds no VLM APIs, bundles no solvers, and claims no certification.
- Added an experimental FEASpec CalculiX ResultDataset library writer under
  `src/osw/experimental/feaspec/`. It consumes a validated write plan and schema
  payload, writes exactly `result_dataset.json`, `result_dataset_manifest.json`,
  `diagnostics.json`, `provenance.json`, and `README_REVIEW_FIRST.txt` with
  atomic temp/replace behavior, and returns size/SHA-256 metadata. It contains
  no CLI/GUI behavior, copies no original solver artifacts, parses no
  additional numerical results, executes no solver, calls no SolverAdapter or
  runner code, mutates no ProjectSchema, validates no issue `#8`, adds no VLM
  APIs, bundles no solvers, and claims no certification.
- Added a historical design contract for the FEASpec CalculiX result import
  write CLI. It defined plan-only default behavior, explicit write mode,
  required result/output directories, limitations/review acknowledgements, exit
  codes, text/JSON output, path policy, and safety boundaries before the
  implementation gate.
- Added `feaspec-calculix-result-import-write`, an experimental review-gated
  CLI command for CalculiX ResultDataset persistence. It defaults to plan-only,
  requires explicit `--write`, `--output-dir`, `--acknowledge-limitations`, and
  `--acknowledge-review-required` before writing, delegates file persistence to
  the library writer, writes only the five standard ResultDataset review files,
  copies no original solver artifacts, executes no solver, calls no
  SolverAdapter or runner code, mutates no ProjectSchema, validates no issue
  `#8`, edits no releases, and claims no certification.
- Added a design-only FEASpec CalculiX result import write GUI contract. It
  defines future preview entry points, ResultDataset write dialog flow,
  panels/tabs, action states, disabled reasons, file-dialog policy,
  acknowledgements, CLI/GUI consistency, and no-run safety boundaries while
  implementing no GUI source, file dialog, CLI behavior change, ResultDataset
  write, solver execution, SolverAdapter/runner path, ProjectSchema mutation,
  or issue `#8` validation.
- Added an experimental FEASpec CalculiX result write view-model under
  `src/osw/experimental/feaspec/`. It computes UI-agnostic panels, rows, action
  states, disabled reasons, acknowledgements, preview records, and lexical
  save-path plans for the future ResultDataset write GUI while adding no
  PySide/Qt import, GUI dialog, file dialog, writer invocation, ResultDataset
  write, solver execution, SolverAdapter/runner path, ProjectSchema mutation,
  VLM API, release mutation, or issue `#8` validation.
- Added the initial experimental FEASpec CalculiX result write dialog under
  `src/osw/gui/dialogs/`. It rendered the write view-model as a display-only
  PySide6 dialog with source, artifact, diagnostics, draft mapping, write plan,
  schema/manifest, safety, actions, and result panels. That initial slice
  added no QFileDialog, writer invocation, ResultDataset file write, CLI
  behavior change, solver execution, SolverAdapter/runner path, ProjectSchema
  mutation, VLM API, release mutation, or issue `#8` validation.
- Added a design/planning-only FEASpec CalculiX result write GUI file-dialog
  contract. It defines future output-directory selection, default-directory
  policy, cancel no-op behavior, path validation, create-dir and overwrite
  acknowledgements, CLI/GUI consistency, and mocked implementation tests while
  adding no QFileDialog implementation, GUI source change, writer invocation,
  ResultDataset file write, solver execution, SolverAdapter/runner path,
  ProjectSchema mutation, VLM API, release mutation, or issue `#8` validation.
- Added experimental FEASpec CalculiX result write GUI output-directory
  selection under `src/osw/gui/dialogs/`. It uses directory-only
  `QFileDialog.getExistingDirectory` behavior with injectable test selection,
  cancel no-op behavior, selected-directory display, and refreshed save-plan
  analysis while adding no writer invocation, ResultDataset file write,
  directory creation during selection, artifact copying, CLI behavior change,
  solver execution, SolverAdapter/runner path, ProjectSchema mutation, VLM
  API, release mutation, or issue `#8` validation.
- Added a design-only FEASpec CalculiX result write GUI writer-integration
  contract. It defines future write-action enablement, final confirmation,
  acknowledgement gating, single library-writer call boundary, failure
  handling, post-write display, retry behavior, state refresh, and mocked test
  expectations while adding no GUI writer invocation, GUI file writes, GUI or
  view-model source mutation, CLI behavior change, library writer behavior
  change, solver execution, SolverAdapter/runner path, ProjectSchema mutation,
  VLM API, release mutation, or issue `#8` validation.
- Added experimental FEASpec CalculiX result write GUI writer integration under
  `src/osw/gui/dialogs/`. The write action now enables only when reviewed gates
  and acknowledgements pass, requires explicit confirmation, and delegates
  actual ResultDataset persistence to the existing library writer. It writes
  only standard ResultDataset review files under the selected output directory,
  copies no original solver artifacts, opens no output folder shell command,
  changes no CLI/library writer behavior, executes no solver, calls no
  SolverAdapter/runner/subprocess path, mutates no ProjectSchema, edits no
  release/tag/assets/issues, and does not validate or close issue `#8`.
- Polished the FEASpec CalculiX result write GUI post-write display. The dialog
  now shows clearer status, written-file table rows with payload kind, size, and
  SHA-256 hash, grouped diagnostics, grouped limitations, failure details,
  retry guidance, and a deterministic copy-ready text summary as display text
  only. It adds no OS clipboard integration, open-output shell command, artifact
  copying, CLI/library writer behavior change, solver execution, ProjectSchema
  mutation, release/tag/asset/issue mutation, or issue `#8` validation.
- Added a closure review for the FEASpec CalculiX result write GUI scope. The
  review records the experimental GUI write flow as complete for standard
  ResultDataset review-file persistence after CLI, writer, schema, plan,
  view-model, dialog, output-directory chooser, writer integration, and
  post-write polish gates. It is docs/tests only and adds no runtime behavior,
  source writer change, solver execution, live `ccx` validation, issue `#8`
  closure, bundled solver claim, or certification claim.
- Preserved the release boundaries: no dependency install, solver install,
  release mutation, asset upload, issue closure, bundled external solver,
  stable-production claim, industrial certification claim, or VFEA
  implementation claim.

### v0.1.4rc1 Candidate Metadata Aligned

Candidate package version: `0.1.4rc1`

- Aligned package, CLI, and release metadata for the `v0.1.4-rc1` prerelease
  candidate after the release-boundary decision selected the v0.1.4 line. No
  `v0.1.4-rc1` tag, release assets, or GitHub Release were created by this
  metadata gate.

### v0.1.3rc2 Maintenance Development Cycle Opened

Previous development package version: `0.1.3rc2.dev0`

- Added reusable release asset download smoke automation for Issue `#2`,
  covering `SHA256SUMS.txt`, `release_asset_manifest.json`, safe archive
  checks, and optional full wheel/sdist/portable ZIP smoke.
- Improved Windows portable ZIP user guidance for Issue `#4`, including
  unsigned/no MSI/no code-signing warnings, no bundled external solver wording,
  checksum verification, and future `README_RUN_FIRST.txt` template guidance.
- Added a read-only `Release asset smoke` GitHub Actions workflow for Issue
  `#2`: pull requests and `develop` pushes use offline release asset fixtures,
  while live GitHub release downloads are manual `workflow_dispatch` only.
- Made the offline release asset fixture byte-stable across CI checkouts so
  `release_asset_manifest.json` checksum verification is not changed by Git
  line-ending normalization.
- Documented the OSW-MAINT-002 duplicate-file quarantine review for Issue `#1`,
  retaining 19 divergent archived files under ignored artifacts with no restore,
  no permanent deletion, and no high-risk secrets found.
- Added v0.1.3rc2 maintenance issue closure triage for Issues `#1`, `#2`,
  `#4`, and `#5`, recording evidence-based completion decisions without
  release, asset, or tag mutation.
- Finalized the reusable post-public release checklist for Issue `#3`, covering
  the `v0.1.3-rc1` flow from metadata/tag gates through draft, asset upload,
  publish, post-public audit, docs polish, CI/manual smoke, and issue closure
  triage without stable-production, MSI, signing, or bundled-solver claims.
- Added remaining-open-issue triage for the v0.1.3rc2 cycle, recommending
  Issue `#13` onboarding examples/tutorials as the next practical public
  usability slice, Issue `#16` as a release-trust fallback, and live optional
  validation only on machines with the relevant tools installed.
- Improved onboarding examples and tutorials for Issue `#13`, adding a tutorial
  index, first CLI walkthrough, first GUI walkthrough, result dataset
  walkthrough, release asset smoke walkthrough, categorized examples, and
  optional dependency diagnostics for the `0.1.3rc2.dev0` maintenance line.
- Recorded onboarding closure evidence for Issue `#13`, including first-run CLI
  smoke results, public docs QA coverage, and preserved prerelease/no
  bundled-solver limitations.
- Documented the code signing and installer strategy for Issue `#16`, covering
  current unsigned portable ZIP status, checksum/manifest limits, GitHub
  artifact attestation distinction, Authenticode signing options, MSI/MSIX/Store
  tradeoffs, and no-secret signing rules.
- Added remaining-open-issue triage after release-trust closure, recommending
  Issue `#12` v0.1.4 planning as the next gate, Issue `#15` Plugin Manager UX as
  the fallback implementation slice, and live optional validation / full-smoke
  workflow dispatch as deferred unless suitable environments or maintainer
  request are available.
- Added v0.1.4 feature selection planning for Issue `#12`, recommending a
  workflow/product-polish feature line with Issue `#15` Plugin Manager
  UX/install receipts as the first implementation candidate, Issue `#14`
  ResultViewer/FieldViewer workflow as the second candidate, Issue `#17` VFEA
  scope as planning-only, and Issues `#6`-`#11` live validation deferred until
  suitable environments are available.
- Locked v0.1.4 scope to Issue `#15` Plugin Manager UX/install receipts as the
  first implementation slice, keeping remote plugin store, dependency
  auto-install, plugin signing, marketplace behavior, plugin code execution
  during install, and GUI solver execution out of scope.
- Improved Plugin Manager UX for Issue `#15`, adding clearer managed install
  receipt summaries, quarantine/rejection records, diagnostics/safety
  messaging, managed-root uninstall eligibility, and CLI wording consistency
  without adding remote store, dependency auto-install, plugin signing,
  marketplace behavior, or plugin code execution during install.
- Recorded Plugin Manager UX closure evidence for Issue `#15`, preserving the
  local-only install, manifest-only validation, managed-root uninstall, no
  remote store, no dependency auto-install, no signing, and no marketplace
  boundaries.
- Recorded v0.1.4 planning closure evidence for Issue `#12` after feature
  selection, scope lock, Issue `#15` implementation, and Issue `#15` closure
  evidence landed on `develop`; Issue `#14` remains the next feature candidate,
  Issue `#17` remains experimental/deferred, and Issues `#6`-`#11` remain
  environment-dependent live validation.
- Improved ResultViewer / FieldViewer workflow for Issue `#14`, adding clearer
  catalog summaries, dataset details, plot/table/field/report handoff hints,
  field artifact summaries, diagnostics, PyVista optional/fallback state, and
  summary-first limitations without adding solver execution, script execution,
  full FRD/OpenFOAM field parsing, or mandatory PyVista.
- Recorded ResultViewer / FieldViewer closure evidence for Issue `#14`,
  preserving the no solver execution, no script execution, no external command
  execution, optional PyVista, and no full FRD/OpenFOAM field parser boundaries.
- Added v0.1.4 remaining scope review after Issue `#14` and Issue `#15`
  closure, selecting Issue `#17` VFEA experimental scope definition as the next
  planning-only slice while keeping Issues `#6`-`#11` live optional validation
  environment-dependent and deferred.
- Defined the experimental VFEA scope for Issue `#17`, documenting FEASpec
  candidate/validator/human-review/benchmark requirements, CalculiX-first
  planning, optional/non-default Abaqus export planning only, and explicit
  non-goals against automatic unreviewed solver execution, VLM API integration,
  topology optimization implementation, and certification claims.
- Recorded VFEA scope closure evidence for Issue `#17`, preserving the
  planning-only status, human-review requirement, no automatic solver execution,
  no mandatory Abaqus, no credentials, no topology optimization implementation,
  no certification, and no native commercial CAD import boundaries.
- Added a v0.1.4 completion review, recording that Issues `#12`, `#15`, `#14`,
  and `#17` complete the planned workflow/product-polish and VFEA scope line
  while Issues `#6`-`#11` remain live optional validation and no version, tag,
  release, or asset mutation is performed.
- Added a release-boundary decision recommending `v0.1.4-rc1` as the cleaner
  next prerelease boundary if maintainers choose release prep, while preserving
  active metadata `0.1.3rc2.dev0` until a later metadata-alignment gate.
- Recorded a `v0.1.3rc2` maintenance revalidation baseline covering release
  integrity, workflow safety, asset smoke evidence, known warnings, and next
  maintenance choices.
- Opened the `v0.1.3rc2` maintenance development cycle after the public
  `v0.1.3-rc1` prerelease and attached release assets.
- Carried forward the local validation documentation commit with PySide6/Pillow
  evidence and the missing optional solver/science backend matrix.
- Kept `v0.1.3-rc1` as the current public prerelease tag; no `v0.1.3-rc2` tag
  was created by this development-cycle gate.

### Patch v0.1.3rc1 Release Candidate Tag Published

Release-candidate package version: `0.1.3rc1`

Release-candidate tag: `v0.1.3-rc1`

- OSW-RELEASE-003 aligns source package metadata to `0.1.3rc1` after
  OSW-RELEASE-002 preserved historical local tags through `v0.1.2` and repaired
  the default editable import path for this checkout.
- OSW-RELEASE-005 created the local annotated `v0.1.3-rc1` tag, OSW-RELEASE-008
  pushed only that tag to `origin`, and OSW-RELEASE-009 verified that the remote
  tag peels to `a6e8d3a8211e02359841d10e1947e16ab847b132`.
- The existing `v0.1.2` final tag remains historical source-release evidence at
  `c39f21372ef837f096aa0d430cced82adc6f3485` and must not be moved,
  recreated, retargeted, deleted, or reused as the current `develop` line.
- No branch push, all-tags push, force push, GitHub Release, package artifact,
  binary installer, or public announcement was created by the v0.1.3rc1
  tag-only gates.

## 0.1.2 - GitHub Source Release Published

### Patch v0.1.2 Source Release

Final package version: `0.1.2`

Published final tag: `v0.1.2`

- OSW-AUTO-072 prepared final `0.1.2` package metadata after the local
  `v0.1.2-rc1` candidate and OSW-AUTO-071 triage reported no P0/P1 blockers.
- OSW-AUTO-073 created the local annotated `v0.1.2` tag, and OSW-AUTO-077
  pushed only `refs/heads/develop:refs/heads/develop` and
  `refs/tags/v0.1.2:refs/tags/v0.1.2` to GitHub.
- Remote `develop` and `v0.1.2^{}` both resolve to
  `c39f21372ef837f096aa0d430cced82adc6f3485`; the remote annotated tag object
  verified by OSW-AUTO-077 is `353a87897c842ee01aaae18abc4d69f330406e09`.
- Local `v0.1.2-rc1` remains annotated evidence at
  `28b30c1f79d4c62d160629e96fc1fcefa2382ebe` and was not pushed by
  OSW-AUTO-077.
- The local `v0.1.1` final tag remains historical local-only evidence at
  `7b232f5003fcc8eb207846570499ffb3442d3197` and must not be published as
  current after the OSW-AUTO-067 GUI workflow fix.
- GUI workflow evidence remains based on OSW-AUTO-068 and OSW-AUTO-070: import
  creates visible project items, Project Tree and Properties update,
  Run/Generate uses `WorkbenchWorkflowSession`, and table/report state reflects
  imported project data and diagnostics.
- Known limitations remain P2/P3: optional external solver executables and
  live runs are environment-specific, manual desktop CUA depth is limited,
  Cantera 3.2 emits a deprecation warning, external URL freshness is outside the
  local docs checker, and packaging smoke is separate.
- Release artifacts, a GitHub Release page, binary installers, and public
  announcement text were not created by the source publish gate.

### Patch v0.1.2rc1 Release Candidate

- OSW-AUTO-070 prepares package metadata for `0.1.2rc1` and the local
  annotated `v0.1.2-rc1` release-candidate gate after OSW-AUTO-068 verified
  the GUI workflow fix with no P0/P1 blockers.
- The local `v0.1.1` final tag remains historical evidence at
  `7b232f5003fcc8eb207846570499ffb3442d3197` and must not be published as
  current after the post-tag GUI workflow fix.
- `v0.1.2-rc1` is local-only unless a later explicit maintainer push gate
  approves it. Final `0.1.2` / `v0.1.2`, release artifacts, public push, and
  announcement remain blocked.

### GUI Workflow Glue

- OSW-AUTO-067 improves the GUI-native Import -> Configure/Inspect ->
  Run/Generate -> Result/Table -> Report path after OSW-AUTO-066 classified the
  interactive GUI workflow as `PASS_WITH_LIMITATIONS`.
- GUI imports can now add visible project items for supported mesh, standard
  geometry, `.m`, and `.mat` preview paths; selection updates the properties
  panel and table/plot/mesh preview state where data is available.
- GUI Run/Generate routes through a workflow service that prepares bounded
  case/template outputs or records optional dependency diagnostics without
  direct GUI solver subprocess execution.
- GUI report export now includes current imported/project state, result tables,
  mesh metadata, figure placeholders, and diagnostics when available.
- The local annotated `v0.1.1` tag remains preserved release evidence at
  `7b232f5003fcc8eb207846570499ffb3442d3197`. After this post-release workflow
  fix merges, `develop` is ahead of `v0.1.1`; public publish remains blocked
  pending a new release/version decision.

## 0.1.1 - Final Metadata Prepared

Final package version: `0.1.1`

Planned final local tag: `v0.1.1`

Final v0.1.1 metadata is prepared after the patch RC1 recovery path passed local
QA and source-install validation. The final `v0.1.1` tag is not created by this
release-prep update; it remains pending a dedicated local tag gate. No public tag
push, release artifact build, external solver binary bundle, remote push gate, or
public announcement is created by this update.

### Release Evidence

- Historical local `v0.1.0` evidence remains preserved at
  `da8728adf679314442755ed781c1dd57d1c6ed27` and must not be published as the
  current release.
- Local annotated `v0.1.1-rc1` evidence remains preserved at
  `da1a2c9e2d27674dc4bb85a2800138170c4c4dec`; it was not pushed.
- OSW-AUTO-061A was a docs/readiness cleanup only. The maintainer accepted that
  docs-only post-RC delta for this final-prep path.
- OSW-AUTO-057 fixed the isolated source-run blockers found after the local
  `v0.1.0` tag was created, including Ruff UP042 enum issues and subprocess
  PATH stabilization for QA tests.
- OSW-AUTO-058 verified a fresh source-install retest with no P0/P1 blockers.
- OSW-AUTO-060 verified `0.1.1rc1` source-install validation with ruff,
  default/importlib pytest, fast QA, pre-merge QA, docs link checking, and
  duplicate basename checking.

### Known Limitations

- Optional external solver executables remain environment-specific and are not
  bundled by default.
- GUI live interaction depth remains environment-specific; source-install
  validation records dependency and offscreen/QA evidence, not a full manual GUI
  UAT.
- External URL freshness remains out of scope for the local-only docs checker.
- Public push remains blocked until an explicit maintainer gate.

## 0.1.1rc1 - Patch Release Candidate

Release candidate package version: `0.1.1rc1`

Local release-candidate tag: `v0.1.1-rc1`

This patch release candidate follows the source-install recovery path selected
in OSW-AUTO-059. The existing local annotated `v0.1.0` tag remains historical
local-only evidence at `da8728adf679314442755ed781c1dd57d1c6ed27` and must not
be published as the current release. `v0.1.1-rc1` is local-only unless a later
explicit maintainer push gate approves the exact tag.

No final `v0.1.1` tag, public tag push, release artifact build, external solver
binary bundle, remote push gate, or public announcement is created by this
release-candidate prep.

### Fixed Blocker Summary

- OSW-AUTO-057 fixed the isolated source-run blockers found after the local
  `v0.1.0` tag was created, including Ruff UP042 enum issues and subprocess
  PATH stabilization for QA tests.
- OSW-AUTO-058 verified a fresh source-install retest with ruff, default
  pytest, importlib pytest, fast QA, pre-merge QA, docs link checking, duplicate
  basename checking, and GUI offscreen launch passing with no P0/P1 blockers.
- OSW-AUTO-060 updates package metadata and release checks for the
  `0.1.1rc1` patch candidate without moving or publishing historical tags.

### Known Limitations

- Optional external solver executables remain environment-specific and are not
  bundled by default.
- GUI live interaction depth remains environment-specific even though offscreen
  launch smoke passed in source-install retest.
- External URL freshness remains out of scope for the local-only docs checker.
- Final `v0.1.1` remains blocked until a later final release gate.
- Public push remains blocked until an explicit maintainer gate.

## 0.1.0 - Final Metadata Prepared

Final package version: `0.1.0`

Planned final local tag: `v0.1.0`

Final v0.1.0 metadata is prepared after local RC3 UAT passed with no P0 or P1
blockers. The final `v0.1.0` tag is not created by this release-prep update; it
remains pending a dedicated local tag gate. No public tag push, release artifact
build, external solver binary bundle, remote push gate, or public announcement is
created by this update.

Local annotated `v0.1.0-rc1`, `v0.1.0-rc2`, and `v0.1.0-rc3` remain historical
local release evidence. RC3 points to
`dc7df75c53f0a4acb0a1ccf33d97c01ffdde4b16`, the last release-candidate commit
before this final metadata-prep change.

### Highlights

- PySide6 desktop GUI shell architecture remains optional behind the `gui`
  extra, with CLI diagnostics when PySide6 is unavailable.
- Plugin/add-in architecture covers importers, solvers, scripts,
  post-processing, and reports without executing plugin code during manifest
  validation.
- ProjectSchema, UnitSystem, MaterialDB, ResultDataset, and FigureDataset define
  the core v0.1 data contracts.
- Standard/exported CAD and mesh import policy remains explicit; commercial
  native CAD direct import is out of scope.
- meshio, Gmsh, PyVista, and Matplotlib workflows are optional integration
  surfaces with missing-dependency diagnostics.
- CalculiX linear static demo coverage includes input deck generation, optional
  runner diagnostics, result parsing, golden fixtures, and validation helpers.
- OpenFOAM cavity and duct template demos remain bounded educational templates,
  not a full OpenFOAM UI.
- Cantera and CoolProp basic demos cover small chemistry/property workflows with
  explicit SI-unit data and optional dependency behavior.
- MATLAB/Octave `.m` and `.mat` workflows remain preview-first; importing a
  script does not auto-run code.
- FigureDataset, ResultDataset, and HTML report workflows include assumptions,
  warnings, validation notes, figures, result tables, and known limitations.
- Validation, golden tests, docs link checking, duplicate test basename
  prevention, scope checks, architecture checks, and solver artifact scans are
  part of the release QA harness.

### RC3 Local UAT Summary

- OSW-AUTO-052 local UAT passed with no P0 or P1 blockers.
- Automated QA passed: release metadata, docs link checker, duplicate basename
  checker, scope drift, architecture boundaries, solver artifact scan, fast QA,
  pre-merge QA, ruff, required pytest suites, and default `pytest -q`.
- Demo smoke results: CAD import and HTML report passed; mesh import, Gmsh,
  CalculiX, OpenFOAM, Cantera/CoolProp, and MATLAB/Octave workflows passed with
  optional dependency missing where local optional stacks were unavailable.
- PySide6 was missing in the local UAT environment, so GUI help and friendly
  missing-extra diagnostics passed, but live GUI interaction was skipped.
- Live external solver runs were not performed because local solver executables
  and optional stacks were missing; this is treated as environment-specific and
  non-blocking for the base v0.1 source workflow.

### Known Limitations

- Simulink, `.slx`, and `.mlapp` workflows are not supported.
- Native commercial CAD direct import is not supported; use standard/exported
  formats such as STEP, STL, OBJ, IGES, BREP, or mesh formats.
- OSW is not a MATLAB clone, full ANSYS clone, full OpenFOAM UI, industrial
  certified CAE product, or substitute for expert engineering judgment.
- External solver executables and heavy optional Python stacks are not bundled
  by default and remain local environment responsibilities.
- External URL freshness is intentionally out of scope for the local-only docs
  link checker.

## 0.1.0rc3 - Draft

Release candidate package version: `0.1.0rc3`

Planned local release-candidate tag: `v0.1.0-rc3`

RC3 is the current local release-candidate target for `develop` after the
post-RC2 hardening work in OSW-AUTO-047 and OSW-AUTO-048. Local annotated
`v0.1.0-rc1` remains historical evidence at
`29c5c8bec8df30c7f7be72fc9be5e5409794968e`; local annotated `v0.1.0-rc2`
remains historical evidence at
`684dc6138d4257564bbcdd176a9d5ed311a7316d` and is no longer current
`develop` after OSW-AUTO-047/048. Neither prior RC tag should be pushed as the
current RC.

No public tag push, final `v0.1.0` tag, release artifact build, external solver
binary bundle, remote push gate, or public announcement is created by this
release-notes update.

### Highlights

- Package and CLI version metadata move from `0.1.0rc2` to `0.1.0rc3`.
- Release metadata QA accepts prior local rc1 and rc2 evidence while validating
  an expected annotated rc3 tag after the local tag gate.
- Default `pytest -q` collection remains fixed by OSW-AUTO-047 through unique
  test basenames and duplicate-basename QA.
- Documentation link checking is implemented by OSW-AUTO-048 and remains
  local-only/no-network by default. External URL freshness is intentionally out
  of scope for that checker.

### Known Limitations

- OSW v0.1 remains educational and research oriented, with unchanged
  out-of-scope boundaries recorded in `docs/known_limitations.md`.
- Optional external solvers and tools are not bundled by default.
- Final `v0.1.0`, public tag push, release artifacts, and public announcement
  remain blocked until separate maintainer-controlled gates.

## 0.1.0rc2 - Draft

Release candidate package version: `0.1.0rc2`

Planned release-candidate tag: `v0.1.0-rc2`

RC2 supersedes the local-only rc1 tag as the current `develop` release
candidate. The existing local `v0.1.0-rc1` tag remains historical evidence for
OSW-AUTO-043 and must not be pushed as the current RC after OSW-AUTO-044A/045.

No public tag push, final `v0.1.0` tag, release artifact build, external solver
binary bundle, or public announcement is created by this release-notes update.

### Highlights

- Package and CLI version metadata move from `0.1.0rc1` to `0.1.0rc2`.
- Release metadata QA now supports strict pre-tag checks, prior local RC
  evidence, and current RC tag validation without mutating tags.
- RC2 keeps the v0.1 feature scope from rc1: PySide6 GUI shell,
  plugin/add-in architecture, ProjectSchema / UnitSystem / MaterialDB,
  standard CAD/Mesh import policy, meshio/Gmsh/PyVista surfaces, CalculiX
  linear static demo, OpenFOAM cavity/duct templates, Cantera/CoolProp demos,
  MATLAB/Octave preview-first workflow, FigureDataset / ResultDataset / report
  flow, validation/golden/QA harness.

### Known Limitations

- OSW v0.1 remains educational and research oriented, with unchanged
  out-of-scope boundaries recorded in `docs/known_limitations.md`.
- Optional external solvers and tools are not bundled by default.
- Default `pytest -q` duplicate basename collection behavior remains a P2
  follow-up if still present; split suites and importlib-mode collection remain
  release evidence.
- `tools/qa/check_docs_links.py` remains a P2 follow-up if still absent.

## 0.1.0rc1 - Draft

Release candidate package version: `0.1.0rc1`

Planned release-candidate tag: `v0.1.0-rc1`

No Git tag is created by the release-notes step.

### Highlights

- PySide6 GUI shell with preview-oriented workflows.
- Plugin/add-in architecture for importers, solvers, script workflows,
  post-processing, and reports.
- ProjectSchema, UnitSystem, MaterialDB, ResultDataset, and FigureDataset
  contracts.
- Standard/exported CAD and mesh import policy; no native commercial CAD direct
  import claim.
- meshio, Gmsh, and PyVista pipeline surfaces with optional dependency
  diagnostics.
- CalculiX linear static cantilever demo with input deck generation, optional
  runner diagnostics, result summaries, and validation helper.
- OpenFOAM cavity and duct template demos; no full OpenFOAM UI or broad solver
  coverage claim.
- Cantera and CoolProp basic chemistry/property demos with optional dependency
  diagnostics.
- MATLAB/Octave `.m` and `.mat` preview-first workflow; script execution remains
  explicit and user-triggered.
- FigureDataset, ResultDataset, and HTML report workflow with assumptions,
  warnings, validation notes, and known limitations.
- Validation matrix, golden tests, physical sanity checks, and local QA harness
  for release readiness review.
- Plugin install, manifest validation, and health reporting surfaces designed to
  avoid executing plugin code during manifest validation.

### Known Limitations

- OSW v0.1 is educational and research oriented; it is not industrial
  certified and does not replace expert engineering judgment.
- Simulink, `.slx`, and `.mlapp` workflows are not supported.
- Commercial native CAD direct import is not supported. Use standard/exported
  formats such as STEP, STL, OBJ, IGES, or mesh formats.
- OSW is not a MATLAB clone, ANSYS clone, commercial CAD replacement, process
  simulator, or full OpenFOAM UI.
- OpenFOAM support is limited to bounded cavity and duct templates.
- Optional external solvers and tools such as CalculiX, OpenFOAM tools, Gmsh,
  GNU Octave, and SU2 are not bundled by default.
- Optional Python stacks such as PySide6, meshio, PyVista, Cantera, CoolProp,
  SciPy, and hdf5storage may be absent in base environments and should produce
  diagnostics or skips rather than hidden success.
- The broad default `pytest -q` command has a P2 follow-up for duplicate test
  module basename collection behavior if still present; CI-style split suites
  and importlib-mode collection are the current release evidence path.
- `tools/qa/check_docs_links.py` remains a P2 follow-up if still absent; docs
  link checking is recorded as a placeholder skip.

### QA Evidence Summary

- Pre-merge QA: `python tools/qa/run_pre_merge_qa.py` is part of the release
  evidence path when available.
- Fast QA: `python tools/qa/run_fast_qa.py` checks CLI version, doctor output,
  unit tests, lint, scope, architecture, and artifact scans.
- Unit, integration, golden, and validation suites are documented in
  `docs/10_release_checklist.md`.
- Optional external solver smoke checks remain environment-specific and are not
  required for base release-candidate metadata.

### Release Discipline

- Repository source license: `GPL-3.0-or-later`.
- The `LICENSE` file contains canonical GNU GPL version 3 text; the "or later"
  grant is recorded in project metadata and release documentation.
- Third-party dependency and optional solver notices are tracked in
  `docs/14_third_party_notices.md`.
- Source and wheel artifacts may be prepared only after the dedicated release/tag
  gate passes. External solver binaries are not bundled by default.
