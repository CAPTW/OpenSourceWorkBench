# Gmsh Meshing Example

This example path is reserved for the bounded v0.1 Gmsh meshing demo. The Gmsh
adapter is optional: base OSW installs can import the module and report a
friendly diagnostic when `gmsh` is unavailable.

Minimal educational template:

```python
from osw.mesh.gmsh_adapter import GmshPrimitive, MeshSizeControl, generate_primitive_mesh

result = generate_primitive_mesh(
    GmshPrimitive.plate(width=1.0, height=0.5, name="plate"),
    "plate.msh",
    mesh_size=MeshSizeControl(target_size=0.2),
    vtu_path="plate.vtu",
)
```

The adapter only covers small primitive plate/box templates and `.msh` to
MeshModel/VTU conversion through meshio. It does not perform complex CAD healing
or solver-specific mesh generation.
