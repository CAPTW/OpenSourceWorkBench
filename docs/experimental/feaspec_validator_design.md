# FEASpec validator design

Status: design-only contract. The follow-up experimental semantic validator
report layer is implemented on `develop`; the full validator is not implemented
as a production or full physics validator, no solver execution is added, and
this document remains the validator contract.

## Release Context

`v0.1.4-rc1` is a public prerelease. This validator design is post-release
development on `develop`. It does not change the published release, release
assets, release tag, or package metadata.

## Relationship To Existing Model Layer

The experimental model layer under `src/osw/experimental/feaspec/` performs
structural loading and basic checks only. It verifies required fields, explicit
units, geometry IDs and references, target references, and approved review
state for documented examples.

This validator design defines semantic validation. It is the contract the
experimental report-layer implementation follows before any full ProjectSchema
persistence, ProjectSchema mutation, or SolverAdapter handoff is considered.

## Validator Goals

- Protect future solver handoff from incomplete or unsafe FEASpec data.
- Preserve uncertainty, evidence, assumptions, and provider provenance.
- Force human review before any approved solver flow.
- Produce actionable diagnostics with stable categories and codes.
- Support a CalculiX-first compatibility path for small educational cases.
- Keep Abaqus optional and non-default if discussed.

## Non-Goals

- No implementation in this gate.
- No production/full physics validator implementation.
- No full ProjectSchema persistence or ProjectSchema mutation.
- No solver adapter or exporter.
- No CalculiX case generator.
- No Abaqus exporter.
- No solver execution.
- No VLM API, provider client, credentials, or API keys.
- No mandatory Abaqus or commercial solver dependency.
- No topology optimization implementation.
- No industrial certification, compliance, or production CAE claim.

## Validator Pipeline

Future validation should run as an explicit pipeline:

1. Parse/model load phase: load `FEASpecCandidate` or approved FEASpec data
   through the experimental model layer.
2. Schema phase: verify required fields, known enum values, and list/object
   shapes.
3. Unit phase: verify the unit system and every dimensional quantity.
4. Geometry phase: verify unique IDs, graph references, connectivity, regions,
   dimensions, and coordinate frames.
5. Material/section phase: verify material models, properties, units, section
   assignments, and target references.
6. Boundary-condition phase: verify target references, degrees of freedom,
   values, coordinate frames, and likely constraint sufficiency.
7. Load phase: verify target references, units, magnitudes, directions, vectors,
   and sign conventions.
8. Evidence/confidence phase: verify evidence links, confidence levels, source
   provenance, and unresolved assumptions.
9. Human review phase: verify review state, reviewed item coverage, accepted
   warnings, and local approval notes.
10. Solver compatibility phase: verify compatibility for the requested future
    solver preparation path without generating or running a case.
11. Benchmark readiness phase: verify synthetic seed metadata, ground-truth
    FEASpec loading, and expected metrics.
12. Validation report output phase: return structured diagnostics and a final
    validation state.

## Diagnostic Model

Each future diagnostic should have these fields:

- `code`: stable machine-readable code.
- `severity`: one of `info`, `warning`, `error`, or `blocker`.
- `category`: diagnostic category.
- `message`: concise reviewer-facing explanation.
- `target_ref`: affected FEASpec entity or path.
- `evidence_ref`: related evidence item when available.
- `suggested_fix`: specific review or correction action.
- `blocks_approval`: whether this diagnostic prevents approval.
- `blocks_solver_handoff`: whether this diagnostic prevents future solver
  handoff.

## Severity Taxonomy

- `info`: contextual note that does not block review or future handoff.
- `warning`: issue that may remain only if a human explicitly accepts it.
- `error`: issue that blocks approval until corrected or replaced with an
  explicit reviewed override.
- `blocker`: issue that blocks approval and future solver handoff.

## Diagnostic Categories

- `schema`
- `units`
- `geometry`
- `material`
- `section`
- `boundary_condition`
- `load`
- `dimension`
- `evidence`
- `human_review`
- `solver_compatibility`
- `benchmark`

