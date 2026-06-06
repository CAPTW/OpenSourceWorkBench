# FEASpec examples overview

Status: documentation and fixture examples loaded by the experimental FEASpec
Python model layer; no full validator, ProjectSchema bridge, solver adapter,
VLM API, or solver execution is implemented.

The canonical examples live under `examples/feaspec/`. They show the expected
shape of FEASpec data for the experimental model layer without adding a full
validator, ProjectSchema bridge, solver adapter, VLM API, provider credentials,
or solver execution.

## Candidate Vs Approved Examples

Candidate examples use `spec_type: "candidate"`. They are untrusted draft
objects and may include warnings, uncertainty, and review-required diagnostics.

Approved examples use `spec_type: "approved"`. They include a `human_review`
section and `validation.state: "approved"`. Approval in these examples only
means that a deterministic educational fixture was reviewed; it is not an
industrial certification claim and it does not imply solver execution.

Only approved FEASpec data may proceed toward future ProjectSchema or
SolverAdapter handoff. Candidate fixtures must not be treated as solver-ready.

## Valid Example List

- `examples/feaspec/cantilever_beam_candidate.json`
- `examples/feaspec/cantilever_beam_approved.json`
- `examples/feaspec/truss_2d_candidate.json`
- `examples/feaspec/truss_2d_approved.json`
- `examples/feaspec/plate_with_hole_candidate.json`

## Invalid Example List

- `examples/feaspec/invalid_missing_units.json`
- `examples/feaspec/invalid_unconnected_graph.json`
- `examples/feaspec/invalid_load_target.json`

Invalid examples are diagnostic fixtures. They are deliberately not approved
and must not be presented as runnable solver cases.

The future validator contract in
[FEASpec validator design](feaspec_validator_design.md) maps these invalid
fixtures to stable diagnostic categories and codes. The examples remain
fixtures only; they do not implement the validator or make any case
solver-ready.

## FEASpec IR Field Mapping

Each example includes the design fields from
[FEASpec IR design](feaspec_ir_design.md):

- `schema_version`
- `spec_type`
- `source`
- `problem_type`
- `units`
- `geometry`
- `materials`
- `sections`
- `boundary_conditions`
- `loads`
- `dimensions`
- `assumptions`
- `evidence`
- `confidence`
- `diagnostics`
- `validation`
- `solver_compatibility`

Approved examples also include `human_review`. Invalid examples include
`expected_diagnostics` so future validators can compare expected failure modes.

## Human Review Requirement

The examples preserve the human-review boundary:

- candidates remain untrusted;
- approved examples record the deterministic reviewer/action/timestamp
  placeholder;
- `approval_required_before_solver_case_generation` remains explicit;
- no example performs or implies solver execution.

## Non-Goals

- No full FEASpec validator.
- No ProjectSchema bridge.
- No VFEA implementation.
- No production validator.
- No ProjectSchema bridge.
- No SolverAdapter or CalculiX case generator.
- No solver execution.
- No VLM API integration.
- No credentials, API keys, or provider configuration.
- No mandatory Abaqus dependency.
- No topology optimization.
- No industrial certification.
- No native commercial CAD import.

## Future Use

Future Python models and validators should use these examples as compatibility
fixtures. An implementation gate should first make these examples parse through
the future model layer, then add validation checks that preserve the
candidate/approved boundary and explicit-unit requirements.

The next validator implementation gate should follow the design-only
diagnostic catalog in [FEASpec validator design](feaspec_validator_design.md)
before any ProjectSchema bridge, SolverAdapter/export path, or solver
execution gate is considered.
