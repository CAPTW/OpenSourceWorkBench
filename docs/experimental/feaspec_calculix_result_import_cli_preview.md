# FEASpec CalculiX result import CLI preview

Status: experimental CLI preview implemented. This is preview only: no
numerical parser, no ResultDataset write, no ResultDataset persistence, no
solver execution, and no ProjectSchema mutation.

## Release Context

`v0.1.4-rc1` is a public prerelease. This CLI preview is post-release
development on `develop`; it does not edit the public release, mutate tags,
upload assets, close issues, install solvers, or run live optional validation.

## Command

```text
osw feaspec-calculix-result-import-preview --result-dir PATH
```

Options:

- `--result-dir PATH`: required explicit CalculiX result directory to inspect.
- `--format text|json`: output format, default `text`.
- `--strict`: exit with code `2` when the plan is blocked, unsupported, or
  still requires future numerical parsing.
- `--include-artifacts` / `--no-include-artifacts`: include or hide top-level
  artifact records, default include.
- `--include-diagnostics` / `--no-include-diagnostics`: include or hide
  top-level diagnostic records, default include.

The command inspects an already-existing directory only. It does not create
directories, copy artifacts, write manifests, persist a `ResultDataset`, or
start CalculiX.

## Underlying Model API

The CLI is a thin adapter over the FEASpec CalculiX result import model:

- `inspect_calculix_result_directory(result_dir)`
- `plan_calculix_result_import(result_dir)`
- `build_calculix_result_dataset_draft(plan)`
- `explain_calculix_result_import_plan(plan)`

The CLI does not add a write/import command and does not add a numerical result
parser. The in-memory draft returned in JSON remains a preview record with
`writes_files=false`.

## Text Output

The text preview states the safety boundary directly:

- preview only;
- no files written;
- no solver execution;
- no numerical parser;
- no ResultDataset persistence;
- issue `#8` remains open;
- external solvers are optional and not bundled.

## JSON Output

JSON output includes:

- `command`;
- `status`;
- `result_dir`;
- `artifact_count`;
- `artifacts`;
- `diagnostics`;
- `provenance`;
- `dataset_draft`;
- `parse_not_implemented`;
- `solver_execution_performed`;
- `files_written`;
- `status_summary`;
- `limitations`.

Top-level `solver_execution_performed` describes this preview command and is
always `false`. Source run metadata remains visible under `provenance` and the
`source_run_solver_execution_performed` convenience field.

When `.sta` or `.cvg` files are present, `status_summary` contains text-only
category counts, completion/failure text indicators, and bounded per-file
summaries. It does not parse numeric convergence values and does not write files.

## Exit Codes

- `0`: preview succeeded, including plans with warnings in non-strict mode.
- `1`: invalid arguments, missing path, unreadable path, or non-directory path.
- `2`: strict mode rejected a blocked, unsupported, or parse-not-implemented
  plan.

## Result Artifacts

The preview can classify:

- `run_metadata.json`;
- `*.manifest.json`;
- `*.diagnostics.json`;
- `stdout.txt`;
- `stderr.txt`;
- `.dat`;
- `.frd`;
- `.sta`;
- `.cvg`;
- `README_RUN_FIRST.txt`;
- `.inp`;
- other files as unsupported artifact references.

The `.dat` and `.frd` files are classified by path, suffix, size, and hash only.
The `.sta` and `.cvg` files may include text-only status summaries. There is no
numerical parser and no numeric convergence-value parsing capability.

## Safety Boundary

The CLI preview preserves these boundaries:

- no solver execution;
- no SolverAdapter integration;
- no runner integration;
- no external command invocation;
- no numerical parser;
- no numeric convergence parser;
- no ResultDataset write;
- no ResultDataset persistence;
- no ProjectSchema mutation;
- no VLM API;
- no provider credentials or API key fields;
- no bundled solver;
- no industrial certification;
- no release, tag, asset, or issue mutation.

## Relationship To Issue #8

Issue `#8` remains open until a prepared-machine live CalculiX validation gate
passes. This preview command does not validate local `ccx`, does not record
issue `#8` pass evidence, and does not close issue `#8`.

## Non-Goals

- No numerical parsing.
- No `.frd` parser.
- No `.dat` parser.
- No write-capable import command.
- No ResultDataset persistence.
- No solver execution.
- No certification.
- No industrial certification.
- No bundled solver.
- No SolverAdapter handoff.
- No runner handoff.
- No VLM API.
- No provider credentials.

## Next Implementation Slices

- `OSW-EXP-030_FEASPEC_RESULT_IMPORT_PARSER_DESIGN`
- `OSW-EXP-031_FEASPEC_RESULTDATASET_DRAFT_REVIEW`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
