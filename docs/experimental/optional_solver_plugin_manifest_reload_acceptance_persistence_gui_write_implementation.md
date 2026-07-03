# Optional Solver Plugin Manifest Reload Acceptance Persistence GUI Write Implementation

## 1. Status

Experimental persistence GUI write panel implemented.

The panel is explicit-target only, dry-run-first, acknowledgement-gated, and
confirmation-gated. It uses the OSW-EXP-126 writer only. It performs no write
on construction, no write on refresh, no write on target selection, no write
on dry-run, selects no default path, and performs no background write.

The panel performs no input state-file reading or parsing, no reload
file-reader invocation, no OSW-EXP-102 state-writer invocation, no CLI
behavior, no CLI subprocess, no subprocess use, no runtime reload acceptance,
no active acceptance mutation, no ProjectSchema mutation, no directory scan,
no network fetch, no plugin package import, no reloadable bundle creation, no
export file creation, no report file creation, no clipboard behavior, no
report attachment, no open-output-folder behavior, no live discovery, no
passive refresh, no validation execution, no solver execution, no dependency
installation, no dependency uninstall, no solver uninstall, no automatic
activation, no trust restoration, no issue/release/tag/asset mutation, no
version bump, no validation-pass claim, no validation-fail claim, no
issue-closure claim, no bundled-solver claim, and no certification claims.

## 2. Purpose

This gate implements the OSW-EXP-131 GUI write design as a narrow PySide panel
for explicit local reload acceptance persistence review-record writes. It
builds on the OSW-EXP-130 display-only panel, consumes a supplied OSW-EXP-125
persistence view-model, and delegates dry-run and actual write requests to the
OSW-EXP-126 writer API.

GUI write success remains local review-record persistence only. It is not
runtime reload acceptance, validation evidence, validation failure,
ProjectSchema mutation, trust restoration, automatic activation, issue closure,
release mutation, bundled-solver evidence, or certification.

## 3. Public Module/Class Names

- Module:
  `osw.gui.dialogs.optional_solver_plugin_manifest_reload_acceptance_persistence_write_panel`
- Class:
  `OptionalSolverPluginManifestReloadAcceptancePersistenceWritePanel`
- Lazy package export:
  `osw.gui.dialogs.OptionalSolverPluginManifestReloadAcceptancePersistenceWritePanel`

## 4. Input Policy

The panel consumes a supplied
`OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel` or compatible
safe mapping/object rendered by the base display-only panel. Target paths are
caller supplied through `set_target_path()`.

The panel does not read target files, parse input state files, inspect source
manifests, invoke the reload file reader, invoke the OSW-EXP-102 state writer,
call CLI code, use CLI subprocesses, use subprocesses, scan directories, fetch
network manifests, or import plugin packages.

## 5. Construction Behavior

Construction creates the review panel and explicit write-gate widgets. If no
target is supplied, the panel displays `target_required=yes`. Construction does
not write files, read files, parse files, choose a target, create directories,
invoke the writer, invoke a reader, call CLI code, mutate ProjectSchema, accept
runtime reload, run discovery, run validation, run solver execution, install
dependencies, uninstall dependencies, activate candidates, restore trust,
mutate issues/releases/tags/assets, or claim certification.

## 6. Target Selection/Assignment Behavior

The implementation provides `set_target_path()` and `clear_target()` as
explicit caller-controlled assignment methods. It does not open a native file
dialog and does not choose a default target path. Setting or clearing a target
updates only widget-local state and redacted display text.

Target assignment invalidates the previous dry-run and clears displayed writer
mapping state. It does not create directories, inspect parent directories,
scan directories, read the target, parse target content, write the target, or
imply runtime acceptance or validation evidence.

## 7. Dry-Run Behavior

`run_dry_run()` blocks locally when no target is set and returns a deterministic
blocked writer-style mapping without invoking the writer. With an explicit
target, it builds a `ReloadAcceptancePersistenceWriteRequest` with
`dry_run=True` and `caller_acknowledged_persistence_write=False`, then calls the
OSW-EXP-126 writer API.

Dry-run creates no files. Dry-run success is a write plan only; it is not an
actual write, runtime reload acceptance, validation success, validation
failure, ProjectSchema mutation, issue closure, release mutation, or
certification.

## 8. Acknowledgement And Confirmation Behavior

The panel exposes `set_acknowledged()` and `set_confirmed()` and mirrors them
through checkboxes. Actual write remains blocked until acknowledgement and
confirmation are both true after a fresh successful dry-run.

Acknowledgement means only that the caller has reviewed the local
review-record persistence boundary. It is not validation evidence, trust
restoration, automatic activation, issue closure, release mutation, or
certification.

