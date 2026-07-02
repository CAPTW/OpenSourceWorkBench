# Optional Solver Plugin Manifest Reload Acceptance Persistence GUI Review Implementation

## 1. Status

Experimental persistence GUI review panel implemented.

The panel is display-only, view-model/result-only, supplied-record-only, and
non-mutating. It adds no writer invocation, no file writes, no file reading, no
file parsing, no input state-file reading, no input state-file parsing, no
reload file-reader invocation, no OSW-EXP-102 state-writer invocation, no CLI
behavior, no CLI subprocess, no subprocess use, no runtime reload acceptance,
no active acceptance mutation, no ProjectSchema mutation, no default target
path, no background write, no directory scan, no network fetch, no plugin
package import, no reloadable bundle creation, no export file creation, no
report file creation, no clipboard behavior, no report attachment, no
open-output-folder behavior, no live discovery, no passive refresh, no
validation execution, no solver execution, no dependency installation, no
dependency uninstall, no solver uninstall, no automatic activation, no trust
restoration, no issue mutation, no release mutation, no tag mutation, no asset
mutation, no version bump, no validation-pass claim, no validation-fail claim,
no issue-closure claim, no bundled-solver claim, and no certification claim.

## 2. Purpose

This gate implements the OSW-EXP-129 display-only PySide review surface for
reload acceptance persistence planning. The panel lets users inspect supplied
OSW-EXP-125 persistence view-model records and supplied OSW-EXP-126 writer
dry-run/result mappings without making the GUI a writer, loader, validator,
runtime acceptance surface, ProjectSchema editor, issue workflow, release
workflow, or certification surface.

## 3. Public Module/Class Names

- Module:
  `osw.gui.dialogs.optional_solver_plugin_manifest_reload_acceptance_persistence_panel`
- Class:
  `OptionalSolverPluginManifestReloadAcceptancePersistencePanel`
- Lazy package export:
  `osw.gui.dialogs.OptionalSolverPluginManifestReloadAcceptancePersistencePanel`

## 4. Input Policy

The panel consumes a supplied
`OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel` or any safe
mapping/object exposing `to_mapping()`. It may also consume a supplied writer
dry-run/result mapping/object exposing `to_mapping()`.

The panel does not read persisted state files, parse state files, inspect
directories, invoke the reload file reader, invoke the OSW-EXP-102 state
writer, invoke the OSW-EXP-126 persistence writer, call CLI code, use CLI
subprocesses, use subprocesses, fetch network manifests, or import plugin
packages.

## 5. Construction Behavior

Construction creates read-only Qt tables and a read-only safety text panel. If
no view-model is supplied, the panel renders the deterministic unavailable
persistence state. Construction does not write files, read files, parse files,
choose a target, create directories, call a writer, call a reader, call CLI
code, mutate ProjectSchema, perform runtime reload acceptance, or run
discovery, validation, solver execution, install, or uninstall behavior.

## 6. View-Model Rendering

The panel renders the supplied persistence view-model mapping directly. It
shows summary/readiness, storage policy, write-plan data, acknowledgements,
expiry, schema/migration rows, provenance, evidence/history, diagnostics,
non-action flags, disabled/future actions, and safety guidance. The panel does
not compute an independent acceptance policy and does not rewrite supplied
diagnostics as truth.

## 7. Writer Result Rendering

When a caller supplies a writer dry-run/result mapping, the panel displays
status, redacted target display, planned/written flags, byte count, SHA-256,
cleanup status, temporary-file status, diagnostics, warnings, blockers, and
the caveat that any write success remains only local review-record persistence.
The panel does not invoke the writer and does not call the writer with
`dry_run=False`.

## 8. Target/Storage Rendering

The target/storage tab renders storage policy id, storage label, redacted target
display, target required state, target blocked state, parent missing,
directory-target blocked, symlink blocked, existing target replacement policy,
no default target path, no background path, and no directory creation. Target
display is redacted; raw absolute paths are not shown by default.

## 9. Dry-Run/Write-Plan Rendering

The dry-run/write-plan tab renders `dry_run`, `planned`,
`writer_future_only`, byte count, SHA-256, payload kind/schema,
blocker/warning/diagnostic counts, non-action context, and disabled/future
action context. It explicitly states that dry-run is not write, dry-run success
is not validation success, dry-run success is not validation failure, dry-run
success is not runtime acceptance, and dry-run success is not ProjectSchema
mutation.

## 10. Acknowledgement Rendering

The acknowledgement tab renders required, satisfied, expired, blocking,
not-validation-evidence, and not-trust-restoration states. Missing or expired
acknowledgements remain blockers for future writer behavior. Acknowledgements
remain review data only; they are not validation evidence and are not trust
restoration.

## 11. Expiry Rendering

