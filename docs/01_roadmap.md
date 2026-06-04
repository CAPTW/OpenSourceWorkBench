# OSW v0.1 Roadmap

Each milestone must remain runnable without commercial software and must avoid
industrial certification claims.

## Roadmap Items

1. P0 scope baseline: North Star, roadmap, guardrails, risks, Git safety rails,
   and contributor docs.
2. P1 core contracts: ProjectSchema, UnitSystem, MaterialDB, ResultDataset, and
   FigureDataset.
3. P2 plugin/add-in API: importers, solvers, scripts, post-processing, and
   report contributors.
4. P3 PySide6 shell: project tree, preview panes, validation surfaces, and
   report entry points.
5. P4 standard geometry and mesh preview workflows.
6. P5 bounded solver, science, and script demo workflows.
7. P6 HTML reports, golden tests, validation matrix, and release checklist.

## Post-Public-Release Roadmap

The public `v0.1.3-rc1` prerelease is published with source assets and a
Windows portable ZIP. Post-public-release planning is split into separate
tracks so maintenance, future features, and optional live validation do not
blur scope or release claims:

- [Post-public-release roadmap](roadmap/README.md)
- [v0.1.3rc2 maintenance and revalidation](roadmap/v0_1_3rc2.md)
- [v0.1.4 next feature line](roadmap/v0_1_4.md)
- [Live optional validation](roadmap/live_optional_validation.md)
- [Current roadmap pointer](roadmap/current.md)

The next recommended planning gate is
`OSW-GH-001_ISSUES_AND_MILESTONES_TRIAGE`.

## Demo Mapping

| Demo | User story | Roadmap item | v0.1 completion signal |
| --- | --- | --- | --- |
| 1. Empty project | Create/open a minimal valid project and inspect metadata. | P1, P3, P6 | Project validates and appears in GUI/report. |
| 2. STEP import preview | Preview standard exported geometry without native CAD. | P2, P4, P6 | Import preview summarizes metadata before mutation. |
| 3. Mesh import preview | Load mesh metadata and fields through meshio-facing contracts. | P2, P4, P6 | Mesh preview shows counts, fields/groups, units, and warnings. |
| 4. Gmsh meshing template | Prepare a small meshing workflow with reviewable parameters. | P2, P4, P5, P6 | Template preparation is inspectable and optional-Gmsh aware. |
| 5. CalculiX cantilever | Demonstrate a linear static educational case boundary. | P2, P5, P6 | Case or fixture result maps to ResultDataset with limits. |
| 6. OpenFOAM cavity/duct template | Demonstrate a bounded CFD template, not full solver coverage. | P2, P5, P6 | Template/report states it is not a full OpenFOAM UI. |
| 7. Cantera/CoolProp basics | Demonstrate chemistry/property data flow and reporting. | P2, P5, P6 | Property/reactor output includes units and dependency status. |
| 8. MATLAB/Octave figure preview | Preview `.m`/`.mat` figure data before project mutation. | P2, P5, P6 | No arbitrary `.m` auto-run; figure/table data previews safely. |

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

## Parking Lot

The following are explicitly outside the v0.1 roadmap unless a later decision
log entry moves them:

- native commercial CAD direct import;
- Simulink, `.slx`, or `.mlapp`;
- full ANSYS Workbench-like workflow cloning;
- full OpenFOAM case editor or solver UI;
- nonlinear contact/plasticity demos;
- industrial certification, compliance, or production accuracy claims;
- GUI-triggered direct external solver execution.
