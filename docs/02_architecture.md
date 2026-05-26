# OSW Architecture

The repository uses a `src/osw` package layout. Core domain contracts live under
`osw.core`, while GUI, geometry, mesh, solver, script, and post-processing
packages remain separated by responsibility.

The GUI must coordinate workflows but not directly execute external solver
subprocesses. Solver adapters should prepare validated cases and hand execution
to an explicit backend/service boundary in later milestones.

Heavy integrations such as PySide6, Gmsh, PyVista, Cantera, CoolProp, and SciPy
are optional extras so bootstrap tests can run in a light Python environment.

## Project Schema Integration

The completed PySide6 GUI baseline binds to `osw.core` through ProjectSchema
objects. Core schema, unit, material, validation, and project IO modules remain
PySide6-free; GUI widgets consume them through explicit `set_project()` methods
without replacing the visual shell or adding solver execution behavior.

## Plugin Contract Integration

Plugin manifests and discovery live under `osw.plugins` and remain GUI-free.
Local discovery reads manifest data only, entry point loading is explicit, and
health checks inspect Python package availability and executable presence without
running solver binaries. See `docs/03_plugin_contract.md` for the manifest
schema and security rules.

## Runner Diagnostics Integration

External command execution is centralized behind `ExternalCommandRunner` and
`RunManager`. These services live outside the GUI, accept argument lists instead
of shell strings, capture stdout/stderr, enforce timeouts, and classify runtime
artifacts under controlled run directories. Solver and script adapters may use
this backend boundary in later steps; GUI widgets must not launch subprocesses
directly.

## Mesh Import Bridge

Standard/exported mesh import lives under `osw.mesh` and remains independent of
GUI and solver adapters. The meshio bridge imports meshio lazily, extracts
`MeshInfo` metadata, can attach summaries to ProjectSchema `MeshRef` records,
and reports unsupported, corrupt, or dependency-missing imports through
structured diagnostics. It does not run Gmsh, solvers, shell commands, or native
commercial CAD readers. See `docs/16_mesh_import_bridge.md`.
