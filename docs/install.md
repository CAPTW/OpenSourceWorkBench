# Installation Guide

This guide covers source installs for OSW v0.1. The recommended release path is
conda or source checkout plus editable Python install. PyInstaller or standalone
desktop packaging is not required for v0.1 release readiness; if it blocks the
release, use the source install path below.

OSW v0.1 is an educational and research prototype. It does not bundle external
solver runtimes, does not require commercial software, and does not claim
industrial certification. See [Known Limitations](known_limitations.md) for the
release boundary.

## Install Matrix

| Path | Use when | Installs optional solvers? |
| --- | --- | --- |
| Conda development environment | You want a reproducible local dev shell | No |
| Pip editable install | You already have Python 3.11+ | No |
| uv editable install | You use uv for fast local environments | No |
| Optional extras | You need GUI, mesh, visualization, chemistry, or script support | Python packages only |
| External solver tools | You choose to run local executable smoke checks | User-installed separately |
| Docker | You need an isolated experiment shell | Optional, not the v0.1 release path |

## Requirements

- Python 3.11 or newer.
- Git for source checkout.
- One of: conda, pip, or uv.
- No external solver executable is required for base install, CLI smoke, or unit
  tests.

Base install keeps heavy dependencies optional. PySide6, meshio, Gmsh, PyVista,
Cantera, CoolProp, SciPy, hdf5storage, GNU Octave, CalculiX, and OpenFOAM are
not required for bootstrap.

## Get The Source

```powershell
git clone <repository-url> OpenSolverWorkbench
cd OpenSolverWorkbench
```

Use the local repository path instead when you already have a checkout.

## Conda Install

The checked-in `environment.yml` installs the editable development package and
keeps optional solver stacks out of the base environment.

Windows PowerShell:

```powershell
conda env create -f environment.yml
conda activate osw-dev
python -m osw.cli --version
python -m osw.cli doctor
pytest tests/unit -q
```

Linux shell:

```sh
conda env create -f environment.yml
conda activate osw-dev
python -m osw.cli --version
python -m osw.cli doctor
pytest tests/unit -q
```

Update an existing environment after dependency metadata changes:

```powershell
conda env update -f environment.yml --prune
```

Use the same command in a Linux shell if conda is available.

## Pip Editable Install

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
python -m osw.cli doctor
pytest tests/unit -q
```

Linux shell:

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m osw.cli doctor
pytest tests/unit -q
```

PowerShell may need quotes around extras when a shell expands brackets:

```powershell
python -m pip install -e ".[dev]"
```

## uv Editable Install

Windows PowerShell:

```powershell
uv venv .venv --python 3.11
.\.venv\Scripts\Activate.ps1
uv pip install -e ".[dev]"
python -m osw.cli doctor
pytest tests/unit -q
```

Linux shell:

```sh
uv venv .venv --python 3.11
. .venv/bin/activate
uv pip install -e ".[dev]"
python -m osw.cli doctor
pytest tests/unit -q
```

## Optional Python Extras

Install optional extras only for workflows you intend to inspect or run.

```powershell
python -m pip install -e ".[gui]"
python -m pip install -e ".[mesh]"
python -m pip install -e ".[viz]"
python -m pip install -e ".[thermo]"
python -m pip install -e ".[mscript]"
```

Available extras:

| Extra | Purpose |
| --- | --- |
| `gui` | PySide6 desktop shell |
| `mesh` | meshio and Gmsh-facing mesh workflows |
| `viz` | PyVista and Matplotlib visualization surfaces |
| `thermo` / `chm` | Cantera and CoolProp examples |
| `mscript` | SciPy and hdf5storage for `.mat` preview support |
| `all` | All Python optional extras, still no external solver executables |

Optional extras do not install external solver programs such as `ccx`, OpenFOAM,
or GNU Octave.

## Optional External Solver Notes

External tools are local opt-in dependencies. Missing executables should produce
diagnostics or skipped optional tests, not base install failures.

### CalculiX

- OSW v0.1 uses CalculiX only for a bounded linear static educational handoff.
- Install `ccx` separately from a trusted package manager or the CalculiX
  project distribution for your platform.