## Required Diagnostic Codes

The future validator must reserve these codes:

| Code | Category | Default severity | Blocking intent |
| --- | --- | --- | --- |
| `FS_SCHEMA_MISSING_FIELD` | `schema` | `error` | Blocks approval |
| `FS_UNITS_MISSING_SYSTEM` | `units` | `blocker` | Blocks approval and solver handoff |
| `FS_UNITS_AMBIGUOUS` | `units` | `error` | Blocks approval unless explicitly reviewed |
| `FS_GEOM_DUPLICATE_ID` | `geometry` | `error` | Blocks approval |
| `FS_GEOM_MISSING_NODE` | `geometry` | `error` | Blocks approval |
| `FS_GEOM_DISCONNECTED_GRAPH` | `geometry` | `error` | Blocks approval |
| `FS_MATERIAL_MISSING` | `material` | `error` | Blocks approval |
| `FS_SECTION_MISSING` | `section` | `error` | Blocks approval |
| `FS_BC_INVALID_TARGET` | `boundary_condition` | `error` | Blocks approval |
| `FS_BC_INSUFFICIENT_CONSTRAINTS` | `boundary_condition` | `warning` | Blocks solver handoff unless accepted or corrected |
| `FS_LOAD_INVALID_TARGET` | `load` | `error` | Blocks approval |
| `FS_LOAD_MISSING_UNITS` | `load` | `blocker` | Blocks approval and solver handoff |
| `FS_DIMENSION_CONFLICT` | `dimension` | `error` | Blocks approval |
| `FS_EVIDENCE_MISSING` | `evidence` | `warning` | May block approval depending on entity |
| `FS_CONFIDENCE_LOW` | `evidence` | `warning` | Blocks automatic approval |
| `FS_REVIEW_MISSING` | `human_review` | `blocker` | Blocks approval and solver handoff |
| `FS_REVIEW_NOT_APPROVED` | `human_review` | `blocker` | Blocks solver handoff |
| `FS_SOLVER_UNSUPPORTED_ELEMENT` | `solver_compatibility` | `error` | Blocks that solver path |
| `FS_SOLVER_ABAQUS_NON_DEFAULT` | `solver_compatibility` | `info` | Records optional/non-default handling |
| `FS_BENCHMARK_METADATA_MISSING` | `benchmark` | `warning` | Blocks benchmark readiness |

## Validation States

- `unchecked`: no validator report has been produced.
- `invalid`: at least one unaccepted error or blocker exists.
- `valid-with-warnings`: no errors or blockers remain, but warnings require
  review.
- `approved`: a human has approved the FEASpec, no blockers remain, and any
  warnings are explicitly accepted.
- `rejected`: the reviewer rejected the candidate while preserving diagnostics
  and notes.

## Approval Rules

- A `FEASpecCandidate` cannot be treated as solver-ready.
- Approved FEASpec data requires a `human_review` block.
- Approved FEASpec data requires validation state `approved`.
- Approved FEASpec data requires no unresolved blockers.
- Warnings may remain only with explicit human acceptance.
- Low-confidence or missing-evidence items cannot be automatically approved.

## Solver Handoff Gate

Only an approved FEASpec may proceed toward future solver handoff. There must
be no automatic unreviewed solver execution from image, drawing, heuristic, or
VLM output.

The ProjectSchema bridge plan layer is implemented separately. Full
ProjectSchema persistence and ProjectSchema mutation are future work.
SolverAdapter handoff is future work. CalculiX or Abaqus export is future work.
This gate defines the validation contract only and does not generate or run
solver cases.

[FEASpec to ProjectSchema bridge design](feaspec_to_projectschema_bridge_design.md)
records that bridge boundary. It requires approved FEASpec data, a validator
report with no blockers, explicit units, provenance/evidence preservation,
bridge diagnostics, and unmapped-field reporting before a ProjectSchema draft
plan can be considered.

