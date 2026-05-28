# OpenFOAM Template Binding

`OSW-FUNC-016_OPENFOAM_TEMPLATE_BINDING` adds a bounded OpenFOAM path for
educational cavity and duct/internal-flow templates. It is not a full OpenFOAM
case editor or broad CFD workflow.

## Model

OpenFOAM models live in `osw.solvers.openfoam.model`:

- `OpenFOAMCaseRequest` and `OpenFOAMCaseResult` describe deterministic case
  generation.
- `OpenFOAMRunPolicy`, `OpenFOAMRunRequest`, and `OpenFOAMRunResult` describe
  explicit solver runs through the backend runner.
- `OpenFOAMResidualSummary` and `OpenFOAMResidualSeries` store parsed residual
  data in a report-friendly form.

All paths serialize as strings and importing the package does not require
OpenFOAM, PySide6, meshio, Gmsh, PyVista, SciPy, Octave, MATLAB, or Cantera.

## Templates

`default_cavity_request()` and `default_duct_request()` create serializable
requests. `generate_openfoam_case()` writes deterministic files:

- `0/U`
- `0/p`
- `constant/transportProperties`
- `constant/turbulenceProperties` for duct
- `system/blockMeshDict`
- `system/controlDict`
- `system/fvSchemes`
- `system/fvSolution`

The cavity template uses a moving lid, fixed walls, and empty front/back
patches. The duct template uses inlet velocity, outlet pressure, wall no-slip,
and empty front/back patches. Unsupported templates and missing duct roles
produce diagnostics instead of silent mapping.

## Runner

`OpenFOAMRunner` resolves `blockMesh`, `icoFoam`, and `simpleFoam` through
`ExecutablePathRegistry`. Resolution does not execute OpenFOAM. Explicit solver
runs use `ExternalCommandRunner`, argument lists, a case working directory,
stdout/stderr capture, timeouts, and artifact collection. Missing executables,
missing case directories, timeouts, nonzero return codes, and missing logs are
reported as structured diagnostics.

## Residuals And Results

`parse_openfoam_log()` and `parse_openfoam_case_logs()` extract common residual
lines such as:

```text
Solving for Ux, Initial residual = 0.001, Final residual = 1e-06, No Iterations 2
```

The parser handles Ux, Uy, Uz, p, and other field names. Missing, empty,
partial, or corrupt logs produce warnings/errors rather than tracebacks.
`openfoam_residuals_to_result_dataset()` bridges residual summaries into
`ResultDataset` tables for report generation.

## CLI

```powershell
python -m osw.cli openfoam-check
python -m osw.cli openfoam-write-case --template cavity --out-dir artifacts\openfoam\cavity
python -m osw.cli openfoam-write-case --template duct --inlet-velocity 3.0 --outlet-pressure 0 --out-dir artifacts\openfoam\duct
python -m osw.cli openfoam-run-case artifacts\openfoam\cavity --solver icoFoam --timeout 30
python -m osw.cli openfoam-parse-log tests\fixtures\openfoam\residual_simple.log
python -m osw.cli openfoam-results-summary tests\fixtures\openfoam
```

Case generation and log parsing do not require OpenFOAM installed. Run commands
are explicit and fail gracefully when the requested executable is missing.

## GUI

`OpenFOAMTemplateDialog` adds a small, theme-aware template surface with stable
object names. It can generate case files and, after explicit user action, call
`OpenFOAMRunner`. The GUI does not call subprocess APIs directly.

## Limitations

- No full OpenFOAM dictionary editor.
- No multiphase, reacting, turbulence-advisor, or broad solver coverage.
- No velocity/pressure field parser or PyVista visualization in this step.
- Generated cases are teaching templates and require engineering review before
  external use.

## Next Step

Next functional step: `OSW-FUNC-017_RESULT_VIEWER_DATASET_BINDING`.
