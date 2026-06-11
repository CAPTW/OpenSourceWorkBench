"""Experimental FEASpec to CalculiX case-plan model.

The planner returns serializable planning records and diagnostics only. It does
not write CalculiX input decks, import solver adapters, mutate ProjectSchema
files, use provider APIs, or execute external tools.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .bridge_diagnostics import BridgeDiagnosticCode, BridgeSeverity
from .calculix_diagnostics import (
    CalculiXPlanDiagnosticCode,
    CalculiXPlanSeverity,
    FEASpecCalculiXPlanDiagnostic,
)
from .models import FEASpecDocument
from .project_bridge import (
    BridgeStatus,
    FEASpecProjectBridgePlan,
    FEASpecProjectExtensionNeed,
    plan_project_from_feaspec,
)

SUPPORTED_ELEMENT_TYPES = frozenset(
    {"T3D2", "B31", "CPS3", "CPS4", "CPE3", "CPE4", "C3D4", "C3D8"}
)
SUPPORTED_LOAD_KINDS = frozenset({"point_force", "force", "pressure", "distributed"})
SUPPORTED_STEP_TYPES = frozenset({"static", "linear_static"})
DEFAULT_OUTPUT_VARIABLES = ("U", "S")


class CalculiXCaseStatus(str, Enum):
    """Status for an experimental FEASpec CalculiX case plan."""

    BLOCKED = "blocked"
    PLAN_READY = "plan-ready"
    PLAN_READY_WITH_WARNINGS = "plan-ready-with-warnings"


@dataclass(frozen=True)
class CalculiXCaseNodePlan:
    """Reviewed node-like planning record preserved for future mesh mapping."""

    node_id: str
    coordinates: tuple[Any, ...] = ()
    coordinate_frame: str = ""
    source_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "node_id": self.node_id,
            "coordinates": list(self.coordinates),
            "coordinate_frame": self.coordinate_frame,
            "source_ref": self.source_ref,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CalculiXCaseElementPlan:
    """Explicit element planning record for future deck writing."""

    element_id: str
    element_type: str
    node_refs: tuple[str, ...] = ()
    source_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "element_id": self.element_id,
            "element_type": self.element_type,
            "node_refs": list(self.node_refs),
            "source_ref": self.source_ref,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CalculiXCaseMaterialPlan:
    """Material planning record with explicit FEASpec provenance."""

    material_id: str
    name: str = ""
    model: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    units: dict[str, Any] = field(default_factory=dict)
    source_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "material_id": self.material_id,
            "name": self.name,
            "model": self.model,
            "properties": dict(self.properties),
            "units": dict(self.units),
            "source_ref": self.source_ref,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CalculiXCaseSectionPlan:
    """Section planning record."""

    section_id: str
    material_ref: str = ""
    target_refs: tuple[str, ...] = ()
    section_type: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    units: dict[str, Any] = field(default_factory=dict)
    source_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "section_id": self.section_id,
            "material_ref": self.material_ref,
            "target_refs": list(self.target_refs),
            "section_type": self.section_type,
            "properties": dict(self.properties),
            "units": dict(self.units),
            "source_ref": self.source_ref,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CalculiXCaseBoundaryConditionPlan:
    """Boundary-condition planning record."""

    bc_id: str
    kind: str = ""
    target_refs: tuple[str, ...] = ()
    degrees_of_freedom: tuple[str, ...] = ()
    values: tuple[Any, ...] = ()
    units: dict[str, Any] = field(default_factory=dict)
    coordinate_frame: str = ""
    source_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "bc_id": self.bc_id,
            "kind": self.kind,
            "target_refs": list(self.target_refs),
            "degrees_of_freedom": list(self.degrees_of_freedom),
            "values": list(self.values),
            "units": dict(self.units),
            "coordinate_frame": self.coordinate_frame,
            "source_ref": self.source_ref,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CalculiXCaseLoadPlan:
    """Load planning record."""

    load_id: str
    kind: str = ""
    target_refs: tuple[str, ...] = ()
    magnitude: dict[str, Any] = field(default_factory=dict)
    direction: str = ""
    vector: tuple[Any, ...] = ()
    units: dict[str, Any] = field(default_factory=dict)
    coordinate_frame: str = ""
    source_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "load_id": self.load_id,
            "kind": self.kind,
            "target_refs": list(self.target_refs),
            "magnitude": dict(self.magnitude),
            "direction": self.direction,
            "vector": list(self.vector),
            "units": dict(self.units),
            "coordinate_frame": self.coordinate_frame,
            "source_ref": self.source_ref,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CalculiXCaseStepPlan:
    """Analysis step planning record."""

    step_id: str = "linear_static"
    analysis_type: str = "static"
    nonlinear: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "step_id": self.step_id,
            "analysis_type": self.analysis_type,
            "nonlinear": self.nonlinear,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CalculiXCaseOutputRequestPlan:
    """Output request planning record."""

    request_id: str
    kind: str = "field"
    target: str = "all"
    variables: tuple[str, ...] = DEFAULT_OUTPUT_VARIABLES
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "kind": self.kind,
            "target": self.target,
            "variables": list(self.variables),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class FEASpecCalculiXCasePlan:
    """Experimental CalculiX case-plan result for approved FEASpec data."""

    status: CalculiXCaseStatus
    case_id: str
    source_feaspec_id: str
    target_solver: str = "calculix"
    unit_context: dict[str, Any] = field(default_factory=dict)
    nodes: tuple[CalculiXCaseNodePlan, ...] = ()
    elements: tuple[CalculiXCaseElementPlan, ...] = ()
    materials: tuple[CalculiXCaseMaterialPlan, ...] = ()
    sections: tuple[CalculiXCaseSectionPlan, ...] = ()
    boundary_conditions: tuple[CalculiXCaseBoundaryConditionPlan, ...] = ()
    loads: tuple[CalculiXCaseLoadPlan, ...] = ()
    steps: tuple[CalculiXCaseStepPlan, ...] = ()
    output_requests: tuple[CalculiXCaseOutputRequestPlan, ...] = ()
    provenance_comments: tuple[str, ...] = ()
    diagnostics: tuple[FEASpecCalculiXPlanDiagnostic, ...] = ()
    unmapped_fields: tuple[str, ...] = ()
    extension_needs: tuple[FEASpecProjectExtensionNeed, ...] = ()
    bridge_status: BridgeStatus | None = None
    validator_report: dict[str, Any] = field(default_factory=dict)
    ready_for_inp_writer: bool = False
    ready_for_solver_execution: bool = False
    inp_writer_performed: bool = False
    solver_execution_performed: bool = False

    @property
    def is_blocked(self) -> bool:
        return self.status is CalculiXCaseStatus.BLOCKED

    @property
    def is_plan_ready(self) -> bool:
        return self.status in {
            CalculiXCaseStatus.PLAN_READY,
            CalculiXCaseStatus.PLAN_READY_WITH_WARNINGS,
        }

    @property
    def diagnostic_codes(self) -> set[CalculiXPlanDiagnosticCode]:
        return {diagnostic.code for diagnostic in self.diagnostics}

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "case_id": self.case_id,
            "source_feaspec_id": self.source_feaspec_id,
            "target_solver": self.target_solver,
            "unit_context": dict(self.unit_context),
            "nodes": [item.to_dict() for item in self.nodes],
            "elements": [item.to_dict() for item in self.elements],
            "materials": [item.to_dict() for item in self.materials],
            "sections": [item.to_dict() for item in self.sections],
            "boundary_conditions": [item.to_dict() for item in self.boundary_conditions],
            "loads": [item.to_dict() for item in self.loads],
            "steps": [item.to_dict() for item in self.steps],
            "output_requests": [item.to_dict() for item in self.output_requests],
            "provenance_comments": list(self.provenance_comments),
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "unmapped_fields": list(self.unmapped_fields),
            "extension_needs": [item.to_dict() for item in self.extension_needs],
            "bridge_status": self.bridge_status.value if self.bridge_status else "",
            "validator_report": dict(self.validator_report),
            "ready_for_inp_writer": self.ready_for_inp_writer,
            "ready_for_solver_execution": self.ready_for_solver_execution,
            "inp_writer_performed": self.inp_writer_performed,
            "solver_execution_performed": self.solver_execution_performed,
        }


def plan_calculix_case_from_feaspec(
    spec_or_dict: FEASpecDocument | Mapping[str, Any] | str | Path,
    *,
    target_solver: str = "calculix",
) -> FEASpecCalculiXCasePlan:
    """Plan a CalculiX case model from approved FEASpec data."""

    bridge_plan = plan_project_from_feaspec(spec_or_dict, target_solver=target_solver)
    return plan_calculix_case_from_bridge(bridge_plan)


def plan_calculix_case_from_bridge(
    bridge_plan: FEASpecProjectBridgePlan,
) -> FEASpecCalculiXCasePlan:
    """Plan a CalculiX case model from a FEASpec ProjectSchema bridge plan."""

    diagnostics = _diagnostics_from_bridge(bridge_plan)
    target_solver = str(bridge_plan.solver_target or "").casefold()
    if target_solver != "calculix":
        diagnostics.append(
            _diag(
                CalculiXPlanDiagnosticCode.FC_BRIDGE_BLOCKED,
                CalculiXPlanSeverity.BLOCKER,
                "CalculiX case planning requires a calculix bridge target.",
                target_ref=target_solver,
                source_field="solver_target",
                suggested_fix="Create a bridge plan with target_solver='calculix'.",
            )
        )

    if bridge_plan.is_blocked:
        diagnostics.append(
            _diag(
                CalculiXPlanDiagnosticCode.FC_BRIDGE_BLOCKED,
                CalculiXPlanSeverity.BLOCKER,
                "Bridge planning is blocked, so no CalculiX case plan is ready.",
                source_field="bridge_plan",
                suggested_fix="Resolve bridge diagnostics before CalculiX case planning.",
            )
        )

    draft = bridge_plan.project_draft
    if draft is None:
        return FEASpecCalculiXCasePlan(
            status=_status_for(diagnostics, has_warnings=False),
            case_id=_case_id(bridge_plan.provenance.source),
            source_feaspec_id=str(bridge_plan.provenance.source.get("source_id", "")),
            target_solver="calculix",
            provenance_comments=tuple(_provenance_comments(bridge_plan)),
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
            unmapped_fields=tuple(bridge_plan.unmapped_fields),
            extension_needs=tuple(bridge_plan.extension_needs),
            bridge_status=bridge_plan.status,
            validator_report=dict(bridge_plan.validator_report),
        )

    graph = draft.geometry_graph
    nodes = tuple(_node_plans(graph))
    elements, element_diagnostics = _element_plans(graph)
    diagnostics.extend(element_diagnostics)
    materials = tuple(_material_plans(draft.materials))
    sections = tuple(_section_plans(draft.sections, material_ref=_first_material_ref(materials)))
    boundary_conditions = tuple(_bc_plans(draft.boundary_conditions))
    loads = tuple(_load_plans(draft.loads))
    diagnostics.extend(_draft_diagnostics(draft, nodes, elements, materials, sections))
    diagnostics.extend(_target_diagnostics(graph, elements, boundary_conditions, loads))
    diagnostics.extend(_load_diagnostics(loads))
    diagnostics.extend(_constraint_diagnostics(boundary_conditions))
    diagnostics.extend(_provenance_diagnostics(bridge_plan))
    diagnostics = _dedupe_diagnostics(diagnostics)
    status = _status_for(
        diagnostics,
        has_warnings=bool(bridge_plan.extension_needs or bridge_plan.unmapped_fields),
    )
    ready_for_inp_writer = (
        status is not CalculiXCaseStatus.BLOCKED
        and bool(elements)
        and not any(item.blocks_case_plan for item in diagnostics)
    )

    return FEASpecCalculiXCasePlan(
        status=status,
        case_id=_case_id(bridge_plan.provenance.source),
        source_feaspec_id=str(bridge_plan.provenance.source.get("source_id", "")),
        target_solver="calculix",
        unit_context=dict(draft.units),
        nodes=nodes,
        elements=tuple(elements),
        materials=materials,
        sections=sections,
        boundary_conditions=boundary_conditions,
        loads=loads,
        steps=_default_steps(),
        output_requests=_default_output_requests(),
        provenance_comments=tuple(_provenance_comments(bridge_plan)),
        diagnostics=tuple(diagnostics),
        unmapped_fields=tuple(bridge_plan.unmapped_fields),
        extension_needs=tuple(bridge_plan.extension_needs),
        bridge_status=bridge_plan.status,
        validator_report=dict(bridge_plan.validator_report),
        ready_for_inp_writer=ready_for_inp_writer,
        ready_for_solver_execution=False,
        inp_writer_performed=False,
        solver_execution_performed=False,
    )


def explain_calculix_case_plan(plan: FEASpecCalculiXCasePlan) -> list[str]:
    """Return concise reviewer-facing case-plan explanations."""

    lines = [
        f"CalculiX case-plan status: {plan.status.value}.",
        f"Case plan '{plan.case_id}' targets CalculiX planning only.",
    ]
    if plan.ready_for_inp_writer:
        lines.append("The plan is ready for a future reviewed `.inp` writer.")
    else:
        lines.append("The plan is not ready for a `.inp` writer.")
    for diagnostic in plan.diagnostics:
        target = f" [{diagnostic.target_ref}]" if diagnostic.target_ref else ""
        lines.append(
            f"{diagnostic.severity.value.upper()} {diagnostic.code.value}{target}: "
            f"{diagnostic.message}"
        )
    lines.append("No `.inp` writer or solver execution was performed.")
    return lines


def _diagnostics_from_bridge(
    bridge_plan: FEASpecProjectBridgePlan,
) -> list[FEASpecCalculiXPlanDiagnostic]:
    diagnostics: list[FEASpecCalculiXPlanDiagnostic] = []
    code_map = {
        BridgeDiagnosticCode.FB_APPROVAL_REQUIRED: CalculiXPlanDiagnosticCode.FC_APPROVAL_REQUIRED,
        BridgeDiagnosticCode.FB_VALIDATION_BLOCKED: (
            CalculiXPlanDiagnosticCode.FC_VALIDATION_BLOCKED
        ),
        BridgeDiagnosticCode.FB_UNSUPPORTED_GEOMETRY: (
            CalculiXPlanDiagnosticCode.FC_UNSUPPORTED_GEOMETRY
        ),
        BridgeDiagnosticCode.FB_MISSING_MATERIAL: CalculiXPlanDiagnosticCode.FC_MATERIAL_MISSING,
        BridgeDiagnosticCode.FB_UNSUPPORTED_SECTION: CalculiXPlanDiagnosticCode.FC_SECTION_MISSING,
        BridgeDiagnosticCode.FB_INVALID_BC_TARGET: CalculiXPlanDiagnosticCode.FC_BC_INVALID_TARGET,
        BridgeDiagnosticCode.FB_INVALID_LOAD_TARGET: (
            CalculiXPlanDiagnosticCode.FC_LOAD_INVALID_TARGET
        ),
        BridgeDiagnosticCode.FB_UNSUPPORTED_LOAD_TYPE: (
            CalculiXPlanDiagnosticCode.FC_LOAD_UNSUPPORTED_TYPE
        ),
        BridgeDiagnosticCode.FB_UNITS_UNSUPPORTED: CalculiXPlanDiagnosticCode.FC_UNITS_UNSUPPORTED,
        BridgeDiagnosticCode.FB_SOLVER_TARGET_UNSUPPORTED: (
            CalculiXPlanDiagnosticCode.FC_BRIDGE_BLOCKED
        ),
        BridgeDiagnosticCode.FB_PROVENANCE_INCOMPLETE: (
            CalculiXPlanDiagnosticCode.FC_PROVENANCE_INCOMPLETE
        ),
    }
    for diagnostic in bridge_plan.diagnostics:
        diagnostics.append(
            FEASpecCalculiXPlanDiagnostic.make(
                code_map.get(diagnostic.code, CalculiXPlanDiagnosticCode.FC_BRIDGE_BLOCKED),
                _severity_from_bridge(diagnostic.severity),
                diagnostic.message,
                target_ref=diagnostic.target_ref,
                source_field=diagnostic.source_field,
                suggested_fix=diagnostic.suggested_fix,
                blocks_case_plan=diagnostic.blocks_bridge,
                blocks_solver_handoff=diagnostic.blocks_solver_handoff,
            )
        )
    return diagnostics


def _node_plans(graph: Mapping[str, Any]) -> list[CalculiXCaseNodePlan]:
    frames = _coordinate_frame_ids(graph)
    default_frame = frames[0] if frames else ""
    nodes: list[CalculiXCaseNodePlan] = []
    for item in _mapping_sequence(graph.get("nodes", ()), field_name="nodes"):
        node_id = str(item.get("id", ""))
        if not node_id:
            continue
        nodes.append(
            CalculiXCaseNodePlan(
                node_id=node_id,
                coordinates=tuple(_sequence(item.get("coordinates", ()), field_name="coordinates")),
                coordinate_frame=str(item.get("coordinate_frame", default_frame)),
                source_ref=node_id,
                metadata={
                    "source_kind": "feaspec_geometry_node",
                    "units": item.get("units", ""),
                    "evidence_refs": list(
                        _sequence(item.get("evidence_refs", ()), field_name="evidence_refs")
                    ),
                    "confidence": item.get("confidence"),
                },
            )
        )
    return nodes


def _element_plans(
    graph: Mapping[str, Any],
) -> tuple[list[CalculiXCaseElementPlan], list[FEASpecCalculiXPlanDiagnostic]]:
    diagnostics: list[FEASpecCalculiXPlanDiagnostic] = []
    elements: list[CalculiXCaseElementPlan] = []
    element_payloads = _explicit_element_payloads(graph)
    if not element_payloads:
        diagnostics.append(
            _diag(
                CalculiXPlanDiagnosticCode.FC_MESH_REQUIRED,
                CalculiXPlanSeverity.BLOCKER,
                "CalculiX case planning requires explicit mesh or element topology.",
                source_field="geometry_graph",
                suggested_fix="Provide reviewed mesh elements before `.inp` writer handoff.",
            )
        )
        return elements, diagnostics

    for index, item in enumerate(element_payloads, start=1):
        element_id = str(item.get("element_id", item.get("id", f"element_{index}")))
        element_type = str(item.get("element_type", item.get("type", ""))).upper()
        if element_type not in SUPPORTED_ELEMENT_TYPES:
            diagnostics.append(
                _diag(
                    CalculiXPlanDiagnosticCode.FC_UNSUPPORTED_ELEMENT_TYPE,
                    CalculiXPlanSeverity.BLOCKER,
                    f"Element {element_id!r} uses unsupported element type {element_type!r}.",
                    target_ref=element_id,
                    source_field="elements",
                    suggested_fix="Use an explicitly reviewed CalculiX element family.",
                )
            )
        node_refs = tuple(
            str(ref) for ref in _sequence(item.get("node_refs", ()), field_name="node_refs")
        )
        if not node_refs:
            diagnostics.append(
                _diag(
                    CalculiXPlanDiagnosticCode.FC_MESH_REQUIRED,
                    CalculiXPlanSeverity.BLOCKER,
                    f"Element {element_id!r} is missing node_refs.",
                    target_ref=element_id,
                    source_field="elements",
                    suggested_fix="Provide explicit element connectivity.",
                )
            )
        elements.append(
            CalculiXCaseElementPlan(
                element_id=element_id,
                element_type=element_type,
                node_refs=node_refs,
                source_ref=str(item.get("source_ref", element_id)),
                metadata={
                    key: value
                    for key, value in item.items()
                    if key
                    not in {"element_id", "id", "element_type", "type", "node_refs", "source_ref"}
                },
            )
        )
    return elements, diagnostics


def _material_plans(materials: Sequence[Mapping[str, Any]]) -> list[CalculiXCaseMaterialPlan]:
    plans: list[CalculiXCaseMaterialPlan] = []
    for item in materials:
        material_id = str(item.get("id", item.get("material_id", "")))
        if not material_id:
            continue
        plans.append(
            CalculiXCaseMaterialPlan(
                material_id=material_id,
                name=str(item.get("name", material_id)),
                model=str(item.get("model", "")),
                properties=dict(item.get("properties", {})),
                units=dict(item.get("units", {})),
                source_ref=material_id,
                metadata={
                    "source_evidence": list(
                        _sequence(item.get("source_evidence", ()), field_name="source_evidence")
                    ),
                    "confidence": item.get("confidence"),
                },
            )
        )
    return plans


def _section_plans(
    sections: Sequence[Mapping[str, Any]],
    *,
    material_ref: str,
) -> list[CalculiXCaseSectionPlan]:
    plans: list[CalculiXCaseSectionPlan] = []
    for item in sections:
        section_id = str(item.get("id", item.get("section_id", "")))
        if not section_id:
            continue
        plans.append(
            CalculiXCaseSectionPlan(
                section_id=section_id,
                material_ref=str(item.get("material_ref", material_ref)),
                target_refs=tuple(
                    str(ref)
                    for ref in _sequence(item.get("target_refs", ()), field_name="target_refs")
                ),
                section_type=str(item.get("section_type", "")),
                properties=dict(item.get("properties", {})),
                units=dict(item.get("units", {})),
                source_ref=section_id,
                metadata={
                    "source_evidence": list(
                        _sequence(item.get("source_evidence", ()), field_name="source_evidence")
                    ),
                    "confidence": item.get("confidence"),
                },
            )
        )
    return plans


def _bc_plans(
    boundary_conditions: Sequence[Mapping[str, Any]],
) -> list[CalculiXCaseBoundaryConditionPlan]:
    plans: list[CalculiXCaseBoundaryConditionPlan] = []
    for item in boundary_conditions:
        bc_id = str(item.get("id", item.get("bc_id", "")))
        if not bc_id:
            continue
        plans.append(
            CalculiXCaseBoundaryConditionPlan(
                bc_id=bc_id,
                kind=str(item.get("kind", item.get("type", ""))),
                target_refs=tuple(
                    str(ref)
                    for ref in _sequence(item.get("target_refs", ()), field_name="target_refs")
                ),
                degrees_of_freedom=tuple(
                    str(dof)
                    for dof in _sequence(
                        item.get("degrees_of_freedom", ()),
                        field_name="degrees_of_freedom",
                    )
                ),
                values=tuple(_sequence(item.get("values", ()), field_name="values")),
                units=dict(item.get("units", {})),
                coordinate_frame=str(item.get("coordinate_frame", "")),
                source_ref=bc_id,
                metadata={
                    "evidence_refs": list(
                        _sequence(item.get("evidence_refs", ()), field_name="evidence_refs")
                    ),
                    "confidence": item.get("confidence"),
                },
            )
        )
    return plans


def _load_plans(loads: Sequence[Mapping[str, Any]]) -> list[CalculiXCaseLoadPlan]:
    plans: list[CalculiXCaseLoadPlan] = []
    for item in loads:
        load_id = str(item.get("id", item.get("load_id", "")))
        if not load_id:
            continue
        magnitude = dict(item.get("magnitude", {}))
        units = dict(item.get("units", {}))
        if "units" in magnitude and "magnitude" not in units:
            units = {**units, "magnitude": magnitude["units"]}
        plans.append(
            CalculiXCaseLoadPlan(
                load_id=load_id,
                kind=str(item.get("kind", item.get("type", ""))),
                target_refs=tuple(
                    str(ref)
                    for ref in _sequence(item.get("target_refs", ()), field_name="target_refs")
                ),
                magnitude=magnitude,
                direction=str(item.get("direction", "")),
                vector=tuple(_sequence(item.get("vector", ()), field_name="vector")),
                units=units,
                coordinate_frame=str(item.get("coordinate_frame", "")),
                source_ref=load_id,
                metadata={
                    "evidence_refs": list(
                        _sequence(item.get("evidence_refs", ()), field_name="evidence_refs")
                    ),
                    "confidence": item.get("confidence"),
                },
            )
        )
    return plans


def _draft_diagnostics(
    draft: Any,
    nodes: Sequence[CalculiXCaseNodePlan],
    elements: Sequence[CalculiXCaseElementPlan],
    materials: Sequence[CalculiXCaseMaterialPlan],
    sections: Sequence[CalculiXCaseSectionPlan],
) -> list[FEASpecCalculiXPlanDiagnostic]:
    diagnostics: list[FEASpecCalculiXPlanDiagnostic] = []
    missing_units = [
        name for name in ("name", "length", "force") if not str(draft.units.get(name, "")).strip()
    ]
    if missing_units:
        diagnostics.append(
            _diag(
                CalculiXPlanDiagnosticCode.FC_UNITS_UNSUPPORTED,
                CalculiXPlanSeverity.BLOCKER,
                "CalculiX planning requires explicit unit context.",
                target_ref=", ".join(missing_units),
                source_field="units",
                suggested_fix="Declare explicit FEASpec system, length, and force units.",
            )
        )
    if not nodes:
        diagnostics.append(
            _diag(
                CalculiXPlanDiagnosticCode.FC_UNSUPPORTED_GEOMETRY,
                CalculiXPlanSeverity.BLOCKER,
                "No reviewed geometry nodes are available for case planning.",
                source_field="geometry_graph.nodes",
                suggested_fix="Provide reviewed geometry graph nodes.",
            )
        )
    if not elements:
        diagnostics.append(
            _diag(
                CalculiXPlanDiagnosticCode.FC_MESH_REQUIRED,
                CalculiXPlanSeverity.BLOCKER,
                "No explicit CalculiX element plan is available.",
                source_field="elements",
                suggested_fix="Provide reviewed mesh topology before deck writer handoff.",
            )
        )
    if not materials:
        diagnostics.append(
            _diag(
                CalculiXPlanDiagnosticCode.FC_MATERIAL_MISSING,
                CalculiXPlanSeverity.BLOCKER,
                "No reviewed material plan is available.",
                source_field="materials",
                suggested_fix="Add reviewed material data.",
            )
        )
    if not sections:
        diagnostics.append(
            _diag(
                CalculiXPlanDiagnosticCode.FC_SECTION_MISSING,
                CalculiXPlanSeverity.BLOCKER,
                "No reviewed section plan is available.",
                source_field="sections",
                suggested_fix="Add reviewed section assignments.",
            )
        )
    return diagnostics


def _target_diagnostics(
    graph: Mapping[str, Any],
    elements: Sequence[CalculiXCaseElementPlan],
    boundary_conditions: Sequence[CalculiXCaseBoundaryConditionPlan],
    loads: Sequence[CalculiXCaseLoadPlan],
) -> list[FEASpecCalculiXPlanDiagnostic]:
    known_targets = _known_target_refs(graph, elements)
    diagnostics: list[FEASpecCalculiXPlanDiagnostic] = []
    for condition in boundary_conditions:
        missing = [target for target in condition.target_refs if target not in known_targets]
        if missing:
            diagnostics.append(
                _diag(
                    CalculiXPlanDiagnosticCode.FC_BC_INVALID_TARGET,
                    CalculiXPlanSeverity.BLOCKER,
                    "Boundary condition target does not resolve to reviewed geometry.",
                    target_ref=f"{condition.bc_id}: {', '.join(missing)}",
                    source_field="boundary_conditions",
                    suggested_fix="Retarget the boundary condition before writer handoff.",
                )
            )
    for load in loads:
        missing = [target for target in load.target_refs if target not in known_targets]
        if missing:
            diagnostics.append(
                _diag(
                    CalculiXPlanDiagnosticCode.FC_LOAD_INVALID_TARGET,
                    CalculiXPlanSeverity.BLOCKER,
                    "Load target does not resolve to reviewed geometry.",
                    target_ref=f"{load.load_id}: {', '.join(missing)}",
                    source_field="loads",
                    suggested_fix="Retarget the load before writer handoff.",
                )
            )
    return diagnostics


def _load_diagnostics(
    loads: Sequence[CalculiXCaseLoadPlan],
) -> list[FEASpecCalculiXPlanDiagnostic]:
    diagnostics: list[FEASpecCalculiXPlanDiagnostic] = []
    for load in loads:
        if load.kind and load.kind not in SUPPORTED_LOAD_KINDS:
            diagnostics.append(
                _diag(
                    CalculiXPlanDiagnosticCode.FC_LOAD_UNSUPPORTED_TYPE,
                    CalculiXPlanSeverity.BLOCKER,
                    f"Load kind {load.kind!r} is not in the supported planning subset.",
                    target_ref=load.load_id,
                    source_field="loads",
                    suggested_fix="Use a reviewed force, pressure, or distributed load mapping.",
                )
            )
        if load.magnitude and not str(load.magnitude.get("units", "")).strip():
            diagnostics.append(
                _diag(
                    CalculiXPlanDiagnosticCode.FC_UNITS_UNSUPPORTED,
                    CalculiXPlanSeverity.BLOCKER,
                    f"Load {load.load_id!r} magnitude is missing units.",
                    target_ref=load.load_id,
                    source_field="loads",
                    suggested_fix="Add explicit load magnitude units.",
                )
            )
    return diagnostics


def _constraint_diagnostics(
    boundary_conditions: Sequence[CalculiXCaseBoundaryConditionPlan],
) -> list[FEASpecCalculiXPlanDiagnostic]:
    constrained_dofs = sum(len(condition.degrees_of_freedom) for condition in boundary_conditions)
    if constrained_dofs >= 2:
        return []
    return [
        _diag(
            CalculiXPlanDiagnosticCode.FC_BC_INSUFFICIENT_CONSTRAINTS,
            CalculiXPlanSeverity.WARNING,
            "Boundary conditions may be insufficient for a stable future case.",
            source_field="boundary_conditions",
            suggested_fix="Review supports and constrained degrees of freedom.",
            blocks_case_plan=False,
            blocks_solver_handoff=True,
        )
    ]


def _provenance_diagnostics(
    bridge_plan: FEASpecProjectBridgePlan,
) -> list[FEASpecCalculiXPlanDiagnostic]:
    provenance = bridge_plan.provenance
    if provenance.source and provenance.evidence and provenance.human_review:
        return []
    return [
        _diag(
            CalculiXPlanDiagnosticCode.FC_PROVENANCE_INCOMPLETE,
            CalculiXPlanSeverity.WARNING,
            "Case-plan provenance is incomplete.",
            source_field="provenance",
            suggested_fix="Preserve source, evidence, confidence, and human review records.",
            blocks_case_plan=False,
            blocks_solver_handoff=True,
        )
    ]


def _default_steps() -> tuple[CalculiXCaseStepPlan, ...]:
    return (
        CalculiXCaseStepPlan(
            metadata={
                "planned_only": True,
                "source": "FEASpec CalculiX case plan",
                "supported_step_types": sorted(SUPPORTED_STEP_TYPES),
                "inp_writer_performed": False,
                "solver_execution_performed": False,
            }
        ),
    )


def _default_output_requests() -> tuple[CalculiXCaseOutputRequestPlan, ...]:
    return (
        CalculiXCaseOutputRequestPlan(
            request_id="default_displacement_stress",
            variables=DEFAULT_OUTPUT_VARIABLES,
            metadata={
                "planned_only": True,
                "inp_writer_performed": False,
                "solver_execution_performed": False,
            },
        ),
    )


def _explicit_element_payloads(graph: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    direct = list(_mapping_sequence(graph.get("elements", ()), field_name="elements"))
    if direct:
        return direct
    mesh = graph.get("mesh")
    if isinstance(mesh, Mapping):
        mesh_elements = list(
            _mapping_sequence(mesh.get("elements", ()), field_name="mesh.elements")
        )
        if mesh_elements:
            return mesh_elements
    topology = graph.get("mesh_topology")
    if isinstance(topology, Mapping):
        topology_elements = list(
            _mapping_sequence(topology.get("elements", ()), field_name="mesh_topology.elements")
        )
        if topology_elements:
            return topology_elements
    return []


def _known_target_refs(
    graph: Mapping[str, Any],
    elements: Sequence[CalculiXCaseElementPlan],
) -> set[str]:
    refs: set[str] = {element.element_id for element in elements}
    for field_name in ("nodes", "edges", "regions"):
        for item in _mapping_sequence(graph.get(field_name, ()), field_name=field_name):
            item_id = str(item.get("id", ""))
            if item_id:
                refs.add(item_id)
    return refs


def _coordinate_frame_ids(graph: Mapping[str, Any]) -> list[str]:
    return [
        str(item.get("id", ""))
        for item in _mapping_sequence(
            graph.get("coordinate_frames", ()),
            field_name="coordinate_frames",
        )
        if item.get("id")
    ]


def _first_material_ref(materials: Sequence[CalculiXCaseMaterialPlan]) -> str:
    return materials[0].material_id if materials else ""


def _provenance_comments(bridge_plan: FEASpecProjectBridgePlan) -> list[str]:
    source = bridge_plan.provenance.source
    source_id = str(source.get("source_id", "unknown"))
    comments = [
        f"Source FEASpec: {source_id}",
        f"Bridge status: {bridge_plan.status.value}",
        "Human review is required before writer handoff.",
        "No `.inp` writer or solver execution was performed.",
    ]
    validation_state = bridge_plan.provenance.validation_summary.get("validation_state")
    if validation_state:
        comments.append(f"Validator state: {validation_state}")
    return comments


def _status_for(
    diagnostics: Sequence[FEASpecCalculiXPlanDiagnostic],
    *,
    has_warnings: bool,
) -> CalculiXCaseStatus:
    if any(diagnostic.blocks_case_plan for diagnostic in diagnostics):
        return CalculiXCaseStatus.BLOCKED
    if has_warnings or any(
        diagnostic.severity is CalculiXPlanSeverity.WARNING for diagnostic in diagnostics
    ):
        return CalculiXCaseStatus.PLAN_READY_WITH_WARNINGS
    return CalculiXCaseStatus.PLAN_READY


def _severity_from_bridge(severity: BridgeSeverity) -> CalculiXPlanSeverity:
    return {
        BridgeSeverity.INFO: CalculiXPlanSeverity.INFO,
        BridgeSeverity.WARNING: CalculiXPlanSeverity.WARNING,
        BridgeSeverity.ERROR: CalculiXPlanSeverity.ERROR,
        BridgeSeverity.BLOCKER: CalculiXPlanSeverity.BLOCKER,
    }[severity]


def _diag(
    code: CalculiXPlanDiagnosticCode,
    severity: CalculiXPlanSeverity,
    message: str,
    *,
    target_ref: str = "",
    source_field: str = "",
    suggested_fix: str = "",
    blocks_case_plan: bool | None = None,
    blocks_solver_handoff: bool = True,
) -> FEASpecCalculiXPlanDiagnostic:
    return FEASpecCalculiXPlanDiagnostic.make(
        code,
        severity,
        message,
        target_ref=target_ref,
        source_field=source_field,
        suggested_fix=suggested_fix,
        blocks_case_plan=blocks_case_plan,
        blocks_solver_handoff=blocks_solver_handoff,
    )


def _dedupe_diagnostics(
    diagnostics: Sequence[FEASpecCalculiXPlanDiagnostic],
) -> list[FEASpecCalculiXPlanDiagnostic]:
    seen: set[tuple[CalculiXPlanDiagnosticCode, str, str]] = set()
    unique: list[FEASpecCalculiXPlanDiagnostic] = []
    for diagnostic in diagnostics:
        key = (diagnostic.code, diagnostic.target_ref, diagnostic.source_field)
        if key not in seen:
            seen.add(key)
            unique.append(diagnostic)
    return unique


def _case_id(source: Mapping[str, Any]) -> str:
    source_id = str(source.get("source_id", "feaspec"))
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", source_id).strip("-") or "feaspec"
    return f"{slug}-calculix-case-plan"


def _sequence(value: object, *, field_name: str) -> Sequence[Any]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Sequence):
        msg = f"{field_name} must be a sequence."
        raise TypeError(msg)
    return value


def _mapping_sequence(value: object, *, field_name: str) -> list[Mapping[str, Any]]:
    return [
        item
        for item in _sequence(value, field_name=field_name)
        if isinstance(item, Mapping)
    ]
