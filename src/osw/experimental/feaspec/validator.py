"""Experimental semantic validator for FEASpec documents.

The validator is deliberately bounded to field-level checks and structured
reports. It does not bridge to ProjectSchema, generate solver input, call
external commands, use network APIs, or execute solvers.
"""

from __future__ import annotations

import json
from collections import Counter, deque
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .diagnostics import (
    DiagnosticCategory,
    DiagnosticCode,
    DiagnosticSeverity,
    FEASpecValidationDiagnostic,
    FEASpecValidationReport,
    ValidationPhaseResult,
    infer_validation_state,
)
from .models import FEASpecDocument, SpecType, ValidationState, parse_feaspec_dict

REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "spec_type",
    "source",
    "problem_type",
    "units",
    "geometry",
    "materials",
    "sections",
    "boundary_conditions",
    "loads",
    "dimensions",
    "assumptions",
    "evidence",
    "confidence",
    "diagnostics",
    "validation",
    "solver_compatibility",
}
BENCHMARK_REQUIRED_FILES = {
    "prompt.txt",
    "source_metadata.json",
    "ground_truth_feaspec.json",
    "expected_metrics.json",
    "README.md",
}
BENCHMARK_REQUIRED_METRICS = {
    "schema_validity_required",
    "required_validation_state",
    "node_count",
    "edge_count",
    "bc_count",
    "load_count",
    "material_count",
    "dimension_count",
    "solver_compatibility_expected",
    "detection_metrics_later",
}
CALCULIX_PROBLEM_TYPES = {
    "linear_static_2d",
    "linear_static_2d_beam",
    "linear_static_2d_truss",
    "linear_static_2d_frame",
    "linear_static_2d_plane_stress",
}
COMPATIBLE_SOLVER_STATES = {
    "planned",
    "planned_after_approval",
    "supported",
    "compatible-for-preparation",
}


def validate_feaspec(
    spec_or_dict: FEASpecDocument | Mapping[str, Any] | str | Path,
    *,
    require_approval: bool = False,
) -> FEASpecValidationReport:
    """Validate FEASpec data and return a structured report.

    The function accepts a model instance, mapping, or JSON path. Invalid
    FEASpec examples are parsed with diagnostics preserved so callers get a
    report instead of an exception.
    """

    data = _payload_from_input(spec_or_dict)
    phases: list[ValidationPhaseResult] = []

    schema_diags = _schema_phase(data)
    phases.append(ValidationPhaseResult("schema/model", tuple(schema_diags)))

    model: FEASpecDocument | None = None
    if isinstance(data, Mapping):
        try:
            model = parse_feaspec_dict(data, allow_diagnostics=True)
        except Exception as exc:  # noqa: BLE001 - report parser failures as diagnostics
            schema_diags.append(
                _diag(
                    DiagnosticCode.FS_SCHEMA_MISSING_FIELD,
                    DiagnosticSeverity.BLOCKER,
                    DiagnosticCategory.SCHEMA,
                    f"FEASpec data could not be parsed: {exc}",
                    target_ref="feaspec",
                    suggested_fix="Repair the FEASpec JSON shape before validation.",
                )
            )

    if model is not None:
        phases.extend(
            [
                ValidationPhaseResult("units", tuple(_units_phase(data, model))),
                ValidationPhaseResult("geometry", tuple(_geometry_phase(model))),
                ValidationPhaseResult(
                    "material/section",
                    tuple(_material_section_phase(model)),
                ),
                ValidationPhaseResult(
                    "boundary_condition",
                    tuple(_boundary_condition_phase(model)),
                ),
                ValidationPhaseResult("load", tuple(_load_phase(model))),
                ValidationPhaseResult(
                    "evidence/confidence",
                    tuple(_evidence_confidence_phase(model)),
                ),
                ValidationPhaseResult(
                    "human_review",
                    tuple(_human_review_phase(model, require_approval=require_approval)),
                ),
            ]
        )

    return _build_report(phases, model=model)


def validate_for_solver(
    spec_or_dict: FEASpecDocument | Mapping[str, Any] | str | Path,
    solver_id: str = "calculix",
) -> FEASpecValidationReport:
    """Validate FEASpec data for a future solver preparation path."""

    data = _payload_from_input(spec_or_dict)
    model = _parse_model(data)
    base_report = validate_feaspec(data, require_approval=True)
    phases = list(base_report.phase_results)
    phases.append(
        ValidationPhaseResult(
            "solver_compatibility",
            tuple(_solver_compatibility_phase(model, solver_id=solver_id)),
        )
    )
    return _build_report(phases, model=model, solver_id=solver_id)


