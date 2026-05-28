# OpenSolver Workbench UI Completion Summary

This document freezes the completed OpenSolver Workbench visual shell as the
local baseline for future functional integration. Do not rerun the pixel
implementation queue or replace this GUI with a generic skeleton.

## Completed UI Steps

- UI-000_REFERENCE_SPEC_DOCS
- UI-001_THEME_MANAGER
- UI-002_MAIN_SHELL_LAYOUT
- UI-003_LEFT_PROJECT_TREE
- UI-004_TOP_TOOLBAR_AND_STEPPER
- UI-005_CENTRAL_VIEWPORT_MOCK
- UI-006_RUN_MONITOR_AND_CHARTS
- UI-007_RIGHT_PROPERTIES_PANEL
- UI-008_REPORT_PREVIEW_AND_STATUS_BAR
- UI-009_VISUAL_QA_AND_SCREENSHOT_CAPTURE
- UI-010_FINAL_POLISH_PASS

The queue state is complete in `.codex/ui_queue_state.json`.

## Final GUI Capabilities

The baseline GUI is a PySide6 visual shell for the `HeatSink_Flow` Run screen.
It includes:

- top title, toolbar, utility actions, and workflow stepper
- left `HeatSink_Flow` project tree with filter/footer
- central QPainter mock simulation viewport with legend, mesh overlay,
  orientation cube, axis triad, and scale bar
- bottom run monitor with log, residuals, warnings/progress, and Octave/MATLAB
  figure mock panels
- right inspector with properties tabs, material, boundary conditions, solver
  settings, plugins, and report preview
- compact status bar with solver, memory, cores, and readiness indicators
- visual QA screenshot capture and comparison utilities

The GUI is mock/preview oriented. It must not directly execute external solver,
MATLAB/Octave, OpenFOAM, CalculiX, Gmsh, report generation, or file-export
subprocess behavior from button paths.

## Theme Behavior

The GUI supports:

- Dark
- Light
- System

Dark is the reference/default visual mode. Light and System preserve the same
layout and mock data. System stores `system` and resolves safely through the
theme manager.

The theme system is documented in `docs/ui/theme_system.md` and implemented in:

- `src/osw/gui/theme_tokens.py`
- `src/osw/gui/theme.py`
- `src/osw/gui/widgets/theme_selector.py`
- `src/osw/gui/dialogs/preferences_dialog.py`

## Visual QA Artifact Policy

Generated visual artifacts belong under `artifacts/ui/` and are ignored by git.
Do not commit generated screenshots or diffs unless a future prompt explicitly
promotes a file into an approved golden/reference path.

The approved reference image is:

```text
docs/ui/reference/osw_run_screen.png
```

The root-level `GUI.png`, if present, must remain untouched and must not be
committed from the repository root.

## How To Run The GUI

Use the repo-local GUI environment when available:

```powershell
.venv\Scripts\python.exe -m osw.cli gui
```

