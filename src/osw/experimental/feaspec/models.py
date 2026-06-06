"""Experimental FEASpec data models.

This module is intentionally limited to parsing, preserving, and serializing
FEASpec-style dictionaries plus structural basic checks. It does not implement
ProjectSchema bridging, solver adapters, VLM provider integration, or solver
execution.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Self

from .errors import FEASpecDiagnosticError, FEASpecModelError

SOURCE_TYPES = frozenset(
    {
        "image",
        "drawing",
        "text",
        "text_problem_statement",
        "manual",
        "manual_annotation",
        "generated_benchmark",
        "synthetic_drawing_placeholder",
    }
)
LOAD_TYPES = frozenset({"point_force", "force", "moment", "pressure", "distributed"})
SOLVER_COMPATIBILITY_STATES = frozenset(
    {
        "planned",
        "planned_after_approval",
        "supported",
        "optional_non_default",
        "unsupported",
        "unknown",
        "blocked",
    }
)


class SpecType(str, Enum):
    """Top-level FEASpec document type."""

    CANDIDATE = "candidate"
    APPROVED = "approved"

    @classmethod
    def from_value(cls, value: object) -> SpecType:
        try:
            return cls(str(value))
        except ValueError as exc:
            msg = f"Unsupported FEASpec spec_type: {value!r}"
            raise FEASpecModelError(msg) from exc


class ValidationState(str, Enum):
    """Document validation/review state for FEASpec data."""

    UNCHECKED = "unchecked"
    INVALID = "invalid"
    VALID_WITH_WARNINGS = "valid-with-warnings"
    APPROVED = "approved"
    REJECTED = "rejected"

    @classmethod
    def from_value(cls, value: object) -> ValidationState:
        try:
            return cls(str(value))
        except ValueError as exc:
            msg = f"Unsupported FEASpec validation state: {value!r}"
            raise FEASpecModelError(msg) from exc


@dataclass(frozen=True)
class FEASource:
    source_type: str
    source_id: str = ""
    summary: str = ""
    provider_id: str = ""
    trust: str = ""
    notes: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> FEASource:
        payload = _mapping(data, "source")
        known = {"source_type", "source_id", "summary", "provider_id", "trust", "notes"}
        return cls(
            source_type=str(payload.get("source_type", "")),
            source_id=str(payload.get("source_id", "")),
            summary=str(payload.get("summary", "")),
            provider_id=str(payload.get("provider_id", "")),
            trust=str(payload.get("trust", "")),
            notes=str(payload.get("notes", "")),
            extra=_extra(payload, known),
        )

    def to_dict(self) -> dict[str, Any]:
        return _drop_empty(
            {
                "source_type": self.source_type,
                "source_id": self.source_id,
                "summary": self.summary,
                "provider_id": self.provider_id,
                "trust": self.trust,
                "notes": self.notes,
                **self.extra,
            }
        )


@dataclass(frozen=True)
class FEASpecUnits:
    system: str
    length: str = ""
    force: str = ""
    stress: str = ""
    mass: str = ""
    time: str = ""
    temperature: str = ""
    angle: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> FEASpecUnits:
        payload = _mapping(data, "units")
        known = {"system", "length", "force", "stress", "mass", "time", "temperature", "angle"}
        return cls(
            system=str(payload.get("system", "")),
            length=str(payload.get("length", "")),
            force=str(payload.get("force", "")),
            stress=str(payload.get("stress", "")),
            mass=str(payload.get("mass", "")),
            time=str(payload.get("time", "")),
            temperature=str(payload.get("temperature", "")),
            angle=str(payload.get("angle", "")),
            extra=_extra(payload, known),
        )

    def to_dict(self) -> dict[str, Any]:
        return _drop_empty(
            {
                "system": self.system,
                "length": self.length,
                "force": self.force,
                "stress": self.stress,
                "mass": self.mass,
                "time": self.time,
                "temperature": self.temperature,
                "angle": self.angle,
                **self.extra,
            }
        )


@dataclass(frozen=True)
class FEANode:
    id: str
    coordinates: list[Any] = field(default_factory=list)
    units: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    confidence: Any = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> FEANode:
        payload = _mapping(data, "geometry.nodes[]")
        known = {"id", "coordinates", "units", "evidence_refs", "confidence"}
        return cls(
            id=str(payload.get("id", "")),
            coordinates=list(
                _sequence(payload.get("coordinates", []), "geometry.nodes[].coordinates")
            ),
            units=str(payload.get("units", "")),
            evidence_refs=_str_list(payload.get("evidence_refs", [])),
            confidence=payload.get("confidence"),
            extra=_extra(payload, known),
        )

    def to_dict(self) -> dict[str, Any]:
        return _drop_none(
            {
                "id": self.id,
                "coordinates": list(self.coordinates),
                "units": self.units,
                "evidence_refs": list(self.evidence_refs),
                "confidence": self.confidence,
                **self.extra,
            }
        )


@dataclass(frozen=True)
class FEAEdge:
    id: str
    node_refs: list[str] = field(default_factory=list)
    kind: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    confidence: Any = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> FEAEdge:
        payload = _mapping(data, "geometry.edges[]")
        known = {"id", "node_refs", "kind", "evidence_refs", "confidence"}
        return cls(
            id=str(payload.get("id", "")),
            node_refs=_str_list(payload.get("node_refs", [])),
            kind=str(payload.get("kind", "")),
            evidence_refs=_str_list(payload.get("evidence_refs", [])),
            confidence=payload.get("confidence"),
            extra=_extra(payload, known),
        )

    def to_dict(self) -> dict[str, Any]:
        return _drop_none(
            {
                "id": self.id,
                "node_refs": list(self.node_refs),
                "kind": self.kind,
                "evidence_refs": list(self.evidence_refs),
                "confidence": self.confidence,
                **self.extra,
            }
        )


@dataclass(frozen=True)
class FEARegion:
    id: str
    boundary_refs: list[str] = field(default_factory=list)
    boundary_edge_refs: list[str] = field(default_factory=list)
    void_edge_refs: list[str] = field(default_factory=list)
    region_type: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    confidence: Any = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> FEARegion:
        payload = _mapping(data, "geometry.regions[]")
        known = {
            "id",
            "boundary_refs",
            "boundary_edge_refs",
            "void_edge_refs",
            "region_type",
            "evidence_refs",
            "confidence",
        }
        return cls(
            id=str(payload.get("id", "")),
            boundary_refs=_str_list(payload.get("boundary_refs", [])),
            boundary_edge_refs=_str_list(payload.get("boundary_edge_refs", [])),
            void_edge_refs=_str_list(payload.get("void_edge_refs", [])),
            region_type=str(payload.get("region_type", "")),
            evidence_refs=_str_list(payload.get("evidence_refs", [])),
            confidence=payload.get("confidence"),
            extra=_extra(payload, known),
        )

    def to_dict(self) -> dict[str, Any]:
        return _drop_empty(
            {
                "id": self.id,
                "boundary_refs": list(self.boundary_refs),
                "boundary_edge_refs": list(self.boundary_edge_refs),
                "void_edge_refs": list(self.void_edge_refs),
                "region_type": self.region_type,
                "evidence_refs": list(self.evidence_refs),
                "confidence": self.confidence,
                **self.extra,
            }
        )


@dataclass(frozen=True)
class CoordinateFrame:
    id: str
    type: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> CoordinateFrame:
        payload = _mapping(data, "geometry.coordinate_frames[]")
        known = {"id", "type"}
        return cls(
            id=str(payload.get("id", "")),
            type=str(payload.get("type", "")),
            extra=_extra(payload, known),
        )

    def to_dict(self) -> dict[str, Any]:
        return _drop_empty({"id": self.id, "type": self.type, **self.extra})


@dataclass(frozen=True)
class GeometryGraph:
    nodes: list[FEANode] = field(default_factory=list)
    edges: list[FEAEdge] = field(default_factory=list)
    regions: list[FEARegion] = field(default_factory=list)
    coordinate_frames: list[CoordinateFrame] = field(default_factory=list)
    scale_constraints: list[Any] = field(default_factory=list)
    dimension_constraints: list[Any] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> GeometryGraph:
        payload = _mapping(data, "geometry.geometry_graph")
        known = {
            "nodes",
            "edges",
            "regions",
            "coordinate_frames",
            "scale_constraints",
            "dimension_constraints",
        }
        return cls(
            nodes=[
                FEANode.from_dict(item)
                for item in _sequence(payload.get("nodes", []), "nodes")
            ],
            edges=[
                FEAEdge.from_dict(item)
                for item in _sequence(payload.get("edges", []), "edges")
            ],
            regions=[
                FEARegion.from_dict(item)
                for item in _sequence(payload.get("regions", []), "regions")
            ],
            coordinate_frames=[
                CoordinateFrame.from_dict(item)
                for item in _sequence(payload.get("coordinate_frames", []), "coordinate_frames")
            ],
            scale_constraints=list(
                _sequence(payload.get("scale_constraints", []), "scale_constraints")
            ),
            dimension_constraints=list(
                _sequence(payload.get("dimension_constraints", []), "dimension_constraints")
            ),
            extra=_extra(payload, known),
        )

    @property
    def node_ids(self) -> set[str]:
        return {node.id for node in self.nodes if node.id}

    @property
    def edge_ids(self) -> set[str]:
        return {edge.id for edge in self.edges if edge.id}

    @property
    def region_ids(self) -> set[str]:
        return {region.id for region in self.regions if region.id}

    @property
    def geometry_ids(self) -> set[str]:
        return self.node_ids | self.edge_ids | self.region_ids

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "regions": [region.to_dict() for region in self.regions],
            "coordinate_frames": [frame.to_dict() for frame in self.coordinate_frames],
            "scale_constraints": list(self.scale_constraints),
            "dimension_constraints": list(self.dimension_constraints),
            **self.extra,
        }


@dataclass(frozen=True)
class MaterialSpec:
    id: str
    name: str = ""
    model: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    units: dict[str, Any] = field(default_factory=dict)
    source_evidence: list[str] = field(default_factory=list)
    confidence: Any = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> MaterialSpec:
        payload = _mapping(data, "materials[]")
        known = {"id", "name", "model", "properties", "units", "source_evidence", "confidence"}
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            model=str(payload.get("model", "")),
            properties=_dict(payload.get("properties", {}), "materials[].properties"),
            units=_dict(payload.get("units", {}), "materials[].units"),
            source_evidence=_str_list(payload.get("source_evidence", [])),
            confidence=payload.get("confidence"),
            extra=_extra(payload, known),
        )

    def to_dict(self) -> dict[str, Any]:
        return _drop_none(
            {
                "id": self.id,
                "name": self.name,
                "model": self.model,
                "properties": dict(self.properties),
                "units": dict(self.units),
                "source_evidence": list(self.source_evidence),
                "confidence": self.confidence,
                **self.extra,
            }
        )


@dataclass(frozen=True)
class SectionSpec:
    id: str
    target_refs: list[str] = field(default_factory=list)
    section_type: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    units: dict[str, Any] = field(default_factory=dict)
    source_evidence: list[str] = field(default_factory=list)
    confidence: Any = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> SectionSpec:
        payload = _mapping(data, "sections[]")
        known = {
            "id",
            "target_refs",
            "section_type",
            "properties",
            "units",
            "source_evidence",
            "confidence",
        }
        return cls(
            id=str(payload.get("id", "")),
            target_refs=_str_list(payload.get("target_refs", [])),
            section_type=str(payload.get("section_type", "")),
            properties=_dict(payload.get("properties", {}), "sections[].properties"),
            units=_dict(payload.get("units", {}), "sections[].units"),
            source_evidence=_str_list(payload.get("source_evidence", [])),
            confidence=payload.get("confidence"),
            extra=_extra(payload, known),
        )

    def to_dict(self) -> dict[str, Any]:
        return _drop_none(
            {
                "id": self.id,
                "target_refs": list(self.target_refs),
                "section_type": self.section_type,
                "properties": dict(self.properties),
                "units": dict(self.units),
                "source_evidence": list(self.source_evidence),
                "confidence": self.confidence,
                **self.extra,
            }
        )


@dataclass(frozen=True)
class BoundaryConditionSpec:
    id: str
    target_refs: list[str] = field(default_factory=list)
    kind: str = ""
    degrees_of_freedom: list[str] = field(default_factory=list)
    values: list[Any] = field(default_factory=list)
    units: dict[str, Any] = field(default_factory=dict)
    coordinate_frame: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    confidence: Any = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> BoundaryConditionSpec:
        payload = _mapping(data, "boundary_conditions[]")
        known = {
            "id",
            "target_refs",
            "kind",
            "degrees_of_freedom",
            "values",
            "units",
            "coordinate_frame",
            "evidence_refs",
            "confidence",
        }
        return cls(
            id=str(payload.get("id", "")),
            target_refs=_str_list(payload.get("target_refs", [])),
            kind=str(payload.get("kind", "")),
            degrees_of_freedom=_str_list(payload.get("degrees_of_freedom", [])),
            values=list(_sequence(payload.get("values", []), "boundary_conditions[].values")),
            units=_dict(payload.get("units", {}), "boundary_conditions[].units"),
            coordinate_frame=str(payload.get("coordinate_frame", "")),
            evidence_refs=_str_list(payload.get("evidence_refs", [])),
            confidence=payload.get("confidence"),
            extra=_extra(payload, known),
        )

    def to_dict(self) -> dict[str, Any]:
        return _drop_none(
            {
                "id": self.id,
                "target_refs": list(self.target_refs),
                "kind": self.kind,
                "degrees_of_freedom": list(self.degrees_of_freedom),
                "values": list(self.values),
                "units": dict(self.units),
                "coordinate_frame": self.coordinate_frame,
                "evidence_refs": list(self.evidence_refs),
                "confidence": self.confidence,
                **self.extra,
            }
        )


@dataclass(frozen=True)
class LoadSpec:
    id: str
    target_refs: list[str] = field(default_factory=list)
    kind: str = ""
    magnitude: dict[str, Any] = field(default_factory=dict)
    direction: str = ""
    vector: list[Any] = field(default_factory=list)
    coordinate_frame: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    confidence: Any = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> LoadSpec:
        payload = _mapping(data, "loads[]")
        known = {
            "id",
            "target_refs",
            "kind",
            "magnitude",
            "direction",
            "vector",
            "coordinate_frame",
            "evidence_refs",
            "confidence",
        }
        return cls(
            id=str(payload.get("id", "")),
            target_refs=_str_list(payload.get("target_refs", [])),
            kind=str(payload.get("kind", "")),
            magnitude=_dict(payload.get("magnitude", {}), "loads[].magnitude"),
            direction=str(payload.get("direction", "")),
            vector=list(_sequence(payload.get("vector", []), "loads[].vector")),
            coordinate_frame=str(payload.get("coordinate_frame", "")),
            evidence_refs=_str_list(payload.get("evidence_refs", [])),
            confidence=payload.get("confidence"),
            extra=_extra(payload, known),
        )

    def to_dict(self) -> dict[str, Any]:
        return _drop_none(
            {
                "id": self.id,
                "target_refs": list(self.target_refs),
                "kind": self.kind,
                "magnitude": dict(self.magnitude),
                "direction": self.direction,
                "vector": list(self.vector),
                "coordinate_frame": self.coordinate_frame,
                "evidence_refs": list(self.evidence_refs),
                "confidence": self.confidence,
                **self.extra,
            }
        )


@dataclass(frozen=True)
class DimensionConstraint:
    id: str
    target_refs: list[str] = field(default_factory=list)
    value: Any = None
    units: str = ""
    source: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    confidence: Any = None
    review_status: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> DimensionConstraint:
        payload = _mapping(data, "dimensions[]")
        known = {
            "id",
            "target_refs",
            "value",
            "units",
            "source",
            "evidence_refs",
            "confidence",
            "review_status",
        }
        return cls(
            id=str(payload.get("id", "")),
            target_refs=_str_list(payload.get("target_refs", [])),
            value=payload.get("value"),
            units=str(payload.get("units", "")),
            source=str(payload.get("source", "")),
            evidence_refs=_str_list(payload.get("evidence_refs", [])),
            confidence=payload.get("confidence"),
            review_status=str(payload.get("review_status", "")),
            extra=_extra(payload, known),
        )

    def to_dict(self) -> dict[str, Any]:
        return _drop_none(
            {
                "id": self.id,
                "target_refs": list(self.target_refs),
                "value": self.value,
                "units": self.units,
                "source": self.source,
                "evidence_refs": list(self.evidence_refs),
                "confidence": self.confidence,
                "review_status": self.review_status,
                **self.extra,
            }
        )


@dataclass(frozen=True)
class Assumption:
    text: str
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_value(cls, value: object) -> Assumption:
        if isinstance(value, Mapping):
            payload = dict(value)
            text = str(payload.get("text", payload.get("summary", "")))
            return cls(text=text, extra=_extra(payload, {"text", "summary"}))
        return cls(text=str(value))

    def to_value(self) -> str | dict[str, Any]:
        if self.extra:
            return {"text": self.text, **self.extra}
        return self.text


@dataclass(frozen=True)
class EvidenceRef:
    id: str
    kind: str = ""
    text: str = ""
    confidence: Any = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> EvidenceRef:
        payload = _mapping(data, "evidence[]")
        known = {"id", "kind", "text", "confidence"}
        return cls(
            id=str(payload.get("id", "")),
            kind=str(payload.get("kind", "")),
            text=str(payload.get("text", "")),
            confidence=payload.get("confidence"),
            extra=_extra(payload, known),
        )

    def to_dict(self) -> dict[str, Any]:
        return _drop_none(
            {
                "id": self.id,
                "kind": self.kind,
                "text": self.text,
                "confidence": self.confidence,
                **self.extra,
            }
        )


@dataclass(frozen=True)
class Confidence:
    values: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> Confidence:
        return cls(values=_dict(data, "confidence"))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.values)


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    code: str
    message: str
    target_refs: list[str] = field(default_factory=list)
    path: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> Diagnostic:
        payload = _mapping(data, "diagnostics[]")
        known = {"severity", "code", "message", "target_refs", "path"}
        return cls(
            severity=str(payload.get("severity", "")),
            code=str(payload.get("code", "")),
            message=str(payload.get("message", "")),
            target_refs=_str_list(payload.get("target_refs", [])),
            path=str(payload.get("path", "")),
            extra=_extra(payload, known),
        )

    @classmethod
    def error(
        cls,
        code: str,
        message: str,
        *,
        path: str = "",
        target_refs: Sequence[str] = (),
    ) -> Diagnostic:
        return cls("error", code, message, list(target_refs), path)

    @classmethod
    def warning(
        cls,
        code: str,
        message: str,
        *,
        path: str = "",
        target_refs: Sequence[str] = (),
    ) -> Diagnostic:
        return cls("warning", code, message, list(target_refs), path)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "target_refs": list(self.target_refs),
            "path": self.path,
            **self.extra,
        }
        return _drop_empty(payload)


@dataclass(frozen=True)
class ValidationInfo:
    state: ValidationState
    review_required: bool = True
    approval_required_before_solver_case_generation: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> ValidationInfo:
        payload = _mapping(data, "validation")
        known = {"state", "review_required", "approval_required_before_solver_case_generation"}
        return cls(
            state=ValidationState.from_value(payload.get("state", ValidationState.UNCHECKED.value)),
            review_required=bool(payload.get("review_required", True)),
            approval_required_before_solver_case_generation=bool(
                payload.get("approval_required_before_solver_case_generation", True)
            ),
            extra=_extra(payload, known),
        )

    @property
    def is_approved(self) -> bool:
        return self.state is ValidationState.APPROVED

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "review_required": self.review_required,
            "approval_required_before_solver_case_generation": (
                self.approval_required_before_solver_case_generation
            ),
            **self.extra,
        }


@dataclass(frozen=True)
class SolverCompatibility:
    solvers: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> SolverCompatibility:
        payload = _dict(data, "solver_compatibility")
        return cls(
            solvers={
                str(name): dict(value) if isinstance(value, Mapping) else {"state": str(value)}
                for name, value in payload.items()
            }
        )

    def state_for(self, solver_name: str) -> str:
        entry = self.solvers.get(solver_name, {})
        return str(entry.get("state", "unknown"))

    def to_dict(self) -> dict[str, Any]:
        return {name: dict(entry) for name, entry in self.solvers.items()}


@dataclass(frozen=True)
class HumanReview:
    reviewer: str = ""
    action: str = ""
    timestamp: str = ""
    reviewed_items: list[str] = field(default_factory=list)
    notes: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> HumanReview:
        payload = _mapping(data, "human_review")
        known = {"reviewer", "action", "timestamp", "reviewed_items", "notes"}
        return cls(
            reviewer=str(payload.get("reviewer", "")),
            action=str(payload.get("action", "")),
            timestamp=str(payload.get("timestamp", "")),
            reviewed_items=_str_list(payload.get("reviewed_items", [])),
            notes=str(payload.get("notes", "")),
            extra=_extra(payload, known),
        )

    def to_dict(self) -> dict[str, Any]:
        return _drop_empty(
            {
                "reviewer": self.reviewer,
                "action": self.action,
                "timestamp": self.timestamp,
                "reviewed_items": list(self.reviewed_items),
                "notes": self.notes,
                **self.extra,
            }
        )


@dataclass(frozen=True)
class FEASpecDocument:
    schema_version: str
    spec_type: SpecType
    source: FEASource
    problem_type: str
    units: FEASpecUnits
    geometry: GeometryGraph
    materials: list[MaterialSpec]
    sections: list[SectionSpec]
    boundary_conditions: list[BoundaryConditionSpec]
    loads: list[LoadSpec]
    dimensions: list[DimensionConstraint]
    assumptions: list[Assumption]
    evidence: list[EvidenceRef]
    confidence: Confidence
    diagnostics: list[Diagnostic]
    validation: ValidationInfo
    solver_compatibility: SolverCompatibility
    human_review: HumanReview | None = None
    expected_diagnostics: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> Self:
        payload = _mapping(data, "feaspec")
        known = {
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
            "human_review",
            "expected_diagnostics",
        }
        geometry_payload = _mapping(payload.get("geometry", {}), "geometry")
        graph = GeometryGraph.from_dict(geometry_payload.get("geometry_graph", {}))
        human_review = (
            HumanReview.from_dict(payload["human_review"])
            if isinstance(payload.get("human_review"), Mapping)
            else None
        )
        return cls(
            schema_version=str(payload.get("schema_version", "")),
            spec_type=SpecType.from_value(payload.get("spec_type", "")),
            source=FEASource.from_dict(payload.get("source", {})),
            problem_type=str(payload.get("problem_type", "")),
            units=FEASpecUnits.from_dict(payload.get("units", {})),
            geometry=graph,
            materials=[
                MaterialSpec.from_dict(item)
                for item in _sequence(payload.get("materials", []), "materials")
            ],
            sections=[
                SectionSpec.from_dict(item)
                for item in _sequence(payload.get("sections", []), "sections")
            ],
            boundary_conditions=[
                BoundaryConditionSpec.from_dict(item)
                for item in _sequence(payload.get("boundary_conditions", []), "boundary_conditions")
            ],
            loads=[
                LoadSpec.from_dict(item)
                for item in _sequence(payload.get("loads", []), "loads")
            ],
            dimensions=[
                DimensionConstraint.from_dict(item)
                for item in _sequence(payload.get("dimensions", []), "dimensions")
            ],
            assumptions=[
                Assumption.from_value(item)
                for item in _sequence(payload.get("assumptions", []), "assumptions")
            ],
            evidence=[
                EvidenceRef.from_dict(item)
                for item in _sequence(payload.get("evidence", []), "evidence")
            ],
            confidence=Confidence.from_dict(payload.get("confidence", {})),
            diagnostics=[
                Diagnostic.from_dict(item)
                for item in _sequence(payload.get("diagnostics", []), "diagnostics")
            ],
            validation=ValidationInfo.from_dict(payload.get("validation", {})),
            solver_compatibility=SolverCompatibility.from_dict(
                payload.get("solver_compatibility", {})
            ),
            human_review=human_review,
            expected_diagnostics=_str_list(payload.get("expected_diagnostics", [])),
            extra=_extra(payload, known),
        )

    @property
    def is_candidate(self) -> bool:
        return self.spec_type is SpecType.CANDIDATE

    @property
    def is_approved(self) -> bool:
        return self.spec_type is SpecType.APPROVED and self.validation.is_approved

    @property
    def approval_required_before_solver_case_generation(self) -> bool:
        return self.validation.approval_required_before_solver_case_generation

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "spec_type": self.spec_type.value,
            "source": self.source.to_dict(),
            "problem_type": self.problem_type,
            "units": self.units.to_dict(),
            "geometry": {"geometry_graph": self.geometry.to_dict()},
            "materials": [material.to_dict() for material in self.materials],
            "sections": [section.to_dict() for section in self.sections],
            "boundary_conditions": [bc.to_dict() for bc in self.boundary_conditions],
            "loads": [load.to_dict() for load in self.loads],
            "dimensions": [dimension.to_dict() for dimension in self.dimensions],
            "assumptions": [assumption.to_value() for assumption in self.assumptions],
            "evidence": [evidence.to_dict() for evidence in self.evidence],
            "confidence": self.confidence.to_dict(),
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
            "validation": self.validation.to_dict(),
            "solver_compatibility": self.solver_compatibility.to_dict(),
            **self.extra,
        }
        if self.human_review is not None:
            payload["human_review"] = self.human_review.to_dict()
        if self.expected_diagnostics:
            payload["expected_diagnostics"] = list(self.expected_diagnostics)
        return payload


@dataclass(frozen=True)
class FEASpecCandidate(FEASpecDocument):
    """Untrusted FEASpec draft data that must not be treated as solver-ready."""


@dataclass(frozen=True)
class FEASpec(FEASpecDocument):
    """Human-approved FEASpec data for future bridge planning."""


def parse_feaspec_dict(
    data: object,
    *,
    allow_diagnostics: bool = False,
) -> FEASpecCandidate | FEASpec:
    """Parse a FEASpec dictionary and run structural basic checks.

    Set ``allow_diagnostics`` to return a model for deliberately invalid
    diagnostic fixtures. By default, any basic-check error raises
    :class:`FEASpecDiagnosticError`.
    """

    from .basic_checks import check_feaspec_dict

    payload = _mapping(data, "feaspec")
    diagnostics = check_feaspec_dict(payload)
    if any(diagnostic.severity == "error" for diagnostic in diagnostics) and not allow_diagnostics:
        raise FEASpecDiagnosticError(diagnostics)
    document_type: type[FEASpecCandidate] | type[FEASpec]
    spec_type = SpecType.from_value(payload.get("spec_type", ""))
    document_type = FEASpec if spec_type is SpecType.APPROVED else FEASpecCandidate
    model = document_type.from_dict(payload)
    if diagnostics:
        model_diagnostics = tuple(model.diagnostics)
        object.__setattr__(model, "diagnostics", list(model_diagnostics + tuple(diagnostics)))
    return model


def _mapping(data: object, path: str) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        msg = f"{path} must be a mapping."
        raise FEASpecModelError(msg)
    return data


def _dict(data: object, path: str) -> dict[str, Any]:
    return dict(_mapping(data, path))


def _sequence(data: object, path: str) -> Sequence[Any]:
    if data is None:
        return ()
    if isinstance(data, str) or not isinstance(data, Sequence):
        msg = f"{path} must be a sequence."
        raise FEASpecModelError(msg)
    return data


def _str_list(data: object) -> list[str]:
    return [str(item) for item in _sequence(data, "list")]


def _extra(payload: Mapping[str, Any], known: set[str]) -> dict[str, Any]:
    return {str(key): value for key, value in payload.items() if key not in known}


def _drop_empty(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        str(key): value
        for key, value in payload.items()
        if value not in ("", [], {}) and value is not None
    }


def _drop_none(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in payload.items() if value is not None}
