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

The defining user experience is:

```text
Import -> Configure -> Run or prepare -> Result -> Report
```

`Run` is deliberately narrow in v0.1. It may mean preparing a case, loading a
fixture result, running a small pure-Python demo, or documenting the external
command a user can run outside the GUI. It does not mean broad GUI-triggered
external solver execution.

## v0.1 Demos

| Demo | Scope | Expected evidence |
| --- | --- | --- |
| 1. Empty project | Create/open the smallest valid OSW project. | Project metadata, default units, validation status. |
| 2. STEP import preview | Inspect standard exported geometry metadata. | Preview summary before project mutation. |
| 3. Mesh import preview | Load mesh metadata through meshio-facing contracts. | Mesh dimensions, fields/groups, validation notes. |
| 4. Gmsh meshing template | Prepare a small educational meshing workflow. | Template parameters and generated-case plan, not broad meshing UI. |
| 5. CalculiX cantilever | Demonstrate a linear static case boundary. | Prepared case or fixture result with assumptions and limits. |
| 6. OpenFOAM cavity or duct template | Demonstrate a bounded CFD template. | Case template summary, not full OpenFOAM solver coverage. |
| 7. Cantera/CoolProp basics | Demonstrate thermo/property data flow. | Small property or reactor result with units and source notes. |
| 8. MATLAB/Octave script figure preview | Inspect `.m`/`.mat` output safely. | Previewed figure/table data without auto-running arbitrary code. |

## v0.1 Must Support

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

## v0.1 Must Not Support

- Native SolidWorks, CATIA, NX, Creo, or other commercial CAD direct import.
- Simulink, `.slx`, or `.mlapp` compatibility.
- Full OpenFOAM solver coverage or a full OpenFOAM UI.
- Full MATLAB proprietary toolbox compatibility.
- OSW v0.1 does not claim industrial certification, engineering accuracy,
  compliance, or production CAE readiness.
- GUI direct subprocess solver execution.
- Nonlinear contact/plasticity unless explicitly deferred as future work.
- Full ANSYS Workbench-style workflow cloning.

## Success Path

Every accepted v0.1 workflow must show this path:

1. Import: load or preview standard/exported input without proprietary software.
2. Configure: assign project metadata, units, materials, and demo parameters.
3. Run: prepare or execute only the bounded demo path allowed for that workflow.
4. Result: open structured ResultDataset and FigureDataset outputs.
5. Report: export an HTML report with input summary, assumptions, validation
   status, and reproducibility notes.

If a workflow cannot show this path transparently, it should be parked or
deferred rather than expanded into unbounded solver coverage.

## Scope Test

Before accepting work into v0.1, ask:

- Does it help one of the eight demos reach Import -> Configure -> Run ->
  Result -> Report?
- Can it run or be inspected without commercial software?
- Are heavy dependencies optional for bootstrap and unit tests?
- Does it make no industrial certification claim and avoid native commercial
  CAD, Simulink, `.mlapp`, full OpenFOAM UI, and GUI direct solver execution?
- Is the validation evidence honest about educational/research limits?