The expiry tab renders the persistence acknowledgement expiry rows supplied by
the view-model, including reload, source fingerprint change, schema version
change, unsafe claim appearance, trust policy change, future discovery-refresh
result, file reader policy change, GUI file-dialog policy change, CLI
explicit-path policy change, acceptance policy change, ProjectSchema policy
change, validation issue state change, persistence schema change, persistence
storage-policy change, persistence CLI policy change, persistence GUI policy
change, and writer policy change when present. Expiry requires re-review and is
not validation failure.

## 12. Schema/Migration Rendering

The schema tab renders payload kind, schema version, schema mismatch,
unsupported schema, migration required, separate-from-ProjectSchema state, and
the fact that the GUI does not repair or migrate files. Schema mismatch is not
validation failure. Persistence schema remains separate from ProjectSchema.

## 13. Redaction/Privacy Rendering

The redaction/privacy tab renders that raw paths are hidden by default,
secret-like values are blocked, unredacted paths remain blocked by policy,
fingerprints are not trust signals, full file contents are not displayed,
plugin code is not displayed, and diagnostics are rendered through redaction
helpers.

## 14. Provenance Rendering

The provenance tab renders persistence view-model source, source display,
source kind, preview identifier, payload fingerprint when supplied safely,
untrusted-by-default state, non-authoritative state, and trust-label-not-
certification state. Provenance remains reference-only and does not certify or
validate a source.

## 15. Candidate Lifecycle Rendering

The lifecycle tab renders inactive preview review-only state, persisted active
future activation review, deactivated review state, reactivation future review,
discovery-refresh review state, no automatic activation, no trust restoration,
and no built-in override.

## 16. Stale-Source/Re-Preview Rendering

The stale-source tab renders that old previews are not silently trusted,
missing/moved/changed sources require re-preview, the persistence GUI does not
inspect referenced source files, stale-source state is not validation failure,
and re-preview remains future-gated.

## 17. Conflict/Shared-Stack Rendering

The conflict tab renders conflict visibility, built-ins winning by default,
persisted records not overriding built-ins, shared-stack warning visibility,
the GUI not resolving conflicts, and future policy requirements.

## 18. Unsafe-Claim Rendering

The unsafe-claim tab renders unsafe claims as visible and blocked. It states
that unsafe claims are not persisted as truth and that validation success,
validation failure, issue closure, release mutation, bundled solver,
dependency installation, solver execution, trust restoration, and
certification claims remain blocked.

## 19. Evidence/History Rendering

The evidence/history tab renders reference-only history and evidence rows.
Historical evidence remains reference-only, skipped-missing remains
skipped-missing, persisted records are not validation evidence, no evidence is
deleted or rewritten, and no issue closure is implied.

## 20. Diagnostics Rendering

The diagnostics tab renders supplied OSW-EXP-125 persistence diagnostics and
supplied OSW-EXP-126 writer diagnostics. It also reserves and displays
`OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_*` diagnostics for GUI review
availability, not-requested state, preview rendering, future-only planning,
future-only write behavior, target required/redacted state, acknowledgement
requirements, blockers, dry-run-not-write, write-not-runtime-acceptance, no
validation claim, no ProjectSchema mutation, and error state.

## 21. Non-Action Flags Rendering

The non-action tab renders false/safety states for runtime reload acceptance,
persistence write, ProjectSchema mutation, default path, background write,
directory scan, network fetch, plugin package import, CLI subprocess, GUI
subprocess, reloadable bundle, export file, report file, clipboard, report
attachment, open-output-folder behavior, live discovery, passive refresh,
validation, solver execution, dependency install/uninstall, solver uninstall,
candidate activation, trust restoration, issue mutation, release mutation, tag
mutation, asset mutation, version bump, validation-pass claim,
validation-fail claim, issue-closure claim, bundled-solver claim, and
certification claim. A supplied `persistence_write_performed=True` value is
rendered only as explicit local review-record write metadata, never runtime
acceptance.

## 22. Disabled/Future Actions Rendering

The disabled/future actions tab renders disabled future actions including
choose target, plan persistence record, write persistence record, persist
acceptance record, write acceptance state, accept for session review, accept as
trusted, activate reloaded candidate, refresh discovery, validate solver,
execute solver, install dependency, uninstall dependency, uninstall solver,
mutate ProjectSchema, create export summary, create report file, create
reloadable bundle, copy to clipboard, attach to report, open output folder,
close issue, mutate release, push tag, upload asset, claim validation success,
claim validation failure, and claim certification.

## 23. Safety Guidance

The safety tab states that the panel is display-only; construction, refresh,
target-display update, dry-run planning, and writer-result display are not
runtime reload acceptance. It states that dry-run is not write, dry-run success
is not validation success or validation failure, persisted records are not
validation evidence or ProjectSchema mutation, persisted records do not restore
trust or automatically activate candidates, persisted records do not close
issues or mutate releases, trust labels are not certification, skipped-missing
remains skipped-missing, issues #6 through #11 remain open, and
prepared-machine validation remains separate.

