# Optional solver plugin manifest deactivation GUI implementation

## Status

Experimental PySide deactivation GUI surface implemented.

- View-model driven.
- No deactivation persistence.
- No file deletion.
- No dependency uninstall.
- No solver uninstall.
- No discovery execution.
- No validation execution.
- No solver execution.
- No issue mutation and no release mutation.

This gate (OSW-EXP-086) implements a PySide review/control panel that renders the
pure OSW-EXP-085 deactivation view-model. It adds GUI source only; it does not
implement the product behavior of deactivating a manifest into persistent OSW
configuration.

## Purpose

Render deactivation readiness, deactivation state, deactivation candidates,
acknowledgements, blockers, diagnostics, shared-stack/conflict warnings, evidence
retention, trust/provenance badges, safety guidance, and disabled/future action
states for review only.

The panel lets a user inspect what a future deactivation persistence gate would
require (active candidates, acknowledgements, shared-stack/trust resolution)
without deleting files, uninstalling anything, running discovery, validation, or
solver execution.

## Public module and class names

- Module: `src/osw/gui/dialogs/optional_solver_plugin_manifest_deactivation_panel.py`
- Public class: `OptionalSolverPluginManifestDeactivationPanel`
- Lazy package export: `OptionalSolverPluginManifestDeactivationPanel` is exported
  from `osw.gui.dialogs` via the existing lazy `__getattr__` hook.

Constructor seams (dependency injection for testability):

- `view_model`: an `OptionalSolverPluginManifestDeactivationViewModel` (defaults to
  `.unavailable()`).
- `acknowledgement_callback`: an optional pure callback that receives the
  widget-local acknowledgement map and returns a fresh view-model.
- `theme_tokens`: optional theme tokens.

## User flow

- Empty / no-activation-state view: deactivation unavailable, active-required
  diagnostic, safety guidance, all unsafe actions disabled/future-only.
- Active candidate review: active candidates render with deactivation state,
  readiness, and blockers; untrusted sources are flagged.
- Deactivation-ready view: readiness `ready_non_persistent` is shown but nothing is
  persisted.
- Blocked-acknowledgement view: missing required acknowledgements block readiness.
- Shared-stack/conflict warning view: duplicate stack ids render with the
  built-ins-win policy and a required future-policy note.
- Deactivated view: deactivated candidates render with evidence retained and are
  not validation failures.
- Reactivation-future-gate view: a caller-supplied reactivation readiness is shown
  as future-only.

## Rendered sections

- Summary (readiness, state, counts, evidence-retained, honesty flags).
- Deactivation candidates (stack id, display name, source type, label, redacted
  reference, trust label, activation state, deactivation state, readiness,
  blockers, warnings, required acknowledgements, built-in relationship,
  shared-stack indicators, historical evidence, redaction flag).
- Acknowledgements (id, label, required, satisfied, blocking, reason, related,
  warning).
- Diagnostics (severity, category, `OSPMG_DEACTIVATION_*` code, message, source,
  stack id, suggested fix, blocker).
- Shared-stack/conflicts (stack id, built-in source, user/plugin source, active /
  deactivated states, built-ins-win default, keeps-built-ins note, required future
  policy).
- Evidence retention (historical evidence, evidence retained, not validation
  failure, skipped-missing remains, issue closure not implied, evidence not
  deleted).
- Trust/provenance (badges plus untrusted/authoritative/not-certification text).
- Action states (current/future/unavailable + disabled reasons).
- Safety guidance (boundary statements and blocked transitions).

## Action boundary

- Runtime deactivation is not implemented.
- Deactivation persistence is not implemented.
- File deletion is not performed.
- Dependency uninstall is not performed.
- Solver uninstall is not performed.
- Discovery is not executed.
- Validation is not executed.
- Solver execution is not performed.
- Issue/release mutation is not performed.

Unsafe actions (`run_discovery`, `run_validation`, `uninstall_dependency`,
`uninstall_solver`, `execute_solver`, `close_issue`) are always rendered as
unavailable, disabled, and future-only. Future actions (`request_deactivation`,
`deactivate_candidate`, `reactivate_candidate`, `export_redacted_summary`) render
as disabled (future-only). The `acknowledge_*` actions are widget-local and only
become enabled when a pure acknowledgement callback is injected; toggling them
rebuilds a supplied view-model and persists nothing.

