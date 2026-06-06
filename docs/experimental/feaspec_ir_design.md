# FEASpec IR design

Status: design-only, experimental, and not implemented

Related release: `v0.1.4-rc1`

Release URL: https://github.com/CAPTW/OpenSourceWorkBench/releases/tag/v0.1.4-rc1

Related scope: [VFEA experimental scope definition](../roadmap/vfea_experimental_scope.md)

## Release Context

`v0.1.4-rc1` is a public prerelease. The VFEA experimental scope issue `#17`
is closed, and the accepted scope requires an inspectable FEASpec candidate,
validator requirements, human review, benchmark requirements, and a
CalculiX-first export path.

FEASpec is not implemented in the current codebase. This document is a
design-only contract for future work. It does not add Python models, provider
integrations, validator code, ProjectSchema migrations, solver adapters, VLM
APIs, credentials, or solver execution.

## Product Guardrails

OpenSolver Workbench is educational/research software. FEASpec planning must
preserve these boundaries:

- no industrial certification, compliance, or production CAE claim;
- no automatic unreviewed solver execution from image or VLM output;
- no mandatory Abaqus or commercial solver dependency;
- no bundled external solvers;
- no VFEA implementation claim;
- no FEASpec implementation claim;
- no native commercial CAD import claim;
- no stable production claim.

Any drawing, image, text, heuristic, or model-assisted interpretation is
untrusted draft evidence until a human reviews and approves it.

## Design Goals

FEASpec should be a small, explicit, inspectable intermediate representation
for candidate engineering problem setup. The IR should:

- represent a candidate geometry, material, boundary-condition, load, and unit
  model before solver case generation;
- preserve uncertainty, assumptions, evidence, and provider provenance;
- support validation before ProjectSchema or SolverAdapter handoff;
- require human review before an approved FEASpec can proceed;
- bridge to ProjectSchema and solver-adapter planning later without making
  solver execution automatic;
- support synthetic benchmark fixtures with ground-truth FEASpec files.

## Core Flow

```text
Drawing/Image/Text/Manual input
  -> FEASpecCandidate
  -> FEASpecValidator
  -> Human Review
  -> Approved FEASpec
  -> ProjectSchema bridge
  -> CalculiX-first export path
  -> ResultDataset/report path
```

The flow is a future design path only. A future implementation must keep
providers and validators behind explicit boundaries and must not bypass human
review.

## FEASpecCandidate vs Approved FEASpec

`FEASpecCandidate` is the untrusted draft object. It may be incomplete,
ambiguous, low-confidence, or internally inconsistent. It is allowed to contain
unknown units, missing materials, unresolved load targets, disconnected
geometry, and provider diagnostics because those issues are exactly what the
validator and reviewer need to see.

An approved FEASpec is a human-reviewed object that has passed validation or
has explicit accepted warnings. Approval means the user inspected the draft and
accepted its assumptions for an educational/research workflow. It does not mean
the model is certified, production-ready, or physically correct.

Only an approved FEASpec may proceed to ProjectSchema bridging or solver case
generation. A candidate must not be used for automatic unreviewed solver
execution.

## Top-Level Schema Fields

The planned top-level fields are:

- `schema_version`
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

The fields are a design contract, not a shipped Python schema.

## Source Model

The `source` block records where candidate information came from. Supported
source kinds should include:

- `image`
- `drawing`
- `text_problem_statement`
- `manual_annotation`
- `generated_benchmark`

The source model should record file identifiers, provider identifiers, manual
annotation IDs, text spans, image regions, and generation metadata where
available. VLM output must not be directly trusted; it must be treated as
provider evidence that can be wrong.

No VLM API, provider credential, API key, or provider configuration is part of
this gate.

## Unit Model

Engineering quantities must carry explicit units. The `units` block should
declare the unit system and defaults for length, force, stress, mass, time,
temperature, and angle when relevant.

