# FEASpec to ProjectSchema bridge implementation

Status: experimental bridge plan layer implemented. It does not mutate
ProjectSchema, does not persist ProjectSchema files, does not export solver
cases, and does not execute solvers.

Related release: `v0.1.4-rc1`

Related design: [FEASpec to ProjectSchema bridge design](feaspec_to_projectschema_bridge_design.md)

## Release Context

`v0.1.4-rc1` is a public prerelease. This implementation is post-release
development on `develop`; it does not change the public release, release tag,
release assets, or version metadata.

The bridge is experimental VFEA infrastructure. It creates an inspectable draft
plan from approved FEASpec data and validator evidence. It is not full
ProjectSchema persistence, a solver exporter, VFEA completion, or solver
execution.

## Package Path

The implementation lives under:

- `src/osw/experimental/feaspec/project_bridge.py`
- `src/osw/experimental/feaspec/bridge_diagnostics.py`

These modules use only Python standard-library helpers and the existing
experimental FEASpec model and validator layers.

## Public API

- `plan_project_from_feaspec(spec_or_dict, *, target_solver="calculix")`
- `explain_bridge_plan(plan)`

`plan_project_from_feaspec` accepts a FEASpec model, dictionary, or JSON path.
It validates the input with `validate_for_solver(...)`, checks bridge
preconditions, and returns a `FEASpecProjectBridgePlan`.

`explain_bridge_plan` returns concise user-readable status, diagnostic, and
extension-need messages. It does not execute any external process.

## Bridge Result Objects

The public result objects are:

- `FEASpecProjectBridgePlan`
- `FEASpecProjectDraft`
- `FEASpecProjectProvenance`
- `FEASpecProjectExtensionNeed`
- `FEASpecBridgeDiagnostic`
- `BridgeStatus`

The plan includes:

- `project_draft`
- `extension_needs`
- `unmapped_fields`
- `diagnostics`
- `provenance`
- `validator_report`
- `solver_target`
- `solver_export_performed=False`
- `solver_execution_performed=False`

The draft contains a ProjectSchema-compatible dictionary where safe, plus
FEASpec-native graph, section, load, dimension, evidence, and confidence data
that current ProjectSchema cannot represent losslessly.

## Preconditions

Bridge planning requires:

- approved FEASpec input, not `FEASpecCandidate`;
- `human_review.action` set to `approved`;
- validator report with no blockers or errors;
- explicit units for bridge-critical quantities;
- valid boundary-condition and load targets;
- supported solver target metadata.

Candidates, invalid examples, unknown solver targets, invalid load targets,
and missing load units return a blocked plan with bridge diagnostics.

## Mapping Summary

| FEASpec area | Bridge plan mapping |
| --- | --- |
| source/provenance | `FEASpecProjectProvenance.source`, evidence mapping, Project metadata |
| units | `FEASpecProjectDraft.units` and ProjectSchema-compatible `units` |
| geometry graph | draft `geometry_graph` plus ProjectSchema geometry metadata; no meshing |
| materials | draft materials and ProjectSchema-compatible material entries where safe |
| sections | draft sections plus extension needs |
| boundary conditions | draft boundary conditions and ProjectSchema boundary-style records |
| loads | draft loads and boundary-style preview records plus load extension needs |
| dimensions | draft dimensions plus dimension extension needs |
| assumptions | draft assumptions and project/report notes |
| evidence/confidence | provenance records and mapping metadata |
| validation/diagnostics | validator summary plus bridge diagnostics |
| solver target metadata | `solver_target`, prepare-only solver config metadata, no export/run |

The bridge records `unmapped_fields` for graph-native geometry, evidence,
sections, loads, and dimensions that current ProjectSchema cannot represent
without future schema decisions.

## Diagnostics

Bridge diagnostics use the `FB_*` codes reserved by the design:

- `FB_APPROVAL_REQUIRED`
- `FB_VALIDATION_BLOCKED`
- `FB_UNSUPPORTED_GEOMETRY`
- `FB_UNMAPPED_REGION`
- `FB_MISSING_MATERIAL`
- `FB_UNSUPPORTED_SECTION`
- `FB_INVALID_BC_TARGET`
- `FB_INVALID_LOAD_TARGET`
- `FB_UNSUPPORTED_LOAD_TYPE`
- `FB_UNITS_UNSUPPORTED`
- `FB_SOLVER_TARGET_UNSUPPORTED`
- `FB_PROVENANCE_INCOMPLETE`

Blocker and error diagnostics block bridge output. Warnings may produce a
`draft-ready-with-warnings` plan, but warnings do not authorize solver handoff.

## Solver Handoff Boundary

The bridge stops at a draft plan. It does not:

- create solver decks;
- persist ProjectSchema files;
- call SolverAdapter;
- call runner code;
- execute solvers;
- call VLM APIs;
- handle credentials;
- install dependencies.

The default target remains CalculiX-first. Explicit `target_solver="abaqus"`
records optional/non-default warning diagnostics and remains non-default.
Abaqus is not required.

## Examples Covered

Focused tests cover:

- approved cantilever example;
- approved truss example;
- candidate cantilever blocked with `FB_APPROVAL_REQUIRED`;
- invalid missing-units example blocked with `FB_UNITS_UNSUPPORTED`;
- invalid load-target example diagnosed with `FB_INVALID_LOAD_TARGET`;
- unknown solver target blocked with `FB_SOLVER_TARGET_UNSUPPORTED`;
- explicit Abaqus target warning without changing the default target.

## Non-Goals

- No full ProjectSchema persistence.
- No ProjectSchema schema mutation.
- No ProjectSchema migration.
- No CalculiX export.
- No Abaqus export.
- No solver adapter call.
- No runner call.
- No GUI change.
- No VLM API, provider client, credentials, or API keys.
- No topology optimization implementation.
- No automatic unreviewed solver execution.
- No solver execution.
- No industrial certification, compliance, production CAE, or accuracy claim.
- No native commercial CAD import.

## Next Implementation Slices

Potential follow-up gates:

- `OSW-EXP-009_FEASPEC_TO_CALCULIX_CASE_PLANNING`
  records the design-only CalculiX-first case planning boundary in
  [FEASpec to CalculiX case planning](feaspec_to_calculix_case_planning.md).
- `OSW-EXP-010_FEASPEC_TO_CALCULIX_CASE_PLAN_MODEL`
  adds the bounded experimental case-plan object in
  [FEASpec to CalculiX case-plan model](feaspec_to_calculix_case_plan_model.md).
- `OSW-EXP-011_FEASPEC_TO_CALCULIX_INP_WRITER_DESIGN`
  records the design-only no-run `.inp` writer boundary in
  [FEASpec to CalculiX INP writer design](feaspec_to_calculix_inp_writer_design.md).
- `OSW-EXP-012_FEASPEC_CALCULIX_INP_RENDERER_IMPLEMENTATION_NO_RUN`
  adds the no-run renderer in
  [FEASpec CalculiX INP renderer implementation](feaspec_to_calculix_inp_renderer_implementation.md).
  The renderer still does not mutate ProjectSchema, call SolverAdapter or
  runner code, execute CalculiX, or validate issue `#8`.
- `OSW-EXP-013_FEASPEC_HUMAN_REVIEW_UI_DESIGN`
- `OSW-EXP-014_FEASPEC_PROJECTSCHEMA_EXTENSION_DECISION`
