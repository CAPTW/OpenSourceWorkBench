# Prepared environment plan for live optional validation

Date: 2026-06-06

Related release: `v0.1.4-rc1`

Release URL: https://github.com/CAPTW/OpenSourceWorkBench/releases/tag/v0.1.4-rc1

Version: `0.1.4rc1`

Related evidence:

- [Live optional validation matrix for v0.1.4-rc1](live_optional_validation_matrix_v0_1_4rc1.md)
- `OSW-VALID-002_LIVE_OPTIONAL_VALIDATION_MATRIX`

## Context

`v0.1.4-rc1` is a public prerelease. The `OSW-VALID-002` installed-only audit
classified all live optional validation issues `#6` through `#11` as
`skipped-missing` on the current machine because the relevant optional packages
or external solver commands were absent.

This document defines the prepared-machine requirements and rerun plan for
future validation gates. It does not install dependencies, does not install
external solvers, does not run live solver validation, does not mutate release
assets or tags, and does not close issues.

## Policy

- Live optional validation is installed-only inside OSW validation gates.
- Dependency installation must happen outside the validation gate and outside
  this repository workflow.
- External solver installation must happen outside the validation gate.
- Validation artifacts must be written only under `artifacts/validation/`.
- Release tags, GitHub Releases, and release assets must not be mutated by
  validation gates.
- Issues must not be closed without a separate explicit closure gate after
  passing evidence is available.
- Missing optional tools must be reported as `skipped-missing`, not hidden
  success.

## Environment Requirements

| Issue | Target | Required prepared-machine components | Optional helpful components |
| --- | --- | --- | --- |
| `#6` | Gmsh | Python `gmsh` module and/or `gmsh` executable on `PATH`. | `meshio` for mesh readback. |
| `#7` | GNU Octave | `octave` or `octave-cli` on `PATH`. | Headless-safe figure backend if figure capture is tested. |
| `#8` | CalculiX `ccx` | `ccx` executable on `PATH`. | Existing tiny OSW CalculiX fixture and parser checks. |
| `#9` | OpenFOAM | Initialized OpenFOAM shell environment, `foamVersion`, `blockMesh`, and one solver command such as `icoFoam`, `simpleFoam`, or `foamRun`. | Small tutorial cavity/template fixture. |
| `#10` | CoolProp / Cantera | Python `CoolProp` package and Python `cantera` package. | Built-in Cantera mechanism such as `gri30.yaml`. |
| `#11` | PyVista / meshio | Python `meshio` package and Python `pyvista` package. | `vtk` if required by PyVista; stable offscreen rendering if screenshots are tested. |

## Validation Commands And Pass Criteria

Commands below are future prepared-machine guidance. Do not run them from this
planning gate.

| Issue | Version/import command | Minimal live smoke | Expected artifact | Pass condition |
| --- | --- | --- | --- | --- |
| `#6` Gmsh | `gmsh --version` and/or `.venv\Scripts\python.exe -c "import gmsh; print(gmsh.__version__)"` | Generate a tiny `.geo` square/triangle mesh under `artifacts/validation/live_optional/<step>/gmsh/`. | Nonzero `.msh` plus stdout/stderr/status JSON. | Version/import succeeds, mesh is generated, and optional readback succeeds when `meshio` is present. |
| `#7` Octave | `octave --version` or `octave-cli --version` | Run a safe synthetic script under `artifacts/validation/live_optional/<step>/octave/` that only computes known numeric output. | Script, stdout/stderr, status JSON, optional figure artifact. | Command exits 0, expected numeric output is present, no arbitrary user script is executed. |
| `#8` CalculiX | `ccx -v` or `ccx -h` | Run an existing tiny cantilever fixture if available; otherwise stop at version/import and classify partial. | Solver log, `.dat`/`.sta` or parser summary when a run is performed. | Tiny case completes and expected output files parse, or version-only evidence is explicitly classified `partial`. |
| `#9` OpenFOAM | `foamVersion` plus command discovery for `blockMesh` and solver command. | Run a smallest existing OSW/OpenFOAM template only in an initialized environment with short timeout. | Case directory under validation artifacts, logs, status JSON. | Environment is initialized, mesh command and tiny solver/template smoke succeed, and logs are summarized. |
| `#10` CoolProp / Cantera | `.venv\Scripts\python.exe -c "import CoolProp, cantera; print('ok')"` | CoolProp finite water/air property lookup; Cantera finite gas state/equilibrium smoke using a built-in mechanism. | Property JSON/status JSON. | Imports succeed and computed values are finite and physically plausible for the bounded smoke case. |
| `#11` PyVista / meshio | `.venv\Scripts\python.exe -c "import meshio, pyvista; print('ok')"` | meshio tiny mesh write/read; PyVista simple mesh construction without requiring an interactive display. | Tiny mesh file, status JSON, optional offscreen screenshot. | meshio round-trip succeeds; PyVista mesh object is constructed; screenshot is optional and may be skipped with a headless diagnostic. |

## Closure Criteria

`passed` requires:

- required component installed and version/import check succeeds;
- minimal live smoke runs in a bounded temp artifact directory;
- expected output artifacts exist and are nonzero where applicable;
- no blocking warnings or unexplained failures remain.

`passed-with-warnings` applies when:

- a live smoke passes; and
- only non-blocking limitations remain, such as optional paired readback or
  screenshot support missing.

`partial` applies when:

- a tool/package is discovered and version/import succeeds; but
- the full live smoke cannot be safely completed in the prepared environment.

The issue remains open when:

- status is `skipped-missing`;
- status is `skipped-not-configured`;
- status is `failed`;
- status is only `partial` and the issue acceptance criteria require a live
  run;
- evidence has not yet passed a separate explicit closure gate.

## Prepared-Machine Profiles

| Profile | Purpose | Components |
| --- | --- | --- |
| Profile A: Python science packages only | Issue `#10` property/chemistry validation. | `CoolProp`, `cantera`. |
| Profile B: mesh/visualization | Issues `#6` readback and `#11` mesh/visualization validation. | `gmsh` Python module or executable, `meshio`, `pyvista`, `vtk` if required. |
| Profile C: structural solver | Issue `#8` CalculiX validation. | `ccx` executable and tiny OSW CalculiX fixture support. |
| Profile D: CFD/OpenFOAM | Issue `#9` OpenFOAM validation. | Initialized OpenFOAM environment with `foamVersion`, `blockMesh`, and a solver command. |
| Profile E: full optional validation workstation | Full `#6`-`#11` rerun. | Profiles A through D plus GNU Octave. |

## Safety Constraints

- Use short timeouts.
- Write only to `artifacts/validation/`.
- Do not access network resources.
- Do not run arbitrary user scripts.
- Do not run long solver jobs.
- Do not write into user project directories.
- Do not commit generated runtime artifacts.
- Do not claim certification, production CAE accuracy, or broad solver
  coverage.

## Known Limitations

- `v0.1.4-rc1` remains a prerelease.
- The Windows portable ZIP is unsigned.
- There is no MSI installer or code signing.
- External solvers are not bundled.
- VFEA remains experimental scope documentation and is not implemented.
- Live optional validation is environment-specific.

## Next Steps

- Rerun `OSW-VALID-002_LIVE_OPTIONAL_VALIDATION_MATRIX` or a successor
  installed-only validation gate on a prepared machine.
- Use one closure gate per issue, or a clearly scoped multi-issue closure gate,
  only after passing evidence exists.
- Continue `OSW-EXP-002_FEASPEC_IR_DESIGN` separately if maintainers prefer
  experimental design work over live optional validation.