def validate_benchmark_seed(seed_dir_or_paths: str | Path) -> FEASpecValidationReport:
    """Validate one FEASpec benchmark seed folder for metadata readiness."""

    seed_dir = Path(seed_dir_or_paths)
    diagnostics: list[FEASpecValidationDiagnostic] = []
    missing_files = sorted(BENCHMARK_REQUIRED_FILES - {path.name for path in seed_dir.iterdir()})
    for filename in missing_files:
        diagnostics.append(
            _diag(
                DiagnosticCode.FS_BENCHMARK_METADATA_MISSING,
                DiagnosticSeverity.ERROR,
                DiagnosticCategory.BENCHMARK,
                f"Benchmark seed is missing {filename}.",
                target_ref=filename,
                suggested_fix="Add the required benchmark seed metadata file.",
            )
        )

    metadata_path = seed_dir / "source_metadata.json"
    if metadata_path.exists():
        metadata = _load_json(metadata_path)
        if metadata.get("source_type") != "synthetic_drawing_placeholder":
            diagnostics.append(
                _diag(
                    DiagnosticCode.FS_BENCHMARK_METADATA_MISSING,
                    DiagnosticSeverity.WARNING,
                    DiagnosticCategory.BENCHMARK,
                    "Benchmark seed should identify synthetic placeholder source state.",
                    target_ref="source_metadata.source_type",
                    suggested_fix="Set source_type to synthetic_drawing_placeholder.",
                )
            )

    metrics_path = seed_dir / "expected_metrics.json"
    if metrics_path.exists():
        metrics = _load_json(metrics_path)
        for field_name in sorted(BENCHMARK_REQUIRED_METRICS - set(metrics)):
            diagnostics.append(
                _diag(
                    DiagnosticCode.FS_BENCHMARK_METADATA_MISSING,
                    DiagnosticSeverity.ERROR,
                    DiagnosticCategory.BENCHMARK,
                    f"Benchmark expected_metrics is missing {field_name}.",
                    target_ref=f"expected_metrics.{field_name}",
                    suggested_fix="Add the missing expected metric metadata.",
                )
            )

    ground_truth_path = seed_dir / "ground_truth_feaspec.json"
    phases = [ValidationPhaseResult("benchmark_readiness", tuple(diagnostics))]
    model: FEASpecDocument | None = None
    if ground_truth_path.exists():
        model = _parse_model(_payload_from_input(ground_truth_path))
        report = validate_feaspec(model, require_approval=True)
        phases.extend(report.phase_results)

    return _build_report(phases, model=model, benchmark_seed=seed_dir.name)


def explain_diagnostics(report: FEASpecValidationReport) -> list[str]:
    """Return concise reviewer-facing diagnostic explanations."""

    explanations: list[str] = []
    for diagnostic in report.diagnostics:
        target = f" [{diagnostic.target_ref}]" if diagnostic.target_ref else ""
        explanations.append(
            f"{diagnostic.severity.value.upper()} {diagnostic.code.value}{target}: "
            f"{diagnostic.message}"
        )
    return explanations


def _payload_from_input(
    spec_or_dict: FEASpecDocument | Mapping[str, Any] | str | Path,
) -> Mapping[str, Any]:
    if isinstance(spec_or_dict, FEASpecDocument):
        return spec_or_dict.to_dict()
    if isinstance(spec_or_dict, str | Path):
        return _load_json(Path(spec_or_dict))
    return spec_or_dict


def _load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_model(data: Mapping[str, Any]) -> FEASpecDocument:
    return parse_feaspec_dict(data, allow_diagnostics=True)


def _schema_phase(data: object) -> list[FEASpecValidationDiagnostic]:
    diagnostics: list[FEASpecValidationDiagnostic] = []
    if not isinstance(data, Mapping):
        return [
            _diag(
                DiagnosticCode.FS_SCHEMA_MISSING_FIELD,
                DiagnosticSeverity.BLOCKER,
                DiagnosticCategory.SCHEMA,
                "FEASpec document must be a mapping.",
                target_ref="feaspec",
                suggested_fix="Provide a JSON object at the top level.",
            )
        ]

    for field_name in sorted(REQUIRED_TOP_LEVEL_FIELDS - set(data)):
        diagnostics.append(
            _diag(
                DiagnosticCode.FS_SCHEMA_MISSING_FIELD,
                DiagnosticSeverity.ERROR,
                DiagnosticCategory.SCHEMA,
                f"Required FEASpec field {field_name!r} is missing.",
                target_ref=field_name,
                suggested_fix="Add the required top-level FEASpec field.",
            )
        )
    return diagnostics


