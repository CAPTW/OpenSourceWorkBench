# FEASpec to CalculiX case planning

Status: design-only. This document defines a future planning contract only:
there is no case generator, no `.inp` writer, no CalculiX export, no
SolverAdapter call, no runner call, no `ccx` execution, and no solver
execution in this gate.

Related release: `v0.1.4-rc1`

Follow-up implementation evidence:
[FEASpec to CalculiX case-plan model](feaspec_to_calculix_case_plan_model.md)
adds the scoped experimental model described here. The model returns
serializable planning records and diagnostics only; it still does not add a
case generator, `.inp` writer, CalculiX export, SolverAdapter call, runner
call, live `ccx` validation, or solver execution.

## Release Context

`v0.1.4-rc1` is a public prerelease. This planning document is post-release
development on `develop`; it does not change the public release, release tag,
release assets, package metadata, or version.

## Relationship To Existing Layers

The future FEASpec-to-CalculiX path must build on these existing layers:

- FEASpec models parse and preserve candidate or approved FEASpec data.
- FEASpec validator reports approval blockers, solver handoff blockers,
  field-level CalculiX compatibility, and benchmark readiness.
- FEASpec Project bridge planning returns a draft-ready or
  draft-ready-with-warnings bridge plan with provenance, diagnostics,
  extension needs, unmapped fields, and a ProjectSchema-compatible dictionary.
- Existing CalculiX deck tools can prepare bounded linear-static decks from
  explicit ProjectSchema, mesh topology, material, section, node set,
  boundary-condition, and load inputs.

This document sits between the bridge plan and any future CalculiX exporter. It
defines what a future case-plan object should contain before any `.inp` writer
or exporter is considered.

## Planning Goals

- Define a CalculiX-first educational linear-static subset.
- Protect solver handoff from incomplete FEASpec or bridge data.
- Preserve source provenance, evidence, confidence, review state, assumptions,
  unmapped fields, and diagnostics.
- Make unsupported geometry, missing mesh topology, unsupported loads, missing
  materials, missing sections, and insufficient constraints visible.
- Avoid automatic unreviewed solver execution from image, VLM, heuristic,
  bridge, or case-plan output.

## Preconditions

Future case planning may begin only when all of these conditions hold:

- input is an approved FEASpec, not a `FEASpecCandidate`;
- `human_review.action` is approved and visible;
- validator report has no blockers and no errors;
- bridge plan status is `draft-ready` or `draft-ready-with-warnings`;
- bridge plan includes explicit units and no bridge blockers;
- reviewed materials, sections, boundary conditions, loads, and target
  references are present;
- target solver is `calculix`;
- no warning is hidden from the reviewer before later case generation.

Failure to satisfy a precondition should produce a planning diagnostic and no
case-plan output.

## Future Case-Plan Object

A later implementation may define a serializable case-plan object with these
fields:

```text
FEASpecCalculiXCasePlan
  case_id
  source_feaspec_id
  target_solver
  unit_context
  nodes
  elements
  materials
  sections
  boundary_conditions
  loads
  steps
  output_requests
  provenance_comments
  diagnostics
  unmapped_fields
```

The object is a reviewed planning artifact. It is not a solver deck, not a
written `.inp` file, and not permission to execute `ccx`.

## Geometry And Mesh Strategy

There is no meshing in this gate. A FEASpec geometry graph is not enough for a
solver deck because CalculiX deck preparation requires explicit mesh topology,
node identifiers, element connectivity, element sets, node sets, and surfaces.

Future case planning must require an explicit mesh source before deck
generation. That source may be a reviewed MeshModel, a future reviewed
FEASpec mesh extension, or another explicit mesh artifact. Geometry-only graph
data should remain provenance and target-set evidence until mesh topology is
available.

Unsupported geometry blocks case generation. The plan must not infer hidden
mesh topology or silently convert graph edges into elements without a reviewed
element strategy.

## Node And Element Strategy

The first planned subset is small, educational, and linear-static:

- 1D truss or beam planning only after explicit element family selection;
- 2D plane-stress or shell-style educational planning only after explicit
  thickness or section data;
- 3D solid planning only when mesh connectivity and supported CalculiX element
  types are explicit.

Truss, beam, shell, plane-stress, and solid element decisions remain deferred
to a future case-plan model or writer design gate. Element type mapping must be
explicit, reviewed, and diagnostic-backed. Unsupported element choices should
emit `FC_UNSUPPORTED_ELEMENT_TYPE`.

## Materials And Sections

The baseline material scope is isotropic linear elastic material data with
explicit material IDs, Young's modulus, Poisson ratio, and units.

Future case planning should require:

- material IDs mapped from approved FEASpec or reviewed bridge data;
- explicit section IDs or target assignments;
- explicit thickness, area, or cross-section properties when required by the
  selected element family;
- visible provenance back to FEASpec material and section records.

Missing material data should emit `FC_MATERIAL_MISSING`. Missing or
unsupported section data should emit `FC_SECTION_MISSING` or a more specific
future section diagnostic.

## Boundary Conditions

Boundary-condition targets must resolve to reviewed target sets, nodes, edges,
faces, or element sets before any future deck writer can run. Degree-of-freedom
mapping must be explicit and visible.

Future planning should map only reviewed constraints such as fixed or
component displacement boundary conditions. Invalid targets should emit
`FC_BC_INVALID_TARGET`. Insufficient constraints should emit
`FC_BC_INSUFFICIENT_CONSTRAINTS` and block or warn according to the future
case-plan policy.

