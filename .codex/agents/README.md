# OSW Agent Roles

These role files define reusable review perspectives for Codex work. They are
not autonomous permissions to spawn subagents; use them only when the active
prompt asks for role-based review or parallel agent work.

Each role must follow root `AGENTS.md`, the Task Card, and the Git safety rules.

## Roles

- product-owner: scope, roadmap, and non-goal guard.
- architecture: dependency direction and plugin boundaries.
- core-schema: ProjectSchema, UnitSystem, MaterialDB, ResultDataset,
  FigureDataset.
- gui: PySide6 shell and preview workflows.
- visualization: PyVista, Matplotlib, FigureDataset.
- format-import: standard/exported CAD, mesh, CAE, CFD, chemistry formats.
- mesh: meshio and Gmsh-facing workflows.
- cae-calculix: bounded CalculiX linear static demo.
- cfd-openfoam: bounded OpenFOAM cavity/duct templates.
- chm: Cantera and CoolProp basics.
- mscript: `.m` and `.mat` preview-first workflows.
- qa-test: tests, golden fixtures, validation, and QA scripts.
- docs-release: reports, release checklist, validation matrix, claims.
- reviewer: score findings against the review protocol.
- git-operator: local-only Git safety.
