# CalculiX Result Parser

`OSW-FUNC-015_CALCULIX_RESULT_PARSER` parses already-collected CalculiX
artifacts into report-friendly summaries. It does not run `ccx` and does not
attempt full FRD field visualization.

## Scope

The parser supports v0.1 linear static result summaries:

- `.dat` best-effort max displacement and max von Mises stress extraction;
- `.sta` step, increment, completion, warning, and error summaries;
- stdout/stderr/log warning and error summaries through the generic log parser;
- `.frd` artifact detection with an explicit deferred full-field parser
  diagnostic;
- `CalculiXParsedResults` serialization and `ResultDataset` summary bridge;
- cantilever beam validation using `F L^3 / (3 E I)`.

## Result Dataset Bridge

`calculix_results_to_result_dataset()` emits a lightweight `ResultDataset` with
scalar summaries:

- `max_displacement`
- `max_von_mises_stress`

The dataset carries parser status, diagnostics, and artifact references in
metadata so report generation can show the result evidence without requiring
mesh topology or FRD field arrays.

## CLI

```powershell
python -m osw.cli calculix-parse-dat tests\fixtures\calculix\results\simple_success.dat
python -m osw.cli calculix-parse-sta tests\fixtures\calculix\results\simple_success.sta
python -m osw.cli calculix-results-summary tests\fixtures\calculix\results
python -m osw.cli calculix-validate-cantilever tests\fixtures\calculix\results --force 100 --length 1 --elastic-modulus 2.1e11 --second-moment-area 8.333333333e-10
```

All parser commands are read-only with respect to solver execution. They do not
require `ccx`, PyVista, meshio, Gmsh, SciPy, Octave, or MATLAB.

## GUI And Reports

`CalculixDeckDialog` includes a safe `Parse Results` action that consumes the
last `CalculiXRunResult` or a selected case directory. It displays max
displacement, max stress, and parser diagnostics, and `MainWindow` appends a
compact parse summary to the existing run monitor. Report generation can consume
the bridged `ResultDataset` and show the scalar summaries in result tables.

## Limitations

- Full FRD displacement/stress field parsing is deferred.
- Parsed scalar summaries are evidence for review, not proof of physical
  validity.
- Nonlinear, contact, plasticity, modal, thermal, and coupled result
  interpretation are out of scope for v0.1.
- Missing, empty, corrupt, or partial artifacts produce diagnostics instead of
  raw tracebacks.

## Next Step

Next functional step: `OSW-FUNC-016_OPENFOAM_TEMPLATE_BINDING`.
