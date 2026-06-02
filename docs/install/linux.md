# Linux Install

This page documents the Linux source-install path for OSW v0.1. Distribution
packages for external tools are optional and vary by distro.

## Base Install

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
python -m osw.cli --help
python -m osw.cli doctor
```

Base install is intended to remain light. It does not require GUI packages,
solver executables, chemistry packages, mesh conversion packages, or MAT-file
helpers.

## GUI Install

```sh
python -m pip install -e ".[gui]"
python -m osw.cli gui
```

Linux desktops may require system libraries for Qt/PySide6. Follow your
distribution's Qt/PySide6 package guidance if wheels alone are insufficient.

## Development Install

```sh
python -m pip install -e ".[dev]"
python -m pytest tests/unit -q
ruff check src tests
python tools/qa/run_fast_qa.py
```

For CI-style split suites:

```sh
python -m pytest tests/integration -q
python -m pytest tests/golden -q
python -m pytest tests/validation -q
```

## Optional Python Stacks

```sh
python -m pip install -e ".[gui,viz,mesh,mscript,chm]"
```

Compiled optional packages may be easier through conda-forge on some Linux
distributions. The checked-in `environment.yml` installs the base development
extra only; install optional extras explicitly when needed.

## External Solver Notes

Gmsh, GNU Octave, CalculiX `ccx`, and OpenFOAM are optional. Install them with
your distribution package manager, conda-forge, or upstream project guidance
only when you intend to run optional live workflows.

OpenFOAM often requires sourcing a shell setup script before commands such as
`blockMesh`, `icoFoam`, or `simpleFoam` are visible:

```sh
. /opt/openfoam*/etc/bashrc
python -m osw.cli openfoam-check
```

Keep generated case outputs, `processor*`, `postProcessing`, logs, and solver
scratch directories out of Git.

## Diagnostics

Use check commands to distinguish missing optional tools from source failures:

```sh
python -m osw.cli gmsh-check
python -m osw.cli octave-check
python -m osw.cli calculix-check
python -m osw.cli openfoam-check
python -m osw.cli coolprop-check
python -m osw.cli cantera-check
```

Missing optional dependencies should be clear diagnostics or skips, not import
crashes.
