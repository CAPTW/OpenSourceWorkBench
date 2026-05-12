# Scope Guardrails

These guardrails define what OSW v0.1 may do, what it must not do, and when a
request should stop, park, or defer.

## In Scope

- PySide6 GUI shell and workflow previews.
- Plugin/add-in contracts for importers, solvers, scripts, post-processing, and
  reports.
- ProjectSchema, UnitSystem, MaterialDB, ResultDataset, and FigureDataset.
- Standard/exported CAD, CAE, CFD, chemistry, `.m`, and `.mat` workflows.
- meshio, Gmsh, PyVista, and Matplotlib integration points.
- Bounded educational demos for CalculiX, OpenFOAM templates, Cantera,
  CoolProp, and MATLAB/Octave figure preview.
- HTML reports, validation matrix, golden tests, and release checklist.

## Out of Scope

- Native SolidWorks, CATIA, NX, Creo, or other commercial CAD direct import.
- Simulink, `.slx`, or `.mlapp` support.
- Full OpenFOAM solver coverage or a full OpenFOAM UI.
- Full MATLAB proprietary toolbox compatibility.
- Industrial certification, compliance, accuracy, or production CAE claims.
- GUI direct subprocess solver execution.
- Proprietary solver automation that requires licensed commercial software.

## Scope Drift

Scope drift is any change that:

- turns a bounded demo into broad solver/product coverage;
- implies OSW is a MATLAB, ANSYS, Simulink, or commercial CAD replacement;
- adds direct GUI execution of external solvers before backend safety exists;
- makes heavy dependencies mandatory for bootstrap or unit tests;
- accepts proprietary native formats instead of standard/exported formats;
- adds user-facing claims that exceed validation evidence.

## Stop, Park, Defer

Stop immediately when a request introduces secrets, destructive Git operations,
industrial certification claims, GUI direct solver subprocess execution, or
native commercial CAD import.

Park when the idea is useful but needs architecture first, such as generalized
solver execution, remote job orchestration, or broad OpenFOAM case management.
Parked work needs a decision log entry before implementation.

Defer when the idea is plausible after v0.1 but not necessary for the eight
demos, such as richer material libraries, more import formats, GUI polish,
parallel solver execution, or advanced MATLAB compatibility.

## Success Criteria

For any v0.1 workflow, the acceptable path is:

1. Import: input is standard/exported or a local template.
2. Configure: units, materials, case options, and assumptions are visible.
3. Run: execution is absent, mocked, prepared, or bounded by the demo contract.
4. Result: outputs map into ResultDataset and FigureDataset concepts.
5. Report: HTML report records inputs, assumptions, validation, and limitations.

If a proposed feature cannot satisfy this path without expanding scope, it does
not enter v0.1.
