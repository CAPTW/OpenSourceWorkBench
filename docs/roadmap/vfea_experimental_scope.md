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
providers, VFEA, the full physics validator, full ProjectSchema persistence,
ProjectSchema mutation, solver adapters, exporters, or solver execution.

### FEASpec Candidate

`FEASpecCandidate` is the untrusted draft interpretation created by providers.
It can be incomplete and can contain confidence, evidence, and diagnostics.

### FEASpec Validator

`FEASpecValidator` is the planned validation boundary. A post-release
experimental report layer now covers field-level diagnostics for missing units,
missing materials, disconnected geometry, invalid load targets, human-review
state, solver compatibility, and benchmark readiness. It still does not perform
full physics validation, numerical rigid-body mode solving, mesh generation,
full ProjectSchema persistence, ProjectSchema mutation, exporter generation, or
solver execution.

### Human Review UI

The Human Review UI is a future planning surface for inspecting candidate
nodes, connectivity, dimensions, loads, boundary conditions, materials, units,
confidence, assumptions, and diagnostics. Users must approve a reviewed FEASpec
before export or run handoff.

Post-release experimental work now includes a
[FEASpec human review record model](../experimental/feaspec_human_review_record_model.md)
for JSON-serializable reviewer state, accepted warnings, diagnostic decisions,
validator summaries, and no-run/run-request acknowledgements. The
[FEASpec human review CLI approval](../experimental/feaspec_human_review_cli_approval.md)
workflow can create, validate, and summarize those records as a no-run CLI
workflow. It is not a GUI implementation, run gate, result importer,
ProjectSchema mutation, or solver execution path.

The
[FEASpec human review GUI dialog design](../experimental/feaspec_human_review_gui_dialog_design.md)
extends the human-review planning line with a design-only future dialog
contract. It maps the record model and CLI workflow into entry points, panels,
diagnostics, warning acceptance, approval gating, record preview, save
behavior, and CLI/GUI consistency without adding GUI implementation, result
import, run-gate behavior, ProjectSchema mutation, VLM APIs, dependency
installation, or solver execution.

The
[FEASpec human review GUI dialog view-model](../experimental/feaspec_human_review_gui_dialog_viewmodel.md)
adds a pure Python, UI-agnostic state/action layer for that future dialog. It
computes panels, diagnostic rows, warning rows, action availability, record
preview, and save-plan analysis without importing PySide/Qt, adding GUI source,
implementing result import or run-gate behavior, mutating ProjectSchema,
calling SolverAdapter/runner/subprocess paths, adding VLM APIs, or executing
solvers.

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
design-only and does not implement a production validator, full ProjectSchema
persistence, ProjectSchema mutation, solver exporter, VLM provider, or solver
execution.

Validator implementation evidence:
[FEASpec validator implementation](../experimental/feaspec_validator_implementation.md)
adds an experimental semantic validator report layer for existing FEASpec
models, examples, and benchmark seed fixtures. It produces structured
diagnostics and solver handoff blockers, keeps candidates untrusted, and keeps
CalculiX compatibility field-level only. It does not implement VFEA,
full ProjectSchema persistence, ProjectSchema mutation, CalculiX or Abaqus
export, VLM provider integration, credentials, mesh generation, numerical
physics validation, or solver execution.

Bridge design evidence:
[FEASpec to ProjectSchema bridge design](../experimental/feaspec_to_projectschema_bridge_design.md)
defines the bridge boundary from approved FEASpec plus a validator report with
no blockers into a ProjectSchema draft plan. The follow-up
[FEASpec to ProjectSchema bridge implementation](../experimental/feaspec_to_projectschema_bridge_implementation.md)
adds an experimental plan layer with field mappings, explicit-unit handling,
provenance/evidence preservation, bridge diagnostic codes, unmapped-field
reporting, ProjectSchema extension needs, and the solver handoff boundary. It
does not implement full ProjectSchema persistence, mutate ProjectSchema,
generate CalculiX or Abaqus exports, add VLM APIs or credentials, or execute
solvers.

