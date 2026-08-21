"""Core 3D Workspace selection contracts.

Solver-agnostic, GUI-free, JSON-friendly data contracts for named entity
selections used by future 3D Workspace overlays and boundary-condition targets.

These models are metadata/state only. They never trigger a solver, never import
GUI/PyVista/meshio/solver-runner code, and carry no executable/command fields.
Legacy raw mesh entity ids remain readable. New node/cell targets may carry a
versioned fingerprint-bound ``EntityLocator``; staleness is always computed
from current mesh evidence rather than persisted as a mutable flag.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .validation import ValidationReport


class EntityKind(StrEnum):
    """Kind of entity a selection target references."""

    NODE = "node"
    CELL = "cell"
    FACE = "face"
    EDGE = "edge"
    POINT = "point"
    GEOMETRY_FACE = "geometry_face"
    GEOMETRY_EDGE = "geometry_edge"
    GEOMETRY_BODY = "geometry_body"
    SOLVER_LABEL = "solver_label"
    UNKNOWN = "unknown"

    @classmethod
    def coerce(cls, value: object) -> EntityKind:
        if isinstance(value, EntityKind):
            return value
        text = str(value or "").strip().lower()
        try:
            return cls(text)
        except ValueError:
            return cls.UNKNOWN


class SelectionMode(StrEnum):
    """Transient interactive selection mode (GUI/editor state)."""

    NODE = "node"
    CELL = "cell"
    FACE = "face"
    EDGE = "edge"
    MIXED = "mixed"
    NONE = "none"

    @classmethod
    def coerce(cls, value: object) -> SelectionMode:
        if isinstance(value, SelectionMode):
            return value
        text = str(value or "").strip().lower()
        try:
            return cls(text)
        except ValueError:
            return cls.NONE


class SelectionOperation(StrEnum):
    """How one picked entity changes the transient current selection."""

    REPLACE = "replace"
    ADD = "add"
    TOGGLE = "toggle"
    SUBTRACT = "subtract"

    @classmethod
    def coerce(cls, value: object) -> SelectionOperation:
        if isinstance(value, SelectionOperation):
            return value
        text = str(value or "").strip().lower()
        try:
            return cls(text)
        except ValueError:
            return cls.REPLACE


# MVP-active entity kinds are renderable/usable in the v0.1 workspace slice.
# Other kinds serialize and validate but are flagged as not-yet-MVP.
MVP_ACTIVE_ENTITY_KINDS: frozenset[EntityKind] = frozenset(
    {EntityKind.NODE, EntityKind.CELL, EntityKind.SOLVER_LABEL, EntityKind.UNKNOWN}
)
# Kinds whose ids are expected to be positive integer entity indices.
_INT_ID_KINDS: frozenset[EntityKind] = frozenset(
    {EntityKind.NODE, EntityKind.CELL, EntityKind.FACE, EntityKind.EDGE, EntityKind.POINT}
)
# Mesh-backed kinds should carry a mesh reference for later resolution.
_MESH_KINDS: frozenset[EntityKind] = _INT_ID_KINDS
_MODE_TO_ENTITY_KIND: dict[SelectionMode, EntityKind] = {
    SelectionMode.NODE: EntityKind.NODE,
    SelectionMode.CELL: EntityKind.CELL,
    SelectionMode.FACE: EntityKind.FACE,
    SelectionMode.EDGE: EntityKind.EDGE,
}


def _normalize_id(value: object) -> int | str:
    """Preserve int ids as ints and everything else as strings (no auto-int)."""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return value
    return str(value)


def _string_dict(value: Mapping[str, Any] | None) -> dict[str, Any]:
    return dict(value or {})


@dataclass(frozen=True)
class EntityLocator:
    """Durable identity for entities on one exact mesh."""

    identity_schema: str = ""
    mesh_ref: str = ""
    mesh_fingerprint: str = ""
    entity_kind: EntityKind = EntityKind.UNKNOWN
    id_namespace: str = ""
    entity_ids: tuple[int | str, ...] = ()
    cell_block_key: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "identity_schema", str(self.identity_schema or ""))
        object.__setattr__(self, "mesh_ref", str(self.mesh_ref or ""))
        object.__setattr__(
            self,
            "mesh_fingerprint",
            str(self.mesh_fingerprint or "").lower(),
        )
        object.__setattr__(self, "entity_kind", EntityKind.coerce(self.entity_kind))
        object.__setattr__(self, "id_namespace", str(self.id_namespace or ""))
        object.__setattr__(
            self,
            "entity_ids",
            tuple(_normalize_id(item) for item in self.entity_ids),
        )
        object.__setattr__(
            self,
            "cell_block_key",
            None if self.cell_block_key is None else str(self.cell_block_key),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "identity_schema": self.identity_schema,
            "mesh_ref": self.mesh_ref,
            "mesh_fingerprint": self.mesh_fingerprint,
            "entity_kind": self.entity_kind.value,
            "id_namespace": self.id_namespace,
            "entity_ids": list(self.entity_ids),
        }
        if self.cell_block_key is not None:
            payload["cell_block_key"] = self.cell_block_key
        return payload

    @classmethod
    def from_dict(cls, data: object) -> EntityLocator:
        if not isinstance(data, Mapping):
            msg = "EntityLocator data must be a mapping."
            raise TypeError(msg)
        return cls(
            identity_schema=str(data.get("identity_schema", "")),
            mesh_ref=str(data.get("mesh_ref", "")),
            mesh_fingerprint=str(data.get("mesh_fingerprint", "")),
            entity_kind=EntityKind.coerce(
                data.get("entity_kind", EntityKind.UNKNOWN.value)
            ),
            id_namespace=str(data.get("id_namespace", "")),
            entity_ids=tuple(
                _normalize_id(item)
                for item in data.get("entity_ids", ()) or ()
            ),
            cell_block_key=(
                None
                if data.get("cell_block_key") is None
                else str(data.get("cell_block_key"))
            ),
        )

    def validate(self, *, path: str = "entity_locator") -> ValidationReport:
        report = ValidationReport()
        for field_name, value in (
            ("identity_schema", self.identity_schema),
            ("mesh_ref", self.mesh_ref),
            ("mesh_fingerprint", self.mesh_fingerprint),
            ("id_namespace", self.id_namespace),
        ):
            if not value:
                report.add_error(
                    f"{path}.{field_name}",
                    f"Durable entity locator requires {field_name}.",
                )
        if self.entity_kind not in {EntityKind.NODE, EntityKind.CELL}:
            report.add_error(
                f"{path}.entity_kind",
                "Durable entity locators support only node or cell entities.",
            )
        if not self.entity_ids:
            report.add_error(
                f"{path}.entity_ids",
                "Durable entity locator requires at least one entity ID.",
            )
        if len(set(self.entity_ids)) != len(self.entity_ids):
            report.add_error(
                f"{path}.entity_ids",
                "Durable entity locator entity IDs must be unique.",
            )
        return report


@dataclass(frozen=True)
class SelectionTargetRef:
    """A serializable reference to selected mesh/geometry/solver-label entities."""

    kind: EntityKind = EntityKind.UNKNOWN
    ids: tuple[int | str, ...] = ()
    mesh_ref: str = ""
    label: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    locator: EntityLocator | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", EntityKind.coerce(self.kind))
        # Order is preserved deliberately (reproducible rendering / report / adapter order).
        object.__setattr__(self, "ids", tuple(_normalize_id(item) for item in self.ids))
        object.__setattr__(self, "mesh_ref", str(self.mesh_ref or ""))
        object.__setattr__(self, "label", str(self.label or ""))
        object.__setattr__(self, "provenance", _string_dict(self.provenance))
        object.__setattr__(self, "metadata", _string_dict(self.metadata))
        object.__setattr__(self, "locator", _coerce_locator(self.locator))

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "kind": self.kind.value,
            "ids": list(self.ids),
            "mesh_ref": self.mesh_ref,
            "label": self.label,
            "provenance": dict(self.provenance),
            "metadata": dict(self.metadata),
        }
        if self.locator is not None:
            payload["locator"] = self.locator.to_dict()
        return payload

    @classmethod
    def from_dict(cls, data: object) -> SelectionTargetRef:
        if not isinstance(data, Mapping):
            msg = "SelectionTargetRef data must be a mapping."
            raise TypeError(msg)
        return cls(
            kind=EntityKind.coerce(data.get("kind", EntityKind.UNKNOWN.value)),
            ids=tuple(_normalize_id(item) for item in data.get("ids", ()) or ()),
            mesh_ref=str(data.get("mesh_ref", "")),
            label=str(data.get("label", "")),
            provenance=_string_dict(data.get("provenance", {})),
            metadata=_string_dict(data.get("metadata", {})),
            locator=_coerce_locator(data.get("locator")),
        )

    def validate(self, *, path: str = "selection_target") -> ValidationReport:
        report = ValidationReport()
        if not self.ids:
            report.add_warning(f"{path}.ids", "Selection target has no entity ids.")
        if self.kind in _INT_ID_KINDS and self.locator is None:
            for index, item in enumerate(self.ids):
                if not isinstance(item, int):
                    report.add_warning(
                        f"{path}.ids[{index}]",
                        f"Entity kind {self.kind.value!r} expects integer ids; got {item!r}.",
                    )
        if self.kind in _MESH_KINDS and not self.mesh_ref:
            report.add_warning(
                f"{path}.mesh_ref",
                f"Mesh-backed selection kind {self.kind.value!r} has no mesh_ref for resolution.",
            )
        if self.locator is not None:
            report.extend(self.locator.validate(path=f"{path}.locator"))
            if self.locator.entity_kind is not self.kind:
                report.add_error(
                    f"{path}.locator.entity_kind",
                    "Locator entity kind must match its selection target.",
                )
            if self.locator.entity_ids != self.ids:
                report.add_error(
                    f"{path}.locator.entity_ids",
                    "Locator entity IDs must match their canonical selection target IDs.",
                )
            if self.mesh_ref and self.locator.mesh_ref != self.mesh_ref:
                report.add_error(
                    f"{path}.locator.mesh_ref",
                    "Locator mesh_ref must match its selection target.",
                )
        return report


@dataclass(frozen=True)
class NamedSelection:
    """A persisted, user-visible named group of selected entities."""

    id: str = ""
    name: str = ""
    description: str = ""
    entity_kind: EntityKind = EntityKind.UNKNOWN
    targets: tuple[SelectionTargetRef, ...] = ()
    source_mesh_ref: str = ""
    solver_labels: dict[str, list[str]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", str(self.id or ""))
        object.__setattr__(self, "name", str(self.name or ""))
        object.__setattr__(self, "description", str(self.description or ""))
        object.__setattr__(self, "entity_kind", EntityKind.coerce(self.entity_kind))
        object.__setattr__(self, "targets", tuple(_coerce_target(item) for item in self.targets))
        object.__setattr__(self, "source_mesh_ref", str(self.source_mesh_ref or ""))
        object.__setattr__(self, "solver_labels", _normalize_solver_labels(self.solver_labels))
        object.__setattr__(self, "metadata", _string_dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "entity_kind": self.entity_kind.value,
            "targets": [target.to_dict() for target in self.targets],
            "source_mesh_ref": self.source_mesh_ref,
            "solver_labels": {key: list(value) for key, value in self.solver_labels.items()},
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> NamedSelection:
        if not isinstance(data, Mapping):
            msg = "NamedSelection data must be a mapping."
            raise TypeError(msg)
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            description=str(data.get("description", "")),
            entity_kind=EntityKind.coerce(data.get("entity_kind", EntityKind.UNKNOWN.value)),
            targets=tuple(
                SelectionTargetRef.from_dict(item)
                for item in data.get("targets", ()) or ()
                if isinstance(item, Mapping)
            ),
            source_mesh_ref=str(data.get("source_mesh_ref", "")),
            solver_labels=_normalize_solver_labels(data.get("solver_labels", {})),
            metadata=_string_dict(data.get("metadata", {})),
        )

    def validate(self, *, path: str = "named_selection") -> ValidationReport:
        report = ValidationReport()
        if not self.id:
            report.add_error(f"{path}.id", "Named selection id is required.")
        if not self.name:
            report.add_error(f"{path}.name", "Named selection name is required.")
        if not self.targets:
            report.add_error(
                f"{path}.targets", "Named selection must reference at least one target."
            )
        if self.entity_kind == EntityKind.UNKNOWN:
            report.add_warning(
                f"{path}.entity_kind",
                "Named selection entity_kind is unknown; it is not renderable in the MVP.",
            )
        for index, target in enumerate(self.targets):
            report.extend(target.validate(path=f"{path}.targets[{index}]"))
        return report


@dataclass(frozen=True)
class SelectionState:
    """Transient interactive selection state; not persisted in ProjectSchema."""

    active_targets: tuple[SelectionTargetRef, ...] = ()
    mode: SelectionMode = SelectionMode.NONE
    last_committed_selection_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "active_targets", tuple(_coerce_target(item) for item in self.active_targets)
        )
        object.__setattr__(self, "mode", SelectionMode.coerce(self.mode))
        object.__setattr__(
            self, "last_committed_selection_id", str(self.last_committed_selection_id or "")
        )
        object.__setattr__(self, "metadata", _string_dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_targets": [target.to_dict() for target in self.active_targets],
            "mode": self.mode.value,
            "last_committed_selection_id": self.last_committed_selection_id,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> SelectionState:
        if not isinstance(data, Mapping):
            msg = "SelectionState data must be a mapping."
            raise TypeError(msg)
        return cls(
            active_targets=tuple(
                SelectionTargetRef.from_dict(item)
                for item in data.get("active_targets", ()) or ()
                if isinstance(item, Mapping)
            ),
            mode=SelectionMode.coerce(data.get("mode", SelectionMode.NONE.value)),
            last_committed_selection_id=str(data.get("last_committed_selection_id", "")),
            metadata=_string_dict(data.get("metadata", {})),
        )

    def to_named_selection(
        self, id: str, name: str, description: str = ""
    ) -> NamedSelection:
        """Commit the current transient targets into a persistable NamedSelection."""
        entity_kind = _MODE_TO_ENTITY_KIND.get(self.mode)
        if entity_kind is None:
            entity_kind = self.active_targets[0].kind if self.active_targets else EntityKind.UNKNOWN
        source_mesh_ref = ""
        for target in self.active_targets:
            if target.mesh_ref:
                source_mesh_ref = target.mesh_ref
                break
        return NamedSelection(
            id=id,
            name=name,
            description=description,
            entity_kind=entity_kind,
            targets=self.active_targets,
            source_mesh_ref=source_mesh_ref,
            metadata=dict(self.metadata),
        )


@dataclass(frozen=True)
class BoundaryTargetRef:
    """Structured optional target for a BoundaryCondition (hybrid with legacy target)."""

    selection_id: str = ""
    solver_label: str = ""
    display: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "selection_id", str(self.selection_id or ""))
        object.__setattr__(self, "solver_label", str(self.solver_label or ""))
        object.__setattr__(self, "display", str(self.display or ""))
        object.__setattr__(self, "metadata", _string_dict(self.metadata))

    @property
    def is_empty(self) -> bool:
        return not (self.selection_id or self.solver_label or self.display)

    def to_dict(self) -> dict[str, Any]:
        return {
            "selection_id": self.selection_id,
            "solver_label": self.solver_label,
            "display": self.display,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> BoundaryTargetRef:
        if not isinstance(data, Mapping):
            msg = "BoundaryTargetRef data must be a mapping."
            raise TypeError(msg)
        return cls(
            selection_id=str(data.get("selection_id", "")),
            solver_label=str(data.get("solver_label", "")),
            display=str(data.get("display", "")),
            metadata=_string_dict(data.get("metadata", {})),
        )

    def validate(self, *, path: str = "target_ref") -> ValidationReport:
        report = ValidationReport()
        if self.is_empty:
            report.add_warning(
                path,
                "Boundary target reference has no selection_id, solver_label, or display.",
            )
        return report


def _coerce_target(value: object) -> SelectionTargetRef:
    if isinstance(value, SelectionTargetRef):
        return value
    if isinstance(value, Mapping):
        return SelectionTargetRef.from_dict(value)
    msg = "Selection target must be a SelectionTargetRef or mapping."
    raise TypeError(msg)


def _coerce_locator(value: object) -> EntityLocator | None:
    if value is None:
        return None
    if isinstance(value, EntityLocator):
        return value
    if isinstance(value, Mapping):
        return EntityLocator.from_dict(value)
    msg = "Selection locator must be an EntityLocator, mapping, or None."
    raise TypeError(msg)


def has_durable_entity_locators(
    selections: Sequence[NamedSelection],
) -> bool:
    """Return whether any selection carries new fingerprint-bound identity."""

    return any(
        target.locator is not None
        for selection in selections
        for target in selection.targets
    )


def _normalize_solver_labels(value: object) -> dict[str, list[str]]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, list[str]] = {}
    for key, labels in value.items():
        if isinstance(labels, str):
            normalized[str(key)] = [labels]
        elif isinstance(labels, Iterable):
            normalized[str(key)] = [str(item) for item in labels]
        else:
            normalized[str(key)] = [str(labels)]
    return normalized


def coerce_boundary_target_ref(value: object) -> BoundaryTargetRef | None:
    """Coerce dict/BoundaryTargetRef/None into an optional BoundaryTargetRef."""
    if value is None:
        return None
    if isinstance(value, BoundaryTargetRef):
        return value
    if isinstance(value, Mapping):
        return BoundaryTargetRef.from_dict(value)
    msg = "BoundaryCondition target_ref must be a BoundaryTargetRef, mapping, or None."
    raise TypeError(msg)


def coerce_named_selections(value: Sequence[Any] | None) -> list[NamedSelection]:
    """Coerce a sequence of NamedSelection/dict into a list of NamedSelection."""
    if not value:
        return []
    result: list[NamedSelection] = []
    for item in value:
        if isinstance(item, NamedSelection):
            result.append(item)
        elif isinstance(item, Mapping):
            result.append(NamedSelection.from_dict(item))
        else:
            msg = "Project selection must be a NamedSelection or mapping."
            raise TypeError(msg)
    return result


__all__ = [
    "MVP_ACTIVE_ENTITY_KINDS",
    "BoundaryTargetRef",
    "EntityLocator",
    "EntityKind",
    "NamedSelection",
    "SelectionMode",
    "SelectionOperation",
    "SelectionState",
    "SelectionTargetRef",
    "coerce_boundary_target_ref",
    "coerce_named_selections",
    "has_durable_entity_locators",
]