If the GUI environment is missing, recreate it:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.venv\Scripts\python.exe -m pip install -e ".[gui]"
```

## How To Capture Screenshots

Capture the current Dark baseline:

```powershell
.venv\Scripts\python.exe tools\ui\capture_main_window.py --theme dark --out artifacts\ui\osw_dark_after.png --offscreen --width 2048 --height 1152
```

Capture all themes manually:

```powershell
.venv\Scripts\python.exe tools\ui\capture_main_window.py --theme dark --out artifacts\ui\osw_dark.png --offscreen --width 2048 --height 1152
.venv\Scripts\python.exe tools\ui\capture_main_window.py --theme light --out artifacts\ui\osw_light.png --offscreen --width 2048 --height 1152
.venv\Scripts\python.exe tools\ui\capture_main_window.py --theme system --out artifacts\ui\osw_system.png --offscreen --width 2048 --height 1152
```

Compare Dark against the reference:

```powershell
.venv\Scripts\python.exe tools\ui\compare_reference.py --reference docs\ui\reference\osw_run_screen.png --candidate artifacts\ui\osw_dark_after.png --resize-candidate --out-json artifacts\ui\osw_dark_after_compare.json --out-diff artifacts\ui\osw_dark_after_diff.png
```

## Known Remaining Visual Mismatches

- The central heat sink remains a QPainter mock, not a full 3D/PyVista result.
- Toolbar icons are simplified glyphs and text buttons.
- The report preview sits within the right panel scroll area and may be partly
  below the first viewport depending on height.
- Pixel comparison remains advisory because the implementation uses real Qt
  widgets and a deterministic mock viewport rather than screenshot reuse.

## What Not To Rerun

Do not rerun or recreate:

- UI-000 through UI-010
- OSW-AUTO-000 bootstrap
- OSW-AUTO-004_GUI_SKELETON

The completed GUI is now the baseline. Future prompts must integrate into it
rather than replacing it.

## Recommended Next Functional Implementation Step

The next work should connect this completed visual shell to real data models in
this order:

1. ProjectSchema / UnitSystem / MaterialDB
2. Plugin manifest and discovery
3. ExternalCommandRunner / diagnostics
4. Project tree binding to ProjectSchema
5. Properties panel binding to material / boundary / solver config models
6. Run monitor binding to Runner logs
7. ResultDataset / FigureDataset integration
8. Solver and script adapters

Recommended next prompt:

```text
OSW-FUNC-001_PROJECT_SCHEMA_INTEGRATION
```

If the repository's functional autopilot queue is being used, adapt the existing
`OSW-AUTO-005_PROJECT_SCHEMA` step to this completed GUI baseline. Do not run a
generic GUI skeleton step.

## Functional Binding Note

`OSW-FUNC-001_PROJECT_SCHEMA_INTEGRATION` binds the frozen GUI to the
`HeatSink_Flow` demo `ProjectSchema` via `MainWindow.set_project()`,
`ProjectTreePanel.set_project()`, and `PropertiesPanel.set_project()`. Future
functional prompts should continue extending those model bindings instead of
rerunning a GUI skeleton.

`OSW-FUNC-004_PLUGIN_MANAGER_DIALOG_BINDING` adds a safe Plugin Manager dialog
and right-panel plugin registry binding on top of the frozen GUI. It reads
manifest data, displays health diagnostics, and stores local enable/path state
without loading plugin code or running solver executables.

`OSW-FUNC-005_MESH_IMPORT_BRIDGE` adds standard/exported mesh metadata import on
top of the existing ProjectSchema binding. Mesh refs can carry `MeshInfo`
summaries, the project tree continues to render mesh rows, and the properties
panel can show selected mesh metadata without replacing the mock viewport or
running external tools.

`OSW-FUNC-006_MSCRIPT_IMPORT_PREVIEW` adds safe MATLAB/Octave `.m` preview on
top of the same visual shell. Script refs can carry preview metadata and safety
summaries, the project tree continues to render script rows, and the properties
panel can show selected script summary data. The GUI preview does not run
MATLAB, Octave, or script content.

`OSW-FUNC-007_OCTAVE_RUNNER` adds an explicit, safety-gated Run with Octave path
to the script preview surface. The action routes through backend
`OctaveRunner`/`ExternalCommandRunner`, uses isolated workspaces and timeout
handling, and remains disabled for high-risk or out-of-scope safety findings by
default. The GUI still does not launch subprocesses directly.

`OSW-FUNC-008_FIGURE_CAPTURE_DATASET` adds FigureDataset viewing and report
handoff for existing PNG/SVG/PDF/CSV/JSON run artifacts. The Plot Viewer lists
figure metadata and workspace summaries, report previews can consume figure
datasets, and script preview can hand off captured artifacts after an explicit
Octave run. The GUI still does not execute scripts during import, preview, or
figure inspection.

`OSW-FUNC-009_MAT_READER` adds preview-only MATLAB MAT data inspection. MAT
preview dialogs show version, variable summaries, table previews, diagnostics,
and safe CSV export for compatible numeric variables. The ProjectSchema binding
stores MAT metadata through safe preview references, and the GUI still does not
invoke MATLAB, Octave, or external commands.

`OSW-FUNC-010_BOUNDARY_CURVE_BRIDGE` adds reusable BoundaryCurve previews on top
of the same frozen shell. Project trees can show boundary curves when a project
has them, the properties panel can show curve summaries and boundary-condition
curve references, and the BoundaryCurve dialog previews x/y data and validation
messages without generating solver files or running external tools.

`OSW-FUNC-011_REPORT_GENERATOR_BINDING` binds the existing report preview card
to real `ReportSummary` data. The panel can show generated report sections,
figure counts, and warning counts, while MainWindow report actions export
deterministic HTML through `osw.post` without running solvers, scripts, MATLAB,
Octave, or GUI subprocess calls.

`OSW-FUNC-012_GMSH_ADAPTER` adds a safe Gmsh primitive meshing dialog and menu
hook. The dialog can preview `.geo` text without Gmsh installed and can submit
an explicit mesh generation request through the backend Gmsh adapter and
`ExternalCommandRunner`. The GUI still does not call subprocess directly,
replace the shell, or add solver adapter behavior.

`OSW-FUNC-013_CALCULIX_INPUT_DECK` adds a safe CalculiX input deck dialog and
Run menu hook. The dialog previews readiness diagnostics and writes reviewed
`.inp` text only; it does not run `ccx`, parse results, replace the shell, or
call subprocesses from the GUI.

`OSW-FUNC-014_CALCULIX_RUNNER_BINDING` extends that dialog with an explicit
`Run with CalculiX` path backed by `CalculiXRunner` and `ExternalCommandRunner`.
The GUI shows run status, logs, artifacts, and diagnostics, and the run monitor
receives a compact summary. The GUI still does not call subprocess directly or
parse CalculiX result files.

`OSW-FUNC-015_CALCULIX_RESULT_PARSER` adds a read-only `Parse Results` hook to
the same CalculiX dialog. The dialog displays parsed max displacement, max
stress, and parser diagnostics from existing artifacts only, while the run
monitor can receive a compact result summary. The GUI still does not run `ccx`,
parse full FRD fields, or call subprocesses directly.