No silent unit inference is allowed for approval. Unknown units must block approval
or require a human-entered override. Conversions should later be centralized
through UnitSystem-facing code rather than distributed through provider or solver
logic.

## GeometryGraph Model

The `geometry` block should contain a `geometry_graph` with:

- `nodes`: stable IDs, coordinates, coordinate frame, evidence refs, and
  confidence;
- `edges`: stable IDs, node references, curve type, evidence refs, and
  confidence;
- `regions`: stable IDs, boundary edge references, region type, evidence refs,
  and confidence;
- `coordinate_frames`: named frames and transforms;
- `scale_constraints`: known scale, dimension links, or unresolved scale
  diagnostics;
- `dimension_constraints`: extracted or user-entered dimensions linked to
  geometry entities.

The graph must support connectivity checks and explicit target references for
loads and boundary conditions.

## Materials And Sections

Materials should be referenced explicitly and should remain separate from
geometry extraction. The baseline future scope is isotropic elastic educational
cases.

Material fields should include:

- `id`
- `name`
- `model`
- `properties`
- `units`
- `source_evidence`
- `confidence`

Section fields should include:

- `id`
- `target_refs`
- `section_type`
- `properties`
- `units`
- `source_evidence`
- `confidence`

Missing material or section data should produce diagnostics before approval.

## Boundary Conditions

Boundary conditions should include:

- `id`
- `target_refs`
- `kind`
- `degrees_of_freedom`
- `values`
- `units`
- `coordinate_frame`
- `evidence_refs`
- `confidence`

Targets must point to valid nodes, edges, regions, or named sets. Invalid
targets must block approval or require explicit human correction.

## Loads

Supported load planning types include:

- `point_force`
- `moment`
- `pressure`
- `distributed_load`

Load fields should include:

- `id`
- `target_refs`
- `kind`
- `magnitude`
- `units`
- `direction`
- `vector`
- `coordinate_frame`
- `evidence_refs`
- `confidence`

Loads must have explicit units and valid targets. Direction and sign
conventions must be visible during review.

## Dimensions And Assumptions

Dimensions may be extracted from an image, parsed from a problem statement,
entered manually, or generated as benchmark ground truth.

Dimension fields should include:

- `id`
- `target_refs`
- `value`
- `units`
- `source`
- `evidence_refs`
- `confidence`
- `review_status`

Assumptions must be explicit. Examples include plane-stress approximation,
linear-static behavior, simplified support geometry, uniform thickness, or
ignored fillets. Assumptions should remain visible in reports.

## Evidence And Confidence

Evidence is first-class. Each inferred entity should be able to point to one or
more evidence records:

- `evidence_ref`
- `source_region`
- `text_span`
- `provider_id`
- `provider_version`
- `confidence`
- `human_override`
- `notes`

Confidence scores are review aids, not correctness guarantees. Human overrides
should record what changed, who approved it in the local workflow, and why.

## Diagnostics

Diagnostics should be structured so a reviewer can understand what blocks
approval and what remains a warning. Planned diagnostics include:

- missing units;
- missing material;
- invalid load target;
- invalid boundary-condition target;
- disconnected graph;
- duplicate or ambiguous node;
- unsupported problem type;
- insufficient constraints or rigid body mode warning;
- solver incompatibility;
- low-confidence source evidence;
- unresolved assumptions.

Each diagnostic should identify severity, affected entity IDs, evidence refs,
and a suggested review action.

## Validation States

Allowed validation states are:

- `unchecked`
- `invalid`
- `valid-with-warnings`
- `approved`
- `rejected`

`approved` requires human review. `valid-with-warnings` can support review, but
it is not automatically approved. `rejected` should preserve diagnostics and
review notes so the candidate can be improved or used as benchmark negative
evidence.

## Solver Compatibility

The `solver_compatibility` block should declare compatibility by planned
export path, not as a general claim of solver support.

