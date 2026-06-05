# First GUI Walkthrough

The GUI is optional and requires PySide6. Use this walkthrough to understand the
layout before adding optional solver stacks.

## Install GUI Extra

From the repository root:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[gui]"
```

On Linux/macOS:

```bash
.venv/bin/python -m pip install -e ".[gui]"
```

## Launch

```powershell
.venv\Scripts\python.exe -m osw.cli gui
```

Linux/macOS:

```bash
.venv/bin/python -m osw.cli gui
```

If PySide6 is missing, the command should report an optional dependency
diagnostic. Missing PySide6 is not a base CLI failure.

## Layout

Use the committed screenshots as a visual map:

| Theme | Screenshot |
| --- | --- |
| Dark | ![OpenSolver Workbench dark theme](../assets/screenshots/osw_dark.png) |
| Light | ![OpenSolver Workbench light theme](../assets/screenshots/osw_light.png) |
| System | ![OpenSolver Workbench system theme](../assets/screenshots/osw_system.png) |

Main areas:
- project tree: project items, imported files, and workflow objects
- viewer: preview/result/report surfaces
- properties: selected item metadata and validation messages
- run monitor: diagnostics and prepared-command state
- report/result panels: summaries, tables, field metadata, and report status

The GUI may prepare cases, preview commands, validate inputs, and inspect
results. It must not directly run external solver subprocesses from a button
path in v0.1.

## Plugin Manager Receipts

Open **Plugins > Plugin Manager** to inspect local plugin state.

The plugin table separates discovered plugin metadata from managed install
state:
- source kind
- install status
- managed-root status
- receipt presence
- diagnostic count

For a plugin installed through the local folder or ZIP flow, select the row and
open the **Receipt** tab. It shows the plugin ID, source path/kind, installed
path, installed timestamp, manifest path, file count when recorded, uninstall
eligibility, and a raw receipt JSON preview.

Open the **Quarantine** tab to inspect rejected local install attempts. It lists
the count, latest reasons, source path/kind, quarantine path when a ZIP copy was
retained, diagnostics, and raw record JSON.

Open the **Safety** tab before uninstalling. It repeats the boundaries:
- local folder/ZIP install only
- no plugin code execution during install or discovery
- no remote/network plugin install
- no dependency auto-install
- no plugin signing or marketplace
- uninstall is restricted to managed-root receipts

Built-in, entry-point, and unmanaged local plugins do not have install receipts,
so the uninstall button remains disabled for those rows.

## Headless Environments

In CI, remote shells, or machines without a desktop session, GUI launch or
visual rendering may be skipped. Use screenshots and CLI tutorials for
headless onboarding.

## Limitations

- GUI availability does not imply solver availability.
- PyVista field rendering remains optional.
- OSW is not an industrial-certified GUI solver platform.
