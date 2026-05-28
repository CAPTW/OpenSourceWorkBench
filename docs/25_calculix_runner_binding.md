# CalculiX Runner Binding

`OSW-FUNC-014_CALCULIX_RUNNER_BINDING` binds prepared CalculiX `.inp` decks to
safe `ccx` execution through the existing OSW backend runner.

## Scope

The runner supports explicit execution of an existing `.inp` deck only. It:

- resolves `ccx` through `ExecutablePathRegistry` without executing it;
- copies the deck into an isolated case directory by default;
- runs `ccx jobname` through `ExternalCommandRunner`;
- captures stdout and stderr;
- enforces timeout policy;
- collects `.inp`, `.dat`, `.frd`, `.sta`, `.cvg`, `.12d`, `.log`, and backend
  runner summary artifacts;
- reports missing executable, missing input deck, timeout, nonzero return code,
  and missing artifact diagnostics.

The runner does not generate contours, run nonlinear/contact/plasticity
analyses, or bypass the backend runner. Parsed result summaries are handled by
`OSW-FUNC-015_CALCULIX_RESULT_PARSER` after artifacts already exist.

## CLI

```powershell
python -m osw.cli calculix-check
python -m osw.cli calculix-run-inp artifacts\calculix\cantilever.inp --case-dir artifacts\calculix\cantilever_run --timeout 10
python -m osw.cli calculix-run-demo --demo cantilever --out-dir artifacts\calculix\cantilever_run
```

`calculix-check` resolves `ccx` only. `calculix-run-inp` and
`calculix-run-demo` are explicit run commands. If `ccx` is missing, they return
a friendly missing-executable diagnostic.

## GUI

`CalculixDeckDialog` retains the existing deck preview/write workflow and adds a
`Run with CalculiX` action. The action writes the reviewed deck, then calls
`CalculiXRunner`; it does not construct subprocess calls in the GUI. The dialog
shows run status, case directory, stdout/stderr tail, artifacts, and diagnostics,
and `MainWindow` appends a compact run summary to the existing run monitor.

## Security Rules

- No `ccx` execution occurs during import, plugin health, deck preview, or deck
  generation.
- `ccx` runs only from an explicit `CalculiXRunRequest`/runner call.
- Commands are argument lists and use `ExternalCommandRunner`.
- Runtime artifacts belong under temporary directories or `artifacts/calculix`
  and should not be committed.

## Parser Handoff

`OSW-FUNC-015_CALCULIX_RESULT_PARSER` can consume the artifacts recorded by
`CalculiXRunResult` and produce `CalculiXParsedResults` plus a lightweight
`ResultDataset`. This is a read-only post-processing step and does not change
runner execution behavior.

## Known Limitations

- Full FRD field parsing and contour visualization are deferred.
- The runner does not validate physical correctness of a CalculiX solution.
- Partial/missing result artifacts after a zero return code are warnings, not
  proof of solver correctness.

## Next Step

Next functional step: `OSW-FUNC-016_OPENFOAM_TEMPLATE_BINDING`.
