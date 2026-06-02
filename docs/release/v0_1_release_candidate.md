# v0.1 Release Candidate

This page records the OSW v0.1 internal release-candidate handoff. It is not a
final public release announcement, tag push, binary installer, or package
publication.

## Candidate Label

v0.1 release candidate / internal handoff.

Current package metadata: `0.1.2`.

## Feature Coverage

- Frozen PySide6 GUI visual shell.
- ProjectSchema, UnitSystem, MaterialDB, ResultDataset, and FigureDataset
  contracts.
- Manifest-first Plugin Manager, local plugin install hardening, and plugin
  health diagnostics.
- External runner diagnostics through backend/service boundaries.
- Mesh bridge and optional meshio import/export paths.
- Gmsh primitive `.geo` generation and optional explicit mesh generation.
- MATLAB/Octave `.m` preview and safety scan.
- Optional GNU Octave runner.
- FigureDataset artifact normalization.
- MAT reader and workspace summaries.
- BoundaryCurve import/export.
- HTML report generator and report preview binding.
- CalculiX input deck, runner binding, result parser, and validation metric.
- OpenFOAM cavity/duct templates and residual parser.
- CHM CoolProp and Cantera optional adapters.
- Unified ResultViewer and FieldViewer metadata panel.

## Release Gate Status

`OSW-FUNC-020_RELEASE_VALIDATION_GATE` passed with warnings on 2026-06-02.
`OSW-FUNC-021_PACKAGING_RELEASE_DOCS` adds install, optional dependency, and
release-candidate documentation on top of that evidence.

## Warnings

- Optional live dependencies were missing locally during the release gate:
  meshio, PyVista, SciPy/hdf5storage, Gmsh, GNU Octave, CoolProp, Cantera, and
  external solver executables.
- PySide6 was available locally for the release-gate GUI screenshot smoke.
- Untracked desktop duplicate `* (1)` files are present and can disrupt raw
  recursive Ruff or Pytest collection if included.
- The local venv had a stale duplicate editable `.pth` pointing at another
  checkout; validation commands pinned `PYTHONPATH` to the intended checkout.
- Full CalculiX FRD field parsing and full OpenFOAM field parsing are deferred.
- Vector glyphs, streamlines, time animation, and PDF export are deferred.

## Public Release Boundary

Do not publish this candidate as a final public release until the later
freeze/handoff and maintainer-controlled tag/push gates are complete.

## Links

- [Packaging and Release Docs](../32_packaging_release_docs.md)
- [Optional Dependencies](../install/optional_dependencies.md)
- [Known Limitations](known_limitations_v0_1.md)
- [Release Checklist](../10_release_checklist.md)
- [Validation Matrix](../04_validation_matrix.md)