CalculiX planning evidence:
[FEASpec to CalculiX case planning](../experimental/feaspec_to_calculix_case_planning.md)
defines the future CalculiX-first case-plan contract after approved FEASpec,
validator, and bridge evidence. It remains design-only and separate from issue
`#8` live `ccx` validation. It does not implement a case generator, `.inp`
writer, SolverAdapter/exporter, runner call, live validation, or solver
execution.

Case-plan model evidence:
[FEASpec to CalculiX case-plan model](../experimental/feaspec_to_calculix_case_plan_model.md)
adds the experimental serializable planning object for approved bridge plans.
It preserves reviewed records and `FC_*` diagnostics, keeps
`ready_for_solver_execution` false, and still does not write `.inp` files,
export CalculiX cases, mutate ProjectSchema, run `ccx`, call VLM APIs, or close
issue `#8`.

INP renderer evidence:
[FEASpec CalculiX INP renderer implementation](../experimental/feaspec_to_calculix_inp_renderer_implementation.md)
adds a no-run renderer for writer-ready case plans only. It renders
deterministic `.inp` text, writes only to caller-provided paths with overwrite
protection, keeps `ready_for_solver_execution` false, and still does not run
`ccx`, call SolverAdapter or runner code, mutate ProjectSchema, add VLM APIs,
or close issue `#8`.

No-run export and preview evidence:
[FEASpec CalculiX INP golden fixtures](../experimental/feaspec_to_calculix_inp_golden_fixtures.md),
[FEASpec CalculiX no-run exporter](../experimental/feaspec_calculix_exporter_no_run.md),
and
[FEASpec CalculiX exporter CLI preview](../experimental/feaspec_calculix_exporter_cli_preview.md)
extend the CalculiX-first path with controlled renderer fixtures, an explicit
caller-directory no-run bundle API, and a preview-only CLI. The CLI preview
reports validation, bridge, case-plan, render, planned-file, and diagnostic
status without writing files, creating output directories, running `ccx`,
calling SolverAdapter or runner code, mutating ProjectSchema, adding VLM APIs,
or closing issue `#8`.

[FEASpec CalculiX exporter CLI write no-run](../experimental/feaspec_calculix_exporter_cli_write_no_run.md)
adds the explicit local write command for the no-run bundle. It requires a
caller-provided output directory, blocks unready examples, writes only expected
bundle files when exporter diagnostics allow it, and still does not run `ccx`,
call SolverAdapter or runner code, mutate ProjectSchema, add VLM APIs, or close
issue `#8`.

[FEASpec CalculiX result import and run gate design](../experimental/feaspec_calculix_result_import_or_run_gate_design.md)
defines the future post-export flow without implementing it. Export, human
review, installed-only run, result import, and ResultDataset/report summary stay
separate gates; issue `#8` remains the live CalculiX validation track; and the
design does not add solver execution, SolverAdapter/runner/subprocess calls,
ProjectSchema mutation, VLM APIs, release mutation, or issue closure.

[FEASpec CalculiX result status scanner](../experimental/feaspec_calculix_result_status_scanner.md)
adds post-release text-only `.sta` / `.cvg` status-summary evidence for
existing result directories. It does not parse numeric convergence values,
write ResultDataset files, execute CalculiX, validate issue `#8`, or complete
VFEA.

[FEASpec CalculiX `.dat` minimal parser design](../experimental/feaspec_calculix_result_dat_minimal_parser_design.md)
records the future `.dat` preview subset before implementation. It defines
accepted known headers, scalar candidates, small text tables, rejected
free-form or unitless content, `FP_DAT_*` diagnostics, safety limits, and
ResultDataset preview mapping while adding no parser code, numerical
extraction, solver execution, issue `#8` validation, ProjectSchema mutation, or
VFEA completion claim.

