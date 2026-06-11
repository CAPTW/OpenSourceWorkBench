"""Experimental FEASpec-to-ProjectSchema bridge plan layer.

The bridge creates an inspectable draft plan only. It does not persist
ProjectSchema files, generate solver decks, call solver adapters, use provider
APIs, or execute solvers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .bridge_diagnostics import (
    BridgeDiagnosticCode,
    BridgeSeverity,
    FEASpecBridgeDiagnostic,
)
from .diagnostics import DiagnosticCode, FEASpecValidationReport
from .io import load_feaspec
from .models import FEASpecDocument, SpecType, parse_feaspec_dict
from .validator import validate_for_solver

SUPPORTED_LOAD_KINDS = frozenset({"point_force", "force"})
SUPPORTED_SOLVER_TARGETS = frozenset({"calculix", "abaqus"})


class BridgeStatus(str, Enum):
    """Bridge planning status."""

    BLOCKED = "blocked"
    DRAFT_READY = "draft-ready"
    DRAFT_READY_WITH_WARNINGS = "draft-ready-with-warnings"


@dataclass(frozen=True)
class FEASpecProjectExtensionNeed:
    """ProjectSchema capability needed for a lossless FEASpec mapping."""

    source_field: str
    reason: str
    suggested_target: str = ""
    required_before_solver_handoff: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "source_field": self.source_field,
            "reason": self.reason,
            "suggested_target": self.suggested_target,
            "required_before_solver_handoff": self.required_before_solver_handoff,
        }


@dataclass(frozen=True)
class FEASpecProjectProvenance:
    """Source and review provenance preserved by the bridge plan."""

    source: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    confidence: dict[str, Any] = field(default_factory=dict)
    human_review: dict[str, Any] = field(default_factory=dict)
    validation_summary: dict[str, Any] = field(default_factory=dict)
    solver_target: str = "calculix"
    mapping: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "source": dict(self.source),
            "evidence": [dict(item) for item in self.evidence],
            "confidence": dict(self.confidence),
            "human_review": dict(self.human_review),
            "validation_summary": dict(self.validation_summary),
            "solver_target": self.solver_target,
            "mapping": dict(self.mapping),
        }


@dataclass(frozen=True)
class FEASpecProjectDraft:
    """ProjectSchema-compatible draft and preserved FEASpec bridge fields."""

    name: str
    problem_type: str
    units: dict[str, Any]
    geometry_graph: dict[str, Any]
    materials: list[dict[str, Any]]
    sections: list[dict[str, Any]]
    boundary_conditions: list[dict[str, Any]]
    loads: list[dict[str, Any]]
    dimensions: list[dict[str, Any]]
    assumptions: list[str]
    solver_target: str = "calculix"
    solver_export_performed: bool = False
    solver_execution_performed: bool = False
    project_schema_compatible_dict: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "problem_type": self.problem_type,
            "units": dict(self.units),
            "geometry_graph": dict(self.geometry_graph),
            "materials": [dict(item) for item in self.materials],
            "sections": [dict(item) for item in self.sections],
            "boundary_conditions": [dict(item) for item in self.boundary_conditions],
            "loads": [dict(item) for item in self.loads],
            "dimensions": [dict(item) for item in self.dimensions],
            "assumptions": list(self.assumptions),
            "solver_target": self.solver_target,
            "solver_export_performed": self.solver_export_performed,
            "solver_execution_performed": self.solver_execution_performed,
            "project_schema_compatible_dict": dict(self.project_schema_compatible_dict),
        }


@dataclass(frozen=True)
class FEASpecProjectBridgePlan:
    """Result returned by :func:`plan_project_from_feaspec`."""

    status: BridgeStatus
    project_draft: FEASpecProjectDraft | None
    provenance: FEASpecProjectProvenance
    diagnostics: tuple[FEASpecBridgeDiagnostic, ...] = ()
    extension_needs: tuple[FEASpecProjectExtensionNeed, ...] = ()
    unmapped_fields: tuple[str, ...] = ()
    solver_target: str = "calculix"
    validator_report: dict[str, Any] = field(default_factory=dict)
    solver_export_performed: bool = False
    solver_execution_performed: bool = False

    @property
    def is_blocked(self) -> bool:
        return self.status is BridgeStatus.BLOCKED

    @property
    def is_draft_ready(self) -> bool:
        return self.status in {
            BridgeStatus.DRAFT_READY,
            BridgeStatus.DRAFT_READY_WITH_WARNINGS,
        }

    @property
    def diagnostic_codes(self) -> set[BridgeDiagnosticCode]:
        return {diagnostic.code for diagnostic in self.diagnostics}

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "project_draft": self.project_draft.to_dict() if self.project_draft else None,
            "provenance": self.provenance.to_dict(),
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
            "extension_needs": [item.to_dict() for item in self.extension_needs],
            "unmapped_fields": list(self.unmapped_fields),
            "solver_target": self.solver_target,
            "validator_report": dict(self.validator_report),
            "solver_export_performed": self.solver_export_performed,
            "solver_execution_performed": self.solver_execution_performed,
        }


def plan_project_from_feaspec(
    spec_or_dict: FEASpecDocument | Mapping[str, Any] | str | Path,
    *,
    target_solver: str = "calculix",
) -> FEASpecProjectBridgePlan:
    """Plan a ProjectSchema-compatible draft from approved FEASpec data.

    The bridge is intentionally non-mutating: it returns a draft plan and
    diagnostics without writing files, preparing solver cases, or running
    external tools.
    """

    solver_target = str(target_solver or "calculix").casefold()
    spec = _parse_spec(spec_or_dict)
    validator_report = validate_for_solver(spec, solver_target)
    diagnostics = _bridge_diagnostics(spec, validator_report, solver_target=solver_target)
    provenance = _build_provenance(spec, validator_report, solver_target=solver_target)

    if any(diagnostic.blocks_bridge for diagnostic in diagnostics):
        return FEASpecProjectBridgePlan(
            status=BridgeStatus.BLOCKED,
            project_draft=None,
            provenance=provenance,
            diagnostics=tuple(diagnostics),
            extension_needs=(),
            unmapped_fields=(),
            solver_target=solver_target,
            validator_report=validator_report.to_dict(),
        )

    extension_needs = tuple(_extension_needs(spec))
    unmapped_fields = tuple(need.source_field for need in extension_needs)
    project_draft = _build_project_draft(spec, solver_target=solver_target)
    status = (
        BridgeStatus.DRAFT_READY_WITH_WARNINGS
        if diagnostics or extension_needs
        else BridgeStatus.DRAFT_READY
    )
    return FEASpecProjectBridgePlan(
        status=status,
        project_draft=project_draft,
        provenance=provenance,
        diagnostics=tuple(diagnostics),
        extension_needs=extension_needs,
        unmapped_fields=unmapped_fields,
        solver_target=solver_target,
        validator_report=validator_report.to_dict(),
    )


def explain_bridge_plan(plan: FEASpecProjectBridgePlan) -> list[str]:
    """Return concise user-readable bridge-plan explanations."""

    lines = [f"Bridge status: {plan.status.value}."]
    if plan.project_draft is not None:
        lines.append(
            f"Draft project '{plan.project_draft.name}' targets "
            f"{plan.project_draft.solver_target} planning only."
        )
    for diagnostic in plan.diagnostics:
        target = f" [{diagnostic.target_ref}]" if diagnostic.target_ref else ""
        lines.append(
            f"{diagnostic.severity.value.upper()} {diagnostic.code.value}{target}: "
            f"{diagnostic.message}"
        )
    for need in plan.extension_needs:
        lines.append(f"Extension needed for {need.source_field}: {need.reason}")
    if not plan.solver_export_performed and not plan.solver_execution_performed:
        lines.append("No solver export or solver execution was performed.")
    return lines


def _parse_spec(spec_or_dict: FEASpecDocument | Mapping[str, Any] | str | Path) -> FEASpecDocument:
    if isinstance(spec_or_dict, FEASpecDocument):
        return spec_or_dict
    if isinstance(spec_or_dict, str | Path):
        return load_feaspec(spec_or_dict, allow_diagnostics=True)
    return parse_feaspec_dict(spec_or_dict, allow_diagnostics=True)


def _bridge_diagnostics(
    spec: FEASpecDocument,
    validator_report: FEASpecValidationReport,
    *,
    solver_target: str,
) -> list[FEASpecBridgeDiagnostic]:
    diagnostics: list[FEASpecBridgeDiagnostic] = []
    if spec.spec_type is not SpecType.APPROVED:
        diagnostics.append(
            FEASpecBridgeDiagnostic.make(
                BridgeDiagnosticCode.FB_APPROVAL_REQUIRED,
                BridgeSeverity.BLOCKER,
                "Only an approved FEASpec may be bridged into a ProjectSchema draft.",
                source_field="spec_type",
                target_ref=spec.spec_type.value,
                suggested_fix="Review and approve the FEASpec before bridge planning.",
            )
        )
    if spec.human_review is None or spec.human_review.action != "approved":
        diagnostics.append(
            FEASpecBridgeDiagnostic.make(
                BridgeDiagnosticCode.FB_APPROVAL_REQUIRED,
                BridgeSeverity.BLOCKER,
                "A human_review approval record is required before bridge planning.",
                source_field="human_review",
                suggested_fix="Record human review and approval notes.",
            )
        )
    if validator_report.has_blockers or validator_report.has_errors:
        diagnostics.append(
            FEASpecBridgeDiagnostic.make(
                BridgeDiagnosticCode.FB_VALIDATION_BLOCKED,
                BridgeSeverity.BLOCKER,
                "Validator report has blockers or errors; bridge planning is blocked.",
                source_field="validator_report",
                suggested_fix="Resolve validator diagnostics before bridge planning.",
            )
        )
    diagnostics.extend(_map_validator_diagnostics(validator_report))
    diagnostics.extend(_unit_diagnostics(spec))
    diagnostics.extend(_target_diagnostics(spec))
    diagnostics.extend(_solver_diagnostics(solver_target))
    diagnostics.extend(_provenance_diagnostics(spec))
    return _dedupe_diagnostics(diagnostics)


def _map_validator_diagnostics(
    validator_report: FEASpecValidationReport,
) -> list[FEASpecBridgeDiagnostic]:
    diagnostics: list[FEASpecBridgeDiagnostic] = []
    for item in validator_report.diagnostics:
        if item.code is DiagnosticCode.FS_LOAD_MISSING_UNITS:
            diagnostics.append(
                FEASpecBridgeDiagnostic.make(
                    BridgeDiagnosticCode.FB_UNITS_UNSUPPORTED,
                    BridgeSeverity.BLOCKER,
                    item.message,
                    target_ref=item.target_ref,
                    source_field="loads",
                    suggested_fix=item.suggested_fix,
                )
            )
        elif item.code is DiagnosticCode.FS_BC_INVALID_TARGET:
            diagnostics.append(
                FEASpecBridgeDiagnostic.make(
                    BridgeDiagnosticCode.FB_INVALID_BC_TARGET,
                    BridgeSeverity.BLOCKER,
                    item.message,
                    target_ref=item.target_ref,
                    source_field="boundary_conditions",
                    suggested_fix=item.suggested_fix,
                )
            )
        elif item.code is DiagnosticCode.FS_LOAD_INVALID_TARGET:
            diagnostics.append(
                FEASpecBridgeDiagnostic.make(
                    BridgeDiagnosticCode.FB_INVALID_LOAD_TARGET,
                    BridgeSeverity.BLOCKER,
                    item.message,
                    target_ref=item.target_ref,
                    source_field="loads",
                    suggested_fix=item.suggested_fix,
                )
            )
        elif item.code is DiagnosticCode.FS_MATERIAL_MISSING:
            diagnostics.append(
                FEASpecBridgeDiagnostic.make(
                    BridgeDiagnosticCode.FB_MISSING_MATERIAL,
                    BridgeSeverity.BLOCKER,
                    item.message,
                    target_ref=item.target_ref,
                    source_field="materials",
                    suggested_fix=item.suggested_fix,
                )
            )
        elif item.code is DiagnosticCode.FS_SECTION_MISSING:
            diagnostics.append(
                FEASpecBridgeDiagnostic.make(
                    BridgeDiagnosticCode.FB_UNSUPPORTED_SECTION,
                    BridgeSeverity.ERROR,
                    item.message,
                    target_ref=item.target_ref,
                    source_field="sections",
                    suggested_fix=item.suggested_fix,
                )
            )
        elif item.code is DiagnosticCode.FS_SOLVER_ABAQUS_NON_DEFAULT:
            diagnostics.append(
                FEASpecBridgeDiagnostic.make(
                    BridgeDiagnosticCode.FB_SOLVER_TARGET_UNSUPPORTED,
                    BridgeSeverity.WARNING,
                    item.message,
                    target_ref=item.target_ref,
                    source_field="solver_compatibility",
                    suggested_fix=item.suggested_fix,
                    blocks_bridge=False,
                    blocks_solver_handoff=True,
                )
            )
        elif item.code is DiagnosticCode.FS_SOLVER_UNSUPPORTED_ELEMENT:
            diagnostics.append(
                FEASpecBridgeDiagnostic.make(
                    BridgeDiagnosticCode.FB_SOLVER_TARGET_UNSUPPORTED,
                    BridgeSeverity.BLOCKER,
                    item.message,
                    target_ref=item.target_ref,
                    source_field="solver_compatibility",
                    suggested_fix=item.suggested_fix,
                )
            )
    return diagnostics


def _unit_diagnostics(spec: FEASpecDocument) -> list[FEASpecBridgeDiagnostic]:
    missing = [
        name
        for name in ("system", "length", "force")
        if not str(getattr(spec.units, name, "")).strip()
    ]
    if not missing:
        return []
    return [
        FEASpecBridgeDiagnostic.make(
            BridgeDiagnosticCode.FB_UNITS_UNSUPPORTED,
            BridgeSeverity.BLOCKER,
            "Bridge planning requires explicit FEASpec units.",
            target_ref=", ".join(f"units.{name}" for name in missing),
            source_field="units",
            suggested_fix="Declare system, length, and force units before bridge planning.",
        )
    ]


def _target_diagnostics(spec: FEASpecDocument) -> list[FEASpecBridgeDiagnostic]:
    diagnostics: list[FEASpecBridgeDiagnostic] = []
    geometry_ids = spec.geometry.geometry_ids
    for bc in spec.boundary_conditions:
        missing_targets = [target for target in bc.target_refs if target not in geometry_ids]
        if missing_targets:
            diagnostics.append(
                FEASpecBridgeDiagnostic.make(
                    BridgeDiagnosticCode.FB_INVALID_BC_TARGET,
                    BridgeSeverity.BLOCKER,
                    "Boundary condition target does not map to reviewed geometry.",
                    target_ref=f"{bc.id}: {', '.join(missing_targets)}",
                    source_field="boundary_conditions",
                    suggested_fix="Correct boundary-condition target references.",
                )
            )
    for load in spec.loads:
        missing_targets = [target for target in load.target_refs if target not in geometry_ids]
        if missing_targets:
            diagnostics.append(
                FEASpecBridgeDiagnostic.make(
                    BridgeDiagnosticCode.FB_INVALID_LOAD_TARGET,
                    BridgeSeverity.BLOCKER,
                    "Load target does not map to reviewed geometry.",
                    target_ref=f"{load.id}: {', '.join(missing_targets)}",
                    source_field="loads",
                    suggested_fix="Correct load target references.",
                )
            )
        if load.kind and load.kind not in SUPPORTED_LOAD_KINDS:
            diagnostics.append(
                FEASpecBridgeDiagnostic.make(
                    BridgeDiagnosticCode.FB_UNSUPPORTED_LOAD_TYPE,
                    BridgeSeverity.ERROR,
                    f"Load kind {load.kind!r} has no direct bridge mapping yet.",
                    target_ref=load.id,
                    source_field="loads",
                    suggested_fix="Keep this load as an extension need until mapped.",
                )
            )
    return diagnostics


def _solver_diagnostics(solver_target: str) -> list[FEASpecBridgeDiagnostic]:
    if solver_target in SUPPORTED_SOLVER_TARGETS:
        return []
    return [
        FEASpecBridgeDiagnostic.make(
            BridgeDiagnosticCode.FB_SOLVER_TARGET_UNSUPPORTED,
            BridgeSeverity.BLOCKER,
            f"Unsupported bridge solver target {solver_target!r}.",
            target_ref=solver_target,
            source_field="solver_compatibility",
            suggested_fix="Use calculix or a separately approved future target.",
        )
    ]


def _provenance_diagnostics(spec: FEASpecDocument) -> list[FEASpecBridgeDiagnostic]:
    if spec.source.source_type and spec.evidence and spec.confidence.to_dict():
        return []
    return [
        FEASpecBridgeDiagnostic.make(
            BridgeDiagnosticCode.FB_PROVENANCE_INCOMPLETE,
            BridgeSeverity.WARNING,
            "Bridge provenance is incomplete.",
            source_field="source/evidence/confidence",
            suggested_fix="Preserve source, evidence, and confidence records.",
            blocks_bridge=False,
            blocks_solver_handoff=True,
        )
    ]


def _dedupe_diagnostics(
    diagnostics: list[FEASpecBridgeDiagnostic],
) -> list[FEASpecBridgeDiagnostic]:
    seen: set[tuple[BridgeDiagnosticCode, str, str]] = set()
    unique: list[FEASpecBridgeDiagnostic] = []
    for diagnostic in diagnostics:
        key = (diagnostic.code, diagnostic.target_ref, diagnostic.source_field)
        if key not in seen:
            seen.add(key)
            unique.append(diagnostic)
    return unique


def _build_provenance(
    spec: FEASpecDocument,
    validator_report: FEASpecValidationReport,
    *,
    solver_target: str,
) -> FEASpecProjectProvenance:
    return FEASpecProjectProvenance(
        source=spec.source.to_dict(),
        evidence=[item.to_dict() for item in spec.evidence],
        confidence=spec.confidence.to_dict(),
        human_review=spec.human_review.to_dict() if spec.human_review else {},
        validation_summary={
            "validation_state": validator_report.validation_state.value,
            "diagnostic_codes": sorted(code.value for code in validator_report.diagnostic_codes),
            "has_blockers": validator_report.has_blockers,
            "has_errors": validator_report.has_errors,
            "can_handoff_to_solver": validator_report.can_handoff_to_solver,
        },
        solver_target=solver_target,
        mapping={
            "source": "project.metadata/bridge.provenance",
            "units": "project.units",
            "geometry": "project.geometry.metadata.bridge_geometry_graph",
            "materials": "project.materials",
            "boundary_conditions": "project.physics[].boundary_conditions",
            "loads": "bridge.loads/project extension need",
            "evidence": "bridge.provenance.evidence",
        },
    )


def _extension_needs(spec: FEASpecDocument) -> list[FEASpecProjectExtensionNeed]:
    needs = [
        FEASpecProjectExtensionNeed(
            "geometry.geometry_graph",
            "ProjectSchema has no graph-native nodes/edges/regions table.",
            "geometry graph or named target sets",
            required_before_solver_handoff=True,
        ),
        FEASpecProjectExtensionNeed(
            "evidence/confidence",
            "ProjectSchema has no dedicated provenance/evidence table.",
            "provenance records",
        ),
    ]
    if spec.sections:
        needs.append(
            FEASpecProjectExtensionNeed(
                "sections",
                "ProjectSchema has no first-class FEASpec section assignment records.",
                "section records",
                required_before_solver_handoff=True,
            )
        )
    if spec.loads:
        needs.append(
            FEASpecProjectExtensionNeed(
                "loads",
                "ProjectSchema currently represents loads through boundary-style records.",
                "load records",
                required_before_solver_handoff=True,
            )
        )
    if spec.dimensions:
        needs.append(
            FEASpecProjectExtensionNeed(
                "dimensions",
                "ProjectSchema has no graph-linked dimension constraint records.",
                "dimension constraint records",
            )
        )
    return needs


def _build_project_draft(
    spec: FEASpecDocument,
    *,
    solver_target: str,
) -> FEASpecProjectDraft:
    source_id = spec.source.source_id or "feaspec"
    name = f"FEASpec bridge draft: {source_id}"
    units = _unit_dict(spec)
    geometry_graph = spec.geometry.to_dict()
    materials = [material.to_dict() for material in spec.materials]
    sections = [section.to_dict() for section in spec.sections]
    bcs = [bc.to_dict() for bc in spec.boundary_conditions]
    loads = [load.to_dict() for load in spec.loads]
    dimensions = [dimension.to_dict() for dimension in spec.dimensions]
    assumptions = [assumption.to_value() for assumption in spec.assumptions]
    project_dict = _project_schema_dict(
        spec,
        name=name,
        units=units,
        solver_target=solver_target,
        geometry_graph=geometry_graph,
    )
    return FEASpecProjectDraft(
        name=name,
        problem_type=spec.problem_type,
        units=units,
        geometry_graph=geometry_graph,
        materials=materials,
        sections=sections,
        boundary_conditions=bcs,
        loads=loads,
        dimensions=dimensions,
        assumptions=assumptions,
        solver_target=solver_target,
        project_schema_compatible_dict=project_dict,
    )


def _project_schema_dict(
    spec: FEASpecDocument,
    *,
    name: str,
    units: dict[str, Any],
    solver_target: str,
    geometry_graph: dict[str, Any],
) -> dict[str, Any]:
    boundary_records = [
        _bc_record(bc, source_field="boundary_conditions")
        for bc in spec.boundary_conditions
    ]
    boundary_records.extend(_load_boundary_record(load) for load in spec.loads)
    material_assignments = {
        target: spec.materials[0].id
        for section in spec.sections
        for target in section.target_refs
        if spec.materials
    }
    physics = {
        "setup_id": "feaspec-bridge-setup",
        "name": "FEASpec bridge planning setup",
        "domain": "CAE",
        "analysis_type": spec.problem_type,
        "materials": [material.id for material in spec.materials],
        "boundary_conditions": boundary_records,
        "material_assignments": material_assignments,
        "solver_config": {
            "solver_id": f"{solver_target}-feaspec-planning",
            "name": f"{solver_target} FEASpec planning",
            "execution_mode": "prepare_only",
            "parameters": {
                "feaspec_bridge": True,
                "solver_export_performed": False,
                "solver_execution_performed": False,
            },
        },
        "files": [],
    }
    return {
        "schema_version": "0.1",
        "metadata": {
            "name": name,
            "description": "Experimental FEASpec bridge draft; no solver export or execution.",
            "tags": ["feaspec", "experimental", "bridge-plan"],
        },
        "units": units,
        "materials": [_project_material(material) for material in spec.materials],
        "geometry": [
            {
                "id": "feaspec-geometry-graph",
                "name": "FEASpec geometry graph",
                "path": f"feaspec://{spec.source.source_id or 'bridge'}/geometry_graph",
                "format": "FEASpecGeometryGraph",
                "role": "bridge_preview",
                "status": "reviewed",
                "metadata": {
                    "bridge_geometry_graph": geometry_graph,
                    "source_id": spec.source.source_id,
                    "no_meshing_in_bridge": True,
                },
            }
        ],
        "meshes": [],
        "scripts": [],
        "physics": [physics],
        "solvers": [physics["solver_config"]],
        "results": [],
        "report": {
            "path": "reports/feaspec_bridge_preview.html",
            "title": "FEASpec bridge preview",
            "include_validation": True,
            "include_warnings": True,
        },
        "plugins": [],
        "warnings": [
            {
                "path": "feaspec_bridge",
                "message": "Experimental bridge draft only; no solver export or execution.",
            }
        ],
    }


def _unit_dict(spec: FEASpecDocument) -> dict[str, Any]:
    return {
        "name": spec.units.system,
        "length": spec.units.length,
        "mass": spec.units.mass or "kg",
        "time": spec.units.time or "s",
        "temperature": spec.units.temperature or "K",
        "amount": "mol",
        "current": "A",
        "force": spec.units.force,
        "stress": spec.units.stress or "Pa",
        "energy": "J",
        "pressure": spec.units.stress or "Pa",
        "power": "W",
    }


def _project_material(material: Any) -> dict[str, Any]:
    elastic: dict[str, Any] | None = None
    young = material.properties.get("youngs_modulus") or material.properties.get("young_modulus")
    poisson = material.properties.get("poissons_ratio") or material.properties.get("poisson_ratio")
    if isinstance(young, Mapping):
        elastic = {
            "type": "isotropic_elastic",
            "young_modulus": {
                "value": young.get("value"),
                "unit": young.get("units", young.get("unit", "")),
            },
            "poisson_ratio": _quantity_value(poisson, default=0.0),
        }
    payload: dict[str, Any] = {
        "material_id": material.id,
        "name": material.name or material.id,
        "library": "feaspec_bridge",
        "metadata": {
            "feaspec_material": material.to_dict(),
            "bridge_source": "materials",
        },
    }
    if elastic is not None:
        payload["elastic"] = elastic
    return payload


def _quantity_value(value: object, *, default: float) -> object:
    if isinstance(value, Mapping):
        return value.get("value", default)
    return value if value is not None else default


def _bc_record(item: Any, *, source_field: str) -> dict[str, Any]:
    return {
        "name": item.id,
        "type": item.kind,
        "value": ", ".join(str(value) for value in getattr(item, "values", [])),
        "unit": ", ".join(f"{key}={value}" for key, value in getattr(item, "units", {}).items()),
        "target": ", ".join(item.target_refs),
        "kind": item.kind,
        "values": {
            "target_refs": list(item.target_refs),
            "degrees_of_freedom": list(getattr(item, "degrees_of_freedom", [])),
            "coordinate_frame": getattr(item, "coordinate_frame", ""),
        },
        "metadata": {
            "bridge_source": source_field,
            "feaspec_id": item.id,
            "evidence_refs": list(getattr(item, "evidence_refs", [])),
            "confidence": getattr(item, "confidence", None),
        },
    }


def _load_boundary_record(load: Any) -> dict[str, Any]:
    magnitude = load.magnitude
    return {
        "name": load.id,
        "type": load.kind,
        "value": str(magnitude.get("value", "")),
        "unit": str(magnitude.get("units", magnitude.get("unit", ""))),
        "target": ", ".join(load.target_refs),
        "kind": load.kind,
        "values": {
            "target_refs": list(load.target_refs),
            "direction": load.direction,
            "vector": list(load.vector),
            "coordinate_frame": load.coordinate_frame,
        },
        "metadata": {
            "bridge_source": "loads",
            "feaspec_id": load.id,
            "evidence_refs": list(load.evidence_refs),
            "confidence": load.confidence,
            "mapped_as_boundary_record": True,
            "native_load_record_extension_needed": True,
        },
    }
