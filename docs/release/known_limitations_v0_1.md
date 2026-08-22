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

- **Native report-asset availability resolution is unsupported (`DEFERRED_RETAINED`).** Without an authorized resolver, the manager and report bridge continue to represent typed `external_absolute` and `project_relative` references as `unresolved_no_resolver` placeholders. “Relink selected screenshot…” performs point-in-time selected-file and suffix checks and, only after explicit confirmation plus post-confirmation file and stale-target revalidation, replaces one in-memory Project screenshot record: `external_absolute` remains `external_absolute`, while `project_relative` becomes `external_absolute`. Relink does not perform typed native resolution; the runtime descriptor still has no `effective_path`, the report bridge supplies no usable `image_path`, and the placeholder remains. Saving the Project is separate and explicit. These compatibility checks add no durable claim of existence, readability, locality, containment, link safety, provider silence, sandboxing, race-free consumption, authenticity, malware safety, or production readiness, and make no negative finding about the target. Legacy or unmarked compatibility behavior is separate, may perform filesystem checks, and is not certified provider-silent.
- This status documents an unsupported and unscheduled native boundary; it does
  not remove a previously supported native feature. See [Report Asset Runtime
  Path Native Deferral](../experimental/report_asset_runtime_path_native_deferral.md).
- Full CalculiX FRD parser.
- Full OpenFOAM field parser.
- Bounded vector-field mapping and preview-only Mesh Viewer glyph
  controls/state are implemented for compatible three-component point/cell
  arrays. Live PyVista glyph rendering, arbitrary vector visualization,
  streamlines, tensor visualization, and time animation remain unsupported;
  the preview requires optional GUI/visualization components where applicable
  and is not solver validation, scientific validation, certification, or
  production readiness.
- PDF export.
- Binary desktop installers.
- Remote plugin store, plugin signing, and dependency auto-install.
- The historical public `v0.1.5-rc1` GitHub prerelease has five attached
  Release assets: a wheel, an sdist, an unsigned Windows portable ZIP,
  `SHA256SUMS.txt`, and `release_asset_manifest.json`. GitHub's automatic
  source archives are separate from that five-asset count. The current
  published public `v0.1.5-rc2` GitHub prerelease has four attached Release
  assets: a wheel, an sdist, `SHA256SUMS.txt`, and
  `release_asset_manifest.json`. Release-asset `quick` and `full-static`
  verification establish only their stated identity and static-consistency
  result, report `release_readiness=false`, and do not establish
  installability, launch behavior, runtime correctness, engineering
  correctness, regulated-use suitability, or publication readiness. No MSI,
  code signing, Python package-index publication, bundled-solver distribution,
  stable-production status, broader engineering assurance, or future packaging
  format is claimed; those remain separately gated.

For the broader standing limitations document, see
[Known Limitations](../known_limitations.md).
