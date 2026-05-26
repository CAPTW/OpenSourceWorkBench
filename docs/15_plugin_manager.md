# Plugin Manager

`OSW-FUNC-004_PLUGIN_MANAGER_DIALOG_BINDING` binds the completed GUI shell to
the manifest-first plugin registry and health checks.

## Purpose

The Plugin Manager lets users inspect plugin manifests, enable or disable
plugins, review dependency and executable diagnostics, and configure executable
paths for future solver/script adapters.

This step is a GUI binding only. It does not implement plugin installation,
solver adapters, external solver execution, or plugin code loading.

## Dialog

The dialog lives at `osw.gui.dialogs.plugin_manager_dialog.PluginManagerDialog`.

It shows:

- discovered manifest rows
- enabled/disabled state
- health status
- manifest JSON
- capabilities
- Python dependency diagnostics
- executable diagnostics
- discovery diagnostics, including invalid manifests and duplicate IDs

Discovery reads manifest files only. Entry point metadata can be listed without
loading entry point objects.

## Executable Paths

Executable path configuration is handled by `ExecutablePathDialog` and
`PluginStateStore`.

The dialog can store paths for manifest `executable_names`, then health checks
can resolve those paths through the same `ExecutablePathRegistry` semantics used
by the backend runner. It does not run executables and does not call
`--version`.

## State

`osw.plugins.state.PluginStateStore` stores:

- disabled plugin IDs
- configured executable paths

The store is JSON-backed when a path is supplied and in-memory otherwise. It is
independent of PySide6 so unit tests and CLI paths can use it without GUI
extras.

## Main Window Binding

The completed GUI shell now has safe Plugins menu actions:

- Plugin Manager
- Refresh Plugins
- Plugin Health Check

The right inspector's Plugins section can show registry-backed rows when
manifests are discovered. If no registry data is available, it retains the
visual demo rows from the frozen GUI baseline.

## Security Rules

- Manifest validation does not execute plugin code.
- Local plugin discovery reads manifest data only.
- Entry point loading is explicit and is not used by ordinary dialog refresh.
- Health checks do not run solver executables.
- The GUI does not call `ExternalCommandRunner`.
- Install from folder/zip remains deferred.
- No network plugin store is implemented.

## Known Limitations

- Enable/disable state is local UI state only; solver adapters are not wired.
- Executable path browsing is a path configuration helper, not an executable
  validation run.
- Entry point metadata rows are informational until a future explicit loading
  workflow is designed.
- No plugin install/uninstall workflow is present in this step.

## Next Step

Next functional step: `OSW-FUNC-005_MESH_IMPORT_BRIDGE`.
