# First CLI Walkthrough

This walkthrough should work from a fresh source checkout without external
solver executables. It uses the repository virtual environment and writes only
ignored runtime outputs under `artifacts/tutorials/`.

## Windows Commands

Run from the repository root:

```powershell
.venv\Scripts\python.exe -m osw.cli --version
.venv\Scripts\python.exe -m osw.cli --help
.venv\Scripts\python.exe -m osw.cli project-demo-json --out artifacts\tutorials\first_cli_demo_project.json
.venv\Scripts\python.exe -m osw.cli project-validate artifacts\tutorials\first_cli_demo_project.json
.venv\Scripts\python.exe -m osw.cli report-summary artifacts\tutorials\first_cli_demo_project.json
```

Expected result:
- `--version` prints the installed OSW package version.
- `--help` lists commands such as `plugins-health`, `project-demo-json`,
  `project-validate`, `result-dataset-inspect`, and `gui`.
- `project-demo-json` writes a HeatSink_Flow demo ProjectSchema JSON file.
- `project-validate` validates the project without running solvers.
- `report-summary` prints deterministic report sections without writing an HTML
  file.

If the demo project contains script references, MATLAB/Octave preview warnings
are expected. Preview warnings are not script execution. OSW does not auto-run
`.m` files, shell commands, external solvers, or network calls during this
walkthrough.

## Linux/macOS Variant

Use the venv Python for your shell:

```bash
.venv/bin/python -m osw.cli --version
.venv/bin/python -m osw.cli --help
.venv/bin/python -m osw.cli project-demo-json --out artifacts/tutorials/first_cli_demo_project.json
.venv/bin/python -m osw.cli project-validate artifacts/tutorials/first_cli_demo_project.json
.venv/bin/python -m osw.cli report-summary artifacts/tutorials/first_cli_demo_project.json
```

## What This Does Not Do

- It does not run Gmsh, CalculiX, OpenFOAM, GNU Octave, MATLAB, or any external
  solver.
- It does not write committed files.
- It does not prove engineering accuracy or industrial certification.

## Next Step

Continue with [Result Dataset Walkthrough](result_dataset_walkthrough.md), then
try [First GUI Walkthrough](first_gui_walkthrough.md) if PySide6 is installed.
