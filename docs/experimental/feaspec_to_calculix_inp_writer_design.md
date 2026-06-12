# FEASpec to CalculiX INP writer design

Status: design-only. There is no writer implementation, no generated `.inp`
files, no CalculiX export, no SolverAdapter handoff, no runner handoff, and no
solver execution in this gate.

Related release: `v0.1.4-rc1`

Follow-up implementation evidence:
[FEASpec CalculiX INP renderer implementation](feaspec_to_calculix_inp_renderer_implementation.md)
records the later OSW-EXP-012 no-run renderer. That follow-up renders
deterministic text only from writer-ready case plans and preserves this design
boundary: no `ccx` invocation, no SolverAdapter or runner call, no ProjectSchema
mutation, no live issue `#8` validation, and no solver execution.

## Release Context

`v0.1.4-rc1` is a public prerelease. This document records post-release
development planning on `develop`; it does not edit the public release, mutate
tags, upload assets, install solvers, or run live optional validation.

## Relationship To Existing Layers

The future writer is downstream of the current experimental FEASpec layers:

- FEASpec models load and preserve candidate or approved data.
- The FEASpec validator reports approval blockers, solver handoff blockers,
  field-level CalculiX compatibility, and benchmark readiness.
- The ProjectSchema bridge creates an inspectable draft plan without mutating
  ProjectSchema or exporting solver cases.
- The CalculiX case-plan model creates a `FEASpecCalculiXCasePlan` with
  reviewed records, `FC_*` diagnostics, and readiness flags.
- A future `.inp` writer may render deterministic text only after the case plan
  is explicitly writer-ready.

The writer sits after case planning and before any file export or run workflow.
It must not bypass human review, validation diagnostics, or the installed-only
live validation track.

## Writer Goals

The first writer scope should support small educational linear-static
CalculiX cases only. The writer goals are:

- deterministic `.inp` text generation from reviewed planning records;
- traceable provenance comments in the generated text;
- no implicit solver execution;
- explicit diagnostics for unsupported or incomplete plans;
- a narrow baseline that can be tested with text fixtures before any live
  `ccx` validation.

## Writer Preconditions

A future writer may render or write only when all of these preconditions hold:

- `FEASpecCalculiXCasePlan.ready_for_inp_writer == true`;
- `FEASpecCalculiXCasePlan.ready_for_solver_execution == false` remains true
  until a separate run gate exists;
- no blocker diagnostics remain on the case plan;
- explicit units are present for model, material, section, boundary-condition,
  and load quantities;
- explicit node and element topology are present;
- explicit materials and sections are mapped to supported element families;
- reviewed boundary-condition and load targets resolve to known nodes,
  elements, sets, faces, or surfaces;
- static step and output request metadata are present and supported;
- provenance and human-review metadata are complete enough for generated
  comments.

Failure to satisfy a precondition returns writer diagnostics and no rendered
solver deck text.

## Proposed Writer API

The future API should be small and reviewable:

```text
render_calculix_inp(case_plan) -> CalculiXInpRenderResult
write_calculix_inp(case_plan, path, *, overwrite=False) -> CalculiXInpWriteResult
explain_inp_render_result(result) -> list[str]
```

There is no implementation in this gate. The render API should produce text in
memory only. The write API should be a later explicit writer gate and should
refuse to overwrite existing files unless `overwrite=True` is supplied.

## Proposed Result Objects

Future result objects should be serializable and diagnostic-first:

- `CalculiXInpRenderResult`: status, rendered text, sections, diagnostics,
  source case-plan ID, provenance summary, and `solver_execution_performed=False`.
- `CalculiXInpWriteResult`: render result, requested path, written path when
  allowed, overwrite decision, diagnostics, and
  `solver_execution_performed=False`.
- `CalculiXInpSection`: section name, ordered lines, source record IDs, and
  warnings.
- `CalculiXInpDiagnostic`: stable `FW_*` diagnostic code, severity, message,
  target reference, source field, suggested fix, and blocking flags.

Result objects must not contain solver process handles, subprocess arguments,
runner requests, or implicit permission to run `ccx`.

## File-Section Ordering

The writer should emit sections in this deterministic order:

1. header/provenance comments;
2. `*NODE`;
3. `*ELEMENT`;
4. material cards;
5. section/property cards;
6. boundary cards;
7. load cards;
8. `*STEP`;
9. output request cards;
10. `*END STEP`.

The output should be stable across platforms. Normalization for future tests
should cover line endings and insignificant trailing whitespace only.

## Header/Provenance Comments

Header comments should include:

- source FEASpec ID;
- case-plan ID;
- human review information;
- validator and bridge summary;
- warning that the file is generated from experimental FEASpec evidence;
- explicit no industrial certification claim;
- no automatic solver execution statement;
- release or package version when available.

The comments are traceability metadata, not proof of solver correctness.

## Node Section Strategy

The `*NODE` section should use deterministic node ordering. Numeric formatting
must be explicit and stable, for example a fixed precision or a documented
compact scientific format.

The first scope should support only explicit coordinate systems already present
in the case plan. The writer must not infer missing coordinates, rescale
coordinates silently, or generate mesh nodes from FEASpec geometry graph edges.

Missing node topology blocks rendering with `FW_NODE_MISSING` or
`FW_MESH_REQUIRED`.

## Element Section Strategy