## Trust and safety boundary

- User/plugin manifests are untrusted by default.
- Built-ins are authoritative by default.
- Trust label is not certification.
- Deactivated state is not validation evidence.
- Deactivated state is not a validation failure.
- Deactivation GUI is not deletion.
- Deactivation GUI is not uninstall.
- Deactivation GUI is not solver execution.

## Testing strategy

- Injected view-models render every section (empty, rich mix, blocked, ready,
  deactivated, shared-stack).
- Offscreen Qt subprocess tests (`QT_QPA_PLATFORM=offscreen`) with a PySide6
  import guard so base unit tests never require GUI extras.
- Disabled/future action-state assertions for unsafe actions.
- No-side-effect assertions: source scan rejects subprocess/discovery/
  file-write/delete/uninstall/clipboard/browser paths; the deactivation view-model
  remains free of PySide/Qt imports; the acknowledgement callback is widget-local
  and a panel without a callback ignores toggles.

## Relationship to OSW-EXP-081 design

The panel is a GUI surface over the OSW-EXP-081 deactivation contract. The runtime
deactivation behavior and persistence in that design remain future-gated.

## Relationship to OSW-EXP-085 view-model

The panel consumes the OSW-EXP-085 pure deactivation view-model. That view-model
remains pure: it gains no PySide/Qt imports, no file IO, no file deletion, no
deactivation persistence, no plugin import, no directory scan, no network fetch, no
discovery execution, no validation, no solver execution, and no dependency
uninstall/install.

## Relationship to OSW-EXP-080 activation GUI

The OSW-EXP-080 activation panel remains view-model driven and non-persistent and
is unchanged by this gate. Active candidate display is not deactivation
persistence; the deactivation GUI does not turn the activation GUI into a state
mutation surface.

## Relationship to OSW-EXP-083/084 discovery-refresh view-model and GUI

The discovery-refresh view-model and GUI remain view-model driven and
non-executing. The deactivation GUI does not alter discovery-refresh source
inclusion/exclusion behavior; deactivated candidates remain excluded or inactive by
policy.

## Relationship to explicit import GUI

File loading and preview do not imply activation or deactivation. Deactivation does
not delete imported JSON files. This gate changes no explicit import preview
history.

## Relationship to health panel and passive discovery

No passive discovery behavior change, no discovery service source edits, no
background refresh, and no startup refresh. The optional solver health panel keeps
its existing behavior.

## Relationship to CLI and export summary

No CLI behavior changes and no CLI deactivation command are added. The panel renders
an in-memory redacted summary only (from view-model data); it writes no files, adds
no clipboard integration, no shell/browser action, and no open-output-folder
action.

## Relationship to live optional validation issues

Issues `#6` through `#11` remain open. Deactivation is not live optional
validation. A deactivated state must not mark issues ready to close. Skipped-missing
remains skipped-missing, and prepared-machine validation remains a separate gate.

## Non-actions

This gate does not:

- implement runtime deactivation or deactivation persistence;
- delete manifest files;
- uninstall dependencies or solvers;
- mutate activation, discovery, or plugin-manager state;
- run discovery, validation, or solvers;
- install dependencies;
- import plugin packages, scan directories, or fetch network manifests;
- implement CLI behavior;
- write files, integrate the clipboard, or open a shell/browser/output folder;
- mutate issues, releases, tags, or assets;
- bump versions;
- make any validation-pass claim, validation-fail claim, issue-closure claim,
  bundled-solver claim, or certification claim.

Deactivation is not deletion. Deactivation is not uninstall. Deactivation is not a
validation failure. User-selected and plugin-provided manifests remain untrusted;
built-ins remain authoritative; historical validation evidence is retained;
skipped-missing optional validation remains neither pass nor failure, and issues
`#6` through `#11` stay open.

## Future gates

- `OSW-EXP-087_OPTIONAL_SOLVER_PLUGIN_MANIFEST_REACTIVATION_DESIGN`
- A future deactivation persistence gate (out of scope here).
- A future deactivation source/discovery-integration gate.
- `OSW-VALID` prepared-machine validation reuse.