[FEASpec CalculiX `.dat` metadata section scanner](../experimental/feaspec_calculix_result_dat_section_scanner.md)
adds the first `.dat` scanner implementation slice. It classifies only section
headings, spans, section kinds, unsupported/unknown sections, snippets, and
counts. It does not extract numeric values, extract tables, infer units, write
ResultDataset files, execute CalculiX, validate issue `#8`, mutate
ProjectSchema, or complete VFEA.

[FEASpec CalculiX `.dat` minimal parser](../experimental/feaspec_calculix_result_dat_parser.md)
adds the next bounded parser slice. It accepts only explicit scalar candidates
and small delimited table candidates with explicit units, preserves raw text
and line provenance, and enriches result-import previews in memory only. It
does not implement free-form `.dat` parsing, `.frd` numerical field parsing, unit inference,
ResultDataset persistence, solver execution, issue `#8` validation,
ProjectSchema mutation, or VFEA completion.

[FEASpec CalculiX `.frd` block metadata scanner](../experimental/feaspec_calculix_result_frd_block_scanner.md)
adds `.frd` block metadata visibility. It records block candidates,
field-reference candidates, mesh-reference candidates, unsupported diagnostics,
and ResultDataset candidate-only mapping while adding no numerical field
parsing, mesh reconstruction, solver execution, issue `#8` validation,
ProjectSchema mutation, or VFEA completion.

[FEASpec CalculiX ResultDataset draft mapping](../experimental/feaspec_calculix_result_dataset_draft_mapping.md)
adds in-memory mapping from result import evidence into a future
ResultDataset-shaped draft. It preserves artifacts, status summaries, bounded
`.dat` scalar/table candidates, deferred `.frd` references, provenance,
diagnostics, and limitations while adding no ResultDataset persistence, file
writes, additional numerical parsing, mesh reconstruction, solver execution,
issue `#8` validation, ProjectSchema mutation, or VFEA completion.

[FEASpec CalculiX ResultDataset write design](../experimental/feaspec_calculix_result_dataset_write_design.md)
defines the future reviewed persistence contract for that draft. It records the
output layout, schema/versioning, path and overwrite policy, atomic-write
strategy, artifact reference policy, validation-before-write rules, CLI/GUI
future entry points, and `FDW_*` diagnostics while adding no persistence
implementation, file writes, `.frd` numerical parsing, mesh reconstruction,
solver execution, issue `#8` validation, ProjectSchema mutation, or VFEA
completion.

[FEASpec CalculiX ResultDataset write plan](../experimental/feaspec_calculix_result_dataset_write_plan.md)
adds an in-memory planning model for the reviewed persistence boundary. It
records explicit output-directory readiness, path safety, planned standard
files, future atomic write paths, artifact references, diagnostics, and
limitations acknowledgement while still adding no ResultDataset persistence,
actual file writes, artifact copying, solver execution, issue `#8` validation,
ProjectSchema mutation, or VFEA completion.

[FEASpec CalculiX ResultDataset schema payload model](../experimental/feaspec_calculix_result_dataset_schema.md)
adds the in-memory schema bundle for the reviewed draft/write-plan boundary. It
records ResultDataset, manifest, diagnostics, provenance, and review README
payloads while still adding no ResultDataset persistence, file writes,
CLI behavior, solver execution, issue `#8` validation, ProjectSchema mutation,
or VFEA completion.

[FEASpec CalculiX ResultDataset writer](../experimental/feaspec_calculix_result_dataset_writer.md)
adds reviewed library-only file persistence for that schema bundle. It writes
only the five standard ResultDataset review files from a valid plan/payload and
contains no CLI/GUI behavior, artifact copying, solver execution, issue `#8`
validation, ProjectSchema mutation, or VFEA completion.

