"""Typed CalculiX deck models for prepare-only linear static workflows."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class CalculiXAnalysisType(StrEnum):
    """Analysis families supported by the v0.1 deck writer."""

    LINEAR_STATIC = "linear_static"


class CalculiXElementType(StrEnum):
    """Small CalculiX element set supported or reserved by OSW v0.1."""

    C3D4 = "C3D4"
    C3D8 = "C3D8"
    C3D10 = "C3D10"
    C3D20 = "C3D20"
    CPS3 = "CPS3"
    CPS4 = "CPS4"
    UNKNOWN = "UNKNOWN"


class CalculiXDeckStatus(StrEnum):
    """Status values for deck generation results."""

    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class CalculiXMaterial:
    """Isotropic elastic material mapped to CalculiX syntax."""

    name: str
    elastic_modulus: float
    poisson_ratio: float
    density: float | None = None
    units: str = "SI"
    source_material_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "elastic_modulus": self.elastic_modulus,
            "poisson_ratio": self.poisson_ratio,
            "density": self.density,
            "units": self.units,
            "source_material_id": self.source_material_id,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CalculiXMaterial:
        if not isinstance(data, Mapping):
            msg = "CalculiXMaterial must be a mapping."
            raise ValueError(msg)
        density = data.get("density")
        return cls(
            name=str(data.get("name", "")),
            elastic_modulus=float(data.get("elastic_modulus", 0.0)),
            poisson_ratio=float(data.get("poisson_ratio", 0.0)),
            density=float(density) if density not in (None, "") else None,
            units=str(data.get("units", "SI")),
            source_material_id=str(data.get("source_material_id", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CalculiXNode:
    """One-based CalculiX node record."""

    node_id: int
    coordinates: tuple[float, float, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "coordinates": list(self.coordinates),
        }

    @classmethod
    def from_dict(cls, data: object) -> CalculiXNode:
        if not isinstance(data, Mapping):
            msg = "CalculiXNode must be a mapping."
            raise ValueError(msg)
        return cls(
            node_id=int(data.get("node_id", 0)),
            coordinates=_float_tuple(data.get("coordinates", (0.0, 0.0, 0.0)), length=3),
        )


@dataclass(frozen=True)
class CalculiXElement:
    """One-based CalculiX element record."""

    element_id: int
    element_type: str
    node_ids: tuple[int, ...]
    element_set: str = "EALL"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "element_id": self.element_id,
            "element_type": self.element_type,
            "node_ids": list(self.node_ids),
            "element_set": self.element_set,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CalculiXElement:
        if not isinstance(data, Mapping):
            msg = "CalculiXElement must be a mapping."
            raise ValueError(msg)
        return cls(
            element_id=int(data.get("element_id", 0)),
            element_type=str(data.get("element_type", CalculiXElementType.UNKNOWN.value)),
            node_ids=_int_tuple(data.get("node_ids", ())),
            element_set=str(data.get("element_set", "EALL")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CalculiXNodeSet:
    """Named CalculiX node set."""

    name: str
    node_ids: tuple[int, ...]
    role: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "node_ids": list(self.node_ids),
            "role": self.role,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CalculiXNodeSet:
        if not isinstance(data, Mapping):
            msg = "CalculiXNodeSet must be a mapping."
            raise ValueError(msg)
        return cls(
            name=str(data.get("name", "")),
            node_ids=_int_tuple(data.get("node_ids", ())),
            role=str(data.get("role", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CalculiXElementSet:
    """Named CalculiX element set."""

    name: str
    element_ids: tuple[int, ...]
    role: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "element_ids": list(self.element_ids),
            "role": self.role,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CalculiXElementSet:
        if not isinstance(data, Mapping):
            msg = "CalculiXElementSet must be a mapping."
            raise ValueError(msg)
        return cls(
            name=str(data.get("name", "")),
            element_ids=_int_tuple(data.get("element_ids", ())),
            role=str(data.get("role", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CalculiXSurfaceSet:
    """Element-face surface placeholder for pressure loads."""

    name: str
    element_faces: tuple[tuple[int, str], ...] = field(default_factory=tuple)
    element_ids: tuple[int, ...] = field(default_factory=tuple)
    role: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "element_faces": [
                [element_id, face] for element_id, face in self.element_faces
            ],
            "element_ids": list(self.element_ids),
            "role": self.role,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CalculiXSurfaceSet:
        if not isinstance(data, Mapping):
            msg = "CalculiXSurfaceSet must be a mapping."
            raise ValueError(msg)
        raw_faces = data.get("element_faces", ())
        faces = tuple(
            (int(item[0]), str(item[1]))
            for item in raw_faces
            if isinstance(item, Sequence) and not isinstance(item, str) and len(item) >= 2
        )
        return cls(
            name=str(data.get("name", "")),
            element_faces=faces,
            element_ids=_int_tuple(data.get("element_ids", ())),
            role=str(data.get("role", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CalculiXBoundary:
    """Boundary condition record for the v0.1 deck writer."""

    name: str
    set_name: str
    dof_start: int = 1
    dof_end: int = 3
    value: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "set_name": self.set_name,
            "dof_start": self.dof_start,
            "dof_end": self.dof_end,
            "value": self.value,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CalculiXBoundary:
        if not isinstance(data, Mapping):
            msg = "CalculiXBoundary must be a mapping."
            raise ValueError(msg)
        return cls(
            name=str(data.get("name", "")),
            set_name=str(data.get("set_name", data.get("node_set", ""))),
            dof_start=int(data.get("dof_start", 1)),
            dof_end=int(data.get("dof_end", 3)),
            value=float(data.get("value", 0.0)),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CalculiXLoad:
    """Force or pressure load record for the v0.1 deck writer."""

    name: str
    load_type: str
    target_set: str
    components: tuple[float, float, float] | None = None
    magnitude: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "load_type": self.load_type,
            "target_set": self.target_set,
            "components": list(self.components) if self.components is not None else None,
            "magnitude": self.magnitude,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CalculiXLoad:
        if not isinstance(data, Mapping):
            msg = "CalculiXLoad must be a mapping."
            raise ValueError(msg)
        components = data.get("components")
        magnitude = data.get("magnitude")
        return cls(
            name=str(data.get("name", "")),
            load_type=str(data.get("load_type", data.get("kind", ""))),
            target_set=str(data.get("target_set", data.get("node_set", data.get("surface", "")))),
            components=(
                _float_tuple(components, length=3)
                if components not in (None, "")
                else None
            ),
            magnitude=float(magnitude) if magnitude not in (None, "") else None,
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CalculiXStep:
    """Linear static step metadata."""

    name: str
    analysis_type: str = CalculiXAnalysisType.LINEAR_STATIC.value
    output_requests: tuple[str, ...] = ("U", "S", "E")
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "analysis_type": self.analysis_type,
            "output_requests": list(self.output_requests),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CalculiXStep:
        if not isinstance(data, Mapping):
            msg = "CalculiXStep must be a mapping."
            raise ValueError(msg)
        return cls(
            name=str(data.get("name", "")),
            analysis_type=str(data.get("analysis_type", CalculiXAnalysisType.LINEAR_STATIC.value)),
            output_requests=tuple(
                str(item) for item in data.get("output_requests", ("U", "S", "E"))
            ),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CalculiXInputDeck:
    """Report-friendly CalculiX deck model."""

    heading: str
    nodes: tuple[CalculiXNode, ...]
    elements: tuple[CalculiXElement, ...]
    materials: tuple[CalculiXMaterial, ...]
    node_sets: tuple[CalculiXNodeSet, ...] = field(default_factory=tuple)
    element_sets: tuple[CalculiXElementSet, ...] = field(default_factory=tuple)
    surface_sets: tuple[CalculiXSurfaceSet, ...] = field(default_factory=tuple)
    boundaries: tuple[CalculiXBoundary, ...] = field(default_factory=tuple)
    loads: tuple[CalculiXLoad, ...] = field(default_factory=tuple)
    steps: tuple[CalculiXStep, ...] = field(default_factory=tuple)
    diagnostics: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "heading": self.heading,
            "nodes": [node.to_dict() for node in self.nodes],
            "elements": [element.to_dict() for element in self.elements],
            "materials": [material.to_dict() for material in self.materials],
            "node_sets": [node_set.to_dict() for node_set in self.node_sets],
            "element_sets": [
                element_set.to_dict() for element_set in self.element_sets
            ],
            "surface_sets": [
                surface_set.to_dict() for surface_set in self.surface_sets
            ],
            "boundaries": [boundary.to_dict() for boundary in self.boundaries],
            "loads": [load.to_dict() for load in self.loads],
            "steps": [step.to_dict() for step in self.steps],
            "diagnostics": [dict(item) for item in self.diagnostics],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CalculiXInputDeck:
        if not isinstance(data, Mapping):
            msg = "CalculiXInputDeck must be a mapping."
            raise ValueError(msg)
        return cls(
            heading=str(data.get("heading", "")),
            nodes=tuple(CalculiXNode.from_dict(item) for item in data.get("nodes", ())),
            elements=tuple(
                CalculiXElement.from_dict(item) for item in data.get("elements", ())
            ),
            materials=tuple(
                CalculiXMaterial.from_dict(item) for item in data.get("materials", ())
            ),
            node_sets=tuple(
                CalculiXNodeSet.from_dict(item) for item in data.get("node_sets", ())
            ),
            element_sets=tuple(
                CalculiXElementSet.from_dict(item)
                for item in data.get("element_sets", ())
            ),
            surface_sets=tuple(
                CalculiXSurfaceSet.from_dict(item)
                for item in data.get("surface_sets", ())
            ),
            boundaries=tuple(
                CalculiXBoundary.from_dict(item) for item in data.get("boundaries", ())
            ),
            loads=tuple(CalculiXLoad.from_dict(item) for item in data.get("loads", ())),
            steps=tuple(CalculiXStep.from_dict(item) for item in data.get("steps", ())),
            diagnostics=tuple(dict(item) for item in data.get("diagnostics", ())),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CalculiXDeckResult:
    """Structured result for a prepare-only deck generation request."""

    status: str
    deck: CalculiXInputDeck | None = None
    input_text: str = ""
    output_path: Path | None = None
    diagnostics: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    source_project_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status in {
            CalculiXDeckStatus.OK.value,
            CalculiXDeckStatus.WARNING.value,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "deck": self.deck.to_dict() if self.deck is not None else None,
            "input_text": self.input_text,
            "output_path": str(self.output_path) if self.output_path else "",
            "diagnostics": [dict(item) for item in self.diagnostics],
            "source_project_name": self.source_project_name,
            "metadata": dict(self.metadata),
        }


# Backwards-compatible aliases for the package's historical "Calculix" spelling.
CalculixAnalysisType = CalculiXAnalysisType
CalculixElementType = CalculiXElementType
CalculixDeckStatus = CalculiXDeckStatus
CalculixMaterial = CalculiXMaterial
CalculixNode = CalculiXNode
CalculixElement = CalculiXElement
CalculixNodeSet = CalculiXNodeSet
CalculixElementSet = CalculiXElementSet
CalculixSurfaceSet = CalculiXSurfaceSet
CalculixBoundary = CalculiXBoundary
CalculixLoad = CalculiXLoad
CalculixStep = CalculiXStep
CalculixInputDeck = CalculiXInputDeck
CalculixDeckResult = CalculiXDeckResult


def _int_tuple(value: object) -> tuple[int, ...]:
    if value is None:
        return ()
    if isinstance(value, Iterable) and not isinstance(value, str | bytes):
        return tuple(int(item) for item in value)
    return (int(value),)


def _float_tuple(value: object, *, length: int) -> tuple[float, ...]:
    if isinstance(value, Iterable) and not isinstance(value, str | bytes):
        items = tuple(float(item) for item in value)
    else:
        items = (float(value),)
    if len(items) >= length:
        return items[:length]
    return (*items, *(0.0 for _ in range(length - len(items))))
