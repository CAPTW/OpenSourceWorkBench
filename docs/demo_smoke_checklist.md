# v0.1 Demo Smoke Checklist

This checklist is for documentation-based v0.1 release readiness review. It
confirms that each tutorial has an inspectable path through:

```text
Import -> Configure -> Run or prepare -> Result -> Report
```

These checks do not require every optional dependency to be installed locally.
When a dependency or executable is missing, a clear diagnostic or documented skip
is acceptable evidence.

## Smoke Review Rules

- Record whether each demo passed documentation smoke, optional local executable
  smoke, or was skipped with a reason.
- Do not treat missing optional dependencies as release blockers unless the
  tutorial claims they are mandatory.
- Do not commit generated solver outputs, runtime directories, logs, reports, or
  binary artifacts from smoke runs.
- Use [Known Limitations](known_limitations.md) when interpreting solver,
  validation, optional dependency, and script execution results.
- Use [Tutorial Examples](tutorials.md) as the tutorial source of truth.

## Evidence Template

For each demo, record:

- reviewer and date;
- dependency status from `python -m osw.cli doctor`;
- tutorial link reviewed;
- documentation smoke result;
- optional local executable smoke result, if attempted;
- report or self-check evidence path;
- skip reason, if skipped;
- warnings or follow-up notes.

## 01_step_import

Purpose: verify that standard/exported geometry preview documentation is clear.

Expected user-facing workflow: choose a STEP, ASCII STL, or OBJ file; preview
metadata; review body and bounding-box information; accept the preview into the
project/report only after review.

Required/optional dependencies: base OSW install is enough for documentation
smoke. Optional CAD bridge behavior may be unavailable.

Smoke check steps:

- Open [examples/01_step_import](../examples/01_step_import/README.md).
- Confirm the tutorial explains standard/exported geometry preview.
- Confirm it says OSW v0.1 does not support native commercial CAD direct import.
- If a small local STL/OBJ fixture exists, run preview locally; otherwise record
  documentation smoke only.

Expected evidence: tutorial section review, optional geometry preview summary,
and any warning or diagnostic text.

Pass criteria: tutorial covers goal, prerequisites, steps, expected output, and
troubleshooting; no unsupported native-format claim is present.

Skip criteria: optional local preview can be skipped when no small neutral file
is available.

Known limitations or safety notes: v0.1 focuses on standard/neutral/exported
formats and metadata preview; complex CAD healing and proprietary feature
history are outside this smoke check.

## 02_mesh_import

Purpose: verify mesh import preview documentation and mesh metadata expectations.

Expected user-facing workflow: load a small standard mesh through the meshio
bridge, review `MeshInfo`, and optionally convert to VTU.

Required/optional dependencies: documentation smoke needs base OSW only. Optional
local executable smoke needs `meshio` and a small mesh fixture.

Smoke check steps:

- Open [examples/02_mesh_import](../examples/02_mesh_import/README.md).
- Confirm supported standard mesh formats and missing dependency diagnostics are
  documented.
- If `meshio` and a fixture are available, run `load_mesh_info()` and optional
  VTU conversion in a scratch directory.
- Confirm generated conversion artifacts are not staged.

Expected evidence: `MeshInfo` summary or a documented `meshio` skip.

Pass criteria: tutorial distinguishes supported formats, optional dependency
behavior, and reportable mesh metadata.

Skip criteria: optional local import can be skipped when `meshio` or a fixture is
not available.

Known limitations or safety notes: mesh quality and conversion checks are
lightweight review aids, not solver-specific convergence evidence.

## 03_gmsh_meshing

Purpose: verify bounded Gmsh primitive meshing documentation.

Expected user-facing workflow: choose a small plate or box primitive, configure
mesh size, generate `.msh` if Gmsh is installed, and optionally convert to VTU.

Required/optional dependencies: documentation smoke needs base OSW only.
Optional local executable smoke needs Gmsh and usually `meshio`.

Smoke check steps:

- Open [examples/03_gmsh_meshing](../examples/03_gmsh_meshing/README.md).
- Confirm the tutorial describes primitive-only meshing and mesh size control.
- If Gmsh is installed, generate output in a scratch directory and record the
  artifact path without committing it.
- If Gmsh is missing, record the missing dependency diagnostic as the smoke
  result.

Expected evidence: tutorial review, missing-Gmsh diagnostic, or scratch `.msh`
metadata.

Pass criteria: tutorial keeps Gmsh bounded to primitive educational templates
and does not imply broad CAD meshing coverage.

Skip criteria: optional local generation can be skipped when Gmsh is unavailable.

Known limitations or safety notes: generated meshes should stay small and should
not be committed unless deliberately curated as fixtures.

## 04_calculix_cantilever

Purpose: verify CalculiX linear static handoff and result-summary documentation.

Expected user-facing workflow: prepare a small mesh/material/BC/load case,
generate `.inp`, optionally run `ccx` outside the GUI path, parse a small result
summary, and report assumptions.

Required/optional dependencies: documentation smoke needs base OSW only.
Optional local executable smoke needs a local `ccx` executable and scratch case
directory.

Smoke check steps:

