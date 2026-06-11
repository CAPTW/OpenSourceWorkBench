# FEASpec to ProjectSchema bridge design

Status: design-only bridge contract. The bridge not implemented in this gate;
no source bridge implementation, ProjectSchema mutation, solver adapter,
exporter, VLM API, credentials, topology optimization, or solver execution is
added.

Related release: `v0.1.4-rc1`

Related evidence:

- [FEASpec IR design](feaspec_ir_design.md)
- [FEASpec Python models](feaspec_python_models.md)
- [FEASpec validator implementation](feaspec_validator_implementation.md)
- [VFEA experimental scope definition](../roadmap/vfea_experimental_scope.md)

## Release Context

`v0.1.4-rc1` is a public prerelease. This document is post-release
development on `develop` and does not change the public release, release tag,
release assets, or version metadata.

The current codebase has experimental FEASpec Python models and a field-level
semantic validator report layer. It does not have a FEASpec to ProjectSchema
converter. This document records the future bridge contract before any source
implementation is attempted.

## Goals

The future bridge should translate an approved FEASpec into a normal OSW
ProjectSchema draft while preserving evidence and limitations. It should:

- require an approved FEASpec and a validator report with no blockers;
- keep explicit units at every project boundary;
- map reviewed FEASpec entities into ProjectSchema concepts when a safe field
  exists;
- report unmapped fields instead of dropping or inventing data;
- preserve source, provenance, evidence, confidence, diagnostics, and human
  review decisions;
- keep ProjectSchema validation as a separate downstream check;
- stop before SolverAdapter/export handoff, mesh generation, or solver
  execution.

## Bridge Preconditions

The bridge preconditions are deliberately strict:

- Input must be an approved FEASpec, not a `FEASpecCandidate`.
- The FEASpec must contain a `human_review` record with reviewer, timestamp,
  approval decision, and accepted warnings when applicable.
- The latest validator report must exist, target the same FEASpec revision,
  and have no blockers.
- The validator report must show validation state `approved`.
- Units must be explicit for dimensions, material properties, loads, boundary
  values, and any other dimensional quantity.
- Geometry graph IDs, material IDs, section IDs, boundary-condition targets,
  and load targets must be stable and unique.
- Solver compatibility may be recorded as planning metadata only. It must not
  trigger export or solver execution.

Failure to satisfy a precondition should produce a bridge diagnostic and no
ProjectSchema output.

## Bridge Output

The future API should return a structured result instead of mutating a project
in place:

```text
BridgeResult
  project: Project | None
  diagnostics: list[BridgeDiagnostic]
  unmapped_fields: list[UnmappedFEASpecField]
  provenance_map: list[ProvenanceMapping]
  extension_needs: list[ProjectSchemaExtensionNeed]
```

The bridge result should be previewable and serializable for reports. A caller
can decide whether to save the generated project draft after review. The bridge
must not write solver files or launch external commands.

## Field Mapping Table

