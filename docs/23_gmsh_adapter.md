# Gmsh Adapter

`OSW-FUNC-012_GMSH_ADAPTER` adds a bounded Gmsh mesh generation bridge. It is a
primitive educational meshing workflow, not a solver adapter and not a CAD
healing pipeline.

## Models

Gmsh models live under `osw.mesh.gmsh_model`:

- `GmshGeometrySpec` describes primitive geometry and metadata.
- `GmshMeshSizeField` records global/min/max mesh size settings.
- `GmshPhysicalGroup` records stable physical group placeholder metadata.
- `GmshMeshRequest` describes an explicit generation request.
- `GmshMeshResult` records `.geo`, `.msh`, optional `.vtu`, diagnostics, runner
  result, artifacts, and optional MeshInfo.

All models serialize paths as strings and can be imported without Gmsh, meshio,
PyVista, or PySide6 installed.

## Geo Generation

`generate_geo_script()` and `write_geo_script()` create deterministic `.geo`
text without executing Gmsh. Supported primitives are:

- rectangle
- box
- cylinder
- sphere
- plate_with_hole

Mesh size controls are written as Gmsh characteristic length settings. Physical
groups use stable placeholder labels such as `inlet`, `outlet`, `wall`, and
`domain` where practical.

## Execution

`GmshAdapter.generate_mesh()` is the only generation path. It:

- resolves `gmsh` through `ExecutablePathRegistry` without executing it;
- writes the `.geo` script;
- runs `gmsh` through `ExternalCommandRunner` with a list command and timeout;
- records stdout/stderr and runtime artifacts;
- reports missing Gmsh as a friendly dependency diagnostic;
- optionally converts `.msh` to MeshModel/MeshInfo/VTU through the meshio bridge.

GUI code opens a preview dialog and calls this adapter API; it does not call
subprocess directly. Plugin discovery and health checks read manifest metadata
only and never run Gmsh.

## CLI

```powershell
python -m osw.cli gmsh-check
python -m osw.cli gmsh-formats
python -m osw.cli gmsh-write-geo --kind box --length 1 --width 0.2 --height 0.1 --mesh-size 0.05 --out artifacts\mesh\box.geo
python -m osw.cli gmsh-generate --kind box --length 1 --width 0.2 --height 0.1 --mesh-size 0.05 --out-dir artifacts\mesh
```

`gmsh-write-geo` does not require Gmsh. `gmsh-generate` requires an explicit
user command and fails gracefully when Gmsh is missing.

## Limitations

- No native commercial CAD import.
- No complex CAD healing.
- No solver-specific mesh generation.
- No solver execution.
- Physical groups are placeholders for later solver adapter steps.
- meshio conversion is optional; generated `.msh` artifacts remain valid report
  evidence even when conversion is unavailable.

## Next Step

Next functional step: `OSW-FUNC-013_CALCULIX_INPUT_DECK`.