- Open [examples/04_calculix_cantilever](../examples/04_calculix_cantilever/README.md).
- Confirm the tutorial is limited to linear static educational handoff.
- Confirm missing material, missing support, and missing load diagnostics are
  described.
- If `ccx` is available, use the reviewed backend runner path only and keep
  generated outputs outside the repository.

Expected evidence: tutorial review, generated input deck summary, optional
runner diagnostic, or parsed fixture/result summary.

Pass criteria: tutorial separates case preparation from optional local solver
execution and includes validation/limitations language.

Skip criteria: optional local execution can be skipped when `ccx` is missing.

Known limitations or safety notes: OSW v0.1 does not claim industrial
certification or production structural validation.

## 05_openfoam_cavity

Purpose: verify OpenFOAM cavity and duct template documentation.

Expected user-facing workflow: generate cavity or duct template files in a
scratch directory, review patch names and generated dictionaries, and optionally
run OpenFOAM outside OSW.

Required/optional dependencies: documentation smoke needs base OSW only.
Optional local executable smoke needs a local OpenFOAM installation.

Smoke check steps:

- Open [examples/05_openfoam_cavity](../examples/05_openfoam_cavity/README.md).
- Confirm both cavity and duct template paths are described.
- Confirm patch-name warnings and scratch-output guidance are present.
- If OpenFOAM is installed, run any external command outside OSW and keep
  runtime outputs out of the repository.

Expected evidence: generated case file list, patch warning review, or documented
missing-OpenFOAM skip.

Pass criteria: tutorial clearly states template generation is not broad solver
coverage and does not provide a full OpenFOAM solver UI.

Skip criteria: optional local execution can be skipped when OpenFOAM is missing.

Known limitations or safety notes: generated templates are teaching artifacts;
users must review local solver version, mesh suitability, schemes, and boundary
conditions before external execution.

## 06_cantera_reactor

Purpose: verify bounded Cantera 0D reactor tutorial and reporting evidence.

Expected user-facing workflow: preview reactor configuration, explicitly run a
small local reactor only when Cantera and the mechanism are available, then
report species/time table and temperature/time plot placeholder.

Required/optional dependencies: documentation smoke needs base OSW only.
Optional local executable smoke needs Cantera and a mechanism such as
`gri30.yaml`.

Smoke check steps:

- Open [examples/06_cantera_reactor](../examples/06_cantera_reactor/README.md).
- Confirm SI inputs, mechanism dependency, and bounded time integration are
  documented.
- If Cantera is installed, run the smallest tutorial case locally and record the
  table summary.
- If Cantera or the mechanism is missing, record the friendly diagnostic.

Expected evidence: preview dictionary, species/time table, plot placeholder, or
missing dependency/mechanism diagnostic.

Pass criteria: tutorial distinguishes preview from explicit run and keeps the
workflow to a bounded 0D reactor.

Skip criteria: optional local execution can be skipped when Cantera or the
mechanism is unavailable.

Known limitations or safety notes: this is not a process simulator or combustion
CFD workflow.

## 07_coolprop_property

Purpose: verify bounded CoolProp property point and sweep-table documentation.

Expected user-facing workflow: configure fluid, pressure, temperature, and
outputs; calculate a property point; optionally create a small sweep table and
CSV attachment.

Required/optional dependencies: documentation smoke needs base OSW only.
Optional local executable smoke needs CoolProp.

Smoke check steps:

- Open [examples/07_coolprop_property](../examples/07_coolprop_property/README.md).
- Confirm explicit SI inputs and optional CoolProp diagnostics are documented.
- If CoolProp is installed, run a small water property point and record table or
  CSV text.
- If CoolProp is missing, record the friendly dependency diagnostic.

Expected evidence: property table, CSV text, plot placeholder, or missing
dependency diagnostic.

Pass criteria: tutorial keeps the workflow to property points and small sweeps.

Skip criteria: optional local calculation can be skipped when CoolProp is
missing.

Known limitations or safety notes: this is not a process flowsheet simulator.

## 08_mscript_figure

Purpose: verify MATLAB/Octave script preview and figure-capture safety language.

Expected user-facing workflow: import `.m` as a preview, review script/function
classification and safety findings, then explicitly run through the reviewed
Octave runner only when the user chooses to execute.

Required/optional dependencies: documentation smoke needs base OSW only.
Optional local executable smoke needs GNU Octave for execution and optional
Matplotlib for later viewing/report integration.

Smoke check steps:

- Open [examples/08_mscript_figure](../examples/08_mscript_figure/README.md).
- Confirm import/preview happens before execution.
- Confirm execution is user-triggered and routed through the reviewed runner
  path, not automatic import.
- If GNU Octave is available and the user approves, run in a temporary workspace
  and collect PNG/SVG paths without committing runtime outputs.

Expected evidence: preview model, safety findings, optional `FigureDataset`, or
missing-Octave diagnostic.

Pass criteria: tutorial clearly states `.m` import does not execute code and
script output remains untrusted until reviewed.

Skip criteria: optional execution can be skipped when GNU Octave is missing or
when the reviewer chooses preview-only smoke.

Known limitations or safety notes: OSW v0.1 does not support Simulink or
`.mlapp`; `.m` safety scanning is heuristic and does not prove a script is safe.
