# FEASpec CalculiX exporter CLI write no-run

Status: experimental no-run write command. It writes local bundle only and
performs no solver execution.

Related release context: `v0.1.4-rc1` is a public prerelease. This CLI write
command is post-release development on `develop`; it does not edit the public
release, mutate tags, upload assets, close issues, install solvers, or run live
optional validation.

## Command

Command name:

```powershell
python -m osw.cli feaspec-calculix-export-write --feaspec examples\feaspec\cantilever_beam_approved.json --output-dir artifacts\feaspec-export
```

Required input is one of:

- `--feaspec PATH`: FEASpec JSON input. The command validates, bridges, creates
  a CalculiX case plan, and calls the no-run exporter.
- `--case-plan PATH`: experimental `FEASpecCalculiXCasePlan` JSON input for an
  already reviewed, writer-ready case plan.

Required output:

- `--output-dir PATH`: output directory for the no-run bundle. The directory
  must already exist unless `--create-dir` is supplied.

Options:

- `--target-solver calculix`: bounded to CalculiX.
- `--format text|json`: default `text`; JSON is intended for automation and
  tests.
- `--strict`: blocked exports still return exit code `2`; exported-with-warnings
  remains exit code `0` for this write boundary.
- `--basename NAME`: bundle basename, default `feaspec_calculix_case`.
- `--overwrite`: overwrite only the expected bundle target files.
- `--create-dir`: create the final output directory if its parent exists.

Exit codes:

- `0`: bundle exported or exported-with-warnings.
- `2`: export blocked by validation, planning, render, path, basename, or
  target-file diagnostics.
- `1`: unreadable input, invalid JSON, or command-line usage errors.

## Written Bundle

When export succeeds, the command writes exactly:

- `<basename>.inp`
- `<basename>.manifest.json`
- `<basename>.diagnostics.json`
- `README_RUN_FIRST.txt`

Blocked exports write no bundle files.

## Example Commands

Approved cantilever example, currently blocked because reviewed mesh and
element topology are not present:

```powershell
python -m osw.cli feaspec-calculix-export-write --feaspec examples\feaspec\cantilever_beam_approved.json --output-dir artifacts\feaspec-export --basename cantilever_case
```

Candidate example, blocked until human review approval is recorded:

```powershell
python -m osw.cli feaspec-calculix-export-write --feaspec examples\feaspec\cantilever_beam_candidate.json --output-dir artifacts\feaspec-export
```

JSON output:

```powershell
python -m osw.cli feaspec-calculix-export-write --feaspec examples\feaspec\invalid_load_target.json --output-dir artifacts\feaspec-export --format json
```

Successful synthetic ready case-plan export, for developer-maintained no-run
fixtures and tests:

```powershell
python -m osw.cli feaspec-calculix-export-write --case-plan path\to\ready_case_plan.json --output-dir artifacts\feaspec-export --basename ready_case
```

The `--case-plan` path is experimental. It is only for reviewed
`FEASpecCalculiXCasePlan` JSON data that already contains explicit nodes,
elements, materials, sections, boundary conditions, loads, static step metadata,
and output requests.

## JSON Output

JSON output is parseable and includes:

- `version`;
- `input_path`;
- `input_kind`;
- `output_dir`;
- `target_solver`;
- `export_status`;
- `files_written`;
- `solver_execution_performed: false`;
- `written_files`;
- `diagnostics`;
- `limitations`.

## Text Output

Text output reports:

- input path and kind;
- output directory;
- target solver;
- export status;
- written files when exported;
- diagnostics when blocked;
- `files_written`;
- `solver_execution_performed: false`;
- limitations.

The text output states that no solver execution occurred, external solvers are
optional and not bundled, and issue `#8` live CalculiX validation remains
separate.

## Safety Boundary

The CLI write command is a file-bundle boundary:

- no solver execution;
- no ccx;
- no SolverAdapter;
- no runner;
- no subprocess;
- no external command;
- no ProjectSchema mutation;
- no VLM provider or API call;
- no credential handling.

The command may read FEASpec or case-plan JSON and may call only the no-run
exporter API. It writes only to the explicit `--output-dir` when export
diagnostics permit it.

## Path Safety

The output directory is required. Missing directories block unless `--create-dir`
is provided. Existing target files block unless `--overwrite` is provided.
`--overwrite` overwrites only:

- `<basename>.inp`
- `<basename>.manifest.json`
- `<basename>.diagnostics.json`
- `README_RUN_FIRST.txt`

The basename must be a simple filename stem. Path separators, parent traversal,
drive-letter syntax, wildcards, empty names, and control characters are blocked.

## Relationship To Preview Command

`feaspec-calculix-export-preview` writes no files and creates no directories. It
is the diagnostic-first command for checking readiness and planned filenames.

`feaspec-calculix-export-write` writes local no-run bundle files only after the
user explicitly supplies `--output-dir` and the exporter reports success.

## Relationship To Issue #8

Issue `#8` remains live CalculiX `ccx` validation. This write command does not
validate installed `ccx`, does not run live optional validation, and does not
close issue `#8`.

Live CalculiX validation remains separate from the CLI write command.

The next boundary is design-only:
[FEASpec CalculiX result import and run gate design](feaspec_calculix_result_import_or_run_gate_design.md)
defines separate future gates for human review, installed-only run, result
import, and ResultDataset/report summary. It does not add a result importer,
run command, SolverAdapter/runner/subprocess call, solver execution, or live
issue `#8` validation.

## Non-Goals

- No solver execution.
- No bundled solver.
- No industrial certification.
- No production-readiness claim.
- No release edit, release publish, tag mutation, or asset upload.
- No Abaqus export.
- No topology optimization.

## Next Implementation Slices

- `OSW-EXP-018_FEASPEC_HUMAN_REVIEW_UI_DESIGN`
- `OSW-EXP-019_FEASPEC_CALCULIX_RESULT_IMPORT_MODEL`
- `OSW-EXP-020_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`
- `OSW-EXP-021_FEASPEC_CALCULIX_RESULT_IMPORT_CLI`
