# FEASpec CalculiX result import model

Status: experimental result import model implemented. Result import model only:
minimal bounded `.dat` candidate enrichment, no broad numerical parser, no
ResultDataset write, and no solver execution.

## Release Context

`v0.1.4-rc1` is a public prerelease. This implementation is post-release
development on `develop`; it does not edit the public release, mutate tags,
upload assets, install solvers, close issues, or run live optional validation.

## Package Path

The implementation lives under the experimental FEASpec package:

- `src/osw/experimental/feaspec/calculix_result_import.py`
- `src/osw/experimental/feaspec/calculix_result_diagnostics.py`
- `src/osw/experimental/feaspec/calculix_result_status_scanner.py`
- `src/osw/experimental/feaspec/calculix_result_dat_section_scanner.py`
- `src/osw/experimental/feaspec/calculix_result_dat_parser.py`
- `src/osw/experimental/feaspec/calculix_result_frd_block_scanner.py`
- `src/osw/experimental/feaspec/calculix_result_dataset_draft_mapping.py`

The public package exports the result import model API from
`osw.experimental.feaspec`.

## Public API

- `inspect_calculix_result_directory(result_dir)`
- `plan_calculix_result_import(result_dir)`
- `build_calculix_result_dataset_draft(plan)`
- `build_calculix_result_dataset_draft_mapping(plan)`
- `summarize_calculix_result_dataset_draft_mapping(mapping)`
- `explain_calculix_result_import_plan(plan)`

The API accepts an explicit result directory and returns pure Python data
objects. A separate preview-only CLI command now exposes this model for
inspection, but no write-capable import command exists and no files are written.

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
size, SHA-256, and parser metadata scans. `.sta` and `.cvg` files may also
carry text-only status summaries. `.dat` files may carry section-only heading,
span, kind, and snippet summaries, plus bounded minimal scalar/table candidate
summaries when explicit units are available. `.frd` files may carry block
metadata summaries and deferred reference candidates. Broad numerical result
content, free-form tables, `.frd` field data, and numeric convergence values are
not parsed.
[FEASpec CalculiX `.dat` minimal parser design](feaspec_calculix_result_dat_minimal_parser_design.md)
records the bounded `.dat` subset.
The implemented
[FEASpec CalculiX `.dat` metadata section scanner](feaspec_calculix_result_dat_section_scanner.md)
does not extract numeric values or table rows.
The implemented
[FEASpec CalculiX `.dat` minimal parser](feaspec_calculix_result_dat_parser.md)
parses only explicit scalar candidates and small delimited table candidates with
explicit unit context.
The implemented
[FEASpec CalculiX `.frd` block metadata scanner](feaspec_calculix_result_frd_block_scanner.md)
adds block-boundary summaries and deferred references, but `.frd` values,
fields, and mesh topology remain unparsed in the current model.

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
- scalar summary placeholders, populated from metadata and bounded `.dat`
  minimal parser candidates when available;
- table placeholders, populated from bounded `.dat` minimal parser candidates
  when available;
- a structured `draft_mapping` payload for future reviewed ResultDataset
  persistence gates;
- provenance from run metadata and export manifest;
- limitations;
- diagnostics.

The draft is a pure data object. It is not a persisted `ResultDataset`, creates
no parent directories, overwrites nothing, and performs no ResultDataset write.

## ResultDataset Draft Mapping

[FEASpec CalculiX ResultDataset draft mapping](feaspec_calculix_result_dataset_draft_mapping.md)
adds a stable in-memory mapping layer over the existing import plan. It maps
artifact metadata, status summaries, bounded `.dat` scalar/table candidates,
deferred `.frd` references, provenance, diagnostics, and limitations into a
reviewable draft structure. The mapping writes no files, performs no
ResultDataset persistence, parses no additional `.frd` numerical field values,
reconstructs no mesh, infers no units, and makes no solver correctness claim.

## Status Summary Enrichment

