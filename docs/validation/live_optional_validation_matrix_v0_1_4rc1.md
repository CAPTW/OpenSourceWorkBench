# Live optional validation matrix for v0.1.4-rc1

Date: 2026-06-06

Related release: `v0.1.4-rc1`

Release URL: https://github.com/CAPTW/OpenSourceWorkBench/releases/tag/v0.1.4-rc1

Release tag target: `f1683b441ab308fd65318ef6de3f1282549946a1`

Version: `0.1.4rc1`

Validation step: `OSW-VALID-002_LIVE_OPTIONAL_VALIDATION_MATRIX`

## Scope

This matrix records an installed-only live optional validation audit for the
public `v0.1.4-rc1` prerelease. The audit did not install dependencies, did not
install solver binaries, did not mutate the GitHub Release, did not upload
assets, did not push tags, and did not close issues.

The result is environment evidence only. It does not certify solver accuracy,
does not make optional dependencies mandatory, and does not change the base
package requirement that import, CLI smoke, and unit tests stay lightweight.

Generated local evidence is under:

- `artifacts/validation/live_optional/OSW-VALID-002/discovery.json`
- `artifacts/validation/live_optional/OSW-VALID-002/live_optional_validation_summary.json`
- `artifacts/validation/live_optional/OSW-VALID-002/*/status.json`

Those artifacts are runtime evidence and must not be committed.

## Summary

Overall status: `completed-with-warnings`

All live optional targets were classified as `skipped-missing` on this machine
because the required optional tools or packages were not installed.

| Issue | Target | Discovered state | Status | Local artifact | Recommendation |
| --- | --- | --- | --- | --- | --- |
| `#6` | Gmsh | Python `gmsh` module missing; `gmsh` executable missing. | `skipped-missing` | `artifacts/validation/live_optional/OSW-VALID-002/gmsh/status.json` | Keep open until Gmsh is available on a prepared validation machine. |
| `#7` | GNU Octave | `octave` and `octave-cli` executables missing. | `skipped-missing` | `artifacts/validation/live_optional/OSW-VALID-002/octave/status.json` | Keep open until GNU Octave is installed. |
| `#8` | CalculiX `ccx` | `ccx` executable missing. | `skipped-missing` | `artifacts/validation/live_optional/OSW-VALID-002/calculix/status.json` | Keep open until CalculiX `ccx` is installed. |
| `#9` | OpenFOAM | `foamVersion`, `blockMesh`, `icoFoam`, `simpleFoam`, and `foamRun` missing. | `skipped-missing` | `artifacts/validation/live_optional/OSW-VALID-002/openfoam/status.json` | Keep open until an initialized OpenFOAM environment is available. |
| `#10` | CoolProp / Cantera | Python `CoolProp` and `cantera` packages missing. | `skipped-missing` | `artifacts/validation/live_optional/OSW-VALID-002/coolprop_cantera/status.json` | Keep open until one or both optional science packages are installed. |
| `#11` | PyVista / meshio | Python `pyvista` and `meshio` packages missing. | `skipped-missing` | `artifacts/validation/live_optional/OSW-VALID-002/pyvista_meshio/status.json` | Keep open until optional visualization and mesh packages are installed. |

## Environment Discovery

The audit used `.venv\Scripts\python.exe`, which reported OSW version
`0.1.4rc1`.

Installed discovered packages relevant to the local GUI/runtime baseline:

- `PySide6` `6.11.1`
- `Pillow` `12.2.0`

Missing discovered optional packages included:

- `gmsh`
- `CoolProp`
- `cantera`
- `meshio`
- `pyvista`
- `vtk`
- `matplotlib`
- `scipy`
- `h5py`
- `hdf5storage`

Missing discovered optional executables included:

- `gmsh`
- `octave`
- `octave-cli`
- `ccx`
- `foamVersion`
- `blockMesh`
- `icoFoam`
- `simpleFoam`
- `foamRun`

## Per-Issue Notes

### Issue #6: Gmsh

No Gmsh live validation was run. The Python module and executable were both
missing, so the issue remains open for a prepared environment.

### Issue #7: GNU Octave

No GNU Octave live validation was run. Neither `octave` nor `octave-cli` was
available, so the issue remains open for a prepared environment.

### Issue #8: CalculiX `ccx`

No CalculiX live validation was run. The `ccx` executable was missing, so the
issue remains open for a prepared environment.

### Issue #9: OpenFOAM

No OpenFOAM live validation was run. The expected OpenFOAM commands and
initialized shell environment were absent, so the issue remains open for a
prepared environment.

### Issue #10: CoolProp / Cantera

No CoolProp or Cantera live validation was run. The optional Python packages
were missing, so the issue remains open for a prepared environment.

### Issue #11: PyVista / meshio

No PyVista or meshio live validation was run. The optional Python packages were
missing, so the issue remains open for a prepared environment.

## Known Limitations

- `v0.1.4-rc1` remains a prerelease.
- The Windows portable ZIP is unsigned and has no MSI installer.
- External solvers are not bundled.
- Optional solver and science validation is environment-dependent.
- VFEA remains experimental scope documentation and is not implemented.
- This evidence is not an industrial certification, compliance, or production
  CAE claim.

## Next Actions

- Keep issues `#6` through `#11` open while the required optional tools are
  missing.
- Rerun this matrix on a prepared validation machine with the relevant tools
  already installed.
- Use separate closure gates only for issues with passing live evidence.
