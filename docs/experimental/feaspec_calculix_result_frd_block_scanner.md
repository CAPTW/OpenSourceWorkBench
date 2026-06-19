# FEASpec CalculiX `.frd` block metadata scanner

Status: experimental block scanner implemented.
No numerical field parser. No node or element value arrays. No mesh
reconstruction. No ResultDataset write. No solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- Public release artifacts, tags, assets, and issues are not edited by this
  gate.

## Package path

- `src/osw/experimental/feaspec/calculix_result_frd_block_scanner.py`

## Public API

- `scan_calculix_frd_blocks`
- `scan_calculix_frd_blocks_directory`
- `explain_calculix_frd_block_scan`

## Supported file

- `.frd`

Other suffixes are rejected by this scanner. `.dat` parsing, `.sta` / `.cvg`
status scanning, and live CalculiX validation remain separate.

## Captured block metadata

The scanner reads bounded text metadata and records:

- block label text;
- heading line number;
- line span;
- block kind;
- bounded snippets;
- unsupported and unknown diagnostics;
- deferred reference candidates.

The scanner preserves metadata from the existing result metadata scanner,
including suffix, artifact kind, size, SHA-256, line count, and snippets.

## Block kinds

- `header`
- `mesh_reference_candidate`
- `node_reference_candidate`
- `element_reference_candidate`
- `field_reference_candidate`
- `result_block_candidate`
- `unsupported`
- `unknown`

Reference candidates are preview-only records. They may identify that a block is
related to mesh, node, element, field, result, or unknown content, but they do
not contain numerical arrays.

## Safety limits

- maximum file size;
- maximum line count;
- maximum block count;
- maximum block span;
- maximum snippet length;
- maximum unknown block retention;
- maximum reference candidate retention;
- no recursion by default in the directory scanner.

Limit overflows produce diagnostics and partial metadata rather than hidden
success.

## Diagnostics

The scanner uses the shared `FP_*` parser diagnostic catalog and adds FRD block
diagnostics:

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

## Relationship to metadata scanner

The FRD block scanner consumes metadata scanner output when available and
preserves the metadata snapshot in its result. It adds block and reference
candidate summaries only after suffix, size, hash, line, and snippet evidence is
available.

## Relationship to result import model

When `.frd` artifacts are present, the result import model attaches
`frd_block_scan` and `frd_block_summary` to the artifact metadata. The in-memory
ResultDataset draft may carry deferred field or mesh references with
`candidate-not-parsed` status.

No ResultDataset file is written. No ProjectSchema mutation is performed.

## Relationship to CLI preview

`feaspec-calculix-result-import-preview` may include `frd_block_summary` in JSON
output and may print compact block counts in text output. The preview remains
read-only and writes no files.

## Safety boundary

- no numerical field parser;
- no node or element value arrays;
- no field array reconstruction;
- no mesh reconstruction;
- no visualization arrays;
- no numeric value extraction;
- no unit inference;
- no ResultDataset write;
- no solver execution;
- no SolverAdapter;
- no runner;
- no subprocess;
- no file writes.

The scanner can preserve numeric-looking tokens as bounded text snippets, but it
does not convert them into values or arrays.

## Fixture policy

- Tests use `tmp_path` generated `.frd` text.
- No tracked solver output fixtures are added in this gate.
- No tracked `.frd`, `.dat`, `.sta`, `.cvg`, `.out`, `.err`, or solver log
  fixtures are added.
- Synthetic snippets must not claim real engineering validation.

## Relationship to #8

This scanner does not validate live `ccx`. Issue `#8` remains open until a
prepared-machine live CalculiX validation gate passes.
Issue #8 remains open.

## Non-goals

- no numerical parsing;
- no numerical field parser;
- no node or element value arrays;
- no mesh reconstruction;
- no visualization data structures;
- no ResultDataset persistence;
- no certification;
- no bundled solver;
- no industrial certification.

## Next implementation slices

- `OSW-EXP-038_FEASPEC_RESULT_IMPORT_DATASET_WRITE_DESIGN`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