- Ensure `ccx` is on `PATH` before running optional local executable smoke.
- Base tests and input deck generation do not require `ccx`.

Optional smoke:

```powershell
pytest tests/integration/test_calculix_runner_optional.py -q
```

### OpenFOAM

- OSW v0.1 generates cavity and duct template files. It is not a full OpenFOAM
  UI or solver coverage layer.
- Install OpenFOAM separately if you choose to run generated cases outside OSW.
- Linux installs usually require sourcing the OpenFOAM environment script before
  commands are available. Follow your OpenFOAM distribution instructions.
- Windows users commonly run OpenFOAM through WSL, a container, or a dedicated
  distribution. Keep generated runtime directories out of Git.

No base OSW test requires OpenFOAM execution.

### GNU Octave

- `.m` workflows are preview-first. Importing a script must not execute it.
- Install GNU Octave separately only if you choose to run the reviewed Octave
  runner explicitly.
- Ensure `octave` is on `PATH`.
- Script execution must be user-triggered and run through the reviewed runner
  path with timeout, stdout/stderr capture, and artifact handling.

Optional smoke:

```powershell
pytest tests/integration/test_octave_runner_optional.py -q
pytest tests/integration/test_mscript_figure_capture_optional.py -q
```

### Cantera

- Cantera is an optional Python dependency for bounded 0D reactor examples.
- Install through `python -m pip install -e ".[thermo]"` or a conda-forge
  environment if your platform needs compiled packages.
- A local mechanism such as `gri30.yaml` must be available for real examples.
- Missing Cantera or mechanisms should be reported clearly and may be a valid
  skip for optional smoke.

Optional smoke:

```powershell
pytest tests/integration/test_cantera_optional.py -q
```

### CoolProp

- CoolProp is an optional Python dependency for property points and sweep
  tables.
- Install through `python -m pip install -e ".[thermo]"` or conda-forge.
- Missing CoolProp should produce a friendly diagnostic and is not a base
  install failure.

## Docker Optional Note

Docker is optional for v0.1. This repository does not require a Docker image for
release readiness. If you create a local Dockerfile experiment, keep it simple,
install the base editable package, and do not bundle external solver runtimes or
commercial software. Prefer the conda or source install path for the v0.1
release.

## Local CI Verification

Use the same local-safe commands as the GitHub Actions workflow:

```powershell
python -m osw.cli --version
python -m osw.cli doctor
ruff check src tests
pytest tests/unit -q
pytest tests/integration -q -m "not external_solver"
pytest tests/golden -q
pytest tests/validation -q
python tools/qa/run_fast_qa.py
python tools/qa/check_scope_drift.py
python tools/qa/check_architecture_boundaries.py
python tools/qa/check_no_solver_artifacts_committed.py
```

Run external solver smoke only when the relevant local executable is installed:

```powershell
pytest tests/integration -q -m external_solver
```

## Troubleshooting

### `python` points to the wrong version

Use `py -3.11` on Windows or `python3.11` on Linux when creating the virtual
environment.

### Editable install cannot parse extras

Quote extras if your shell treats brackets specially:

```powershell
python -m pip install -e ".[dev]"
```

### `osw` command is not found

Use the module form from the active environment:

```powershell
python -m osw.cli doctor
```

Then verify the environment is activated and reinstall with `python -m pip
install -e ".[dev]"`.

### Optional dependency missing

Run:

```powershell
python -m osw.cli doctor
```

Install only the optional extra needed for the workflow. Missing optional
dependencies are expected in base environments.

### External executable missing

Install the external tool separately and ensure it is on `PATH`. Do not treat a
missing `ccx`, OpenFOAM command, or `octave` as a base install failure.

### Windows execution policy blocks activation

Activate the environment with a policy scoped to the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Linux OpenFOAM commands are unavailable

Source the OpenFOAM environment script for your distribution before running
OpenFOAM commands. Keep OpenFOAM runtime outputs, logs, and processor
directories outside tracked files.

### Generated artifacts appear in Git status

Do not commit solver runtime outputs, generated reports, logs, caches, or
temporary case directories. Run:

```powershell
python tools/qa/check_no_solver_artifacts_committed.py
```

before review or release readiness checks.
