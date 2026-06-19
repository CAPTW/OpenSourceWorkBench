# FEASpec CalculiX `.dat` metadata section scanner

Status: experimental section scanner implemented.
No numerical parser. No numeric value extraction. No ResultDataset write.
No solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- Public release artifacts, tags, assets, and issues are not edited by this gate.

## Package path

- `src/osw/experimental/feaspec/calculix_result_dat_section_scanner.py`
- `src/osw/experimental/feaspec/calculix_result_parser_diagnostics.py`

## Public API

- `scan_calculix_dat_sections`
- `scan_calculix_dat_sections_directory`
- `explain_calculix_dat_section_scan`

The API returns pure Python data objects. It performs no file writes and no
external command invocation.

## Supported file

- `.dat`

Other suffixes are rejected by this scanner. `.frd` parsing remains future work,
and `.sta` / `.cvg` status text remains handled by the existing status scanner.

## Captured section metadata

The scanner captures bounded text metadata only:

- heading text;
- line span;
- section kind;
- snippets;
- unsupported and unknown diagnostics.

It does not extract values, rows, columns, units, fields, or engineering
correctness.

## Section kinds

- header
- solver message
- scalar candidate
- table candidate
- displacement candidate
- stress candidate
- node output candidate
- element output candidate
- unsupported
- unknown

Candidate means preview metadata only. A table candidate is not a parsed table,
and a scalar candidate is not a parsed scalar value.

## Safety limits

- line count;
- section size;
- snippet length;
- retained section count;
- retained unknown section count;
- no recursion by default.

Limit overflows produce diagnostics and partial summaries rather than hidden
success.

## Diagnostics

The section scanner uses shared `FP_*` diagnostics and the `.dat` section codes:

- `FP_DAT_SECTION_SCAN_ONLY`
- `FP_DAT_SECTION_HEADING_UNSUPPORTED`
- `FP_DAT_SECTION_TOO_LARGE`
- `FP_DAT_SECTION_LINE_LIMIT_EXCEEDED`
- `FP_DAT_TABLE_CANDIDATE_UNPARSED`
- `FP_DAT_NUMERIC_VALUES_NOT_PARSED`
- `FP_DAT_UNKNOWN_SECTION`
- `FP_DAT_NO_RECOGNIZED_SECTIONS`

Metadata diagnostics such as `FP_FILE_MISSING`, `FP_PATH_NOT_FILE`,
`FP_UNSUPPORTED_FORMAT`, `FP_SIZE_LIMIT_EXCEEDED`, `FP_LINE_LIMIT_EXCEEDED`,
`FP_SNIPPET_TRUNCATED`, `FP_ENCODING_UNSUPPORTED`, `FP_METADATA_ONLY`, and
`FP_PARSE_NOT_IMPLEMENTED` are preserved when applicable.

## Relationship to metadata scanner

The scanner consumes `scan_calculix_result_file_metadata` output when provided,
or runs the metadata scanner first. It preserves suffix, artifact kind, file
size, SHA-256, line information, snippets, metadata-only diagnostics, and
parse-not-implemented diagnostics.

## Relationship to result import model

`inspect_calculix_result_directory` attaches `dat_section_scan` and
`dat_section_summary` payloads to `.dat` artifact metadata. The section scanner
still has no numerical parser, no table extraction, and no ResultDataset write.
A separate minimal `.dat` parser may consume these section candidates and attach
bounded preview summaries without changing the scanner boundary.

The `feaspec-calculix-result-import-preview` CLI may report `.dat` section
summary counts in text or JSON. The command remains preview-only and does not
write files.

## Safety boundary

- no numeric value extraction;
- no table extraction;
- no unit inference;
- no `.frd` parser;
- no solver execution;
- no subprocess;
- no SolverAdapter;
- no runner;
- no file writes;
- no ResultDataset write;
- no VLM API;
- no provider credentials.

Numeric-looking tokens in snippets are preserved as text and flagged with
`FP_DAT_NUMERIC_VALUES_NOT_PARSED`; they are not converted into numeric values.
Table-like headings are marked only with `FP_DAT_TABLE_CANDIDATE_UNPARSED`;
rows and columns are not extracted.

## Fixture policy

- Tests use `tmp_path` generated `.dat` files.
- No tracked solver output fixtures are added in this gate.
- No tracked `.dat`, `.frd`, `.sta`, `.cvg`, `.out`, `.err`, or solver log
  fixtures are added.

## Relationship to #8

The scanner does not validate live `ccx`.
Issue #8 remains open until a prepared-machine live CalculiX validation gate
passes.

## Non-goals

- no numerical parsing
- no numeric value extraction
- no table extraction
- no unit inference
- no ResultDataset persistence
- no ResultDataset write
- no solver execution
- no certification
- no industrial certification
- no bundled solver

## Next implementation slices

- `OSW-EXP-035_FEASPEC_RESULT_PARSER_DAT_MINIMAL_IMPLEMENTATION`
- `OSW-EXP-036_FEASPEC_RESULT_PARSER_FRD_BLOCK_SCANNER_DESIGN`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
