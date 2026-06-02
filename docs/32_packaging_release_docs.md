# Packaging And Release Docs

`OSW-FUNC-021_PACKAGING_RELEASE_DOCS` records the v0.1 source-install,
optional-dependency, and release-candidate handoff path. It does not introduce
binary installers, Docker packaging, new solver behavior, or plugin install
hardening.

## Packaging Position

OSW v0.1 is distributed as a source checkout with editable Python installs.
Standalone desktop installers, PyInstaller bundles, Docker images, and public
release artifacts are deferred until later packaging gates.

The base package has no mandatory runtime dependencies beyond Python packaging
metadata. Heavy stacks remain optional extras in `pyproject.toml`:

| Extra | Purpose |
| --- | --- |
| `gui` | PySide6 desktop shell |
| `mesh` | `meshio` and Gmsh-facing Python package support |
| `viz` | PyVista and Matplotlib visualization paths |
| `mscript` | SciPy and hdf5storage MAT-file preview support |
| `chm` / `thermo` | Cantera and CoolProp examples |
| `dev` | pytest and Ruff |
| `all` | Python optional extras only; no external executables |

## Install Guides

- [Windows install](install/windows.md)
- [Linux install](install/linux.md)
- [Source and development install](install/source_install.md)
- [Optional dependencies](install/optional_dependencies.md)

## Quickstart

```powershell
python -m pip install -e .
python -m osw.cli --help
python -m osw.cli doctor
python -m osw.cli project-demo-json --out artifacts\release\demo_project.json
python -m osw.cli project-validate artifacts\release\demo_project.json
python -m osw.cli report-export artifacts\release\demo_project.json --out artifacts\release\demo_report.html
```

GUI quickstart:

```powershell
python -m pip install -e ".[gui]"
python -m osw.cli gui
```

## Release Candidate Status

The v0.1 release gate passed with warnings on 2026-06-02. Warnings were local
environment and repository hygiene issues: optional dependencies were missing,
untracked desktop duplicate `* (1)` files were present, and the local venv had a
stale duplicate editable `.pth` entry. See
[v0.1 Release Candidate](release/v0_1_release_candidate.md).

After `OSW-FUNC-023_V0_1_FREEZE_AND_HANDOFF`, this candidate is locally frozen
as an internal release candidate. It is still not a public final release until a
later maintainer-controlled tag/push gate explicitly approves the exact release
path.

## Plugin Install Note

`OSW-FUNC-022_PLUGIN_INSTALL_HARDENING` adds local folder/ZIP plugin install,
receipt, quarantine/rejection, uninstall, GUI, and CLI flows. It remains
local-only: no remote plugin store, plugin signing, dependency auto-install, or
plugin code execution during install/health is part of v0.1.

## Artifact Hygiene

Generated `artifacts/*` outputs and `.codex/reports/*` reports are runtime
evidence. Leave them untracked unless a later prompt explicitly promotes a small
curated fixture. Duplicate `* (1)` files should be cleaned manually in a later
hygiene step and must not be staged from this docs gate.
