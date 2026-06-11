# FEASpec validator implementation

Status: experimental semantic validator implemented. This is not a full
physics validator, does not execute solvers, and does not implement a
ProjectSchema bridge.

## Release Context

`v0.1.4-rc1` is a public prerelease. This validator report layer is
post-release development on `develop`; it does not change the public release,
release tag, release assets, or version metadata.

## Package Path

The implementation lives under:

- `src/osw/experimental/feaspec/`

The new modules are:

- `diagnostics.py`
- `validator.py`

They use only the Python standard library and existing FEASpec model layer.

## Public API

- `validate_feaspec(spec_or_dict, *, require_approval=False)`
- `validate_for_solver(spec_or_dict, solver_id="calculix")`
- `validate_benchmark_seed(seed_dir_or_paths)`
- `explain_diagnostics(report)`

The API accepts FEASpec model instances, dictionaries, or JSON paths where
appropriate. It returns `FEASpecValidationReport` rather than mutating project
state or preparing solver files.

## Diagnostic Model

Validator diagnostics use:

- severity: `info`, `warning`, `error`, `blocker`;
- category: schema, units, geometry, material, section, boundary condition,
  load, dimension, evidence, human review, solver compatibility, or benchmark;
- diagnostic code from the reserved `FS_*` catalog;
- blocking flags for approval and future solver handoff.

The report exposes `is_valid`, `has_blockers`, `has_errors`,
`can_be_approved`, `can_handoff_to_solver`, phase results, and the raw
diagnostic list.

`can_handoff_to_solver` is only true for reports produced through
`validate_for_solver(...)` after the requested solver compatibility phase
passes. A plain `validate_feaspec(...)` report can show approval readiness, but
does not by itself authorize solver handoff.

## Validation Phases

The implementation covers field-level phases:

- schema/model;
- units;
- geometry graph;
- material/section;
- boundary condition;
- load;
- evidence/confidence;
- human review;
- solver compatibility;
- benchmark readiness.

These phases validate explicit units, geometry IDs and references,
connectivity, material/section presence, boundary-condition and load targets,
load units, evidence/confidence presence, approved human-review state, planned
solver compatibility metadata, and benchmark seed metadata.

## Candidate Vs Approved Behavior

`FEASpecCandidate` remains untrusted and is not solver-ready. Candidate reports
include a human-review diagnostic that blocks future solver handoff.

Approved FEASpec data requires:

- `human_review`;
- `validation.state: "approved"`;
- no blockers;
- no unaccepted errors.

Warnings may still require explicit user acceptance in a future review UI.

## Solver Compatibility

Solver compatibility checks are field-level only.

- CalculiX remains the first planned path for small educational linear-static
  FEASpec cases.
- Abaqus remains optional and non-default only.
- Unknown solver IDs emit unsupported compatibility diagnostics.
- No exporter, input deck, script, mesh, external command, or solver run is
  generated.

## Bridge Design Follow-Up

[FEASpec to ProjectSchema bridge design](feaspec_to_projectschema_bridge_design.md)
records the next design-only boundary after this validator report layer. It
requires an approved FEASpec, a validator report with no blockers, explicit
units, provenance/evidence preservation, bridge diagnostics, and unmapped-field
reporting before any future ProjectSchema draft can be produced.

That bridge design remains documentation only. It does not add source bridge
implementation, mutate ProjectSchema, implement SolverAdapter/export handoff,
generate CalculiX or Abaqus files, call VLM APIs, handle credentials, or execute
solvers.

## Examples And Benchmark Coverage

The validator is covered against:

- approved examples: cantilever beam and 2D truss;
- candidate examples: cantilever beam, 2D truss, and plate with hole;
- invalid examples: missing units, unconnected graph, and invalid load target;
- benchmark seeds: `cantilever_001`, `cantilever_002`, `truss_001`,
  `truss_002`, `frame_001`, and `plate_with_hole_001`.

Benchmark readiness checks verify required seed files, source metadata,
expected metrics, and ground-truth FEASpec loading. They do not compute VLM
scores and do not execute solvers.

## Non-Goals

- No full physics validation.
- No numerical rigid-body mode solve.
- No mesh generation.
- No ProjectSchema bridge.
- No solver adapter or exporter.
- No CalculiX case generation.
- No Abaqus export.
- No VLM API, provider client, credentials, or API keys.
- No solver execution.
- No industrial certification, compliance, or production CAE claim.
- No topology optimization implementation.

## Next Implementation Slices

- `OSW-EXP-007_FEASPEC_TO_PROJECTSCHEMA_BRIDGE_DESIGN`
- `OSW-EXP-008_FEASPEC_TO_PROJECTSCHEMA_BRIDGE_IMPLEMENTATION`
- `OSW-EXP-009_FEASPEC_HUMAN_REVIEW_UI_DESIGN`
- `OSW-EXP-010_FEASPEC_TO_CALCULIX_CASE_PLANNING`