def _units_phase(
    data: Mapping[str, Any],
    model: FEASpecDocument,
) -> list[FEASpecValidationDiagnostic]:
    diagnostics: list[FEASpecValidationDiagnostic] = []
    units = data.get("units")
    if not isinstance(units, Mapping) or not str(model.units.system).strip():
        diagnostics.append(
            _diag(
                DiagnosticCode.FS_UNITS_MISSING_SYSTEM,
                DiagnosticSeverity.BLOCKER,
                DiagnosticCategory.UNITS,
                "FEASpec units.system is required.",
                target_ref="units.system",
                suggested_fix="Declare the unit system before review.",
            )
        )
    for unit_name in ("length", "force"):
        if not str(getattr(model.units, unit_name, "")).strip():
            diagnostics.append(
                _diag(
                    DiagnosticCode.FS_UNITS_AMBIGUOUS,
                    DiagnosticSeverity.ERROR,
                    DiagnosticCategory.UNITS,
                    f"FEASpec units.{unit_name} is required.",
                    target_ref=f"units.{unit_name}",
                    suggested_fix="Declare explicit default units.",
                )
            )
    return diagnostics


def _geometry_phase(model: FEASpecDocument) -> list[FEASpecValidationDiagnostic]:
    diagnostics: list[FEASpecValidationDiagnostic] = []
    graph = model.geometry
    node_ids = [node.id for node in graph.nodes if node.id]
    edge_ids = [edge.id for edge in graph.edges if edge.id]
    region_ids = [region.id for region in graph.regions if region.id]
    all_ids = node_ids + edge_ids + region_ids
    for duplicate_id, count in Counter(all_ids).items():
        if count > 1:
            diagnostics.append(
                _diag(
                    DiagnosticCode.FS_GEOM_DUPLICATE_ID,
                    DiagnosticSeverity.ERROR,
                    DiagnosticCategory.GEOMETRY,
                    f"Geometry id {duplicate_id!r} is repeated.",
                    target_ref=duplicate_id,
                    suggested_fix="Use stable unique IDs for geometry entities.",
                )
            )

    known_nodes = set(node_ids)
    for edge in graph.edges:
        for node_ref in edge.node_refs:
            if node_ref not in known_nodes:
                diagnostics.append(
                    _diag(
                        DiagnosticCode.FS_GEOM_MISSING_NODE,
                        DiagnosticSeverity.ERROR,
                        DiagnosticCategory.GEOMETRY,
                        f"Edge {edge.id!r} references missing node {node_ref!r}.",
                        target_ref=edge.id,
                        suggested_fix="Correct the edge node_refs before approval.",
                    )
                )

    if _disconnected_nodes(model):
        diagnostics.append(
            _diag(
                DiagnosticCode.FS_GEOM_DISCONNECTED_GRAPH,
                DiagnosticSeverity.ERROR,
                DiagnosticCategory.GEOMETRY,
                "Geometry graph contains disconnected node components.",
                target_ref="geometry.geometry_graph",
                suggested_fix="Connect the graph or split it into reviewed parts.",
            )
        )
    return diagnostics


