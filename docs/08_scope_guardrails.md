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
- FEASpec documentation examples and synthetic benchmark seed fixtures that
  remain JSON/text-only and do not include generated solver outputs.
- Experimental FEASpec Python models and structural basic checks that load and
  serialize documented fixtures without adding a production/full physics
  validator, full ProjectSchema persistence, ProjectSchema mutation, solver
  adapter, VLM provider, or solver execution.
- Design-only FEASpec validator contract documentation that defines future
  diagnostics, severity taxonomy, human-review gates, solver handoff blockers,
  CalculiX-first compatibility, Abaqus optional/non-default handling, and
  benchmark readiness without implementing runtime validator behavior.
- Experimental FEASpec semantic validator reports that validate documented
  model fields, examples, and benchmark readiness without mesh generation,
  numerical physics validation, full ProjectSchema persistence, ProjectSchema
  mutation, solver export, VLM integration, or solver execution.
- Design-only FEASpec to ProjectSchema bridge documentation that defines
  approved-spec preconditions, validator-report requirements, explicit-unit
  mapping, provenance/evidence preservation, bridge diagnostics, unmapped-field
  reporting, and ProjectSchema extension needs without full ProjectSchema
  persistence or schema mutation.
- Experimental FEASpec to ProjectSchema bridge plan layer that accepts only
  approved FEASpec, requires a validator report with no blockers, returns a
  draft plan with diagnostics, extension needs, unmapped fields, and a
  ProjectSchema-compatible dictionary, and still does not persist ProjectSchema,
  mutate ProjectSchema, call solver adapters/exporters, or execute solvers.
- Design-only FEASpec to CalculiX case planning that defines a future
  CalculiX-first case-plan object, mesh requirements, mapping diagnostics, and
  issue `#8` separation without implementing a case generator, `.inp` writer,
  SolverAdapter/exporter call, live `ccx` validation, or solver execution.
- Experimental FEASpec to CalculiX case-plan model that consumes only approved
  FEASpec bridge plans, returns serializable planning records and `FC_*`
  diagnostics, reports missing explicit mesh topology, and still does not write
  `.inp` files, call solver adapters/exporters, mutate ProjectSchema, run
  `ccx`, call VLM APIs, or execute solvers.
- Design-only FEASpec to CalculiX `.inp` writer documentation that defines
  future writer preconditions, `FW_*` diagnostics, deterministic section
  ordering, provenance comments, golden fixture strategy, and issue `#8`
  separation without implementing a writer, generating `.inp` files, calling
  solver adapters/runners, mutating ProjectSchema, or executing solvers.
- Experimental FEASpec CalculiX `.inp` renderer implementation that renders
  deterministic text only from writer-ready case plans, writes only to
  caller-provided paths with overwrite protection, and still does not run
  `ccx`, call SolverAdapter or runner code, mutate ProjectSchema, validate
  issue `#8`, add VLM APIs, or add tracked generated `.inp` fixtures.
- Controlled FEASpec CalculiX `.inp` golden text fixtures under
  `tests/fixtures/feaspec/calculix_golden/` that lock deterministic renderer
  output without running CalculiX, producing solver outputs, validating issue
  `#8`, or claiming engineering correctness.

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
- FEASpec examples or benchmark seeds presented as solver-validated results.
- Treating FEASpec model parsing or basic checks as proof of physical validity,
  solver readiness, or industrial certification.
- Treating FEASpec validator design documentation as a production validator,
  ProjectSchema bridge, solver exporter, VLM provider, or solver execution
  capability.
- Treating FEASpec semantic validator reports as proof of physical correctness,
  generated solver cases, ProjectSchema conversion, VLM interpretation, or
  permission for unreviewed solver execution.
- Treating FEASpec to ProjectSchema bridge design as a source bridge
  implementation, ProjectSchema migration, SolverAdapter/export path, VLM
  provider, or permission to execute solvers.
- Treating FEASpec bridge plan output as full ProjectSchema persistence,
  ProjectSchema schema mutation, solver export, SolverAdapter handoff, VLM
  provider output, or permission to execute solvers.
- Treating FEASpec to CalculiX case planning as a case generator, `.inp`
  writer, SolverAdapter/exporter implementation, live `ccx` validation, or
  permission to execute solvers.
- Treating FEASpec to CalculiX case-plan model output as a solver deck,
  `.inp` writer handoff, SolverAdapter/exporter implementation, ProjectSchema
  mutation, live `ccx` validation, or permission to execute solvers.
- Treating FEASpec to CalculiX `.inp` writer design as an implemented writer,
  generated deck fixture, SolverAdapter/exporter implementation, live `ccx`
  validation, ProjectSchema mutation, or permission to execute solvers.
- Treating the FEASpec CalculiX `.inp` renderer as a CalculiX exporter,
  SolverAdapter integration, runner integration, live `ccx` validation,
  ProjectSchema mutation, physical validation, or permission to execute
  solvers.
- Treating FEASpec CalculiX `.inp` golden fixtures as solver outputs, live
  `ccx` validation, engineering-correctness evidence, or permission to execute
  solvers.

## Scope Drift Definition

Scope drift is any change that:

- turns a bounded demo into broad solver/product coverage;
- implies OSW is a MATLAB, ANSYS, Simulink, or commercial CAD replacement;
- adds direct GUI execution of external solvers before backend safety exists;
- adds automatic unreviewed solver execution from image or VLM output;
- treats an unapproved FEASpec candidate as solver-ready;
- turns FEASpec basic checks into solver execution, solver export, or physical
  validation without a separate gate;
- turns FEASpec validator design into runtime validation, ProjectSchema
  persistence, solver export, or solver execution without a separate gate;
- turns FEASpec semantic validation into mesh generation, numerical physics
  validation, full ProjectSchema persistence, ProjectSchema mutation, solver
  export, VLM API integration, or solver execution without a separate gate;
- turns FEASpec bridge design into ProjectSchema mutation, source conversion
  behavior, solver adapter/export behavior, VLM API integration, or solver
  execution without a separate gate;
- turns FEASpec bridge plan behavior into full ProjectSchema persistence,
  ProjectSchema schema mutation, solver deck generation, solver
  adapter/export behavior, VLM API integration, or solver execution without a
  separate gate;
- turns FEASpec to CalculiX case planning into case generation, `.inp` writing,
  SolverAdapter/export behavior, live `ccx` validation, dependency install, or
  solver execution without a separate gate;
- turns FEASpec to CalculiX case-plan model output into solver deck writing,
  solver adapter/export behavior, live `ccx` validation, ProjectSchema
  mutation, dependency install, or solver execution without a separate gate;
- turns FEASpec to CalculiX `.inp` writer design into writer implementation,
  generated `.inp` fixtures, solver adapter/export behavior, live `ccx`
  validation, dependency install, or solver execution without a separate gate;
- turns the FEASpec CalculiX `.inp` renderer into SolverAdapter/exporter
  behavior, runner behavior, live `ccx` validation, dependency install,
  generated tracked `.inp` fixtures, ProjectSchema mutation, or solver
  execution without a separate gate;
- turns FEASpec CalculiX golden `.inp` fixtures into solver outputs, live
  validation evidence, physical validation, runner behavior, dependency
  install, or solver execution without a separate gate;
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
