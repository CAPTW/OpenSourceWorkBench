# Optional solver GUI discovery refresh implementation

## Status

Experimental GUI passive refresh implemented.

This gate adds:

- explicit user action only
- injected refresh runner support for tests and future orchestration
- default built-in passive discovery runner
- refresh status and error display
- atomic health panel view-model replacement after successful refresh

This gate does not add:

- no automatic startup refresh
- no background worker implementation
- no threading implementation
- no active smoke validation
- no solver execution
- no external solver command execution
- no dependency installation
- no solver installation
- no issue mutation
- no release mutation

## Package path / GUI class

Package path:

- `src/osw/gui/dialogs/optional_solver_health_panel.py`

Public class:

- `OptionalSolverHealthPanel`

## Relationship to refresh view-model

The panel consumes
[Optional solver GUI discovery refresh view-model](optional_solver_gui_discovery_refresh_viewmodel.md)
helpers for request planning and result application.

The GUI does not mutate card rows directly. A successful refresh applies
supplied passive discovery reports through the pure helper and swaps the
accepted `OptionalSolverHealthPanelViewModel` atomically.

The panel swaps the accepted `OptionalSolverHealthPanelViewModel` atomically.

## Refresh action behavior

`Refresh Passive Discovery` is a current GUI action.

The action is:

- explicit user action only
- enabled when an injected runner is configured or the default built-in
  passive runner is allowed
- disabled with a clear reason when no runner is configured and the default
  runner is disabled
- synchronous in this implementation
- not run during panel construction

Refresh output is setup/health UX evidence only. It is not validation evidence.

## Injected runner and default passive discovery runner

Tests and future orchestration can inject a runner. The runner receives an
`OptionalSolverRefreshRequest` and returns either:

- `OptionalSolverRefreshResult`
- `OptionalSolverDiscoveryReport`
- `None` for a canceled/no-op refresh

When no runner is injected and the default runner is allowed, the panel calls
the built-in passive discovery service for built-in manifests. That service is
limited to:

- `shutil.which` executable presence checks
- `importlib.util.find_spec` Python package presence checks
- `importlib.metadata.version` package version metadata
- environment variable presence checks with values hidden

It does not run solver commands, active smoke checks, installers, plugin
loading, issue APIs, or release APIs.

## Status/error display

The panel exposes deterministic status and error text:

- refresh idle
- passive refresh running
- passive refresh completed
- passive refresh failed
- passive refresh canceled
- stale refresh ignored

The test accessors expose:

- `refresh_action_enabled()`
- `refresh_action_reason()`
- `refresh_status_text()`
- `refresh_error_text()`
- `refresh_request_id()`
- `refresh_result_summary_text()`
- `trigger_refresh_for_test()`
- `set_refresh_runner_for_test()`
- `refresh_runner_call_count()`
- `current_stack_card_texts()`
- `current_summary_text()`

## View-model replacement behavior

Successful refresh builds and accepts a new health panel view-model. Failed,
canceled, or stale refresh preserves the current view-model.

Failed, canceled, or stale refresh preserves the current view-model.

Selection and filters are passed through the refresh apply helper, which
preserves selected stack id and filters where safe.

## Export summary interaction

Export summary renders the currently accepted view-model.

- export before refresh uses the original view-model
- export after successful refresh uses the refreshed view-model
- failed, canceled, or stale refresh keeps export bound to the previous
  accepted view-model
- export remains not validation evidence

## Privacy/redaction behavior

Refresh keeps the existing redaction defaults:

- paths are redacted by default
- environment values are never displayed
- full path display is not enabled by this GUI action
- no telemetry is collected
- exported summaries inherit the accepted redacted view-model

## Safety boundary

- no automatic startup refresh
- no active smoke
- no solver execution
- no external solver command execution
- no subprocess usage for solver operations
- no install action
- no dependency installation
- no issue mutation
- no release mutation
- refresh is not validation evidence
- issue closure remains unavailable from the panel
- external solvers are not bundled
- no certification claim

## Relationship to #6~#11

The panel can refresh passive setup state for optional solver issues:

- Gmsh: `#6`
- GNU Octave: `#7`
- CalculiX `ccx`: `#8`
- OpenFOAM: `#9`
- CoolProp / Cantera: `#10`
- PyVista / meshio: `#11`

Issues `#6` through `#11` remain open. `skipped-missing` remains not pass
evidence. Refresh output cannot close issues.

Skipped-missing remains not pass evidence.

## Future gates

- `OSW-EXP-069_OPTIONAL_SOLVER_PLUGIN_MANIFEST_LOADING_DESIGN` - completed as
  a design-only source/trust contract in
  [Optional solver plugin manifest loading design](optional_solver_plugin_manifest_loading_design.md).
- `OSW-VALID` prepared-machine validation reuse

## Plugin manifest loading design follow-up

[Optional solver plugin manifest loading design](optional_solver_plugin_manifest_loading_design.md)
defines how future accepted plugin-provided manifests can be labeled and
handed to passive discovery without executing plugin code. A later refresh
implementation may refresh over accepted manifest sets, but this design adds
no plugin loader, filesystem scan, network fetch, marketplace integration,
active smoke validation, solver execution, dependency installation, issue
mutation, release mutation, validation-pass claim, issue-closure claim,
bundled-solver claim, or certification claim.

## Plugin manifest loader model follow-up

[Optional solver plugin manifest loader model](optional_solver_plugin_manifest_loader_model.md)
implements a data-only loader for explicit manifest documents. The current GUI
refresh action still refreshes only over its configured manifest set and does
not scan plugin directories, import plugin packages, fetch network manifests,
or treat plugin manifest loading as validation evidence.

## Plugin manifest CLI preview follow-up

[Optional solver plugin manifest CLI preview](optional_solver_plugin_manifest_cli_preview.md)
adds an explicit JSON command for previewing plugin manifest loader reports.
The current GUI refresh action still does not consume those files, scan plugin
directories, import plugin packages, fetch network manifests, execute solvers,
install dependencies, mutate issues, or turn manifest presence into validation
evidence.

## Plugin manifest GUI design follow-up

[Optional solver plugin manifest GUI design](optional_solver_plugin_manifest_gui_design.md)
defines future GUI review of plugin manifest loader reports before any accepted
manifest activation model exists. The current refresh action remains built-in
or caller-supplied only and does not auto-refresh from plugin preview files,
scan plugin directories, import plugin packages, fetch network manifests,
execute solvers, install dependencies, mutate issues, or create validation
evidence.
