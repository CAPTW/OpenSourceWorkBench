# FEASpec CalculiX result parser design

Status: design-only.

This document defines a staged parsing strategy. The `.sta` / `.cvg` status
scanner is implemented as a text-only scanner, the `.dat` metadata section
scanner is implemented as a heading/span/snippet scanner, and a bounded `.dat`
minimal parser is implemented for explicit scalar/table candidates with explicit
units. The `.frd` block scanner now has a design-only contract for future
block-boundary metadata. Broad `.dat` numerical parsing and `.frd` parsing
remain unimplemented.
This design does not implement a broad numerical result parser, does not write
ResultDataset files, and does not execute CalculiX.

## Release context

- v0.1.4-rc1 is a public prerelease.
- This design is post-release development on `develop`.
- Public release artifacts are not edited by this gate.

## Relationship to existing gates and model layer

- The parser strategy supports `feaspec-calculix-result-import-preview` and the
  existing result import model.
- It is a future design layer for `build_calculix_result_dataset_draft` mapping.
- The installed-only run gate is unchanged.
- Issue `#8` remains open.
- Live validations remain separate: `#8` remains open until a dedicated live
  validation gate passes.

## Parser principles

- Explicit input files and output directories only.
- No solver execution and no external command invocation.
- No external API integrations, provider secret configuration, or solver installation behavior.
- No silent unit inference from parse text.
- Deterministic diagnostics with explicit codes.
- Parse only known, bounded, safe subsets of `.dat`, `.frd`, `.sta`, and `.cvg`.
- Preserve provenance, artifact identity, and hash metadata.
- Keep parser behavior preview-only with no file writes.
- Keep unsupported content as structured warnings.

## Safety limits

- `max_file_size_bytes`: 4,000,000 bytes for `.dat` and `.sta` scanners, 8,000,000
  bytes for `.frd`.
- `max_line_count`: 50,000 lines per file.
- `max_record_count`: 100,000 parsed records per table/collection.
- `encoding_policy`: `utf-8` preferred; accept `utf-8-sig` with conversion notices;
  reject unsupported encodings as `FP_ENCODING_UNSUPPORTED`.
- Line ending normalization for `\r\n`, `\n`, and `\r` in text scanners.
- Deterministic truncation path when line or record limits are exceeded.
- No timeout needed because parsing is bounded and in-process only.
- No temporary process launch or temporary environment mutation.

## Parser phases

### Phase 0 metadata scanner

- Build file inventory from an explicit result directory.
- Record extension-level classification for:
  `.dat`, `.frd`, `.sta`, `.cvg`, `run_metadata.json`, `*.manifest.json`,
  `*.diagnostics.json`, `stdout.txt`, `stderr.txt`, `README_RUN_FIRST.txt`,
  `.inp`, and `other`.
- Record file identity metadata:
  source path, canonical path, size, hash, suffix, first/last line snippets.
- Emit warnings for unsupported artifacts and parser boundary limitations.

### Phase 1 `.sta` / `.cvg` status summary scanner

- Implemented as a text-only status/progress scanner for direct `.sta` and
  `.cvg` files.
- Classify progress, convergence-message, warning, error, completion, failure,
  informational, and unknown lines.
- Preserve bounded line numbers and snippets.
- Numeric convergence tokens remain text snippets only and are not parsed.
- Do not derive physics conclusions or report numeric validation.
- Unsupported format variants or unknown sections are recorded as
  `FP_STATUS_PATTERN_UNSUPPORTED` or retained as unknown lines.

### Phase 2 `.dat` text summary/table scanner

- Implemented first as a text-only metadata section scanner for direct `.dat`
  files.
- The detailed design lives in
  [FEASpec CalculiX `.dat` minimal parser design](feaspec_calculix_result_dat_minimal_parser_design.md).
- The implemented scanner lives in
  [FEASpec CalculiX `.dat` metadata section scanner](feaspec_calculix_result_dat_section_scanner.md).
- The implemented minimal parser lives in
  [FEASpec CalculiX `.dat` minimal parser](feaspec_calculix_result_dat_parser.md).
- Recognize known heading prefixes, section spans, candidate section kinds, and
  bounded snippets only.
- Unknown `.dat` headings are preserved as `FP_DAT_UNKNOWN_SECTION`.
- Unsupported headings are preserved as `FP_DAT_SECTION_HEADING_UNSUPPORTED`.
- Table-like headings are marked as candidates with
  `FP_DAT_TABLE_CANDIDATE_UNPARSED`; rows and columns are not extracted.