Initial planning should be CalculiX-first for small, inspectable,
linear-static educational cases. Abaqus may appear only as optional,
non-default export planning later; Abaqus must not be required.

Compatibility checks should cover:

- problem type;
- element family;
- material model;
- section type;
- load and boundary-condition support;
- unit readiness;
- known export limitations;
- whether a solver case can be prepared without running a solver.

## Serialization Example: Minimal Cantilever Beam Candidate

```json
{
  "schema_version": "0.1-draft",
  "kind": "FEASpecCandidate",
  "source": {
    "kind": "text_problem_statement",
    "text_span": "cantilever beam, length 1 m, tip load 100 N",
    "provider_id": "generated_benchmark"
  },
  "problem_type": "linear_static_2d",
  "units": {
    "system": "SI",
    "length": "m",
    "force": "N",
    "stress": "Pa"
  },
  "geometry": {
    "geometry_graph": {
      "nodes": [
        {"id": "n1", "xy": [0.0, 0.0]},
        {"id": "n2", "xy": [1.0, 0.0]}
      ],
      "edges": [
        {"id": "e1", "nodes": ["n1", "n2"], "kind": "line"}
      ],
      "regions": []
    }
  },
  "materials": [
    {"id": "steel", "model": "isotropic_elastic", "status": "missing_properties"}
  ],
  "sections": [
    {"id": "sec1", "target_refs": ["e1"], "section_type": "beam", "status": "missing_properties"}
  ],
  "boundary_conditions": [
    {"id": "bc_fixed", "target_refs": ["n1"], "degrees_of_freedom": ["ux", "uy", "rz"]}
  ],
  "loads": [
    {"id": "load_tip", "kind": "point_force", "target_refs": ["n2"], "vector": [0.0, -100.0], "units": "N"}
  ],
  "dimensions": [
    {"id": "dim_length", "target_refs": ["e1"], "value": 1.0, "units": "m"}
  ],
  "assumptions": ["linear static", "2D beam idealization"],
  "evidence": [{"id": "ev1", "kind": "text_span", "confidence": 0.9}],
  "confidence": {"overall": 0.65},
  "diagnostics": [
    {"severity": "error", "code": "missing_material_properties", "target_refs": ["steel"]},
    {"severity": "error", "code": "missing_section_properties", "target_refs": ["sec1"]}
  ],
  "validation": {"state": "invalid"},
  "solver_compatibility": {"calculix": {"state": "blocked", "reason": "missing properties"}}
}
```

## Serialization Example: Minimal 2D Truss Candidate

```json
{
  "schema_version": "0.1-draft",
  "kind": "FEASpecCandidate",
  "source": {
    "kind": "generated_benchmark",
    "provider_id": "synthetic_truss_seed"
  },
  "problem_type": "linear_static_2d_truss",
  "units": {
    "system": "SI",
    "length": "m",
    "force": "N",
    "stress": "Pa"
  },
  "geometry": {
    "geometry_graph": {
      "nodes": [
        {"id": "n1", "xy": [0.0, 0.0]},
        {"id": "n2", "xy": [1.0, 0.0]},
        {"id": "n3", "xy": [0.5, 0.5]}
      ],
      "edges": [
        {"id": "e1", "nodes": ["n1", "n3"], "kind": "bar"},
        {"id": "e2", "nodes": ["n2", "n3"], "kind": "bar"},
        {"id": "e3", "nodes": ["n1", "n2"], "kind": "bar"}
      ],
      "regions": []
    }
  },
  "materials": [{"id": "mat1", "model": "isotropic_elastic", "youngs_modulus": {"value": 200000000000.0, "units": "Pa"}}],
  "sections": [{"id": "sec1", "target_refs": ["e1", "e2", "e3"], "area": {"value": 0.0001, "units": "m^2"}}],
  "boundary_conditions": [
    {"id": "bc_left", "target_refs": ["n1"], "degrees_of_freedom": ["ux", "uy"]},
    {"id": "bc_right", "target_refs": ["n2"], "degrees_of_freedom": ["uy"]}
  ],
  "loads": [{"id": "load_top", "kind": "point_force", "target_refs": ["n3"], "vector": [0.0, -1000.0], "units": "N"}],
  "dimensions": [],
  "assumptions": ["pin-jointed truss", "small displacement"],
  "evidence": [{"id": "ev_truss", "kind": "generated_ground_truth", "confidence": 1.0}],
  "confidence": {"overall": 1.0},
  "diagnostics": [],
  "validation": {"state": "valid-with-warnings", "warnings": ["benchmark candidate still requires review"]},
  "solver_compatibility": {"calculix": {"state": "compatible-for-preparation"}}
}
```