| FEASpec field | ProjectSchema target | Strategy | Notes |
| --- | --- | --- | --- |
| `source` | `Project.metadata`, `GeometryRef.metadata`, future provenance extension | Preserve source kind, file identifiers, provider/manual annotation IDs, and text spans in metadata. | ProjectSchema has no dedicated provenance table today. |
| `problem_type` | `PhysicsSetup.analysis_type`, `PhysicsSetup.metadata` if added later | Map supported educational cases such as linear-static planning text. | Unsupported problem types emit `FB_SOLVER_TARGET_UNSUPPORTED`. |
| `units` | `Project.units`, `BoundaryCondition.unit`, `Material.properties` units | Use explicit units only and centralize future conversions through UnitSystem-facing code. | Unknown or unsupported units emit `FB_UNITS_UNSUPPORTED`. |
| `geometry.geometry_graph.nodes` | future geometry/mesh extension or `GeometryRef.metadata` | Preserve node IDs, coordinates, frames, evidence, and confidence as metadata until ProjectSchema has graph entities. | No meshing in bridge. |
| `geometry.geometry_graph.edges` | future geometry/mesh extension or `GeometryRef.metadata` | Preserve connectivity and curve type as reviewed metadata. | Unsupported curves emit `FB_UNSUPPORTED_GEOMETRY`. |
| `geometry.geometry_graph.regions` | future geometry/mesh extension or `MeshRef.metadata` | Preserve region IDs and boundary edge references. | Missing target mapping emits `FB_UNMAPPED_REGION`. |
| `materials` | `Project.materials` | Map reviewed isotropic elastic materials into existing material records when the property set is supported. | Missing or unsupported material data emits `FB_MISSING_MATERIAL`. |
| `sections` | `PhysicsSetup.material_assignments`, future section extension | Map simple target-to-material or target-to-section assignments where possible. | Unsupported sections emit `FB_UNSUPPORTED_SECTION`. |
| `boundary_conditions` | `PhysicsSetup.boundary_conditions` / `BoundaryCondition` | Map reviewed fixed/displacement-style constraints with valid targets and units. | Invalid targets emit `FB_INVALID_BC_TARGET`. |
| `loads` | `BoundaryCondition` or future load extension | Map supported nodal force-style educational loads with explicit units and valid targets. | Unsupported load kinds emit `FB_UNSUPPORTED_LOAD_TYPE`; invalid targets emit `FB_INVALID_LOAD_TARGET`. |
| `dimensions` | `GeometryRef.metadata`, `Project.metadata`, future geometry extension | Preserve dimensional constraints and evidence. | The bridge must not silently resize geometry. |
| `assumptions` | `Project.warnings`, `Project.metadata`, report metadata | Preserve reviewed assumptions as limitations and warnings. | Assumptions must remain visible in reports. |
| `evidence` | metadata/provenance map and future provenance extension | Preserve evidence references, image regions, text spans, and annotations. | Missing evidence emits `FB_PROVENANCE_INCOMPLETE`. |
| `confidence` | metadata/provenance map and diagnostics | Preserve confidence per mapped entity. | Low confidence should remain report-visible. |
| `diagnostics` | bridge diagnostics and `Project.warnings` | Carry accepted warnings and bridge-specific diagnostics forward. | New bridge diagnostic codes use `FB_*`. |
| `validation` | metadata/provenance map and report notes | Preserve validator state, report hash, and approval timestamp. | Validation evidence is not industrial certification. |
| `solver_compatibility` | `SolverConfig.execution_mode="prepare_only"` metadata only | Record intended CalculiX-first compatibility planning without export. | SolverAdapter/export is future work. |

## Geometry Strategy

The bridge should treat the FEASpec geometry graph as reviewed problem setup,
not as a mesh generator. The initial design should support:

- stable graph IDs for nodes, edges, and regions;
- reviewed coordinates and coordinate frames when explicit units are present;
- evidence and confidence for each mapped entity;
- named target sets for loads, boundary conditions, sections, and materials;
- diagnostics for unsupported geometry features and unmapped regions.

There is no meshing in bridge. Mesh generation, element selection, geometry
repair, CAD import, and solver case preparation remain later gates. Until
ProjectSchema has graph-native fields, the bridge should preserve graph
entities in metadata and report `ProjectSchema` extension needs rather than
pretending the conversion is complete.

## Material And Section Strategy

The first bridge design should support small educational linear-static cases:

- isotropic elastic material data with explicit units;
- reviewed material IDs and material names;
- simple target assignments from regions, edges, or named sets;
- section metadata for thickness, area, or cross-section only when explicit and
  supported;
- bridge diagnostics for missing material properties or unsupported sections.

Unsupported nonlinear material, contact, or commercial solver-specific section
features must remain unmapped and report-visible. They must not be converted
into approximate values without review.

## Boundary And Load Strategy

Boundary conditions and loads are bridge-critical because they affect solver
meaning. The bridge should:

- validate every target against reviewed geometry graph IDs or named sets;
- preserve direction, coordinate frame, component values, and units;
- map supported constraints and force-like loads into ProjectSchema boundary
  records or future load records;
- keep pressure, distributed loads, moments, and unsupported load kinds as
  unmapped or future extension needs until a safe ProjectSchema representation
  exists;
- report invalid targets and unsupported types with bridge diagnostics.

The bridge must not create default loads, default constraints, or hidden solver
fixes to make a model run.

## Units Strategy

The bridge should accept only explicit units. It may normalize units through
UnitSystem-facing code in a later implementation, but this design does not add
conversion behavior.

Unknown unit systems, missing dimensional units, ambiguous labels, and mixed
unsupported units should block bridge output with `FB_UNITS_UNSUPPORTED`.
Bare floats from image, text, or provider output must not cross into
ProjectSchema as physical quantities.

## Provenance Strategy

The bridge must preserve provenance rather than summarizing it away:

- FEASpec source provider or manual annotation source;
- image regions, drawing marks, or text spans used as evidence;
- confidence values for inferred entities;
- human reviewer identity or local review marker;
- validator report identity, timestamp, and accepted warnings;
- mapping from each ProjectSchema object back to FEASpec IDs.

If provenance cannot be attached to an output field, the bridge should emit
`FB_PROVENANCE_INCOMPLETE` and record the missing mapping in `unmapped_fields`.

## Bridge Diagnostic Codes

Bridge diagnostic codes use the `FB_*` prefix so they remain distinct from
validator `FS_*` codes.