- Numeric-looking tokens remain snippets with `FP_DAT_NUMERIC_VALUES_NOT_PARSED`;
  values are not extracted or converted.
- No mesh reconstruction, element-level parsing, unit inference, or correctness
  claims at this stage.
- The minimal parser slice is implemented for explicit scalar candidates and
  small delimited table candidates with explicit units only. It remains bounded,
  preview-only, and does not implement a free-form `.dat` parser.

### Phase 3 `.frd` field/block scanner

- The detailed design lives in
  [FEASpec CalculiX `.frd` block scanner design](feaspec_calculix_result_frd_block_scanner_design.md).
- Future block-level metadata scan only: block boundaries, block kinds, labels,
  short snippets, and field/mesh reference candidates.
- Record discoverable node/element references and candidate block names without
  reconstructing topology.
- No full mesh rebuild or interpolation in this phase.
- Full FRD field arrays remain deferred and represented as references.
- Artifacts that appear parseable by future parser phases are flagged as
  `FP_PARTIAL_PARSE` when incomplete.

## `.sta` / `.cvg` scanner output

- Primary intent: classify run completion status and warning/error signals.
- Map known success/failure phrases to parser diagnostics and severity codes.
- Keep parser confidence low unless run metadata and manifest are coherent.

## `.dat` parser plan

- The current implementation scans only a small, deterministic text subset:
  headings, spans, candidate kinds, snippets, and diagnostics.
- The minimal implementation additionally parses explicit `label = value unit`
  and `label: value unit` scalar candidates, plus small pipe- or comma-delimited
  tables with explicit unit rows or explicit unit context.
- The future parser remains limited to a controlled educational linear-static
  subset with explicit metadata and reviewed limitations.
- Reject unsupported sections as `FP_UNSUPPORTED_SECTION`.
- Do not parse free-form numeric tokens outside the bounded minimal parser.
- No unit inference from token shape; units must be provided by metadata or explicit
  parser phase configuration.

## `.frd` parser plan

- Phase-3 remains design-only until a separate implementation gate.
- Future scanner identifies block headers, field references, and
  element/node-related declarations.
- No numeric value matrix parse in this phase.
- Field payloads are mapped as `field_references` with source path and artifact
  role.
- Mesh references remain deferred metadata; no mesh reconstruction is performed.

## Unit handling

- Units must be carried through run metadata and/or parser configuration.
- The parser does not infer unit systems from bare numbers.
- Missing units are emitted as `FP_UNITS_MISSING`.

## Parser diagnostics

The parser layer exposes deterministic parser diagnostics with these codes:

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
- `FP_STATUS_SCAN_ONLY`
- `FP_STATUS_PATTERN_UNSUPPORTED`
- `FP_STATUS_NO_RECOGNIZED_LINES`
- `FP_STATUS_PARTIAL_SUMMARY`
- `FP_STATUS_NUMERIC_VALUES_NOT_PARSED`
- `FP_DAT_SECTION_SCAN_ONLY`
- `FP_DAT_SECTION_HEADING_UNSUPPORTED`
- `FP_DAT_SECTION_TOO_LARGE`
- `FP_DAT_SECTION_LINE_LIMIT_EXCEEDED`
- `FP_DAT_TABLE_CANDIDATE_UNPARSED`
- `FP_DAT_NUMERIC_VALUES_NOT_PARSED`
- `FP_DAT_UNKNOWN_SECTION`
- `FP_DAT_NO_RECOGNIZED_SECTIONS`
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
- `FP_DAT_PARSE_NOT_IMPLEMENTED`
- `FP_DAT_SECTION_UNSUPPORTED`
- `FP_DAT_TABLE_HEADER_UNSUPPORTED`
- `FP_DAT_TABLE_TOO_LARGE`
- `FP_DAT_ROW_LIMIT_EXCEEDED`
- `FP_DAT_COLUMN_LIMIT_EXCEEDED`
- `FP_DAT_NUMERIC_VALUE_UNPARSED`
- `FP_DAT_NUMERIC_CONVERSION_FAILED`
- `FP_DAT_UNITS_MISSING`
- `FP_DAT_AMBIGUOUS_UNIT_CONTEXT`
- `FP_DAT_EMPTY_SECTION`
- `FP_DAT_PARTIAL_PARSE`
- `FP_DAT_PROVENANCE_MISSING`
- `FP_DAT_RESULT_DATASET_WRITE_FORBIDDEN`
- `FP_FRD_PARSE_NOT_IMPLEMENTED`
- `FP_FRD_BLOCK_SCAN_ONLY`
- `FP_FRD_BLOCK_UNSUPPORTED`
- `FP_FRD_BLOCK_TOO_LARGE`
- `FP_FRD_BLOCK_LIMIT_EXCEEDED`
- `FP_FRD_UNKNOWN_RECORD`
- `FP_FRD_BINARY_UNSUPPORTED`
- `FP_FRD_FIELD_VALUES_NOT_PARSED`
- `FP_FRD_MESH_RECONSTRUCTION_FORBIDDEN`
- `FP_FRD_UNITS_MISSING`
- `FP_FRD_PROVENANCE_MISSING`
- `FP_FRD_RESULT_DATASET_WRITE_FORBIDDEN`

