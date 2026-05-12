# Mesh Agent Rules

This directory owns mesh-facing contracts and preview workflows.

- Prefer meshio-facing metadata, fields, groups, and validation summaries over
  ad hoc mesh parsing.
- Gmsh integration points are optional and must not make Gmsh mandatory for base
  import, CLI smoke, or unit tests.
- Keep meshing workflows bounded to educational templates until scope expands.
- Do not commit generated mesh runtime directories, solver cases, or large
  derived artifacts.
- Mesh outputs should connect to ProjectSchema, UnitSystem, ResultDataset,
  FigureDataset, and report evidence where relevant.
