# Known Limitations For v0.1

OSW v0.1 is an educational and research prototype. It records transparent demo
workflows and validation evidence, but it does not certify engineering results
or replace expert review.

## Product Boundary

- Not industrial certified.
- Not a production CAE, CFD, chemistry, or safety-critical decision system.
- Not a MATLAB, ANSYS, Simulink, OpenFOAM, SolidWorks, CATIA, NX, or Creo
  clone.
- No native commercial CAD direct import.
- No Simulink, `.slx`, or `.mlapp` compatibility.
- No full OpenFOAM GUI/editor or broad solver coverage.
- No process flowsheet simulator or DWSIM bridge.

## Solver And Script Boundary

- GUI paths do not directly execute solver subprocesses.
- External execution is explicit, optional, and routed through backend runner
  boundaries where implemented.
- `.m` and `.mat` workflows are preview-first. Importing a script must not run
  arbitrary code.
- Script safety scanning is heuristic and does not prove code is safe.

## Optional Dependencies

PySide6, PyVista, meshio, Gmsh, GNU Octave, SciPy, hdf5storage, h5py, CoolProp,
Cantera, CalculiX `ccx`, OpenFOAM, Matplotlib, and Pillow are optional for v0.1
base install. Missing optional dependencies should produce diagnostics or skips.
Pillow is used only by helper/image workflows when present; it is not mandatory
for the base package.

## Plugin Trust Boundary

Local plugin folder and ZIP install is manifest-first and rejects unsafe archive
paths before extraction, but v0.1 does not provide plugin signing, a remote
plugin store/catalog, dependency auto-install, or automatic trust elevation.
Installed plugin code should run only later through explicit plugin-system
workflows, not during install or health checks.

## Deferred Work

- Full CalculiX FRD parser.
- Full OpenFOAM field parser.
- Vector glyphs, streamlines, and time animation.
- PDF export.
- Binary desktop installers.
- Remote plugin store, plugin signing, and dependency auto-install.

For the broader standing limitations document, see
[Known Limitations](../known_limitations.md).
