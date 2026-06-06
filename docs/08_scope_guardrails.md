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
- Planning-only experimental VFEA scope documentation when it preserves human
  review, validation gates, and no automatic solver execution.
- Planning-only FEASpec IR design that records candidate data, explicit units,
  evidence, diagnostics, human approval, and future ProjectSchema/SolverAdapter
  boundaries without implementing solver behavior.

## Out of Scope

- Native SolidWorks, CATIA, NX, Creo, or other commercial CAD direct import.
- Simulink, `.slx`, or `.mlapp` support.
- Full OpenFOAM solver coverage or a full OpenFOAM UI.
- Full MATLAB proprietary toolbox compatibility.
- Industrial certification, compliance, accuracy, or production CAE claims.
- GUI direct subprocess solver execution.
- Proprietary solver automation that requires licensed commercial software.
- Automatic unreviewed solver execution from image or VLM output.
- ProjectSchema or SolverAdapter handoff from an unapproved FEASpec candidate.
- Mandatory Abaqus dependency, Abaqus exporter implementation, or commercial
  solver requirement in VFEA planning.
- Topology optimization implementation inside the initial VFEA scope.

## Scope Drift Definition

Scope drift is any change that:

- turns a bounded demo into broad solver/product coverage;
- implies OSW is a MATLAB, ANSYS, Simulink, or commercial CAD replacement;
- adds direct GUI execution of external solvers before backend safety exists;
- adds automatic unreviewed solver execution from image or VLM output;
- treats an unapproved FEASpec candidate as solver-ready;
- makes Abaqus or another commercial solver mandatory;
- makes heavy dependencies mandatory for bootstrap or unit tests;
- accepts proprietary native formats instead of standard/exported formats;
- adds user-facing claims that exceed validation evidence.
- adds nonlinear contact/plasticity as in-scope work instead of future research;
- changes file IO, parser, or runner behavior without focused tests.

## Stop / Park / Defer Criteria

Use this table before implementing any ambiguous request.

| Decision | Criteria | Required action |
| --- | --- | --- |
| Stop | Secrets, destructive Git operations, industrial certification claims, GUI direct solver subprocess execution, native commercial CAD direct import, Simulink or `.mlapp`, full ANSYS clone, or full OpenFOAM UI. | Do not implement. Write a blocker or scope report. |
| Park | Useful idea, but architecture is missing or risk is high: generalized solver execution, remote jobs, broad OpenFOAM case management, native CAD research, or advanced runner design. | Add a decision/risk note and create a future Task Card. |
| Defer | Plausible after v0.1 but not needed for the eight demos: richer materials, more formats, GUI polish, parallel execution, nonlinear contact/plasticity, or advanced MATLAB compatibility. | Mark post-v0.1 and keep current diff focused. |
| Proceed | Directly supports one of the eight demos and can show Import -> Configure -> Run -> Result -> Report without violating non-goals. | Implement within the Task Card and add evidence. |

## Success Path Criteria

For any v0.1 workflow, the acceptable path is:

1. Import: input is standard/exported or a local template.
2. Configure: units, materials, case options, and assumptions are visible.
3. Run: execution is absent, fixture-backed, prepared, or bounded by the demo
   contract.
4. Result: outputs map into ResultDataset and FigureDataset concepts.
5. Report: HTML report records inputs, assumptions, validation, and limitations.

If a proposed feature cannot satisfy this path without expanding scope, it does
not enter v0.1.

## Required Review Questions

- Which v0.1 demo does this change unblock?
- Is any optional dependency made mandatory for bootstrap or unit tests?
- Does any user-facing text overclaim solver coverage, validation, or
  certification?
- Can the workflow be inspected before mutation or execution?
- Are generated artifacts, solver outputs, and reports either ignored or curated
  as fixtures?

## Automated Guard

Use `python tools/qa/check_scope_drift.py` to scan changed files and
`python tools/qa/check_scope_drift.py --text "<claim>"` to check a proposed
claim before editing documentation or UI text.
