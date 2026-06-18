# FEASpec CalculiX result parser design

Status: design-only.

This document defines a staged parsing strategy only. It does not implement
`.dat`, `.frd`, `.sta`, or `.cvg` parsing. It does not write ResultDataset files
and does not execute CalculiX.

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

- Parse only known `.sta`/`.cvg` marker lines used for run status evidence.
- Collect execution state, step increments, convergence pass/fail markers, and warning
  lines as summary diagnostics.
- Do not derive physics conclusions or report numeric validation.
- Unsupported format variants or unknown sections are recorded as
  `FP_UNSUPPORTED_SECTION`.

### Phase 2 `.dat` text summary/table scanner

- Controlled educational linear-static subset:
  best-effort extraction of known scalar summaries and small text tables only.
- Recognize known heading prefixes and table-like blocks only.
- Unknown `.dat` headings are reported as `FP_UNSUPPORTED_SECTION`.
- Table rows are stored as candidate row/column pairs with a strict numeric parsing
  policy and conversion diagnostics.
- No mesh reconstruction or element-level parsing at this stage.
- `.dat` values remain candidates until unit context is supplied from export/run
  metadata.

### Phase 3 `.frd` field/block scanner

- Block-level metadata scan only (counts, block headers, available fields).
- Record discoverable node/element references and candidate block names.
- No full mesh rebuild or interpolation in this phase.
- Full FRD field arrays remain deferred and represented as references.
- Artifacts that appear parseable by future parser phases are flagged as
  `FP_PARTIAL_PARSE` when incomplete.

## `.sta` / `.cvg` scanner output

- Primary intent: classify run completion status and warning/error signals.
- Map known success/failure phrases to parser diagnostics and severity codes.
- Keep parser confidence low unless run metadata and manifest are coherent.

## `.dat` parser plan

- Implement only a small, deterministic text subset:
  scalar summary candidates and compact tables from known labels.
- Reject unsupported sections as `FP_UNSUPPORTED_SECTION`.
- Parse numeric tokens conservatively; failed conversions become
  `FP_NUMERIC_CONVERSION_FAILED`.
- No unit inference from token shape; units must be provided by metadata or explicit
  parser phase configuration.

## `.frd` parser plan

- Phase-3 scanner identifies:
  block headers, field references, and element/node-related declarations.
- No numeric value matrix parse in this phase.
- Field payloads are mapped as `field_references` with source path and artifact
  role.
- Future phases can upgrade this to full `.frd` field parsing.

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
- `OSW-EXP-032_FEASPEC_RESULT_PARSER_DAT_MINIMAL_IMPLEMENTATION`
- `OSW-EXP-033_FEASPEC_RESULT_PARSER_FRD_BLOCK_SCANNER_DESIGN_OR_IMPLEMENTATION`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`

## Non-goals

- No numerical parser implementation in this gate.
- No resultdataset write.
- No solver execution.
- No SolverAdapter/runner wiring.
- No live `.ccx` validation claims.
- No bundled solver.
- No industrial certification or production-CAE claim.
- No ProjectSchema mutation.
- No external API integrations or secret configuration.
