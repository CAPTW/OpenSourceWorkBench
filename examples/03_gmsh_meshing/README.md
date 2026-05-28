# Tutorial 03: Gmsh Meshing Template

## Goal

Prepare a bounded educational mesh from a primitive rectangle, box, cylinder,
sphere, or plate-with-hole template and convert the generated `.msh` output
toward OSW mesh/report contracts.

## Prerequisites

- Optional mesh stack:

  ```powershell
  python -m pip install -e .[mesh]
  ```

- Optional local Gmsh executable for actual mesh generation.
- Optional `meshio` for MeshModel/VTU conversion.

The module can be imported without Gmsh installed; `.geo` generation does not
require Gmsh, and mesh generation returns a friendly diagnostic when the
executable is missing.

## Steps

1. Choose a small primitive. Keep the demo bounded to simple educational
   geometry.
2. Generate a `.geo` file without running Gmsh:

   ```powershell
   python -m osw.cli gmsh-write-geo --kind box --length 1 --width 0.2 --height 0.1 --mesh-size 0.05 --out artifacts\mesh\box.geo
   ```

3. If Gmsh is installed and you explicitly want to generate a mesh, run:

   ```powershell
   python -m osw.cli gmsh-generate --kind box --length 1 --width 0.2 --height 0.1 --mesh-size 0.05 --out-dir artifacts\mesh
   ```

4. Review mesh size control, physical group metadata placeholder, output paths,
   and warnings before using the mesh in a solver tutorial.
5. Include the mesh settings and output artifact summary in the HTML report.

## Expected Output

- A generated `.msh` file when Gmsh is available.
- A MeshModel/VTU path when meshio conversion is available and supported.
- A clear missing-Gmsh diagnostic when Gmsh is absent.
- Reportable metadata for primitive type, mesh size, physical groups placeholder,
  and generated artifacts.

## Troubleshooting

- `Gmsh executable was not found`: install Gmsh or configure the executable path
  in Plugin Manager.
- If VTU export fails, keep the `.msh` artifact and record the conversion
  warning.
- Reduce `target_size` only for very small examples; large generated meshes do
  not belong in the repository.
- This tutorial does not perform complex CAD healing or solver-specific mesh
  generation.
