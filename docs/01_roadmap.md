# OSW v0.1 Roadmap

Each milestone must remain runnable without commercial software. Each milestone
must make no industrial certification claim.

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

The current public prerelease is `v0.1.5-rc3`, and current package metadata is
`0.1.5`. Published annotated `v0.1.5-rc3` peels to release source
`4b1effccf3bbc4fd18073c0ab39f90cfb6822232`. Later docs-only `develop`
commits do not move that tag or release source. Older `v0.1.5-rc2`,
`v0.1.5-rc1`, `v0.1.3-rc1`, and `v0.1.4-rc1` references are historical
unless a page explicitly marks them as the current boundary.

Post-public-release planning stays split into separate tracks so maintenance,
future features, and optional live validation do not blur scope or release
claims. OpenFOAM v12 template compatibility issues #18 and #19 are closed with
WSL-scoped evidence; this does not close optional live OpenFOAM validation issue
#9 by itself. Optional validation issues #6 through #11 are now closed after
separate bounded evidence and closure gates. They remain conceptually separate
tracks, and their closure evidence is issue-state evidence only: missing
optional dependencies are skipped-missing, not pass, and bounded validation is
not certification, production-readiness, broad solver/science correctness, or
release-readiness evidence.

- [Post-public-release roadmap](roadmap/README.md)
- [Current development cycle](development/current_cycle.md)
- [v0.1.3rc2 maintenance and revalidation](roadmap/v0_1_3rc2.md)
- [v0.1.4 next feature line](roadmap/v0_1_4.md)
- [Live optional validation](roadmap/live_optional_validation.md)
- [Current roadmap pointer](roadmap/current.md)

The current next-gate pointer is maintained in
[Current roadmap pointer](roadmap/current.md).

**Native report-asset filesystem resolution is `DEFERRED_RETAINED`.** Production native resolution is unsupported, the strict zero-provider-contact-before-attestation invariant remains unchanged, and no implementation is scheduled. Accepted schema, lexical, privacy, stale-binding, relink, and unresolved-placeholder contracts and their evidence remain retained. The status is not an implementation failure or a native-support claim; reopening requires a qualifying trigger and a separately authorized policy/architecture gate. Branches, worktrees, and evidence remain retained until a separate cleanup decision. Legacy compatibility paths remain outside the typed-resolver policy and are not certified provider-silent.

The canonical boundary and objective reopening criteria are documented in
[Report Asset Runtime Path Native
Deferral](experimental/report_asset_runtime_path_native_deferral.md).

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
- OSW v0.1 does not claim industrial certification, compliance, or production accuracy;
- GUI-triggered direct external solver execution.
- native report-asset availability resolution while its lifecycle remains
  `DEFERRED_RETAINED`.