## 9. Actual Write Behavior

`write_persistence_record()` writes only when all gates pass:

- explicit target path is present
- successful dry-run exists
- dry-run is fresh for the current target/view-model/request state
- acknowledgement is present
- confirmation is present

When a gate is missing, the panel returns a deterministic blocked mapping and
does not invoke the writer. When all gates pass, the panel calls the OSW-EXP-126
writer API with `dry_run=False` and
`caller_acknowledged_persistence_write=True`. The write target is the explicit
caller-supplied target only.

## 10. Write Invalidation Behavior

Changing the target path, clearing the target, changing the supplied
view-model, or changing the explicit replacement policy invalidates the
previous dry-run. A stale dry-run blocks actual write until a new successful
dry-run is produced for the latest state.

## 11. Writer Request/Result Behavior

The panel builds `ReloadAcceptancePersistenceWriteRequest` records with the
OSW-EXP-126 payload kind and schema version, explicit target path, explicit
`allow_replace`, and `safety_review_id="osw-exp-132-gui-write"`. The request
context is `gui_explicit_target_dry_run_first_write`.

Writer results are converted with `to_mapping()` when available, then rendered
through the existing display-only writer-result surface. The panel does not
reinterpret writer diagnostics as validation truth.

## 12. Target/Storage Rendering

`target_text()` renders target-required state, redacted target display,
explicit replacement state, `default_target_path_used=no`, and
`background_write_performed=no`. Raw parent paths are hidden; the displayed
target label is the basename or a redacted external marker.

## 13. Dry-Run/Write-Plan Rendering

The panel reuses the OSW-EXP-130 dry-run/write-plan rendering and adds write
gate text showing whether the dry-run is fresh, acknowledgement is present,
confirmation is present, and write is ready. Dry-run display does not write and
does not imply runtime acceptance or validation evidence.

## 14. Writer Result Rendering

The panel renders writer status, planned/written flags, target display, byte
count, SHA-256, payload kind/schema, diagnostics, blockers, warnings, cleanup
state, and the local-review-record-only caveat supplied by the writer mapping.
Completed writer status means only an explicit local review-record persistence
write occurred.

## 15. Acknowledgement/Expiry Rendering

The base panel continues to render acknowledgement and expiry rows from the
supplied persistence view-model. The write panel adds explicit acknowledgement
and confirmation gates for GUI writes. Missing acknowledgement or stale
dry-run state blocks actual write.

## 16. Schema/Migration Rendering

Schema and migration rows remain rendered from the supplied persistence
view-model and writer result. Schema mismatch or unsupported schema is not a
validation failure. The GUI does not migrate files and does not mutate
ProjectSchema.

## 17. Redaction/Privacy Rendering

Target paths are redacted to display labels. Raw paths, secrets, tokens, API
keys, full file content, and plugin code are not displayed by the write panel.
Writer diagnostics remain redaction-first. Fingerprints are diagnostic context,
not trust signals.

## 18. Provenance Rendering

The panel renders supplied persistence provenance through the base panel and
writer provenance through writer result mappings. Provenance remains
reference-only and untrusted by default. Trust labels are not certification.

## 19. Candidate Lifecycle Rendering

Candidate lifecycle rows remain rendered from the supplied persistence
view-model. A persisted review record does not activate candidates, reactivate
deactivated candidates, restore trust, override built-ins, or alter runtime
reload state.

## 20. Stale-Source/Re-Preview Rendering

Stale-source and re-preview rows remain visible through the supplied
persistence view-model. The GUI write panel does not inspect referenced source
files and does not silently trust old previews. Stale-source state is not
validation failure.

## 21. Conflict/Shared-Stack Rendering

Conflict and shared-stack rows remain visible through the supplied persistence
view-model. Built-ins remain authoritative by default. The GUI write panel does
not resolve conflicts or override built-ins.

## 22. Unsafe-Claim Rendering

Unsafe claims remain visible through the supplied persistence view-model and
writer diagnostics. The GUI write panel blocks missing gates and relies on the
writer to block unsafe payloads. It does not persist unsafe claims as truth and
does not claim validation success, validation failure, issue closure, release
mutation, bundled solvers, dependency installation, solver execution, trust
restoration, or certification.

## 23. Evidence/History Rendering

Evidence/history rows remain rendered as reference-only context. A persisted
GUI write record is not validation evidence, does not delete or rewrite
history, does not close issues, and does not convert skipped-missing optional
validation into success.

## 24. Diagnostics Rendering

The panel surfaces writer diagnostics plus GUI write diagnostics:

- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_TARGET_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_DRY_RUN_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_STALE_DRY_RUN`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_ACK_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_CONFIRM_REQUIRED`

Diagnostics are review information only and are not validation claims.

## 25. Non-Action Flags Rendering

`write_non_action_flags()` renders downstream safety flags as false for runtime
acceptance, ProjectSchema mutation, default/background reload/write, directory
scan, network fetch, plugin import, CLI/GUI subprocess use, reloadable bundle,
export/report files, clipboard/report/open-folder behavior, discovery,
validation, solver execution, dependency install/uninstall, automatic
activation, trust restoration, issue/release/tag/asset mutation, version bump,
validation-pass/fail claim, issue-closure claim, bundled-solver claim, and
certification claim.

`persistence_write_performed` may be true only when the OSW-EXP-126 writer
reports an explicit local review-record write. It never means runtime
acceptance, ProjectSchema mutation, validation evidence, trust restoration,
automatic activation, issue closure, release mutation, or certification.

## 26. Disabled/Future Actions Rendering

`disabled_future_actions()` keeps unsafe actions documented as disabled or out
of scope: runtime acceptance, ProjectSchema mutation, live discovery, solver
validation, solver execution, dependency installation, automatic activation,
trust restoration, issue closure, release mutation, and certification claims.

## 27. Safety Guidance

The panel renders safety guidance stating that GUI write success is not runtime
reload acceptance, not validation evidence, not validation failure, not
ProjectSchema mutation, not trust restoration, not automatic activation, not
issue closure, not release mutation, and not certification. It also states that
writes are explicit local review-record persistence only, no default target
path is selected, no background write is performed, and no reload file reader,
CLI bridge, or subprocess is used.

## 28. Relationship To OSW-EXP-131 Design

OSW-EXP-131 designed this explicit-target, dry-run-first,
acknowledgement-gated, confirmation-gated GUI write workflow. This
implementation follows that design and keeps GUI writes local,
non-authoritative, redacted, and separate from runtime acceptance,
ProjectSchema state, validation, issue/release workflows, and certification.

## 29. Relationship To OSW-EXP-130 Display-Only Panel

The write panel subclasses the OSW-EXP-130 display-only panel and reuses its
view-model and writer-result rendering. It adds explicit write gates without
changing the display-only panel behavior.

## 30. Relationship To OSW-EXP-126 Writer

The panel uses the OSW-EXP-126 writer API for dry-run and actual local
review-record writes. It does not bypass writer path, redaction, schema,
acknowledgement, or safety policies. The writer remains the only code path that
serializes and writes the persistence record.

## 31. Relationship To OSW-EXP-128 CLI

The OSW-EXP-128 CLI remains stdout-first and dry-run-only. The GUI write panel
does not call CLI code and does not use CLI subprocesses. CLI success does not
imply GUI persistence or runtime acceptance.

## 32. Relationship To OSW-EXP-125 Persistence View-Model

The OSW-EXP-125 persistence view-model remains the source for readiness,
acknowledgements, expiry, diagnostics, non-action flags, disabled/future
actions, provenance, lifecycle, conflicts, unsafe claims, and evidence/history.
The GUI does not compute independent acceptance policy.

## 33. Relationship To Reload Acceptance GUI/CLI

Reload acceptance GUI and CLI surfaces remain review-only and separate from
persistence writes. Acceptance review success does not imply persistence, and
persistence write success does not imply runtime reload acceptance.

## 34. Relationship To Reload File Reader And Explicit-Path Preview

The reload file reader remains explicit-path and bounded. The GUI write panel
does not read input state files, parse input state files, or invoke the reload
file reader. Preview success does not imply acceptance, and acceptance success
does not imply persistence.

## 35. Relationship To ProjectSchema

The persistence record is not ProjectSchema state and is not project
validation evidence. The GUI write panel performs no ProjectSchema import,
mutation, migration, or synchronization. Future ProjectSchema integration
requires a separate gate.

## 36. Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. GUI write output is not live optional
validation evidence. Skipped-missing remains skipped-missing until a separate
prepared-machine validation gate changes that evidence.

## 37. Security/Privacy Review

The panel redacts target paths, avoids raw path display, displays no file
content, displays no plugin code, stores no secrets, fetches no remote URLs,
executes no scripts, imports no plugin packages, runs no solvers, and uses no
subprocess. Malicious payloads remain data for the supplied view-model and
writer diagnostics to block; the panel does not treat them as truth.

## 38. Non-Actions

