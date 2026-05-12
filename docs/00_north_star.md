# OSW North Star

OpenSolver Workbench v0.1 is an open-source educational and research
Engineering Solver & Script Workbench. Its purpose is to make engineering
workflow state visible and reviewable across import, configuration, solver
handoff, results, validation, and report generation.

The product promise is not breadth. The product promise is a small set of
transparent, reproducible workflows that teach how solver workbenches are built
and how data moves through them.

## North Star Statement

OSW v0.1 helps a student, researcher, or solver developer open a project, import
standard data, configure units/materials/cases, run or prepare a bounded demo
workflow, inspect results, and export an HTML report with enough validation
evidence to understand what happened.

## v0.1 Demos

1. Empty project: create/open the smallest valid OSW project.
2. STEP import preview: inspect standard exported geometry metadata.
3. Mesh import preview: load a mesh through meshio-facing contracts.
4. Gmsh meshing template: prepare a small educational meshing workflow.
5. CalculiX cantilever: demonstrate a linear static case boundary.
6. OpenFOAM cavity or duct template: demonstrate a bounded CFD template.
7. Cantera/CoolProp basics: demonstrate thermo/property data flow.
8. MATLAB/Octave script figure preview: inspect `.m`/`.mat` output safely.

## Must Support

- PySide6 desktop GUI shell and workflow previews.
- Plugin/add-in architecture for importers, solvers, scripts, and reports.
- ProjectSchema, UnitSystem, MaterialDB, ResultDataset, and FigureDataset
  contracts.
- Standard/exported CAD, CAE, CFD, and chemistry formats.
- meshio, Gmsh, PyVista, and Matplotlib integration points.
- CalculiX linear static demo and OpenFOAM cavity/duct template demo.
- Cantera and CoolProp basic demo flows.
- MATLAB/Octave `.m` and `.mat` preview-first workflow.
- HTML report output, validation matrix, and golden tests.

## Must Not Support

- Native SolidWorks, CATIA, NX, Creo, or other commercial CAD direct import.
- Simulink, `.slx`, or `.mlapp` compatibility.
- Full OpenFOAM solver coverage or a full OpenFOAM UI.
- Full MATLAB proprietary toolbox compatibility.
- Industrial certification, accuracy, compliance, or production CAE claims.
- GUI direct subprocess solver execution.

## Success Path

The v0.1 happy path is:

1. Import: load or preview standard/exported input without proprietary software.
2. Configure: assign project metadata, units, materials, and demo parameters.
3. Run: prepare or execute only the bounded demo path allowed for that workflow.
4. Result: open structured ResultDataset and FigureDataset outputs.
5. Report: export an HTML report with input summary, assumptions, validation
   status, and reproducibility notes.

If a workflow cannot show this path transparently, it should be parked or
deferred rather than expanded into unbounded solver coverage.