[FEASpec to ProjectSchema bridge implementation](feaspec_to_projectschema_bridge_implementation.md)
adds the experimental draft-plan layer. It does not implement full
ProjectSchema persistence, mutate ProjectSchema, generate solver exports, call
VLM APIs, handle credentials, or execute solvers.

## CalculiX-First Compatibility

The first planned compatibility path is CalculiX-first for small,
inspectable, educational linear-static cases. Future rules should initially
prefer:

- `linear_static_2d`
- `linear_static_2d_truss`
- simple beam, truss, frame, shell/plane-stress planning cases where the
  FEASpec fields are explicit and reviewable.

Unsupported problem types, unsupported element families, missing sections,
missing materials, ambiguous units, invalid targets, and unaccepted warnings
must produce diagnostics. No case generation is performed in this gate.

## Abaqus Optional/Non-Default Compatibility

Abaqus handling is optional_non_default only. Abaqus is never required, never
the default path, and never a base dependency. Any future Abaqus export planning
must be separate from the CalculiX-first path and must preserve the no
mandatory commercial solver boundary.

`FS_SOLVER_ABAQUS_NON_DEFAULT` should record that Abaqus-specific compatibility
is advisory and non-default if a future user explicitly selects that planning
path.

## Evidence/Confidence Policy

Evidence and confidence are review aids, not correctness guarantees.

- Low confidence blocks automatic approval.
- Missing evidence may block approval when the entity was inferred from image,
  drawing, heuristic, or VLM-like output.
- Human overrides must be tracked with the changed entity, accepted warning,
  reviewer action, and local notes.
- Confidence scores must remain visible in review reports.

## Benchmark Readiness

Benchmark readiness is validated through metadata and ground truth, not through
solver execution.

Future benchmark checks should require:

- `ground_truth_feaspec.json` loads through the FEASpec model layer.
- `expected_metrics.json` exists and includes planned metrics.
- `source_metadata.json` identifies synthetic placeholder state when no image
  is generated.
- expected diagnostic codes are declared for invalid fixtures.
- benchmark reports distinguish schema/diagnostic readiness from solver
  accuracy.

## Public API Contract

The implementation follow-up uses these API names:

```python
validate_feaspec(spec) -> FEASpecValidationReport
validate_for_solver(spec, solver_id) -> FEASpecValidationReport
explain_diagnostics(report) -> list[str]
```

The design gate did not implement them. Current implementation evidence is
documented in
[FEASpec validator implementation](feaspec_validator_implementation.md).

## Future Implementation Slices

- `OSW-EXP-006_FEASPEC_VALIDATOR_IMPLEMENTATION`
- `OSW-EXP-007_FEASPEC_TO_PROJECTSCHEMA_BRIDGE_DESIGN`
- `OSW-EXP-008_FEASPEC_TO_PROJECTSCHEMA_BRIDGE_IMPLEMENTATION`
- `OSW-EXP-009_FEASPEC_TO_CALCULIX_CASE_PLANNING`

Each future slice must preserve the candidate/approved boundary, human review,
no automatic unreviewed solver execution, no mandatory Abaqus, and no
industrial certification claim.

## Examples Mapping

- `invalid_missing_units`: should produce `FS_UNITS_MISSING_SYSTEM`,
  `FS_LOAD_MISSING_UNITS`, or another explicit unit diagnostic.
- `invalid_unconnected_graph`: should produce
  `FS_GEOM_DISCONNECTED_GRAPH`.
- `invalid_load_target`: should produce `FS_LOAD_INVALID_TARGET`.
- approved cantilever: should remain eligible for human-reviewed
  CalculiX-first preparation planning, not automatic execution.
- approved truss: should remain eligible for human-reviewed CalculiX-first
  preparation planning, not automatic execution.

## Known Limitations

- Experimental design only.
- No full physics validation.
- No numerical rigid-body mode solve.
- No mesh generation.
- No full ProjectSchema persistence or ProjectSchema mutation.
- No solver adapter or exporter.
- No solver execution.
- No VLM API or credentials.
- No industrial certification.