## Parser output model

Proposed parser output model (report object) includes:

- `parser_report`: phase status, artifact inventory, and parse outcomes.
- `scalar_candidates`: structured scalar candidates with provisional confidence and
  unit metadata.
- `table_candidates`: bounded table candidates with column/row metadata.
- `field_references`: discoverable FRD field candidates and parse readiness flags.
- `artifact_references`: all discovered artifacts and metadata snapshots.
- `diagnostics`: ordered diagnostic list with codes and reasons.
- `provenance`: result directory, run metadata, manifest, manifest links, file hashes.
- `limitations`: explicit warning set describing deferred capabilities.

No file writes and no external commands are emitted through this output model.

## ResultDataset mapping

Result import can map parser output into future ResultDataset contracts as:

- Scalars: candidate maxima and scalar result summaries into
  `ResultDataset`/report summary fields.
- Tables: text and status tables into `ResultTable`-like payloads.
- Artifacts: `.dat`, `.frd`, `.sta`, `.cvg`, `run_metadata.json`, and manifest and
  diagnostics files as artifact references.
- Field references: FRD node/element field candidates mapped as deferred
  `field_references`.
- Provenance: source paths, run metadata links, manifest links, and execution flags.
- Diagnostics: parser diagnostics preserved and elevated to import-level diagnostics
  before any write action.
- Limitations: explicit statement that parser coverage is partial and preview-only.

## Fixture strategy

- No tracked solver output fixtures are added in this design gate.
- Future parser implementation tests should use explicit synthetic in-test text blocks for
  boundary cases and line/limit behavior.
- Full external fixture growth waits for parser implementation gates and dedicated fixture
  directories.

## Test strategy

- Add design-document tests for phase definitions, limits, diagnostics set, and
  boundary claims.
- Add parser unit tests with synthetic text lines and in-memory fixtures:
  - metadata-only run directory
  - malformed encoding
  - oversized file and line behavior
  - unsupported sections
  - `.sta` status parse candidates
  - `.dat` table/summarized scalar candidates
  - `.frd` block reference candidates
- Keep tests solver-free and no external file dependencies.

## Future implementation slices

- `OSW-EXP-031_FEASPEC_RESULT_PARSER_METADATA_SCANNER_IMPLEMENTATION`
- `OSW-EXP-032_FEASPEC_RESULT_PARSER_STA_CVG_STATUS_SCANNER`
- `OSW-EXP-033_FEASPEC_RESULT_PARSER_DAT_MINIMAL_DESIGN`
- `OSW-EXP-034_FEASPEC_RESULT_PARSER_DAT_METADATA_SECTION_SCANNER`
- `OSW-EXP-035_FEASPEC_RESULT_PARSER_DAT_MINIMAL_IMPLEMENTATION`
- `OSW-EXP-036_FEASPEC_RESULT_PARSER_FRD_BLOCK_SCANNER_DESIGN`
- `OSW-EXP-037_FEASPEC_RESULT_PARSER_FRD_BLOCK_SCANNER_IMPLEMENTATION`
- `OSW-EXP-038_FEASPEC_RESULT_IMPORT_DATASET_WRITE_DESIGN`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`

## Non-goals

- No broad numerical parser implementation in this design baseline.
- No free-form `.dat` parser implementation.
- No `.frd` parser implementation.
- No resultdataset write.
- No solver execution.
- No SolverAdapter/runner wiring.
- No live `.ccx` validation claims.
- No bundled solver.
- No industrial certification or production-CAE claim.
- No ProjectSchema mutation.
- No external API integrations or secret configuration.
