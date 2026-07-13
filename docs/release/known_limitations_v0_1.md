# Known Limitations For v0.1

OSW v0.1 is an educational and research prototype. It records transparent demo
workflows and validation evidence, but it does not certify engineering results
or replace expert review.

## Product Boundary

- Not industrial certified.
- No industrial certification.
- Not a production CAE, CFD, chemistry, or safety-critical decision system.
- Not a MATLAB, ANSYS, Simulink, OpenFOAM, SolidWorks, CATIA, NX, or Creo
  clone.
- No native commercial CAD direct import.
- No native SolidWorks, CATIA, NX, Creo, or other commercial CAD direct import.
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
- No plugin signing, remote plugin marketplace, or dependency auto-install is
  provided in v0.1.

## Deferred Work

- **Native report-asset availability resolution is unsupported (`DEFERRED_RETAINED`).** OSW can preserve and lexically validate a typed path reference without accessing the filesystem, but it cannot establish existence, regular-file status, readability, locality, containment, link/reparse safety, provider silence, sandboxing, or race-free consumption. Typed unresolved references remain visible as placeholders and can be explicitly relinked. This limitation does not mean the referenced asset is missing, unreadable, unsafe, or nonexistent. Legacy compatibility behavior is separate and is not certified provider-silent.
- This status documents an unsupported and unscheduled native boundary; it does
  not remove a previously supported native feature. See [Report Asset Runtime
  Path Native Deferral](../experimental/report_asset_runtime_path_native_deferral.md).
- Full CalculiX FRD parser.
- Full OpenFOAM field parser.
- Vector glyphs, streamlines, and time animation.
- PDF export.
- Binary desktop installers.
- Remote plugin store, plugin signing, and dependency auto-install.
- Published GitHub Release assets, package artifacts, and binary installers for
  `v0.1.3-rc1`.

For the broader standing limitations document, see
[Known Limitations](../known_limitations.md).
