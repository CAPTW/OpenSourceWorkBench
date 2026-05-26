# OpenSolver Workbench GUI Reference Specification

This document preserves the visual target for the OpenSolver Workbench v0.1
main Run screen so later implementation passes do not need the full prompt or
reference screenshot in chat context. The Dark theme is the visual reference and
default. Light and System themes must preserve the same layout, density, mock
data, and workflow structure; they are theme derivatives, not different user
interfaces.

The target is a professional engineering desktop app for educational and
research CAE / CFD / CHM / MATLAB-Octave workflows. It must not imply a full
ANSYS clone, MATLAB clone, Simulink support, `.mlapp` support, native
SolidWorks/CATIA/NX/Creo import, full OpenFOAM UI, industrial certification, or
production CAE guarantees.

## Reference Image

Preferred reference path:

```text
docs/ui/reference/osw_run_screen.png
```

If that image is missing, use this specification as the authoritative layout
and visual anchor. Do not use the screenshot as a flat background image in the
application. Build the UI from real PySide6 widgets, layouts, styles, and mock
visualization widgets.

## Overall Window

- Application title: `OpenSolver Workbench`
- Subtitle near title: `Open Source CAE / CFD / CHM / MATLAB-Octave`
- Default reference size: `2048 x 1152`
- Minimum usable size: `1440 x 810`
- Default active project: `HeatSink_Flow`
- Default active workflow step: `4 Run`
- Layout density: compact, data-heavy, engineering workstation style
- Visual language: crisp borders, small fonts, compact tables, restrained
  dashboard panels

Approximate layout proportions at `2048 x 1152`:

- Top app bar + toolbar + stepper: about `118 px`
- Left sidebar: about `320 px`
- Right inspector: about `410-460 px`
- Bottom run monitor: about `360 px`
- Status bar: about `28 px`
- Central viewport fills remaining space

Main regions:

1. Top title, toolbar, and workflow stepper
2. Left project tree sidebar
3. Central 3D/result viewport
4. Bottom run monitor
5. Right properties/inspector panel
6. Bottom status bar

## Top Header, Toolbar, And Workflow

Top-left text:

```text
OpenSolver Workbench
Open Source CAE / CFD / CHM / MATLAB-Octave
```

Main toolbar actions:

- `New`
- `Open`
- `Save`
- `Save As`
- `Import`
- `Export`

Center workflow stepper:

- `1 Import` complete with a check mark
- `2 Configure` complete with a check mark
- `3 Mesh` complete with a check mark
- `4 Run` active, blue highlighted
- `5 Results` inactive
- `6 Report` inactive

Top-right actions:

- `Terminal`
- `Preferences`
- `Help`
- `About`

Menu bar items for the shell:

- `File`
- `Import`
- `Plugins`
- `Run`
- `Reports`
- `Help`

The Preferences action must expose theme selection for `Dark`, `Light`, and
`System`.

## Left Project Sidebar

Header:

```text
PROJECTS
```

Active project:

```text
HeatSink_Flow
```

Tree structure:

```text
HeatSink_Flow
  Geometry
    heatsink.step
    enclosure.stp
    fluid_domain.csg
  Mesh
    mesh.msh
    mesh_stats.txt
  Physics
    heat_transfer.yaml
    turbulence.yaml
  Solvers
    chtSolver
    settings.json
  Scripts
    preprocess.m
    run_case.m
    postprocess.m
  Results
    run_0001
      fields.ex2
      residuals.dat
      monitor.log
    run_0000 (baseline)
  Reports
    report.md
    report.pdf
```

Group icon colors and meanings:

- Geometry: green cube-like icon
- Mesh: purple grid icon
- Physics: orange physics/field icon
- Solvers: blue sigma-like icon
- Scripts: yellow code icon
- Results: cyan chart icon
- Reports: red document icon

Additional visual requirements:

- Add a green check mark on `mesh.msh` or the Mesh group when practical.
- Include small refresh/search affordances near the header if practical.
- Add a bottom filter/search area:

```text
FILTERS
Search project tree...
```

- Add bottom-left footer:

```text
Active Project: HeatSink_Flow
```

## Central Viewport

Viewport toolbar:

- `View: von Mises Stress` dropdown
- Select/pointer tool
- Rotate/orbit tool
- Pan tool
- Zoom tool
- Fit tool
- Section/clip tool
- Camera/screenshot tool

Main mock visualization:

- Stylized 3D heat sink similar to the screenshot
- Blue heat sink with multiple fins
- Left cylindrical inlet/outlet pipe
- Triangular surface mesh overlay
- False-color contour from blue to green/yellow/red
- Highest red/yellow concentration near fin roots and base
- Semi-transparent contour haze is acceptable for first mock rendering
- Do not require PyVista in the first visual shell
- Keep the widget API compatible with a future PyVista-backed viewport

Legend text:

```text
von Mises Stress
(Pa)
0.00e+00 to 2.50e+08
```

Legend visuals:

- Vertical colorbar, blue through green/yellow to red
- Left side of the viewport

Orientation cube:

- Upper right
- Labels: `TOP`, `FRONT`, `RIGHT`
- Axes: `X` red, `Y` green, `Z` blue

Additional viewport elements:

