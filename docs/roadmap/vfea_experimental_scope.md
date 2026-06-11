# VFEA experimental scope definition

Status: planning-only VFEA scope, experimental. The full VFEA workflow is not
implemented; later post-release gates add an experimental FEASpec Python model
layer and an experimental semantic validator report layer only.

Related issue: `#17`

## Base Project Identity

OpenSolver Workbench is an educational/research Engineering Solver & Script
Workbench. It is not a MATLAB, Simulink, ANSYS, Abaqus, or commercial CAD
clone. It is not an industrial-certified solver platform, and users must
validate engineering results independently.

VFEA means Vision-to-FEA in this planning document. It is a possible future
experimental plugin line for assisted finite-element setup from drawings,
images, or problem descriptions. It is not core OSW solver behavior and the
full workflow is not implemented in the current codebase.

## Problem Statement

Drawing, image, and problem-description assisted FEA setup could help users
draft simple educational models faster. It is also risky. Geometry can be
hallucinated, units can be ambiguous, loads and boundary conditions can be
misread, and a plausible looking model can still be physically wrong.

The scope therefore starts with a planning-only experimental plugin concept:
convert untrusted visual or textual input into an inspectable FEASpec candidate,
validate it, require human review, and only then allow an approved path into
normal OSW project and solver-adapter workflows.

## Core Principle

There must be no automatic unreviewed solver execution from image or VLM output.

Any image, drawing, heuristic, or model output is untrusted draft evidence until
the user inspects and approves the FEASpec. A future implementation must surface
uncertainty, diagnostics, missing data, assumptions, and solver compatibility
before any export or run handoff is considered.

## Proposed Architecture

```text
Drawing/Image input
  + optional problem statement text
  -> provider layer
       - ManualAnnotationProvider
       - HeuristicProvider
       - VLMProvider later
  -> FEASpecCandidate
  -> FEASpecValidator
  -> Human Review UI
  -> approved FEASpec
  -> ProjectSchema bridge
  -> CalculiX-first export path
  -> ResultDataset/report path
```

### Input

- Drawing or image file supplied by the user.
- Optional problem statement text describing geometry, dimensions, loads,
  materials, fixtures, and intended analysis type.
- Optional manual annotations created by a user in a future review UI.

### Provider Layer

- `ManualAnnotationProvider`: future planning name for user-created annotations
  without external AI.
- `HeuristicProvider`: future planning name for deterministic extraction such
  as line/region candidates, dimensions, or labels.
- `VLMProvider`: future planning name for optional model-assisted
  interpretation. It must remain optional, guarded, and separate from base OSW.

This gate does not add provider code, image processing, VLM integration, API
keys, credentials, or configuration files.

Later post-release FEASpec work may add Python model objects, structural basic
checks, and field-level semantic validator reports. That does not implement
providers, VFEA, the full physics validator, ProjectSchema bridging, solver
adapters, exporters, or solver execution.

### FEASpec Candidate

`FEASpecCandidate` is the untrusted draft interpretation created by providers.
It can be incomplete and can contain confidence, evidence, and diagnostics.

### FEASpec Validator

`FEASpecValidator` is the planned validation boundary. A post-release
experimental report layer now covers field-level diagnostics for missing units,
missing materials, disconnected geometry, invalid load targets, human-review
state, solver compatibility, and benchmark readiness. It still does not perform
full physics validation, numerical rigid-body mode solving, mesh generation,
ProjectSchema bridging, exporter generation, or solver execution.

### Human Review UI

The Human Review UI is a future planning surface for inspecting candidate
nodes, connectivity, dimensions, loads, boundary conditions, materials, units,
confidence, assumptions, and diagnostics. Users must approve a reviewed FEASpec
before export or run handoff.

### Approved FEASpec

An approved FEASpec is a reviewed input object for normal OSW workflows. It is
not proof of engineering correctness. It is a user-approved, validated draft
that can be bridged into ProjectSchema and solver-adapter planning.

## FEASpec IR Planning

The FEASpec intermediate representation should be small, explicit, and
inspectable. Candidate fields include:

- `source`: image path, annotation source, provider name, and provenance.
- `problem_type`: analysis family such as simple 2D/3D linear static.
- `units`: length, force, stress, mass, time, and temperature assumptions.
- `geometry_graph`: nodes, edges, regions, features, dimensions, and labels.
- `materials`: names, properties, units, and confidence/evidence.
- `boundary_conditions`: targets, constraint type, direction, and evidence.
- `loads`: targets, load type, magnitude, direction, units, and evidence.
- `dimensions`: extracted or user-provided dimensions with units and confidence.
- `assumptions`: inferred simplifications that need review.
- `confidence`: per-item confidence or uncertainty flags.
- `evidence`: text spans, image regions, annotations, or provider diagnostics.
- `diagnostics`: warnings, errors, missing data, and validation messages.

Bare numeric engineering quantities should not cross the project boundary
without units.

## Human Review Requirements

A future VFEA workflow must require users to inspect:

- nodes, edges, regions, and connectivity;
- loads, boundary conditions, materials, and units;
- dimensions and assumed scale;
- solver compatibility warnings;
- confidence/evidence for inferred items;
- missing information and ambiguity diagnostics.

Users must approve the reviewed FEASpec before any export or solver run handoff.
Uncertainty must be visible; low-confidence or missing items must not be hidden
behind a successful-looking result.

## Validation Requirements

Before any approved FEASpec can bridge into ProjectSchema or solver-adapter
planning, validation should cover:

- schema validity;
- graph connectivity;
- missing units and incompatible unit systems;
- missing materials or incomplete material properties;
- invalid load or boundary-condition targets;
- likely rigid body modes;
- unsupported problem types or element families;
- solver compatibility for the selected export path;
- diagnostics severe enough to block export.

