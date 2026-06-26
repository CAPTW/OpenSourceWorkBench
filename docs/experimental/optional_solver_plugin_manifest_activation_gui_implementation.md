# Optional solver plugin manifest activation GUI implementation

## Status

Experimental PySide activation GUI surface implemented.

This gate (OSW-EXP-080) adds a view-model-driven PySide review/control panel over
the OSW-EXP-079 pure activation view-model.

Status boundaries:

- view-model driven
- no activation persistence
- no plugin package import
- no directory scan
- no network fetch
- no discovery execution
- no validation execution
- no solver execution
- no dependency installation
- no issue mutation
- no release mutation
- no tag mutation
- no asset mutation

## Purpose

Render activation readiness, acknowledgements, blockers, diagnostics,
conflicts, trust/provenance badges, and disabled/future action states for
optional solver plugin manifests, so a user can review what activation would
require — without activating anything.

## Public module and class names

Module:

`src/osw/gui/dialogs/optional_solver_plugin_manifest_activation_panel.py`

Public class:

- `OptionalSolverPluginManifestActivationPanel`

It is also exposed through the lazy `osw.gui.dialogs` package export
(`OptionalSolverPluginManifestActivationPanel`).

## User flow

- empty / no-preview state: the panel shows activation unavailable before
  preview, surfaces the preview-required diagnostic, and shows safety guidance.
- candidate review: each previewed manifest source is shown as an activation
  candidate with its readiness, blockers, warnings, and required acknowledgements.
- acknowledgement review: required acknowledgements are listed with
  satisfied/blocking state.
- blocked/readiness states: schema, conflict, unsafe-claim, and
  missing-acknowledgement candidates render as blocked.
- active-candidate display: when the caller supplies active candidate state, the
  panel renders it as `active_candidate` (still not validation evidence).
- deactivated display: when the caller supplies deactivated state, the panel
  renders it as `deactivated`.

Acknowledgement interaction is widget-local and non-persistent: when a pure
acknowledgement callback is injected, acknowledge actions toggle a widget-local
acknowledgement map and rebuild the supplied view-model. Without a callback, the
panel is display-only.

## Rendered sections

- summary (counts, readiness tallies, honesty flags)
- candidates
- acknowledgements
- diagnostics
- conflicts
- trust/provenance
- action states
- safety guidance

## Action boundary

- activation persistence is not implemented
- discovery is not executed
- validation is not executed
- install is not executed
- solver execution is not performed
- issue/release mutation is not performed

Every action except the widget-local acknowledge toggles is disabled/future-only:
`request_activation`, `activate_candidate`, `deactivate_candidate`,
`run_discovery_with_activated_manifests`, `run_validation`,
`install_dependency`, `execute_solver`, `close_issue`, and
`export_redacted_summary` are all disabled in this gate.

## Trust and safety boundary

- user-selected and plugin-provided manifests are untrusted by default
- trust label is not certification
- active candidate is not validation evidence
- activation GUI is not install
- activation GUI is not solver execution

## Testing strategy

- injected view-models built from caller-supplied activation candidates
- injected pure acknowledgement callback for widget-local toggles
- no real discovery, validation, install, or solver execution
- disabled/future action-state assertions
- source-scan and AST import checks for no-side-effect boundaries
- offscreen Qt subprocess tests guarded on PySide6 availability

## Relationship to OSW-EXP-078 design

The panel implements a GUI surface for the activation contract designed in
OSW-EXP-078, preserving its preview-only, untrusted-by-default, and
activation-is-not-validation boundaries.

## Relationship to OSW-EXP-079 view-model

The panel consumes `OptionalSolverPluginManifestActivationViewModel` records and
does not add PySide/Qt imports, file IO, activation persistence, plugin import,
discovery execution, validation execution, solver execution, or dependency
installation to the view-model. The view-model remains pure.

## Relationship to OSW-EXP-077 explicit import GUI

The OSW-EXP-077 explicit import panel remains preview-only and unchanged. File
loading and preview do not imply activation; the activation panel is a separate
surface.

## Relationship to health panel and discovery refresh

The activation panel does not alter optional solver health panel discovery.
Activated candidate display is not health validation. Discovery refresh using
activated manifests remains a future separate gate.

## Relationship to CLI and export summary

No CLI behavior changes and no CLI activation command are added. The panel can
render an in-memory redacted summary (`redacted_summary_text`) derived from
view-model data only; it writes no files, touches no clipboard, and opens no
shell, browser, or output folder.

## Non-actions

This gate does not:

- persist activation
- import plugin packages
- scan directories
- fetch network manifests
- run discovery
- run validation
- execute solvers
- install dependencies
- mutate issues, releases, tags, or assets
- bump versions
- make any validation-pass claim, issue-closure claim, bundled-solver claim, or
  certification claim

User-selected and plugin-provided manifests remain untrusted; skipped-missing
optional validation remains neither pass nor failure, and issues `#6` through
`#11` stay open.

## Deactivation design follow-up

[Optional solver plugin manifest deactivation design](optional_solver_plugin_manifest_deactivation_design.md)
(OSW-EXP-081) defines the future, design-only deactivation contract for active
candidates. Deactivation is explicit, acknowledged, provenance-preserving, and
non-deleting/non-uninstalling/non-executing; this GUI gate renders the
`deactivated` state only when supplied by the view-model and adds no
deactivation buttons, callbacks, persistence, or state mutation.

## Future gates

- `OSW-EXP-081_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DEACTIVATION_DESIGN`
- `OSW-EXP-082_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DISCOVERY_REFRESH_INTEGRATION_DESIGN`
- `OSW-VALID` prepared-machine validation reuse
