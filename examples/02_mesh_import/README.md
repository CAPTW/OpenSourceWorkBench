# Mesh Import Example

This directory is reserved for small, curated mesh import examples.

The v0.1 mesh import bridge targets standard/exported formats through the
optional `meshio` extra:

- Gmsh `.msh`
- Abaqus/CalculiX `.inp`
- ANSYS `.msh`
- Nastran `.bdf`, `.nas`, `.fem`
- SU2 `.su2`
- VTK `.vtk`
- VTU `.vtu`
- XDMF `.xdmf`, `.xmf`
- CGNS `.cgns` when local dependencies permit

Generated solver or meshing runtime directories should not be committed here.