def _material_section_phase(model: FEASpecDocument) -> list[FEASpecValidationDiagnostic]:
    diagnostics: list[FEASpecValidationDiagnostic] = []
    if not model.materials:
        diagnostics.append(
            _diag(
                DiagnosticCode.FS_MATERIAL_MISSING,
                DiagnosticSeverity.ERROR,
                DiagnosticCategory.MATERIAL,
                "At least one material is required for future solver preparation.",
                target_ref="materials",
                suggested_fix="Add reviewed material data with explicit units.",
            )
        )
    for material in model.materials:
        if not material.properties:
            diagnostics.append(
                _diag(
                    DiagnosticCode.FS_MATERIAL_MISSING,
                    DiagnosticSeverity.ERROR,
                    DiagnosticCategory.MATERIAL,
                    f"Material {material.id!r} is missing properties.",
                    target_ref=material.id,
                    suggested_fix="Add material properties before approval.",
                )
            )

    if not model.sections:
        diagnostics.append(
            _diag(
                DiagnosticCode.FS_SECTION_MISSING,
                DiagnosticSeverity.ERROR,
                DiagnosticCategory.SECTION,
                "At least one section assignment is required.",
                target_ref="sections",
                suggested_fix="Assign sections to reviewed geometry targets.",
            )
        )
    known_targets = model.geometry.geometry_ids
    for section in model.sections:
        if not section.properties:
            diagnostics.append(
                _diag(
                    DiagnosticCode.FS_SECTION_MISSING,
                    DiagnosticSeverity.ERROR,
                    DiagnosticCategory.SECTION,
                    f"Section {section.id!r} is missing properties.",
                    target_ref=section.id,
                    suggested_fix="Add section properties before approval.",
                )
            )
        for target_ref in section.target_refs:
            if target_ref not in known_targets:
                diagnostics.append(
                    _diag(
                        DiagnosticCode.FS_SECTION_MISSING,
                        DiagnosticSeverity.ERROR,
                        DiagnosticCategory.SECTION,
                        f"Section {section.id!r} references unknown target {target_ref!r}.",
                        target_ref=section.id,
                        suggested_fix="Retarget the section to known geometry.",
                    )
                )
    return diagnostics


def _boundary_condition_phase(model: FEASpecDocument) -> list[FEASpecValidationDiagnostic]:
    diagnostics: list[FEASpecValidationDiagnostic] = []
    known_targets = model.geometry.geometry_ids
    constrained_dofs = 0
    for condition in model.boundary_conditions:
        constrained_dofs += len(condition.degrees_of_freedom)
        for target_ref in condition.target_refs:
            if target_ref not in known_targets:
                diagnostics.append(
                    _diag(
                        DiagnosticCode.FS_BC_INVALID_TARGET,
                        DiagnosticSeverity.ERROR,
                        DiagnosticCategory.BOUNDARY_CONDITION,
                        (
                            f"Boundary condition {condition.id!r} references "
                            f"unknown target {target_ref!r}."
                        ),
                        target_ref=condition.id,
                        suggested_fix="Retarget the boundary condition to known geometry.",
                    )
                )
    if not model.boundary_conditions or constrained_dofs == 0:
        diagnostics.append(
            _diag(
                DiagnosticCode.FS_BC_INSUFFICIENT_CONSTRAINTS,
                DiagnosticSeverity.WARNING,
                DiagnosticCategory.BOUNDARY_CONDITION,
                "Boundary conditions may be insufficient for a stable future case.",
                target_ref="boundary_conditions",
                suggested_fix="Review supports before solver handoff.",
                blocks_approval=False,
                blocks_solver_handoff=True,
            )
        )
    return diagnostics


def _load_phase(model: FEASpecDocument) -> list[FEASpecValidationDiagnostic]:
    diagnostics: list[FEASpecValidationDiagnostic] = []
    known_targets = model.geometry.geometry_ids
    for load in model.loads:
        for target_ref in load.target_refs:
            if target_ref not in known_targets:
                diagnostics.append(
                    _diag(
                        DiagnosticCode.FS_LOAD_INVALID_TARGET,
                        DiagnosticSeverity.ERROR,
                        DiagnosticCategory.LOAD,
                        f"Load {load.id!r} references unknown target {target_ref!r}.",
                        target_ref=load.id,
                        suggested_fix="Retarget the load to known geometry.",
                    )
                )
        magnitude_has_units = bool(str(load.magnitude.get("units", "")).strip())
        if load.magnitude and not magnitude_has_units:
            diagnostics.append(
                _diag(
                    DiagnosticCode.FS_LOAD_MISSING_UNITS,
                    DiagnosticSeverity.BLOCKER,
                    DiagnosticCategory.LOAD,
                    f"Load {load.id!r} magnitude is missing units.",
                    target_ref=load.id,
                    suggested_fix="Add explicit load magnitude units.",
                )
            )
    return diagnostics