| Code | Severity | Meaning |
| --- | --- | --- |
| `FB_APPROVAL_REQUIRED` | blocker | Input is a candidate, missing human review, or not approved. |
| `FB_VALIDATION_BLOCKED` | blocker | Validator report is missing, stale, not approved, or has blockers. |
| `FB_UNSUPPORTED_GEOMETRY` | error | Geometry graph entity cannot be represented safely. |
| `FB_UNMAPPED_REGION` | warning/error | Region or named set has no ProjectSchema target. |
| `FB_MISSING_MATERIAL` | blocker | Required material or material property is missing. |
| `FB_UNSUPPORTED_SECTION` | error | Section type or property set is outside the first bridge scope. |
| `FB_INVALID_BC_TARGET` | blocker | Boundary-condition target does not map to reviewed geometry. |
| `FB_INVALID_LOAD_TARGET` | blocker | Load target does not map to reviewed geometry. |
| `FB_UNSUPPORTED_LOAD_TYPE` | error | Load kind has no safe ProjectSchema representation yet. |
| `FB_UNITS_UNSUPPORTED` | blocker | Units are missing, ambiguous, or unsupported by the bridge. |
| `FB_SOLVER_TARGET_UNSUPPORTED` | warning/error | Requested solver path is unsupported by bridge planning. |
| `FB_PROVENANCE_INCOMPLETE` | warning/error | Source, evidence, confidence, or review provenance cannot be preserved. |

The future bridge should return diagnostics even when it returns a draft
project. Warnings do not imply solver readiness.

## Future API Sketch

The first implementation gate should remain small and non-executing:

```text
bridge_feaspec_to_project(
    spec: FEASpec,
    validator_report: FEASpecValidationReport,
    *,
    target_solver: str | None = "calculix",
) -> BridgeResult
```

The function should be pure with respect to the filesystem. It should not write
project files by default, import GUI modules, import solver adapters, launch
subprocesses, call network APIs, or load VLM providers.

## ProjectSchema Extension Needs

ProjectSchema mutation is future work. This design identifies likely extension
needs but does not change `src/osw/core/project_schema.py`.

Likely extension needs:

- a provenance/evidence table that can link ProjectSchema objects to FEASpec
  source IDs;
- graph-native geometry entities or named target sets;
- explicit load records separate from boundary conditions where needed;
- section records for thickness, area, and cross-section assignments;
- human-review metadata and accepted-warning records;
- bridge diagnostics and unmapped-field records.

Until those fields exist, metadata and warnings can preserve information for
preview, but a future implementation must clearly mark partial mappings.

## Solver Handoff Boundary

SolverAdapter/export is future work. The bridge should end at a ProjectSchema
draft and bridge diagnostics. It must not generate CalculiX input decks, Abaqus
input files, meshes, shell scripts, runner jobs, or executable commands.

The planning line remains CalculiX-first. Abaqus is optional/non-default and
must not be required. Any future Abaqus export discussion needs a separate
planning gate and must not introduce a mandatory commercial dependency.

## Test Strategy

Future implementation tests should be network-free, solver-free, and independent
of heavy optional dependencies:

- approved FEASpec fixture maps into a ProjectSchema draft;
- candidate FEASpec is blocked with `FB_APPROVAL_REQUIRED`;
- stale or blocking validator report is blocked with `FB_VALIDATION_BLOCKED`;
- explicit units are preserved and missing units are blocked;
- geometry graph IDs are preserved in metadata or future graph fields;
- invalid boundary-condition and load targets are reported;
- unmapped fields are reported rather than silently dropped;
- provenance and confidence are preserved for mapped entities;
- no solver adapter, exporter, subprocess, VLM provider, or credential module is
  imported.

## Non-Goals

- No source bridge implementation in this gate.
- No ProjectSchema mutation in this gate.
- No ProjectSchema migration.
- No mesh generation.
- No CalculiX exporter or case generation.
- No Abaqus exporter.
- No SolverAdapter implementation or handoff.
- No VLM API, provider client, credentials, API keys, or network call.
- No automatic unreviewed solver execution.
- No solver execution.
- No topology optimization implementation.
- No industrial certification, compliance, production CAE, or accuracy claim.
- No native commercial CAD import.

## Next Slices

Suggested follow-up gates:

- `OSW-EXP-008_FEASPEC_TO_PROJECTSCHEMA_BRIDGE_IMPLEMENTATION`
- `OSW-EXP-009_FEASPEC_HUMAN_REVIEW_UI_DESIGN`
- `OSW-EXP-010_FEASPEC_TO_CALCULIX_CASE_PLANNING`

Any implementation gate must start from the preconditions, diagnostics, and
non-goals above and must keep solver execution out of the bridge.
