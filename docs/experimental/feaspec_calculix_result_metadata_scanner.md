# FEASpec CalculiX result metadata scanner

Status: experimental metadata scanner implemented.
No numerical parser. No ResultDataset write. No solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- Public release artifacts are not edited by this gate.

## Package path

- `src/osw/experimental/feaspec/calculix_result_metadata_scanner.py`
- `src/osw/experimental/feaspec/calculix_result_parser_diagnostics.py`

## Public API

- `scan_calculix_result_file_metadata(path, limits=None)`
- `scan_calculix_result_directory_metadata(result_dir, limits=None)`
- `explain_calculix_result_metadata_scan(scan)`

## Captured metadata

The scanner records per-file:

- resolved path/name/suffix
- artifact kind
- `byte_size`
- `sha256`
- encoding status (`utf-8`, `utf-8-sig`, or replacement policy)
- `line_count` and truncation
- first and last line snippets up to `max_snippet_lines`
- `snippet_truncated`
- parser phase
- parse-not-implemented flag for `.dat`, `.frd`, `.sta`, `.cvg`
- per-file diagnostics
- deterministic status (`scanned`, `scanned-with-warnings`, `blocked`, `unsupported`, `limit-exceeded`)

## Safety limits

The scanner applies bounded metadata-only limits to avoid heavy reads:

- `max_file_bytes` (default `100000`)
- `max_lines` (default `256`)
- `max_snippet_chars` (default `160`)
- `max_snippet_lines` (default `4`)
- `allowed_suffixes` (`.dat`, `.frd`, `.sta`, `.cvg`, `.inp`, `.txt`, `.json`, `.log` and manifest/log/json variants)

No recursion is performed by default. Files are scanned only when they are direct
children of the provided result directory.

## Diagnostics

The scanner uses `FP_*` diagnostics from
`calculix_result_parser_diagnostics.py`, including:

- `FP_FILE_MISSING`
- `FP_PATH_NOT_FILE`
- `FP_UNSUPPORTED_FORMAT`
- `FP_SIZE_LIMIT_EXCEEDED`
- `FP_LINE_LIMIT_EXCEEDED`
- `FP_SNIPPET_TRUNCATED`
- `FP_HASH_FAILED`
- `FP_ENCODING_UNSUPPORTED`
- `FP_PARSE_NOT_IMPLEMENTED`
- `FP_METADATA_ONLY`
- `FP_PARTIAL_PARSE`
- `FP_UNSUPPORTED_SECTION`
- `FP_UNSUPPORTED_RESULT_BLOCK`
- `FP_NUMERIC_CONVERSION_FAILED`
- `FP_NO_PRIMARY_FIELD`
- `FP_UNITS_MISSING`
- `FP_PROVENANCE_MISSING`
- `FP_SOLVER_RUN_FAILED`
- `FP_FORBIDDEN_PATH`
- `FP_EXTERNAL_COMMAND_FORBIDDEN`
- `FP_RESULT_DATASET_WRITE_FORBIDDEN`

## Relationship to result import model

- `inspect_calculix_result_directory` calls the file scanner for every discovered file.
- Artifact metadata includes `result_parser` payload with byte size, hashes, snippets,
  parser phase, and parse-not-implemented flag.
- FI parse-not-implemented warnings remain warnings; no numerical parse is added.

## Safety boundary

This scanner is metadata-only and does not implement numerical parsing.
It does not run CalculiX, does not spawn subprocesses, does not call solver
adapter or runner paths, and does not write files.
It does not infer units from parse text and it does not execute external commands.
It does not run external command execution.
No external command invocation is performed.
It does not include external API integrations or provider-secret configuration.
No subprocess calls are executed.

## Fixture policy

- Tests use `tmp_path` and synthetic fixtures only.
- This gate does not add tracked solver output fixtures (`.dat`, `.frd`, `.sta`,
  `.cvg`, logs, `.12d`, `.out`, `.err`).
- Runtime artifacts are treated as ignored and preview-only.

## Relationship to issue #8

The scanner does not validate live `ccx` execution.
Issue `#8` remains open until a dedicated installed-only validation gate.

## Non-goals

- Numerical parsing of `.dat`/`.frd`/`.sta`/`.cvg`.
- ResultDataset persistence.
- Solver execution in preview model.
- Certification claims.
- Bundled solvers.

## Next implementation slices

- `OSW-EXP-032_FEASPEC_RESULT_PARSER_STA_CVG_STATUS_SCANNER`
- `OSW-EXP-033_FEASPEC_RESULT_PARSER_DAT_MINIMAL_DESIGN`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
