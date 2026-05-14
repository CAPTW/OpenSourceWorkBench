# Tutorial 03: Gmsh Meshing Template

## Goal

Prepare a bounded educational mesh from a primitive plate or box and convert the
generated `.msh` output toward OSW mesh/report contracts.

## Prerequisites

- Optional mesh stack:

  ```powershell
  python -m pip install -e .[mesh]
  ```

- Optional `gmsh` Python package and local Gmsh runtime for actual mesh
  generation.
- Optional `meshio` for MeshModel/VTU conversion.

The module can be imported without Gmsh installed; generation returns a friendly
diagnostic when the dependency is missing.

## Steps

1. Choose a small primitive. Keep the demo bounded to plate or box geometry.
2. Generate a `.msh` file and optional VTU preview artifact:

   ```python
   from osw.mesh.gmsh_adapter import (
       GmshPrimitive,
       MeshSizeControl,
       generate_primitive_mesh,
   )

   result = generate_primitive_mesh(
       GmshPrimitive.plate(width=1.0, height=0.5, name="plate"),
       "plate.msh",
       mesh_size=MeshSizeControl(target_size=0.2),
       vtu_path="plate.vtu",
   )
   print(result.to_dict())
   ```

3. Review mesh size control, physical group metadata placeholder, output paths,
   and warnings before using the mesh in a solver tutorial.
4. Include the mesh settings and output artifact summary in the HTML report.

## Expected Output

- A generated `.msh` file when Gmsh is available.
- A MeshModel/VTU path when meshio conversion is available and supported.
- A clear missing-Gmsh diagnostic when Gmsh is absent.
- Reportable metadata for primitive type, mesh size, physical groups placeholder,
  and generated artifacts.

## Troubleshooting

- `gmsh is not installed`: install the optional Gmsh stack or use the missing
  dependency diagnostic as the tutorial result.
- If VTU export fails, keep the `.msh` artifact and record the conversion
  warning.
- Reduce `target_size` only for very small examples; large generated meshes do
  not belong in the repository.
- This tutorial does not perform complex CAD healing or solver-specific mesh
  generation.
