# FEASpec CalculiX `.dat` minimal parser design

Status: design baseline retained; bounded minimal parser implemented.
No free-form `.dat` parser. No `.frd` parser. No unit inference.
No ResultDataset write. No solver execution.

The first implementation slice after this design is the
[FEASpec CalculiX `.dat` metadata section scanner](feaspec_calculix_result_dat_section_scanner.md).
It recognizes headings, spans, section kinds, and bounded snippets only; it does
not parse numeric values or extract tables.

The minimal parser implementation is documented in
[FEASpec CalculiX `.dat` minimal parser](feaspec_calculix_result_dat_parser.md).
It consumes section scanner output and parses only explicit scalar/table
candidate sections with explicit unit context.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This design is post-release development on `develop`.
- Public release artifacts, tags, assets, and issues are not edited by this gate.

## Relationship to existing layers

- Metadata scanner: records `.dat` identity, suffix, size, SHA-256, line counts,
  and bounded snippets without parsing numerical result content.
- `.sta/.cvg` status scanner: classifies status/progress text only and does not
  parse numeric convergence values.
- Result import model: classifies existing result artifacts and builds an
  in-memory draft with `writes_files=false`.
- Result import CLI preview: reports the import plan and limitations without
  writing files.
- ResultDataset draft: future parser output may be mapped into an in-memory
  preview draft before any persistence gate exists.

## Parser principles

- Accept explicit `.dat` files only.
- Read a bounded text subset with deterministic limits.
- Recognize only known headings and small educational sections.
- Preserve line-number provenance for every accepted candidate.
- Emit diagnostics for unsupported sections instead of guessing.
- Use export/run metadata when available for context.
- No silent unit inference from text.
- No engineering correctness claims from parser output.
- No solver execution, subprocess use, SolverAdapter handoff, runner handoff, or
  file writes.

## Minimum supported future subset

The future implementation may support only a small, reviewed, educational
linear-static subset:

- file metadata/header summary;
- known small scalar summary sections when the label is explicit;
- known small text tables with explicit headings;
- line-number provenance for every scalar or table candidate;
- unsupported-section diagnostics for content outside the allowlist.

Any candidate values remain preview candidates until unit context and review
evidence are available. The minimal implementation extracts only bounded
candidate values from explicit allowlisted scalar/table text with units.

The implemented section scanner covers only metadata for this subset: headings,
spans, snippets, known/unknown/unsupported section categories, and counts.

## Explicitly unsupported

- Free-form unknown tables.
- Ambiguous unitless numeric values.
- Field data or field block reconstruction.
- Mesh reconstruction.
- `.frd` data.
- Nonlinear, contact, plasticity, or broad CalculiX coverage claims.
- Solver correctness, physical validation, certification, or production CAE
  claims.

## Safety limits

Future implementation should use explicit limits before reading or accepting
content:

- `max_file_size_bytes`: proposed default `4_000_000`.
- `max_line_count`: proposed default `50_000`.
- `max_table_rows`: proposed default `500`.
- `max_columns`: proposed default `16`.
- `max_scalar_candidates`: proposed default `100`.
- `max_unsupported_snippets`: proposed default `25`.

Limit overflows must produce diagnostics and partial-preview output rather than
hidden truncation or success.

## Unit handling

- Use export/run metadata when available.
- Use explicit parser configuration only in a future parser implementation gate.
- No unit inference from text, labels, whitespace, or bare numeric tokens.
- Missing units produce diagnostics.
- Ambiguous unit context blocks ResultDataset-ready status.

## Planned diagnostics

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

These are design codes for broader future parser slices. Runtime diagnostics for
the minimal implementation are documented in
`feaspec_calculix_result_dat_parser.md`.

## Parser output model

The future parser report should remain a pure in-memory object with:

- `scalar_candidates`: explicit-label scalar preview candidates with source
  line numbers, raw text, unit context, and confidence/limitation notes;
- `table_candidates`: small known-table preview candidates with heading, source
  line span, raw text rows, column labels, and truncation state;
- `unsupported_sections`: heading/snippet records for sections outside the
  allowlist;
- `diagnostics`: ordered `FP_DAT_*` and shared `FP_*` diagnostics;
- `provenance`: source path, file hash, metadata scan reference, run metadata
  reference, export manifest reference, and line spans;
- `limitations`: explicit no-certification, partial-parser, and unit-context
  limitations.

## ResultDataset mapping

- Scalar summaries map only as preview candidates until a future review/write
  gate accepts them.
- Tables map only as preview table candidates.
- Artifacts remain retained as artifact references.
- Field references remain `.frd` block-scanner work, not `.dat` work.
- Limitations and diagnostics must be preserved beside any preview draft.
- This design gate does not add ResultDataset persistence.

## Fixture strategy

- No tracked solver output fixtures are added in this design gate.
- Future implementation tests should use synthetic tiny `.dat` text generated
  in tests or explicitly allowlisted test fixtures.
- Future tiny fixtures must live under a reviewed test path and must not be
  real engineering validation evidence.
- No generated runtime `.dat`, `.frd`, `.sta`, `.cvg`, `.out`, `.err`, solver
  log, or live CalculiX output is added here.

## Test strategy for future implementation

- Known heading accepted.
- Unknown heading rejected.
- Oversized table blocked.
- Missing units diagnostic emitted.
- Malformed numeric cell diagnostic emitted.
- Numeric text remains untrusted until unit context and parser rules accept it.
- No external command invocation.
- No ResultDataset write.
- No `.frd` field parsing.
- No SolverAdapter, runner, subprocess, ProjectSchema mutation, VLM API, or
  provider credential import.

## Relationship to #8

This `.dat` parser design does not validate live `ccx`.
Issue `#8` remains open until a prepared-machine live CalculiX validation gate
passes.

## Non-goals

- No free-form parser implementation.
- No broad `.dat` parser implementation.
- No unsupported numerical extraction.
- No broad numerical result parsing.
- No `.frd` numerical field parser.
- No ResultDataset persistence.
- No ResultDataset write.
- No solver execution.
- No bundled solver.
- No industrial certification.

## Future implementation slices

- `OSW-EXP-034_FEASPEC_RESULT_PARSER_DAT_METADATA_SECTION_SCANNER`
- `OSW-EXP-035_FEASPEC_RESULT_PARSER_DAT_MINIMAL_IMPLEMENTATION`
- `OSW-EXP-036_FEASPEC_RESULT_PARSER_FRD_BLOCK_SCANNER_DESIGN`
- `OSW-EXP-038_FEASPEC_RESULT_IMPORT_DATASET_WRITE_DESIGN`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
