# Mesh Import Bridge

`OSW-FUNC-005_MESH_IMPORT_BRIDGE` adds the first standard mesh import boundary
for OpenSolver Workbench. It is a metadata and conversion bridge, not a meshing
or solver execution feature.

## Purpose

The mesh bridge lets OSW inspect exported mesh files, summarize their metadata,
and attach the summary to `ProjectSchema` as `MeshRef` data. This keeps the GUI
and project tree connected to real mesh metadata without replacing the visual
baseline or adding solver execution.

## Data Model

The core mesh model lives under `src/osw/mesh`:

- `MeshFormat` identifies supported exported mesh families.
- `MeshBounds` stores a serializable bounding box.
- `MeshCellBlock` summarizes homogeneous cell blocks.
- `MeshInfo` stores lightweight metadata: source path, format, node count,
  element count, cell types, bounds, point/cell/field data names, physical
  groups, warnings, and metadata.
- `MeshModel` can carry optional normalized points/cells for preview and
  conversion while keeping `MeshInfo` as the project-facing summary.

Large arrays are optional and should not be stored directly in ProjectSchema.

## meshio Bridge

`src/osw/mesh/meshio_bridge.py` imports `meshio` lazily. Importing `osw`,
`osw.mesh`, or non-GUI modules does not require meshio.

Supported extension recognition includes:

- `.msh`
- `.inp`
- `.bdf`, `.nas`, `.fem`
- `.su2`
- `.vtk`, `.vtu`
- `.xdmf`, `.xmf`
- `.cgns`
- `.med`

STL and OBJ remain standard geometry surface preview formats in v0.1. Mesh
surface import for those extensions is deferred so the existing geometry import
workflow keeps ownership of `.stl` and `.obj` files.

When meshio is installed, `read_mesh()` returns a `MeshImportResult` containing
a `MeshModel`, diagnostics, status, source path, and detected format. When
meshio is missing, unsupported, or a file is corrupt, the bridge returns
friendly diagnostics instead of raw tracebacks.

## Conversion

`write_mesh()` exports supported normalized mesh data through meshio when the
optional dependency is available. Output support is intentionally small and
standard:

- `.vtu`
- `.vtk`
- `.msh`
- `.inp`
- `.xdmf`, `.xmf`

The older compatibility helpers (`load_mesh_info()`, `load_mesh()`, and
`export_vtu()`) remain available for existing callers and tests.

## ProjectSchema Binding

`MeshRef` can now carry a serializable `mesh_info` summary alongside existing
fields such as `node_count`, `cell_count`, `face_count`, and
`quality_summary`. `mesh_to_project_ref()` converts a `MeshModel` into a
ProjectSchema `MeshRef` without storing large arrays.

The frozen GUI uses the existing ProjectSchema path:

- `ProjectTreePanel` renders mesh refs under the Mesh group.
- `PropertiesPanel` can read mesh summary rows for a selected mesh.
- `MainWindow.import_mesh_file()` and `attach_mesh_to_project()` attach
  metadata only. They do not run external tools or solvers.

## Built-in Plugin Metadata

`builtin_meshio_plugin_manifest()` returns a data-only manifest for the
`osw.meshio` mesh importer bridge:

- domain: `MESH`
- type: `mesh_importer`
- optional dependency: `meshio`
- capabilities: `mesh_info`, `mesh_conversion`,
  `project_mesh_ref_binding`

This manifest does not load plugin code or execute external commands.

## CLI

Mesh CLI commands are dependency-guarded:

```powershell
.venv\Scripts\python.exe -m osw.cli mesh-formats
.venv\Scripts\python.exe -m osw.cli mesh-info tests\fixtures\mesh\tiny.msh
.venv\Scripts\python.exe -m osw.cli mesh-convert input.msh output.vtu
```

`mesh-formats` works without meshio. `mesh-info` and `mesh-convert` require
meshio and return a friendly dependency diagnostic when the optional mesh extra
is not installed.

## Commercial Native CAD Scope

The mesh bridge does not support native commercial CAD readers. Extensions such
as `.sldprt`, `.sldasm`, `.catpart`, `.catproduct`, `.prt`, and `.asm` produce a
clear diagnostic:

```text
v0.1 supports standard/exported CAD and mesh formats. Please export STEP/STL/OBJ or a supported mesh format.
```

No native SolidWorks, CATIA, NX, Creo, or similar direct import is implemented.

## Security Rules

- Mesh import uses library parsing only and does not execute external programs.
- GUI mesh import helpers do not call `ExternalCommandRunner`.
- Mesh conversion does not run Gmsh, solvers, or shell commands.
- meshio remains optional and lazily imported.
- Runtime/generated mesh artifacts must not be committed unless intentionally
  added as small fixtures.

## Known Limitations

- Full mesh quality analysis is deferred; current summaries are counts, cell
  distribution, bounds, data names, and cheap warnings.
- Gmsh mesh generation is not part of this bridge.
- PyVista viewer binding is not part of this bridge.
- Solver-specific mesh parsing and repair are deferred.

## Next Step

Next functional step: `OSW-FUNC-006_MSCRIPT_IMPORT_PREVIEW`.