For `.sta` and `.cvg` artifacts, artifact metadata can include:

- `status_scan`
- `status_summary`

These payloads classify progress, convergence-message, warning, error,
completion, failure, informational, and unknown text lines. They preserve
bounded snippets and counts only. They do not parse numeric convergence values,
do not infer units, and do not certify solver correctness.

## DAT Section Summary Enrichment

For `.dat` artifacts, artifact metadata can include:

- `dat_section_scan`
- `dat_section_summary`

These payloads classify section headings, section spans, section kinds, unknown
sections, unsupported sections, and bounded snippets only. They do not extract
numeric values, do not extract table rows or columns, do not infer units, and do
not certify solver correctness.

## DAT Minimal Parse Enrichment

For `.dat` artifacts, artifact metadata can also include:

- `dat_minimal_parse`
- `dat_minimal_parse_summary`

These payloads contain in-memory scalar/table preview candidates only for
explicit scalar lines and small delimited tables with explicit units. They do
not infer units, do not parse free-form `.dat` output, do not parse `.frd`
fields, do not certify solver correctness, and do not write ResultDataset
files.

## FRD Block Scanner Boundary

`.frd` artifacts remain artifact references plus deferred field and mesh
references in the ResultDataset draft. The `.frd` block scanner adds block
candidates, field-reference candidates, mesh-reference candidates,
unsupported-block diagnostics, and limitations in memory only. It does not add
numerical field parsing, mesh reconstruction, ResultDataset writes, solver
execution, SolverAdapter or runner calls, ProjectSchema mutation, or issue `#8`
validation.

## Safety Boundary

The model preserves these boundaries:

- no solver execution;
- no subprocess path;
- no SolverAdapter integration;
- no runner integration;
- no broad numerical parser;
- no numeric convergence parser;
- no free-form numeric value extraction;
- no free-form table extraction;
- no file writes;
- no ProjectSchema mutation;
- no VLM API;
- no provider credentials or API key fields;
- no release mutation;
- no asset upload or delete;
- no tag mutation;
- no issue mutation.

## CLI Preview

`feaspec-calculix-result-import-preview` is a thin CLI preview over this model.
It requires an explicit `--result-dir`, supports text or JSON output, and keeps
the same result import model only boundary: no broad numerical parser, no
free-form `.dat` parser, no ResultDataset write, no ResultDataset persistence,
and no solver execution.

The preview command does not persist the in-memory draft, does not create
directories, does not call SolverAdapter or runner code, and does not validate
issue `#8`. See
`docs/experimental/feaspec_calculix_result_import_cli_preview.md` for the CLI
contract.

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

- No broad numerical parsing.
- No `.frd` parser.
- No free-form `.dat` parser.
- No broad `.dat` parser implementation.
- No ResultDataset persistence.
- No certification.
- No industrial certification.
- No bundled solver.
- No SolverAdapter handoff.
- No runner handoff.
- No write-capable import command.
- No VLM API.
- No provider credentials.

## Next Implementation Slices

- `OSW-EXP-029_FEASPEC_RESULT_IMPORT_CLI_PREVIEW`
- `OSW-EXP-030_FEASPEC_RESULT_IMPORT_PARSER_DESIGN`
- `OSW-EXP-033_FEASPEC_RESULT_PARSER_DAT_MINIMAL_DESIGN`
- `OSW-EXP-035_FEASPEC_RESULT_PARSER_DAT_MINIMAL_IMPLEMENTATION`
- `OSW-EXP-036_FEASPEC_RESULT_PARSER_FRD_BLOCK_SCANNER_DESIGN`
- `OSW-EXP-037_FEASPEC_RESULT_PARSER_FRD_BLOCK_SCANNER_IMPLEMENTATION`
- `OSW-EXP-038_FEASPEC_RESULT_IMPORT_RESULTDATASET_DRAFT_MAPPING`
- `OSW-EXP-039_FEASPEC_RESULT_IMPORT_DATASET_WRITE_DESIGN`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
