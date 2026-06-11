# FEASpec Python models

Status: implemented as an experimental model layer with an experimental
semantic validator report layer; no full physics validator, no ProjectSchema
bridge, and no solver execution.

## Release Context

`v0.1.4-rc1` is a public prerelease. This model layer is post-release
development on `develop` and does not change the published release, release
assets, or tag.

## Package Path

The experimental package lives at:

- `src/osw/experimental/feaspec/`

It is intentionally separate from core `ProjectSchema`, solver adapters, GUI
code, and external provider integrations.

## Public API

The first public API is:

- `load_feaspec(path)`
- `dump_feaspec(spec, path)`
- `parse_feaspec_dict(data)`
- `FEASpecCandidate`
- `FEASpec`
- `FEASpecDocument`
- `ValidationState`
- `SpecType`
- `FEASpecModelError`
- `FEASpecDiagnosticError`

Validator report API:

- `validate_feaspec`
- `validate_for_solver`
- `validate_benchmark_seed`
- `explain_diagnostics`
- `FEASpecValidationReport`
- `FEASpecValidationDiagnostic`
- `DiagnosticSeverity`
- `DiagnosticCategory`
- `DiagnosticCode`

The implementation uses Python standard-library dataclasses and JSON helpers.
No new dependency is required.

## Candidate Vs Approved Behavior

`FEASpecCandidate` is untrusted draft data. It may carry warnings,
uncertainty, incomplete assumptions, and diagnostic evidence. A candidate is
not approved for solver handoff and must not be used for automatic unreviewed
solver execution.

`FEASpec` represents the approved document shape. An approved document requires
`human_review` and `validation.state: "approved"`. That approval only prepares
data for a future bridge design; the bridge is not implemented in this gate.

## Basic Checks

The `basic_checks` module performs only structural checks:

- required top-level fields;
- explicit units at the document level and quantity blocks;
- unique geometry IDs;
- edge endpoints that reference known nodes;
- boundary-condition and load target references that point to known geometry;
- approved documents require human review;
- approved documents require approved validation state.

The checks also make the existing invalid examples surface expected diagnostic
codes. They are structural checks, not the semantic validator report layer or a
production/full physics validator.

## Validator Design Follow-Up

[FEASpec validator design](feaspec_validator_design.md) records the semantic
validator contract for this model layer. It defines the validation
pipeline, diagnostic model, severity taxonomy, rule catalog, human-review
approval rules, solver handoff gate, CalculiX-first compatibility, Abaqus
optional/non-default handling, and benchmark readiness checks.

[FEASpec validator implementation](feaspec_validator_implementation.md) adds an
experimental semantic report layer for those rules. It remains field-level and
does not implement a full physics validator, ProjectSchema bridge,
SolverAdapter/export handoff, VLM API, credentials, or solver execution.

[FEASpec to ProjectSchema bridge design](feaspec_to_projectschema_bridge_design.md)
records a later design-only mapping from approved FEASpec data and validator
reports into a future ProjectSchema draft. It defines preconditions, field
mappings, bridge diagnostics, provenance handling, unmapped-field reporting, and
ProjectSchema extension needs without adding bridge source code, mutating
ProjectSchema, implementing solver adapters/exporters, or executing solvers.

## Examples Coverage

The model layer loads the current files under `examples/feaspec/`:

- candidate examples;
- approved examples;
- invalid diagnostic examples when `allow_diagnostics=True`.

It also loads approved ground-truth FEASpec files in
`tests/fixtures/feaspec/benchmark_seeds/`. Benchmark metrics remain planned
schema and detection targets, not solver accuracy or VLM benchmark scores.

## Non-Goals

- No full physics validator.
- No VFEA implementation.
- No VLM API, provider client, credential, or API key handling.
- No automatic solver execution.
- No CalculiX generator.
- No Abaqus exporter.
- Abaqus remains optional/non-default if discussed; there is no mandatory
  Abaqus or commercial solver dependency.
- No topology optimization implementation.
- No industrial certification, compliance, or production CAE claim.
- No native commercial CAD import.

## Next Implementation Slices

Possible follow-up gates:

- `OSW-EXP-006_FEASPEC_VALIDATOR_IMPLEMENTATION`
- `OSW-EXP-007_FEASPEC_TO_PROJECTSCHEMA_BRIDGE_DESIGN`
- `OSW-EXP-008_FEASPEC_TO_PROJECTSCHEMA_BRIDGE_IMPLEMENTATION`
- `OSW-EXP-009_FEASPEC_HUMAN_REVIEW_UI_DESIGN`
- `OSW-EXP-010_FEASPEC_TO_CALCULIX_CASE_PLANNING`
