# Optional solver plugin manifest reactivation GUI implementation

## Status

Experimental PySide reactivation GUI surface implemented.

- View-model driven.
- No reactivation persistence.
- No automatic activation.
- No trust restoration.
- No file restore, no file rewrite, and no file deletion.
- No discovery execution.
- No validation execution.
- No solver execution.
- No dependency install and no dependency uninstall.
- No solver uninstall.
- No issue mutation and no release mutation.

This gate (OSW-EXP-089) implements a PySide review/control panel that renders the
pure OSW-EXP-088 reactivation view-model. It adds GUI source only; it does not
implement the product behavior of reactivating a manifest into persistent OSW
configuration or active candidate state.

## Purpose

Render reactivation readiness, reactivation state, candidates, acknowledgements,
blockers, diagnostics, stale-source/re-preview warnings, shared-stack warnings,
deactivation-history and evidence retention, trust/provenance badges, safety
guidance, and disabled/future action states for review only.

The panel lets a user inspect what a future reactivation persistence gate would
require (a deactivated candidate, acknowledgements, stale-source re-preview,
conflict/trust resolution) without automatically activating anything, restoring
trust, restoring/rewriting/deleting files, installing/uninstalling anything,
running discovery, validation, or solver execution.

## Public module and class names

- Module: `src/osw/gui/dialogs/optional_solver_plugin_manifest_reactivation_panel.py`
- Public class: `OptionalSolverPluginManifestReactivationPanel`
- Lazy package export: `OptionalSolverPluginManifestReactivationPanel` is exported
  from `osw.gui.dialogs` via the existing lazy `__getattr__` hook.

Constructor seams (dependency injection for testability):

- `view_model`: an `OptionalSolverPluginManifestReactivationViewModel` (defaults to
  `.unavailable()`).
- `acknowledgement_callback`: an optional pure callback that receives the
  widget-local acknowledgement map and returns a fresh view-model.
- `theme_tokens`: optional theme tokens.

## User flow

- Empty / no-deactivation-state view: reactivation unavailable,
  deactivated-required diagnostic, safety guidance, all unsafe actions
  disabled/future-only.
- Deactivated candidate review: deactivated candidates render with reactivation
  state, readiness, and blockers; untrusted sources are flagged.
- Reactivation-ready view: readiness `ready_non_persistent` is shown but nothing is
  persisted or activated.
- Blocked-acknowledgement view: missing required acknowledgements block readiness.
- Stale-source/re-preview-required view: a stale/missing source blocks until
  acknowledged; old preview data is not silently trusted.
- Shared-stack/conflict warning view: duplicate stack ids render with the
  built-ins-win policy.
- Future-activation-required view: a candidate routed back toward activation review.
- Active-candidate-future-gate view: a caller-supplied future-gate routing state.
- Reactivation-error view: a caller-supplied error state.

## Rendered sections

- Summary (readiness, state, counts, history/evidence-retained, honesty flags).
- Reactivation candidates (stack id, display name, source type, label, redacted
  reference, trust label, activation/deactivation/reactivation state, readiness,
  blockers, warnings, required acknowledgements, built-in relationship,
  shared-stack indicators, stale-source state, re-preview-required flag,
  deactivation history, historical evidence, redaction flag).
- Acknowledgements (id, label, required, satisfied, blocking, reason, related,
  warning).
- Diagnostics (severity, category, `OSPMG_REACTIVATION_*` code, message, source,
  stack id, suggested fix, blocker).
- Shared-stack/conflicts (stack id, built-in source, user/plugin source, active /
  deactivated / reactivation states, built-ins-win default, keeps-built-ins note,
  required future policy).
- Stale-source/re-preview (stale state, re-preview-required, redacted reference,
  not-silently-trusted, no-file-IO, no-file-restore, future-policy).
- Evidence and deactivation-history retention (history retained, evidence
  retained, not validation success, not validation failure reversal,
  skipped-missing remains, issue closure not implied, evidence not deleted).
- Trust/provenance (badges plus untrusted/authoritative/not-certification text).
- Action states (current/future/unavailable + disabled reasons).
- Safety guidance (boundary statements and blocked transitions).

## Action boundary

- Runtime reactivation is not implemented.
- Reactivation persistence is not implemented.
- Automatic activation is not performed.
- Trust restoration is not performed.
- File restore/rewrite/delete is not performed.
- Dependency install/uninstall is not performed.
- Solver uninstall is not performed.
- Discovery is not executed.
- Validation is not executed.
- Solver execution is not performed.
- Issue/release mutation is not performed.

Unsafe actions (`run_discovery`, `run_validation`, `install_dependency`,
`uninstall_dependency`, `uninstall_solver`, `execute_solver`, `close_issue`) are
always rendered as unavailable, disabled, and future-only. Future actions
(`request_reactivation`, `reactivate_candidate`, `route_to_activation_review`,
`export_redacted_summary`) render as disabled (future-only). The `acknowledge_*`
actions are widget-local and only become enabled when a pure acknowledgement
callback is injected; toggling them rebuilds a supplied view-model and persists
nothing.

