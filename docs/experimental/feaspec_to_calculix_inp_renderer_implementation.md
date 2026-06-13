# FEASpec CalculiX INP renderer implementation

Status: experimental renderer implemented. The renderer is no-run: it performs
no solver execution, no `ccx` invocation, no SolverAdapter or runner call, and
no ProjectSchema mutation.

Related release: `v0.1.4-rc1`

## Release Context

`v0.1.4-rc1` is a public prerelease. This implementation is post-release
development on `develop`; it does not edit the public release, mutate tags,
upload assets, close issues, install solvers, or run live optional validation.

## Package Path

The implementation lives under the experimental FEASpec package:

- `src/osw/experimental/feaspec/calculix_inp_renderer.py`
- `src/osw/experimental/feaspec/calculix_inp_diagnostics.py`

The public package exports the renderer API from
`osw.experimental.feaspec`.

## Public API

The renderer exposes:

- `render_calculix_inp(case_plan) -> CalculiXInpRenderResult`
- `write_calculix_inp(case_plan, path, *, overwrite=False) -> CalculiXInpWriteResult`
- `explain_inp_render_result(result) -> list[str]`

The result objects are diagnostic-first:

- `CalculiXInpRenderResult`
- `CalculiXInpWriteResult`
- `CalculiXInpSection`
- `FEASpecCalculiXInpDiagnostic`

Every render and write result keeps `ready_for_solver_execution` false.

Follow-up exporter evidence:
[FEASpec CalculiX no-run exporter](feaspec_calculix_exporter_no_run.md)
wraps this renderer into a caller-directory export bundle with `.inp`,
manifest JSON, diagnostics JSON, and `README_RUN_FIRST.txt`. The exporter keeps
the same no-run boundary: no `ccx`, no SolverAdapter, no runner, no subprocess,
and no issue `#8` validation.

## Preconditions

Rendering requires:

- `FEASpecCalculiXCasePlan.ready_for_inp_writer == true`;
- no blocking case-plan diagnostics;
- explicit units;
- explicit node topology;
- explicit element topology;
- explicit material data;
- explicit section/property assignment;
- reviewed boundary-condition targets;
- reviewed load targets;
- supported static step metadata;
- supported output request metadata.

The renderer does not invent mesh, element type, material, section, boundary
condition, load, step, or output data. Missing or unsupported records return
`FW_*` diagnostics and no rendered text.

## Section Ordering

Rendered text is deterministic and uses stable line endings. Sections are
emitted in this order:

1. header/provenance comments
2. `*NODE`
3. `*ELEMENT`
4. material cards
5. section/property cards
6. boundary cards
7. load cards
8. `*STEP`
9. output request cards
10. `*END STEP`

Header comments include the OpenSolver Workbench experimental FEASpec notice,
case-plan ID, source FEASpec ID when available, human-review/provenance notes,
an explicit no-certification warning, and a no solver execution note.

## Write Behavior

`write_calculix_inp` writes only rendered text to the caller-provided path. It
refuses to overwrite an existing path unless `overwrite=True` is supplied. It
does not create parent directories implicitly; callers must create the target
directory before writing.

Focused write tests use only pytest `tmp_path`. The follow-up
[FEASpec CalculiX INP golden fixtures](feaspec_to_calculix_inp_golden_fixtures.md)
gate adds controlled no-run golden text fixtures under
`tests/fixtures/feaspec/calculix_golden/`. Those fixtures are not solver
outputs, were not produced by running CalculiX, and do not validate issue `#8`.

## Diagnostics

The renderer uses the `FW_*` diagnostic catalog:

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

Blocking diagnostics prevent rendered text and file writes. Warning diagnostics
remain visible to reviewers.

## Safety Boundary

The renderer does not:

- execute solvers;
- invoke `ccx`;
- import or call `subprocess`;
- call SolverAdapter code;
- call runner code;
- mutate ProjectSchema;
- import GUI modules;
- import VLM providers;
- use API keys or credentials;
- create release assets.

The renderer is a text generation boundary only. Solver execution remains a
separate installed-only run gate.

## Examples

Existing approved FEASpec examples currently block with mesh-required behavior
because they preserve reviewed graph and target evidence but do not include
explicit mesh or element topology.

Focused tests include synthetic in-memory writer-ready case plans with explicit
nodes, elements, material, section, boundary condition, load, static step, and
output requests. The golden fixture tests compare normalized renderer text for
the cantilever and truss cases against the controlled no-run fixture files.

Candidates and invalid examples remain blocked by validation, bridge, or
case-plan diagnostics before renderer handoff.

## Relationship To Issue #8

Issue #8 remains live CalculiX `ccx` validation. This renderer does not validate
installed `ccx`, does not run live optional validation, and does not close issue
#8. Future live validation must run only on a prepared machine where `ccx` is
already installed and under a separate validation or closure gate.

## Non-Goals

- No solver run.
- No golden fixture generation in this gate.
- No CalculiX exporter or SolverAdapter integration.
- No runner integration.
- No Abaqus export.
- No topology optimization.
- No industrial certification, compliance, production CAE, or accuracy claim.
- No stable production claim.
- No bundled external solvers.

## Next Implementation Slices

- `OSW-EXP-014_FEASPEC_CALCULIX_EXPORTER_NO_RUN`
- `OSW-EXP-015_FEASPEC_CALCULIX_EXPORTER_CLI_PREVIEW`
- `OSW-EXP-016_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`
