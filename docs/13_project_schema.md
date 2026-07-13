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
- `ReportScreenshotAsset` and `ReportAssetPathKind`

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

## Report Screenshot Path Intent

Project schema `0.2` preserves an explicit report-screenshot `path_kind` for
`legacy_raw`, `external_absolute`, and `project_relative` records;
`managed_project_asset` remains reserved. Schema `0.1` and omitted
`path_kind` values retain their legacy omission semantics. Serialization and
round-trip preserve the stored path text and kind, but do not resolve a target.

**Native resolution: `DEFERRED_RETAINED`.** Without an authorized resolver, typed `external_absolute` and `project_relative` records remain `unresolved_no_resolver` in the manager/report bridge. Explicit relink replaces one in-memory Project screenshot record only after the existing validation, explicit-confirmation, post-confirmation file-check, and stale-target-revalidation flow: `external_absolute` remains `external_absolute`, while `project_relative` becomes `external_absolute`. Serialization and relink do not create a typed `effective_path` or usable report `image_path`, so the unresolved placeholder remains; saving the Project is separate and explicit. This establishes no durable native filesystem fact and makes no negative finding about the target. Legacy or unmarked compatibility behavior is separate, may perform filesystem checks, and is not certified provider-silent.

See [Report Asset Runtime Path Native
Deferral](experimental/report_asset_runtime_path_native_deferral.md) for the
canonical native-fact and legacy compatibility boundaries.

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

Report screenshot validation is lexical only. It validates the declared kind
and string form without establishing existence, file type, readability,
locality, containment, provider silence, or any other filesystem fact.

## GUI Binding

The frozen visual widgets now expose lightweight binding methods:

- `ProjectTreePanel.set_project(project)`
- `PropertiesPanel.set_project(project)`
- `MainWindow.set_project(project)`

The binding preserves object names, visual layout, theme behavior, and mock
preview widgets.
