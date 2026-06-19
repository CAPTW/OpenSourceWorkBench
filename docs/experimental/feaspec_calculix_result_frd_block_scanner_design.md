# FEASpec CalculiX `.frd` block scanner design

Status: design baseline retained.
An experimental `.frd` block metadata scanner is now implemented under
`src/osw/experimental/feaspec/calculix_result_frd_block_scanner.py`.
No numerical field parser. No node or element value arrays. No mesh
reconstruction. No ResultDataset write. No solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This design is post-release development on `develop`.
- Public release artifacts, tags, assets, and issues are not edited by this
  gate.

## Relationship to existing layers

The `.frd` block scanner sits after the existing safe inspection layers:

- the metadata scanner records suffix, artifact kind, byte size, SHA-256, line
  and snippet evidence;
- the `.sta` / `.cvg` status scanner classifies text-only progress and status
  messages without numeric convergence parsing;
- the `.dat` metadata section scanner records headings, section spans, section
  kinds, and snippets without extracting values;
- the `.dat` minimal parser parses only bounded explicit scalar/table candidates
  with explicit unit context;
- the result import model and CLI preview keep all parser output in memory and
  do not persist a ResultDataset;
- the ResultDataset draft can carry `.frd` references as candidates and
  limitations only.

## Scanner principles

- Accept explicit `.frd` files only.
- Start metadata-first and preserve source path, size, hash, line count, and
  snippets before any block-level analysis.
- Detect block boundaries before any content interpretation.
- Classify block kinds conservatively and deterministically.
- Preserve labels, titles, and short snippets only when they are safe text.
- Do not perform numerical field parsing.
- Do not reconstruct mesh nodes, elements, topology, or visualization arrays.
- Do not infer units from `.frd` text, record shapes, or labels.
- Do not claim solver correctness, validation, or engineering accuracy.
- Preserve unsupported or unknown records as diagnostics and limitations.
- Use no external tools, no subprocess calls, no SolverAdapter, and no runner.

## Implemented scanner subset

The implementation produces only these bounded metadata records:

- file metadata from the existing metadata scanner;
- block boundary candidates with start and end line or record positions;
- block kinds such as header, result set, node reference, element reference,
  field reference, unsupported, unknown, and binary/opaque;
- labels or titles when they are safe text snippets;
- field-reference candidates that name a discoverable field without parsing its
  values;
- mesh-reference candidates that indicate node/element-related blocks without
  reconstructing topology;
- unsupported-block diagnostics with bounded snippets and provenance.

The subset is intentionally a scanner contract, not a numerical parser.

## Explicitly unsupported

The design explicitly does not support:

- node value arrays;
- element value arrays;
- full mesh reconstruction;
- element connectivity reconstruction;
- field array parsing;
- visualization data structures;
- binary `.frd` parsing;
- full CalculiX result parser claims;
- engineering validation or correctness claims.

## Safety limits

Future scanner limits must be explicit and testable:

- `max_file_size_bytes`;
- `max_line_count`;
- `max_record_count`;
- `max_block_count`;
- `max_block_span`;
- `max_snippet_chars`;
- `max_unsupported_block_snippets`.

Limit overflows must produce diagnostics and partial metadata, not hidden
success.

## Encoding and format handling

- Prefer text or ASCII-like `.frd` metadata first.
- Treat binary, mixed binary, or unknown encodings as unsupported for this
  scanner.
- Preserve deterministic replacement snippets only when decoding can be bounded
  and reviewed.
- Do not call external conversion tools.
- Do not use CalculiX, mesh viewers, visualization libraries, or shell commands
  to inspect `.frd` content.

## Diagnostics

The `.frd` block scanner uses shared parser diagnostics plus these `FP_FRD_*`
codes:

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
- `FP_FRD_NO_RECOGNIZED_BLOCKS`
- `FP_FRD_REFERENCE_CANDIDATE_ONLY`

## Scanner output model

The scanner output is a pure in-memory report with:

- `block_candidates`: ordered block boundary records with kind, label, span,
  and provenance;
- `field_reference_candidates`: references to discoverable result fields, with
  no parsed values;
- `mesh_reference_candidates`: references to node or element-related blocks,
  with no reconstructed topology;
- `unsupported_blocks`: unsupported or unknown block records with snippets;
- `diagnostics`: ordered `FP_*` diagnostics;
- `provenance`: source file path, metadata scanner payload, hash, and line or
  record evidence;
- `limitations`: explicit statements that values, fields, units, and mesh are
  not parsed.

No file writes and no external commands are part of this output model.

## ResultDataset mapping

ResultDataset integration remains candidate-only:

- `.frd` artifacts remain artifact references with metadata and hashes;
- block candidates become preview references;
- field-reference candidates become deferred field references;
- mesh-reference candidates become deferred mesh references;
- numerical arrays remain future work and are not placed into ResultDataset
  tables or fields by this scanner;
- limitations and diagnostics are preserved before any future write gate.

No ResultDataset persistence or ProjectSchema mutation is added by this design.

## Fixture strategy

- No tracked solver output fixtures are added in this design gate.
- No tracked `.frd`, `.dat`, `.sta`, `.cvg`, `.out`, `.err`, or solver log
  fixtures are added.
- Implementation tests use tiny synthetic `.frd` text generated under
  `tmp_path` or another allowlisted test path.
- Fixture cases include recognizable block boundaries,
  unsupported records, malformed records, oversized blocks, and binary-ish
  byte sequences.
- Synthetic fixtures must not claim real engineering validation.

## Future test strategy

Implementation tests verify:

- block boundary detection for tiny synthetic text;
- supported block-kind classification;
- unsupported-block diagnostics;
- unknown-record diagnostics;
- file size, record, block count, and block span limits;
- binary or unknown encoding rejection;
- no numeric extraction from field records;
- no mesh reconstruction from node or element records;
- no unit inference;
- no external command invocation;
- no ResultDataset write;
- no solver execution.

## Relationship to #8

This design does not validate live `ccx`.
Issue `#8` remains open until a prepared-machine live CalculiX validation gate
passes.

## Non-goals

- no numerical `.frd` field parser
- no numerical field parsing
- no mesh reconstruction
- no visualization field reconstruction
- no unit inference
- no ResultDataset persistence
- no ResultDataset write
- no solver execution
- no subprocess
- no SolverAdapter
- no runner
- no ProjectSchema mutation
- no VLM API
- no provider credentials
- no bundled solver
- no certification
- no industrial certification

## Future implementation slices

- `OSW-EXP-037_FEASPEC_RESULT_PARSER_FRD_BLOCK_SCANNER_IMPLEMENTATION`
- `OSW-EXP-038_FEASPEC_RESULT_IMPORT_DATASET_WRITE_DESIGN`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
