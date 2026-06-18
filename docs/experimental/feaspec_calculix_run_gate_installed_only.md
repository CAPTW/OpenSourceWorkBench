# FEASpec CalculiX installed-only run gate

Status: experimental installed-only run gate implemented. It performs no solver
install, no result import, and no certification.

## Release Context

`v0.1.4-rc1` is a public prerelease. This implementation is post-release
development on `develop`; it does not edit the public release, mutate tags,
upload assets, install solvers, close issues, or run live optional validation
by default.

## Package Path

The implementation lives under the experimental FEASpec package:

- `src/osw/experimental/feaspec/calculix_run_gate.py`
- `src/osw/experimental/feaspec/calculix_run_diagnostics.py`

The public package exports the installed-only run gate API from
`osw.experimental.feaspec`.

## CLI Command

Command name:

```powershell
python -m osw.cli feaspec-calculix-run-installed-only --export-dir artifacts\feaspec-export
```

The command defaults to dry-run mode. It inspects the export bundle, discovers
`ccx` if possible, reports readiness, writes no files, and starts no process.

Execute mode is explicit:

```powershell
python -m osw.cli feaspec-calculix-run-installed-only `
  --export-dir artifacts\feaspec-export `
  --execute `
  --confirm-run `
  --acknowledge-readme `
  --timeout-seconds 10 `
  --run-dir artifacts\feaspec-run
```

## Preconditions

Execute mode requires:

- an existing FEASpec CalculiX no-run export bundle;
- exactly one selected `.inp` input file;
- an export manifest that records `solver_execution_performed=false`;
- `README_RUN_FIRST.txt`;
- explicit `--confirm-run`;
- explicit `--acknowledge-readme`;
- `ccx` already installed on `PATH` or supplied through `--ccx`;
- a short timeout;
- an empty isolated run directory.

The run gate does not download, install, upgrade, bundle, or configure
CalculiX.

## Dry-Run Mode

Dry-run mode is the default. It:

- validates the export bundle;
- attempts installed `ccx` discovery;
- reports readiness and diagnostics;
- writes no files;
- creates no run directory;
- starts no process;
- keeps `solver_execution_performed=false`.

## Execute Mode

Execute mode requires all three authorization flags:

- `--execute`
- `--confirm-run`
- `--acknowledge-readme`

When those flags and all bundle/runtime checks pass, the gate copies the `.inp`
deck into the isolated run directory, starts only the discovered or explicit
`ccx` executable, waits with the bounded timeout, and captures the process
status. Nonzero exit and timeout are diagnostics, not hidden success.

## Outputs

Execute mode writes only runtime artifacts in the isolated run directory:

- `run_metadata.json`
- `stdout.txt`
- `stderr.txt`
- CalculiX runtime outputs if the installed `ccx` generates them

Runtime artifacts remain untracked. The run gate does not stage artifacts and
does not parse or import solver result files.

## Diagnostics

The run gate uses these `FR_*` diagnostics:

- `FR_RUN_NOT_AUTHORIZED`
- `FR_EXECUTE_FLAG_REQUIRED`
- `FR_CONFIRMATION_REQUIRED`
- `FR_README_NOT_ACKNOWLEDGED`
- `FR_CCX_MISSING`
- `FR_CCX_NOT_EXECUTABLE`
- `FR_EXPORT_BUNDLE_INVALID`
- `FR_MANIFEST_MISSING`
- `FR_INP_MISSING`
- `FR_README_MISSING`
- `FR_RUN_DIR_UNSAFE`
- `FR_RUN_DIR_NOT_EMPTY`
- `FR_TIMEOUT`
- `FR_NONZERO_EXIT`
- `FR_OUTPUT_MISSING`
- `FR_FORBIDDEN_PATH`
- `FR_METADATA_WRITE_FAILED`
- `FR_PROCESS_START_FAILED`

Blocking diagnostics prevent execution. Timeout and nonzero exits are captured
in logs and metadata.

## Relationship To Result Import

Result import is a separate future gate. This implementation does not add a
`.frd`, `.dat`, `.sta`, or `.cvg` parser, does not create a `ResultDataset`,
and does not summarize solver results. It records process metadata and logs
only.

## Relationship To Issue #8

Issue `#8` remains open unless a separate validation and closure gate confirms
live installed CalculiX evidence on a prepared machine. This run gate can
classify local `ccx` absence as `skipped-missing`, and a passing local run in
this development gate still does not close or comment on issue `#8`.

## Safety

The installed-only run gate preserves these boundaries:

- no solver install;
- no dependency install or upgrade;
- no release mutation;
- no tag push;
- no issue mutation;
- no asset upload or delete;
- no SolverAdapter;
- no broad runner integration;
- no GUI run button;
- no ProjectSchema mutation;
- no VLM API;
- no credential handling;
- no automatic unreviewed solver execution.

## Non-Goals

- No production certification.
- No industrial certification.
- No bundled solver.
- No Abaqus export.
- No topology optimization.
- No result import implementation.
- No release publication or release asset mutation.
- No issue `#8` closure.

## Next Implementation Slices

- `OSW-EXP-028_FEASPEC_RESULT_IMPORT_MODEL`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
- `OSW-MAINT-018_ISSUE_8_CALCULIX_VALIDATION_TRIAGE`
