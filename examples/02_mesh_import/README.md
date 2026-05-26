# Mesh Import Preview Example

This directory is reserved for small mesh import preview examples. The current
bridge uses the tiny checked-in test mesh under `tests/fixtures/mesh/tiny.msh`
for automated smoke coverage.

Run locally with the optional mesh extra installed:

```powershell
.venv\Scripts\python.exe -m osw.cli mesh-info tests\fixtures\mesh\tiny.msh
```

The mesh import bridge reads standard/exported mesh formats only. It does not
run Gmsh, solvers, or native commercial CAD importers.