[FEASpec CalculiX result import write CLI](../experimental/feaspec_calculix_result_import_write_cli.md)
implements the reviewed command boundary for invoking that persistence stack.
It defaults to plan-only review and requires explicit write and review
acknowledgements before writing standard ResultDataset review files. It copies
no artifacts, executes no solver, validates no issue `#8`, and does not
complete VFEA.

[FEASpec CalculiX result import write GUI design](../experimental/feaspec_calculix_result_import_write_gui_design.md)
defines the future GUI workflow for that ResultDataset write stack. It is
design-only and records entry points, panels, disabled reasons, file-dialog
policy, acknowledgements, and CLI/GUI consistency while adding no GUI source,
file dialog, CLI behavior change, solver execution, issue `#8` validation,
ProjectSchema mutation, or VFEA completion.

[FEASpec CalculiX result write view-model](../experimental/feaspec_calculix_result_write_viewmodel.md)
adds an experimental UI-agnostic state/action layer for the same write stack.
It computes panels, rows, disabled reasons, acknowledgements, preview records,
and lexical save-path plans without adding PySide/Qt imports, GUI dialog or
file-dialog behavior, writer invocation, ResultDataset persistence, solver
execution, ProjectSchema mutation, issue `#8` validation, or VFEA completion.

[FEASpec CalculiX result write dialog](../experimental/feaspec_calculix_result_write_dialog.md)
adds an experimental PySide6 dialog over that state layer. It shows the
reviewed write evidence, disabled write action reasons, and later
directory-only output selection. The latest GUI writer integration delegates
ResultDataset persistence to the library writer only after enabled gates and
explicit confirmation. It copies no artifacts, executes no solver, mutates no
ProjectSchema, validates no issue `#8`, and does not complete VFEA.

[FEASpec CalculiX result write GUI file dialog planning](../experimental/feaspec_calculix_result_write_gui_file_dialog_planning.md)
adds the design/planning-only output-directory chooser contract for future GUI
work. It defines directory-selection policy, default-directory behavior,
cancel no-op behavior, create-dir and overwrite acknowledgement handling, path
validation, CLI/GUI consistency, and future mocked tests while adding no
QFileDialog implementation, no GUI source changes, no writer invocation, no
ResultDataset persistence, no solver execution, no issue `#8` validation, and
does not complete VFEA.

[FEASpec CalculiX result write GUI file dialog](../experimental/feaspec_calculix_result_write_gui_file_dialog.md)
adds experimental directory-only output selection to the write dialog. It
updates dialog-local selected-directory display and save-plan analysis with
cancel no-op behavior, but still invokes no writer, writes no ResultDataset
files, creates no directories during selection, copies no artifacts, executes
no solver, validates no issue `#8`, and does not complete VFEA.

[FEASpec CalculiX result write GUI writer integration design](../experimental/feaspec_calculix_result_write_gui_writer_integration_design.md)
adds the design-only future writer-integration contract for the write dialog.
It defines write enablement, final confirmation, acknowledgement gating, a
single library-writer call boundary, failure recovery, post-write display,
retry behavior, state refresh, and mocked tests while adding no GUI writer
invocation, no GUI file writes, no GUI or view-model source mutation, no solver
execution, no issue `#8` validation, and no VFEA completion.

[FEASpec CalculiX result write GUI writer integration](../experimental/feaspec_calculix_result_write_gui_writer_integration.md)
adds the guarded GUI writer call for reviewed ResultDataset persistence. The
dialog requires the reviewed write plan, schema payload, selected output
directory, acknowledgements, and explicit confirmation before delegating to the
existing library writer. It writes only standard ResultDataset review files,
copies no original solver artifacts, executes no solver, changes no CLI/library
writer behavior, validates no issue `#8`, and does not complete VFEA.

