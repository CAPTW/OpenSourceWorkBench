# OSW Project Schema

`ProjectSchema` is the first functional layer under the completed PySide6 GUI
baseline. It gives the visual shell a real, serializable project model without
adding solver execution or replacing the GUI.

## Core Models

The schema lives under `src/osw/core/` and includes:

- `UnitSystem` and `Quantity`
- `Material`, `MaterialDB`, and `builtin_materials()`
- `Project`, `ProjectMetadata`, `GeometryRef`, `MeshRef`, `ScriptRef`
- `PhysicsSetup`, `BoundaryCondition`, and `SolverConfig`
- `BoundaryCurve`, `CurveAxis`, and `BoundaryCurveSource`
- `ResultRef`, `ReportConfig`, `PluginRef`, and `ProjectWarning`

Core modules do not import PySide6. GUI modules may import the core schema.

## Demo Project

`create_heatsink_flow_demo_project()` returns the `HeatSink_Flow` project that
matches the frozen GUI mock:

- geometry: `heatsink.step`, `enclosure.stp`, `fluid_domain.csg`
- mesh: `mesh.msh`, `mesh_stats.txt`
- solver: `chtSolver`, `Steady-State`, `GMRES`, `AMG`, `1.0e-06`
- scripts: `preprocess.m`, `run_case.m`, `postprocess.m`
- results: `run_0001`, `fields.ex2`, `residuals.dat`, `monitor.log`,
  `run_0000 (baseline)`
- report: `HeatSink_Flow Simulation Report`, `Run 0001`, `Overview`,
  `Key Results`, `Summary`

## IO

JSON project files use only the Python standard library. YAML project files use
optional PyYAML and raise a friendly `ProjectSchemaError` when PyYAML is not
installed.

CLI helpers:

```powershell
python -m osw.cli project-demo-json --out artifacts\demo_project.json
python -m osw.cli project-validate artifacts\demo_project.json
```

These commands do not require PySide6 and do not run solvers.

## Validation

Validation checks metadata, units, materials, boundary rows, solver tolerance,
safe-preview requirements for `.m` scripts, missing mesh/result references, and
warnings for proprietary CAD extensions. OSW v0.1 supports standard exported
formats and does not implement native SolidWorks, CATIA, NX, or Creo direct
import.

Boundary curve validation checks x/y length, at least two points for
interpolation, finite numeric values, missing unit metadata, monotonic x values
for time/spatial profiles, and source traceability. Boundary conditions can
reference a `curve_id`; ProjectSchema warns when the referenced curve is missing
or when the curve kind appears inconsistent with the boundary type.

## GUI Binding

The frozen visual widgets now expose lightweight binding methods:

- `ProjectTreePanel.set_project(project)`
- `PropertiesPanel.set_project(project)`
- `MainWindow.set_project(project)`

The binding preserves object names, visual layout, theme behavior, and mock
preview widgets.