Validation is evidence for review, not certification.

## Benchmark Requirements

Benchmarking should use curated, synthetic drawings before any live user data or
VLM provider integration is trusted. Suggested assets:

- synthetic line drawings with known nodes and edges;
- simple cantilever, truss, plate-with-hole, and bracket-style educational
  examples;
- ground-truth FEASpec files;
- deliberately ambiguous drawings to verify uncertainty reporting;
- negative fixtures with missing units, impossible loads, and disconnected
  geometry.

Suggested metrics:

- schema validity rate;
- node precision and recall;
- connectivity F1;
- boundary-condition detection accuracy;
- load detection accuracy;
- dimension extraction accuracy;
- material extraction accuracy;
- case generation success after human-approved correction;
- result sanity checks for approved benchmark cases.

Benchmark results must not be presented as industrial certification.

## Solver Strategy

The preferred planning path is CalculiX-first because OSW already has bounded
educational CalculiX adapter and fixture evidence. A future VFEA implementation
should plan export around small, inspectable, linear-static educational cases
first.

Abaqus may be discussed only as optional, non-default export planning. OSW must not require Abaqus, must not depend on commercial solver availability, and must
not imply Abaqus compatibility is present.

No commercial solver execution is part of this scope definition.

## ResultDataset And Report Path

If a future VFEA workflow reaches an approved solver-adapter path, results
should return through existing OSW contracts:

- ProjectSchema records reviewed inputs, assumptions, and diagnostics.
- Solver adapters prepare or import bounded cases.
- ResultDataset stores summary data and parsed results.
- Reports disclose source, assumptions, validation status, limitations, and
  user approval checkpoints.

Reports must not overstate the reliability of image/VLM interpretation.

## Future Topology Optimization

Topology optimization is a separate future plugin concept. A possible later
educational path could use a 2D SIMP-style demonstration, but it is outside
`OSW-EXP-001`.

Topology optimization must not be bundled into the initial VFEA scope, must not
be implied by FEASpec planning, and must have its own validation and review
gate before any implementation.

## In Scope For Next Prompt

The next prompt may work on:

- docs/spec only or schema planning;
- FEASpec IR design;
- validator requirements;
- benchmark design;
- human review flow design;
- explicit provider contracts as planning text;
- explicit non-goals and risk controls.

## Out Of Scope

- Implementation code.
- VFEA schema implementation.
- VLM API integration.
- Provider credentials, API keys, or secrets.
- Image processing implementation.
- Drawing annotation UI implementation.
- FEASpec full physics validator implementation.
- Automatic solver execution.
- CalculiX exporter implementation.
- Abaqus exporter implementation.
- Requiring Abaqus or any commercial solver.
- Topology optimization implementation.
- Industrial certification, compliance, or production accuracy claims.
- Native commercial CAD import.
- GitHub Release edits, release assets, tags, or package version changes.

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Hallucinated geometry | Bad model topology or missing features | Require visual evidence, confidence, graph validation, and human approval. |
| Wrong units or scale | Loads, dimensions, and material properties become invalid | Require explicit units, unit diagnostics, and review checkpoints. |
| Unsafe load or boundary-condition inference | Physically invalid or misleading case setup | Validate targets, directions, magnitudes, and rigid body modes before export. |
| Overtrust in VLM output | Users may treat draft interpretation as correct | Label output as candidate data and require human review before approval. |
| Benchmark overfitting | Good benchmark scores fail to generalize | Include negative and ambiguous fixtures; separate benchmark claims from certification. |
| Commercial solver dependency creep | Scope drifts toward proprietary automation | Keep CalculiX-first planning and Abaqus optional/non-default planning only. |

## Next Prompt

Recommended next prompt: `OSW-EXP-002_FEASPEC_IR_DESIGN`.

Follow-up design evidence: [FEASpec IR design](../experimental/feaspec_ir_design.md)
defines the planning-only intermediate representation contract for future
Vision-to-FEA work. It keeps `FEASpecCandidate` untrusted until validation and
human approval, requires explicit units and diagnostics, preserves
confidence/evidence, and keeps solver compatibility CalculiX-first with Abaqus
optional and non-default. It does not implement FEASpec, VFEA, VLM APIs,
credentials, solver execution, or topology optimization.

Example and seed evidence:
[FEASpec examples](../experimental/feaspec_examples.md) and
[FEASpec benchmark seeds](../experimental/feaspec_benchmark_seeds.md) provide
canonical JSON examples and synthetic benchmark seed fixtures for future model
and validator work. They remain docs/fixtures only and do not add solver output,
VLM integration, or certification claims.

Validator design evidence:
[FEASpec validator design](../experimental/feaspec_validator_design.md) defines
the future diagnostic taxonomy, rule catalog, human-review approval gates,
solver handoff block rules, CalculiX-first compatibility checks, Abaqus
optional/non-default handling, and benchmark readiness requirements. It is
design-only and does not implement a production validator, ProjectSchema
bridge, solver exporter, VLM provider, or solver execution.

Validator implementation evidence:
[FEASpec validator implementation](../experimental/feaspec_validator_implementation.md)
adds an experimental semantic validator report layer for existing FEASpec
models, examples, and benchmark seed fixtures. It produces structured
diagnostics and solver handoff blockers, keeps candidates untrusted, and keeps
CalculiX compatibility field-level only. It does not implement VFEA,
ProjectSchema bridging, CalculiX or Abaqus export, VLM provider integration,
credentials, mesh generation, numerical physics validation, or solver
execution.

Alternative if maintainers decide this scope definition is complete:
`OSW-EXP-001A_VFEA_ISSUE_CLOSURE`.