- Small axis triad at lower left
- Scale bar at bottom right:

```text
0 25 50 75 100 mm
```

## Bottom Run Monitor

Section title:

```text
RUN MONITOR
```

Four-pane layout:

1. `LOG`
2. `RESIDUALS`
3. `WARNINGS` plus `PROGRESS`
4. `OCTAVE / MATLAB FIGURE`

### Log Panel

Use a monospace font and compact lines. Content should resemble:

```text
[12:41:02] OpenSolver 2.1.0 ...
[12:41:02] Case : HeatSink_Flow
[12:41:02] Mesh : mesh.msh ...
[12:41:02] Solver: chtSolver ...
[12:41:04] Reading material library: builtin
[12:41:06] Applying boundary conditions...
[12:41:09] Starting steady-state solve...
[12:41:18] Iteration 080 residuals below 1.0e-04
[12:41:26] Converged in 122 iterations.
[12:41:26] Writing results...
[12:41:28] Run completed successfully.
```

### Residuals Chart

- Dark chart background in Dark mode
- Log-scale y-axis labels
- X-axis: iterations
- Multiple colored curves: `p`, `T`, `Ux`, `Uy`, `Uz`
- Legend on the right

### Warnings And Progress

Warning cards:

- `Mesh skewness is high in 142 cells`
- `Non-orthogonal faces detected (max 68°)`
- `Using default turbulent Prandtl number (0.85)`

Progress text:

```text
Run 0001 (steady-state)
Elapsed 00:00:26
Remaining 00:00:00
100%
```

Progress actions:

- Progress bar at `100%`
- `Open Results Folder` button

### Octave / MATLAB Figure

Panel title:

```text
Temperature Along Centreline
```

Subtitle:

```text
y = 0, z = 0
```

Plot requirements:

- Line plot with cyan markers
- X-axis: `x (mm)`
- Y-axis: `Temperature (°C)`

Command line text:

```text
>> plot(centreline_x, T_center, '-o')
```

`.m` and `.mat` workflows remain preview-first. The GUI shell must not execute
arbitrary MATLAB or Octave scripts by default.

## Right Properties And Inspector Panel

Tabs:

- `Properties`
- `Materials`
- `BCS`
- `Advanced`

The `Properties` tab is active by default.

### Material Section

Header:

```text
MATERIAL
```

Fields:

```text
Material Library: builtin
Material: Aluminum 6061
```

Action:

- `Edit Material...`

### Boundary Conditions Section

Header:

```text
BOUNDARY CONDITIONS
```

Table columns:

- `Name`
- `Type`
- `Value`

Rows:

| Name | Type | Value |
| --- | --- | --- |
| `inlet` | `Velocity Inlet` | `3.0 m/s` |
| `outlet` | `Pressure Outlet` | `0 Pa` |
| `wall_heatsink` | `Wall (No Slip)` | `—` |
| `base_bottom` | `Heat Flux` | `1.0e5 W/m²` |
| `symmetry` | `Symmetry` | `—` |

Buttons:

- `Add`
- `Edit`
- `Copy`
- `Remove`

### Solver Settings Section

Header:

```text
SOLVER SETTINGS
```

Fields:

```text
Solver: chtSolver
Time Scheme: Steady-State
Linear Solver: GMRES
Preconditioner: AMG
Convergence Tol.: 1.0e-06
Advanced Options collapsed
```

The GUI may preview or configure solver settings but must not directly execute
solver subprocesses.

### Plugins Section

Header:

```text
PLUGINS
```

Rows:

- `Octave / MATLAB Interface Enabled`
- `ParaView Catalyst Enabled`
- `Mesh Quality Checker Enabled`
- `Report Generator Enabled`

Action:

- `Manage Report...`

Plugin UI must respect OSW plugin manifest boundaries and avoid side effects at
import time.

### Report Preview Section

Header:

```text
REPORT PREVIEW
```

Content:

```text
HeatSink_Flow Simulation Report
Run 0001
1. Overview
2. Key Results
3. Summary
```

Visuals and action:

- Small thumbnail placeholder resembling a heat sink contour
- `Export Report...` button

## Status Bar

Left/center content:

```text
Solver: chtSolver
Memory: 6.2 GB / 15.9 GB
Cores: 12 / 16
```

Right content:

```text
Ready
```

Visuals:

- Green status indicator near solver/readiness state
- Compact memory usage bar
- Compact core usage bar

## Implementation Notes

- Use PySide6 for the desktop shell.
- Build visible regions as separate widgets rather than a single large
  `MainWindow` file.
- Use QPainter-based mock chart widgets and a QPainter-based
  `MockSimulationViewport` for the first visual pass.
- Use system fonts only:
  - Windows: `Segoe UI`
  - Fallbacks: `Inter`, `Noto Sans`, `Arial`, `sans-serif`
  - Monospace logs: `Consolas`, `Cascadia Mono`, `Menlo`, `monospace`
- Do not download icon packs or commit proprietary fonts.
- Use simple text/icons, QPainter icons, or local SVG if icons are needed.
- Keep all theme colors behind semantic theme tokens.
- Runtime visual behavior is mock-only in this prompt set; no real solver
  execution belongs in the GUI button path.
