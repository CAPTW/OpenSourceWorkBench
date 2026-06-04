# Quickstart

This quickstart gets OpenSolver Workbench running from source on Windows and
shows the lightweight CLI checks that should work before optional solver stacks
are installed.

## Windows Source Install

```powershell
git clone https://github.com/CAPTW/OpenSourceWorkBench.git
cd OpenSourceWorkBench
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[gui]"
```

Use the venv Python explicitly in commands below. This avoids importing another
checkout or a globally installed package.

## GUI Launch

```powershell
.\.venv\Scripts\python.exe -m osw.cli gui
```

If PySide6 is missing, install the GUI extra:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[gui]"
```

## CLI Smoke

```powershell
.\.venv\Scripts\python.exe -m osw.cli --help
.\.venv\Scripts\python.exe -m osw.cli plugins-health
.\.venv\Scripts\python.exe -m osw.cli project-demo-json --out artifacts\demo_project.json
.\.venv\Scripts\python.exe -m osw.cli project-validate artifacts\demo_project.json
.\.venv\Scripts\python.exe -m osw.cli report-summary artifacts\demo_project.json
```

Expected result:

- `--help` lists CLI commands.
- `plugins-health` reports local plugin manifests or says none were found.
- `project-demo-json` writes a HeatSink_Flow demo ProjectSchema JSON file.
- `project-validate` may print preview warnings for demo scripts, but should not
  run solvers.
- `report-summary` prints the deterministic report section list.

Files under `artifacts/*` are ignored runtime outputs.

## Result And Field Inspection

```powershell
.\.venv\Scripts\python.exe -m osw.cli result-dataset-inspect tests\fixtures\fields\scalar_field_dataset.json
.\.venv\Scripts\python.exe -m osw.cli field-dataset-inspect tests\fixtures\fields\scalar_field_dataset.json
```

Expected result:

- ResultDataset summary for the tiny scalar-field fixture.
- Field dataset summary listing scalar and vector arrays.
- No external solver execution.

## Optional Dependency Diagnostics

Some commands intentionally report missing optional dependencies unless the
matching toolchain is installed:

```powershell
.\.venv\Scripts\python.exe -m osw.cli octave-check
.\.venv\Scripts\python.exe -m osw.cli coolprop-check
.\.venv\Scripts\python.exe -m osw.cli cantera-check
.\.venv\Scripts\python.exe -m osw.cli gmsh-check
.\.venv\Scripts\python.exe -m osw.cli calculix-check
.\.venv\Scripts\python.exe -m osw.cli openfoam-check
```

Expected result:

- Installed tools are reported with their resolved path.
- Missing tools produce explicit diagnostics.
- A missing optional executable is not a base install failure.

## Troubleshooting

- PySide6 missing: install `.[gui]` and rerun the GUI command.
- Optional solver missing: install that solver separately, then rerun the
  specific `*-check` command. OSW does not bundle Gmsh, CalculiX, OpenFOAM, or
  GNU Octave.
- Octave missing: `mscript-preview` and `mscript-scan` still work for `.m`
  safety review; `mscript-run` needs GNU Octave.
- SciPy or hdf5storage missing: MAT inspection commands may return a dependency
  diagnostic. Install `.[mscript]` for MAT workflows.
- GitHub Release state is unrelated to local execution. A draft release page
  does not change source install, CLI smoke, GUI launch, or optional dependency
  behavior.

## Next Reading

- [Tutorials](tutorials/README.md)
- [First CLI Walkthrough](tutorials/first_cli_walkthrough.md)
- [Result Dataset Walkthrough](tutorials/result_dataset_walkthrough.md)
- [First GUI Walkthrough](tutorials/first_gui_walkthrough.md)
- [Examples](../examples/README.md)
- [Examples Index](examples.md)
- [Known Limitations For v0.1](release/known_limitations_v0_1.md)
- [Optional Dependencies](install/optional_dependencies.md)