[FEASpec CalculiX result write GUI post-write polish](../experimental/feaspec_calculix_result_write_gui_post_write_polish.md)
improves the post-write display for the guarded write dialog. It shows clearer
status, written-file table rows, SHA-256 hashes, grouped diagnostics, grouped
limitations, failure details, retry guidance, and copy-ready display text while
adding no OS clipboard integration, no open-output shell command, no artifact
copying, no solver execution, no issue `#8` validation, and no VFEA completion.

[FEASpec CalculiX result write GUI closure review](../experimental/feaspec_calculix_result_write_gui_closure_review.md)
closes the experimental ResultDataset write GUI slice as complete for
review-file persistence. The closure adds no runtime behavior, no source
writer changes, no solver execution, no live `ccx` validation, no issue `#8`
closure, and no VFEA completion.

[Post-experimental ResultDataset scope review](post_exp_resultdataset_scope_review.md)
summarizes the full FEASpec/CalculiX ResultDataset line after that closure and
the OSW-VALID-004 live CalculiX rerun. It records the live `ccx` result as
`skipped-missing`, keeps issues `#6` through `#11` open for prepared-machine
validation, and requires a future release-boundary decision before any new
release assets.

[Post-experimental release-boundary decision](../release/post_exp_release_boundary_decision.md)
selects `v0.1.5-rc1` as the next boundary for this substantial post-release
experimental line. Metadata alignment, tag creation, release edits, asset
build/upload, and issue closure remain deferred to separate gates.

[OpenSolver Workbench v0.1.5-rc1 candidate](../release/v0_1_5_rc1_candidate.md)
records the follow-up package metadata alignment to `0.1.5rc1`. The alignment
is metadata-only: it creates no `v0.1.5-rc1` tag, release, or assets, and it
does not change the skipped-missing live optional validation state.

Human review GUI evidence:
[FEASpec human review GUI dialog implementation](../experimental/feaspec_human_review_gui_dialog_implementation.md)
records the initial OSW-EXP-023 read-only PySide6 dialog that rendered existing
human-review view-model state, diagnostics, warning rows, disabled action
reasons, safety copy, and record preview. That gate did not add record save
integration, file dialogs, result import, installed-only run gates,
SolverAdapter/runner/subprocess paths, ProjectSchema mutation, VLM APIs,
release mutation, issue mutation, issue `#8` live validation, or solver
execution.

[FEASpec human review GUI save integration](../experimental/feaspec_human_review_gui_save_integration.md)
adds explicit caller-path JSON review-record persistence to that GUI. It writes
one validated review record only when the caller provides a safe `.json` path,
refuses unacknowledged overwrites, and never creates parent directories
implicitly. It still adds no file dialog, export bundle write, `.inp` write,
result import, installed-only run gate, SolverAdapter/runner/subprocess path,
ProjectSchema mutation, VLM API, issue `#8` live validation, issue mutation, or
solver execution.

[FEASpec human review GUI file dialog design](../experimental/feaspec_human_review_gui_file_dialog_design.md)
defines the future path chooser for selecting a review-record JSON save path.
It is design-only and keeps the existing save integration as the only write
path. It adds no `QFileDialog` usage, GUI source mutation, export bundle write,
result import, run gate implementation, SolverAdapter/runner/subprocess path,
ProjectSchema mutation, VLM API, issue `#8` validation, issue mutation, or
solver execution.

[FEASpec human review GUI file dialog implementation](../experimental/feaspec_human_review_gui_file_dialog_implementation.md)
implements that chooser as review-record JSON path selection only. Choosing a
path updates the existing save plan and writes nothing until the existing save
integration runs. It adds no export bundle write, `.inp` write, result import,
run gate, SolverAdapter/runner/subprocess path, ProjectSchema mutation, VLM
API, issue `#8` validation, issue mutation, or solver execution.

