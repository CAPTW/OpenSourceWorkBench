# FEASpec CalculiX `.dat` minimal parser

Status: experimental minimal parser implemented.
Bounded known sections only. No free-form parser. No `.frd` parser.
No ResultDataset write. No solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- Public release artifacts, tags, assets, and issues are not edited by this gate.

## Package path

- `src/osw/experimental/feaspec/calculix_result_dat_parser.py`
- `src/osw/experimental/feaspec/calculix_result_parser_diagnostics.py`

## Public API

- `parse_calculix_dat_minimal`
- `parse_calculix_dat_directory_minimal`
- `explain_calculix_dat_minimal_parse`

The API returns pure Python data objects. It performs no file writes, no solver
execution, no external command invocation, no SolverAdapter handoff, and no
runner handoff.

## Supported content

The parser accepts explicit `.dat` files and consumes the metadata section
scanner output. It parses only:

- explicit scalar candidates in `label = value unit` form;
- explicit scalar candidates in `label: value unit` form;
- small pipe- or comma-delimited table candidates with a header row;
- table values only when each parsed numeric value column has explicit units;
- source provenance including path, section heading, raw line text, and line
  number.

The parser preserves raw strings beside parsed preview values. Parsed values are
preview candidates only and do not establish solver correctness.

## Required unit policy

- A scalar requires a unit token or an explicit `unit_context` mapping.
- A table numeric value column requires a unit row or explicit `unit_context`.
- No unit inference is performed from labels, headings, value shapes, or bare
  numbers.
- Missing units produce diagnostics and skip numeric extraction for that scalar
  or column.

## Safety limits

- scalar count;
- table rows;
- table columns;
- section size;
- snippet retention;
- direct-directory scan only, no recursion by default.

Limit overflows produce diagnostics and partial-preview output instead of
hidden success.

## Diagnostics

The minimal parser uses shared `FP_*` diagnostics and these `.dat` minimal
parser codes:

- `FP_DAT_PARSE_MINIMAL_ONLY`
- `FP_DAT_SCALAR_CANDIDATE_PARSED`
- `FP_DAT_TABLE_CANDIDATE_PARSED`
- `FP_DAT_UNITS_REQUIRED`
- `FP_DAT_UNITS_MISSING`
- `FP_DAT_UNIT_INFERENCE_FORBIDDEN`
- `FP_DAT_UNSUPPORTED_SECTION_SKIPPED`
- `FP_DAT_UNKNOWN_TABLE_SKIPPED`
- `FP_DAT_TABLE_ROW_LIMIT_EXCEEDED`
- `FP_DAT_TABLE_COLUMN_LIMIT_EXCEEDED`
- `FP_DAT_SCALAR_LIMIT_EXCEEDED`
- `FP_DAT_NUMERIC_CONVERSION_FAILED`
- `FP_DAT_AMBIGUOUS_VALUE_SKIPPED`
- `FP_DAT_RAW_TEXT_PRESERVED`
- `FP_DAT_RESULT_DATASET_WRITE_FORBIDDEN`

Section scanner diagnostics such as `FP_DAT_SECTION_SCAN_ONLY`,
`FP_DAT_TABLE_CANDIDATE_UNPARSED`, `FP_DAT_NUMERIC_VALUES_NOT_PARSED`,
`FP_DAT_UNKNOWN_SECTION`, and `FP_DAT_NO_RECOGNIZED_SECTIONS` are preserved when
the section scanner emits them.

## Relationship to section scanner

The parser consumes `scan_calculix_dat_sections` output. It only attempts
candidate parsing for section kinds already classified as scalar, table,
displacement, stress, node output, or element output candidates. Unsupported and
unknown sections are preserved as skipped content with diagnostics.

## Relationship to result import model

`inspect_calculix_result_directory` attaches `dat_minimal_parse` and
`dat_minimal_parse_summary` payloads to `.dat` artifact metadata. The
ResultDataset draft can include in-memory scalar and table candidates from this
minimal parse.

This is ResultDataset draft enrichment only. There is no persistence, no
ResultDataset file write, and no ProjectSchema mutation.

## Safety boundary

- no `.frd` parser;
- no free-form table parser;
- no mesh reconstruction;
- no field reconstruction;
- no engineering correctness claims;
- no unit inference;
- no solver execution;
- no subprocess;
- no SolverAdapter;
- no runner;
- no file writes;
- no ResultDataset write;
- no VLM API;
- no provider credentials.

The parser does not validate engineering accuracy. Users must validate results
independently.

## Fixture policy

- Tests use `tmp_path` generated `.dat` text.
- No tracked solver output fixtures are added in this gate.
- No tracked `.dat`, `.frd`, `.sta`, `.cvg`, `.out`, `.err`, or solver log
  fixtures are added.

## Relationship to #8

The parser does not validate live `ccx`.
Issue #8 remains open until a prepared-machine live CalculiX validation gate
passes.

## Non-goals

- no broad numerical parser
- no broad `.dat` parser
- no free-form `.dat` parser
- no `.frd` parser
- no unit inference
- no ResultDataset persistence
- no ResultDataset write
- no solver execution
- no certification
- no industrial certification
- no bundled solver

## Next implementation slices

- `OSW-EXP-036_FEASPEC_RESULT_PARSER_FRD_BLOCK_SCANNER_DESIGN`
- `OSW-EXP-037_FEASPEC_RESULT_IMPORT_DATASET_WRITE_DESIGN`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
