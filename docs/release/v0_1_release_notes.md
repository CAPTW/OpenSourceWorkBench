# v0.1 Release Notes

OpenSolver Workbench v0.1 is an internal release candidate for an open-source
educational and research Engineering Solver and Script Workbench. The
`v0.1.3-rc1` tag exists and a GitHub Release draft exists, but the release is
not published and has no binary installer, package publication, or release
assets.

OSW v0.1 is not industrial certified and is not a production CAE, CFD,
chemistry, CAD, MATLAB, Simulink, or OpenFOAM replacement. Results and demos are
intended for transparent workflow inspection, teaching, and research
prototyping.

## Highlights

- Frozen PySide6 desktop GUI shell with dark/light/system themes.
- ProjectSchema, UnitSystem, MaterialDB, ResultDataset, and FigureDataset
  contracts.
- Manifest-first plugin discovery, health diagnostics, local folder/ZIP install
  hardening, receipts, rejection/quarantine records, and managed uninstall.
- Backend runner diagnostics and explicit execution boundaries.
- Standard/exported mesh metadata bridge and optional meshio conversion.
- Bounded Gmsh primitive `.geo` generation.
- Preview-first MATLAB/Octave `.m` and `.mat` workflows.
- Optional GNU Octave runner for explicitly reviewed scripts.
- FigureDataset artifact normalization and report handoff.
- BoundaryCurve import/export from CSV/MAT/workspace-like data.
- Deterministic HTML report summaries and exports.
- CalculiX input deck generation, explicit runner binding, parser fixtures, and
  cantilever validation metric.
- OpenFOAM cavity/duct template generation and residual parser.
- Optional CoolProp property and Cantera 0D reactor examples.
- Unified ResultViewer, PlotViewer/TableViewer data surfaces, and FieldViewer
  metadata with optional PyVista scalar rendering.

## Install

Base source install:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m osw.cli doctor
```

GUI install:

```powershell
python -m pip install -e ".[gui]"
python -m osw.cli gui
```

Developer install:

```powershell
python -m pip install -e ".[dev]"
python -m pytest tests/unit -q
```

See:

- [Packaging and Release Docs](../32_packaging_release_docs.md)
- [Windows Install](../install/windows.md)
- [Linux Install](../install/linux.md)
- [Source and Development Install](../install/source_install.md)
- [Optional Dependencies](../install/optional_dependencies.md)

## CLI Quickstarts

```powershell
python -m osw.cli --help
python -m osw.cli doctor
python -m osw.cli project-demo-json --out artifacts\release\demo_project.json
python -m osw.cli project-validate artifacts\release\demo_project.json
python -m osw.cli plugins-health
python -m osw.cli report-export artifacts\release\demo_project.json --out artifacts\release\demo_report.html
python -m osw.cli result-catalog-inspect tests\fixtures\results\mixed_result_catalog.json
python -m osw.cli field-dataset-inspect tests\fixtures\fields\scalar_field_dataset.json
```

Generated outputs under `artifacts/*` are local runtime artifacts and should not
be committed.

## Optional Dependency Behavior

PySide6, PyVista, meshio, Gmsh, GNU Octave, SciPy, hdf5storage, h5py, CoolProp,
Cantera, CalculiX `ccx`, OpenFOAM, Matplotlib, Pillow, and PyYAML are optional
for v0.1 base use unless a specific workflow needs them. Missing optional
dependencies should produce diagnostics or skips rather than hidden success.

External executables are not bundled, downloaded, or required for base CLI
smoke or unit tests. GUI paths do not directly execute solver subprocesses.

## Known Limitations

- Educational/research prototype only; no industrial certification.
- No native SolidWorks, CATIA, NX, Creo, or other commercial CAD direct import.
- No Simulink, `.slx`, or `.mlapp` compatibility.
- No full OpenFOAM GUI/editor or broad solver coverage.
- No full MATLAB proprietary toolbox compatibility.
- No full CalculiX FRD field parser.
- No full OpenFOAM field parser.
- No vector glyphs, streamlines, time animation, or PDF report export.
- No process flowsheet simulator or DWSIM bridge.
- No plugin signing, remote plugin store/catalog, or dependency auto-install.
- GitHub Release remains a draft prerelease until an explicit publish gate.
- No package publication, installer, or release assets in this handoff step.

For full details, see [Known Limitations For v0.1](known_limitations_v0_1.md)
and [v0.1 Freeze Handoff](v0_1_freeze_handoff.md).
