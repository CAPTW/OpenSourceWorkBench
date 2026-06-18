# FEASpec CalculiX result import model

Status: experimental result import model implemented. Result import model only:
no numerical parser, no ResultDataset write, and no solver execution.

## Release Context

`v0.1.4-rc1` is a public prerelease. This implementation is post-release
development on `develop`; it does not edit the public release, mutate tags,
upload assets, install solvers, close issues, or run live optional validation.

## Package Path

The implementation lives under the experimental FEASpec package:

- `src/osw/experimental/feaspec/calculix_result_import.py`
- `src/osw/experimental/feaspec/calculix_result_diagnostics.py`

The public package exports the result import model API from
`osw.experimental.feaspec`.

## Public API

- `inspect_calculix_result_directory(result_dir)`
- `plan_calculix_result_import(result_dir)`
- `build_calculix_result_dataset_draft(plan)`
- `explain_calculix_result_import_plan(plan)`

The API accepts an explicit result directory and returns pure Python data
objects. It does not add a CLI command and does not write files.

## Inspected Inputs

The model inspects already-existing files only:

- run metadata: `run_metadata.json`
- export manifest: `*.manifest.json`
- export diagnostics: `*.diagnostics.json`
- `stdout.txt`
- `stderr.txt`
- `.dat`
- `.frd`
- `.sta`
- `.cvg`
- `README_RUN_FIRST.txt`
- `.inp`

The `.dat`, `.frd`, `.sta`, and `.cvg` files are classified by path, suffix,
size, and SHA-256 only. Numerical result content is not parsed.

## Artifact Classification

Artifact kinds are:

- `inp`
- `export_manifest`
- `export_diagnostics`
- `readme`
- `run_metadata`
- `stdout`
- `stderr`
- `dat`
- `frd`
- `sta`
- `cvg`
- `other`

Unsupported files are preserved as artifact references and reported with
diagnostics.

## Diagnostics

The result import model uses these `FI_*` diagnostics:

- `FI_RESULT_DIR_MISSING`
- `FI_RESULT_DIR_NOT_DIRECTORY`
- `FI_MANIFEST_MISSING`
- `FI_RUN_METADATA_MISSING`
- `FI_EXPORT_MANIFEST_MISSING`
- `FI_UNSUPPORTED_FILE`
- `FI_PARSE_NOT_IMPLEMENTED`
- `FI_PARTIAL_IMPORT`
- `FI_NO_PRIMARY_RESULT`
- `FI_RUN_FAILED`
- `FI_RUN_TIMED_OUT`
- `FI_SOLVER_NOT_EXECUTED`
- `FI_PROVENANCE_INCOMPLETE`
- `FI_FORBIDDEN_PATH`
- `FI_RESULT_DATASET_WRITE_FORBIDDEN`

Missing directories and non-directory paths block import planning. Missing
metadata, missing primary result artifacts, run failures, timeouts, unsupported
files, and parse-not-implemented cases remain visible as non-hidden
diagnostics.

## ResultDataset Draft

`build_calculix_result_dataset_draft` builds an in-memory draft with:

- artifact references;
- field references for deferred `.frd` handling;
- scalar summary placeholders, populated only when metadata already supplies
  scalar summary data;
- table placeholders;
- provenance from run metadata and export manifest;
- limitations;
- diagnostics.

The draft is a pure data object. It is not a persisted `ResultDataset`, creates
no parent directories, overwrites nothing, and performs no ResultDataset write.

## Safety Boundary

The model preserves these boundaries:

- no solver execution;
- no subprocess path;
- no SolverAdapter integration;
- no runner integration;
- no numerical parser;
- no file writes;
- no ProjectSchema mutation;
- no VLM API;
- no provider credentials or API key fields;
- no release mutation;
- no asset upload or delete;
- no tag mutation;
- no issue mutation.

## Relationship To Installed-Only Run Gate

The model consumes artifacts that may be produced by the installed-only run
gate, including `run_metadata.json`, logs, and CalculiX runtime outputs. It does
not run `ccx`, retry a failed run, install CalculiX, or infer that a run is
trusted. A run with timeout or nonzero exit remains a partial import plan with
diagnostics.

## Relationship To Issue #8

Issue `#8` remains open until a prepared-machine live validation gate passes.
This result import model does not validate local `ccx`, does not record issue
`#8` pass evidence, and does not close issue `#8`.

## Non-Goals

- No numerical parsing.
- No `.frd` parser.
- No `.dat` parser.
- No ResultDataset persistence.
- No certification.
- No industrial certification.
- No bundled solver.
- No SolverAdapter handoff.
- No runner handoff.
- No CLI command.
- No VLM API.
- No provider credentials.

## Next Implementation Slices

- `OSW-EXP-029_FEASPEC_RESULT_IMPORT_CLI_PREVIEW`
- `OSW-EXP-030_FEASPEC_RESULT_IMPORT_PARSER_DESIGN`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
