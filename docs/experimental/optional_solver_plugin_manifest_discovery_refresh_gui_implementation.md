# Optional solver plugin manifest discovery refresh GUI implementation

## Status

Experimental PySide discovery-refresh GUI surface implemented.

- View-model driven.
- No runtime discovery integration.
- No passive discovery behavior change.
- No discovery execution.
- No validation execution.
- No solver execution.
- No dependency install.
- No activation persistence and no deactivation persistence.
- No issue mutation and no release mutation.

This gate (OSW-EXP-084) implements a PySide review/control panel that renders the
pure OSW-EXP-083 discovery-refresh view-model. It adds GUI source only; it does
not implement the product behavior of "running discovery with activated
manifests".

## Purpose

Render discovery-refresh readiness, refresh modes, refresh state, discovery
source inclusion/exclusion, deactivated candidates, acknowledgements, blockers,
diagnostics, conflicts, unsafe claims, trust/provenance badges, safety guidance,
and disabled/future action states for review only.

The panel lets a user inspect what a future discovery-refresh integration would
require (active candidates, acknowledgements, conflict/trust resolution) without
running discovery, validation, installation, or solver execution.

## Public module and class names

- Module: `src/osw/gui/dialogs/optional_solver_plugin_manifest_discovery_refresh_panel.py`
- Public class: `OptionalSolverPluginManifestDiscoveryRefreshPanel`
- Lazy package export: `OptionalSolverPluginManifestDiscoveryRefreshPanel` is
  exported from `osw.gui.dialogs` via the existing lazy `__getattr__` hook.

Constructor seams (dependency injection for testability):

- `view_model`: an `OptionalSolverPluginManifestDiscoveryRefreshViewModel`
  (defaults to `.unavailable()`).
- `acknowledgement_callback`: an optional pure callback that receives the
  widget-local acknowledgement map and returns a fresh view-model.
- `theme_tokens`: optional theme tokens.

## User flow

- Empty / no-activation-state view: refresh unavailable, active-candidate-required
  diagnostic, safety guidance, all unsafe actions disabled/future-only.
- Built-in-only view: built-in sources render as included and authoritative.
- Active candidate review: active candidates render with inclusion/exclusion and
  blockers; untrusted sources are flagged.
- Deactivated candidate exclusion/inactive-history view: deactivated candidates
  render as excluded by default and are not validation failures.
- Conflict-blocked view: duplicate stack ids render as conflict-blocked with the
  built-ins-win policy.
- Unsafe-claim-blocked view: unsafe manifest claims render as blocked.
- Refresh-ready display: readiness `ready_preview_only` is shown but is not
  validation evidence.
- Result-preview display: caller-supplied result-preview readiness is shown but is
  not validation evidence.

## Rendered sections

- Summary (mode, state, readiness, counts, honesty flags).
- Refresh mode/state (in the summary header and per-source rows).
- Discovery sources (stack id, display name, source type, label, redacted
  reference, trust label, discovery state, activation state, refresh mode,
  inclusion/exclusion, exclusion reason, readiness, blockers, warnings, required
  acknowledgements, unsafe-claim indicators, built-in relationship, redaction
  flag).
- Deactivated candidates (excluded by default; not validation failure; not
  uninstall; not file deletion; redacted reference).
- Acknowledgements (id, label, required, satisfied, blocking, reason, related,
  warning).
- Diagnostics (severity, category, `OSPMG_DISCOVERY_REFRESH_*` code, message,
  source, stack id, suggested fix, blocker).
- Conflicts (stack id, built-in source, user/plugin source, policy,
  built-ins-win default, refresh state, required future policy).
- Unsafe claims (stack id, source label, trust label, indicators, blocked,
  reason).
- Trust/provenance (badges plus untrusted/authoritative/not-certification text).
- Action states (current/future/unavailable + disabled reasons).
- Safety guidance (boundary statements and blocked transitions).

## Action boundary

- Runtime discovery integration is not implemented.
- Passive discovery behavior is not changed.
- Activation/deactivation persistence is not implemented.
- Discovery is not executed.
- Validation is not executed.
- Install is not executed.
- Solver execution is not performed.
- Issue/release mutation is not performed.