## Serialization Example: Approved FEASpec

```json
{
  "schema_version": "0.1-draft",
  "kind": "FEASpec",
  "approval": {
    "state": "approved",
    "reviewed_by": "local_user",
    "reviewed_items": ["units", "geometry", "materials", "sections", "boundary_conditions", "loads"],
    "notes": "Educational benchmark reviewed for CalculiX preparation."
  },
  "source": {
    "kind": "generated_benchmark",
    "provider_id": "synthetic_cantilever_seed"
  },
  "problem_type": "linear_static_2d",
  "units": {"system": "SI", "length": "m", "force": "N", "stress": "Pa"},
  "geometry": {"geometry_graph": {"nodes": [], "edges": [], "regions": []}},
  "materials": [],
  "sections": [],
  "boundary_conditions": [],
  "loads": [],
  "dimensions": [],
  "assumptions": ["educational fixture"],
  "evidence": [],
  "confidence": {"overall": 1.0},
  "diagnostics": [],
  "validation": {"state": "approved"},
  "solver_compatibility": {"calculix": {"state": "compatible-for-preparation"}}
}
```

## Future Conversion

Future conversion paths should be separate implementation gates:

- `FEASpec -> ProjectSchema`: map reviewed units, materials, geometry,
  assumptions, and diagnostics into normal OSW project contracts.
- `FEASpec -> CalculiX case generator`: prepare small educational cases after
  approval, without running a solver by default.
- Optional Abaqus script export later: non-default planning only, never a
  mandatory dependency.

Converters must reject candidates that are not approved or that have blocking
validation diagnostics.

## Benchmark Implications

FEASpec benchmark work should use synthetic ground-truth FEASpec fixtures
before model-assisted provider output is trusted. Suggested metrics include:

- schema validity;
- node precision and recall;
- connectivity F1;
- boundary-condition target accuracy;
- load target and vector accuracy;
- unit completeness;
- dimension extraction accuracy;
- material and section completeness;
- validation diagnostic accuracy;
- case preparation success after human-approved correction.

Benchmarks are evidence for educational quality and regression testing. They
are not industrial certification.

## Non-Goals

- No implementation in this gate.
- No FEASpec Python model implementation.
- No production validator implementation.
- No ProjectSchema migration implementation.
- No SolverAdapter implementation.
- No VLM API integration.
- No credentials, API keys, or provider configuration.
- No automatic unreviewed solver execution.
- No solver execution.
- No topology optimization.
- No mandatory Abaqus.
- No industrial certification.
- No commercial native CAD import.
- No release, tag, asset, or version metadata mutation.

## Next Implementation Slices

Potential future gates:

- `OSW-EXP-003_FEASPEC_DOC_TESTS_AND_EXAMPLES`
- `OSW-EXP-004_FEASPEC_PYTHON_MODELS`
- `OSW-EXP-005_FEASPEC_VALIDATOR_DESIGN`
- `OSW-EXP-006_FEASPEC_TO_PROJECTSCHEMA_BRIDGE_DESIGN`

Each implementation gate must preserve the same guardrails and add focused
tests before any source behavior is merged.