## Trust and safety boundary

- User/plugin manifests are untrusted by default.
- Built-ins are authoritative by default.
- Trust label is not certification.
- Reactivation state is not validation evidence.
- Reactivation state is not validation success.
- Reactivation state is not validation failure reversal.
- Reactivation GUI is not automatic activation.
- Reactivation GUI is not trust restoration.
- Reactivation GUI is not install.
- Reactivation GUI is not solver execution.

## Testing strategy

- Injected view-models render every section (empty, rich, ready, blocked,
  stale-source, conflict, future-activation-required).
- Offscreen Qt subprocess tests (`QT_QPA_PLATFORM=offscreen`) with a PySide6
  import guard so base unit tests never require GUI extras.
- Disabled/future action-state assertions for unsafe actions.
- No-side-effect assertions: source scan rejects subprocess/discovery/
  file-write/delete/uninstall/clipboard/browser paths; the reactivation view-model
  remains free of PySide/Qt imports; the acknowledgement callback is widget-local
  and a panel without a callback ignores toggles.

## Relationship to OSW-EXP-087 design

The panel is a GUI surface over the OSW-EXP-087 reactivation contract. The runtime
reactivation behavior and persistence in that design remain future-gated.

## Relationship to OSW-EXP-088 view-model

The panel consumes the OSW-EXP-088 pure reactivation view-model. That view-model
remains pure: it gains no PySide/Qt imports, no file IO, no file
restore/rewrite/delete, no reactivation persistence, no automatic activation, no
trust restoration, no plugin import, no directory scan, no network fetch, no
discovery execution, no validation, no solver execution, and no dependency
install/uninstall.

## Relationship to OSW-EXP-085/086 deactivation view-model and GUI

The OSW-EXP-086 deactivation panel remains view-model driven and non-mutating and
is unchanged by this gate. Deactivated candidate display is not reactivation
persistence; the reactivation GUI does not turn the deactivation GUI into a state
mutation surface.

## Relationship to OSW-EXP-079/080 activation view-model and GUI

Reactivation routes back through future activation review. The OSW-EXP-080
activation panel remains view-model driven and non-persistent; this gate mutates
no activation state and creates no active candidates.

## Relationship to OSW-EXP-083/084 discovery-refresh view-model and GUI

The discovery-refresh view-model and GUI remain view-model driven and
non-executing. The reactivation GUI does not alter discovery-refresh source
inclusion/exclusion behavior; reactivation-ready candidates do not automatically
become discovery inputs.

## Relationship to explicit import GUI

File loading and preview do not imply activation, deactivation, or reactivation.
Reactivation does not restore, rewrite, or delete imported JSON files. If
stale-source re-preview is required, it is a future explicit user action through
the explicit import boundary. This gate changes no explicit import preview history.

## Relationship to health panel and passive discovery

No passive discovery behavior change, no discovery service source edits, no
background refresh, and no startup refresh. The optional solver health panel keeps
its existing behavior.

## Relationship to CLI and export summary

No CLI behavior changes and no CLI reactivation command are added. The panel
renders an in-memory redacted summary only (from view-model data); it writes no
files, adds no clipboard integration, no shell/browser action, and no
open-output-folder action.

## Relationship to live optional validation issues

Issues `#6` through `#11` remain open. Reactivation is not live optional
validation. A reactivation-ready or future-activation-required state must not mark
issues ready to close. Skipped-missing remains skipped-missing, and
prepared-machine validation remains a separate gate.

## Non-actions

This gate does not:

- implement runtime reactivation or reactivation persistence;
- automatically activate candidates or restore trust;
- restore, rewrite, or delete files;
- install or uninstall dependencies, or uninstall solvers;
- mutate activation, deactivation, discovery, or plugin-manager state;
- run discovery, validation, or solvers;
- import plugin packages, scan directories, or fetch network manifests;
- implement CLI behavior;
- write files, integrate the clipboard, or open a shell/browser/output folder;
- mutate issues, releases, tags, or assets;
- bump versions;
- make any validation-pass claim, validation-failure-reversal claim,
  issue-closure claim, bundled-solver claim, or certification claim.

Reactivation is not automatic activation. Reactivation is not trust restoration.
Reactivation is not validation. User-selected and plugin-provided manifests remain
untrusted; built-ins remain authoritative; deactivation history and historical
validation evidence are retained; skipped-missing optional validation remains
neither pass nor failure, and issues `#6` through `#11` stay open.

## Future gates

- `OSW-EXP-090_OPTIONAL_SOLVER_PLUGIN_MANIFEST_STATE_PERSISTENCE_DESIGN`
- `OSW-EXP-091_OPTIONAL_SOLVER_PLUGIN_MANIFEST_STATE_EXPORT_SUMMARY_DESIGN`
- A future reactivation source/persistence-integration gate.
- `OSW-VALID` prepared-machine validation reuse.
