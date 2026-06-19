# FEASpec CalculiX `.sta` / `.cvg` status scanner

Status: experimental status scanner implemented.
No numerical parser. No numeric convergence parsing. No ResultDataset write.
No solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- Public release artifacts are not edited by this gate.

## Package path

- `src/osw/experimental/feaspec/calculix_result_status_scanner.py`
- `src/osw/experimental/feaspec/calculix_result_parser_diagnostics.py`

## Public API

- `scan_calculix_status_file(path, metadata=None, limits=None)`
- `scan_calculix_status_directory(result_dir, metadata_scan=None, limits=None)`
- `explain_calculix_status_scan(scan)`

The API returns pure Python data objects and performs no file writes.

## Supported files

- `.sta`
- `.cvg`

Other suffixes are rejected for this scanner. `.dat` and `.frd` remain
outside this status scanner.
[FEASpec CalculiX `.dat` minimal parser design](feaspec_calculix_result_dat_minimal_parser_design.md)
defines a future `.dat` subset separately and does not change this scanner.
The implemented
[FEASpec CalculiX `.dat` metadata section scanner](feaspec_calculix_result_dat_section_scanner.md)
classifies `.dat` headings/spans/snippets only and does not parse numeric values.
The design-only
[FEASpec CalculiX `.frd` block scanner design](feaspec_calculix_result_frd_block_scanner_design.md)
keeps future `.frd` handling limited to block metadata and deferred references.

## Captured status summary

The scanner classifies bounded text lines into categories:

- progress lines
- convergence-message lines
- warning lines
- error lines
- completion indicators
- failure indicators
- informational lines
- unknown lines

Captured data includes category counts, line numbers, bounded snippets, raw text
snippets, and flags for warning/error/completion/failure text indicators.
Completion and failure are text indicators only, not engineering correctness or
validation claims.

## Safety limits

- `max_file_bytes`
- `max_lines`
- `max_snippet_chars`
- `max_matched_lines`
- `max_unknown_lines`

The directory scanner inspects only direct `.sta` and `.cvg` children in sorted
order. It performs no recursion by default.

## Diagnostics

The status scanner uses the shared `FP_*` parser diagnostic catalog and adds
status-specific codes:

- `FP_STATUS_SCAN_ONLY`
- `FP_STATUS_PATTERN_UNSUPPORTED`
- `FP_STATUS_NO_RECOGNIZED_LINES`
- `FP_STATUS_PARTIAL_SUMMARY`
- `FP_STATUS_NUMERIC_VALUES_NOT_PARSED`

Existing metadata diagnostics such as `FP_FILE_MISSING`, `FP_PATH_NOT_FILE`,
`FP_UNSUPPORTED_FORMAT`, `FP_SIZE_LIMIT_EXCEEDED`, `FP_LINE_LIMIT_EXCEEDED`,
`FP_SNIPPET_TRUNCATED`, `FP_ENCODING_UNSUPPORTED`, `FP_METADATA_ONLY`, and
`FP_PARSE_NOT_IMPLEMENTED` are preserved when applicable.

## Relationship to metadata scanner

The scanner consumes `scan_calculix_result_file_metadata` output when provided,
or runs the metadata scanner first. It preserves path, suffix, artifact kind,
size, SHA-256, line count, snippet, metadata-only, and diagnostic information.

## Relationship to result import model

`inspect_calculix_result_directory` attaches `status_scan` and `status_summary`
payloads to `.sta` and `.cvg` artifact metadata. The import model still has no
numerical parser and no ResultDataset write. `.dat` and `.frd` numerical parsing
remain unimplemented.

## Safety boundary

- no `.dat` parser
- no `.frd` parser
- no numeric convergence parsing
- no unit inference
- no solver execution
- no subprocess
- no SolverAdapter
- no runner
- no file writes
- no ResultDataset write
- no VLM API
- no provider credentials

Numeric-looking tokens in progress or convergence-message text are kept as
snippets and flagged with `FP_STATUS_NUMERIC_VALUES_NOT_PARSED`; they are not
converted into numeric values.

## Fixture policy

- Tests use `tmp_path` generated `.sta` and `.cvg` files.
- No tracked solver output fixtures are added in this gate.
- No tracked `.dat`, `.frd`, `.sta`, `.cvg`, `.out`, `.err`, or solver log
  fixtures are added.

## Relationship to #8

The scanner does not validate live `ccx`.
Issue #8 remains open until a prepared-machine live CalculiX validation gate
passes.

## Non-goals

- no numerical parsing
- no numeric convergence parsing
- no ResultDataset persistence
- no certification
- no industrial certification
- no bundled solver
- no ResultDataset write
- no solver execution

## Next implementation slices

- `OSW-EXP-033_FEASPEC_RESULT_PARSER_DAT_MINIMAL_DESIGN`
- `OSW-EXP-034_FEASPEC_RESULT_PARSER_DAT_METADATA_SECTION_SCANNER`
- `OSW-EXP-035_FEASPEC_RESULT_PARSER_DAT_MINIMAL_IMPLEMENTATION`
- `OSW-EXP-036_FEASPEC_RESULT_PARSER_FRD_BLOCK_SCANNER_DESIGN`
- `OSW-EXP-037_FEASPEC_RESULT_PARSER_FRD_BLOCK_SCANNER_IMPLEMENTATION`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