Optional solver manifest UX relationship:
[Optional solver manifest UX design](../experimental/optional_solver_manifest_ux_design.md)
is adjacent infrastructure for future optional stack health guidance. VFEA and
FEASpec workflows may later benefit from clearer CalculiX, Gmsh, PyVista, or
meshio availability diagnostics, but this roadmap does not treat manifest UX as
solver installation, solver execution, validation success, issue closure
evidence, a bundled-solver promise, or certification.

[Optional solver manifest schema model](../experimental/optional_solver_manifest_schema_model.md)
adds only typed declarative manifest records and structural diagnostics for
that optional-stack guidance. It does not add solver discovery, CLI or GUI
surfaces, health-check execution, VFEA provider behavior, ProjectSchema
mutation, issue closure evidence, bundled-solver support, or certification.

[Optional solver discovery service design](../experimental/optional_solver_discovery_service_design.md)
adds only the design contract for future manifest-consuming discovery. It may
later help VFEA and FEASpec workflows explain missing CalculiX, Gmsh, PyVista,
or meshio components, but it does not implement discovery source, execute
commands, import optional solver packages, run health checks, mutate issues, or
provide validation success evidence.

[Optional solver discovery service implementation](../experimental/optional_solver_discovery_service_implementation.md)
adds passive manifest-consuming discovery for optional stack presence evidence.
It can help future VFEA and FEASpec UX explain missing or partial CalculiX,
Gmsh, PyVista, or meshio availability, but it still does not add CLI/GUI
behavior, active smoke validation, external command execution, solver
execution, dependency installation, issue mutation, or validation success
evidence.

[Optional solver CLI doctor preview](../experimental/optional_solver_cli_doctor_preview.md)
adds passive text/JSON `optional-solver-list`, `optional-solver-doctor`, and
`optional-solver-explain` surfaces for that evidence. It can help users
understand missing CalculiX, Gmsh, PyVista, or meshio prerequisites before
prepared validation, but it does not add GUI behavior, active smoke validation,
external solver command execution, solver execution, dependency installation,
issue mutation, validation success evidence, or bundled-solver claims.

[Optional solver GUI health panel design](../experimental/optional_solver_gui_health_panel_design.md)
defines the future GUI health surface for the same optional-stack evidence. It
may later help VFEA and FEASpec workflows present CalculiX, Gmsh, PyVista, or
meshio setup state, diagnostics, guidance, and validation history in a redacted
panel, but this design adds no GUI source, view-model source, CLI behavior
change, active smoke validation, external solver command execution, solver
execution, dependency installation, issue mutation, validation success
evidence, issue closure evidence, or bundled-solver claims.

[Optional solver GUI health panel view-model](../experimental/optional_solver_gui_health_panel_viewmodel.md)
adds only the pure data layer for that future optional-stack panel. It can help
future VFEA and FEASpec widgets render setup state consistently, but it does
not add PySide/Qt imports, GUI widgets, CLI behavior changes, discovery
execution, active smoke validation, external solver command execution, solver
execution, dependency installation, issue mutation, validation success
evidence, issue closure evidence, or bundled-solver claims.

[Optional solver GUI health panel implementation](../experimental/optional_solver_gui_health_panel_implementation.md)
adds only the PySide display surface over that supplied view-model. It can help
future workflows show optional-stack setup state, but it does not add
GUI-initiated discovery, active smoke validation, external solver command
execution, solver execution, dependency installation, issue mutation,
validation success evidence, issue closure evidence, or bundled-solver claims.

[Optional solver GUI export summary design](../experimental/optional_solver_gui_export_summary_design.md)
defines only the future redacted summary export workflow for that health
surface. It can later help VFEA and FEASpec support/debugging share setup
state without full paths or environment values by default, but it does not add
export source, file dialogs, clipboard integration, shell/browser actions,
discovery execution, solver execution, dependency installation, issue
mutation, validation success evidence, issue closure evidence, or
bundled-solver claims.

Alternative if maintainers decide this scope definition is complete:
`OSW-EXP-001A_VFEA_ISSUE_CLOSURE`.
