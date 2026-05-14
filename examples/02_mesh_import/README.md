# Tutorial 02: Mesh Import Preview

## Goal

Load standard/exported mesh metadata through the meshio-facing bridge and
produce reportable mesh information: node count, element count, cell types, and
bounding box.

## Prerequisites

- Base OSW development install.
- Optional mesh stack for real mesh reading:

  ```powershell
  python -m pip install -e .[mesh]
  ```

- A small mesh in a supported standard/exported format: `.msh`, `.inp`, `.bdf`,
  `.nas`, `.fem`, `.su2`, `.vtk`, `.vtu`, `.xdmf`, `.xmf`, or optional `.cgns`.

## Steps

1. Place a small mesh fixture in a local scratch path. Keep generated solver or
   meshing runtime directories out of this repository.
2. Inspect mesh metadata:

   ```python
   from pathlib import Path

   from osw.mesh.meshio_bridge import load_mesh_info

   info = load_mesh_info(Path("mesh.msh"))
   print(info.to_dict())
   ```

3. Convert the mesh to VTU when `meshio` supports the source cells:

   ```python
   from pathlib import Path

   from osw.mesh.conversion import convert_mesh_to_vtu

   convert_mesh_to_vtu(Path("mesh.msh"), Path("mesh.vtu"))
   ```

4. Add the mesh summary, warnings, and any export artifact path to the project
   report.

## Expected Output

- `MeshInfo` includes source, format, node count, element count, cell type
  distribution, and bounding box.
- Unsupported or corrupt meshes fail with a user-readable `MeshImportError`.
- VTU export creates a reportable artifact when `meshio` and the cell types are
  supported.

## Troubleshooting

- `meshio is not installed`: install the optional mesh extra before importing
  real mesh files.
- `Unsupported mesh format`: export one of the supported standard mesh formats.
- `Could not read mesh`: open the mesh in a mesh viewer or regenerate it from
  the source tool, then retry with a small fixture.
- Unsupported cell types should be reported in the tutorial output rather than
  hidden or converted silently.
