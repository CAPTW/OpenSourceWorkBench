# Windows Install

This page documents the Windows source-install path for OSW v0.1. It assumes
PowerShell and Python 3.11 or newer.

## Base Install

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
python -m osw.cli --help
python -m osw.cli doctor
```

Base install supports package import, CLI help, project validation, plugin
manifest discovery, report export, and local-safe unit tests. It does not
install PySide6, meshio, Gmsh, PyVista, SciPy, CoolProp, Cantera, Octave, `ccx`,
or OpenFOAM.

## GUI Install

```powershell
python -m pip install -e ".[gui]"
python -m osw.cli gui
```

If PySide6 is missing, GUI commands and tests should report a clear missing
optional dependency or skip. PySide6 absence is not a base install failure.

Offscreen screenshot smoke can be run when PySide6 is installed:

```powershell
python tools\ui\capture_main_window.py --theme dark --out artifacts\ui\windows_dark.png --offscreen --width 2048 --height 1152
```

## Development Install

```powershell
python -m pip install -e ".[dev]"
python -m pytest tests/unit -q
ruff check src tests
python tools\qa\run_fast_qa.py
```

Raw recursive Ruff or GUI tests can be disrupted by untracked desktop duplicate
`* (1).py` files. The v0.1 gate treats those as local hygiene warnings when they
are untracked and unstaged.

## Optional Research Install

```powershell
python -m pip install -e ".[gui,viz,mesh,mscript,chm]"
```

This installs optional Python packages where wheels are available. It still does
not install external solver executables.

## External Tool Paths

Optional tools are resolved through `PATH` or explicit executable configuration
inside OSW runner/plugin diagnostics. Use the check commands before attempting
optional workflows:

```powershell
python -m osw.cli gmsh-check
python -m osw.cli octave-check
python -m osw.cli calculix-check
python -m osw.cli openfoam-check
```

Missing tools should produce diagnostics. Do not treat missing Gmsh, Octave,
`ccx`, or OpenFOAM as a base install failure.

## Portable ZIP

The GitHub Release may include a Windows portable ZIP for convenience. It is not
an MSI installer, not code-signed, and not a stable production release. Extract
it to a user-writable folder and run `OpenSolverWorkbench.exe --help` before
trying GUI or optional solver workflows.

External solver executables are not bundled in the portable ZIP. Verify
`SHA256SUMS.txt` and `release_asset_manifest.json` before running downloaded
assets. See [Windows Portable ZIP](../release/windows_portable_zip.md) for the
full user guide and troubleshooting notes.

## Activation Troubleshooting

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

If `osw` is not found, use module form from the active environment:

```powershell
python -m osw.cli doctor
```

If the wrong checkout is imported, inspect editable `.pth` files in
`.venv\Lib\site-packages`. A stale duplicate editable path was observed during
the v0.1 release gate and should be cleaned manually outside release docs work.
