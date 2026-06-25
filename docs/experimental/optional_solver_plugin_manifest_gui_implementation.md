# Optional solver plugin manifest GUI implementation

## Status

Experimental PySide display component implemented.

This gate adds a view-model driven panel for already-built optional solver
plugin manifest GUI preview records.

Status boundaries:

- view-model driven
- no file dialog
- no plugin loading
- no plugin activation
- no solver execution
- no dependency installation

## Package path and public class

Package path:

`src/osw/gui/dialogs/optional_solver_plugin_manifest_panel.py`

Public class:

- `OptionalSolverPluginManifestPanel`

The class is also exposed through the lazy `osw.gui.dialogs` package export.

## Relationship to plugin manifest GUI view-model

The panel consumes an already-built
`OptionalSolverPluginManifestGuiViewModel`.

It does not parse JSON, load manifest files, call the plugin manifest loader,
open file dialogs, scan directories, import plugin packages, fetch network
manifests, run discovery, execute solvers, install dependencies, mutate issues,
or mutate releases.

## Rendered sections

The panel renders:

- summary header
- accepted manifests table
- rejected manifests table
- conflict table
- diagnostics table
- trust/source labels panel
- safety/policy guidance panel
- disabled action-state footer

Focused GUI tests cover deterministic text accessors for each section.

## Accepted/rejected/conflict display

Accepted manifest rows show stack id, display name, source type, trust label,
related issue, support status, capabilities summary, and a not-validation
evidence notice.

Rejected manifest rows show stack id, source reference, trust label, rejection
reason, diagnostics, suggested fix, and unsafe-claim indicators.

Conflict rows show duplicate stack id, winning source, rejected source, loader
message, built-ins-win policy, and plugin-override-disabled policy.

## Diagnostics display

Diagnostics rows show severity, category, code, message, source reference,
stack id, and suggested fix.

Diagnostics are display records from the supplied view-model. The widget does
not run loader validation or discovery.

The component does not run loader validation or discovery.

## Trust/source labels

The trust panel lists source type, trust label, source reference, and warning
text from the view-model trust badges.

It also states:

- third-party/plugin manifests are not trusted by default
- trust label is not certification

## Safety/action boundary

The safety panel and action footer state:

- no plugin code execution
- no file loading
- no directory scan
- no network fetch
- no solver execution
- no install action
- no issue closure action

The action footer renders all current plugin-manifest preview actions as
disabled or future/display-only placeholders:

- choose explicit JSON files
- activate manifest
- run discovery with plugin manifests
- run validation
- install solver
- close issue

No button activates manifests, runs discovery, executes validation, installs
solvers, or mutates issues.

## Relationship to CLI preview

The panel displays the same accepted, rejected, conflict, diagnostic, source,
and trust semantics produced by the loader model and shown by
`optional-solver-plugin-manifest-preview`.

The CLI preview remains the automation-oriented surface. This GUI component is
review-focused and consumes the pure GUI view-model.

## Relationship to health panel

This component is separate from the optional solver health panel.

It does not activate plugin manifests for health checks, and the health panel
discovery refresh remains built-in/passive unless a later gate defines explicit
plugin manifest activation and discovery semantics.

## Future gates

- `OSW-EXP-075_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPLICIT_IMPORT_GUI_DESIGN`
- `OSW-EXP-076_OPTIONAL_SOLVER_PLUGIN_MANIFEST_ACTIVATION_DESIGN`
- `OSW-VALID` prepared-machine validation reuse
