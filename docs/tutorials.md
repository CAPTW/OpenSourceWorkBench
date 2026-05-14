# OSW v0.1 Tutorial Examples

These tutorials connect the eight v0.1 demos to the common workflow:

```text
Import -> Configure -> Run or prepare -> Result -> Report
```

Each example remains small, local, and inspectable. Optional external
dependencies are marked explicitly, and missing dependency diagnostics are valid
tutorial outcomes when the dependency is not installed.

## Tutorial Index

| Tutorial | Example | Optional dependencies | Main output |
| --- | --- | --- | --- |
| 01 STEP import preview | [examples/01_step_import](../examples/01_step_import/README.md) | Optional CAD kernel stubs only | Geometry preview metadata |
| 02 mesh import preview | [examples/02_mesh_import](../examples/02_mesh_import/README.md) | `meshio` | `MeshInfo`, optional VTU |
| 03 Gmsh meshing template | [examples/03_gmsh_meshing](../examples/03_gmsh_meshing/README.md) | Gmsh, `meshio` | `.msh`, optional VTU |
| 04 CalculiX cantilever | [examples/04_calculix_cantilever](../examples/04_calculix_cantilever/README.md) | Optional `ccx` outside GUI | `.inp`, result summary |
| 05 OpenFOAM cavity and duct | [examples/05_openfoam_cavity](../examples/05_openfoam_cavity/README.md) | Optional OpenFOAM outside OSW | Case template files |
| 06 Cantera reactor | [examples/06_cantera_reactor](../examples/06_cantera_reactor/README.md) | Cantera | Species/time table |
| 07 CoolProp property table | [examples/07_coolprop_property](../examples/07_coolprop_property/README.md) | CoolProp | Property table, CSV |
| 08 MATLAB/Octave figure preview | [examples/08_mscript_figure](../examples/08_mscript_figure/README.md) | GNU Octave for explicit run | Preview, FigureDataset |

## Shared Tutorial Rules

- Keep source inputs small and standard/exported.
- Preview inputs before project mutation.
- Use explicit SI units at solver, chemistry, property, and report boundaries.
- Treat optional dependency failures as reportable diagnostics.
- Keep generated runtime directories, logs, solver outputs, and report exports
  out of the repository unless they are curated fixtures.
- Do not use the GUI as a direct subprocess launcher.

## Tutorial 01: STEP Import Preview

Goal: preview exported geometry metadata before accepting it into a project.

Prerequisites: base OSW install and a small STEP, ASCII STL, or OBJ file. Native
commercial CAD direct import is not supported; export STEP or STL first.

Steps: open [examples/01_step_import](../examples/01_step_import/README.md),
run `import_preview()` on a local file, review format/body/bounding-box metadata,
then record accepted metadata in the report.

Expected output: geometry preview metadata or a clear unsupported-format
diagnostic.

Troubleshooting: use ASCII STL for the lightweight parser, OBJ for vertex/face
preview, or STEP for metadata-only bridge behavior.

## Tutorial 02: Mesh Import Preview

Goal: turn a standard mesh into `MeshInfo` and optional VTU output.

Prerequisites: optional mesh stack with `meshio` and a small mesh file.

Steps: open [examples/02_mesh_import](../examples/02_mesh_import/README.md),
call `load_mesh_info()`, optionally call `convert_mesh_to_vtu()`, and add counts,
cell types, bounding box, and warnings to the report.

Expected output: `MeshInfo` with node/element counts and bounding box, plus an
optional VTU artifact.

Troubleshooting: install the mesh extra for real imports and keep unsupported
cell type warnings visible.

## Tutorial 03: Gmsh Meshing Template

Goal: prepare a tiny primitive mesh with a visible mesh size control.

Prerequisites: optional Gmsh and meshio stacks.

Steps: open [examples/03_gmsh_meshing](../examples/03_gmsh_meshing/README.md),
generate a plate or box mesh, inspect physical group placeholders and artifact
paths, then include the mesh settings in the report.

Expected output: `.msh` file, optional VTU file, and reportable mesh metadata.

Troubleshooting: missing Gmsh is a valid diagnostic. Do not commit large
generated meshes.

## Tutorial 04: CalculiX Cantilever

Goal: generate a linear static cantilever deck and report validation evidence.

Prerequisites: small mesh, isotropic elastic material, fixed support, load, and
optional `ccx` only for explicit external execution.

Steps: open [examples/04_calculix_cantilever](../examples/04_calculix_cantilever/README.md),
generate the `.inp`, review validation messages, optionally run through the
reviewed backend runner outside the GUI, parse a `.dat` summary, and compare the
cantilever displacement estimate.

Expected output: deterministic `.inp`, optional result summary, max
displacement/stress values, and report limitations.

Troubleshooting: fix unsupported cell types, missing material, missing boundary
condition, or missing load before treating a case as ready.

## Tutorial 05: OpenFOAM Cavity And Duct Templates

Goal: generate bounded CFD template files for cavity or duct examples.

Prerequisites: base OSW install for generation and optional OpenFOAM only for
external execution.

Steps: open [examples/05_openfoam_cavity](../examples/05_openfoam_cavity/README.md),
generate a cavity or duct case in a scratch directory, review patch names and
case files, and record generated paths and warnings in the report.

Expected output: `0`, `constant`, and `system` case files plus patch validation
warnings when needed.

Troubleshooting: keep missing OpenFOAM as a diagnostic, not a failure of
template generation.

## Tutorial 06: Cantera Reactor

Goal: run a bounded 0D reactor and produce a species/time table.

Prerequisites: optional Cantera and a local mechanism such as `gri30.yaml`.

Steps: open [examples/06_cantera_reactor](../examples/06_cantera_reactor/README.md),
preview the reactor config, explicitly run only if Cantera is installed, and add
the table plus temperature/time plot placeholder to the report.

Expected output: species/time table, plot placeholder, and dependency or
mechanism diagnostics when needed.

Troubleshooting: keep the time range small and fix invalid composition,
temperature, or pressure before running.

## Tutorial 07: CoolProp Property Table

Goal: calculate a property point and small sweep table with explicit SI inputs.

Prerequisites: optional CoolProp.

Steps: open [examples/07_coolprop_property](../examples/07_coolprop_property/README.md),
calculate a water property point, generate a temperature sweep, export CSV, and
attach the table to the report.

Expected output: table preview, CSV text, plot placeholder, and missing
dependency diagnostics when CoolProp is unavailable.

Troubleshooting: start with `Water`, `D`, and `H`; invalid fluid/property names
come from CoolProp and should be recorded clearly.

## Tutorial 08: MATLAB/Octave Figure Preview

Goal: preview `.m` script safety and capture accepted figures.

Prerequisites: base OSW install for preview; optional GNU Octave only for
explicit execution.

Steps: open [examples/08_mscript_figure](../examples/08_mscript_figure/README.md),
run `import_mscript_preview()`, review safety findings, explicitly run through
the reviewed Octave runner only after approval, and convert accepted PNG/SVG
paths into a `FigureDataset`.

Expected output: preview metadata, safety warnings, optional PNG/SVG artifacts,
and reportable figure records.

Troubleshooting: never auto-run `.m` files during import. Review shell, network,
and file mutation warnings before execution.
