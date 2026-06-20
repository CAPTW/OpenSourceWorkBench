# FEASpec CalculiX result import CLI preview

Status: experimental CLI preview implemented. This is preview only: bounded
minimal `.dat` candidate summaries, no broad numerical parser, no ResultDataset
write, no ResultDataset persistence, no solver execution, and no ProjectSchema
mutation.

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
- `build_calculix_result_dataset_draft_mapping(plan)`
- `summarize_calculix_result_dataset_draft_mapping(mapping)`
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
- `dataset_draft_mapping`;
- `dataset_draft_mapping_summary`;
- `parse_not_implemented`;
- `solver_execution_performed`;
- `files_written`;
- `status_summary`;
- `dat_section_summary`;
- `dat_minimal_parse_summary`;
- `frd_block_summary`;
- `limitations`.

Top-level `solver_execution_performed` describes this preview command and is
always `false`. Source run metadata remains visible under `provenance` and the
`source_run_solver_execution_performed` convenience field.

When `.sta` or `.cvg` files are present, `status_summary` contains text-only
category counts, completion/failure text indicators, and bounded per-file
summaries. It does not parse numeric convergence values and does not write files.

When `.dat` files are present, `dat_section_summary` contains section kind
counts, section counts, unsupported/unknown counts, and bounded per-file
summaries. It does not extract numeric values, does not extract tables, does not
infer units, and does not write files.

When `.dat` files contain explicit scalar candidates or small delimited table
candidates with explicit units, `dat_minimal_parse_summary` contains bounded
candidate counts and parsed-preview value counts. This summary is still
preview-only: no free-form `.dat` parsing, no `.frd` parsing, no unit
inference, no ResultDataset persistence, and no solver execution.

When `.frd` files contain recognizable block metadata, `frd_block_summary`
contains block counts, block kind counts, deferred reference candidate counts,
unsupported/unknown counts, and bounded per-file summaries. This summary is
still preview-only: no numerical field parser, no node or element value arrays,
no mesh reconstruction, no visualization arrays, no unit inference, no
ResultDataset persistence, and no solver execution.

When parser and scanner summaries are present, `dataset_draft_mapping` and
`dataset_draft_mapping_summary` expose the in-memory mapping from artifacts,
status summaries, bounded `.dat` scalar/table candidates, deferred `.frd`
references, provenance, diagnostics, and limitations into a future
ResultDataset-shaped draft. These payloads remain preview-only: no
ResultDataset persistence, no file writes, no additional numerical parsing, no
mesh reconstruction, no unit inference, and no solver execution.

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

The `.dat` and `.frd` files are classified by path, suffix, size, and hash. The
`.sta` and `.cvg` files may include text-only status summaries. The `.dat` files
may include section-only heading/span/snippet summaries and bounded minimal
scalar/table candidate summaries. There is no broad numerical parser and no
numeric convergence-value parsing capability. The `.frd` files may include
block metadata summaries and deferred reference candidates, but no field values,
node or element value arrays, or mesh topology are reconstructed.
[FEASpec CalculiX `.dat` minimal parser design](feaspec_calculix_result_dat_minimal_parser_design.md)
records the bounded `.dat` subset;
the implemented
[FEASpec CalculiX `.dat` metadata section scanner](feaspec_calculix_result_dat_section_scanner.md)
does not extract numeric values itself, and the implemented
[FEASpec CalculiX `.dat` minimal parser](feaspec_calculix_result_dat_parser.md)
parses only explicit scalar/table candidates with explicit unit context.
The implemented
[FEASpec CalculiX `.frd` block metadata scanner](feaspec_calculix_result_frd_block_scanner.md)
defines `.frd` block-reference metadata only; the current preview still does
not parse `.frd` field values or reconstruct meshes.
[FEASpec CalculiX ResultDataset draft mapping](feaspec_calculix_result_dataset_draft_mapping.md)
documents the in-memory mapping from these summaries into a future
ResultDataset draft boundary without persistence.
[FEASpec CalculiX ResultDataset write design](feaspec_calculix_result_dataset_write_design.md)
documents the future reviewed persistence boundary. The current CLI still has
no write/import command, no `--output` persistence mode, and no file writes.
[FEASpec CalculiX ResultDataset write plan](feaspec_calculix_result_dataset_write_plan.md)
documents the implemented in-memory planning model for future persistence; it
is not wired as a CLI write mode and still performs no actual file writes.
[FEASpec CalculiX ResultDataset schema payload model](feaspec_calculix_result_dataset_schema.md)
documents the implemented in-memory schema payload bundle for future
ResultDataset, manifest, diagnostics, provenance, and review README records. It
is not a write-capable import CLI, has no `--output` persistence mode, writes no
files, persists no ResultDataset, and executes no solver.

## Safety Boundary

The CLI preview preserves these boundaries:

- no solver execution;
- no SolverAdapter integration;
- no runner integration;
- no external command invocation;
- no broad numerical parser;
- no numeric convergence parser;
- no free-form numeric value extraction;
- no free-form table extraction;
- no ResultDataset write;
- no ResultDataset persistence;
- no write-capable import CLI;
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

- No broad numerical parsing.
- No `.frd` numerical field parser.
- No free-form `.dat` parser.
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
- `OSW-EXP-033_FEASPEC_RESULT_PARSER_DAT_MINIMAL_DESIGN`
- `OSW-EXP-035_FEASPEC_RESULT_PARSER_DAT_MINIMAL_IMPLEMENTATION`
- `OSW-EXP-036_FEASPEC_RESULT_PARSER_FRD_BLOCK_SCANNER_DESIGN`
- `OSW-EXP-037_FEASPEC_RESULT_PARSER_FRD_BLOCK_SCANNER_IMPLEMENTATION`
- `OSW-EXP-038_FEASPEC_RESULT_IMPORT_RESULTDATASET_DRAFT_MAPPING`
- `OSW-EXP-039_FEASPEC_RESULT_IMPORT_DATASET_WRITE_DESIGN`
- `OSW-EXP-042_FEASPEC_RESULT_IMPORT_DATASET_WRITE_IMPLEMENTATION`
- `OSW-EXP-043_FEASPEC_RESULT_IMPORT_WRITE_CLI_PREVIEW_ONLY`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
