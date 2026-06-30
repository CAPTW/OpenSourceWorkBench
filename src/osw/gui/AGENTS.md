# GUI Agent Rules

This directory owns PySide6-facing desktop UI code.

- GUI code may present project trees, previews, validation messages, report
  entry points, and command-preparation summaries.
- GUI code must not directly call `subprocess` or launch external solvers,
  Octave, MATLAB, OpenFOAM, CalculiX, Gmsh, or similar tools.
- Route domain behavior through core contracts and plugin/service interfaces;
  do not import solver internals into widgets.
- Keep long-running or optional-heavy work out of the UI thread. If execution
  support is later approved, it must use a reviewed backend runner contract.
- Keep PySide6 imports local to GUI modules or optional GUI extras.
- User-facing text must not imply industrial certification, native commercial
  CAD support, full OpenFOAM coverage, or proprietary MATLAB compatibility.
