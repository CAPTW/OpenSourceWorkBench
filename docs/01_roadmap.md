# OSW v0.1 Roadmap

Each milestone must remain runnable without commercial software and must avoid
industrial certification claims.

## Roadmap Items

1. Repository skeleton, CLI smoke checks, Git safety rails, and contributor docs.
2. Core contracts: ProjectSchema, UnitSystem, MaterialDB, ResultDataset, and
   FigureDataset.
3. Plugin/add-in API for importers, solvers, scripts, post-processing, and
   reports.
4. PySide6 shell with project tree, preview panes, validation surfaces, and
   report entry points.
5. Standard geometry and mesh preview workflows.
6. Bounded solver and science demo workflows.
7. HTML reports, golden tests, validation matrix, and release checklist.

## Demo Mapping

| Demo | User story | Roadmap item |
| --- | --- | --- |
| 1. Empty project | Create/open a minimal valid project and inspect metadata. | 2, 4 |
| 2. STEP import preview | Preview standard exported geometry without native CAD. | 3, 5 |
| 3. Mesh import preview | Load mesh metadata and fields through meshio-facing contracts. | 3, 5 |
| 4. Gmsh meshing template | Prepare a small meshing workflow with reviewable parameters. | 3, 5, 6 |
| 5. CalculiX cantilever | Demonstrate a linear static educational case boundary. | 3, 6, 7 |
| 6. OpenFOAM cavity/duct template | Demonstrate a bounded CFD template, not full solver coverage. | 3, 6, 7 |
| 7. Cantera/CoolProp basics | Demonstrate chemistry/property data flow and reporting. | 3, 6, 7 |
| 8. MATLAB/Octave figure preview | Preview `.m`/`.mat` figure data before project mutation. | 3, 6, 7 |

## Phase Gates

- P0: scope, roadmap, Git safety, release guardrails.
- P1: core data contracts and validation model.
- P2: plugin/add-in contracts with no heavy workflow logic.
- P3: GUI shell and preview-first navigation.
- P4: import and mesh demo flows.
- P5: bounded solver/science/script demos.
- P6: report export, validation matrix, golden tests, and release checklist.

## Completion Criteria

v0.1 is complete only when each demo has:

- a documented input fixture or template;
- a preview/configuration step;
- a bounded run or run-preparation step;
- a structured result or figure output;
- a report section;
- validation evidence or a documented limitation.
