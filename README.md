# OpenSolver Workbench

OpenSolver Workbench (OSW) is an open-source educational and research
Engineering Solver & Script Workbench. The v0.1 goal is a safe, inspectable
desktop workbench for demonstrating solver workflows, data exchange, validation,
and report generation.

## v0.1 Scope

- PySide6 desktop GUI architecture.
- Plugin/add-in contracts for solvers and importers.
- Project schema, units, material database, result dataset, and figure dataset.
- Standard/exported CAD, CAE, CFD, and chemistry formats.
- `meshio`, Gmsh, PyVista, and Matplotlib based workflows.
- CalculiX linear static demo.
- OpenFOAM cavity/duct template demo.
- Cantera and CoolProp basic demos.
- MATLAB/Octave `.m` and `.mat` preview-first workflow.
- HTML reports, validation matrix, and golden tests.

The eight planned v0.1 demos are empty project, STEP import preview, mesh import
preview, Gmsh meshing template, CalculiX cantilever, OpenFOAM cavity/duct
template, Cantera/CoolProp basics, and MATLAB/Octave figure preview.

The expected workflow is Import -> Configure -> Run or prepare a bounded demo
run -> inspect Result/Figure data -> export an HTML report with validation notes.

## Non-Goals

OSW v0.1 is not a MATLAB, ANSYS, Simulink, SolidWorks, CATIA, NX, or Creo clone.
It does not claim industrial certification. It does not support native
commercial CAD import, Simulink or `.mlapp`, full OpenFOAM coverage, full MATLAB
toolbox compatibility, or GUI-triggered direct subprocess solver execution.

## Quick Start

```powershell
python -m pip install -e .[dev]
python -m osw.cli --version
python -m osw.cli doctor
pytest tests/unit -q
ruff check src tests
```

Optional stacks are grouped as extras:

- `.[gui]` for PySide6.
- `.[mesh]` for mesh import and Gmsh-facing work.
- `.[viz]` for PyVista and Matplotlib.
- `.[thermo]` for Cantera and CoolProp.
- `.[mscript]` for `.mat` preview support.

No external solver is executed by the bootstrap skeleton.