This gate does not implement runtime reload acceptance, active acceptance
mutation, ProjectSchema mutation, default target path, background write,
directory scan, network fetch, plugin package import, input state-file reading,
input state-file parsing, reload file-reader invocation, OSW-EXP-102
state-writer invocation, CLI behavior, CLI subprocess use, subprocess use,
reloadable bundle creation, export file creation, report file creation,
clipboard behavior, report attachment, open-output-folder behavior, live
discovery, passive refresh, validation execution, solver execution, dependency
installation, dependency uninstall, solver uninstall, automatic activation,
trust restoration, issue mutation, release mutation, tag mutation, asset
mutation, version bump, validation-pass claim, validation-fail claim,
issue-closure claim, bundled-solver claim, or certification claim.

## 39. Testing Strategy

Focused GUI tests cover module import and lazy export, inert construction,
explicit target assignment, target redaction, no write on target assignment,
dry-run without target, dry-run with explicit target and no created file,
stale dry-run invalidation, missing acknowledgement, missing confirmation,
successful explicit write through the OSW-EXP-126 writer, existing-target
replace gating, writer blocked/error rendering, safety text, non-action flags,
disabled/future actions, and source boundary scans for forbidden imports/calls.

Adjacent persistence GUI review, persistence CLI, writer, persistence
view-model, acceptance view-model, acceptance CLI, acceptance panel, state
writer, design docs, reload view-model, file reader, file-dialog panel, and
reload panel tests remain part of the validation set.

## 40. Future Gates

Suggested next gates:

- `OSW-EXP-133_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_DESIGN`, if actual CLI writes are ever needed
- `OSW-EXP-134_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_IMPLEMENTATION`, if the CLI write design is accepted
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION`, if a prepared machine is available

Any future ProjectSchema, reload, discovery, validation, solver execution,
issue/release, tag/asset, or certification work remains separately gated.

## 41. CLI Write Implementation Follow-Up (OSW-EXP-134)

OSW-EXP-134 implements the separate CLI write path
([optional_solver_plugin_manifest_reload_acceptance_persistence_cli_write_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_cli_write_implementation.md)).
The GUI write panel and CLI write command share the OSW-EXP-126 writer
contract but do not invoke each other or use subprocess bridges. CLI write
success remains local review-record persistence only and does not imply GUI
write success, runtime reload acceptance, ProjectSchema mutation, validation
evidence, issue closure, release mutation, trust restoration, automatic
activation, bundled solver support, or certification.

## 42. Summary Audit Follow-Up (OSW-EXP-136)

OSW-EXP-136 adds a separate supplied-record summary audit
([optional_solver_plugin_manifest_reload_acceptance_persistence_summary_audit_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_summary_audit_implementation.md)).
The audit can summarize this GUI write result as local review-record evidence
only. It does not import or call GUI behavior, invoke this panel, call the
writer, read or parse input state files, invoke the reload file reader or
OSW-EXP-102 state writer, accept runtime reload, mutate ProjectSchema, run
discovery/validation/solver execution, activate candidates, restore trust,
mutate issues/releases/tags or assets, or claim certification.

## 43. ProjectSchema Boundary Follow-Up (OSW-EXP-137)

OSW-EXP-137 defines the separate ProjectSchema boundary design
([optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary_design.md](optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary_design.md)).
GUI write success remains local review-record persistence only. It is not
ProjectSchema state, ProjectSchema validation evidence, ProjectSchema
validation failure, ProjectSchema trust state, ProjectSchema activation state,
issue closure, release mutation, bundled-solver support, or certification.

## 44. ProjectSchema Boundary Implementation Follow-Up (OSW-EXP-138)

OSW-EXP-138 implements the separate supplied-record ProjectSchema boundary
([optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary_implementation.md](optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary_implementation.md)).
The boundary may summarize GUI write mappings only when supplied by a caller.
It does not import or invoke this panel, call the writer, read or parse input
state files, mutate ProjectSchema, create ProjectSchema validation evidence,
accept runtime reload, run discovery/validation/solver execution, restore
trust, activate candidates, mutate issues/releases/tags/assets, or claim
certification.

## 45. Prepared-Machine Prerequisites Follow-Up

`OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` was later
parked because no safe runnable prepared-machine manifest-state validation
command was found and the local optional solver/package prerequisites were
missing. The parked prerequisites are documented in
[Optional solver prepared-machine manifest-state validation prerequisites](optional_solver_prepared_machine_manifest_state_validation_prerequisites.md).

GUI write success remains explicit local review-record persistence only. It is
not prepared-machine validation, not validation success, not validation
failure, not ProjectSchema mutation, not issue closure, not release mutation,
not bundled-solver support, and not certification.