def _evidence_confidence_phase(model: FEASpecDocument) -> list[FEASpecValidationDiagnostic]:
    diagnostics: list[FEASpecValidationDiagnostic] = []
    if not model.evidence:
        diagnostics.append(
            _diag(
                DiagnosticCode.FS_EVIDENCE_MISSING,
                DiagnosticSeverity.WARNING,
                DiagnosticCategory.EVIDENCE,
                "FEASpec contains no evidence records.",
                target_ref="evidence",
                suggested_fix="Add provenance or manual review evidence.",
                blocks_approval=False,
                blocks_solver_handoff=True,
            )
        )
    overall = model.confidence.values.get("overall")
    if isinstance(overall, int | float) and overall < 0.5:
        diagnostics.append(
            _diag(
                DiagnosticCode.FS_CONFIDENCE_LOW,
                DiagnosticSeverity.WARNING,
                DiagnosticCategory.EVIDENCE,
                "Overall confidence is low and requires explicit review.",
                target_ref="confidence.overall",
                suggested_fix="Review low-confidence entities before approval.",
                blocks_approval=False,
                blocks_solver_handoff=True,
            )
        )
    return diagnostics


def _human_review_phase(
    model: FEASpecDocument,
    *,
    require_approval: bool,
) -> list[FEASpecValidationDiagnostic]:
    diagnostics: list[FEASpecValidationDiagnostic] = []
    if model.spec_type is SpecType.CANDIDATE:
        diagnostics.append(
            _diag(
                DiagnosticCode.FS_REVIEW_MISSING,
                DiagnosticSeverity.WARNING,
                DiagnosticCategory.HUMAN_REVIEW,
                "FEASpecCandidate is untrusted and is not solver-ready.",
                target_ref="spec_type",
                suggested_fix="Complete human review before solver handoff.",
                blocks_approval=False,
                blocks_solver_handoff=True,
            )
        )
    if model.spec_type is SpecType.APPROVED or require_approval:
        if model.human_review is None:
            diagnostics.append(
                _diag(
                    DiagnosticCode.FS_REVIEW_MISSING,
                    DiagnosticSeverity.BLOCKER,
                    DiagnosticCategory.HUMAN_REVIEW,
                    "Approved FEASpec requires a human_review block.",
                    target_ref="human_review",
                    suggested_fix="Record reviewed items and approval notes.",
                )
            )
        elif model.human_review.action != "approved":
            diagnostics.append(
                _diag(
                    DiagnosticCode.FS_REVIEW_NOT_APPROVED,
                    DiagnosticSeverity.BLOCKER,
                    DiagnosticCategory.HUMAN_REVIEW,
                    "Human review action is not approved.",
                    target_ref="human_review.action",
                    suggested_fix="Approve or reject explicitly after review.",
                )
            )
        if model.validation.state is not ValidationState.APPROVED:
            diagnostics.append(
                _diag(
                    DiagnosticCode.FS_REVIEW_NOT_APPROVED,
                    DiagnosticSeverity.BLOCKER,
                    DiagnosticCategory.HUMAN_REVIEW,
                    "Approved solver handoff requires validation.state approved.",
                    target_ref="validation.state",
                    suggested_fix="Set approved state only after review passes.",
                )
            )
    return diagnostics


def _solver_compatibility_phase(
    model: FEASpecDocument,
    *,
    solver_id: str,
) -> list[FEASpecValidationDiagnostic]:
    diagnostics: list[FEASpecValidationDiagnostic] = []
    solver = solver_id.lower()
    if solver == "abaqus":
        diagnostics.append(
            _diag(
                DiagnosticCode.FS_SOLVER_ABAQUS_NON_DEFAULT,
                DiagnosticSeverity.INFO,
                DiagnosticCategory.SOLVER_COMPATIBILITY,
                "Abaqus is optional/non-default planning only.",
                target_ref="solver_compatibility.abaqus",
                suggested_fix="Use CalculiX-first planning unless explicitly reviewed.",
                blocks_approval=False,
                blocks_solver_handoff=True,
            )
        )
        return diagnostics
    if solver != "calculix":
        diagnostics.append(
            _diag(
                DiagnosticCode.FS_SOLVER_UNSUPPORTED_ELEMENT,
                DiagnosticSeverity.ERROR,
                DiagnosticCategory.SOLVER_COMPATIBILITY,
                f"Unknown solver compatibility path {solver_id!r}.",
                target_ref=f"solver_compatibility.{solver_id}",
                suggested_fix="Use calculix or a separately approved future solver path.",
            )
        )
        return diagnostics

    if model.problem_type not in CALCULIX_PROBLEM_TYPES:
        diagnostics.append(
            _diag(
                DiagnosticCode.FS_SOLVER_UNSUPPORTED_ELEMENT,
                DiagnosticSeverity.ERROR,
                DiagnosticCategory.SOLVER_COMPATIBILITY,
                f"Problem type {model.problem_type!r} is not in the CalculiX-first set.",
                target_ref="problem_type",
                suggested_fix="Use a supported educational linear-static problem type.",
            )
        )
    state = model.solver_compatibility.state_for("calculix")
    if state == "blocked":
        diagnostics.append(
            _diag(
                DiagnosticCode.FS_SOLVER_UNSUPPORTED_ELEMENT,
                DiagnosticSeverity.ERROR,
                DiagnosticCategory.SOLVER_COMPATIBILITY,
                "FEASpec declares CalculiX compatibility as blocked.",
                target_ref="solver_compatibility.calculix",
                suggested_fix="Resolve blocking diagnostics before CalculiX planning.",
            )
        )
    elif state and state not in COMPATIBLE_SOLVER_STATES and state != "unknown":
        diagnostics.append(
            _diag(
                DiagnosticCode.FS_SOLVER_UNSUPPORTED_ELEMENT,
                DiagnosticSeverity.WARNING,
                DiagnosticCategory.SOLVER_COMPATIBILITY,
                f"CalculiX compatibility state {state!r} needs review.",
                target_ref="solver_compatibility.calculix",
                suggested_fix="Document compatibility before solver handoff.",
                blocks_approval=False,
                blocks_solver_handoff=True,
            )
        )
    return diagnostics