The `*ELEMENT` section should support only explicit, reviewed CalculiX element
types. Unsupported types block rendering with `FW_UNSUPPORTED_ELEMENT_TYPE`.

The writer must not perform automatic meshing and must not silently convert
geometry graph edges, regions, or drawing evidence into elements. Element
connectivity must reference known node IDs, and missing connectivity blocks
rendering with `FW_ELEMENT_MISSING` or `FW_MESH_REQUIRED`.

## Material Cards

The baseline material scope is isotropic linear elastic material data. Required
properties should include a material ID, Young's modulus, Poisson ratio when
needed by the target element family, and explicit units.

Missing or incomplete properties block rendering with `FW_MATERIAL_MISSING`.
Material cards should preserve unit notes as comments because CalculiX input
expects consistent user-managed units.

## Section/Property Cards

Section and property cards should be staged by supported element family:

- solid sections first when explicit solid elements and material mappings exist;
- beam, truss, and shell sections only after their required area, inertia,
  thickness, orientation, or equivalent properties are explicit;
- unsupported sections block rendering with `FW_SECTION_MISSING` until a more
  specific future section diagnostic is added.

The writer must not invent default thickness, area, orientation, or section
properties.

## Boundary Cards

Boundary cards should map only reviewed targets. Degree-of-freedom mapping must
be explicit and visible. Invalid or unresolved targets block rendering with
`FW_BC_INVALID_TARGET`.

The writer must not add hidden stabilizing constraints, implicit fixed supports,
or default boundary conditions to make a case run.

## Load Cards

The first planned load subset is:

- concentrated force;
- pressure;
- distributed load.

Unsupported load kinds block rendering with `FW_LOAD_UNSUPPORTED_TYPE`.
Invalid or unresolved load targets block rendering with `FW_LOAD_INVALID_TARGET`.
Load unit comments should be preserved, and unit incompatibility blocks
rendering with a writer diagnostic rather than silent conversion.

## Step/Output Cards

The first step scope is static linear analysis only. Unsupported step metadata
blocks rendering with `FW_STEP_UNSUPPORTED`.

The output request baseline should stay minimal, such as displacement and stress
field output. Unsupported output requests block rendering with
`FW_OUTPUT_UNSUPPORTED`.

The writer may render `*STEP` and `*END STEP` in a future gate, but it must not
invoke `ccx` or request runner execution.

## Diagnostics

Future writer diagnostics use the `FW_*` prefix:

- `FW_PLAN_NOT_READY`
- `FW_MESH_REQUIRED`
- `FW_UNSUPPORTED_ELEMENT_TYPE`
- `FW_NODE_MISSING`
- `FW_ELEMENT_MISSING`
- `FW_MATERIAL_MISSING`
- `FW_SECTION_MISSING`
- `FW_BC_INVALID_TARGET`
- `FW_LOAD_INVALID_TARGET`
- `FW_LOAD_UNSUPPORTED_TYPE`
- `FW_STEP_UNSUPPORTED`
- `FW_OUTPUT_UNSUPPORTED`
- `FW_WRITE_PATH_EXISTS`
- `FW_PROVENANCE_INCOMPLETE`

Blocker diagnostics should prevent rendered text and file output. Warnings may
be returned only when they remain visible to the reviewer.

## Golden Fixture Strategy

Future golden `.inp` files should live under:

```text
tests/fixtures/feaspec/calculix_golden/
```

Those fixtures must be generated only in a future writer implementation gate.
This design gate creates no `.inp` output. Future golden writer tests should
compare normalized text. There is no solver execution in golden writer tests:
they should not execute `ccx`, call a runner, or require CalculiX to be
installed.

Golden fixtures should cover:

- a minimal writer-ready truss or solid example with explicit nodes and
  elements;
- unsupported element diagnostics;
- missing material or section diagnostics;
- invalid boundary-condition or load targets;
- path-exists behavior for the future write API.

## No-Run Safety Boundary

The writer boundary is strictly no-run:

- a future renderer may create text in memory;
- a future writer may write a reviewed file only in an explicit writer gate;
- the writer must not invoke `ccx`;
- the writer must not call SolverAdapter, runner, `ExternalCommandRunner`, or
  subprocess APIs;
- any run gate must be separate, installed-only, and opt-in.

This boundary keeps issue-specific live validation, deck writing, and external
execution separate and auditable.

## Relationship To Issue #8

Issue `#8` is live CalculiX `ccx` validation. It remains separate from this
writer design. This document does not validate a local `ccx` executable, does
not run live optional validation, does not close issue `#8`, and does not prove
that generated decks can solve correctly.

## Non-Goals

- No implementation.
- No `.inp` output in this gate.
- No generated `.inp` files.
- No CalculiX execution.
- No SolverAdapter or runner handoff.
- No subprocess or external command invocation.
- No ProjectSchema mutation.
- No Abaqus export.
- No topology optimization.
- No VLM API, provider client, credentials, or API keys.
- No automatic unreviewed solver execution.
- No live optional validation.
- No industrial certification, compliance, production CAE, or accuracy claim.
- No native commercial CAD import.

## Next Implementation Slices

- `OSW-EXP-012_FEASPEC_CALCULIX_INP_RENDERER_IMPLEMENTATION_NO_RUN`
- `OSW-EXP-013_FEASPEC_CALCULIX_INP_GOLDEN_FIXTURES`
- `OSW-EXP-014_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`