Unsafe actions (`run_discovery`, `run_validation`, `install_dependency`,
`execute_solver`, `close_issue`) are always rendered as unavailable, disabled, and
future-only. Future actions (`request_refresh`, `built_in_only_refresh`,
`include_activated_candidates`, `exclude_deactivated_candidates`,
`export_redacted_summary`) render as available-but-disabled (future-only). The
`acknowledge_*` actions are widget-local and only become enabled when a pure
acknowledgement callback is injected; toggling them rebuilds a supplied view-model
and persists nothing.

## Trust and safety boundary

- User/plugin manifests are untrusted by default.
- Built-ins are authoritative by default.
- Trust label is not certification.
- Discovery inclusion is not validation evidence.
- Refresh-ready is not validation evidence.
- Discovery-refresh GUI is not install.
- Discovery-refresh GUI is not solver execution.

## Testing strategy

- Injected view-models render every section (empty, built-in-only, rich mix,
  blocked, ready, result-preview).
- Offscreen Qt subprocess tests (`QT_QPA_PLATFORM=offscreen`) with a PySide6
  import guard so base unit tests never require GUI extras.
- Disabled/future action-state assertions for unsafe actions.
- No-side-effect assertions: source scan rejects subprocess/discovery/file-write/
  clipboard/browser paths; the discovery-refresh view-model remains free of
  PySide/Qt imports; the acknowledgement callback is widget-local and a panel
  without a callback ignores toggles.

## Relationship to OSW-EXP-082 design

The panel is a GUI surface over the OSW-EXP-082 discovery-refresh integration
contract. The runtime integration behavior in that design remains future-gated.

## Relationship to OSW-EXP-083 view-model

The panel consumes the OSW-EXP-083 pure discovery-refresh view-model. That
view-model remains pure: it gains no PySide/Qt imports, no file IO, no runtime
discovery integration, no passive discovery behavior change, no
activation/deactivation persistence, no plugin import, no directory scan, no
network fetch, no validation, no solver execution, and no dependency installation.

## Relationship to OSW-EXP-080 activation GUI

The OSW-EXP-080 activation panel remains view-model driven and non-persistent and
is unchanged by this gate. Active candidate display is not discovery evidence; the
discovery-refresh GUI does not turn the activation GUI into a discovery runner.

## Relationship to OSW-EXP-081 deactivation design

Deactivated candidates remain excluded or inactive by policy. Deactivation is not
deletion, uninstall, validation failure, or discovery execution. This gate
implements no deactivation view-model extension or GUI deactivation behavior.

## Relationship to health panel and passive discovery

No passive discovery behavior change, no discovery service source edits, no
background refresh, and no startup refresh. The optional solver health panel keeps
its existing behavior. Activated candidates are kept separate from
built-in/passive discovery data.

## Relationship to CLI and export summary

No CLI behavior changes and no CLI discovery-refresh command are added. The panel
renders an in-memory redacted summary only (from view-model data); it writes no
files, adds no clipboard integration, no shell/browser action, and no
open-output-folder action.

## Relationship to live optional validation issues

Issues `#6` through `#11` remain open. Discovery refresh is not live optional
validation. Refresh-ready or result-preview state must not mark issues ready to
close. Skipped-missing remains skipped-missing, and prepared-machine validation
remains a separate gate.

## Non-actions

This gate does not:

- implement runtime discovery integration;
- change passive discovery behavior;
- run discovery, validation, or solvers;
- install dependencies;
- import plugin packages, scan directories, or fetch network manifests;
- persist activation or deactivation state;
- implement CLI behavior;
- write files, integrate the clipboard, or open a shell/browser/output folder;
- mutate issues, releases, tags, or assets;
- bump versions;
- make any validation-pass claim, issue-closure claim, bundled-solver claim, or
  certification claim.

User-selected and plugin-provided manifests remain untrusted; built-ins remain
authoritative; skipped-missing optional validation remains neither pass nor
failure, and issues `#6` through `#11` stay open.

## Future gates

- `OSW-EXP-085_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DEACTIVATION_VIEWMODEL_EXTENSION`
- `OSW-EXP-086_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DEACTIVATION_GUI_IMPLEMENTATION`
- A future discovery-refresh source-integration gate (runtime integration).
- `OSW-VALID` prepared-machine validation reuse.
