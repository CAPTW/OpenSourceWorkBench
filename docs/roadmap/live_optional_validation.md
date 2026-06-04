# Live Optional Validation

Live optional validation collects evidence on machines that already have
optional solver, science, and visualization dependencies installed. It is not a
base-install requirement and it is not an industrial certification plan.

OpenSolver Workbench remains educational/research software. External solvers and
optional scientific packages are not bundled unless explicitly documented.
Users must validate engineering results independently.

## Validation Targets

| Target | Evidence to collect | Missing behavior |
| --- | --- | --- |
| Gmsh | Version, primitive `.geo` generation, optional mesh generation smoke. | Report missing executable or package diagnostic. |
| GNU Octave | Version, bounded `.m` runner smoke, figure output path if available. | Report missing executable diagnostic. |
| CalculiX `ccx` | Version, bounded fixture or dry-run compatible smoke if configured. | Keep fixture-backed parser/deck checks as base evidence. |
| OpenFOAM | Version/environment summary and bounded residual log parser evidence. | Keep template generation and parser fixtures as base evidence. |
| CoolProp | Version and small water property point. | Report optional dependency missing. |
| Cantera | Version and bounded reactor setup or mechanism availability diagnostic. | Report optional dependency missing. |
| SciPy MAT support | SciPy/hdf5storage/h5py availability and MAT info smoke. | Report MAT dependency limitation. |
| PyVista/meshio | Import/version checks and small mesh metadata/render diagnostic. | Report visualization or mesh dependency limitation. |

## Validation Rules

- Run only tools already installed on the local validation machine.
- Do not install external solvers as part of the validation command.
- Use bounded timeouts for any executable smoke.
- Put generated evidence under `artifacts/validation/`.
- Do not commit runtime validation artifacts.
- Do not claim certification, production readiness, or broad solver accuracy.
- Keep base unit tests and CLI smoke independent of these optional dependencies.

## Expected Output

Each validation run should produce an evidence report with:

- installed/missing matrix;
- command and version evidence;
- pass/fail/skip diagnostics;
- generated artifact paths under `artifacts/validation/`;
- limitations and environment assumptions;
- explicit note that the evidence is educational/research validation only.