def _build_report(
    phases: Sequence[ValidationPhaseResult],
    *,
    model: FEASpecDocument | None,
    solver_id: str = "",
    benchmark_seed: str = "",
) -> FEASpecValidationReport:
    diagnostics = tuple(diagnostic for phase in phases for diagnostic in phase.diagnostics)
    approved = bool(model and model.spec_type is SpecType.APPROVED and model.validation.is_approved)
    rejected = bool(model and model.validation.state is ValidationState.REJECTED)
    state = infer_validation_state(diagnostics, approved=approved, rejected=rejected)
    return FEASpecValidationReport(
        validation_state=state,
        diagnostics=diagnostics,
        phase_results=tuple(phases),
        accepted_warnings_required=any(
            diagnostic.severity is DiagnosticSeverity.WARNING for diagnostic in diagnostics
        ),
        solver_id=solver_id,
        benchmark_seed=benchmark_seed,
        metadata={"spec_type": model.spec_type.value if model else ""},
    )


def _disconnected_nodes(model: FEASpecDocument) -> bool:
    graph = model.geometry
    node_ids = [node.id for node in graph.nodes if node.id]
    if len(node_ids) <= 1 or not graph.edges:
        return False
    adjacency: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
    edge_nodes: dict[str, list[str]] = {}
    for edge in graph.edges:
        refs = [ref for ref in edge.node_refs if ref in adjacency]
        edge_nodes[edge.id] = refs
        if len(refs) < 2:
            continue
        first = refs[0]
        for other in refs[1:]:
            adjacency[first].add(other)
            adjacency[other].add(first)
    for region in graph.regions:
        region_edge_refs = [
            *region.boundary_refs,
            *region.boundary_edge_refs,
            *region.void_edge_refs,
        ]
        connected_nodes: list[str] = []
        for edge_ref in region_edge_refs:
            connected_nodes.extend(edge_nodes.get(edge_ref, ()))
        if len(connected_nodes) < 2:
            continue
        first = connected_nodes[0]
        for other in connected_nodes[1:]:
            adjacency[first].add(other)
            adjacency[other].add(first)
    visited = {node_ids[0]}
    queue: deque[str] = deque([node_ids[0]])
    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current] - visited:
            visited.add(neighbor)
            queue.append(neighbor)
    return bool(set(node_ids) - visited)


def _diag(
    code: DiagnosticCode,
    severity: DiagnosticSeverity,
    category: DiagnosticCategory,
    message: str,
    *,
    target_ref: str = "",
    evidence_ref: str = "",
    suggested_fix: str = "",
    blocks_approval: bool | None = None,
    blocks_solver_handoff: bool | None = None,
) -> FEASpecValidationDiagnostic:
    return FEASpecValidationDiagnostic.make(
        code,
        severity,
        category,
        message,
        target_ref=target_ref,
        evidence_ref=evidence_ref,
        suggested_fix=suggested_fix,
        blocks_approval=blocks_approval,
        blocks_solver_handoff=blocks_solver_handoff,
    )
