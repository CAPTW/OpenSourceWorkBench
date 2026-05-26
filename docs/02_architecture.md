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
