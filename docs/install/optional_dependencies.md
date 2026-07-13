# Optional Dependencies

OSW v0.1 keeps optional stacks behind extras, guarded imports, executable
diagnostics, and explicit user actions. Missing optional dependencies are
expected in base environments.

## Python Extras

| Extra | Packages | Needed for |
| --- | --- | --- |
| `gui` | PySide6 | Desktop GUI shell |
| `mesh` | meshio, gmsh | Live mesh import/export conversion and Gmsh Python support |
| `viz` | pyvista, matplotlib | Optional field rendering and plot/image surfaces |
| `mscript` | scipy, hdf5storage | MAT v4-v7.2 and HDF5-style MAT preview helpers |
| `chm` | cantera, CoolProp | Cantera reactor and CoolProp property examples |
| `thermo` | cantera, CoolProp | Alias for chemistry/property examples |
| `dev` | pytest, ruff | Tests and lint |
| `all` | all Python optional packages | Python optional stacks only |

Install selected extras:

```powershell
python -m pip install -e ".[gui,viz,mesh,mscript,chm]"
```

Matplotlib is included in the `viz` extra. Pillow is not a declared pyproject
extra in v0.1, but visual QA and image comparison helpers may use it when
available and should report a skip or diagnostic when it is absent.

## External Executables

| Tool | Optional use | Diagnostic command |
| --- | --- | --- |
| Gmsh | Real primitive mesh generation after `.geo` review | `python -m osw.cli gmsh-check` |
| GNU Octave | Explicit reviewed `.m` execution | `python -m osw.cli octave-check` |
| CalculiX `ccx` | Explicit CalculiX input deck execution | `python -m osw.cli calculix-check` |
| OpenFOAM | Explicit generated case execution outside base workflow | `python -m osw.cli openfoam-check` |

External tools are installed separately by the user. OSW v0.1 does not bundle
them, download them, or require them for base tests.

## Missing Dependency Meaning

Missing optional dependencies are valid diagnostics when the requested workflow
is optional. Examples:

- Missing PySide6 means GUI launch and screenshot capture are unavailable.
- Missing meshio means live mesh conversion is unavailable, while mesh format
  listing and metadata contracts remain import-safe.
- Missing PyVista means field metadata can be inspected but real rendering is
  skipped or replaced by a placeholder diagnostic.
- Missing SciPy/hdf5storage/h5py means live MAT preview may be unavailable.
- Missing CoolProp or Cantera means CHM calculations are unavailable.
- Missing Gmsh, Octave, `ccx`, or OpenFOAM means live external execution is
  unavailable.

Missing optional dependencies should not break base import, CLI help, plugin
manifest discovery, report summary generation, or unit tests.

## Tutorial Expectations

The first-run CLI and result dataset tutorials do not require optional solver
executables or optional science packages. The GUI tutorial requires PySide6 via
the `gui` extra. Optional backend tutorials and live validation issues should be
run only on machines where the corresponding tool is intentionally installed.

Useful diagnostics:

```powershell
python -m osw.cli gmsh-check
python -m osw.cli octave-check
python -m osw.cli calculix-check
python -m osw.cli openfoam-check
python -m osw.cli coolprop-check
python -m osw.cli cantera-check
```

Missing tools mean the matching optional workflow is unavailable; they do not
mean the base package is broken.

## Deferred v0.1 Paths

Full CalculiX FRD field parsing and full OpenFOAM field parsing remain deferred.
Bounded vector-field mapping and preview-only Mesh Viewer glyph controls/state
exist for compatible three-component point/cell arrays, but live PyVista glyph
rendering, arbitrary vector visualization, streamlines, tensor visualization,
time animation, and PDF export remain deferred. The preview requires optional
GUI/visualization components where applicable and makes no solver-validation,
scientific-validation, certification, or production-readiness claim.
