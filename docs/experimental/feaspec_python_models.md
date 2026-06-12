# FEASpec Python models

Status: implemented as an experimental model layer with an experimental
semantic validator report layer and a follow-up experimental bridge plan layer;
no full physics validator, no full ProjectSchema persistence or schema
mutation, and no solver execution.

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
data for bounded bridge planning; full ProjectSchema persistence and
ProjectSchema mutation are not implemented in this gate.

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
does not implement a full physics validator, full ProjectSchema persistence,
ProjectSchema mutation, SolverAdapter/export handoff, VLM API, credentials, or
solver execution.

[FEASpec to ProjectSchema bridge design](feaspec_to_projectschema_bridge_design.md)
records the mapping from approved FEASpec data and validator reports into a
ProjectSchema draft plan. The follow-up
[FEASpec to ProjectSchema bridge implementation](feaspec_to_projectschema_bridge_implementation.md)
adds the experimental plan layer with preconditions, field mappings, bridge
diagnostics, provenance handling, unmapped-field reporting, and ProjectSchema
extension needs. It does not mutate ProjectSchema, implement full ProjectSchema
persistence, implement solver adapters/exporters, or execute solvers.

[FEASpec to CalculiX case planning](feaspec_to_calculix_case_planning.md)
defines the future CalculiX-first case-plan contract after approved FEASpec,
validator, and bridge evidence exist. It remains design-only and does not add a
case generator, `.inp` writer, SolverAdapter/exporter, runner call, live
optional validation, or solver execution.

[FEASpec to CalculiX case-plan model](feaspec_to_calculix_case_plan_model.md)
adds the bounded experimental case-plan object after bridge planning. It
preserves reviewed records and diagnostics, blocks candidates and bridge
blockers, reports `FC_MESH_REQUIRED` for examples without explicit mesh
topology, and keeps writer/export/execution behavior out of scope.

[FEASpec to CalculiX INP writer design](feaspec_to_calculix_inp_writer_design.md)
defines the future no-run writer contract after the case-plan model. It is
design-only and adds no writer implementation, `.inp` output, SolverAdapter
handoff, runner call, or solver execution.

[FEASpec CalculiX INP renderer implementation](feaspec_to_calculix_inp_renderer_implementation.md)
adds the later no-run renderer for writer-ready case plans. It renders
deterministic text only, writes only to caller-provided paths with overwrite
protection, and still does not run `ccx`, call SolverAdapter or runner code,
mutate ProjectSchema, or validate issue `#8`.

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
- `OSW-EXP-009_FEASPEC_TO_CALCULIX_CASE_PLANNING`
- `OSW-EXP-010_FEASPEC_TO_CALCULIX_CASE_PLAN_MODEL`
- `OSW-EXP-011_FEASPEC_TO_CALCULIX_INP_WRITER_DESIGN`
- `OSW-EXP-012_FEASPEC_CALCULIX_INP_RENDERER_IMPLEMENTATION_NO_RUN`
- `OSW-EXP-013_FEASPEC_HUMAN_REVIEW_UI_DESIGN`
- `OSW-EXP-014_FEASPEC_PROJECTSCHEMA_EXTENSION_DECISION`