## 24. Relationship to OSW-EXP-129 Design

OSW-EXP-129 defined the display-only persistence GUI review contract. This gate
implements that contract as a read-only PySide panel and keeps actual GUI write
behavior, target chooser behavior, writer invocation, ProjectSchema
integration, validation, issue/release mutation, and certification out of
scope.

## 25. Relationship to OSW-EXP-126 Writer

The panel may display supplied writer dry-run/result records. It does not
import, instantiate, or call the writer. The writer remains explicit-path,
dry-run-first, acknowledgement-gated, redacted, and separately invoked by
callers outside this panel.

## 26. Relationship to OSW-EXP-128 CLI

The OSW-EXP-128 CLI remains stdout-first and dry-run-only. The GUI panel does
not call the CLI and does not use CLI subprocesses. GUI and CLI share the
persistence view-model/writer result contracts through supplied in-memory
records only.

## 27. Relationship to OSW-EXP-125 Persistence View-Model

The persistence view-model remains the source of readiness and persistence
review rows. The GUI renders its mapping/text-derived rows and does not edit
the view-model, compute an independent acceptance policy, write persistence
state, or create a runtime accepted state.

## 28. Relationship to Reload Acceptance GUI/CLI

Existing reload acceptance GUI and CLI review surfaces remain review-only.
Persistence GUI review is separate from acceptance review. Acceptance success
does not imply persistence, and persistence review or writer-result display
does not imply runtime acceptance.

## 29. Relationship to Reload File Reader and Explicit-Path Preview

The reload file reader remains explicit-path and bounded. This panel does not
read input state files and does not invoke the reload file reader. Preview
success does not imply acceptance, and acceptance review does not imply
persistence.

## 30. Relationship to ProjectSchema

The panel does not mutate ProjectSchema. A persistence review record is not
ProjectSchema state and is not project validation evidence. Any ProjectSchema
integration requires a separate future gate.

## 31. Relationship to Live Optional Validation Issues

Issues #6 through #11 remain open. The panel is not live optional validation,
does not convert skipped-missing into success, does not close issues, and does
not create prepared-machine validation evidence.

## 32. Security/Privacy Review

The panel redacts raw paths, secret-like values, tokens, API keys, external
URLs, and private path context from rendered cells. It does not display full
file contents, plugin code, raw remote payloads, or hidden environment values.
It performs no remote URL fetch, script execution, plugin import, solver
execution, or writer invocation. Malicious payload fields remain supplied data
and are displayed only through redaction helpers and blocker/diagnostic rows.

## 33. Non-Actions

This gate does not invoke writer behavior, write files, read files, parse
files, read input state files, parse input state files, invoke the reload
file-reader, invoke the OSW-EXP-102 state writer, call CLI code, use CLI
subprocesses, use subprocesses, accept runtime reload, perform active
acceptance mutation, mutate ProjectSchema, add default target paths, add
background writes, scan directories, fetch network manifests, import plugin
packages, create reloadable bundles, create export files, create report files,
add clipboard behavior, add report attachment behavior, add open-output-folder
behavior, add live discovery, add passive refresh, run validation, run solver
execution, install dependencies, uninstall dependencies, uninstall solvers,
automatically activate candidates, restore trust, mutate issues, mutate
releases, mutate tags, mutate assets, bump versions, claim validation pass,
claim validation failure, claim issue closure, claim bundled solver support, or
claim certification.

## 34. Testing Strategy

Focused GUI tests cover module import and package lazy export, inert
construction, no file creation, no writer invocation by source boundary, no
reload file-reader or CLI/subprocess boundary, unavailable guidance, supplied
persistence view-model rendering, supplied writer-result rendering, target
redaction, secret redaction, acknowledgement rows, expiry rows,
schema/migration rows, redaction/privacy rows, provenance rows, candidate
lifecycle rows, stale-source rows, conflict/shared-stack rows, unsafe-claim
rows, evidence/history rows, diagnostics including
`OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_*`, non-action flags,
disabled/future actions, safety guidance, refresh/re-render behavior, setter
behavior, and no output files during tests.

Adjacent persistence CLI, writer, persistence view-model, acceptance
view-model, acceptance CLI, acceptance panel, state writer, design docs, reload
view-model, file reader, file-dialog panel, and reload panel tests remain part
of the validation set.

## 35. Future Gates

Suggested next gates:

- `OSW-EXP-131_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_DESIGN`, if write UI is ever needed
- `OSW-EXP-132_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_DESIGN`, if actual CLI writes are ever needed
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION`, if a prepared machine is available

Any future write UI must remain separately gated and must preserve explicit
target review, dry-run-first planning, caller acknowledgement, redaction,
non-authoritative records, no runtime acceptance, no ProjectSchema mutation, no
validation/solver execution, no activation/trust restoration, no issue/release
mutation, and no certification claims.
