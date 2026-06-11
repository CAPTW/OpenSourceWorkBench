# FEASpec to CalculiX case-plan model

Status: experimental case-plan model. This is a planning data layer only: it is
not a `.inp` writer, not a solver adapter, not a runner, and there is no solver
execution.

Related release: `v0.1.4-rc1`

Related design: [FEASpec to CalculiX case planning](feaspec_to_calculix_case_planning.md)

Follow-up design: [FEASpec to CalculiX INP writer design](feaspec_to_calculix_inp_writer_design.md)
defines the future no-run `.inp` renderer contract, writer diagnostics,
section ordering, and golden fixture strategy. It still does not implement a
writer, generate `.inp` files, call solver adapters, run `ccx`, or close issue
`#8`.

## Release Context

`v0.1.4-rc1` is a public prerelease. This implementation is post-release
development on `develop`; it does not edit the public release, mutate tags,
upload assets, install solvers, or run live optional validation.

## Purpose

The case-plan model converts an approved FEASpec bridge plan into an
inspectable CalculiX-first planning object. It preserves reviewed units,
geometry graph nodes, materials, sections, boundary conditions, loads,
provenance, bridge diagnostics, extension needs, and unmapped fields.

The model deliberately stops before deck writing. A FEASpec geometry graph
remains provenance and target evidence until explicit mesh or element topology
is available.

## Public API

The public package exports:

- `plan_calculix_case_from_feaspec`
- `plan_calculix_case_from_bridge`
- `explain_calculix_case_plan`

The returned object is `FEASpecCalculiXCasePlan`.

## Status Model

`CalculiXCaseStatus` values are:

- `blocked`
- `plan-ready`
- `plan-ready-with-warnings`

Approved examples without reviewed element topology currently return a blocked
plan with `FC_MESH_REQUIRED`. This is intentional: reviewed FEASpec geometry is
useful evidence, but it is not enough for a CalculiX input deck.

## Plan Records

The model defines these serializable record types:

- `CalculiXCaseNodePlan`
- `CalculiXCaseElementPlan`
- `CalculiXCaseMaterialPlan`
- `CalculiXCaseSectionPlan`
- `CalculiXCaseBoundaryConditionPlan`
- `CalculiXCaseLoadPlan`
- `CalculiXCaseStepPlan`
- `CalculiXCaseOutputRequestPlan`

Default step and output request records are metadata only. They do not imply
deck writing, export, or execution.

## Readiness Flags

`ready_for_inp_writer` is `false` unless the plan has no case-plan blockers and
contains explicit reviewed element topology.

`ready_for_solver_execution` is always `false`. Solver execution is outside
this model and remains a separate reviewed runner concern.

The result also records:

- `inp_writer_performed: false`
- `solver_execution_performed: false`

## Diagnostics

The `FC_*` diagnostic catalog is:

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

Candidates are rejected with `FC_APPROVAL_REQUIRED`. Validator blockers or
errors are surfaced as `FC_VALIDATION_BLOCKED`. Blocked bridge plans are
surfaced as `FC_BRIDGE_BLOCKED`. Missing explicit mesh or element topology is
surfaced as `FC_MESH_REQUIRED`.

## Covered Fixtures

Focused tests cover:

- approved cantilever FEASpec example;
- approved truss FEASpec example;
- FEASpec candidate rejection;
- missing units diagnostics;
- invalid load target diagnostics;
- disconnected graph validator blocking;
- non-CalculiX bridge target rejection;
- no writer, exporter, runner, network, VLM, credential, GUI, or solver imports.

## Non-Goals

- No `.inp` writing.
- No case file creation.
- No CalculiX export.
- No solver adapter handoff.
- No runner handoff.
- No `ccx` execution.
- No live optional validation.
- No ProjectSchema mutation.
- No GUI workflow.
- No VLM API, provider client, credentials, or API keys.
- No Abaqus exporter and no mandatory Abaqus dependency.
- No topology optimization implementation.
- No industrial certification, compliance, production CAE, or accuracy claim.
- No native commercial CAD import.

## Issue #8 Separation

Issue `#8` remains live installed-only CalculiX `ccx` validation. The case-plan
model does not satisfy that issue because it does not run `ccx` and does not
create solver artifacts.

## Next Recommended Gates

- `OSW-EXP-011_FEASPEC_TO_CALCULIX_INP_WRITER_DESIGN`
  records the design-only future writer boundary in
  [FEASpec to CalculiX INP writer design](feaspec_to_calculix_inp_writer_design.md).
- `OSW-EXP-012_FEASPEC_CALCULIX_INP_RENDERER_IMPLEMENTATION_NO_RUN`