The planner must not create hidden stabilizing constraints just to make a model
run.

## Loads

The first planned load subset is:

- point force;
- pressure;
- distributed load.

Every load must include units, direction or component mapping, target
references, coordinate frame assumptions, and provenance. Invalid targets
should emit `FC_LOAD_INVALID_TARGET`. Unsupported load kinds should emit
`FC_LOAD_UNSUPPORTED_TYPE`. Missing or unsupported units should emit
`FC_UNITS_UNSUPPORTED`.

The planner must not create default loads, rescale loads silently, or map a
load onto a different target without review.

## Steps And Output Requests

The first planned analysis step is static linear. Unsupported steps should
emit `FC_STEP_UNSUPPORTED`.

Default output requests may be planned for displacement and stress summaries,
but they remain planning records only. Unsupported output requests should emit
`FC_OUTPUT_UNSUPPORTED`. No solver execution occurs in this design gate.

## Diagnostics

Future case planning diagnostics use the `FC_*` prefix:

- `FC_APPROVAL_REQUIRED`
- `FC_VALIDATION_BLOCKED`
- `FC_BRIDGE_BLOCKED`
- `FC_MESH_REQUIRED`
- `FC_UNSUPPORTED_GEOMETRY`
- `FC_UNSUPPORTED_ELEMENT_TYPE`
- `FC_MATERIAL_MISSING`
- `FC_SECTION_MISSING`
- `FC_BC_INVALID_TARGET`
- `FC_BC_INSUFFICIENT_CONSTRAINTS`
- `FC_LOAD_INVALID_TARGET`
- `FC_LOAD_UNSUPPORTED_TYPE`
- `FC_UNITS_UNSUPPORTED`
- `FC_STEP_UNSUPPORTED`
- `FC_OUTPUT_UNSUPPORTED`
- `FC_PROVENANCE_INCOMPLETE`

Blocker diagnostics should prevent case-plan output. Warning diagnostics may
remain only when visible and accepted by human review in a future workflow.

## Safety Boundary

This gate does not add:

- `.inp` writer behavior;
- case generator implementation;
- CalculiX export;
- SolverAdapter calls;
- runner calls;
- `ccx` execution;
- `subprocess` calls;
- automatic unreviewed solver execution;
- VLM APIs or provider credentials.

Any future implementation must keep preview, review, and explicit approval
separate from solver deck writing and solver execution.

## Relationship To Issue #8

Issue `#8` is live CalculiX `ccx` validation. It remains separate from this
planning gate.

This document does not validate a local `ccx` executable, does not run live
optional validation, and does not close issue `#8`. Future live validation must
run only on a prepared machine where `ccx` is already installed and under a
separate validation or closure gate.

## Abaqus Boundary

Abaqus remains optional and non-default. This CalculiX-first path does not add
an Abaqus exporter, does not require Abaqus, and does not add a commercial
solver dependency. Any Abaqus planning must remain separate and explicit.

## Test Strategy

Future tests should be network-free, solver-free, and independent of heavy
optional dependencies:

- approved cantilever bridge plan reaches case-plan readiness when explicit
  mesh topology and section data are available;
- approved truss bridge plan reaches case-plan readiness when explicit element
  family and target sets are available;
- candidates are rejected with `FC_APPROVAL_REQUIRED`;
- validator blockers are rejected with `FC_VALIDATION_BLOCKED`;
- bridge blockers are rejected with `FC_BRIDGE_BLOCKED`;
- missing mesh topology is blocked with `FC_MESH_REQUIRED`;
- invalid load and boundary targets produce `FC_LOAD_INVALID_TARGET` or
  `FC_BC_INVALID_TARGET`;
- insufficient constraints produce `FC_BC_INSUFFICIENT_CONSTRAINTS`;
- unsupported element and load types remain diagnostic-visible.

## Future Implementation Slices

- `OSW-EXP-010_FEASPEC_TO_CALCULIX_CASE_PLAN_MODEL` implemented the bounded
  experimental planning object in
  [FEASpec to CalculiX case-plan model](feaspec_to_calculix_case_plan_model.md).
- `OSW-EXP-011_FEASPEC_TO_CALCULIX_INP_WRITER_DESIGN` records the design-only
  future `.inp` renderer boundary in
  [FEASpec to CalculiX INP writer design](feaspec_to_calculix_inp_writer_design.md).
- `OSW-EXP-012_FEASPEC_CALCULIX_INP_RENDERER_IMPLEMENTATION_NO_RUN`
  adds a bounded no-run text renderer for writer-ready case plans, documented
  in
  [FEASpec CalculiX INP renderer implementation](feaspec_to_calculix_inp_renderer_implementation.md).
- `OSW-EXP-013_FEASPEC_CALCULIX_INP_GOLDEN_FIXTURES`
- `OSW-EXP-014_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`

## Non-Goals

- No implementation.
- No case generation.
- No `.inp` writer.
- No CalculiX export.
- No solver execution.
- No `ccx` execution.
- No SolverAdapter call.
- No runner call.
- No automatic unreviewed solver execution.
- No Abaqus export.
- No topology optimization.
- No live optional validation.
- No issue closure.
- No release, tag, or asset mutation.
- No industrial certification, compliance, production CAE, or accuracy claim.
- No native commercial CAD import.
